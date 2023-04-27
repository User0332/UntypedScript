# Standard for lib/utils/win32/async.uts

Exports:
```ts
namespace Async
{
    (function) WaitForCallBack(this)(function) Execute_AcceptsCallBack(func_that_accepts_callback, callback)
    namespace ObjectAPI
    {
        (function) CreateExecutor(func_that_accepts_callback_obj)
    }
}
```