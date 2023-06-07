import sys
from types import FunctionType # for debugging

# max limit possible without crashing compiler
sys.setrecursionlimit(3800)

from json import JSONDecodeError, load, loads, dumps

from utils import (
	Token, 
	get_code,
	throw, 
	warn,
	fmt_type
)

#Node Utility Classes
class Node:
	def __init__(self, val: dict, code: str, idx: int, name: str):
		if type(val) in (int, float):
			self.inner = NumNode(val)
		elif type(val) is bool:
			self.inner =  NumNode(int(val))
		elif type(val) is str:
			self.inner = StringLiteral(val)
		elif type(val) is dict:
			self.inner = dumps(val) # this should be an expression
		else:
			self.inner = None
			code = get_code(code, idx)

			throw(f"UTSC 207: AST Expression '{name}' is not valid (is type list -> only int/float, str, bool, and dict are valid node types)!", code)

	def __repr__(self) -> str:
		return str(self.inner)

class NumNode(Node):
	def __init__(self, value: str):
		self.value = value

	def __repr__(self):
		return f'{{"Numerical Constant" : {self.value} }}'

class StringLiteral(Node):
	def __init__(self, value: str):
		self.value = value

	def __repr__(self):
		return f'{{ "String Literal": {dumps(self.value)}  }}'

class BinOpNode(Node):
	def __init__(self, left: Node, op: str, right: Node):
		self.left = left
		self.value = op
		self.right = right

	def __repr__(self):
		return f'{{ "Binary Operation {self.value}" : [{self.left}, {self.right}] }}'

class UnaryOpNode(Node):
	def __init__(self, op: str, node: Node):
		self.op = op
		self.node = node

	def __repr__(self):
		return f'{{"Unary Operation {self.op}" : {self.node} }}'

class RefOpNode(Node):
	def __init__(self, expr: Node):
		self.expr = expr

	def __repr__(self):
		return f'{{ "Addr Operation ref": {{ "expr": {self.expr} }} }}'

class DerefOpNode(Node):
	def __init__(self, addr_expr: Node):
		self.expr = addr_expr

	def __repr__(self):
		return f'{{ "Addr Operation deref": {self.expr} }}'

class VariableDeclarationNode(Node):
	def __init__(self, dtype: str, name: str):
		self.dtype = dtype
		self.name = name

	def __repr__(self):
		return f'{{"Variable Declaration" : {{ "type" : "{self.dtype}", "name" : "{self.name}" }} }}'

class VariableDefinitionNode(Node):
	def __init__(self, dtype: str, name: str, expression: Node, idx: int):
		self.dtype = dtype
		self.name = name
		self.expr = expression
		self.idx = idx

	def __repr__(self):
		return f'{{"Variable Definition" : {{ "type" : "{self.dtype}", "name" : "{self.name}", "value" : {self.expr}, "index" : {self.idx} }} }}'

# Technically this could be an addr assignment node, but it makes the program faster
class VariableAssignmentNode(Node):
	def __init__(self, name: str, expression: Node, idx: int):
		self.name = name
		self.expr = expression
		self.idx = idx

	def __repr__(self):
			return f'{{"Variable Assignment" : {{ "name" : "{self.name}", "value" : {self.expr}, "index" : {self.idx} }} }}'

class VariableAccessNode(Node):
	def __init__(self, var_tok: Token):
		self.name = var_tok.value
		self.idx = var_tok.idx

	def __repr__(self):
		return f'{{"Variable Reference": {{ "name" : "{self.name}", "index" : {self.idx} }} }}'

class AddrAssignmentNode(Node):
	def __init__(self, addr: Node, value: Node):
		self.addr = addr
		self.expr = value

	def __repr__(self):
		return f'{{ "Addr Assignment": {{ "addr": {self.addr}, "value": {self.expr} }} }}'

class ExprSubscriptNode(Node):
	def __init__(self, expr: Node, offset: Node):
		self.expr = expr
		self.offset = offset

	def __repr__(self):
		return str( # Lowered AST, code lowered - expr[offset] -> deref ( expr+(offset*4) )
			DerefOpNode(
				BinOpNode(
					self.expr,
					'+',
					BinOpNode(
						self.offset,
						'*',
						NumNode(4) # Uses constant 4, which may need to be changed for 64-bit types
					)
				)
			)
		)

class ConditionalStatementNode(Node):
	def __init__(self, condition: Node, if_body: dict, else_body: dict):
		self.condition = condition
		self.if_body = dumps(if_body)
		self.else_body = dumps(else_body)

	def __repr__(self):
		return f'{{"Conditional Statement": {{ "condition" : {self.condition}, "if" : {self.if_body}, "else" : {self.else_body} }} }}'

