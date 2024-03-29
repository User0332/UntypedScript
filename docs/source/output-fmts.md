# Compiler Output Formats

This section covers all the file formats that can be passed to the `-o` (`--out`) option of the compiler to specify output filename.

No matter which output format is specified, the compiler will still always invoke the lexer, parser, and compiler (assembly generator).

## Tokens

The compiler will output a list of tokens generated by the lexer if the compiler is asked to output a `.lst` file.

## AST

The compiler will output the abstract syntax tree (in a JSON format) generated by the code if asked to output a `.json` file.

## Assembly

The compiler will generate NASM-valid, x86, intel-syntax assembly (for output filenames ending in `.asm`).

## Object Files, Executables, and DLLs

When asked to output an object file (`.o`), executable (`.exe`), or DLL (`.dll`), the compiler will first generate assembly, then invoke `nasm`, and then invoke `ld` or `gcc` to create the desired output. Note that DLLs aren't actually guaranteed to work at the moment.

## Lowered Code

Code lowering happens when the compiler is asked to output a `.uts` file. Instead of outputting the input file, the compiler will parse and generate AST for the input file, using the AST to boil down the code to its most basic UntypedScript form. When the compiler lowers code, the output is not guaranteed to be syntactically correct. It may be impossible to feed the ouput UntypedScript code back into the compiler because it generates code based off of AST, and some language features modify the AST in ways that would be illegal in normal code. An example is shown when a `heapalloc` statement is lowered:

Input code:
```js
import { malloc, free } from "<libc>"

const main = () => {
    const myvar = heapalloc ([1, 2, 3, 4])

    free(myvar)
}

export { main }
```

Lowered code:
```js
import { malloc,free } from "<libc>"

const main = (() => {
	const myvar = (let .temp0 = ((malloc)(16))
	(deref ((.temp0)+((0)*(4)))) = (1)
	(deref ((.temp0)+((1)*(4)))) = (2)
	(deref ((.temp0)+((2)*(4)))) = (3)
	(deref ((.temp0)+((3)*(4)))) = (4)
	(.temp0))

	(free)(myvar)

	return (0)
})

export { main }
```

Additionally, the code lowerer does not always support all features (meaning output code may not actually be semantically the same as input code), and is usually the last to be updated (if it is). The code lowerer is merely a look into some compiler internals.

## Structs File

An output filename ending in `.structs` will dump a JSON object of struct data (from the current and imported files) into the output file.

## Module Info

When asked to output a `.modinfo` file, the compiler will generate a list of exported names and module data from import `.uts` modules (in a JSON format). Note that these files are usually generated as tempfiles for the compiler to help it with compiling/analyzing imports in `.uts` files.

## Compiler Collected Info

A `.info` output filename will have the compiler dump some of its collected info about the compilation into the file. This is mostly useless information and still for a feature that is in development (having the compiler collect more info to provide potential information).
