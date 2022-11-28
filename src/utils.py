from argparse import ArgumentParser

from sys import (
	stderr, 
	exit
)

# Error buffers
errors = ""
warnings = ""
thrown = False
#


# Color Constants
FAIL = "\033[31m"
END = "\033[0m"
BLUE = "\033[34m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
#


#Getting code for error throwing
def get_code(string: str, index: int):
	return formatline(*strgetline(string, index))

def formatline(line: str, idx: int, linenum: int):
	lineno = "ln "+str(linenum)
	code = BLUE+lineno+END+" "+line+"\n"
	for i, char in enumerate(line):
		if char == "\t":
			code+="\t"
		else:
			code+=" "

		if i == idx:
			break

	linenolen = len(lineno)+1
	code+=(" "*linenolen)+"^^^\n"
	return code

def strgetline(string: str, index: int):
	current_idx = 0
	for i, line in enumerate(string.splitlines()):
		current_idx+=1
		for j in range(1, len(line)):
			current_idx+=1
			if current_idx == index:
				return [line, j, i+1]

		if current_idx == index:
			return [line, j+1, i+1]

	return ["", 0, 0]
#


#Error throwing functions
def throw(message, code=""):
	global errors
	global thrown

	errors+=f"{FAIL}ERROR: {message+END}\n{code}"
	thrown = True

def fmt_type(tok_type: str):
	return f"<{tok_type.lower()}>"

def warn(string, code=""):
	global warnings

	warnings+=f"{YELLOW}WARNING: {string}{END}\n{code}"

def throwerrors():
	global errors

	stderr.write(errors)
	errors = ""

def printwarnings():
	global warnings

	stderr.write(warnings)
	warnings = ""

def checkfailure():
	exit(1) if thrown else None
#


# Custom Exception used in the ast preprocessor
class NonConstantNumericalExpressionException(Exception):
	pass
#

# Utility Classes
class Token:
	def __init__(self, token=None):
		token = token if token else [None, None, None]
		self.type = token[0]
		self.value = token[1]
		self.idx = token[2]

	def __repr__(self):
		return str(self.type)+" -> "+str(self.value)

	def __str__(self):
		return str([self.value, self.type])

class TokenSorter:
	def __init__(self, tokens: list):
		self.tokens = tokens

	def __repr__(self):
		return str(self.tokens)

	def __len__(self):
		return len(self.tokens)

	def __iter__(self):
		return self.tokens.__iter__()

	def __next__(self):
		return self.tokens.__next__()

	def sort(self):
		positions = {}
		tokens = []
	
		for token in self.tokens:
				positions[token[2]] = [token[0], token[1], token[2]]

		token_positions = sorted(positions)

		for pos in token_positions:
			tokens.append(positions[pos])

		tokens.append(["EOF", "Reached end of file", tokens[-1][2]+1])

		self.tokens = tokens
		self.positions = positions

class ArgParser(ArgumentParser):
	def error(self, message):
		throw(f"Fatal Error POGCC 031: {message.capitalize()}")
		throwerrors()
		exit(1)

class SymbolTable:
	def __init__(self, code, parent=None):
		self.symbols = {}
		self.parent: SymbolTable = parent
		self.code = code

	def get(self, name, index):
		attr = self.symbols.get(name, None)
		if attr is None:
			if self.parent:
				return self.parent.get(name, index)
			else:
				line, idx, linenum = strgetline(self.code, index)
				code = formatline(line, idx, linenum)
				throw(f"POGCC 027: Name Error: Name '{name}' not defined.", code)
		
		return attr

	def declare(self, name, dtype, size, address):
		self.symbols[name] = {
			"type" : dtype, 
			"size" : size, 
			"address" : address, 
			"value" : None
			}

	def assign(self, name, value, index):
		if name not in self.symbols.keys():
			
			line, idx, linenum = strgetline(self.code, index)
			code = formatline(line, idx, linenum)
			throw(f"POGCC 027: Name Error: Attemped to assign to undeclared variable '{name}'", code)
		
		#check if value is too large to be held (size > self.symbols[name]['size'])


		if (self.symbols[name]["type"] == "CONST") and self.symbols[name]["value"] is not None:
			line, idx, linenum = strgetline(self.code, index)
			code = formatline(line, idx, linenum)
			throw(f"POGCC 027: Name Error: Attemped to assign to constant '{name}'", code)

		self.symbols[name]["value"] = value
		return self.symbols[name]["address"]

	def delete(self, name):
		del self.symbols[name]
#