class WhileLoopNode(Node):
	def __init__(self, condition: Node, body: dict):
		self.condition = condition
		self.body = dumps(body)

	def __repr__(self) -> str:
		return f'{{ "While Loop": {{ "condition": {self.condition}, "body": {self.body} }} }}'

class UnimplementedNode(Node):
	def __init__(self):
		pass

	def __repr__(self):
		return '{ "Unimplemented Node" : null }'

class AnonymousFunctionNode(Node):
	NORMAL = "normal"
	LOCALLY_EXPOSED = "localonly"
	HEAP_ALLOCATED = "heapalloced"

	def __init__(self, params: dict[str, str], body: dict, flag: str=NORMAL):
		self.params = dumps(params)
		
		if tuple(body.values())[-1].get("Return Statement") is None:
			body["Expression_CompilerAddedDefaultReturn"] = loads(str(FunctionReturnStatement(None)))

		self.body = dumps(body)
		self.flag = flag
	
	def __repr__(self):
		if self.flag == AnonymousFunctionNode.HEAP_ALLOCATED:
			return f'{{ "Verify-Imported0": ["malloc", "heap-allocated functions"], "Verify-Imported1": ["memcpy", "heap-allocated functions"], "Anonymous Function" : {{ "parameters" : {self.params}, "body" : {self.body}, "type": "{self.flag}" }} }}'
		
		return f'{{"Anonymous Function" : {{ "parameters" : {self.params}, "body" : {self.body}, "type": "{self.flag}" }} }}'

class NamespaceDeclarationNode(Node):
	def __init__(self, name: str, body: dict):
		self.body = dumps(body)
		self.name = name
	
	def __repr__(self):
		return f'{{"Namespace Declaration" : {{ "body" : {self.body}, "name": "{self.name}" }} }}'

class FunctionCallNode(Node):
	def __init__(self, addr: Node, args: list[Node]):
		self.addr = addr
		self.args = args

	def __repr__(self):
		return f'{{"Function Call" : {{ "addr" : {self.addr}, "arguments" : {self.args} }} }}'

class FunctionReturnStatement(Node):
	def __init__(self, expr: Node):
		self.expr = expr if expr else NumNode(0)

	def __repr__(self):
		return f'{{ "Return Statement": {self.expr} }}'

class ImportNode(Node):
	def __init__(self, modname: str, names: list[str], idx: int):
		self.modname = dumps(modname)
		self.names = dumps(names)
		self.idx = idx

	def __repr__(self) -> str:
		return f'{{ "Import": {{ "module": {self.modname}, "names": {self.names}, "index": {self.idx} }} }}'

class ExportNode(Node):
	def __init__(self, names: list[str]):
		self.names = dumps(names)

	def __repr__(self) -> str:
		return f'{{ "Export": {self.names} }}'

class NSImportNode(Node):
	def __init__(self, modname: str, names: list[str], idx: int):
		self.modname = dumps(modname)
		self.names = dumps(names)
		self.idx = idx

	def __repr__(self) -> str:
		return f'{{ "Namespace Import": {{ "module": {self.modname}, "names": {self.names}, "index": {self.idx} }} }}'

class NSExportNode(Node):
	def __init__(self, names: list[str]):
		self.names = dumps(names)

	def __repr__(self) -> str:
		return f'{{ "Namespace Export": {self.names} }}'
	
class StructImportNode(Node):
	def __init__(self, modname: str, names: list[str], idx: int):
		self.modname = dumps(modname)
		self.names = dumps(names)
		self.idx = idx

	def __repr__(self) -> str:
		return f'{{ "Struct Import": {{ "module": {self.modname}, "names": {self.names}, "index": {self.idx} }} }}'

class ArrayLiteralNode(Node):
	def __init__(self, vals: list[Node]):
		self.vals = vals

	def __repr__(self) -> str:
		return f'{{ "Array Literal": {self.vals} }}'

class PropertyAccessNode(Node):
	def __init__(self, expr: Node, name: str, idx: int):
		self.expr = expr
		self.name = name
		self.idx = idx

	def __repr__(self) -> str:
		return f'{{ "Property Access": {{ "expr": {self.expr}, "name": "{self.name}", "index": {self.idx} }} }}'
	
