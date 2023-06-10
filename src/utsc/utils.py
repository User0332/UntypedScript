from argparse import ArgumentParser
from json import load
from json.decoder import JSONDecodeError

from os.path import isfile
from sys import (
	stderr, 
	exit
)

# Error buffers
errors = ""
warnings = ""
thrown = False
WARNING_NUMBERS = ["001", "004", "008", "205", "314", "310"]
OMIT_WARNINGS: list[str] = []
ERR_WARNINGS = False
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

	linenolen = len(lineno)-1
	code+=(" "*linenolen)+"^^^\n"
	return code

def strgetline(string: str, target_index: int):
	current_idx = 0

	for i, line in enumerate(string.splitlines()):
		for j in range(len(line)):
			if current_idx == target_index: return [line, j, i+1]

			current_idx+=1

		if current_idx == target_index: return [line, len(line)-1, i+1]

		current_idx+=1

	return ["<<<untypedscript: could not locate code>>>", 0, 0]
#


#Error throwing functions
def throw(message: str, code=""):
	global errors
	global thrown

	errors+=f"{FAIL}ERROR: {message+END}\n{code}"
	thrown = True

def fmt_type(tok_type: str):
	return f"<{tok_type.lower()}>"

def warn(string: str, code=""):
	global warnings

	for warning in OMIT_WARNINGS:
		if string.startswith(f"UTSC {warning}"): return

	if ERR_WARNINGS: return throw(string, code)

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

def import_config(fname: str) -> dict:
	if not isfile(fname):
		throw(f"Fatal Error UTSC 006: Config file {fname} does not exist (use utsc-configure to fix)!")
		return
		
	with open(fname, 'r') as f:
		try: conf = load(f)
		except JSONDecodeError:
			throw(f"Fatal Error UTSC 006: Config file {fname} is not valid JSON!")
			return

	try: # validate keys
		assert isfile(conf["nasmPath"])
		assert isfile(conf["gccPath"])
		assert isfile(conf["ldPath"])

		return conf
	except KeyError as e:
		throw(f"Fatal Error UTSC 006: Some config keys are missing (failed when trying to find {e!r}, use utsc-configure to fix the config)")
	except AssertionError:
		throw("Fatal Error UTSC 006: At least one config value does not exist as a file (the config is invalid)!")

# Custom Exceptions used in the ast preprocessor/lexer
class SigNonConstantNumericalExpressionException(Exception): pass

class SigTermTokenization(Exception): pass
#

# Utility Classes
class Token:
	def __init__(self, token=None):
		token = token if token else [None, None, None]

		self.type: str = token[0]
		self.value: str = token[1]
		self.idx: int = token[2]

	def __repr__(self):
		return str(self.type)+" -> "+str(self.value)

	def __str__(self):
		return str([self.value, self.type])

class ArgParser(ArgumentParser):
	def error(self, message):
		throw(f"Fatal Error UTSC 004: {message.capitalize()}")
		throwerrors()
		exit(1)

class SymbolTable:
	def __init__(self, code, parent=None):
		self.symbols: dict[str, dict[str]] = {}
		self.parent: SymbolTable = parent
		self.code = code

	def get(self, name, index, fallback_qual_name=None) -> dict:
		attr = self.symbols.get(name, None)
		if attr is None:
			if self.parent:
				return self.parent.get(name, index, fallback_qual_name=fallback_qual_name)
			else:
				line, idx, linenum = strgetline(self.code, index)
				code = formatline(line, idx, linenum)

				err = f"UTSC 307: Name Error: Name '{name}' not defined"
				if fallback_qual_name: err+=f" (potential undefined namespaced property being accessed -> '{fallback_qual_name}')"
				throw(err+'.', code)
				
				return None
		
		return attr

	def declare(self, name: str, dtype: str, sizeb: int, address: str, beforeinstr: str=""):
		if self.symbols.get(name, {}).get("type", "").startswith("CONST"):
			throw(f"UTSC 306: Name Error: Attemped to redeclare to constant '{name}'")
			return

		self.symbols[name] = {
			"type": dtype, 
			"size": sizeb, 
			"address": address,
			"beforeinstr": beforeinstr,
			"value" : None
		}

	def assign(self, name: str, value, index: int):
		var = self.get(name, index)
		if var is None: return

		# ADD/TODO?: check if value is too large to be held (size > self.symbols[name]['size'])

		if (var["type"].startswith("CONST")) and (var["value"] is not None):
			code = get_code(self.code, index)
			throw(f"UTSC 306: Name Error: Attemped to reassign to constant '{name}'", code)
			return

		var["value"] = value

		return var["address"]

	def delete(self, name: str):
		del self.symbols[name]
#