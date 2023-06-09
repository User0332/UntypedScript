# Functions

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