class HeapAllocationNode(Node):
	def __init__(self, vals: list[Node], magic_num: int):
		self.vals = vals
		self.magic_num = magic_num

	def __repr__(self) -> str:
		return f'''
		{{
			"Verify-Imported": ["malloc", "heapalloc"],
			"Exec-ExpressionA": {
				VariableDefinitionNode(
					"LET", 
					f".temp{self.magic_num}",
					FunctionCallNode(
						VariableAccessNode(
							Token(["", "malloc", 0])
						), 
						[NumNode(len(self.vals)*4)]
					),
					0
				)
			},
			{
				",".join(
					f"""
					"Exec-Expression{i}": {
						AddrAssignmentNode(
							ExprSubscriptNode(
								VariableAccessNode(
									Token([None, f".temp{self.magic_num}", 0])
								),
								NumNode(i)
							),
							val
						)
					}
					"""
					for i, val in enumerate(self.vals)
				)
			},
			"ExpressionA": {
				VariableAccessNode(
					Token([None, f".temp{self.magic_num}", 0])
				)
			}
		}}'''
	
class DynamicObjectNode(Node):
	def __init__(self, props: dict[str, Node], magic_num: int):
		self.props = props
		self.magic_num = magic_num

	def __repr__(self) -> str:
		return f'''{{
	"Verify-Imported0": ["strcmp", "dynamic objects"],
	"Verify-Imported1": ["Object.AddProperty", "dynamic objects"],
	"Expression": {
		HeapAllocationNode(
			[
				AnonymousFunctionNode(
					{"this": "LET", "name": "LET"}, 
					{
						f"Expression{i}": loads(str(
							ConditionalStatementNode(
								BinOpNode(
									FunctionCallNode(
										VariableAccessNode(Token([None, "strcmp", 0])),
										[VariableAccessNode(Token([None, "name", 0])), StringLiteral(prop)]
									), "==", NumNode(0)
								),
								{
									"Expression": loads(str(
										FunctionReturnStatement(
											BinOpNode(
												VariableAccessNode(Token([None, "this", 0])), "+", NumNode((i*4+12))
											)
										)
									))
								},
								{}
							)
						))
						for i, prop in enumerate(self.props.keys())
					}
				),
				AnonymousFunctionNode(
					{"this": "LET", "name": "LET", "value": "LET"}, 
					{
						**{
							f"Expression{i}": loads(str(
								ConditionalStatementNode(
									BinOpNode(
										FunctionCallNode(
											VariableAccessNode(Token([None, "strcmp", 0])),
											[VariableAccessNode(Token([None, "name", 0])), StringLiteral(prop)]
										), "==", NumNode(0)
									),
									{
										"Expression": loads(str(
											AddrAssignmentNode(
												DerefOpNode(
													BinOpNode(
														DerefOpNode(VariableAccessNode(Token([None, "this", 0]))), "+", NumNode((i*4)+12)
													)
												),
												VariableAccessNode(Token([None, "value", 0]))
											)
										)),
										"Expression-Return": loads(str(
											FunctionReturnStatement(None)
										))
									},
									{}
								)
							))
							for i, prop in enumerate(self.props.keys())
						},
						"Expression": loads(str(
							AddrAssignmentNode(
								DerefOpNode(VariableAccessNode(Token([None, "this", 0]))),
								FunctionCallNode(
									VariableAccessNode(Token([None, "Object.AddProperty", 0])),
									[DerefOpNode(VariableAccessNode(Token([None, "this", 0]))), VariableAccessNode(Token([None, "name", 0])), VariableAccessNode(Token([None, "value", 0]))]
								)
							)
								
						))
					}
				),
				HeapAllocationNode(
					[StringLiteral(name) for name in self.props.keys()]+[NumNode(0)],
					self.magic_num
				),
				*self.props.values()
			],
			self.magic_num+0.5
		)
	}
		}}'''
	
IMPORTED_EXPRS: dict[str, Node] = {}
#

