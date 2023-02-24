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

In this manner, many operations with structs require implicit casts and to some extent wastage of memory. Dynamic objects (which are yet to be introduced), will not need these implicit casts, but will be much slower that structs and will take up more memory, so structs are still recommended for objects that are not created arbitrarily at runtime.

## Next on the list to do:

- Test on Linux system
- Error throwing that actually shows the correct line
- Solve recursion errors in parser
- Remove weird parser bugs that result in a lot of errors
- Floats
- Array Literals
	- `arr[i]` syntax
	- Multidimensional array literals and `arr[i][j]` syntax
- Add asm optimizations
- Elif Blocks (not else-ifs)
- For loops
- 64-bit programs and types
- Hoist global-level funcs
- Being able to 'call' expressions - i.e. call an anonymous function - `(() => puts("hi"))()`
	- Recycle memory used by no-longer-referenced anonymous functions
- Namespaces
- Allow for both stdcall and cdecl functions
- Ability to move data into memory locations (e.x. `{deref(myptr) = 4}`, `{arr[1] = 2}` or `{person.age = 45}`)
- DLL integration
	- Imports
	- Exports
	- Fix DLL Compilation
- Maybe objects?
	- Both Structs (implemented like in C) and Dynamic Objects (which are much slower but can be created arbitrarily at runtime)
		- Export structs via parser's `struct_expr()` function and `export struct <name>` statement
		- Ability to change struct members
	- Object creation syntax
	- Object utils/dynamic objects
	- Object integration with C structs
	- Object destructuring
- Maybe type hinting or a VSCode extension

## Notes

- For the moment, \uXXXX and \XXXX escape codes are not permitted
