# Changelog

### 0.3.0 - Ability to generate functions from `Signature`

Functions can now be created from a `Signature` object, in addition to string signatures. This unlocks many useful use cases, among easily creating function wrappers. Note: the inner function that provides this feature is `get_signature_from_string`. Fixes [#8](https://github.com/smarie/python-makefun/issues/8)

Improved design by getting rid of the regular expression parser to check parameters definition. This assumes that the compiler will correctly raise exceptions when a string signature is not correct, and that `inspect.signature` or `funcsigs.signature` works correctly at detecting all the parameter kinds and annotations on the resulting function. It seems like a fair assumption... Fixes [#9](https://github.com/smarie/python-makefun/issues/9).

### 0.2.0 - Various new features and improvements

`create_function`:

 - `create_function` does not require users to prepend `"def "` to the signature anymore. Fixed [#5](https://github.com/smarie/python-makefun/issues/5)

 - Return annotations are now supported. Fixes [#4](https://github.com/smarie/python-makefun/issues/4).

 - Type hint as comments are supported but the generated function loses the annotations because `inspect.signature` loses the annotation too in that case. Fixes [#7](https://github.com/smarie/python-makefun/issues/7)

 - Variable-length arguments such as `*args` and `**kwargs` are now properly handled. Fixes [#2](https://github.com/smarie/python-makefun/issues/2)

 - Handler functions can now receive the dynamically created function as first argument, by using `create_function(func_signature, func_handler, inject_as_first_arg=True)`. Fixes [#1](https://github.com/smarie/python-makefun/issues/1)

 - Renamed `_call_` into `_call_handler_` in the generated code.

Misc:

 - Added `pytest-cases` dependency for tests.

### 0.1.0 - First public version

First version created, largely inspired by [`decorator`](https://github.com/micheles/decorator)
