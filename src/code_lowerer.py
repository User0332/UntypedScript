from utils import throw, get_code
from json import dumps
from ast_preprocessor import SyntaxTreePreproccesor, SigNonConstantNumericalExpressionException
from typing import Union

class CodeLowerer:
	def __init__(self, ast: dict[str, Union[dict, str, list]], source: str, structs: dict[str, list[str]]):
		self.ast = ast
		self.source = source
		self.code = ""
		self.structs = structs
		self.struct_vars = dict[str, str]()

	def gen_expr_wrap(self, expr: dict):
		self.code+='('
		self.generate_expression(expr)
		self.code+=')'

	def generate_expression(self, expr: dict):
		key: str; node: dict

		for key, node in expr.items():
			if key.startswith("Binary Operation"):
				self.gen_expr_wrap(node[0])
				self.code+=key.removeprefix("Binary Operation ")
				self.gen_expr_wrap(node[1])
			elif key.startswith("Unary Operation"):
				self.code+=key.removeprefix("Unary Operation ")
				self.gen_expr_wrap(node)
			elif key.startswith("Addr Operation"):
				op = key.removeprefix("Addr Operation ")

				if op == "ref":
					self.code+=f"ref {node['name']}"
				elif op == "deref":
					self.code+=f"deref "
					self.gen_expr_wrap(node)
			elif key.startswith("Numerical Constant"):
				self.code+=str(node)
			elif key.startswith("Variable Reference"):
				self.code+=node["name"]
			elif key.startswith("Anonymous Function"):
				params: dict[str, str] = node["parameters"]
				body: dict = node["body"]

				self.code+=f"""({','.join(params)}) => {{
	{FunctionLowerer(body, self.source, self.structs).lower()}
}}"""
			elif key.startswith("String Literal"):
				self.code+=dumps(node)
			elif key.startswith("Function Call"):
				self.call_func(node)
			elif key.startswith("Array Literal"):
				self.make_arr_literal(node)
			elif key.startswith("Property Access"):
				if "Variable Reference" in node["expr"]:
					name: str = node["expr"]["Variable Reference"]["name"]
					if name in self.struct_vars:
						members = self.structs[self.struct_vars[name]]
						prop = node["name"]

						if prop not in members:
							code = get_code(self.source, node["expr"]["Variable Reference"]["index"])

							throw(f"UTSC 307: Member '{name}' does not exist on struct '{self.struct_vars[name]}'", code)
							return
						
						self.code+=f"deref ({name}{'+'+str(members.index(prop)*4) if members.index(prop) else ''})"
						continue

				self.generate_expression(node["expr"])
				self.code+=f".{node['name']}"
			elif key.startswith("Expression"):
				self.gen_expr_wrap(node)
			elif key.startswith("Exec-Expression"):
				self.lower(node)
			elif key.startswith("Verify-Imported"): pass
			else:
				throw(f"(fatal) UTSC 308: Invalid target for expression '{key}'")
				return
			
	def make_arr_literal(self, vals: list[dict]):
		self.code+='['

		for val in vals:
			self.generate_expression(val)
			self.code+=','

		self.code = self.code[:-1]+']'

	def call_func(self, node: dict):
		addr: dict = node["addr"]
		args: list[dict] = node["arguments"]

		self.gen_expr_wrap(addr)
		self.code+='('

		for arg in args:
			self.generate_expression(arg)
			self.code+=','

		self.code = self.code[:-1]+')'

	def import_names(self, node: dict):
		names: list[str] = node["names"]
		module = node["module"]

		self.code+=f"import {{ {','.join(names)} }} from \"{module}\""

	def export_names(self, node: list[str]):
		self.code+=f"export {{ {','.join(node)} }}"

	def declare_variable(self, node: dict):
		name: str = node["name"]
		_type: str = node["type"]

		if _type not in ("CONST", "LET"):
			self.struct_vars[name] = _type.split()[1]

		self.code+=f"{_type.split()[0].lower()} {name}"

	def define_variable(self, node: dict):
		value: dict = node["value"]
		index: int = node["index"]

		self.declare_variable(node)
		self.code+=" = "
		self.gen_expr_wrap(value)

		if value.get("Anonymous Function") is not None: return
		elif value.get("String Literal") is not None: return
		else:
			try: SyntaxTreePreproccesor(self.ast).simplify_numerical_expression(value)
			except SigNonConstantNumericalExpressionException:
				code = get_code(self.source, index)
				throw("UTSC 303: Only constant numerical/function/string values allowed in global scope", code)

	def lower(self, top: dict=None) -> str:
		top = top if top is not None else self.ast

		for key, node in top.items():
			if key.startswith("Expression"):
				self.lower(node)
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
				throw(f"(fatal) UTSC 305: Unimplemented or Invalid AST Node '{key}' (global scope)")
				return ""
			
			self.code+='\n'
			
		return self.code

class FunctionLowerer(CodeLowerer):
	def define_variable(self, node: dict):
		value: dict = node["value"]

		self.declare_variable(node)
		self.code+=" = "
		self.gen_expr_wrap(value)

	def assign_variable(self, node: dict):
		name: str = node["name"]
		value: dict = node["value"]

		self.code+=f"{name} = "
		self.gen_expr_wrap(value)

	def assign_to_addr(self, node: dict):
		addr = node["addr"]
		value = node["value"]

		self.gen_expr_wrap(addr)
		self.code+=" = "
		self.gen_expr_wrap(value)

	def generate_conditional(self, conditional: dict):
		condition: dict = conditional["condition"]
		if_body: dict = conditional["if"]
		else_body: dict = conditional["else"]

		self.code+="if "
		self.gen_expr_wrap(condition)
		self.code+='\n{'
		self.lower(if_body)
		self.code+='}'
		
		if else_body:
			self.code+="else\n{"
			self.lower(else_body)
			self.code+='}'

	def generate_while(self, node: dict):
		condition: dict = node["condition"]
		body: dict = node["body"]

		self.code+="while "
		self.gen_expr_wrap(condition)
		self.code+='\n{'
		self.lower(body)
		self.code+='}'

	def lower(self, top: dict=None) -> str:
		top = top if top is not None else self.ast

		for key, node in top.items():
			if key.startswith("Expression"):
				self.lower(node)
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
				self.code+="return "
				self.gen_expr_wrap(node)
			elif key.startswith("Conditional Statement"):
				self.generate_conditional(node)
			elif key.startswith("While Loop"):
				self.generate_while(node)
			else:
				throw(f"(fatal) UTSC 305: Unimplemented or Invalid AST Node '{key}'")
				return ""
			
			self.code+='\n'

		return self.code