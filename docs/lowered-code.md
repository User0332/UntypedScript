# Lowered Code

When the compiler lowers code (eg. with an output file ending in .uts), the output is not guaranteed to be syntactically correct. It may be impossible to feed the ouput UntypedScript code back into the compiler because it generates code based off of AST, and some language features modify the AST in ways that would be illegal in normal code. An example is shown when a `heapalloc` statement is lowered:

