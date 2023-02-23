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
	def __init__(self, ast: dict, code: str, compiler_path: str, file_path: str, optimize: int):
		self.ast = ast
		self.top = ""
		self.text = "section .text"
		self.bss = "section .bss"
		self.data = "section .data"
		self.symbols = SymbolTable(code)
		self.evaluator = SyntaxTreePreproccesor(ast)
		self.source = code
		self.hidden_counter = 0
		self.optimize = optimize
		self.compiler_path = compiler_path+'/..' if compiler_path.endswith("src") else compiler_path # this will point to the src folder, we want it to point to root proj directory
		self.file_path = file_path
		self.link_with: list[str] = []
		self.exports: list[str] = []
		self.imports: list[str] = []

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
		name: str = node["name"]
		_type: str = node["type"]

		self.bssinstr(f"_{name} resb 4")
		self.symbols.declare(name, _type, 4, f"_{name}")

	def define_variable(self, node: dict):
		name: str = node["name"]
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

			self.datainstr(f"_{name} db {value}")
	#

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

		self.imports.append(module)

		for linked_with in self.link_with:
			if basename(linked_with).removesuffix(".o") in do_not_add_to_link_with:
				self.link_with.remove(linked_with)

	def export_names(self, node: list[str]):
		for name in node:
			self.topinstr(f"global _{name}")
			self.exports.append(name)

	#Traverses the AST and passes off each node to a specialized function
	def traverse(self, top: dict=None):
		key: str; node: dict
		
		top = top if top is not None else self.ast

		for key, node in top.items():
			if key.startswith("Expression"):
				self.traverse(node)
			elif key.startswith("Import"):
				self.import_names(node)
			elif key.startswith("Export"):
				self.export_names(node)
			elif key.startswith("Variable Declaration"):
				self.declare_variable(node)
			elif key.startswith("Variable Definition"):
				self.define_variable(node)
			elif key.startswith("Variable Assignment"):
				code = get_code(self.source, node["index"])
				throw("UTSC 304: Assignments not allowed in global scope.", code)
			else:
				throw(f"UTSC 305: Unimplemented or Invalid AST Node '{key}' (global scope)")

		return self.asm
	#
#

class FunctionCompiler(Compiler):
	def __init__(self, params: list[str], body: dict, code: str, outer: Compiler):
		self.text = ""
		self.body = body
		self.allocated_bytes = 0
		self.symbols = SymbolTable(code, outer.symbols)
		self.source = code
		self.outer = outer
		self.params = params
		self.post_prolog = ""

		arg_offset = 8
		for param in params: # reserve space for each arg
			addr = f"ebp+{arg_offset}"

			self.symbols.declare(param, "LET", 4, addr)

			arg_offset+=4

	def instr(self, instr: str):
		self.text+=f"\n\t{instr}"

	def generate_expression(self, expr: dict):
		key: str; node: dict

		for key, node in expr.items():
			if key.startswith("Binary Operation"):
				op = key.removeprefix("Binary Operation ")

				self.generate_expression(node[0])
				self.instr("push eax") #save result
				self.generate_expression(node[1])
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
					self.generate_expression(node)
					self.instr("neg eax")
				elif op == "not":
					self.generate_expression(node)
					self.instr("cmp eax, 0")
					self.instr("sete al")
					self.instr("movzx eax, al")
			elif key.startswith("Addr Operation"):
				op = key.removeprefix("Addr Operation ")

				if op == "ref":
					self.reference_var(node["name"], node["index"], lea=True)
				elif op == "deref":
					self.generate_expression(node)
					self.instr("mov eax, [eax]")
			elif key.startswith("Numerical Constant"):
				self.instr(f"mov eax, {node}")
			elif key.startswith("Variable Reference"):
				self.reference_var(node["name"], node["index"])
			elif key.startswith("Anonymous Function"):
				params: list[str] = node["parameters"]
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
			else:
				throw(f"UTSC 308: Invalid target for expression '{key}'")

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

	def reference_var(self, name: str, index: int, lea: bool=False):
		try: memaddr = self.symbols.get(name, index)["address"]
		except TypeError: return # doesn't exist, error was thrown on utils.py side, just exit compilation

		if lea:
			self.instr(f"lea eax, [{memaddr}]")
			return

		self.instr(f"mov eax, [{memaddr}]")

	def call_func(self, node: dict):
		name: str = node["name"]
		args: list[dict] = node["arguments"]
		index: int = node["index"]

		try: addr: str = self.symbols.get(name, index)["address"] # make sure func exists
		except TypeError: return # doesn't exist, error was thrown on utils.py side, just exit compilation
		
		if addr.startswith("ebp"): # if addr stored on stack ptr, dereference the ptr
			addr = f"[{addr}]"

		for arg in args[::-1]: # reverse args
			self.generate_expression(arg)
			self.instr("push eax")

		self.instr(f"call {addr}")
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
			elif key.startswith("Function Call"):
				self.call_func(node)
			elif key.startswith("Return Statement"):
				self.return_val(node)
			elif key.startswith("Conditional Statement"):
				self.generate_conditional(node)
			elif key.startswith("While Loop"):
				self.generate_while(node)
			else:
				throw(f"UTSC 305: Unimplemented or Invalid AST Node '{key}'")

		return f"\t{self.generate_prolog()}\n\t{self.text}\n\t{self.generate_epilog()}"