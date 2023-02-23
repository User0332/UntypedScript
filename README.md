# UntypedScript

Project that branched off of the discontinued [PogScript](https://github.com/User0332/PogScript), with a considerably different JavaScript-like syntax. UntypedScript's goal is to become an easy-to-understand and easy-to-write language with speeds comparable to that of C or C++.

Boils down to assembly code. As per the name, includes no form of a type system - you are on your own! Type hints may be introduced in the future. Sample Hello World - (other programs can be found in `tests/`)

```js
import puts from "<libc>"

const main = () => {
	puts("Hello World!")

	return 0
}

export { main }
```

Compile it with `utsc -e helloworld.uts` and run `helloworld.exe`, or just run `utsc -r helloworld.uts`! (You need NASM and MinGW installed - currently only tested on Windows)

## Next on the list to do:

- Test on Linux system
- Error throwing that actually shows the correct line
- Solve recursion errors in parser
- Remove weird parser bugs that result in a lot of errors
- Array Literals
- Add asm optimizations
- Elif Blocks (not else-ifs)
- For loops
- 64-bit programs and types
- Hoist global-level funcs
- Being able to 'call' expressions - i.e. call an anonymous function - `(() => puts("hi"))()`
	- Recycle memory used by no-longer-referenced anonymous functions
- Namespaces
- Allow for both stdcall and cdecl functions
- DLL integration
	- Imports
	- Exports
	- Fix DLL Compilation
- Maybe objects?
	- Both Structs (implemented like in C) and Dynamic Objects (which are much slower but can be created arbitrarily at runtime)
		- Export structs via `struct_expr()` and `export struct <name>` statement
	- Object creation syntax
	- Object utils/dynamic objects
	- Object integration with C structs
	- Object destructuring
- Maybe type hinting or a VSCode extension

## Notes

- For the moment, \uXXXX and \XXXX escape codes are not permitted
