# Variable Types and Assignments

## Variable Types

### Const Variables

Variables defined with the type keyword `const` cannot be changed. However, creating a [pointer](pointers.md#pointers) to the variable and then dereferencing that pointer can change the value.

E.x.
```js
const main = () => {
    const x = 4

    x = 5 // illegal

    deref (ref (x)) = 5 // legal, but not recommended
}

export { main }
```

### Let variables

Variables defined with the `let` keyword may have their values changed.

### Struct Variables

Variables defined with [struct](structs.md#structs) types must have either a `const` or `let` keyword, then the `struct` keyword, and then the struct name to constitute their type. For example, a `const` variable defined as Person struct object would look something like this:

```ts
const struct Person myperson = [/* values of struct members here */]
```

## Assignment Types

Like in C or JavaScript, there are multiple assignment types/operators. They are simple and are as follows:

```js
= // simple assignment

+= // add the value to the variable
-= // subtract the value from the variable
*= // multiply the variable by the value
/= // divide the variable by the value
```

The above special assignment types (`+=`, `-=`, `*=`, `/=`) are lowered to form the following pattern:

```js
varname = varname<operator>value
```

E.x.
```js
// this
x+=4

// is semantically equivalent to this
x = x+4
```
