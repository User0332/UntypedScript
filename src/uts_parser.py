import sys
import traceback # for debugging

# max limit possible without crashing compiler
sys.setrecursionlimit(3800)

from json import loads, dumps

from utils import (
	Token, 
	get_code,
	throw, 
	warn,
	fmt_type
)


#Node Utility Classes
class Node:
	pass

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
	def __init__(self, ident: str, idx: int):
		self.ident = ident
		self.idx = idx

	def __repr__(self):
		return f'{{ "Addr Operation ref": {{ "name": "{self.ident}", "index": {self.idx} }} }}'

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
		self.expr = str(expression)
		self.idx = idx

	def __repr__(self):
		return f'{{"Variable Definition" : {{ "type" : "{self.dtype}", "name" : "{self.name}", "value" : {self.expr}, "index" : {self.idx} }} }}'

class VariableAssignmentNode(Node):
	def __init__(self, name: str, expression: Node, idx: int):
		self.name = name
		self.expr = str(expression)
		self.idx = idx

	def __repr__(self):
			return f'{{"Variable Assignment" : {{ "name" : "{self.name}", "value" : {self.expr}, "index" : {self.idx} }} }}'

class VariableAccessNode(Node):
	def __init__(self, var_tok: Token):
		self.name = var_tok.value
		self.idx = var_tok.idx

	def __repr__(self):
		return f'{{"Variable Reference": {{ "name" : "{self.name}", "index" : {self.idx} }} }}'

