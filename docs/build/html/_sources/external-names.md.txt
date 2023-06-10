# External Names

## Normal Names
Normal names include globally defined variables and functions. These can be exported using a simple `export` statement, like so:

```js
const MY_EXPORTED_VARIABLE = 5

const add = (a, b) => a+b

export {
    MY_EXPORTED_VARIABLE,
    add
}
```

They can be imported with:

```js
import {
    MY_EXPORTED_VARIABLE,
    add
} from "path/to/the/module"
```

Note that module name should not include the `.uts` file extension.

## Namespaces
Namespaces defined using a `namespace` statment can be exported using an `export namespace` statement, with the fully qualified name of the namespace. Exporting a namespace automatically exports all symbols within it and all nested namespaces and their symbols. However, exporting a nested namespace does not expose the parent namespace's attributes.

```ts
namespace MyNamespace {...}

namespace OtherNamespace
{
    namespace NestedNamespace {...}
}

export namespace {
    MyNamespace,
    OtherNamespace.NestedNamespace
}
```

They can be imported with a similar statement:

```ts
import namespace { OtherNamespace.NestedNamespace } from "path/to/module-without-.uts-file-extension"
```

## Structs

Structs do not need an `export` statement; they are all automatically exported. Like all other imports, structs can be imported with a lookalike statement:

```ts
import struct { Person } from "person-struct" // imports struct 'Person' from person-struct.uts
```