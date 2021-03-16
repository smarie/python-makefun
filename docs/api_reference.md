# API reference

In general, using `help(symbol)` is the recommended way to get the latest documentation. In addition, this page provides an overview of the various elements in this package.

## Main symbols

### `create_function`

```python
def create_function(func_signature: Union[str, Signature],
                    func_impl: Callable[[Any], Any],
                    func_name: str = None,
                    inject_as_first_arg: bool = False,
                    add_source: bool = True,
                    add_impl: bool = True,
                    doc: str = None,
                    qualname: str = None,
                    module_name: str = None,
                    **attrs):
```

Creates a function with signature `func_signature` that will call `func_impl` when called. All arguments received by the generated function will be propagated as keyword-arguments to `func_impl` when it is possible (so all the time, except for var-positional or positional-only arguments that get passed as *args. Note that positional-only does not yet exist in python but this case is already covered because it is supported by `Signature` objects).

`func_signature` can be provided in different formats:

 - as a string containing the name and signature without 'def' keyword, such as `'foo(a, b: int, *args, **kwargs)'`. In which case the name in the string will be used for the `__name__` and `__qualname__` of the created function by default.
   
 - as a `Signature` object, for example created using `signature(f)` or handcrafted. Since a `Signature` object does not contain any name, in this case the `__name__` and `__qualname__` of the created function will be copied from `func_impl` by default.

All the other metadata of the created function are defined as follows:

 - default `__name__` attribute (see above) can be overridden by providing a non-None `func_name`
 - default `__qualname__` attribute (see above) can be overridden by providing a non-None `qualname`
 - `__annotations__` attribute is created to match the annotations in the signature.
 - `__doc__` attribute is copied from `func_impl.__doc__` except if overridden using `doc`
 - `__module__` attribute is copied from `func_impl.__module__` except if overridden using `module_name`

Finally two new attributes are optionally created

 - `__source__` attribute: set if `add_source` is `True` (default), this attribute contains the source code of the generated function
 - `__func_impl__` attribute: set if `add_impl` is `True` (default), this attribute contains a pointer to `func_impl`


**Parameters:**

 * `func_signature`: either a string without 'def' such as "foo(a, b: int, *args, **kwargs)" or "(a, b: int)", or a `Signature` object, for example from the output of `inspect.signature` or from the `funcsigs.signature` backport. Note that these objects can be created manually too. If the signature is provided as a string and contains a non-empty name, this name will be used instead of the one of the decorated function.
   
 * `func_impl`: the function that will be called when the generated function is executed. Its signature should be compliant with (=more generic than) `func_signature`
   
 * `inject_as_first_arg`: if `True`, the created function will be injected as the first positional argument of `func_impl`. This can be handy in case the implementation is shared between several facades and needs to know from which context it was called. Default=`False`
   
 * `func_name`: provide a non-`None` value to override the created function `__name__` and `__qualname__`. If this is `None` (default), the `__name__` will default to the one of `func_impl` if `func_signature` is a `Signature`, or to the name defined in `func_signature` if `func_signature` is a `str` and contains a non-empty name.
   
 * `add_source`: a boolean indicating if a '__source__' annotation should be added to the generated function (default: True)
   
 * `add_impl`: a boolean indicating if a '__func_impl__' annotation should be added to the generated function (default: True)
   
 * `doc`: a string representing the docstring that will be used to set the __doc__ attribute on the generated function. If None (default), the doc of func_impl will be used.
   
 * `qualname`: a string representing the qualified name to be used. If None (default), the `__qualname__` will default to the one of `func_impl` if `func_signature` is a `Signature`, or to the name defined in `func_signature` if `func_signature` is a `str` and contains a non-empty name.
   
 * `module_name`: the name of the module to be set on the function (under __module__ ). If None (default), `func_impl.__module__` will be used.
   
 * `attrs`: other keyword attributes that should be set on the function. Note that `func_impl.__dict__` is not automatically copied.

### `@with_signature`

```python
def with_signature(func_signature: Union[str, Signature],
                   func_name: str = None,
                   inject_as_first_arg: bool = False,
                   add_source: bool = True,
                   add_impl: bool = True,
                   doc: str = None,
                   qualname: str = None,
                   module_name: str = None,
                   **attrs
                   ):
```

A decorator for functions, to change their signature. The new signature should be compliant with the old one.

```python
@with_signature(<arguments>)
def impl(...):
    ...
```

