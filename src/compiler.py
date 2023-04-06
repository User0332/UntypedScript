from utils import (
	get_code,
	throw,
	warn,
	SymbolTable,
	SigNonConstantNumericalExpressionException
)

from ast_preprocessor import SyntaxTreePreproccesor

from os import remove as os_remove
from os.path import isfile, normpath, dirname, basename
from sys import platform as sys_platform
from subprocess import call as subproc_call

class Compiler:
	def __init__(self, ast: dict, code: str, compiler_path: str, file_path: str, optimize: int, structs: dict):
		self.ast = ast
		self.top = ""
		self.text = "section .text"
		self.bss = "section .bss"
		self.data = "section .data"
		self.symbols = SymbolTable(code)
		self.evaluator = SyntaxTreePreproccesor(ast)
		self.source = code
		self.structs: dict[str, list[str]] = structs
		self.hidden_counter = 0
		self.optimize = optimize
		self.compiler_path = compiler_path+'/..' if compiler_path.endswith("src") else compiler_path # this will point to the src folder, we want it to point to root proj directory
		self.file_path = file_path
		self.link_with: list[str] = []
		self.exports: list[str] = []
		self.imports: list[str] = []
		self.imported_names: list[str] = []
		self.in_namespace: list[str] = []

		# add more options - i.e. architecture from cmd line args
		self.platform = "win32" if sys_platform == "win32" else "elf32"

	@property
	def asm(self) -> str:
		return f"{self.top}\n\n{self.bss}\n\n{self.text}\n\n{self.data}"

	def instr(self, instruction: str):
		self.text+=f"\n{instruction}"

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

			func_compiler = FunctionCompiler(
				value["parameters"],
				value["body"],
				self.source,
				self
			)

			func_code = func_compiler.traverse()

			self.instr(f"_{name}:")
			self.instr(func_code)
		elif value.get("String Literal") is not None:
			value = ', '.join(str(ord(c)) for c in value["String Literal"])

			self.datainstr(f"_{name} db {value}, 0")
		else:
			try: value = eval(self.evaluator.simplify_numerical_expression(value))
			except SigNonConstantNumericalExpressionException:
				code = get_code(self.source, index)
				throw("UTSC 303: Only constant numerical/function/string values allowed in global scope", code)

			self.datainstr(f"_{name} dd {value}")
	#

	def make_namespace(self, node: dict):
		name: str = node["name"]
		code: dict = node["body"]

		self.in_namespace+=name.split('.') # step in
		self.traverse(code)

		for _ in range(len(name.split('.'))): self.in_namespace.pop(-1) # step out

	def import_names(self, node: dict):
		names: list[str] = node["names"]
		module = node["module"]

		do_not_add_to_link_with: list[str] = []

		uts_mod = f"{self.file_path}/{module}.uts"
		sym_exp_mod = f"{module}.exports"
		asm_mod = f"{self.file_path}/{module}.asm"
		lib_uts_mod = f"{self.compiler_path}/lib/{module}.uts"
		lib_sym_exp_mod = f"{self.compiler_path}/lib/{module}.exports"
		lib_obj_mod = normpath(f"{self.compiler_path}/lib/{module}.o")
		obj_mod = normpath(f"{self.file_path}/{module}.o")

		if (not isfile(uts_mod) and isfile(lib_uts_mod)):
			uts_mod = lib_uts_mod
			sym_exp_mod = lib_sym_exp_mod
			obj_mod = lib_obj_mod

		if sys_platform == "win32":
			shell = ["powershell"]
		else:
			shell = ["bash", "-c"]

		if (isfile(uts_mod)): # if a .uts file, compile it
			try:
				subproc_call([*shell, "utsc", "-o", sym_exp_mod, uts_mod, f"-O{self.optimize}"])
				
				try:
					with open(sym_exp_mod, 'r') as f:
						exports = f.read().splitlines()

					with open(sym_exp_mod+".modules", 'r') as f:
						imports = f.read().splitlines()
				except FileNotFoundError:
					raise ZeroDivisionError() # some random error to catch

				for name in exports:
					if name in self.symbols.symbols:
						throw(f"UTSC 309: Name '{name}' was defined twice while trying to import from '{module}'")

				for module in imports:
					if module in self.imports:
						do_not_add_to_link_with.append(module)
			except ZeroDivisionError:
				warn(f"UTSC 310: Could not check for symbol clashes while importing '{module}'")
			except OSError:
				throw(f"UTSC 301: Module '{module}' could not be compiled - utsc is not in PATH.")

			try:
				os_remove(sym_exp_mod)
				os_remove(sym_exp_mod+".modules")
			except FileNotFoundError: pass

			subproc_call([*shell, "utsc", "-o", obj_mod, uts_mod, f"-O{self.optimize}"])
		elif module != "<libc>": warn(f"UTSC 310: Could not check for symbol clashes while importing '{module}'")

		# make compiler config with NASM and GCC paths/ configured shell to use later
		if (isfile(asm_mod)):
			try: subproc_call([*shell, "nasm", "-f", self.platform, "-o", obj_mod, asm_mod])
			except OSError:
				throw(f"UTSC 301: Module '{module}' could not be compiled - nasm is not in PATH.")

		if isfile(obj_mod): self.link_with.append(obj_mod)
		elif module != "<libc>": # if module doesn't exist...
			code = get_code(self.source, node["index"])

			throw(f"UTSC 302: Module '{module}' doesn't exist!", code)

		for name in names:
			self.topinstr(f"extern _{name}")

			self.symbols.declare(name, "CONST", 4, f"_{name}")

			self.imported_names.append(name)

		self.imports.append(module)

		for linked_with in self.link_with:
			if basename(linked_with).removesuffix(".o") in do_not_add_to_link_with:
				self.link_with.remove(linked_with)

	def import_ns(self, node: dict ):
		ns_names: list[str] = node["names"]
		module: module = node["module"]
		idx: int = node["index"]

		do_not_add_to_link_with: list[str] = []

		uts_mod = f"{self.file_path}/{module}.uts"
		sym_exp_mod = f"{module}.exports"
		lib_uts_mod = f"{self.compiler_path}/lib/{module}.uts"
		lib_sym_exp_mod = f"{self.compiler_path}/lib/{module}.exports"
		lib_obj_mod = normpath(f"{self.compiler_path}/lib/{module}.o")
		obj_mod = normpath(f"{self.file_path}/{module}.o")

		for ns in ns_names:
			if (not isfile(uts_mod) and isfile(lib_uts_mod)):
				uts_mod = lib_uts_mod
				sym_exp_mod = lib_sym_exp_mod
				obj_mod = lib_obj_mod

			if sys_platform == "win32":
				shell = ["powershell"]
			else:
				shell = ["bash", "-c"]

			if not (isfile(uts_mod)):
				print(uts_mod)
				code = get_code(self.source, idx)
				throw("UTSC 312: Cannot import namespace from a non-UntypedScript file (you can only import namespaces from .uts files).", code)
				return
			try:
				subproc_call([*shell, "utsc", "-o", sym_exp_mod, uts_mod, f"-O{self.optimize}"])
				
				try:
					with open(sym_exp_mod, 'r') as f:
						exports = f.read().splitlines()

					with open(sym_exp_mod+".modules", 'r') as f:
						imports = f.read().splitlines()
				except FileNotFoundError:
					raise ZeroDivisionError() # some random error to catch
				
				names: list[str] = []

				for name in exports:
					if name in self.symbols.symbols:
						throw(f"UTSC 309: Name '{name}' was defined twice while trying to import from '{module}'")

					if name.startswith(f"{ns}."): names.append(name)

				for module in imports:
					if module in self.imports:
						do_not_add_to_link_with.append(module)
			except ZeroDivisionError:
				warn(f"UTSC 310: Could not check for symbol clashes while importing '{module}'")
			except OSError:
				throw(f"UTSC 301: Module '{module}' could not be compiled - utsc is not in PATH.")
				return
			
			try:
				os_remove(sym_exp_mod)
				os_remove(sym_exp_mod+".modules")
			except FileNotFoundError: pass

			subproc_call([*shell, "utsc", "-o", obj_mod, uts_mod, f"-O{self.optimize}"])
			
			warn(f"UTSC 310: Could not check for symbol clashes while importing '{module}'")

			if not isfile(obj_mod):
				code = get_code(self.source, node["index"])

				throw(f"UTSC 311: Object file for '{module}' disappeared!", code)

			self.link_with.append(obj_mod)

			for name in names:
				self.topinstr(f"extern _{name}")

				self.symbols.declare(name, "CONST", 4, f"_{name}")

				self.imported_names.append(name)

			self.imports.append(module)

			for linked_with in self.link_with:
				if basename(linked_with).removesuffix(".o") in do_not_add_to_link_with:
					self.link_with.remove(linked_with)

	def export_names(self, node: list[str]):
		for name in node:
			self.topinstr(f"global _{name}")
			self.exports.append(name)

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
				elif key.startswith("Export"):
					self.export_names(node)
					continue
				elif key.startswith("Namespace Export"):
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
	def __init__(self, params: dict[str, str], body: dict, code: str, outer: Compiler):
		self.text = ""
		self.body = body
		self.allocated_bytes = 0
		self.symbols = SymbolTable(code, outer.symbols)
		self.source = code
		self.outer = outer
		self.params = params
		self.post_prolog = ""

		arg_offset = 8
		for param, dtype in params.items(): # reserve space for each arg
			addr = f"ebp+{arg_offset}"

			self.symbols.declare(param, dtype, 4, addr)

			arg_offset+=4

	def instr(self, instr: str):
		self.text+=f"\n\t{instr}"

	def remove_last_instr(self):
		instr = self.text.splitlines()[-1]
		self.text = '\n'.join(self.text.splitlines()[:-1])
		return instr

	def generate_expression(self, expr: dict, getfuncaddr: bool=False, propassign: bool=False):
		key: str; node: dict

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
					self.instr("idiv ebx")
					self.instr("mov eax, edx")
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
				self.reference_var(node["name"], node["index"], getfuncaddr=getfuncaddr)
			elif key.startswith("Anonymous Function"):
				params: dict[str, str] = node["parameters"]
				body: dict = node["body"]

				func = FunctionCompiler(params, body, self.source, self.outer)
				func_asm_body = func.traverse()
				func_name = f"anonymous.{self.outer.hidden_counter}"

				self.outer.instr(f"{func_name}:")
				self.outer.instr(func_asm_body)

				self.instr(f"mov eax, {func_name}")

				self.outer.hidden_counter+=1
			elif key.startswith("String Literal"):
				strname = f"string.{self.outer.hidden_counter}"
				node = ', '.join(str(ord(c)) for c in node)
				self.outer.datainstr(f"{strname} db {node}, 0")
				self.instr(f"mov eax, {strname}")

				self.outer.hidden_counter+=1
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

			try: dtype: str = self.symbols.get(var["name"], var["index"])["type"]
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
				{ "Addr Operation ref" : {"expr": expr } }
			)
			self.instr("push DWORD eax")
			self.instr("mov eax, [eax]")
			self.instr("call [eax+4]")
			self.instr("add esp, 12")
			return True	

		self.generate_expression({ "String Literal": name})
		self.instr("push eax")
		self.generate_expression(expr)
		self.instr("push eax")
		self.instr("call [eax]")
		self.instr("add esp, 8")
		self.instr("mov eax, [eax]")

	def make_arr_literal(self, vals: list[dict]):
		# again, we use the constant 4 for 32-bit, but 64-bit needs 8
		self.allocated_bytes+=(len(vals)*4) # total space needed
		end = self.allocated_bytes+4

		start = f"ebp-{end}"
		addr = start

		for val in vals:
			self.generate_expression(val)
			self.instr(f"mov [{addr}], eax")

			end-=4
			addr = f"ebp-{end}"

		self.instr(f"lea eax, [{start}]")

	def reference_var(self, name: str, index: int, getfuncaddr: bool=False):
		try: memaddr: str = self.symbols.get(name, index)["address"]
		except TypeError: return # doesn't exist, error was thrown on utils.py side, just exit compilation

		if getfuncaddr:
			if memaddr.startswith("ebp"): # if it is a stack address
				self.instr(f"mov eax, [{memaddr}]")
				return

			self.instr(f"lea eax, [{memaddr}]")
			return

		self.instr(f"mov eax, [{memaddr}]")

	def call_func(self, node: dict):
		addr: dict = node["addr"]
		args: list[dict] = node["arguments"]

		for arg in args[::-1]: # reverse args
			self.generate_expression(arg)
			self.instr("push eax")

		self.generate_expression(addr, getfuncaddr=True)

		self.instr("call eax") # address will be stored in eax
		self.instr(f"add esp, {4*len(args)}")

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
		value = node["value"]
		index = node["index"]

		memaddr = self.symbols.assign(name, value, index)

		self.generate_expression(value)

		self.instr(f"mov [{memaddr}], eax")

	def generate_prolog(self):
		return f"push ebp\n\tmov ebp, esp\n\tsub esp, {self.allocated_bytes}"

	def generate_epilog(self):
		# is f"add esp, {self.allocated_bytes}\n\t" needed?
		if self.allocated_bytes:
			return f"mov esp, ebp\n\tpop ebp\n\tret"

		return "pop ebp\n\tret"

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
		self.outer.hidden_counter+=1

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
		self.outer.hidden_counter+=1

		self.instr(f"{whilelabel}:")
		self.generate_expression(condition)
		self.instr("cmp eax, 0")
		self.instr(f"je {contlabel}")
		self.traverse(body)
		self.instr(f"jmp {whilelabel}")
		self.instr(f"{contlabel}:")

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

		return f"\t{self.generate_prolog()}\n\t{self.text}\n\t{self.generate_epilog()}"