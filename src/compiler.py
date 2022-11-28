from utils import (
	get_code,
	throw,
	SymbolTable,
	NonConstantNumericalExpressionException
)

from ast_preprocessor import SyntaxTreePreproccesor

class Compiler:
	def __init__(self, ast: dict, code: str):
		self.ast = ast
		self.top = ""
		self.text = "section .text"
		self.bss = "section .bss"
		self.data = "section .data"
		self.symbols = SymbolTable(code)
		self.evaluator = SyntaxTreePreproccesor(ast)
		self.source = code
		self.hidden_counter = 0

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
		dtype: str = node["type"]

		self.bssinstr(f"_{name} resb 4")
		self.symbols.declare(name, dtype, 4, f"_{name}")

	def define_variable(self, node: dict):
		name: str = node["name"]
		dtype: str = node["type"]
		value: dict = node["value"]
		index: int = node["index"]

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
			except NonConstantNumericalExpressionException:
				code = get_code(self.source, index)
				throw("UTSC 022: Only constant numerical/function/string values allowed in global scope", code)

			self.datainstr(f"_{name} db {value}")

		self.symbols.declare(name, dtype, 4, f"_{name}")
		self.symbols.assign(name, value, index)
	#

	#Traverses the AST and passes off each node to a specialized function
	def traverse(self, top: dict=None):
		key: str; node: dict
		
		top = top if top is not None else self.ast

		for key, node in top.items():
			if key.startswith("Expression"):
				self.traverse(node)
			elif key.startswith("Import"):
				name = node["name"]
				module = node["module"]
				# check for file/module, for now, just pass libc
				if module != "<libc>":
					code = get_code(self.source, node["index"])

					throw(f"UTSC 020: Module '{module}' doesn't exist!", code)

				self.topinstr(f"extern _{name}")

				self.symbols.declare(name, "CONST", 4, f"_{name}")
			elif key.startswith("Export"):
				self.topinstr(f"global _{node}")
			elif key.startswith("Variable Declaration"):
				self.declare_variable(node)
			elif key.startswith("Variable Definition"):
				self.define_variable(node)
			elif key.startswith("Variable Assignment"):
				code = get_code(self.source, node["index"])
				throw("UTSC 023: Assingments not allowed in global scope.", code)
			else:
				throw("UTSC 025: Unimplemented or Invalid AST Node... ?")

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

		for param in params:
			pass # declare each param in func scope

	def instr(self, instr: str):
		self.text+=f"\n\t{instr}"

	def generate_expression(self, expr: dict):
		key: str; node: dict

		for key, node in expr.items():
			if key.startswith("Binary Operation"):
				op = key.removeprefix("Binary Operation ")

				self.generate_expression(node[0])
				self.instr("mov ebx, eax") #save result
				self.generate_expression(node[1])

				if op == "/": #integer division
					self.instr("push eax")
					self.instr("mov eax, ebx")
					self.instr("pop ebx")
					self.instr("idiv ebx")
				elif op == "%": #modulo
					self.instr("push eax")
					self.instr("mov eax, ebx")
					self.instr("pop ebx")
					self.instr("idiv ebx")
					self.instr("mov eax, edx")
				else:
					if op == "+": #addition
						self.instr("add ebx, eax")
					elif op == "-": #subtraction
						self.instr("sub ebx, eax")
					elif op == "*": #integer multiplication
						self.instr("imul ebx, eax")

					self.instr("mov eax, ebx")
			elif key.startswith("Unary Operation"):
				op = key.removeprefix("Unary Operation ")
				if op == "-":
					self.generate_expression(node)
					self.instr("neg eax")
			elif key.startswith("Numerical Constant"):
				if node == 0:
					self.instr(f"xor eax, eax")
					continue
				self.instr(f"mov eax, {node}")
			elif key.startswith("Variable Reference"):
				# FIX: this throws error if var doesn't exist...
				name = node["name"]
				index  = node["index"]

				memaddr = self.symbols.get(name, index)["address"]
				self.instr(f"mov eax, [{memaddr}]")
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

	def call_func(self, node: dict):
		name: str = node["name"]
		args: list[dict] = node["arguments"]
		index: int = node["index"]

		addr: str = self.symbols.get(name, index)["address"] # make sure func exists

		if addr.startswith("esp"): # if addr stored on stack ptr, dereference the ptr
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
		dtype: str = node["type"]

		start = self.allocated_bytes
		self.allocated_bytes+=4

		#add instrs
		self.symbols.declare(name, dtype, 4, f"esp+{start}")

	def define_variable(self, node: dict):
		name: str = node["name"]
		dtype: str = node["type"]
		value: dict = node["value"]
		index: int = node["index"]

		start = self.allocated_bytes
		self.allocated_bytes+=4


		#add instrs
		self.symbols.declare(name, dtype, 4, f"esp+{start}")
		memaddr = self.symbols.assign(name, value, index)
		self.generate_expression(value)
		self.instr(f"mov [{memaddr}], eax")
	#

	def assign_variable(self, node: dict):
		name = node["name"]
		value = node["value"]
		index = node["index"]

		memaddr = self.symbols.assign(name, value, index)

		self.generate_expression(value)

		self.instr(f"mov [{memaddr}], eax")

	def generate_epilog(self):
		return f"add esp, {self.allocated_bytes+8}\n\tpop esi\n\tpop ebx\n\tret"

	def generate_prolog(self):
		return f"push ebx\n\tpush esi\n\tsub esp, {self.allocated_bytes+8}"

	def return_val(self, expr: dict):
		if expr is None: self.instr("xor eax, eax")
		else: self.generate_expression(expr) # this auto places the val in eax

		self.instr(self.generate_epilog()) # place epilog here

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
			else:
				throw("UTSC 025: Unimplemented or Invalid AST Node... ?")

		return f"\t{self.generate_prolog()}\n\t{self.text}\n\t{self.generate_epilog()}"