is totally equivalent to `impl = create_function(<arguments>, func_impl=impl)` except for one additional behaviour:

 - If `func_signature` is set to `None`, there is no `TypeError` as in create_function. Instead, this simply applies the new metadata (name, doc, module_name, attrs) to the decorated function without creating a wrapper. `add_source`, `add_impl` and `inject_as_first_arg` should **not** be set in this case.

 * `func_signature`: the new signature of the decorated function. Either a string without 'def' such as "foo(a, b: int, *args, **kwargs)" or "(a, b: int)", or a `Signature` object, for example from the output of `inspect.signature` or from the `funcsigs.signature` backport. Note that these objects can be created manually too. If the signature is provided as a string and contains a non-empty name, this name will be used instead of the one of the decorated function. Finally `None` can be provided to indicate that user wants to only change the medatadata (func_name, doc, module_name, attrs) of the decorated function, without generating a new function.
   

 * `inject_as_first_arg`: if `True`, the created function will be injected as the first positional argument of `func_impl`. This can be handy in case the implementation is shared between several facades and needs to know from which context it was called. Default=`False`

 * `func_name`: provide a non-`None` value to override the created function `__name__` and `__qualname__`. If this is `None` (default), the `__name__` will default to the one of `func_impl` if `func_signature` is a `Signature`, or to the name defined in `func_signature` if `func_signature` is a `str` and contains a non-empty name.

 * `add_source`: a boolean indicating if a '__source__' annotation should be added to the generated function (default: True)
   
 * `add_impl`: a boolean indicating if a '__func_impl__' annotation should be added to the generated function (default: True)
   
 * `doc`: a string representing the docstring that will be used to set the __doc__ attribute on the generated function. If None (default), the doc of the decorated function will be used.
   
 * `qualname`: a string representing the qualified name to be used. If None (default), the `__qualname__` will default to the one of `func_impl` if `func_signature` is a `Signature`, or to the name defined in `func_signature` if `func_signature` is a `str` and contains a non-empty name.
   
 * `module_name`: the name of the module to be set on the function (under __module__ ). If None (default), the `__module__` attribute of the decorated function will be used.
   
 * `attrs`: other keyword attributes that should be set on the function. Note that the full `__dict__` of the decorated function is not automatically copied.


### `@wraps`

```python
def wraps(f,
          new_sig: Union[str, Signature] = None,
          prepend_args: Union[str, Parameter, Iterable[Union[str, Parameter]]] = None,
          append_args: Union[str, Parameter, Iterable[Union[str, Parameter]]] = None,
          remove_args: Union[str, Iterable[str]] = None,
          func_name: str = None,
          inject_as_first_arg: bool = False,
          add_source: bool = True,
          add_impl: bool = True,
          doc: str = None,
          qualname: str = None,
          module_name: str = None,
          **attrs
          ):
```

A decorator to create a signature-preserving wrapper function.

