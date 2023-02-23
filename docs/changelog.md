# Changelog

### x.y.z - in progress

- Fixed a `KeyError` happening when `wraps` is provided with a string `new_sig`. Fixes
  [#90](https://github.com/smarie/python-makefun/issues/90)

### 1.15.1 - bugfixes

 - Fixed `ValueError: Invalid co_name` happening on python 2 when the name of a function to create starts or ends with
   `_` or contains a double `__` . Fixes [#91](https://github.com/smarie/python-makefun/issues/91)

### 1.15.0 - More PEP-compliant `wraps`

 - `wraps` now always sets the `__wrapped__` attribute, and also sets the `__signature__` attribute when the signature changes, as specified by PEP 362. PR []() by [#86](https://github.com/smarie/python-makefun/pull/86) by [lucaswiman](https://github.com/lucaswiman).

### 1.14.0 - Support for lambda functions

 - `create_wrapper`, `create_function`, `wraps` and `with_signature` now support lambda functions. They also accept a new parameter `co_name` to define the name to be used in the compiled code. PR [#80](https://github.com/smarie/python-makefun/pull/80) by [andrewcleveland](https://github.com/andrewcleveland).

### 1.13.1 - Fixed regression with generators in python 3.5

 - Fixed an issue where using `partial` on a generator function in python 3.5 was raising a `SyntaxError`. Fixed [#79](https://github.com/smarie/python-makefun/issues/79)

### 1.13.0 - Support for async generator functions

 - async generator functions are now supported (See [PEP525](https://www.python.org/dev/peps/pep-0525/)). Fixed [#77](https://github.com/smarie/python-makefun/issues/77). [PR#78](https://github.com/smarie/python-makefun/pull/78) by [broglep-work](https://github.com/broglep-work).

### 1.12.1 - Bugfix

 - Fixed `TypeError` when a `func` attribute is present on the function provided to `create_function`. Fixed [#76](https://github.com/smarie/python-makefun/issues/76)

### 1.12.0 - Refactoring and consistency improvement

 - Fixed `partial` so that :
   - when no argument is provided, it is equivalent to `wraps(f)(f)`. That is, the `__wrapped__` attribute is set. Fixed [#73](https://github.com/smarie/python-makefun/issues/73)
   - it sets the `func` attribute just as `functools.partial` does. Fixed [#75](https://github.com/smarie/python-makefun/issues/75) 
 - Removed `pytest-cases` dependency as it was a circular one. Fixed [#68](https://github.com/smarie/python-makefun/issues/68)
 - Now using `flake8` for qualimetry and `genbadge` for badges. Fixed [#71](https://github.com/smarie/python-makefun/issues/71)
 - Restructured project so that tests are truly independent, to ease rpm/apt/etc. packaging. Fixed [#69](https://github.com/smarie/python-makefun/issues/69)

### 1.11.3 - bugfix with default values representable but not evaluable

 - When a default value `v` in a signature is representable but its `eval(repr(v))` raises an exception, created signatures would raise an exception instead of automatically protecting the symbol. PR [#67](https://github.com/smarie/python-makefun/pull/67) by [gcalmettes](https://github.com/gcalmettes).

### 1.11.2 - bugfix with chained `@wraps`

 - Fixed issue where `@wraps` does not remove the `__wrapped__` attribute when it wraps an already-wrapped function, and modifies its signature. Fixes [#66](https://github.com/smarie/python-makefun/issues/66)

### 1.11.1 - bugfix

 - Fixed a bug happening when trying to generate a function where `float('inf')` is used as a default value. Fixes [#63](https://github.com/smarie/python-makefun/issues/63).

### 1.11.0 - `partial` bugfixes and improvements + new `wraps` parameters

 - `@wraps` now has new arguments `prepend_arg` and `append_arg` to quickly prepend or append a new parameter to a function signature. Fixes [#65](https://github.com/smarie/python-makefun/issues/65)

 - `add_signature_parameters` can now receive string parameter names in its `first` and `last` arguments.

 - Improved generated docstring for `partial` with better support for preset positional args.

 - `partial`'s behaviour is now aligned with the one in `functools.partial` in terms of arguments order and kind. Fixes [#64](https://github.com/smarie/python-makefun/issues/64)

 - Bug fix: passing preset positional arguments to `partial` does not wipe out the rest of the signature any more. Fixes [#62](https://github.com/smarie/python-makefun/issues/62)

### 1.10.2 - Github actions test

 - Technical release: validation of the new github actions workflow.

### 1.10.1 - Github actions migration

 - Technical release: validation of the new github actions workflow for PyPi deployment.

### 1.10.0 - Removing arguments easily in `@wraps`

 - `@wraps` now offers a `remove_params` argument allowing one to remove an argument from the exposed signature, typically to create and inject it in the wrapper. Fixes [#60](https://github.com/smarie/python-makefun/issues/60)

### 1.9.5 - Bugfix with `partial` when f has no args

 - `partial` can now be used to create a copy of a function with no args. Fixed `ValueError: Cannot preset 0 positional args, function case_second has only 0 args.`. Fixed [#59](https://github.com/smarie/python-makefun/issues/59)

### 1.9.4 - removed six dependency

 - Removed unused `six` dependency. Note: this version will ship in conda forge.

### 1.9.3 - Minor compatibility fixes with functools.partial

 - `@wraps` can now be used to wrap a `functools.partial`. Fixed [#57](https://github.com/smarie/python-makefun/issues/57)

 - `create_function` now correctly reuses information from the partialized function if a `functools.partial` is used as the implementation.

 - `create_function` now raises a more explicit error when no `func_name` can be found.

 - `makefun.partial` now generates a signature that is more consistent with `functools.partial`. Fixes [#58](https://github.com/smarie/python-makefun/issues/58)

### 1.9.2 - packaging improvements

 - packaging improvements: set the "universal wheel" flag to 1, and cleaned up the `setup.py`. In particular removed dependency to `six` for setup and added `py.typed` file, as well as set the `zip_safe` flag to False. Removed tests folder from package. Fixes [#54](https://github.com/smarie/python-makefun/issues/54)

### 1.9.1 - `@compile_fun` bugfix

Fixed `OSError: could not get source code` or `IOError: could not get source code` when `@compile_fun` is used on a function that depends on an already-compiled function. Fixed [#51](https://github.com/smarie/python-makefun/issues/51)

### 1.9.0 - `@compile_fun` improvements, bugfix and better exception

`@compile_fun`: added capability to disable recursive compilation (`recurse` arg) , and to exclude some names from compilation (`except_names` arg). Fixed [#49](https://github.com/smarie/python-makefun/issues/49) and [#50](https://github.com/smarie/python-makefun/issues/50)

Fixed issue `ValueError: Cell is empty` with `@compile_fun`. Fixed [#48](https://github.com/smarie/python-makefun/issues/48)

Now raising an `UndefinedSymbolError` when a symbol is not known at compilation time. One step towards [#47](https://github.com/smarie/python-makefun/issues/47)

### 1.8.0 - new `@compile_fun` goodie

New goodie `@compile_fun` decorator to `compile` a function so that it can not be navigated to using the debugger. Fixes [#46](https://github.com/smarie/python-makefun/issues/46)

### 1.7.0 - minor goodies update

`add_signature_parameters` now accepts that one specifies a custom index where to insert the new parameters.

### 1.6.11 - Added __version__ attribute

Added `__version__` attribute to comply with PEP396, following [this guide](https://smarie.github.io/python-getversion/#package-versioning-best-practices). Fixes [#45](https://github.com/smarie/python-makefun/issues/45).

### 1.6.10 - Fixed dependencies 2

Fixed `six` dependency: also declared as a setup dependency.

### 1.6.9 - Fixed dependencies

Added missing `six` dependency explicitly.

### 1.6.8 - Improved performance 

 * Improved performance of inner method `get_signature_string` (used by all entry points) after profiling.

### 1.6.7 - Increased tolerance to function signatures in python 2

 * In python 2 some libraries such as `attrs` can modify the annotations manually, making `signature` return a string representation that is not compliant with the language version. This raised a `SyntaxError` in previous versions. The new version silently removes all these annotations in python versions that do not support them. Fixes [#39](https://github.com/smarie/python-makefun/issues/39).

### 1.6.6 - Bug fix

 * Fixed yet another nasty varpositional-related bug :). Fixes [#38](https://github.com/smarie/python-makefun/issues/38).

### 1.6.5 - Bug fix

 * Fixed `NameError` in case of unknown symbols in type hints. Fixes [#37](https://github.com/smarie/python-makefun/issues/37).

### 1.6.4 - Bug fix and minor improvement

 * Fixed PEP8 error in source code. Fixes [#35](https://github.com/smarie/python-makefun/issues/35).

 * Now string signatures can contain a colon. Fixes [#36](https://github.com/smarie/python-makefun/issues/36)
 
### 1.6.3 - Bug fix with type hints in signature

Fixed bug when the return type annotation of the function to create contains non-locally available type hints. Fixes [#33](https://github.com/smarie/python-makefun/issues/33).

### 1.6.2 - Bug fix with type hints in signature

Fixed bug when the signature of the function to create contains non-locally available type hints. Fixes [#32](https://github.com/smarie/python-makefun/issues/32).

### 1.6.1 - `with_partial` and `partial` minor bug fix

Fixed `partial` to support missing and empty docstring. Fixes [#31](https://github.com/smarie/python-makefun/issues/31).

### 1.6.0 - added `with_partial` and `partial`

New method `partial` that behaves like `functools.partial`, and equivalent decorator `@with_partial`. Fixes [#30](https://github.com/smarie/python-makefun/issues/30).

### 1.5.1 - bug fix

`add_signature_parameters` now correctly inserts parameters in the right order when they are prepended (using `first=`). Fixed [#29](https://github.com/smarie/python-makefun/issues/29).

### 1.5.0 - Major refactoring and bugfixes

**Function creation API:**

 - renamed all `handler` into `impl` for clarity. Fixes [#27](https://github.com/smarie/python-makefun/issues/27).
 - renamed `addsource` and `addhandler` arguments as `add_source` and `add_impl` respectively, for consistency
 - signatures can not be provided as a callable anymore - that was far too confusing. If the reference signature is a callable, then use `@wraps` or `create_wrapper`, because that's probably what you want to do (= reuse not only the signature but also all metadata). Fixes [#26](https://github.com/smarie/python-makefun/issues/26).
 - the function name is now optional in signatures provided as string.
 - now setting `__qualname__` attribute
 - default function name, qualname, doc and module name are the ones from `func_impl` in `create_function` and `@with_signature`, and are the ones from the wrapped function in `create_wrapper` and `@wraps` as intuitively expected. Fixes [#28](https://github.com/smarie/python-makefun/issues/28).
 
 **Wrappers:**
 
  - `@wraps` and `create_wrapper` now offer a `new_sig` argument. In that case the `__wrapped__` attribute is not set. Fixes [#25](https://github.com/smarie/python-makefun/issues/25).
  - `@wraps` and `create_wrapper` now correctly preserve the `__dict__` and other metadata from the wrapped item. Fixes [#24](https://github.com/smarie/python-makefun/issues/24)
 

### 1.4.0 - Non-representable default values are now handled correctly

When a non-representable default value was used in the signature to generate, the code failed with a `SyntaxError`. This case is now correctly handled, by storing the corresponding variable in the generated function's context. Fixes [#23](https://github.com/smarie/python-makefun/issues/23).

### 1.3.0 - Aliases for signature-preserving wrapper scenarios

 - Now providing a `@wraps`, equivalent of `functools.wraps`; and a `create_wrapper` equivalent of `functools.update_wrapper`. Fixes [#21](https://github.com/smarie/python-makefun/issues/21)

 - `@with_signature` now does not override the `__name__` when signature is provided as a function. Fixes [#22](https://github.com/smarie/python-makefun/issues/22)

 - `add_signature_parameters` now accepts that parameters are provided as single elements (not necessarily iterables)

 - Updated documentation


### 1.2.0 - `@with_signature` supports `None`

`None` can be used as the desired signature of `@with_signature`. This indicated that the user does not want to create a new function but only wants to update the metadata. Fixes [#20](https://github.com/smarie/python-makefun/issues/20).


### 1.1.2 - Fixes

Fixed `isgeneratorfunction` for old python versions, see [decorator#63](https://github.com/micheles/decorator/pull/63).

Python<3.3-specific function body is now not loaded at all if not needed.

### 1.1.1 - `@with_signature` fix

`inject_as_first_arg` was missing from `@with_signature`, added it. Fixed [#18](https://github.com/smarie/python-makefun/issues/18).

### 1.1.0 - Support for generators and coroutines

Now `create_function` and `@with_signature` create the same kind of function than the handler. So if it is a generator, a generator-based coroutine, or an async coroutine, the generated function will adapt. Fixes [#6](https://github.com/smarie/python-makefun/issues/6).

### 1.0.2 - Fixed `@with_signature`

Now a string signature can be provided to `@with_signature` without problem. Fixed [#17](https://github.com/smarie/python-makefun/issues/17).

### 1.0.1 - minor: fixed PyPi doc

### 1.0.0 - New parameters, new goodie, and bugfix

`@with_signature` :

 - now exposes all options of `create_function`. Fixed [#12](https://github.com/smarie/python-makefun/issues/12).
 - now correctly sets the module name by default. Fixes [#13](https://github.com/smarie/python-makefun/issues/13)
 - now accepts `None` as the new `func_signature` to declare that the signature is identical to the decorated function. This can be handy to just change the docstring or module name of a function for example. Fixes [#15](https://github.com/smarie/python-makefun/issues/15)


`create_function` and `@with_signature`:

 - New `module_name` parameter to override the module name. Fixes [#14](https://github.com/smarie/python-makefun/issues/14)
 - the handler is now available as a field of the generated function (under `__func_impl__`). New `addhandler` parameter (default: True) controls this behaviour. Fixes [#16](https://github.com/smarie/python-makefun/issues/16)


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

 - Renamed `_call_` into `_func_impl_` in the generated code.

Misc:

 - Added `pytest-cases` dependency for tests.

### 0.1.0 - First public version

First version created, largely inspired by [`decorator`](https://github.com/micheles/decorator)
