# Right now, the ASTCleaner class just removes empty expressions
# e.g. {"Expression @Idx[33]": {} } => {}

class ASTCleaner:
	def __init__(self, ast: dict) -> None:
		self.ast = ast

	def clean(self, top: dict=None) -> dict:
		top = top if top else self.ast

		key: str; node: dict

		for key, node in list(top.items()):
			if type(node) != dict: continue

			if node:
				self.clean(node)
				continue

			if key.startswith("Expression"):
				del top[key]

		return top