It is similar to `functools.wraps`, but 

 - relies on a proper dynamically-generated function. Therefore as opposed to `functools.wraps`, 
   
    - the wrapper body will not be executed if the arguments provided are not compliant with the signature - instead a `TypeError` will be raised before entering the wrapper body. 
    - the arguments will always be received as keywords by the wrapper, when possible. See [documentation](./index.md#signature-preserving-function-wrappers) for details.

 - **you can modify the signature** of the resulting function, by providing a new one with `new_sig` or by providing a list of arguments to remove in `remove_args`, to prepend in `prepend_args`, or to append in `append_args`. See documentation on [full](./index.md#editing-a-signature) and [quick](./index.md#easier-edits) signature edits for details.

Comparison with `@with_signature`: `@wraps(f)` is equivalent to

    `@with_signature(signature(f),
                     func_name=f.__name__,
                     doc=f.__doc__,
                     module_name=f.__module__,
                     qualname=f.__qualname__,
                     __wrapped__=f,
                     **f.__dict__,
                     **attrs)`

In other words, as opposed to `@with_signature`, the metadata (doc, module name, etc.) is provided by the wrapped `wrapped_fun`, so that the created function seems to be identical (except possiblyfor the signature). Note that all options in `with_signature` can still be overrided using parameters of `@wraps`.

If the signature is *not* modified through `new_sig`, `remove_args`, `append_args` or `prepend_args`, the additional `__wrapped__` attribute  on the created function, to stay consistent with the `functools.wraps` behaviour.

See also [python documentation on @wraps](https://docs.python.org/3/library/functools.html#functools.wraps)

**Parameters**

 - `wrapped_fun`: the function that you intend to wrap with the decorated function. As in `functools.wraps`, `wrapped_fun` is used as the default reference for the exposed signature, `__name__`, `__qualname__`, `__doc__` and `__dict__`.
   
 - `new_sig`: the new signature of the decorated function. By default it is `None` and means "same signature as in `wrapped_fun`" (similar behaviour as in `functools.wraps`) If you wish to modify the exposed signature you can either use `remove/prepend/append_args`, or pass a non-None `new_sig`. It can be either a string without 'def' such as "foo(a, b: int, *args, **kwargs)" of "(a, b: int)", or a `Signature` object, for example from the output of `inspect.signature` or from the `funcsigs.signature` backport. Note that these objects can be created manually too. If the signature is provided as a string and contains a non-empty name, this name will be used instead of the one of `wrapped_fun`.
   
 - `prepend_args`: a string or list of strings to prepend to the signature of `wrapped_fun`. These extra arguments should not be passed to `wrapped_fun`, as it does not know them. This is typically used to easily create a wrapper with additional arguments, without having to manipulate the signature objects.
   
 - `append_args`: a string or list of strings to append to the signature of `wrapped_fun`. These extra arguments should not be passed to `wrapped_fun`, as it does not know them. This is typically used to easily create a wrapper with additional arguments, without having to manipulate the signature objects.
   
 - `remove_args`: a string or list of strings to remove from the signature of `wrapped_fun`. These arguments should be injected in the received `kwargs` before calling `wrapped_fun`, as it requires them. This is typically used to easily create a wrapper with less arguments, without having to manipulate the signature objects.
   
 - `func_name`: provide a non-`None` value to override the created function `__name__` and `__qualname__`. If this is `None` (default), the `__name__` will default to the ones of `wrapped_fun` if `new_sig` is `None` or is a `Signature`, or to the name defined in `new_sig` if `new_sig` is a `str` and contains a non-empty name.
   
 - `inject_as_first_arg`: if `True`, the created function will be injected as the first positional argument of the decorated function. This can be handy in case the implementation is shared between several facades and needs to know from which context it was called. Default=`False`
   
 - `add_source`: a boolean indicating if a '__source__' annotation should be added to the generated function (default: True)
   
 - `add_impl`: a boolean indicating if a '__func_impl__' annotation should be added to the generated function (default: True)
   
 - `doc`: a string representing the docstring that will be used to set the __doc__ attribute on the generated function. If None (default), the doc of `wrapped_fun` will be used. If `wrapped_fun` is an instance of `functools.partial`, a special enhanced doc will be generated.
   
 - `qualname`: a string representing the qualified name to be used. If None (default), the `__qualname__` will default to the one of `wrapped_fun`, or the one in `new_sig` if `new_sig` is provided as a string with a non-empty function name.
   
 - `module_name`: the name of the module to be set on the function (under __module__ ). If None (default), the `__module__` attribute of `wrapped_fun` will be used.
   
 - `attrs`: other keyword attributes that should be set on the function. Note that the full `__dict__` of `wrapped_fun` is automatically copied.


### `create_wrapper`

```python
def create_wrapper(wrapped,
                   wrapper,
                   new_sig: Union[str, Signature] = None,
                   prepend_args: Union[str, Parameter, Iterable[Union[str, Parameter]]] = None,
                   append_args: Union[str, Parameter, Iterable[Union[str, Parameter]]] = None,
                   remove_args: Union[str, Iterable[str]] = None,
                   func_name: str = None,
                   inject_as_first_arg: bool = False,
                   add_source: bool = True,
                   add_impl: bool = True,
                   doc: str = None,
                   qualname: str = None,
                   module_name: str = None,
                   **attrs
                   ):
```

Creates a signature-preserving wrapper function. `create_wrapper(wrapped, wrapper, **kwargs)` is equivalent to `wraps(wrapped, **kwargs)(wrapper)`. See [`@wraps`](#wraps)

### `@partial`

```python
def partial(f: Callable, 
            *preset_pos_args, 
            **preset_kwargs
            ):
```

Equivalent of `functools.partial` but relies on a dynamically-created function. As a result the function
looks nicer to users in terms of apparent documentation, name, etc.

See [documentation](./index.md#removing-parameters-easily) for details.

### `@with_partial`

```python
def with_partial(*preset_pos_args, 
                 **preset_kwargs
                 ):
```

Decorator to 'partialize' a function using [`partial`](#partial).

## Signature editing utils

### `add_signature_parameters`

```python
def add_signature_parameters(s,             # type: Signature
                             first=(),      # type: Union[str, Parameter, Iterable[Union[str, Parameter]]]
                             last=(),       # type: Union[str, Parameter, Iterable[Union[str, Parameter]]]
                             custom=(),     # type: Union[Parameter, Iterable[Parameter]]
                             custom_idx=-1  # type: int
                             ):
```

Adds the provided parameters to the signature `s` (returns a new `Signature` instance).

 - `s`: the original signature to edit
 - `first`: a single element or a list of `Parameter` instances to be added at the beginning of the parameter's list. Strings can also be provided, in which case the parameter kind will be created based on best guess.
 - `last`: a single element or a list of `Parameter` instances to be added at the end of the parameter's list. Strings can also be provided, in which case the parameter kind will be created based on best guess.
 - `custom`: a single element or a list of `Parameter` instances to be added at a custom position in the list. That position is determined with `custom_idx`
 - `custom_idx`: the custom position to insert the `custom` parameters to.

### `remove_signature_parameters`

```python
def remove_signature_parameters(s, 
                                *param_names):
```

Removes the provided parameters from the signature `s` (returns a new `Signature` instance).

## Pseudo-compilation

### `compile_fun`

