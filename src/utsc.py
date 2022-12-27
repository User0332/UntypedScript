#LOCAL MODULES
from lexer import Lexer
from uts_parser import Parser
from ast_cleaner import ASTCleaner
from ast_preprocessor import SyntaxTreePreproccesor
from compiler import Compiler
from optimizer import AssemblyOptimizer
from utils import (
	checkfailure, 
	throw, 
	warn, 
	throwerrors, 
	printwarnings, 
	CYAN, 
	END, 
	ArgParser
)

# OTHER UTILITY MODULES
from json import (
	loads, 
	dumps
)


#SYSTEM MODULES
from subprocess import (
	call as subprocess_call
)

from os import (
	getcwd, 
	listdir,
	chdir
)

from os.path import (
	isfile, 
	dirname,
	basename
)

from sys import (
	exit, 
	argv
)


#Indepenedent Environment Constants
COMPILER_EXE_PATH = dirname(argv[0]).replace('\\', '/')
DEFAULT_MODIFIER_PATH = f"{COMPILER_EXE_PATH}/modifiers"
DEFAULT_IMPORT_PATH = f"{COMPILER_EXE_PATH}/imports"
#


def main():
	argparser = ArgParser(description="PogScript Compiler", prog = "pogc2")
	
	argparser.add_argument("-d", "--dump", type=str, help="show AST, tokens, disassembly, or ALL")
	argparser.add_argument("-s", "--suppresswarnings", help="suppress all warnings", action="store_true", default=False)
	argparser.add_argument("filename", nargs='?', default='', type=str, help='Source file')
	argparser.add_argument("-O", "--optimization", type=int, default=0, help="Optimization level to apply. Can be 0 (default), 1, or 2")
	outgroup = argparser.add_mutually_exclusive_group()
	outgroup.add_argument("-o", "--out", type=str, help="output file")
	outgroup.add_argument("-e", "--executable", help="run assemble.ps1 and produce an executable using NASM and MinGW", action="store_true")
	
	

	args = argparser.parse_args()
	
	warnings = not args.suppresswarnings
	executable = args.executable
	compile_optimizations = args.optimization
	
	try:
		show = args.dump.lower()
	except AttributeError:
		show = None 

	file = args.filename

	if file == "":
		for filename in listdir(getcwd()):
			if isfile(filename) and filename.endswith(".uts"):
				file = filename

		if file != "":
			warn("UTSC 011: No source file specified. Assuming the below file.", f">{file}\n")	
		else:
			throw("Fatal Error UTSC 022: No valid source file found.")
			throwerrors()
			return 1

	try:
		with open(file, 'r') as f:
			code = f.read()
	except OSError:
		throw("Fatal Error UTSC 022: Either the specified source file could not be found, or permission was denied.")
	
	#Dependent Constants
	INPUT_FILE_PATH = dirname(file).replace("\\", "/")
	if INPUT_FILE_PATH == '':
		INPUT_FILE_PATH = "./"
	#

	chdir(INPUT_FILE_PATH)

	basesource = ".".join(basename(file).split(".")[:-1])

	if args.out == None:
		out = basesource+".asm"
		if not executable: warn("UTSC 006: -o option unspecified, assuming assembly", f">{out}\n")
	elif not args.out.endswith((".asm", ".lst", ".json")) and args.out != 'NULL':
		warn(f"UTSC 004: '{args.out}' is an invalid output file. Switching to assembly by default.")
		out = basesource+".asm"
	else:
		out = args.out

			
	throwerrors()
	if warnings: printwarnings()
	checkfailure()

	lexer = Lexer(code)

	tokens = lexer.tokenize()
	
	tokens.sort()

	formatted_list = ["[\n"]

	formatted_list += [str(token)+"\n" for token in tokens] + ["]"]

	if show in ("tok", "toks", "token", "tokens", "all"):
		print("Raw:\n\n\n")
		print(tokens)
		print("\n\n")
		print("Pretty-print:\n\n\n")
		print(''.join(formatted_list))
		print(f"Length of tokens: {len(tokens)}\n\n")

	if out.endswith(".lst"):
		with open(out, "w") as f:
			f.write("".join(formatted_list))

	parser = Parser(tokens.tokens, code)

	raw_ast = parser.parse()

	raw_ast = ASTCleaner(raw_ast).clean()

	if compile_optimizations >= 1:
		simplifier = SyntaxTreePreproccesor(raw_ast)
		raw_ast = simplifier.simplify()

	ast = dumps(raw_ast, indent=1)

	if show in ("ast", "tree", "all"):
		ast_name_str = f"{CYAN}AST @File['{file}']{END}"
		print(f"Raw:\n\n\n\n{ast_name_str}\n{raw_ast}\n\n\n")
		print(f"Pretty-print:\n\n\n{ast_name_str}\n{ast}\n\n\n")

	if out.endswith(".json"):
		with open(out, "w") as f:
			f.write(ast)

	throwerrors()
	if warnings: printwarnings()
	checkfailure()

	compiler = Compiler(raw_ast, code, COMPILER_EXE_PATH, INPUT_FILE_PATH)
	asm = compiler.traverse()

	if compile_optimizations >= 2:
		optimizer = AssemblyOptimizer(asm)
		asm = optimizer.optimize()

	throwerrors()
	if warnings: printwarnings()
	checkfailure()

	if show in ("dis", "disassemble", "disassembly", "asm", "assembly", "all"):
		print("Disassembly:\n")
		print(asm)

	if out.endswith(".asm"):
		with open(out, "w") as f:
			f.write(asm)

	if executable:
		try:
			subprocess_call(["powershell", f"{COMPILER_EXE_PATH}/assemble.ps1", out.removesuffix(".asm")])
		except OSError:
			throw("UTSC 022: assemble.bat is missing, destroyed, or broken")

	throwerrors()
	checkfailure()

	return 0

if __name__ == "__main__":
	exit(main())