class VariableSubscriptNode(Node):
	def __init__(self, var_tok: Token, offset: Node):
		self.var_tok = var_tok
		self.offset = offset

	def __repr__(self):
		return str( # Lowered AST, code lowered - var[offset] -> deref ( var+(offset*4) )
			DerefOpNode(
				BinOpNode(
					VariableAccessNode(self.var_tok),
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
	def __init__(self, params: list[str], body: dict):
		self.params = dumps(params)
		self.body = dumps(body)
	
	def __repr__(self):
		return f'{{"Anonymous Function" : {{"parameters" : {self.params}, "body" : {self.body}  }} }}'

class FunctionCallNode(Node):
	def __init__(self, name: str, args: list[Node], idx: int):
		self.name = name
		self.args = args
		self.idx = idx

	def __repr__(self):
		return f'{{"Function Call" : {{"name" : "{self.name}", "arguments" : {self.args}, "index" : {self.idx} }} }}'

class FunctionReturnStatement(Node):
	def __init__(self, expr: dict):
		self.expr = expr if expr else "null"

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

class StructCreationNode(Node):
	def __init__(self, name: str, member_values: list[Node]):
		self.name = name
		self.member_values = member_values

	def __repr__(self) -> str:
		return f'{{ "Struct Creation": {{ "name": "{self.name}", "values": {self.member_values} }} }}'

class ArrayLiteralNode(Node):
	def __init__(self, vals: list[Node]):
		self.vals = vals

	def __repr__(self) -> str:
		return f'{{ "Array Literal": {self.vals} }}'
#

#Parser
class Parser:
	def __init__(self, tokens: list, code):
		self.tokens = tokens
		self.code = code
		self.in_paren = []
		self.in_func = []
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
			expr = str(self.expr())

			if self.current.type not in ("NEWLINE", "EOF"):
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 201: Missing end-of-statement token <newline>", code)

			self.advance() # acknowledge the newline

			expr = "{}" if expr == "None" else expr

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

	#gets blocks of code in between curly braces
	def get_body(self):
		body = {}
		while self.current.value != "}":				
			expr = str(self.expr())

			expr = "{}" if expr == "None" else expr

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
		return self.bin_op(self.atom, ("**", ), self.factor)

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

		expression = self.expr()
		
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

	def grab_import_export_names(self) -> list[str]:
		names: list[str] = []

		while 1:
			self.skip_newlines()

			if self.current.type != "IDENTIFIER":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected identifier, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

				self.advance()
				return UnimplementedNode()
			
			names.append(self.current.value)
			
			self.advance()

			self.skip_newlines()

			if self.current.value == ',':
				self.advance()
				continue

			if self.current.value == '}':
				break

			code = get_code(self.code, self.current.idx)
			throw(f"UTSC 203: Expected '}}' or ',', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
			
			self.advance()
			return UnimplementedNode()

		self.advance() # pass the closing curly brace

		return names

	def get_args(self, end=')'):
		arguments = []

		while self.current.value != end:
			self.skip_newlines()
			expr = self.expr()
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
				throw(f"UTSC 203: Expected '{end}' or ',', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
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
			
			if self.current.value == '=':
				self.advance()
				expr = self.expr()
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
					expr = self.expr()
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

			if self.current.value != '(':
				if self.current.value != '[':
					return VariableAccessNode(current)
				
				self.advance()
				offset = self.expr()
				self.advance()

				return VariableSubscriptNode(current, offset)

			self.advance()

			arguments = self.get_args()

			self.advance() # pass closing paren

			return FunctionCallNode(
				current.value,
				arguments,
				current.idx
			)

		if current.type in ("INTEGER", "FLOAT"):
			self.advance()
			return NumNode(current.value)
		if current.type == "STRING":
			self.advance()
			return StringLiteral(current.value)
		if current.type == "NEW":
			self.advance()

			if self.current.type != "IDENTIFIER":
				self.decrement()

				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected identifier after 'struct' keyword, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
		
			name = self.current.value

			self.advance()

			self.skip_newlines()

			if self.current.value != '{':
				self.decrement()

				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected opening brace after struct name, got '{Token(self.tokens[self.idx+1]).value}'", code)

			self.advance()

			member_vals = self.get_args('}')

			self.advance() # pas last curly brace

			return StructCreationNode(name, member_vals)

		if current.value == '[':
			self.advance(),

			vals = self.get_args(']')

			self.advance() # pass last square bracket

			return ArrayLiteralNode(vals)

		if current.value == '(':
			self.advance()

			if (self.current.type == "IDENTIFIER") or (self.current.value == ')'):
				fallback_idx = self.current.idx
				parameters = []

				while self.current.value != ')':
					if self.current.type != "IDENTIFIER":
						return self.fallback_paren_expr(fallback_idx)

					parameters.append(self.current.value)

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
					expr = self.expr()

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

		if current.value == "if":
			self.advance()
			return self.conditional_expr()
		if current.value == "while":
			self.advance()
			return self.while_expr()

		if self.in_func and self.current.type == "RETURN":
			self.advance()
			expr = self.expr()

			return FunctionReturnStatement(expr)
		if current.type == "EXPORT" and not self.in_func:
			self.advance()

			if self.current.value != '{':
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected '}}', got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
				return UnimplementedNode()

			self.advance()

			names = self.grab_import_export_names()
			
			return ExportNode(names)

		if current.type == "IMPORT" and not self.in_func:
			self.advance()

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
				return UnimplementedNode()

			modnode = self.current

			self.advance()

			return ImportNode(modnode.value, names, modnode.idx)

		code = get_code(self.code, current.idx)
		
		throw(f"UTSC 203: Expected int, float, identifier, '+', '-', or '(', got {fmt_type(current.type)}", code)

		self.advance()
		return UnimplementedNode()

	#Grammar Expressions
	def conditional_expr(self):
		condition = self.expr()

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
			if_nodes = self.expr()
			
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
				
				self.advance()

				return ConditionalStatementNode(
					condition, if_body, else_body
				)

			self.skip_newlines()

			if self.current.value == "{":
				self.advance()
				else_body = self.get_body()
			else:
				else_nodes = self.expr()
				else_body = {f"Expression @Idx[{self.idx}]" : loads(str(else_nodes))}
				if else_nodes is None:
					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 203: Expected expression, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)
		else:
			self.go_back_newlines() # we don't want to consume the expression delimeter
			else_body = {}
		
		return ConditionalStatementNode(condition, if_body, else_body)

	def while_expr(self):
		condition = self.expr()

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
			body_nodes = self.expr()

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
		if self.current.value == "not":
			self.advance()

			node = self.comp_expr()
			return UnaryOpNode("not", node)

		elif self.current.value == "ref":
			self.advance()

			if self.current.type != "IDENTIFIER":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 203: Expected identifier after address operator 'ref', got {fmt_type(Token(self.tokens[self.idx+1]).type)} instead", code)

			ident = self.current

			self.advance() # pass identifier

			return RefOpNode(ident.value, ident.idx)

		elif self.current.value == "deref":
			self.advance()

			expr = self.expr()

			return DerefOpNode(expr)

		return self.bin_op(self.num_expr, ("==", "!=", '<', '>', "<=", ">=", "and", "or"))
		
	def struct_expr(self):
		if self.current.type != "IDENTIFIER":
			self.decrement()

			code = get_code(self.code, self.current.idx)

			throw(f"UTSC 203: Expected identifier after 'struct' keyword, got {fmt_type(Token(self.tokens[self.idx+1]).type)}", code)

		name = self.current.value

		self.advance()

		self.skip_newlines()

		if self.current.value != '{':
			self.decrement()

			code = get_code(self.code, self.current.idx)

			throw(f"UTSC 203: Expected opening brace after struct name, got '{Token(self.tokens[self.idx+1]).value}'", code)

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
				expr = self.expr()

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

		if self.current.type == "NEWLINE":
			return None

		return self.bin_op(self.comp_expr, ('and', 'or'))
	#

#
