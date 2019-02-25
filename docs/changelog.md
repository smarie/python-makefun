# Changelog

### 1.0.1 - minor: fixed PyPi doc

### 1.0.0 - New parameters, new goodie, and bugfix

`@with_signature` :

 - now exposes all options of `create_function`. Fixed [#12](https://github.com/smarie/python-makefun/issues/12).
 - now correctly sets the module name by default. Fixes [#13](https://github.com/smarie/python-makefun/issues/13)
 - now accepts `None` as the new `func_signature` to declare that the signature is identical to the decorated function. This can be handy to just change the docstring or module name of a function for example. Fixes [#15](https://github.com/smarie/python-makefun/issues/15)


`create_function` and `@with_signature`:

 - New `modulename` parameter to override the module name. Fixes [#14](https://github.com/smarie/python-makefun/issues/14)
 - the handler is now available as a field of the generated function (under `__call_handler__`). New `addhandler` parameter (default: True) controls this behaviour. Fixes [#16](https://github.com/smarie/python-makefun/issues/16)


Misc:

 - New goodie to manipulate signatures: `add_signature_parameters`.
 - Fixed dependencies for documentation auto-build.

### 0.5.0 - New helper function, and bugfix

New helper function `remove_signature_parameters`.

Fixed issue with `@with_signature` when argument is a `Signature`. Fixes [#11](https://github.com/smarie/python-makefun/issues/11) 

### 0.4.0 - New `@with_signature` decorator, and `create_function` accepts functions

New decorator `@with_signature` to change the signature of a callable. Fixes [#3](https://github.com/smarie/python-makefun/issues/3)

`create_function` now accepts that a function be passed as a signature template. Fixes [#10](https://github.com/smarie/python-makefun/issues/10)

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
