# UntypedScript

Project that branched off of the discontinued [PogScript](https://github.com/User0332/PogScript), with a considerably different JavaScript-like syntax.

Boils down to assembly code. As per the name, includes no form of a type system - you are on your own! Type hints may be introduced in the future. Sample Hello World - (other programs can be found in `tests/`)

```js
import puts from "<libc>"

const main = () => {
    puts("Hello World!")

    return 0
}

export main
```

Compile it with `utsc -e helloworld.uts` and run `helloworld.exe`! (You need NASM and MinGW installed)

## Next on the list to do:

- Imports/Modules
- Function receiving arguments
- Refs/Derefs/Pointers
- If/Elif/Else Statements
- Namespaces
- Object creation syntax
- Object utils/dynamic objects
- Object integration with C structs
- Object destructuring
- Maybe type hinting or a VSCode extension
