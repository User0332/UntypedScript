import string
from utils import (
	get_code, throw,
	SigTermTokenization,
)

Token = list[
	str, # type
	str, # value
	int  # index
]

class Lexer:
	def __init__(self, code: str) -> None:
		self.code = code
		self.i = 0
		self.num_chars = len(code)
		
		self.VALID_HEX = "0123456789ABCDEF"
		self.KEYWORDS = {
			"import": "IMPORT",
			"from": "FROM",
			"export": "EXPORT",
			"return": "RETURN",
			"namespace": "NAMESPACE",
			"let": "LET",
			"const": "CONST",
			"while": "LOOPING_KEYWD",
			"for": "LOOPING_KEYWD",
			"is": "IDENTITY_COMPARISON",
			"not": "LOGICAL_OP",
			"or": "LOGICAL_OP",
			"and": "LOGICAL_OP",
			"if": "CONDITIONAL_KEYWD",
			"else": "CONDITIONAL_KEYWD",
			"asm": "INLINE_ASSEMBLY",
			"ref": "ADDR_OP",
			"deref": "ADDR_OP",
			"struct": "STRUCT",
			"heapalloc": "HEAP_ALLOC",
			"localonly": "LOCALLY_EXPOSED_FUNC",
		}
		self.SPECIALS = "()[]{}.:,;"
		self.OPERATORS = (
			*"+-*/%", "**"
		)
		self.VALID_WORD = string.ascii_letters+'_'
		self.VALID_DIGITS = string.digits
		self.VALID_IDENT = self.VALID_WORD+self.VALID_DIGITS

	def build_word(self) -> Token:
		start = self.i

		word = ""

		while self.i < self.num_chars:
			char = self.code[self.i]

			if self.i == start:
				word+=char

				self.i+=1
				continue

			if char in self.VALID_IDENT:
				word+=char

				self.i+=1
				continue

			break
			
		if word in self.KEYWORDS.keys():
			return [
				self.KEYWORDS[word], word, start
			]

		return [
			"IDENTIFIER", word, start
		]


	def build_string(self) -> Token:
		start = self.i

		self.i+=1 # pass over the double quote

		in_escape_code = False
		in_hex_esc = False
		hex_code = ""

		string = ""

		while self.i < self.num_chars:
			char = self.code[self.i]

			if (char == '"'):
				if in_escape_code:
					string+='"'
					in_escape_code = False

					self.i+=1
					continue

				return ["STRING", string, start]

			if (char == '\\'):
				if in_escape_code:
					string+='\\'
					in_escape_code = False

					self.i+=1
					continue
				
				in_escape_code = True

				self.i+=1
				continue

			if in_escape_code:
				if char in (
					'n', 'b', 'e', 'f', 'r', 'a',
					't', 'v'
				):
					string+=eval(f"'\\{char}'")
					in_escape_code = False

					self.i+=1
					continue

				if char == 'x':
					in_hex_esc = True
					in_escape_code = False

					self.i+=1
					continue

			if in_hex_esc:
				if char not in self.VALID_HEX:
					code = get_code(self.code, self.i)

					throw("UTSC 101: Invalid Escape Code - Terminating Tokenization!", code)
					raise SigTermTokenization()

				hex_code+=char

				if len(hex_code) == 2:
					string+=eval(f"'\\x{hex_code}'")
					
					hex_code = ""
					in_hex_esc = False

				self.i+=1
				continue

			string+=char

			self.i+=1

		code = get_code(self.code, start)

		throw(f"UTSC 102: Unterminated String - Terminating Tokenization", code)
		raise SigTermTokenization()

	def build_number(self):
		start = self.i

		num = ""

		while self.i < self.num_chars:
			char = self.code[self.i]

			if char in self.VALID_DIGITS:
				num+=char

				self.i+=1
				continue

			if char == '.':
				if '.' not in num:
					num+='.'

					self.i+=1
					continue

				code = get_code(self.code, self.i)

				throw("UTSC 103: Multiple dots in numerical constant - Terminating Tokenization", code)
				raise SigTermTokenization()

			break

		if num.endswith('.'):
			code = get_code(self.i-1)
			
			throw("UTSC 103: Numerical constant ends with a dot - Terminating Tokenization", code)
			raise SigTermTokenization


		if '.' in num:
			return [
				"FLOAT",
				num,
				start
			]

		return [
			"INTEGER",
			num,
			start
		]

	def build_eq_op(self):
		start = self.i

		self.i+=1

		char = self.code[self.i]

		if char == '=':
			return [
				"COMPARISON_OP",
				"==",
				start
			]
		
		if char == '>':
			return [
				"ARROW_FUNC",
				"=>",
				start
			]

		self.i-=1

		return [
			"ASSIGNMENT",
			'=',
			start
		]

	def build_r_ang_bracket_op(self):
		start = self.i

		self.i+=1

		char = self.code[self.i]

		if char == '=':
			return [
				"COMPARISON_OP",
				">=",
				start
			]

		self.i-=1

		return [
			"COMPARISON_OP",
			'>',
			start
		]

	def build_l_ang_bracket_op(self):
		start = self.i

		self.i+=1

		char = self.code[self.i]

		if char == '=':
			return [
				"COMPARISON_OP",
				"<=",
				start
			]

		self.i-=1

		return [
			"COMPARISON_OP",
			'<',
			start
		]

	def try_comment(self):
		self.i+=1

		char = self.code[self.i]

		if char == '/':
			while char != '\n':
				self.i+=1

				try: char = self.code[self.i]
				except IndexError:
					return "line"

			return "line"
		
		if char == '*':
			while 1:
				self.i+=1

				try: char = self.code[self.i]
				except IndexError:
					code = get_code(self.code, self.i-2)

					throw("UTSC 102: Block comment was not closed - terminating tokenization", code)
					raise SigTermTokenization()
				
				if (char == '*') and (self.i+1 < self.num_chars) and (self.code[self.i+1] == '/'):
					self.i+=1
					return "block"

		self.i-=1 # move back to original pos

		return None # explicit failure

	def tokenize(self) -> list[Token]:
		tokens: list[Token] = []

		# purpose: was there some whitespace, a newline, or an operator between tokens such as keywords and identifiers?
		tok_spaced = True 

		while self.i < self.num_chars:
			char = self.code[self.i]		

			if tok_spaced:
				if char == '"':
					tokens.append(
						self.build_string()
					)

					tok_spaced = False
					
					self.i+=1
					continue

				if char in self.VALID_WORD:
					tokens.append(
						self.build_word()
					)

					tok_spaced = False
					continue

				if char in self.VALID_DIGITS:
					tokens.append(
						self.build_number()
					)

					tok_spaced = False
					continue

			if char == '\n':
				tokens.append(
					["NEWLINE", '\n', self.i]
				)

				tok_spaced = True

				self.i+=1
				continue

			if char in string.whitespace:
				tok_spaced = True

				self.i+=1
				continue

			if char == '=':
				tokens.append(
					self.build_eq_op()
				)

				tok_spaced = True

				self.i+=1
				continue
			
			if char == '>':
				tokens.append(
					self.build_r_ang_bracket_op()
				)

				tok_spaced = True

				self.i+=1
				continue

			if char == '<':
				tokens.append(
					self.build_l_ang_bracket_op()
				)

				tok_spaced = True

				self.i+=1
				continue

			if char == '!' and self.code[self.i+1] == '=':
				tokens.append(
					["COMPARISON_OP", "!=", self.i]
				)

				tok_spaced = True

				self.i+=2

				continue

			if char == '/': # try to build a comment
				res =  self.try_comment()

				if res == "line":
					tokens.append(
						["NEWLINE", '\n', self.i]
					)

					self.i+=1
					continue

				if res == "block":
					self.i+=1
					continue

			if char in self.OPERATORS:
				tokens.append(
					["OPERATOR", char, self.i]
				)

				tok_spaced = True

				self.i+=1
				continue

			if char in self.SPECIALS:
				tokens.append(
					["SPECIAL", char, self.i]
				)

				tok_spaced = True

				self.i+=1
				continue

			# token left unlexed
			code = get_code(self.code, self.i)

			throw(f"UTSC 104: Invalid Syntax - Terminating Tokenization @ char {char!r}", code)
			raise SigTermTokenization()

		tokens.append(
			["EOF", "Reached End of File", self.num_chars]
		)

		return tokens