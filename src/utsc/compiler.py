from .utils import (
	get_code,
	throw,
	warn,
	SymbolTable,
	SigNonConstantNumericalExpressionException
)

from .ast_preprocessor import SyntaxTreePreproccesor

from os import remove as os_remove
from os.path import isfile, normpath, dirname, basename
from sys import platform as sys_platform
from subprocess import call as subproc_call

from json import load

from typing import Union

# these constants are for <Windows.h> VirtualAlloc/VirtualProtect/VirtualFree
WINDOWS_H_PAGE_READWRITE = 0x04
WINDOWS_H_PAGE_EXECUTE_READ = 0x20
WINDOWS_H_MEM_COMMIT = 0x1000
WINDOWS_H_MEM_RESERVE = 0x2000
WINDOWS_H_MEM_COMMIT_RESERVE = WINDOWS_H_MEM_COMMIT | WINDOWS_H_MEM_RESERVE
WINDOWS_H_MEM_RELEASE = 0x8000

class Compiler:
	def __init__(self, ast: dict, code: str, compiler_path: str, file_path: str, filename: str, optimize: int, structs: dict, module: bool):
		self.ast = ast
		self.top = ""
		self.text = "section .text"
		self.unprocessed_text = "section .text"
		self.bss = "section .bss"
		self.data = "section .data"
		self.symbols = SymbolTable(code)
		self.evaluator = SyntaxTreePreproccesor(ast)
		self.source = code
		self.structs: dict[str, list[str]] = structs
		self.used_counters: list[int] = []
		self.hidden_cached: int = None
		self.optimize = optimize
		self.compiler_path = compiler_path+'/..'
		self.file_path = file_path
		self.filename = filename
		self.link_with: list[str] = []
		self.exports: list[str] = []
		self.imported_modinfo: dict[str, dict[str, Union[list[str], dict]]] = {}
		self.names_from: dict[str, str] = {}
		self.in_namespace: list[str] = []
		self.imported_names: list[str] = [] # for checking for imports for special features
		self.collected_info: str = '\n'.join(f"Struct '{struct}' has members {members}" for struct, members in self.structs.items())+'\n' # currently just for debug to see how many optimizations are possible
		
		if not module:
			self.dumpvar = f"dumpvar.0"
			self.bssinstr(f"{self.dumpvar} resd 1")

		# add more options - i.e. architecture from cmd line args
		self.platform = "win32" if sys_platform == "win32" else "elf32"

	@property
	def hidden_counter(self):
		if self.hidden_cached: return self.hidden_cached

		i = 0

		while i in self.used_counters: i+=1

		self.hidden_cached = i

		return i
	
	def reload_counter(self):
		self.used_counters.append(self.hidden_cached)
		self.hidden_cached = 0

	@property
	def asm(self) -> str:
		return f"{self.top}\n\n{self.bss}\n\n{self.text}\n\n{self.data}"

	def instr(self, instruction: str, unprocessed: str=None):
		self.text+=f"\n{instruction}"
		self.unprocessed_text+=f"\n{unprocessed if unprocessed is not None else instruction}"

	def topinstr(self, instr: str):
		self.top+=f"\n{instr}"

	def toptextinstr(self, instruction: str):
		self.asm = f"\t{instruction}\n{self.asm}"

	def bssinstr(self, instruction: str):
		self.bss+=f"\n\t{instruction}"

	def datainstr(self, instruction: str):
		self.data+=f"\n\t{instruction}"

	#The two methods below allocate memory for the
	#variable and place it in a symbol table
	def declare_variable(self, node: dict):
		name: str = '.'.join(self.in_namespace+[node["name"]])
		_type: str = node["type"]

		self.bssinstr(f"_{name} resb 4")
		self.symbols.declare(name, _type, 4, f"_{name}")

	def define_variable(self, node: dict):
		name: str = '.'.join(self.in_namespace+[node["name"]])
		_type: str = node["type"]
		value: dict = node["value"]
		index: int = node["index"]

		self.symbols.declare(name, _type, 4, f"_{name}")
		self.symbols.assign(name, value, index)

		if value.get("Anonymous Function") is not None:
			value = value["Anonymous Function"]

			if value["type"] != "normal":
				code = get_code(self.source, value["index"])

				warn(f"UTSC 314: tried to create {value['type']} function in global scope, defaulting to normal function", code)

			func_compiler = FunctionCompiler(
				value["parameters"],
				value["body"],
				self.source,
				self
			)

			self.collected_info+=f"Function '{name}' takes {func_compiler.params}\n"

			func_code = func_compiler.traverse()

			self.instr(f"_{name}:")
			self.instr(func_code, unprocessed=func_compiler.text)

		elif value.get("String Literal") is not None:
			original = value["String Literal"]
			value = ', '.join(str(ord(c)) for c in original)

			self.datainstr(f"_{name} db {value}, 0 ; string {original!r}")

			self.collected_info+=f"Global variable '{name}' is the string {value['String Literal']!r}\n"
		else:
			try: value = eval(self.evaluator.simplify_numerical_expression(value))
			except SigNonConstantNumericalExpressionException:
				code = get_code(self.source, index)
				throw("UTSC 303: Only constant numerical/function/string values allowed in global scope", code)

			self.datainstr(f"_{name} dd {value}")

			self.collected_info+=f"Global variable '{name}' is the number {value}\n"
	#

	def gen_modinfo(self):
		modinfo: dict[str, Union[list[str], dict]] = {}

		modinfo["names"] = self.exports
		modinfo["imported-modules"] = self.imported_modinfo
		modinfo["names-from"] = self.names_from

		return modinfo
	
	def findmod_modinfo(self, modname: str, modules: dict[str, dict[Union[list[str], dict]]]=None) -> bool:
		modules = modules if modules is not None else self.imported_modinfo
		
		for module, info in modules.items():
			if modname == module: return True

			if self.findmod_modinfo(modname, info["imported-modules"]): return True

		return False
	
	def filter_already_imported(self, modinfo: dict[str, Union[list[str], dict]]) -> None:
		for modname, info in modinfo["imported-modules"].items():
			if self.findmod_modinfo(modname): continue
			obj_modname = '.'.join(modname.split('.')[:-1]+['o'])
			self.link_with.append(obj_modname)

			self.filter_already_imported(info)

	def make_namespace(self, node: dict):
		name: str = node["name"]
		code: dict = node["body"]

		self.in_namespace+=name.split('.') # step in
		self.traverse(code)

		for _ in range(len(name.split('.'))): self.in_namespace.pop(-1) # step out

	def import_names(self, node: dict):
		names: list[str] = node["names"]
		module = node["module"]

		self.imported_names.extend(names)

		uts_mod = normpath(f"{self.file_path}/{module}.uts")
		modinfo = normpath(f"{module}.modinfo")
		asm_mod = normpath(f"{self.file_path}/{module}.asm")
		lib_uts_mod = normpath(f"{self.compiler_path}/uts-lib/{module}.uts")
		lib_modinfo = normpath(f"{self.compiler_path}/uts-lib/{module}.modinfo")
		lib_obj_mod = normpath(f"{self.compiler_path}/uts-lib/{module}.o")
		obj_mod = normpath(f"{self.file_path}/{module}.o")

		if (not isfile(uts_mod) and isfile(lib_uts_mod)):
			uts_mod = lib_uts_mod
			modinfo = lib_modinfo
			obj_mod = lib_obj_mod

		if (not isfile(obj_mod) and isfile(lib_obj_mod)):
			obj_mod = lib_obj_mod

		if sys_platform == "win32":
			shell = ["powershell"]
		else:
			shell = ["bash", "-c"]

		if isfile(uts_mod): # if a .uts file, compile it
			try:
				subproc_call([*shell, "utsc", "-o", modinfo, uts_mod, f"-O{self.optimize}"])
				
				try:
					with open(modinfo, 'r') as f:
						modinfo_dict: dict[str, Union[list[str], dict]] = load(f)
				except FileNotFoundError:
					raise ZeroDivisionError() # some random error to catch
				
				if not self.findmod_modinfo(uts_mod):
					self.link_with.append(obj_mod)
					self.filter_already_imported(modinfo_dict)

				self.imported_modinfo[uts_mod] = modinfo_dict
				
				for name in modinfo_dict["names"]:
					if (name in self.names_from) and (self.names_from[name] != uts_mod):
						throw(f"UTSC 309: name '{name}' is defined twice - in both {self.names_from[name]!r} and {uts_mod!r}")
						continue

					self.names_from[name] = uts_mod

				for name in modinfo_dict["names-from"]:
					defined_in = modinfo_dict["names-from"][name]
					if (name in self.names_from) and (self.names_from[name] != defined_in):
						throw(f"UTSC 309: name '{name}' is defined twice - in both {self.names_from[name]!r} and {defined_in}")
						continue

					self.names_from[name] = defined_in
			except ZeroDivisionError:
				throw(f"UTSC 302: An error occurred while importing '{module}'")
				return
			except OSError:
				throw(f"UTSC 301: Module '{module}' could not be compiled - utsc is not in PATH.")
				return

			try:
				os_remove(modinfo)
			except FileNotFoundError: pass

			subproc_call([*shell, "utsc", "-o", obj_mod, uts_mod, f"-O{self.optimize}", "--module"])
		elif module != "<libc>": warn(f"UTSC 310: Could not check for symbol clashes while importing '{module}'")

		# make compiler config with NASM and GCC paths/ configured shell to use later
		if (isfile(asm_mod)):
			try: subproc_call([*shell, "nasm", "-f", self.platform, "-o", obj_mod, asm_mod])
			except OSError:
				throw(f"UTSC 301: Module '{module}' could not be compiled - nasm is not in PATH.")

		if isfile(obj_mod):
			if obj_mod not in self.link_with: self.link_with.append(obj_mod)
		elif module != "<libc>": # if module doesn't exist...
			code = get_code(self.source, node["index"])

			throw(f"UTSC 301: Module '{module}' doesn't exist!", code)

		for name in names:
			if isfile(uts_mod) and name not in modinfo_dict["names"]:
				throw(f"UTSC 307: Module '{module}' does not include name '{name}' (failed at import)")
			
			self.topinstr(f"extern _{name}")
			self.symbols.declare(name, "CONST", 4, f"_{name}")

		if module == "<libc>":
			for name in names:
				if (name in self.names_from) and (self.names_from[name] != uts_mod):
						throw(f"UTSC 309: '{name}' is imported from '<libc>' when it has another origin from {self.names_from[name]!r}")
						continue
				
				self.names_from[name] = "<libc>"

	def import_ns(self, node: dict):
		ns_names: list[str] = node["names"]
		module: module = node["module"]
		idx: int = node["index"]

		uts_mod = normpath(f"{self.file_path}/{module}.uts")
		modinfo = normpath(f"{module}.modinfo")
		lib_uts_mod = normpath(f"{self.compiler_path}/uts-lib/{module}.uts")
		lib_modinfo = normpath(f"{self.compiler_path}/uts-lib/{module}.modinfo")
		lib_obj_mod = normpath(f"{self.compiler_path}/uts-lib/{module}.o")
		obj_mod = normpath(f"{self.file_path}/{module}.o")

		if not isfile(uts_mod):
			uts_mod = lib_uts_mod
			modinfo = lib_modinfo
			obj_mod = lib_obj_mod

		if sys_platform == "win32":
			shell = ["powershell"]
		else:
			shell = ["bash", "-c"]

		if not (isfile(uts_mod)):
			code = get_code(self.source, idx)
			throw("UTSC 312: Cannot import namespace from a non-UntypedScript file (you can only import namespaces from .uts files).", code)
			return
		try:
			subproc_call([*shell, "utsc", "-o", modinfo, uts_mod, f"-O{self.optimize}"])
			
			try:
				with open(modinfo, 'r') as f:
					modinfo_dict: dict[str, Union[list[str], dict]] = load(f)
			except FileNotFoundError:
				raise ZeroDivisionError() # some random error to catch

			if not self.findmod_modinfo(uts_mod):
				self.link_with.append(obj_mod)
				self.filter_already_imported(modinfo_dict)

			self.imported_modinfo[uts_mod] = modinfo_dict

			for name in modinfo_dict["names"]:
				if (name in self.names_from) and (self.names_from[name] != uts_mod):
					throw(f"UTSC 309: name '{name}' is defined twice - in both {self.names_from[name]!r} and {uts_mod!r}")
					continue

				self.names_from[name] = uts_mod

			for name in modinfo_dict["names-from"]:
				defined_in = modinfo_dict["names-from"][name]
				if (name in self.names_from) and (self.names_from[name] != defined_in):
					throw(f"UTSC 309: name '{name}' is defined twice - in both {self.names_from[name]!r} and {defined_in}")
					continue

				self.names_from[name] = defined_in
		except ZeroDivisionError:
			throw(f"UTSC 302: An error occurred while importing '{module}'")
			return
		except OSError:
			throw(f"UTSC 301: Module '{module}' could not be compiled - utsc is not in PATH.")
			return
					
		try:
			os_remove(modinfo)
		except FileNotFoundError: pass

		subproc_call([*shell, "utsc", "-o", obj_mod, uts_mod, f"-O{self.optimize}", "--module"])
		
		if not isfile(obj_mod):
			code = get_code(self.source, node["index"])

			throw(f"UTSC 311: Object file for '{module}' disappeared!", code)

		if obj_mod not in self.link_with: self.link_with.append(obj_mod)

		for ns in ns_names:
			names: list[str] = [
				name for name in modinfo_dict["names"] if name.startswith(f"{ns}.")
			]

			self.imported_names.extend(names)

			for name in names:
				self.topinstr(f"extern _{name}")

				self.symbols.declare(name, "CONST", 4, f"_{name}")

	def import_struct(self, node: dict):
		struct_names: list[str] = node["names"]
		module: module = node["module"]
		idx: int = node["index"]

		uts_mod = normpath(f"{self.file_path}/{module}.uts")
		struct_mod = normpath(f"{self.file_path}/{module}.structs")
		lib_uts_mod = normpath(f"{self.compiler_path}/uts-lib/{module}.uts")
		lib_struct_mod = normpath(f"{self.compiler_path}/uts-lib/{module}.structs")


		if not isfile(uts_mod):
			uts_mod = lib_uts_mod
			struct_mod = lib_struct_mod

		if sys_platform == "win32":
			shell = ["powershell"]
		else:
			shell = ["bash", "-c"]

		if not (isfile(uts_mod)):
			code = get_code(self.source, idx)
			throw("UTSC 312: Cannot import struct from a non-UntypedScript file (you can only import structs from .uts files).", code)
			return
	
		subproc_call([*shell, "utsc", "-o", struct_mod, uts_mod, f"-O{self.optimize}", "--module"])
		
		if not isfile(struct_mod):
			code = get_code(self.source, idx)

			throw(f"UTSC 311: Struct file for '{module}' disappeared!", code)
			return
		
		with open(struct_mod, 'r') as f:
			structs: dict[str, list[str]] = load(f)

		for name in struct_names:
			if name not in structs:
				code = get_code(self.source, idx)

				throw(f"UTSC 307: Struct '{name}' does not exist in '{module}'!", code)
				continue

			if name in self.structs:
				code = get_code(self.source, idx)

				throw(f"UTSC 309: Struct '{name}' (from '{module}') is already defined!", code)
				continue

			self.structs[name] = structs[name]

	def export_names(self, node: list[str]):
		for name in node:
			self.topinstr(f"global _{name}")
			self.exports.append(name)

			if (name in self.names_from) and (self.names_from[name] != self.filename):
					throw(f"UTSC 309: name '{name}' is defined twice - in both {self.names_from[name]!r} and {self.filename!r}")
					continue
			
			self.names_from[name] = self.filename

	def export_ns(self, node: list[str]):
		for ns in node:
			exports = [symbol for symbol in self.symbols.symbols.keys() if symbol.startswith(f"{ns}.")]

			self.export_names(exports)

	#Traverses the AST and passes off each node to a specialized function
	def traverse(self, top: dict=None):
		key: str; node: dict
		
		top = top if top is not None else self.ast

		for key, node in top.items():
			if not self.in_namespace:
				if key.startswith("Import"):
					self.import_names(node)
					continue
				if key.startswith("Namespace Import"):
					self.import_ns(node)
					continue
				if key.startswith("Struct Import"):
					self.import_struct(node)
					continue
				if key.startswith("Export"):
					self.export_names(node)
					continue
				if key.startswith("Namespace Export"):
					self.export_ns(node)
					continue
			if key.startswith("Expression"):
				self.traverse(node)
			elif key.startswith("Variable Declaration"):
				self.declare_variable(node)
			elif key.startswith("Variable Definition"):
				self.define_variable(node)
			elif key.startswith("Variable Assignment"):
				code = get_code(self.source, node["index"])
				throw("UTSC 304: Assignments not allowed in global scope.", code)
			elif key.startswith("Namespace Declaration"):
				self.make_namespace(node)
			else:
				throw(f"(fatal) UTSC 305: Unimplemented or Invalid AST Node '{key}' (global scope)")
				return

		return self.asm
	#
