# Compiler Errors/Warnings

Below is a full list of compiler errors/warnings (and what their numbers mean).

Section pattern: `[name-of-module] (nXX)`, where `n` is the number that will precede all error numbers thrown from that module. Ex. a name error from the compiler module would have the preceding module number `3`, and the error number `07`, creating a fully qualified error number of `307` (`Error UTSC 307`)

## Main UTSC module (0XX)
`01` No specificed source file, assuming first valid file

`02` No valid source file found

`03` File not found

`04` Command line argument error/warning

`05` Parser ran into Python error (specific to implementation, hopefully fixed in the future)

`06` Config Error

`07` Invalid AST insert

## Lexer (1XX)

`01` Invalid escape code in string

`02` Unexpected EOF

`03` Invalid float literal

`04` Unexpected token encountered

## Parser (2XX)

`01` Missing statement delimeter

`02` Unexpected EOF

`03` Expected token

`04` Constant variable was not assigned a value

`05` Name Error

`06` File not found

`07` Invalid AST Expression

## Compiler (3XX)

`01` File not found

`02` Module couldn't be compiled

`03` Invalid global-scope variable value

`04` Reassignment in global scope

`05` Malformed/Unimplemented AST Node encountered

`06` Tried to reassign constant variable

`07` Name Error

`08` Invalid target for expression (ex. `const i = return`)

`09` Multiple symbol definition

`10` Cannot account for multiple symbol definitions

`11` Special or exceptional error/warning

`12` Tried to import a namespace from a non-UntypedScript file

`13` Cannot assign to expression

## Other Modules (4XX)
