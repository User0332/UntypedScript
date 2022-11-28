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

class StringLiteral(NumNode):
	def __repr__(self):
		return super().__repr__() \
			.replace("Numerical Constant", "String Literal")

class BinOpNode(Node):
	def __init__(self, left: Node, op: Token, right: Node):
		self.left = left
		self.op = op
		self.right = right

	def __repr__(self):
		return f'{{ "Binary Operation {self.op.value}" : [{self.left}, {self.right}] }}'

class UnaryOpNode(Node):
	def __init__(self, op: Token, node: Node):
		self.op = op
		self.node = node

	def __repr__(self):
		return f'{{"Unary Operation {self.op.value}" : {self.node} }}'

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
		return f'{{"Variable Reference" : {{ "name" : "{self.name}", "index" : {self.idx} }} }}'

class ConditionalStatementNode(Node):
	def __init__(self, condition: Node, if_body: dict, else_body: dict):
		self.condition = condition
		self.if_body = dumps(if_body)
		self.else_body = dumps(else_body)

	def __repr__(self):
		return f'{{"Conditional Statement" : {{ "condition" : {self.condition}, "if" : {self.if_body}, "else" : {self.else_body} }} }}'

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
	def __init__(self, modname: str, name: str, idx: int):
		self.modname = modname
		self.name = name
		self.idx = idx

	def __repr__(self) -> str:
		return f'{{ "Import": {{ "module": {self.modname}, "name": "{self.name}", "index": {self.idx} }} }}'

class ExportNode(Node):
	def __init__(self, name: str):
		self.name = name

	def __repr__(self) -> str:
		return f'{{ "Export": "{self.name}" }}'
#

