# UntypedScript

Project that branched off of the discontinued [PogScript](https://github.com/User0332/PogScript), with a considerably different JavaScript-like syntax.

Boils down to assembly code. As per the name, includes no form of a type system - you are on your own! Type hints may be introduced in the future. Sample Hello World - (other programs can be found in `tests/`)

```js
import puts from "<libc>"

const main = () => {
    puts("Hello World!")
}

export main
```

Note that `return` is not implemented yet, but will be in the near future.

Compile it with `utsc -e helloworld.uts` and run `helloworld.exe`!