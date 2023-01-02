from utils import SigNonConstantNumericalExpressionException

valid_nodes = (
	"Variable", 
	"Binary Operation", 
	"Unary Operation",
	"Numerical Expression",
	"Expression",
	"Number Literal",
	"value"
)

class SyntaxTreePreproccesor:
	def __init__(self, ast: dict):
		self.ast = ast

	def simplify_numerical_expression(self, node: dict) -> str:
		key: str
		expr = ""

		for key in node:
			if key.startswith("Binary Operation"):
				left = node[key][0]
				right = node[key][1]
				new_expr = self.simplify_numerical_expression(left)
				expr+=new_expr+key.removeprefix("Binary Operation")+" "
				new_expr = self.simplify_numerical_expression(right)
				expr+=new_expr
			elif key.startswith("Unary Operation"):
				new_expr = self.simplify_numerical_expression(node[key])
				expr+=key.removeprefix("Unary Operation")+new_expr
			elif key.startswith("Numerical Constant"):
				expr+=str(node[key])
			else:
				raise SigNonConstantNumericalExpressionException


		return f"({expr})"

	def var_accessed(self, name: str, top: dict=None) -> bool:
		key: str; node: dict
		top = top if top is not None else self.ast

		for key, node in top.items():
			if key.startswith("Variable Reference"):
				if node['name'] == name:
					return True
			elif type(node) is list:
				if self.var_accessed(name, node[0]) or self.var_accessed(name, node[1]):
					return True
			elif type(node) is int:
				continue
			elif key.startswith(valid_nodes):
				if self.var_accessed(name, node):
					return True

		return False

	def simplify(self, top: dict=None) -> tuple[int, dict]:
		key: str; node: dict

		new_nodes = []
		del_nodes = []

		top = top if top is not None else self.ast


		for key, node in top.items():
			if key.startswith(("Variable Declaration", "Variable Definition")):
				name = node['name']
				if not self.var_accessed(name):
					del_nodes.append(key)

			if key.startswith(("Binary Operation", "Unary Operation", "Number Literal")):
				try:
					expr = self.simplify_numerical_expression({key : node})
				except SigNonConstantNumericalExpressionException: pass
				else:
					del_nodes.append(key)
					new_nodes.append(["Numerical Constant", eval(expr)])
					continue

			if key.startswith(valid_nodes):
				if type(node) is dict:
					expr = self.simplify(node)
					new_nodes.append([key, expr])
				elif type(node) is list:
					expr1 = self.simplify(node[0])
					expr2 = self.simplify(node[1])
					new_nodes.append([key, [expr1, expr2]])

		for del_node in del_nodes:
			del top[del_node]

		for new_node in new_nodes:
			top[new_node[0]] = new_node[1]

		return top