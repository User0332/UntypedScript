# Get Started

If you haven't installed the UntypedScript compiler, head over to [Installation](installation.md#installing-untypedscript).

UntypedScript is a mix of JavaScript and C-like features. It has a JS-like syntax, but runs on the CRT.

Start by creating a new `.uts` file. Let's name it `hello.uts`. In `hello.uts`, write the following code:

`hello.uts`
```js
import { puts } from "<libc>"

const main = () => {
    puts("Hello, UntypedScript!")

    return 0
}

export { main }
```

So, what does this suspiciously JavaScript-like code do? Well, there are a few different things going on. First, we use an `import` statement to import the `puts` function from the C standard library. Next, we define our main function in a global variable called `main`, creating a function using the `(args) => { code }` arrow function syntax borrowed from JS. Next, we make a call to `puts`, passing it a string argument. Finally, we return a value of `0` (success) from our main function (the return statement is not required, but it is recommended to be explicit). At the bottom of our file, we add an `export` statement and expose our `main` function globally. This is important, because if a symbol is not exported, it is only visible to the current file, and the C runtime will be unable to run our program.

Let's compile the program with the following command:

```sh
utsc -e hello.uts -O2
```

The `-e` option specifies to the compiler that we want the output to be an executable format (win32 by default, win32 is also the only format currently supported). The compiler will run `nasm`, `gcc`, and `ld` in the background to create an exectuable for us. We can mimic the same behavior by passing `-o hello.exe`, as `utsc` will infer the output file format from the extension. Next, we pass the filename of the program that we want to compile, and lastly we'll pass an `-O2` flag to try to optimize the file as much as possible. For more info on command-line options, you can type the command `utsc -h`.

Lastly, run the generated `hello.exe` file.

```
>>> utsc -e hello.uts -O2
>>> ./hello.exe
Hello, UntypedScript!
>>>
```

Great! You've just written your first ever UntypedScript program! Continue to [Variables](variables.md#variables-and-symbols) to learn more features.