#Parser
class Parser:
	def __init__(self, tokens: list, code):
		self.tokens = tokens
		self.code = code
		self.magic_num = -1 # misc number that will never be the same in between uses
		self.in_paren = []
		self.in_func = []
		self.in_body = []
		self.idx = -1
		self.structs: dict[str, list[str]] = {
			# name: members[]
		}
		self.advance()

	#Gets all the expressions in the code 
	#(which must be split by a <newline>)
	#and formats it into JSON to be read
	#by the compiler class
	def parse(self):
		ast = {}

		while 1:
			expr = str(self.expr_wrapper())

			if self.current.type not in ("NEWLINE", "EOF"):
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 201: Missing end-of-statement token <newline>", code)

				self.advance()
				return UnimplementedNode()

			self.advance() # acknowledge the newline

			ast[f"Expression @Idx[{self.idx}]"] = loads(expr)

			if self.current.type == "EOF":
				break

		return ast

	def advance(self):
		self.idx+=1
		try: self.current = Token(self.tokens[self.idx])
		except IndexError: pass

	def decrement(self):
		self.idx-=2
		self.advance()

	def expr_wrapper(self): # allows for tokens after expressions like expr[], expr(), and expr.<name>, which all still evaluate to expressions
		expr = self.expr()

		if expr is None: return "{}"

		return expr

	#gets blocks of code in between curly braces
	def get_body(self):
		self.in_body.append(None)

		body = {}
		while self.current.value != "}":			
			expr = str(self.expr_wrapper())

			body[f"Expression @Idx[{self.idx}]"] = loads(expr)

			if self.current.value == '}':
				self.advance()
				break

			if self.current.type != "NEWLINE":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 201: Missing end-of-statement token <newline>", code)
				break

			if self.current.type == "EOF":
				code = get_code(self.code, self.current.idx)

				throw("UTSC 202: Unexpected EOF, Expected '}'", code)
				break
			
			self.advance()

		self.advance()

		self.in_body.pop()

		return body

	# skip newlines
	def skip_newlines(self):
		while self.current.type == "NEWLINE": self.advance()

	# "unskip newlines"
	def go_back_newlines(self):
		self.decrement()

		while self.current.type == "NEWLINE": self.decrement()

	# Power (**) operator
	def power(self):
		return self.bin_op(self.wrap_atom, ("**", ), self.factor)

	#Grammar Factor
	def factor(self):
		current = self.current

		if current.value == "-":
			self.advance()
			fac = self.factor()
			if fac is None:
				self.decrement()
				
				code = get_code(self.code, self.current.idx)
				
				throw(f"UTSC 203: Expecting value or expression, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
				
				self.advance()
				return UnimplementedNode()

			return UnaryOpNode(current.value, fac)

		return self.power()

	#Grammar Binary Operation
	def bin_op(self, func_a, ops, func_b=None):
		if func_b is None:
			func_b = func_a
		
		left = func_a()

		while self.current.value in ops:
			if self.in_paren: self.skip_newlines()

			op = self.current.value
			self.advance()

			if self.in_paren: self.skip_newlines()

			right = func_b()
			
			left = BinOpNode(left, op, right)		
		
		return left

	def fallback_paren_expr(self, fallback_idx: int): # Function to call if arrow function parsing fails
		self.in_paren.append(None)

		while self.current.idx != fallback_idx: self.decrement()

		self.skip_newlines()

		expression = self.comp_expr()
		
		self.skip_newlines()

		if expression is None:
			expression = {}
		if self.current.value == ')':
			self.advance()

			self.in_paren.pop()

			return expression
		else:
			self.decrement()

			self.in_paren.pop()

			code = get_code(self.code, self.current.idx)

			throw(f"UTSC 203: Expected ')', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
			
			self.advance()
			return UnimplementedNode()

	def parse_ns_name(self) -> str:
		name = ""

		while 1:
			if self.current.type != "IDENTIFIER":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected identifer, got {fmt_type(self.current.type)}", code)
				
				self.advance()
				return UnimplementedNode()
			
			name+=self.current.value

			self.advance()

			if self.current.value != '.':
				break

			name+='.'
			self.advance()

		return name

	def grab_import_export_names(self, get_name: FunctionType=None) -> list[str]:
		names: list[str] = []

		while 1:
			self.skip_newlines()

			if not get_name:
				if self.current.type != "IDENTIFIER":
					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 203: Expected identifier, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

					self.advance()
					return UnimplementedNode()
				
				names.append(self.current.value)
				
				self.advance()
			else:
				names.append(get_name())

			self.skip_newlines()


			if self.current.value == ',':
				self.advance()
				continue

			if self.current.value == '}':
				break

			code = get_code(self.code, self.current.idx)
			throw(f"UTSC 203: Expected '}}' or ',', got {fmt_type(Token(self.tokens[self.idx-1]).type)}", code)
			
			self.advance()
			return UnimplementedNode()

		self.advance() # pass the closing curly brace

		return names

	def get_args(self, end=')'):
		arguments = []

		while self.current.value != end:
			self.skip_newlines()
			expr = self.expr_wrapper()
			self.skip_newlines()

			if expr is None:
				self.decrement()

				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected expression, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

				self.advance()
				return UnimplementedNode()

			arguments.append(expr)

			if self.current.value == ',':
				self.advance()
				continue
			
			if self.current.value != end:
				code = get_code(self.code, self.current.idx)
				throw(f"UTSC 203: Expected '{end}' or ',', got {fmt_type(self.current.type)}", code)
				
				self.advance()
				return UnimplementedNode()

		return arguments

	#Grammar Term
	def term(self):
		return self.bin_op(self.factor, ('*', '/', '%'))
		
	#Grammar Atom
	def atom(self):
		if self.in_paren: self.skip_newlines()

		current = self.current

		if current.type == "IDENTIFIER":
			self.advance()
			
			if self.current.value == '=': # this needs to be in expr()
				self.advance()
				expr = self.comp_expr()
				if expr is None:
					self.decrement()

					code = get_code(self.code, self.current.idx)
					
					throw(f"UTSC 203: Expected expression after assignment operator '=', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
					
					self.advance()
					return UnimplementedNode()
				else:
					return VariableAssignmentNode(current.value, expr, self.current.idx)
			if self.current.value in ('+', '-', '/', '*'): # += -= *= /= assignment
				op = self.current.value
				self.advance()
				
				if self.current.value == '=':
					self.advance()
					expr = self.comp_expr()
					if expr is None:
						self.decrement()

						code = get_code(self.code, self.current.idx)
						
						throw(f"UTSC 203: Expected expression after assignment operator '{op.value}=', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
						
						self.advance()
						return UnimplementedNode()
					else:
						return VariableAssignmentNode( # Lowered AST for +=, -=, etc.
							current.value,
							BinOpNode(
								VariableAccessNode(current),
								op,
								expr
							),
							self.current.idx
						)

				self.decrement() # back up to operator token

			return VariableAccessNode(current)

		if current.type in ("INTEGER", "FLOAT"):
			self.advance()
			return NumNode(current.value)
		if current.type == "STRING":
			self.advance()
			return StringLiteral(current.value)
		if current.type == "AST_INSERT":
			self.advance()

			if self.current.type != "IDENTIFIER":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected identifier, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

				self.advance()
				return UnimplementedNode()
			
			try:
				name = self.current.value
				self.advance()
				
				return IMPORTED_EXPRS[name]
			except KeyError:
				self.decrement()

				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 205: AST Expression '{self.current.value}' not imported!", code)
			
			return UnimplementedNode()
				
		if current.value == '[':
			self.advance()

			vals = self.get_args(']')

			self.advance() # pass last square bracket

			return ArrayLiteralNode(vals)
		
		if current.value == '{':
			self.advance()
			return self.obj_expr()

		if current.value == '(':
			self.advance()

			if (self.current.type in ("IDENTIFIER", "STRUCT")) or (self.current.value == ')'):
				fallback_idx = self.current.idx
				vartype = ""
				parameters: dict[str, str] = {}

				while self.current.value != ')':
					vartype = "LET"
					if self.current.type == "STRUCT":
						self.advance()
						if self.current.type == "IDENTIFIER":
							vartype = f"LET {self.current.value}"
							self.advance()
						else:
							self.decrement()
							code = get_code(self.code, self.current.idx)
							
							throw("UTSC 203: Expected identifier (struct name) after 'struct' keyword", code)
							return UnimplementedNode()

					if self.current.type != "IDENTIFIER":
						return self.fallback_paren_expr(fallback_idx)
					
					if self.current.value in parameters.keys():
						code = get_code(self.code, self.current.idx)

						warn("UTSC 205: Duplicate parameter name, taking the last occurrence", code)

					parameters[self.current.value] = vartype

					self.advance()
					
					if self.current.value not in (',', ')'):
						return self.fallback_paren_expr(fallback_idx)

					if self.current.value == ',': self.advance()

				self.advance()

				if self.current.type != "ARROW_FUNC":
					return self.fallback_paren_expr(fallback_idx)

				self.advance()

				if self.current.value == '{':
					self.advance()

					self.in_func.append(None) # use an array/stack structure to keep track of inner function scopes
					func_body = self.get_body()
					self.in_func.pop()
				else:
					expr = self.expr_wrapper()

					if expr is None:
						self.decrement()

						code = get_code(self.code, self.current.idx)

						throw(f"UTSC 203: Expected expression, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

						self.advance()
						return UnimplementedNode()

					func_body = {
						f"Return Statement": loads(str(expr))
					}

				return AnonymousFunctionNode(parameters, func_body)

			else:
				return self.fallback_paren_expr(self.current.idx)
		if current.type == "NEWLINE":
			self.advance()
			return None
		
		code = get_code(self.code, current.idx)
		
		throw(f"UTSC 203: Expected int, float, identifier, '+', '-', or '(', got {fmt_type(current.type)}", code)

		self.advance()
		return UnimplementedNode()

	def obj_expr(self):
		self.skip_newlines()

		props = dict[str, Node]()

		while self.current.value != '}':
			self.skip_newlines()

			if self.current.type != "IDENTIFIER":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected identifier, got {fmt_type(self.current.type)}", code)

				self.advance()
				return UnimplementedNode()
			
			propname = self.current.value

			self.advance()
			self.skip_newlines()

			if self.current.value != ':':
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected ':', got '{self.current.value}'", code)

				self.advance()
				return UnimplementedNode()
			
			self.advance()
			self.skip_newlines()

			value = self.comp_expr()
			self.skip_newlines()

			props[propname] = value

			if self.current.value == ',':
				self.advance()
				continue

			if self.current.value == '}': break

			code = get_code(self.code, self.current.idx)

			throw(f"UTSC 203: Expected ',' or '}}', got '{self.current.value}'", code)

			self.advance()
			return UnimplementedNode()
		
		self.advance()

		self.magic_num+=1

		return DynamicObjectNode(props, self.magic_num)		

	def conditional_expr(self):
		condition = self.comp_expr()

		if condition is None:
			code = get_code(self.code, self.current.idx)

			throw(f"UTSC 203: Expected expression, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

			self.advance()
			return UnimplementedNode()

		self.skip_newlines()

		if self.current.value == "{":
			self.advance()
			if_body = self.get_body()
		else:
			if_nodes = self.expr_wrapper()
			
			if if_nodes is None:
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected expression, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

				self.advance()
				return UnimplementedNode()

			if_body = loads(str(if_nodes))

		self.skip_newlines()
			
		if self.current.value == "else":
			self.advance()

			if self.current.value == "if":
				self.advance()
				
				else_body = loads(str(self.conditional_expr()))

				return ConditionalStatementNode(
					condition, if_body, else_body
				)

			self.skip_newlines()

			if self.current.value == "{":
				self.advance()
				else_body = self.get_body()
			else:
				else_nodes = self.expr_wrapper()
				else_body = {f"Expression @Idx[{self.idx}]" : loads(str(else_nodes))}
				if else_nodes is None:
					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 203: Expected expression, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
		else:
			self.go_back_newlines() # we don't want to consume the expression delimeter
			else_body = {}

		self.advance()
		
		return ConditionalStatementNode(condition, if_body, else_body)

	def while_expr(self):
		condition = self.comp_expr()

		if condition is None:
			code = get_code(self.code, self.current.idx)

			throw(f"UTSC 203: Expected expression, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

			self.advance()
			return UnimplementedNode()

		self.skip_newlines()

		if self.current.value == '{':
			self.advance()
			body = self.get_body()
		else:
			body_nodes = self.expr_wrapper()

			if body_nodes is None:
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected expression, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

				self.advance()
				return UnimplementedNode()

			body = loads(str(body_nodes))

		return WhileLoopNode(
			condition,
			body
		)
	
	def comp_expr(self):
		if self.current.type == "NEWLINE": return

		if self.current.value == "not":
			self.advance()

			node = self.comp_expr()
			return UnaryOpNode("not", node)

		elif self.current.value == "ref":
			self.advance()

			expr = self.comp_expr()

			if type(expr) not in (
				PropertyAccessNode, 
				ExprSubscriptNode,
				VariableAccessNode,
				ArrayLiteralNode,
				DynamicObjectNode
			):
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected identifier, property access, subscript expression, array literal, or dynamic object after address operator 'ref', got {fmt_type(self.current.type)} instead", code)

				self.advance()
				return UnimplementedNode()

			return RefOpNode(expr)

		elif self.current.value == "deref":
			self.advance()

			expr = self.comp_expr()

			return DerefOpNode(expr)
		
		elif self.current.type == "HEAP_ALLOC":
			start = self.current

			self.advance()

			expr = self.comp_expr()

			if type(expr) is ArrayLiteralNode:
				self.magic_num+=1
				return HeapAllocationNode(expr.vals, self.magic_num)

			if type(expr) is AnonymousFunctionNode:
				expr.flag = AnonymousFunctionNode.HEAP_ALLOCATED
				return expr

			code = get_code(self.code, start.idx)

			throw(f"UTSC 203: Expected array literal or anonymous function after 'heapalloc', got {fmt_type(self.current.type)}", code)
			return UnimplementedNode()
	
		elif self.current.type == "LOCALLY_EXPOSED_FUNC":
			start = self.current
			self.advance()

			expr = self.comp_expr()

			if type(expr) is AnonymousFunctionNode:
				expr.flag = AnonymousFunctionNode.LOCALLY_EXPOSED
				return expr			

			code = get_code(self.code, start.idx)

			throw(f"UTSC 203: Expected anonymous function after 'localonly', got {fmt_type(self.current.type)}", code)
			return UnimplementedNode()

		return self.bin_op(self.num_expr, ("==", "!=", '<', '>', "<=", ">=", "and", "or"))
		
	def wrap_atom(self):
		expr = self.atom()

		if self.current.value in ('.', '[', '('):
			start = self.current.idx

			if self.current.value == '.':
				node = PropertyAccessNode(expr, "", self.current.idx)
			elif self.current.value == '[':
				node = ExprSubscriptNode(expr, {})
			else:
				node = FunctionCallNode(expr, [])

			while self.current.value in ('.', '[', '('): # property access
				op = self.current.value

				if self.current.idx != start: # if this is not the first go-round
					if op == '.':
						node = PropertyAccessNode(node, "", self.current.idx)
					elif op == '[':
						node = ExprSubscriptNode(node, {})
					else:
						node = FunctionCallNode(node, [])

				self.advance()
				
				if op == '.':
					if self.current.type != "IDENTIFIER":
						self.decrement()

						code = get_code(self.code, self.current.idx)

						throw(f"UTSC 203: Expected identifier after '.' operator, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
						
						self.advance()
						return UnimplementedNode()

					node.name = self.current.value
					
					self.advance()

					continue

				if op == '[':
					offset = self.comp_expr()

					if self.current.value != ']':
						self.decrement()

						code = get_code(self.code, self.current.idx)

						throw(f"UTSC 203: Expected ']', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

						self.advance()
						return UnimplementedNode()

					node.offset = offset

					self.advance()

					continue

				# otherwise, it must be an open paren (function call)
				arguments = self.get_args()

				self.advance()

				node.args = arguments

			return node

		return expr

	def struct_expr(self):
		if self.current.type != "IDENTIFIER":
			self.decrement()

			code = get_code(self.code, self.current.idx)

			throw(f"UTSC 203: Expected identifier after 'struct' keyword, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
			return UnimplementedNode()

		name = self.current.value

		self.advance()

		self.skip_newlines()

		if self.current.value != '{':
			self.decrement()

			code = get_code(self.code, self.current.idx)

			throw(f"UTSC 203: Expected opening brace after struct name, got '{Token(self.tokens[self.idx+1]).value}'", code)
			return UnimplementedNode()

		self.advance()
		
		members = self.grab_import_export_names()

		self.structs[name] = members

		return None

	def num_expr(self):
		return self.bin_op(self.term, ("+", "-"))

	def expr(self) -> Node:
		if self.current.type in ("CONST", "LET"):
			vartype: str = self.current.type
			self.advance()
			if self.current.type == "STRUCT":
				self.advance()

				if self.current.type != "IDENTIFIER":
					self.decrement()
					
					code = get_code(self.code, self.current.idx)
					
					throw(f"UTSC 203: Expected identifier after '{vartype.lower()} struct', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
					
					self.advance()
					return UnimplementedNode()

				struct_name = self.current.value

				vartype+=f" {struct_name}"

				self.advance()

			if self.current.type != "IDENTIFIER":
				self.decrement()
				
				code = get_code(self.code, self.current.idx)
				
				throw(f"UTSC 203: Expected identifier after '{vartype.lower()}', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
				
				self.advance()
				return UnimplementedNode()

			name = self.current.value
			self.advance()

			if self.current.type == "NEWLINE":
				if vartype == "CONST":
					self.decrement()

					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 204: Constants must be assigned values!", code)

					self.advance()
					return UnimplementedNode()

				return VariableDeclarationNode(vartype, name)

			elif self.current.value == '=':
				self.advance()
				expr = self.expr_wrapper()

				if expr is None:
					self.decrement()

					code = get_code(self.code, self.current.idx)
					
					throw(f"UTSC 203: Expected expression after assignment operator '=', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
					
					self.advance()
					return UnimplementedNode()
				else:
					return VariableDefinitionNode(vartype, name, expr, self.current.idx)
			else:
				code = get_code(self.code, self.current.idx)
				
				throw(f"UTSC 203: Expected '=' or <newline>, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
				
				self.advance()
				return UnimplementedNode()
		if self.current.type == "STRUCT":
			self.advance()
			return self.struct_expr()
		if self.current.type == "EXPORT" and not self.in_func:
			self.advance()

			if self.current.type == "NAMESPACE":
				self.advance()

				if self.current.value != '{':
					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 203: Expected '}}', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
					
					self.advance()
					return UnimplementedNode()

				self.advance()

				names = self.grab_import_export_names(get_name=self.parse_ns_name)
				
				return NSExportNode(names)
				

			if self.current.value != '{':
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected '}}', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
				
				self.advance()
				return UnimplementedNode()

			self.advance()

			names = self.grab_import_export_names()
			
			return ExportNode(names)

		if self.current.type == "IMPORT" and not self.in_func:
			self.advance()

			if self.current.type == "NAMESPACE":
				self.advance()

				if self.current.value != '{':
					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 203: Expected '}}', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
					
					self.advance()
					return UnimplementedNode()

				self.advance()

				names = self.grab_import_export_names(get_name=self.parse_ns_name)
				
				if self.current.type != "FROM":
					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 203: Expected 'from', got {self.current.value!r}", code)

					self.advance()
					return UnimplementedNode()

				self.advance()

				if self.current.type != "STRING":
					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 203: Expected module name, got {self.current.value!r}", code)
					
					self.advance()
					return UnimplementedNode()

				modnode = self.current

				self.advance()

				return NSImportNode(modnode.value, names, modnode.idx)
			
			struct = ast_expr = False

			if self.current.type == "STRUCT":
				struct = True
				self.advance()
			elif self.current.type == "AST_EXPRESSION":
				self.advance()
				ast_expr = True

			names: list[str] = []
			
			if self.current.value == '{':
				self.advance()

				names = self.grab_import_export_names()
			else:
				if self.current.type != "IDENTIFIER":
					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 203: Expected identifier or '{{', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

					self.advance()
					return UnimplementedNode()

				names.append(self.current.value)

				self.advance()

			if self.current.type != "FROM":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected 'from', got {self.current.value!r}", code)

				self.advance()
				return UnimplementedNode()

			self.advance()

			if self.current.type != "STRING":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected module name, got {self.current.value!r}", code)
				
				self.advance()
				return UnimplementedNode()

			modnode = self.current

			self.advance()

			if struct: return StructImportNode(modnode.value, names, modnode.idx)

			if ast_expr:
				try:
					with open(modnode.value, 'r') as f:
						exprs: dict[str, dict] = load(f)

						for name in names:
							if name in IMPORTED_EXPRS:
								code = get_code(self.code, modnode.idx)

								throw(f"UTSC 305: Expression '{name}' already imported!", code)
								continue
							IMPORTED_EXPRS[name] = Node(exprs[name], self.code, self.current.idx, name)
				except FileNotFoundError:
					code = get_code(self.code, modnode.idx)

					throw(f"UTSC 306: AST Module '{modnode.value}' does not exist!", code)
				except JSONDecodeError:
					code = get_code(self.code, modnode.idx)

					throw(f"UTSC 306: AST Module '{modnode.value}' does not contain valid JSON!", code)
				except KeyError:
					code = get_code(self.code, modnode.idx)

					throw(f"UTSC 306: AST Module '{modnode.value}' does not contain the expression '{name}'!", code)
				
				return None

			return ImportNode(modnode.value, names, modnode.idx)
		
		if self.current.type == "NAMESPACE":
			self.advance()

			name = self.parse_ns_name()

			self.skip_newlines()

			if self.current.value != '{':
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected opening brace, got {self.current.value!r}", code)
				
				self.advance()
				return UnimplementedNode()
			
			self.advance()

			body = self.get_body()

			return NamespaceDeclarationNode(name, body)

		if self.current.value == "if":
			self.advance()
			return self.conditional_expr()

		if self.current.value == "while":
			self.advance()
			return self.while_expr()

		if self.in_func and (self.current.type == "RETURN"):
			self.advance()
			if self.current.value == '}' and self.in_body: return FunctionReturnStatement(None) # we know this is an empty return statement, don't consume '}' so self.get_body() close the body off
			expr = self.comp_expr()
			
			return FunctionReturnStatement(expr)
		if self.current.type == "NEWLINE":
			return None

		node = self.bin_op(self.comp_expr, ('and', 'or'))

		if (type(node) in (ExprSubscriptNode, PropertyAccessNode, DerefOpNode)) and (self.current.value == '='):
			self.advance()

			expr = self.comp_expr()
			if expr is None:
				self.decrement()

				code = get_code(self.code, self.current.idx)
				
				throw(f"UTSC 203: Expected expression after assignment operator '=', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
				
				self.advance()
				return UnimplementedNode()
			else:
				return AddrAssignmentNode(node, expr)

		return node

#