#Parser
class Parser:
	def __init__(self, tokens, code):
		self.tokens = tokens
		self.code = code
		self.in_func = []
		self.idx = -1
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

				throw(f"UTSC 030: Missing end-of-statement token <newline>", code)

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

			if self.current.type not in ("NEWLINE", "}"):
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 030: Missing end-of-statement token <newline>", code)

			if self.current.type == "EOF":
				code = get_code(self.code, self.current.idx)

				throw("UTSC 018: Unexpected EOF, Expected '}'", code)
				break

			self.advance()

		self.advance()

		return body

	# skip newlines
	def skip_newlines(self):
		while self.current.type == "NEWLINE": self.advance()

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
				
				throw(f"UTSC 018: Expecting value or expression, got {fmt_type(self.current.type)}", code)
				
				self.advance()
				return UnimplementedNode()

			return UnaryOpNode(current, fac)

		return self.power()

	#Grammar Binary Operation
	def bin_op(self, func_a, ops, func_b=None):
		if func_b is None:
			func_b = func_a

		left = func_a()

		while self.current.value in ops:
			op = self.current
			self.advance()
			right = func_b()
			
			left = BinOpNode(left, op, right)		
		

		return left

	def fallback_paren_expr(self, fallback_idx: int): # Function to call if arrow function parsing fails
		while self.current.idx != fallback_idx: self.decrement()

		expression = self.expr()
		if expression is None:
			expression = {}
		if self.current.value == ')':
			self.advance()
			return expression
		else:
			self.decrement()
			code = get_code(self.code, self.current.idx)
			
			throw(f"UTSC 018: Expected ')', got {fmt_type(self.current.type)}", code)
			
			self.advance()
			return UnimplementedNode()

	#Grammar Term
	def term(self):
		return self.bin_op(self.factor, ('*', '/'))
		
	#Grammar Atom
	def atom(self):
		current = self.current

		if current.type == "IDENTIFIER":
			self.advance()

			if self.current.value != '(':
				return VariableAccessNode(current)

			arguments = []

			self.advance()

			while self.current.value != ')':
				expr = self.expr()

				if expr is None:
					self.decrement()

					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 018: Expected expression, got {fmt_type(self.current.type)}", code)

					self.advance()
					return UnimplementedNode()

				arguments.append(expr)

				if self.current.value == ',':
					self.advance()
					continue

				if self.current.value != ')':
					code = get_code(self.code, self.current.idx)
					throw(f"UTSC 018: Expected ')' or ',', got {fmt_type(self.current.type)}", code)
					self.advance()
					return UnimplementedNode()



			self.advance()

			return FunctionCallNode(
				current.value,
				arguments,
				current.idx
			)

		elif current.type in ("INTEGER", "FLOAT"):
			self.advance()
			return NumNode(current.value)
		elif current.type == "STRING":
			self.advance()
			return StringLiteral(current.value)

		elif current.value == '(':
			self.advance()

			if self.current.type == "IDENTIFIER" or self.current.value == ')':
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
					self.decrement()
					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 018: Expected arrow func ('=>'), got {fmt_type(self.current.type)}", code)

					self.advance()
					return UnimplementedNode()

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

						throw(f"UTSC 018: Expected expression, got {fmt_type(self.current.type)}", code)

						self.advance()
						return UnimplementedNode()

					func_body = {
						f"Return Statement": loads(str(expr))
					}

				return AnonymousFunctionNode(parameters, func_body)

		elif current.value == "if":
			self.advance()
			return self.conditional_expr()

		elif self.in_func and self.current.type == "RETURN":
			self.advance()
			expr = self.expr()

			return FunctionReturnStatement(expr)
		elif self.current.type == "EXPORT" and not self.in_func:
			self.advance()

			if self.current.type != "IDENTIFIER":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 018: Expected identifier, got {fmt_type(self.current.type)}", code)
				return UnimplementedNode()

			name = self.current.value

			self.advance()
			
			return ExportNode(name)

		elif self.current.type == "IMPORT" and not self.in_func:
			self.advance()
			
			if self.current.type != "IDENTIFIER":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 018: Expected identifier, got {fmt_type(self.current.type)}", code)
				return UnimplementedNode()

			name = self.current.value

			self.advance()

			if self.current.type != "FROM":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 018: Expected 'from', got {self.current.value!r}", code)
				return UnimplementedNode()

			self.advance()

			if self.current.type != "STRING":
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 018: Expected module name, got {self.current.value!r}", code)
				return UnimplementedNode()

			modnode = self.current

			self.advance()

			return ImportNode(modnode.value, name, modnode.idx)

		code = get_code(self.code, self.current.idx)
		
		throw(f"UTSC 018: Expected int, float, identifier, '+', '-', or '(', got {fmt_type(self.current.type)}", code)

		self.advance()
		return UnimplementedNode()

	#Grammar Expressions
	def conditional_expr(self):
		condition = self.expr()

		if condition is None:
			code = get_code(self.code, self.current.idx)

			throw(f"UTSC 018: Expected expression, got {fmt_type(self.current.type)}", code)

			self.advance()
			return UnimplementedNode()

		self.skip_newlines()

		if self.current.value == "{":
			self.advance()
			if_body = self.get_body()
		else:
			if_nodes = self.expr()
			if_body = {f"Expression @Idx[{self.idx}]" : loads(str(if_nodes))}
			if if_nodes is None:
				code = get_code(self.code, self.current.idx)

				throw(f"UTSC 018: Expected expression, got {fmt_type(self.current.type)}", code)

				self.advance()
				return UnimplementedNode()

		self.skip_newlines()
			
		if self.current.value == "else":
			self.advance()

			self.skip_newlines()

			if self.current.value == "{":
				self.advance()
				else_body = self.get_body()
			else:
				else_nodes = self.expr()
				else_body = {f"Expression @Idx[{self.idx}]" : loads(str(else_nodes))}
				if else_nodes is None:
					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 018: Expected expression, got {fmt_type(self.current.type)}", code)
		else:
			else_body = {}
		
		return ConditionalStatementNode(condition, if_body, else_body)
	
	def comp_expr(self):
		if self.current.value == "not":
			op = self.current
			self.advance()

			node = self.comp_expr()
			return UnaryOpNode(op, node)

		return self.bin_op(self.num_expr, ("==", "!=", "<", ">", "<=", ">=", "and", "or"))
		

	def num_expr(self):
		return self.bin_op(self.term, ("+", "-"))

	def expr(self) -> Node:
		if self.current.type in ("CONST", "LET"):
			vartype: str = self.current.type
			self.advance()
			if self.current.type != "IDENTIFIER":
				self.decrement()
				
				code = get_code(self.code, self.current.idx)
				
				throw(f"UTSC 018: Expected identifier after '{vartype.lower()}', got {fmt_type(self.current.type)}", code)
				
				self.advance()
				return UnimplementedNode()

			name = self.current.value
			self.advance()

			if self.current.type == "NEWLINE":
				if vartype == "CONST":
					self.decrement()

					code = get_code(self.code, self.current.idx)

					throw(f"UTSC 021: Constants must be assigned values!", code)

					self.advance()
					return UnimplementedNode()

				return VariableDeclarationNode(vartype, name)

			elif self.current.value == "=":
				self.advance()
				expr = self.expr()

				if expr is None:
					self.decrement()

					code = get_code(self.code, self.current.idx)
					
					throw(f"UTSC 018: Expected expression after assignment operator '=', got {fmt_type(self.current.type)}", code)
					
					self.advance()
					return UnimplementedNode()
				else:
					return VariableDefinitionNode(vartype, name, expr, self.current.idx)
			else:
				print(self.current)
				code = get_code(self.code, self.current.idx)
				
				throw(f"UTSC 018: Expected '=' or <newline>, got {fmt_type(self.current.type)}", code)
				
				self.advance()
				return UnimplementedNode()

		elif self.current.type == "IDENTIFIER":
			name = self.current.value
			self.advance()
			if self.current.value == "=":
				self.advance()
				expr = self.expr()
				if expr is None:
					self.decrement()

					code = get_code(self.code, self.current.idx)
					
					throw(f"UTSC 018: Expected expression after assignment operator '=', got {fmt_type(self.current.type)}", code)
					
					self.advance()
					return UnimplementedNode()
				else:
					return VariableAssignmentNode(name, expr, self.current.idx)
			else:
				self.decrement() #move index pointer back to the identifier
		elif self.current.type == "NEWLINE":
			return None

		return self.bin_op(self.comp_expr, ('and', 'or'))
	#

#