#

class FunctionCompiler(Compiler):
	def __init__(self, params: dict[str, str], body: dict, code: str, outer: Compiler, localonly_label: str=""):
		self.text = ""
		self.unprocessed_text = ""
		self.body = body
		self.allocated_bytes = 0
		self.symbols = SymbolTable(code, outer.symbols)
		self.source = code
		self.outer = outer
		self.params = params
		self.localonly_offset_label = localonly_label
		self.localonly_amount = 0 # to be set after object creation
		self.ident = outer.hidden_counter
		self.allocated_bytes_label = f"function.{self.ident}.ALLOCATED_BYTES"
		outer.reload_counter()

		arg_offset = 8
		for param, dtype in params.items(): # reserve space for each arg
			addr = f"ebp+{arg_offset}"

			self.symbols.declare(param, dtype, 4, addr)

			arg_offset+=4

		self.last_arg_offset = arg_offset

	def instr(self, instr: str, unprocessed: str=None):
		self.text+=f"\n\t{instr}"
		self.unprocessed_text+=f"\n{unprocessed if unprocessed is not None else instr}"

	def remove_last_instr(self):
		instr = self.text.splitlines()[-1]
		self.text = '\n'.join(self.text.splitlines()[:-1])
		return instr

	def generate_expression(self, expr: dict[str, dict], getfuncaddr: bool=False, propassign: bool=False, passqual: str=None, noopt: bool=False):
		for key, node in expr.items():
			if key.startswith("Binary Operation"):
				op = key.removeprefix("Binary Operation ")

				self.generate_expression(node[0], getfuncaddr=getfuncaddr)
				self.instr("push eax") #save result
				self.generate_expression(node[1], getfuncaddr=getfuncaddr)
				self.instr("pop ebx") # load left node result into ebx

				if op == '/': #integer division
					# switch registers
					self.instr("push eax")
					self.instr("mov eax, ebx")
					self.instr("pop ebx")
					self.instr("xor edx, edx")
					self.instr("idiv ebx")
				elif op == '%': #modulo
					# switch registers
					self.instr("push eax")
					self.instr("mov eax, ebx")
					self.instr("pop ebx")
					self.instr("xor edx, edx")
					self.instr("push edx") # save edx
					self.instr("idiv ebx")
					self.instr("mov eax, edx")
					self.instr("pop edx")
				else:
					if op == '+': #addition
						self.instr("add ebx, eax")
						self.instr("mov eax, ebx")
					elif op == '-': #subtraction
						self.instr("sub ebx, eax")
						self.instr("mov eax, ebx")
					elif op == '*': #integer multiplication
						self.instr("imul ebx, eax")
						self.instr("mov eax, ebx")
					elif op in ('>', '<', ">=", "<=", "==", "!="):
						self.instr("cmp ebx, eax")

						if op == '>':
							self.instr("setg al")
						elif op == '<':
							self.instr("setl al")
						elif op == ">=":
							self.instr("setge al")
						elif op == "<=":
							self.instr("setle al")
						elif op == "==":
							self.instr("sete al")
						elif op == "!=":
							self.instr("setne al")

						self.instr("movzx eax, al")
					else:
						self.instr("cmp ebx, 0")
						self.instr("setne bl")
						self.instr("movzx ebx, bl")
						self.instr("cmp eax, 0")
						self.instr("setne al")
						self.instr("movzx eax, al")						

						if op == "and":
							self.instr("and eax, ebx")
						elif op == "or":
							self.instr("or eax, ebx")
			elif key.startswith("Unary Operation"):
				op = key.removeprefix("Unary Operation ")
				if op == '-':
					self.generate_expression(node, getfuncaddr=getfuncaddr)
					self.instr("neg eax")
				elif op == "not":
					self.generate_expression(node, getfuncaddr=getfuncaddr)
					self.instr("cmp eax, 0")
					self.instr("sete al")
					self.instr("movzx eax, al")
			elif key.startswith("Addr Operation"):
				op = key.removeprefix("Addr Operation ")

				if op == "ref":
					self.generate_expression(node["expr"])
					instr = self.remove_last_instr()
					self.instr(f"lea eax, {instr.split(', ')[1]}")
				elif op == "deref":
					self.generate_expression(node, getfuncaddr=getfuncaddr)
					self.instr("mov eax, [eax]")
			elif key.startswith("Numerical Constant"):
				self.instr(f"mov eax, {node}")
			elif key.startswith("Variable Reference"):
				self.reference_var(node["name"], node["index"], getfuncaddr=getfuncaddr, passqual=passqual, noopt=noopt)
			elif key.startswith("Anonymous Function"):
				params: dict[str, str] = node["parameters"]
				body: dict = node["body"]
				_type: str = node["type"]

				if _type == "localonly":
					self.outer.collected_info+=f"  Local-only Anonymous Function (label with counter @ {self.outer.hidden_counter}) takes {params}\n"
					
					magicnum = self.outer.hidden_counter

					offset_name = f"localonly.arg_offset.NOT_THREAD_SAFE.{magicnum}"
					self.outer.datainstr(f"{offset_name} dd 0")
					
					func = FunctionCompiler(params, body, self.source, self.outer, offset_name)

					last_offset = func.last_arg_offset

					for symbol, info in tuple(self.symbols.symbols.items())[::-1]:
						if (("ebp+eax+") in info["address"]) and ("localonly.arg_offset.NOT_THREAD_SAFE" in info["address"]): continue # from more than one `localonly` level up -> not guaranteed access
						
						addr = f"ebp+eax+{last_offset}+{self.allocated_bytes_label}-{self.allocated_bytes+4}"

						func.symbols.declare(
							symbol,
							info["type"],
							info["size"],
							addr,
							f"mov eax, [{offset_name}]"
						)

						last_offset+=4

					func.localonly_amount = (last_offset-func.last_arg_offset)+self.localonly_amount

					func_name = f"anonymous.{magicnum}"
					func_asm_body = func.traverse()
					self.outer.instr(f"{func_name}:")
					self.outer.instr(func_asm_body, unprocessed=func.text)

					self.instr(f"mov eax, {func_name}")

					self.outer.reload_counter()
				elif _type == "heapalloced":
					self.outer.collected_info+=f"  Heap-allocated Anonymous Function (label with counter @ {self.outer.hidden_counter}) takes {params}\n"

					magicnum = self.outer.hidden_counter

					heapvar_label = f"function.HEAP_ALLOCATED.{magicnum}"
					funcsize_label = f"size_of_function.HEAP_ALLOCATED.{magicnum}"
					total_mem_label = f"mem_req_for_function.HEAP_ALLOCATED.{magicnum}"

					self.outer.bssinstr(f"{heapvar_label} resd 1")

					func = FunctionCompiler(params, body, self.source, self.outer)

					last_offset = 0

					symbols_to_add = {
						name: info for name, info in self.symbols.symbols.items() if (name != "ceci")
					}

					for symbol, info in symbols_to_add.items():
						func.symbols.declare(
							symbol,
							info["type"],
							info["size"],
							f"eax+{funcsize_label}+{last_offset}",
							beforeinstr=f"mov eax, [{heapvar_label}]"
						)

						last_offset+=4

					func.symbols.declare( # special symbol `ceci` needed for heap-allocated recursive functions
						"ceci",
						"CONST",
						4,
						f"eax",
						beforeinstr=f"mov eax, [{heapvar_label}]"
					)

					func_name = f"anonymous.{magicnum}"
					func_asm_body = func.traverse()
					self.outer.instr(f"{func_name}:")

					self.outer.instr(func_asm_body, unprocessed=func.text)
					self.outer.instr(f"{funcsize_label} equ $-{func_name}")
					self.outer.instr(f"{total_mem_label} equ {funcsize_label}+{last_offset}")


					self.instr(f"push {total_mem_label}")
					self.instr("lea eax, [_HeapFuncAlloc] ; no-optimize")
					self.instr("call eax")
					self.instr("add esp, 4")
					self.instr(f"mov [{heapvar_label}], eax")

					self.instr(f"push {funcsize_label}")
					self.instr(f"push {func_name}")
					self.instr(f"push DWORD [{heapvar_label}]")
					self.instr("lea eax, [_memcpy] ; no-optimize")
					self.instr("call eax")
					self.instr("add esp, 12")

					for i, (symbol, info) in enumerate(symbols_to_add.items()):
						end_of_func_offset = i*4
						
						self.instr(info["beforeinstr"])
						self.instr(f"push DWORD [{info['address']}]")

						self.instr(f"mov eax, [{heapvar_label}]")
						self.instr(f"add eax, {funcsize_label}+{end_of_func_offset}")
						self.instr("pop DWORD [eax]")

					self.instr(f"push {total_mem_label}")
					self.instr(f"push DWORD [{heapvar_label}]")
					self.instr("lea eax, [_HeapFuncProtect] ; no-optimize")
					self.instr("call eax")
					self.instr("add esp, 8")

					self.instr(f"mov eax, [{heapvar_label}]")

					self.outer.reload_counter()
				else:
					self.outer.collected_info+=f"  Anonymous Function (label with counter @ {self.outer.hidden_counter}) takes {params}\n"

					func = FunctionCompiler(params, body, self.source, self.outer)
					func_asm_body = func.traverse()
					func_name = f"anonymous.{self.outer.hidden_counter}"
					self.outer.reload_counter()

					self.outer.instr(f"{func_name}:")
					self.outer.instr(func_asm_body, unprocessed=func.text)

					self.instr(f"mov eax, {func_name}")

			elif key.startswith("String Literal"):
				strname = f"string.{self.outer.hidden_counter}"
				chars = ', '.join(str(ord(c)) for c in node)
				self.outer.datainstr(f"{strname} db {chars}, 0 ; string {node!r}")
				self.instr(f"mov eax, {strname} ; string {node!r}")

				self.outer.reload_counter()
			elif key.startswith("Function Call"):
				self.call_func(node)
			elif key.startswith("Array Literal"):
				self.make_arr_literal(node)
			elif key.startswith("Property Access"):
				return self.access_prop(node, getfuncaddr=getfuncaddr, propassign=propassign)
			elif key.startswith("Expression"):
				self.generate_expression(node, getfuncaddr=getfuncaddr)
			elif key.startswith("Exec-Expression"):
				self.traverse(node)
			elif key.startswith("Verify-Imported"):
				if node[0] not in self.outer.imported_names:
					throw(f"(fatal) UTSC 311: You must import '{node[0]}' in order to use {node[1]}")
					return
			else:
				throw(f"(fatal) UTSC 308: Invalid target for expression '{key}'")
				return
	
	def try_ns(self, expr: dict[str, dict], name: str, ns_heirarchy: list=None):
		ns_heirarchy = [] if ns_heirarchy is None else ns_heirarchy

		for key, node in expr.items():
			if key.startswith("Property Access"):
				ns_heirarchy.append(node["name"])
				if not self.try_ns(node["expr"], name, ns_heirarchy): return False
				break

			if key.startswith("Variable Reference"):
				ns_heirarchy.append(node["name"])
				break

			return False
			
		return '.'.join(ns_heirarchy[::-1]+[name])

	def access_prop(self, node: dict, getfuncaddr: bool=False, propassign: bool=False):
		expr: dict[str, dict] = node["expr"]
		name: str = node["name"]

		# try to see if it is a namespace:
		qual_name = self.try_ns(expr, name)

		if qual_name in self.outer.symbols.symbols.keys():
			self.reference_var(qual_name, 0, getfuncaddr=getfuncaddr)
			return

		if expr.get("Variable Reference") is not None:
			var = expr["Variable Reference"]

			try: dtype: str = self.symbols.get(var["name"], var["index"], qual_name)["type"]
			except TypeError: return # var was not found, thrown on utils.py side

			if dtype.startswith(("CONST ", "LET ")):
				if dtype.startswith("LET "):
					struct_type = dtype.removeprefix("LET ")
				else:
					struct_type = dtype.removeprefix("CONST ")

				if struct_type not in self.outer.structs.keys():
					code = get_code(self.source, var["index"])

					throw(f"UTSC 307: Struct '{struct_type}' does not exist!", code)
					return

				try: member_offset = self.outer.structs[struct_type].index(name)*4
				except ValueError: # member name not in list
					code = get_code(self.source, var["index"])

					throw(f"UTSC 307: Member '{name}' does not exist on struct '{struct_type}'", code)
					return

				self.reference_var(var["name"], var["index"])
				self.instr(f"add eax, {member_offset}")
				self.instr("mov eax, [eax]")
				return

		# otherwise, it is a dynamic object, manually call the get function

		if propassign: # if assigning, call the set function
			self.generate_expression({ "String Literal": name})
			self.instr("push eax")
			if ("Variable Reference" not in expr) and ("Property Access" not in expr) and ("Addr Operation deref" not in expr):
				code = get_code(self.source, node["index"])
				throw(f"UTSC 313: Cannot assign property '{name}' to the given expression", code)
				return
			
			self.generate_expression(
				{ "Addr Operation ref" : { "expr": expr } },
				passqual=qual_name,
				noopt=True
			)
			self.instr("push DWORD eax")
			self.instr("mov eax, [eax]")
			self.instr("call [eax+4]")
			self.instr("add esp, 12")
			return True

		self.generate_expression({ "String Literal": name })
		self.instr("push eax")
		self.generate_expression(expr, passqual=qual_name, noopt=True)
		self.instr("push eax")
		self.instr("call [eax]")
		self.instr("add esp, 8")
		self.instr("mov eax, [eax]")

	def make_arr_literal(self, vals: list[dict]):
		# again, we use the constant 4 for 32-bit, but 64-bit needs 8
		self.allocated_bytes+=((len(vals)+1)*4) # total space needed
		arr_addr = current_off = self.allocated_bytes

		addr = f"ebp-{current_off}"

		for val in vals:
			self.generate_expression(val)
			self.instr(f"mov [{addr}], eax")

			current_off-=4
			addr = f"ebp-{current_off}"

		self.instr(f"lea eax, [ebp-{arr_addr}]")

	def reference_var(self, name: str, index: int, getfuncaddr: bool=False, passqual: str=None, noopt: bool=False):
		try:
			info = self.symbols.get(name, index, passqual)
			memaddr = info["address"]
			self.instr(info["beforeinstr"])
		except TypeError: return # doesn't exist, error was thrown on utils.py side, just exit compilation

		if getfuncaddr:
			if memaddr.startswith("ebp"): # if it is a stack address
				self.instr(f"mov eax, [{memaddr}]")
				return

			self.instr(f"lea eax, [{memaddr}]")
			return

		self.instr(f"mov eax, [{memaddr}]{' ; no-optimize' if noopt else ''}")

	def call_func(self, node: dict):
		addr: dict = node["addr"]
		args: list[dict] = node["arguments"]

		for arg in args[::-1]: # reverse args
			self.generate_expression(arg)
			self.instr("push eax")

		self.generate_expression(addr, getfuncaddr=True)

		if self.localonly_offset_label: self.instr("; <create-later [localonly-add-to-offset]>")

		self.instr("call eax") # address will be stored in eax
		self.instr(f"add esp, {4*len(args)}")

		if self.localonly_offset_label: self.instr("; <create-later [localonly-sub-from-offset]>")

		self.outer.collected_info+=f"Function of expr {addr} called with {args}\n"

	#The two methods below allocate memory for the
	#variable and place it in a symbol table
	def declare_variable(self, node: dict):
		name: str = node["name"]
		_type: str = node["type"]

		self.symbols.declare(name, _type, 4, f"ebp-{self.allocated_bytes+4}")

		self.allocated_bytes+=4

	def define_variable(self, node: dict):
		name: str = node["name"]
		_type: str = node["type"]
		value: dict = node["value"]
		index: int = node["index"]

		#add instrs
		self.symbols.declare(name, _type, 4, f"ebp-{self.allocated_bytes+4}")
		memaddr = self.symbols.assign(name, value, index)
		self.generate_expression(value)
		self.instr(f"mov [{memaddr}], eax")

		if value.get("String Literal"):
			self.outer.collected_info+=f"  Local var '{name}' declared as a {_type} string ({value['String Literal']!r})\n"
		elif value.get("Numerical Constant"):
			self.outer.collected_info+=f"  Local var '{name}' declared as a {_type} int/float ({value['Numerical Constant']})\n"

		self.allocated_bytes+=4
	#

	def assign_to_addr(self, node: dict):
		addr: dict[str, dict] = node["addr"]
		value: dict[str, dict] = node["value"]

		self.generate_expression(value)
		self.instr("push eax")
		if self.generate_expression(addr, propassign=True): return # the setter has been called and completed the assignment for us
		self.remove_last_instr()
		self.instr(f"pop DWORD [eax]")

	def assign_variable(self, node: dict):
		name = node["name"]
		value: dict[str, dict] = node["value"]
		index = node["index"]

		memaddr = self.symbols.assign(name, value, index)

		self.generate_expression(value)

		self.instr(f"mov [{memaddr}], eax")

		if value.get("String Literal"):
			self.outer.collected_info+=f"  Local var '{name}' now has string value ({value['String Literal']!r})\n"
		elif value.get("Numerical Constant"):
			self.outer.collected_info+=f"  Local var '{name}' now has int/float value ({value['Numerical Constant']})\n"

	def generate_prolog(self):
		self.outer.datainstr(f"{self.allocated_bytes_label} equ {self.allocated_bytes}")
		return f"push ebp\n\tmov ebp, esp\n\tsub esp, {self.allocated_bytes}"

	def generate_epilog(self):
		if self.allocated_bytes:
			return f"mov esp, ebp\n\tpop ebp\n\tret"

		return "; <add-later? [check-allocated-bytes]>\n\tpop ebp\n\tret"

	def return_val(self, expr: dict):
		if expr is None: self.instr("xor eax, eax")
		else: self.generate_expression(expr) # this auto places the val in eax

		self.instr(self.generate_epilog()) # place epilog here

	def generate_conditional(self, conditional: dict):
		condition: dict = conditional["condition"]
		if_body: dict = conditional["if"]
		else_body: dict = conditional["else"]

		iflabel = f".if.{self.outer.hidden_counter}"
		elselabel = f".else.{self.outer.hidden_counter}"
		contlabel = f".cont.{self.outer.hidden_counter}"
		self.outer.reload_counter()

		self.generate_expression(condition)
		self.instr("cmp eax, 0") # then jump to labels from here
		self.instr(f"jne {iflabel}")
		self.instr(f"jmp {elselabel}")

		self.instr(f"{iflabel}:")
		self.traverse(if_body)
		self.instr(f"jmp {contlabel}")
		self.instr(f"{elselabel}:")
		self.traverse(else_body)		
		self.instr(f"{contlabel}:")

	def generate_while(self, node: dict):
		condition: dict = node["condition"]
		body: dict = node["body"]

		whilelabel = f".while.{self.outer.hidden_counter}"
		contlabel = f".cont.{self.outer.hidden_counter}"
		self.outer.reload_counter()

		self.instr(f"{whilelabel}:")
		self.generate_expression(condition)
		self.instr("cmp eax, 0")
		self.instr(f"je {contlabel}")
		self.traverse(body)
		self.instr(f"jmp {whilelabel}")
		self.instr(f"{contlabel}:")

	def process_text(self):
		processed = self.text.replace(
			"; <create-later [localonly-add-to-offset]>",
			f"add DWORD [{self.localonly_offset_label}], {self.localonly_amount+(self.last_arg_offset-8)+self.allocated_bytes}"
		)

		processed = processed.replace(
			"; <create-later [localonly-sub-from-offset]>",
			f"sub DWORD [{self.localonly_offset_label}], {self.localonly_amount+(self.last_arg_offset-8)+self.allocated_bytes}"
		)

		processed = processed.replace(
			"; <add-later? [check-allocated-bytes]>",
			"mov esp, ebp" if self.allocated_bytes else ""
		)

		return '\n'.join(line for line in processed.splitlines() if line.strip())

	#Traverses the AST and passes off each node to a specialized function
	def traverse(self, top: dict=None):
		key: str; node: dict
		
		top = top if top is not None else self.body	

		for key, node in top.items():
			if key.startswith("Expression"):
				self.traverse(node)
			elif key.startswith("Variable Declaration"):
				self.declare_variable(node)
			elif key.startswith("Variable Definition"):
				self.define_variable(node)
			elif key.startswith("Variable Assignment"):
				self.assign_variable(node)
			elif key.startswith("Addr Assignment"):
				self.assign_to_addr(node)
			elif key.startswith("Function Call"):
				self.call_func(node)
			elif key.startswith("Return Statement"):
				self.return_val(node)
			elif key.startswith("Conditional Statement"):
				self.generate_conditional(node)
			elif key.startswith("While Loop"):
				self.generate_while(node)
			else:
				throw(f"(fatal) UTSC 305: Unimplemented or Invalid AST Node '{key}'")
				return
			
		if top is self.body: self.text = f"\t{self.generate_prolog()}\n\t{self.text}" # not need to add epilog; it should have already been added by a return statement

		return self.process_text()