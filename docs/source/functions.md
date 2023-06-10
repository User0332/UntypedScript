# Anonymous Functions

## Normal Functions

In UntypedScript, all functions are anonymous. They are defined in a similar fashion to JavaScript arrow functions:

```js
(/* arguments */) => {
    // code
}
```

An example addition function could look like this:
```js
const add = (a, b) => {
    return a+b
}
```

Or this (as in JavaScript, functions that only need to return with a single expression can be written on one line):
```js
const add = (a, b) => a+b
```

Both of the above functions will generate the same assembly; there is no semantic difference.

Regular anonymous functions defined within other functions cannot access their paren't function's scope. In order to access a parent function's scope, see the below options

## Local-only Functions

Local-only functions can access the scope of their parent function (as it is at the time of creation). Define it by putting the `localonly` keyword in front of the function expression. However, as per the name, `localonly` functions may only be used within the function they were defined in; returning the from the function or using them in a different function will result in undefined behavior. Functions may not be defined with the `localonly` keyword in the global [scope](scopes.md#global-scope). For more `localonly` details, see [`localonly` function scope](scopes.md#local-only-function-scope). Not thread-safe.

```js
const main = () => {
    let mystr = "Hello, World!"

    let func = localonly (() => {
        mystr = "abc" // can access and change this variable

        func() // can access and change this variable

        newvar = 5 // cannot access or change this variable, since it is defined after the function is defined
    })

    let newvar = 4

    mystr = "new string!" // this change will be reflected in all later calls to func() 

    func()
}

```

## Heap-allocated Functions

Heap-allocated functions can access the scope of **all** parent functions (as they are at the time of creation). Define it by putting the `heapalloc` keyword in front of the function expression. In order to use `heapalloc` functions (currently only supported on win32), you must import `HeapFuncAlloc`, `HeapFuncProtect`, and `HeapFuncFree` from `utils/win32/libheapfunc`. Heap-allocated functions may be used outside of the function that they were defined in, but they must be freed using `HeapFuncFree`. Unlike `localonly` functions, changes in the parent's scope (e.g. changing a variable value) after the heap-allocated function is defined will **not** be reflected within the `heapalloc` function. Functions may not be defined with the `heapalloc` keyword in the global [scope](scopes.md#global-scope). For more heap-allocated function details, see [`heapalloc` function scope](scopes.md#heap-allocated-function-scope). Not guranteed to be thread-safe.

```js
import {
    HeapFuncAlloc,
    HeapFuncProtect,
    HeapFuncFree
} from "utils/win32/libheapfunc"

const getfunc = () => {
    let myvar = 4

    return heapalloc (() => {
        myvar = 3 // can be accessed, but any value changes will not be reflected in the outside scope

        const abc = 19

        return heapalloc (() => {
            myvar = 8+abc // variables from both parent scopes can be accessed
        })
    })
}

const main = () => {
    const heapfunc = getfunc()

    heapfunc()

    const newfunc = heapfunc()

    newfunc()

    // free the functions to prevent memory leaks
    HeapFuncFree(newfunc)
    HeapFuncFree(heapfunc)
}

```