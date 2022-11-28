from re import (
	finditer as re_finditer,
	MULTILINE as RE_MULTILINE,
	IGNORECASE as RE_IGNORECASE
)

from utils import (
	throw, 
	get_code,
	TokenSorter
)

#Lexer
class Lexer():
	def __init__(self, source_code: str):
		self.source_code = source_code

	#Uses regex patterns to search for tokens
	def tokenize(self):
		self.modifier_commands = []
		tokens = []

		working_code = self.source_code

		comments = re_finditer("^//.*$", working_code, RE_MULTILINE)
		for comment in comments:
			working_code = working_code.replace(comment.group(0), " "*len(comment.group()), 1)

		keywds = [
			["^import\s|\simport\s", "IMPORT", RE_MULTILINE],
			["^from\s|\sfrom\s", "FROM", RE_MULTILINE],
			["^export\s|\sexport\s", "EXPORT", RE_MULTILINE],
			["^return\s|\sreturn\s", "RETURN", RE_MULTILINE],
			["^namespace\s|\snamespace\s", "NAMESPACE", RE_MULTILINE],
			["^let\s|\slet\s", "LET", RE_MULTILINE],
			["^const\s|\sconst\s", "CONST", RE_MULTILINE],
			["^is\s|\sis\s", "IDENTITY_COMPARISON", RE_MULTILINE],
			["^not\s|\snot\s|^or\s|\sor\s|^and\s|\sand\s", "LOGICAL_OP", RE_MULTILINE],
			["^if\s|\sif\s|^else\s|\selse\s", "CONDITIONAL_KEYWD"]
		]

		regexes = [
			['".*?"', "STRING"],
			["=>", "ARROW_FUNC"],
			["==|>=|<=|>|<", "COMPARISON_OP"],
			["=", "ASSIGNMENT"],
			["[\d]+\.[\d]+", "FLOAT"],
			["[\.:,\[\]\(\)}{]", "SPECIAL"],
			["\*\*|[/\*\-\+]", "OPERATOR"],
			*keywds,
			["[a-z_]\w*", "IDENTIFIER", RE_IGNORECASE],
			["\d+", "INTEGER"],
			['\n', "NEWLINE"]
		]

		for regex in regexes:
			matches = re_finditer(regex[0], working_code, regex[2]) if len(regex) > 2 else re_finditer(regex[0], working_code)

			for match in matches:
				start = match.start()+1 if regex in keywds else match.start()
				group = match.group().strip('\n') # leave newline in for newline regex match
				tokens.append([regex[1], group.strip(), start])
				working_code = working_code.replace(group, " "*len(group), 1)

		unlexed = "".join(working_code.split())
		if unlexed != "":
			code = get_code(self.source_code, working_code.index(unlexed[0]))
			
			throw(f"POGCC 019: Unknown token {unlexed[0]}", code)

		return TokenSorter(tokens)
#
