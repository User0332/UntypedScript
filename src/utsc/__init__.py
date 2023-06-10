#LOCAL MODULES
from .sequential_lexer import Lexer
from .uts_parser import Parser
from .ast_cleaner import ASTCleaner
from .ast_preprocessor import SyntaxTreePreproccesor
from .code_lowerer import CodeLowerer
from .compiler import Compiler
from .optimizer import AssemblyOptimizer
from .utils import (
	checkfailure, 
	throw, 
	warn, 
	throwerrors, 
	printwarnings,
	import_config,
	CYAN, 
	END,
	WARNING_NUMBERS, 
	ArgParser,
	SigTermTokenization
)

# OTHER UTILITY MODULES
from json import (
	dumps, dump
)

from importlib import import_module


#SYSTEM MODULES
from subprocess import (
	call as subprocess_call
)

from os import (
	getcwd, 
	listdir,
	chdir,
	remove as os_remove,
	rename as os_rename
)

from os.path import (
	isfile, 
	dirname,
	basename,
	normpath
)

from sys import (
	exit,
	argv,
	platform as sys_platform
)


COMPILER_EXE_PATH: str = dirname(
	import_module("utsc").__file__
).replace('\\', '/')

def main():
	argparser = ArgParser(description="UntypedScript Compiler", prog = "utsc")
	
	argparser.add_argument("-d", "--dump", type=str, help="show AST, tokens, disassembly, unprocessed or ALL (unprocessed is not included in ALL)")
	argparser.add_argument("-s", "--suppress-warnings", nargs='*', help="omit the warning numbers passed to this option (or omit all warnings by not passing an argument to this option)")
	argparser.add_argument("-w", "--warn", nargs='+', help="do not omit any warnings passed to this argument (the argument 'err' can also be passed to treat warnings as errors) --- this is evaluated after -s so it is possible to suppress all warnings using -s except the ones passed to this argument")
	argparser.add_argument("filename", nargs='?', default='', type=str, help='Source file')
	argparser.add_argument("-f", "--fmt", type=str, default="win32", help="format to compile to")
	argparser.add_argument("-O", "--optimization", type=int, default=0, help="Optimization level to apply. Can be 0 (default), 1, or 2")
	argparser.add_argument("-m", "--module", action="store_true", help="Compile this file without linking object files")
	outgroup = argparser.add_mutually_exclusive_group()
	outgroup.add_argument("-o", "--out", type=str, help="output filename")
	outgroup.add_argument("-e", "--executable", help="produce an executable using NASM and MinGW/gcc", action="store_true")
	outgroup.add_argument("-r", "--run", help="Run the uts program and exit", action="store_true")

	args = argparser.parse_args()
	
	omit_warnings = args.suppress_warnings
	executable = args.executable
	runfile = args.run
	compile_optimizations = args.optimization
	fmt = args.fmt
	modularize  = args.module
	print_warnings = args.warn if args.warn else []

	if "err" in print_warnings:
		utils.ERR_WARNINGS = True
		print_warnings = [item for item in print_warnings if item != "err"]

	if omit_warnings == []: utils.OMIT_WARNINGS = utils.WARNING_NUMBERS.copy()
	elif omit_warnings is not None:
		utils.OMIT_WARNINGS = omit_warnings

		for warning in omit_warnings:
			if warning not in WARNING_NUMBERS:
				warn(f"UTSC 008: Invalid warning number '{warning}' to omit -s (--suppress-warnings) (ignoring this argument)!")
	
	for warning in print_warnings:
		if warning not in WARNING_NUMBERS:
			warn(f"UTSC 008: Invalid warning number '{warning}' to not omit passed to -w (--warn) (ignoring this argument)!")
			continue

		try: utils.OMIT_WARNINGS.remove(warning)
		except ValueError: pass
		
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
			warn("UTSC 001: No source file specified. Assuming the below file.", f">{file}\n")	
		else:
			throw("Fatal Error UTSC 002: No valid source file found.")
			throwerrors()
			return 1

	try:
		with open(file, 'r') as f:
			code = f.read()
	except OSError:
		throw("Fatal Error UTSC 003: Either the specified source file could not be found, or permission was denied.")

	INPUT_FILE_PATH = dirname(file).replace("\\", "/")
	if INPUT_FILE_PATH == '':
		INPUT_FILE_PATH = "./"

	chdir(INPUT_FILE_PATH)

	basesource = ".".join(basename(file).split(".")[:-1])

	if args.out == None:
		out = basesource+".o"
		if (executable or runfile): out = basesource+".exe"
		else: warn("UTSC 004: -o option unspecified, assuming object file", f">{out}\n")
	elif not args.out.endswith((".asm", ".lst", ".json", ".o", ".dll", ".modinfo", ".structs", ".uts", ".exe", ".info")) and args.out != 'NULL':
		warn(f"UTSC 004: '{args.out}' is an invalid output file. Switching to object file by default.")
		out = basesource+".o"
	else:
		out = args.out

	if isfile("utsc-config.json"):
		config = import_config("utsc-config.json")
	else:
		config = import_config(f"{COMPILER_EXE_PATH}/utsc-config.json")
			
	throwerrors()
	printwarnings()
	checkfailure()

	lexer = Lexer(code)	

	try: tokens = lexer.tokenize()
	except SigTermTokenization: # lexer signaled to terminate compilation
		throwerrors()
		printwarnings()
		return 1

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

	parser = Parser(tokens, code)

	try:
		raw_ast = parser.parse()
	except RecursionError as e:
		throw(f"Fatal Error UTSC 005: Parser overran recursion limit - python: {e}")

		throwerrors()
		printwarnings()
		
		return 1

	raw_ast = ASTCleaner(raw_ast).clean()

	if compile_optimizations >= 1:
		simplifier = SyntaxTreePreproccesor(raw_ast)
		try: raw_ast = simplifier.simplify()
		except KeyError as e:
			throw(f"UTSC 007: Invalid AST expression inserted! python: key not found: {e}")

	ast = dumps(raw_ast, indent=1)

	if show in ("ast", "tree", "all"):
		ast_name_str = f"{CYAN}AST @File['{file}']{END}"
		print(f"Raw:\n\n\n\n{ast_name_str}\n{raw_ast}\n\n\n")
		print(f"Pretty-print:\n\n\n{ast_name_str}\n{ast}\n\n\n")

	if out.endswith(".json"):
		with open(out, 'w') as f:
			f.write(ast)

	if out.endswith(".uts"):
		try: lowered = CodeLowerer(raw_ast, code, parser.structs).lower()
		except KeyError as e:
			throw(f"UTSC 007: Invalid AST expression inserted! python: key not found: {e}")
			lowered = ""

		with open(out, 'w') as f:
			f.write(
				lowered
			)

	throwerrors()
	printwarnings()
	checkfailure()

	compiler = Compiler(raw_ast, code, COMPILER_EXE_PATH, INPUT_FILE_PATH, file, compile_optimizations, parser.structs, modularize)
	try: asm = compiler.traverse()
	except KeyError as e:
		throw(f"UTSC 007: Invalid AST expression inserted! python: key not found: {e}")
		asm = ""

	if (not modularize) and (not out.endswith(".modinfo")):
		for dependency in compiler.link_with:
			print(f"Link dependency (for '{basename(file)}') - {dependency!r}")

	if compile_optimizations >= 2:
		optimizer = AssemblyOptimizer(asm)
		asm = optimizer.optimize()

	throwerrors()
	printwarnings()
	checkfailure()

	if out.endswith(".modinfo"):
		with open(out, 'w') as f:
			dump(compiler.gen_modinfo(), f)

	if out.endswith(".structs"):
		with open(out, 'w') as f:
			dump(compiler.structs, f)

	if out.endswith(".info"):
		with open(out, 'w') as f:
			f.write(compiler.collected_info)

	if show in ("dis", "disassemble", "disassembly", "asm", "assembly", "all"):
		print("Disassembly:\n")
		print(asm)

	if show in ("unprocessed",):
		print("Generated Assembly Code (unprocessed, note that this assembly will not run properly - `-d unprocessed` is merely a tool to look into compiler internals):")
		print(compiler.unprocessed_text)

	if out.endswith((".asm", ".o", ".dll", ".exe")):
		asmname = ''.join(out.split('.')[:-1])+".asm"

		with open(asmname, 'w') as f:
			f.write(asm)

	if out.endswith((".o", ".dll", ".exe")):
		objname = ''.join(out.split('.')[:-1])+".o"
		tempname = f"{objname}.temp"

		try:
			if not modularize:
				subprocess_call(
					[
						config["nasmPath"], 
						asmname, 
						"-f", fmt, 
						"-o", tempname
					]
				)

				subprocess_call(
					[
						config["ldPath"],
						tempname,
						*compiler.link_with,
						'-relocatable',
						'-o', objname
					]
				)
				os_remove(tempname)
			else:
				subprocess_call(
					[
						config["nasmPath"], 
						asmname, 
						"-f", fmt, 
						"-o", objname
					]
				)

		except OSError as e:
			throw(f"UTSC 003: An error occurred while trying to compile '{out}' - python: {e}")

		try: os_remove(asmname)
		except FileNotFoundError: pass

	if out.endswith(".dll"):
		try: subprocess_call(
			[
				config["gccPath"],
				objname,
				"-shared",
				"-o", out,
				f"-O{compile_optimizations}"
			]
		)
		except OSError as e:
			throw(f"UTSC 003: An error occurred while trying to compile '{out}' - python: {e}")

		try: os_remove(objname)
		except FileNotFoundError: pass

	if out.endswith(".exe"):
		try: subprocess_call(
			[
				config["gccPath"],
				objname,
				"-o", out,
				f"-O{compile_optimizations}"
			]
		)
		except OSError as e:
			throw(f"UTSC 003: An error occurred while trying to compile '{out}' - python: {e}")

		try: os_remove(objname)
		except FileNotFoundError: pass

	if runfile:
		try:
			ret_code = subprocess_call([out]) # maybe print this later?
			os_remove(out)
		except OSError as e:
			throw(f"UTSC 003: A file went missing while trying to run & remove {out} (from {file}) - python: {e}")
		
	throwerrors()
	checkfailure()

	return 0

def configure():
	nasm_path = input("Path to NASM: ")
	gcc_path = input("Path to MinGW/GCC: ")
	ld_path = input("Path to ld linker: ")

	conf = {
		"nasmPath": nasm_path,
		"gccPath": gcc_path,
		"ldPath": ld_path
	}

	with open(f"{COMPILER_EXE_PATH}/utsc-config.json", 'w') as f:
		dump(conf, f)

	return 0

if __name__ == "__main__":
	try: exit(main())
	except KeyboardInterrupt:
		print("Interrupt")
		exit(1)
