# Async

UntypedScript currently provides one async library (`utils/win32/async` @ filepath (`/lib/utils/win32/async.uts`) -- only running on windows) which exposes simple functions to get things done in the background. To get started, import the `Async` namespace.

```ts
import namespace { Async } from "utils/win32/async"

const main = () => {

}
```

Then, use `Async.Execute_AcceptsCallback` to execute a function that accepts a callback as an argument. You will have to write the code to call the callback yourself.

```ts
import namespace { Async } from "utils/win32/async"
import { printf } from "<libc>"

const main = () => {
    Async.Execute_AcceptsCallback(
        (callback) => {
            printf("Hello, World!\n")
            callback() // this is the code to call the callback
        },
        // below is the callback
        () => printf("The function is complete!\n")
    )
}
```

Or you could use the `ObjectAPI` to create an executor that you can use later. This time, the function must accept an executor object, which has properties on it such as `func` (the function being executed), `callback` (the callback function), `AddCallback` (a method to add a callback),
and `Start` (starts a new instance of the function). In order to call the callback, one must call `executor.callback()`

```ts
import namespace { Async } from "utils/win32/async"
import { printf } from "<libc>"

const main = () => {
    const executor = Async.ObjectAPI.CreateExecutor(
        (executor_obj) => {
            printf("Hello, World!\n")
            executor_obj.callback() // this is the code to call the callback
        },
    )

    executor.AddCallback(() => printf("The function is complete!\n"), executor)

    executor.Start(executor)
}
```

You may add a callback to the executor after starting the thread, and if the thread finishes before the callback is attached, then it will wait until a callback is attached so that it can call it (see source code of function `Async.WaitForCallback(this)`).

```ts
    ...
    executor.Start(executor)

    executor.AddCallback(() => printf("The function is complete!\n"), executor) // if the thread is already done, this will execute as soon as it is attached
    ...
```

Since it is up to the caller to write the code that calls the callback function, the caller may decide to have the callback recieve a result as an argument instead of leaving a function with no parameters.