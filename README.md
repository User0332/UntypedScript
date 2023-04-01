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

Note that structs in this langauge are very limited - they cannot be nested (i.e. you cannot have a struct member whose type is a struct) or returned from functions unless their type is declared explicitly. For example, take the following code:
```js
import { printf } from "<libc>"

struct Person
{
	name, age
}

struct Car
{
	owner
}

const get_person = () => {
	// WILL WORK
	const struct Person person = ["Joe", 23]

	return person

	// WILL ALSO WORK (produces same effect as the above code, since types don't actually exist and the structs are just syntax sugar for arrays)
	return ["Joe", 23]

	// WILL NOT WORK
	return (struct Person ["Joe", 23])
}

const main = () => {
	// WILL NOT WORK
	printf(get_person().name)

	// WILL WORK
	const struct Person person = get_person()
	printf(person.name)


// -----------------------------------------

	const struct Car mycar = [person]

	// WILL NOT WORK
	printf(mycar.owner.name)

	// WILL WORK
	const struct Person car_owner = mycar.owner

	printf(car_owner.name)
}

export { main }
```

In this manner, many operations with structs require implicit casts and to some extent wastage of memory. Dynamic objects do not need these implicit casts, but are much slower than structs and will also take up more memory than them (even with struct implicit casting), so structs are still recommended for objects that are not created arbitrarily at runtime.

## Structs vs. Objects

At the moment (although the test conducted is very small), there seems to be a neglibile performance difference while using structs versus using objects. They average out at 25.14575ms for structs and 25.843025ms for objects. However, it is important to note that the struct average would be about one millisecond lower if there was no outlier.

![Chart of Struct vs. Object Performance](readme-assets/struct-obj-perf.png)

## Next on the list to do:

- Test on Linux system
- Error throwing that actually shows the correct line
- Solve recursion errors in parser
- Remove weird parser bugs that result in a lot of errors
- Floats
- Add asm optimizations (in progress, constant task)
- Elif Blocks (not else-ifs)
- For loops
- 64-bit programs and types
- Hoist global-level funcs
- Namespaces
- Allow for stdcall functions
- DLL integration
	- Imports
	- Exports
	- Fix DLL Compilation
- Maybe objects?
	- Both Structs (implemented like in C) and Dynamic Objects (which are much slower but can be created arbitrarily at runtime)
		- Export structs via parser's `struct_expr()` function and `export struct <name>` statement
	- Object utils
	- Object integration with C structs
	- Object destructuring
- Type hinting for optimization
- May integrate a sort of lightweight runtime in the future (for a try-catch framework, etc.) that itself runs on the C runtime
	- If this is added there will be an option to compile with the UTS runtime and an option to compile without the runtime (both executables will be standalone (as long as the C runtime exists), the UTS runtime will be automatically linked into the output)
- VSCode extension

## Notes

- For the moment, \uXXXX and \XXXX escape codes are not permitted, and may continue to not be permitted in the future (this feature may never be added)
