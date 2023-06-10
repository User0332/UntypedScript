# Variables and Symbols

Variables can be declared using the following syntax:

`type name`

E.x.

```js
let x

OR

const x
```

Declared variables will have space reserved for them but will start with an undefined value.

Variables can be assigned values using the following syntax:

`name = value`

E.x.

```js
x = 5
```

Variables can be defined (declared and assigned) using the following syntax:

`type name = value`

E.x.

```js
let x = 5

OR

const x = 5
```

Defining a variable is equivalent to declaring it and then assigning it a value.


## Global Variables

Global variables (variables declared outside of a function) can only be defined with constant expressions, which include expressions that can be evaluated numerically at compile time (such as `1+2*3`, which will be replaced by the constant `7`), string literals, like `"Hello, World!"`, and [function definitions](functions.md#normal-functions). Global variables may be assigned different values inside of functions. Global variables can be [exported](external-names.md#normal-names).

## Local Variables

Local variables (variables defined inside a function), on the other hand, can be defined with any value and can be reassigned any value. However, they can only be accessed within the function (scope) that they are declared in[*](scopes.md), and cannot be exported.
