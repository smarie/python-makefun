# makefun

*Dynamically create python functions with a proper signature.*

[![Python versions](https://img.shields.io/pypi/pyversions/makefun.svg)](https://pypi.python.org/pypi/makefun/) [![Build Status](https://travis-ci.org/smarie/python-makefun.svg?branch=master)](https://travis-ci.org/smarie/python-makefun) [![Tests Status](https://smarie.github.io/python-makefun/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-makefun/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-makefun/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-makefun)

[![Documentation](https://img.shields.io/badge/doc-latest-blue.svg)](https://smarie.github.io/python-makefun/) [![PyPI](https://img.shields.io/pypi/v/makefun.svg)](https://pypi.python.org/pypi/makefun/) [![Downloads](https://pepy.tech/badge/makefun)](https://pepy.tech/project/makefun) [![Downloads per week](https://pepy.tech/badge/makefun/week)](https://pepy.tech/project/makefun) [![GitHub stars](https://img.shields.io/github/stars/smarie/python-makefun.svg)](https://github.com/smarie/python-makefun/stargazers)

`makefun` help you create functions dynamically, with the signature of your choice. It was largely inspired by [`decorator`](https://github.com/micheles/decorator), and created mainly to cover [one of its limitations](https://github.com/micheles/decorator/pull/58). Thanks [`micheles`](https://github.com/micheles) for this great piece of work!

The typical use cases are:

 - creating [**signature-preserving function wrappers**](#signature-preserving-function-wrappers) - just like `functools.wraps` but with accurate `TypeError` exception raising when user-provided arguments are wrong, and with a very convenient way to access argument values.

 - creating **function wrappers that have more or less arguments** that the function they wrap. A bit like `functools.partial` but a lot more flexible and friendly for your users. For example, I use it in [my pytest plugins](https://github.com/smarie/OVERVIEW#tests) to add a `requests` parameter to users' tests or fixtures when they do not already have it.

 - more generally, creating **functions with a signature derived from a reference signature**,
 
 - or even creating **functions with a signature completely defined at runtime**.


It currently supports three ways to define the signature of the created function

 - from a given reference function, e.g. `foo`.
 - from strings, e.g. `'foo(a, b=1)'`
 - from `Signature` objects, either manually created, or obtained by using the `inspect.signature` (or its backport `funcsigs.signature`) method.


!!! note "creating signature-preserving decorators"
    Creating decorators and creating signature-preserving function wrappers are two independent problems. `makefun` is solely focused on the second problem. If you wish to solve the first problem you can look at [`decopatch`](https://smarie.github.io/python-decopatch/). It provides a compact syntax, relying on `makefun`, if you wish to tackle both at once.


## Installing

```bash
> pip install makefun
```

## Usage

### 1- Ex-nihilo creation

Let's create a function `foo(b, a=0)` implemented by `func_impl`. The easiest way to provide the signature is as a `str`:

```python
from makefun import create_function

# (1) define the signature. Warning: do not put 'def' keyword here!
func_sig = "foo(b, a=0)"

# (2) define the function implementation
def func_impl(*args, **kwargs):
    """This docstring will be used in the generated function by default"""
    print("func_impl called !")
    return args, kwargs

# (3) create the dynamic function
gen_func = create_function(func_sig, func_impl)
```

We can test it:

```python
>>> args, kwargs = gen_func(2)
func_impl called !
>>> assert args == ()
>>> assert kwargs == {'a': 0, 'b': 2}
```

You can also:

 * remove the name from the signature string (e.g. `'(b, a=0)'`) to directly use the function name of `func_impl`.
 * override the function name, docstring, qualname and module name if you pass a non-None `func_name`, `doc`, `qualname` and `module_name` argument
 * add other attributes on the generated function if you pass additional keyword arguments

See `help(create_function)` for details.


#### Arguments mapping

We can see above that `args` is empty, even if we called `gen_func` with a positional argument. This is completely normal: this is because the created function does not expose `(*args, **kwargs)` but exposes the desired signature `(b, a=0)`. So as for usual python function calls, we lose the information about what was provided as positional and what was provided as keyword. You can try it yourself: write a function `def foo(b, a=0)` and now try to guess from the function body what was provided as positional, and what was provided as keyword...
 
This behaviour is actually a great feature because it makes it much easier to develop the `func_impl`! Indeed, except if your desired signature contains *positional-only* (not yet available as of python 3.7) or *var-positional* (e.g. `*args`) arguments, you will **always** find all named arguments in `**kwargs`.
 

#### More compact syntax

You can use the `@with_signature` decorator to perform exactly the same things than `create_function`, but in a more compact way:

```python
from makefun import with_signature

@with_signature("foo(b, a=0)")
def gen_func(*args, **kwargs):
    """This docstring will be used in the generated function by default"""
    print("func_impl called !")
    return args, kwargs
```

It also has the capability to take `None` as a signature, if you just want to update the metadata (`func_name`, `doc`, `qualname`, `module_name`) without creating any function:

```python
@with_signature(None, func_name='f')
def foo(a):
    return a

assert foo.__name__ == 'f'
```

See `help(with_signature)` for details.

#### PEP484 type hints in `str`

PEP484 type hints are supported in string function definitions:

```python
func_sig = "foo(b: int, a: float = 0) -> str"
```

PEP484 type comments are also supported:

```python
func_signature = """
foo(b,      # type: int
    a = 0,  # type: float
    ):
    # type: (...) -> str
"""
```

but unfortunately `inspect.signature` is not able to detect them so the generated function does not contain the annotations. See [this example](https://github.com/smarie/python-makefun/issues/7#issuecomment-459353197). 


#### Using `Signature` objects

`create_function` and `@with_signature` are able to accept a `Signature` object as input, instead of a `str`. That might be more convenient than using strings to programmatically define signatures. For example we can rewrite the above script using `Signature`:

```python
from makefun import with_signature
from inspect import Signature, Parameter

# (1) define the signature using objects.
parameters = [Parameter('b', kind=Parameter.POSITIONAL_OR_KEYWORD),
              Parameter('a', kind=Parameter.POSITIONAL_OR_KEYWORD, default=0), ]
func_sig = Signature(parameters)
func_name = 'foo'

# (2) define the function
@with_signature(func_sig, func_name=func_name)
def gen_func(*args, **kwargs):
    """This docstring will be used in the generated function by default"""
    print("func_impl called !")
    return args, kwargs
```

Note that `Signature` objects do not contain any function name information. You therefore have to provide an explicit `func_name` argument to `@with_signature` (or to `create_function`) as shown above.

!!! note "`Signature` availability in python 2"
    In python 2 the `inspect` package does not provide any signature-related features, but a complete backport is available: [`funcsigs`](https://github.com/testing-cabal/funcsigs).


### 2- Deriving from existing signatures

In many real-world applications we want to reuse "as is", or slightly modify, an existing signature.

#### Copying a signature

If you just want to expose the same signature as a reference function (and not wrap it nor appear like it), the easiest way to copy the signature from another function `f` is to use `signature(f)` from `inspect`/`funcsigs`.

#### Signature-preserving function wrappers

[`@functools.wraps`](https://docs.python.org/3/library/functools.html#functools.wraps) is a famous decorator to create "signature-preserving" function wrappers. However it does not actually preserve the signature, it just uses a trick (setting the `__wrapped__` attribute) to trigger special dedicated behaviour in `stdlib`'s `help()` and `signature()` methods. See [here](https://stackoverflow.com/questions/308999/what-does-functools-wraps-do/55102697#55102697).
 
This has two major limitations: 

 1. the wrapper code will execute *even when the provided arguments are invalid*. 
 2. the wrapper code can not easily access an argument using its name, from the received `*args, **kwargs`. Indeed one would have to handle all cases (positional, keyword, default) and therefore to use something like `Signature.bind()`.

`makefun` provides a convenient replacement for `@wraps` that fixes these two issues:
 
```python
from makefun import wraps

# a dummy function
def foo(a, b=1):
    """ foo doc """
    return a + b

# our signature-preserving wrapper
@wraps(foo)
def enhanced_foo(*args, **kwargs):
    print('hello!')
    print('b=%s' % kwargs['b'])  # we can reliably access 'b'
    return foo(*args, **kwargs)
``` 

We can check that the wrapper behaves correctly whatever the call modes:

```python
>>> assert enhanced_foo(1, 2) == 3  # positional 'b'
hello!
b=2
>>> assert enhanced_foo(b=0, a=1) == 1  # keyword 'b'
hello!
b=0
>>> assert enhanced_foo(1) == 2  # default 'b'
hello!
b=1
```

And let's pass wrong arguments to it: we see that the wrapper is **not** executed.

```python
>>> enhanced_foo()
TypeError: foo() missing 1 required positional argument: 'a'
```

You can try to do the same experiment with `functools.wraps` to see the difference.

Finally note that a `create_wrapper` function is also provided for convenience ; it is the equivalent of `@wraps` but as a standard function - not a decorator.

!!! note "creating signature-preserving decorators"
    Creating decorators and creating signature-preserving function wrappers are two independent problems. `makefun` is solely focused on the second problem. If you wish to solve the first problem you can look at [`decopatch`](https://smarie.github.io/python-decopatch/). It provides a compact syntax, relying on `makefun`, if you wish to tackle both at once.


#### Editing a signature

Below we show how to add a parameter to a function. We first capture its `Signature` using `inspect.signature(f)`, we modify it to add a parameter, and finally we use it in `wraps` to create our final function:

```python
from makefun import wraps
from inspect import signature, Parameter

# (0) the reference function
def foo(b, a=0):
    print("foo called: b=%s, a=%s" % (b, a))
    return b, a

# (1a) capture the signature of reference function `foo`
foo_sig = signature(foo)
print("Original Signature: %s" % foo_sig)

# (1b) modify the signature to add a new parameter 'z' as first argument
params = list(foo_sig.parameters.values())
params.insert(0, Parameter('z', kind=Parameter.POSITIONAL_OR_KEYWORD))
new_sig = foo_sig.replace(parameters=params)
print("New Signature: %s" % new_sig)

# (2) define the wrapper implementation
@wraps(foo, new_sig=new_sig)
def foo_wrapper(z, *args, **kwargs):
    print("foo_wrapper called ! z=%s" % z)
    # call the foo function 
    output = foo(*args, **kwargs)
    # return augmented output
    return z, output
        
# call it
assert foo_wrapper(3, 2) == 3, (2, 0)
```

yields

```
Original Signature: (b, a=0)
New Signature: (z, b, a=0)

foo_wrapper called ! z=3
foo called: b=2, a=0
```

This way you can therefore easily create function wrappers with different signatures: not only adding, but also removing parameters, changing their kind (forcing keyword-only for example), etc. The possibilities are as endless as the capabilities of the `Signature` objects.

Two helper functions are provided in this toolbox to make it a bit easier for you to edit `Signature` objects:
 
 - `remove_signature_parameters` creates a new signature from an existing one by removing all parameters corresponding to the names provided
 - `add_signature_parameters` prepends the `Parameter`s provided in its `first=` argument, and appends the ones provided in its `last` argument.

```python
from makefun import add_signature_parameters, remove_signature_parameters

def foo(b, c, a=0):
    pass

# original signature
foo_sig = signature(foo)
print("original signature: %s" % foo_sig)

# let's modify it
new_sig = add_signature_parameters(foo_sig,
                first=Parameter('z', kind=Parameter.POSITIONAL_OR_KEYWORD),
                last=Parameter('o', kind=Parameter.POSITIONAL_OR_KEYWORD, 
                               default=True)
          )
new_sig = remove_signature_parameters(new_sig, 'b', 'a')
print("modified signature: %s" % new_sig)
```

yields

```bash
original signature: (b, c, a=0)
modified signature: (z, c, o=True)
```

They might save you a few lines of code if your use-case is not too specific.


#### Removing parameters easily

As goodies, `makefun` provides a `partial` function that are equivalent to [`functools.partial`](https://docs.python.org/2/library/functools.html#functools.partial), except that it is fully signature-preserving and modifies the documentation with a nice helper message explaining that this is a partial view:

```python
def foo(x, y):
    """
    a `foo` function

    :param x:
    :param y:
    :return:
    """
    return x + y
   
from makefun import partial
bar = partial(foo, x=12)
``` 

we can test it:

```python
>>> assert bar(1) == 13
>>> help(bar)
Help on function bar in module makefun.tests.test_partial_and_macros:

bar(y)
    <This function is equivalent to 'foo(y, x=12)', see original 'foo' doc below.>
    
    a `foo` function
    
    :param x:
    :param y:
    :return:
```

A decorator is also available to create partial views easily for quick tests:

```python
@with_partial(x=12)
def foo(x, y):
    """
    a `foo` function

    :param x:
    :param y:
    :return:
    """
    return x + y
```


### 3- Advanced topics

#### Generators and Coroutines

`create_function` and `@with_signature` will automatically create a generator if your implementation is a generator:

```python
# define the implementation
def my_generator_impl(b, a=0):
    for i in range(a, b):
        yield i * i

# create the dynamic function
gen_func = create_function("foo(a, b)", my_generator_impl)

# verify that the new function is a generator and behaves as such
assert isgeneratorfunction(gen_func)
assert list(gen_func(1, 4)) == [1, 4, 9]
```

The same goes for generator-based coroutines:

```python
# define the impl that should be called
def my_gencoroutine_impl(first_msg):
    second_msg = (yield first_msg)
    yield second_msg

# create the dynamic function
gen_func = create_function("foo(first_msg='hello')", my_gencoroutine_impl)

# verify that the new func is a generator-based coroutine and behaves correctly
cor = gen_func('hi')
assert next(cor) == 'hi'
assert cor.send('chaps') == 'chaps'
cor.send('ola')  # raises StopIteration
```

and asyncio coroutines as well

```python
# define the impl that should be called
async def my_native_coroutine_impl(sleep_time):
    await sleep(sleep_time)
    return sleep_time

# create the dynamic function
gen_func = create_function("foo(sleep_time=2)", my_native_coroutine_impl)

# verify that the new function is a native coroutine and behaves correctly
from asyncio import get_event_loop
out = get_event_loop().run_until_complete(gen_func(5))
assert out == 5
```

#### Generated source code

The generated source code is in the `__source__` field of the generated function:

```python
print(gen_func.__source__)
```

prints the following source code:

```python
def foo(b, a=0):
    return _func_impl_(b=b, a=a)

```

The `_func_impl_` symbol represents your implementation. As [already mentioned](#arguments_mapping), you see that the variables are passed to it *as keyword arguments* when possible (`_func_impl_(b=b)`, not simply `_func_impl_(b)`). Of course if it is not possible it adapts:

```python
gen_func = create_function("foo(a=0, *args, **kwargs)", func_impl)
print(gen_func.__source__)
```

prints the following source code:

```python
def foo(a=0, *args, **kwargs):
    return _func_impl_(a=a, *args, **kwargs)
```

#### Function reference injection

In some scenarios you may wish to share the same implementation among several created functions, for example to expose slightly different signatures on top of the same core.

In that case you may wish your implementation to know from which dynamically generated function it is being called. For this, simply use `inject_as_first_arg=True`, and the called function will be injected as the first argument:

```python
def core_impl(f, *args, **kwargs):
    print("This is generic core called by %s" % f.__name__)
    # here you could use f.__name__ in a if statement to determine what to do
    if f.__name__ == "func1":
        print("called from func1 !")
    return args, kwargs

# generate 2 functions
func1 = create_function("func1(a, b)", core_impl, inject_as_first_arg=True)
func2 = create_function("func2(a, d)", core_impl, inject_as_first_arg=True)

func1(1, 2)
func2(1, 2)
```

yields

```
This is generic core called by func1
called from func1 !
This is generic core called by func2
```

### 4. Other goodies

#### `@compile_fun`

A draft decorator to `compile` any existing function so that users cant debug through it. It can be handy to mask some code from your users for convenience (note that this does not provide any obfuscation, people can still reverse engineer your code easily. Actually the source code even gets copied in the function's `__source__` attribute for convenience):

```python
from makefun import compile_fun

@compile_fun
def foo(a, b):
    return a + b

assert foo(5, -5.0) == 0
print(foo.__source__)
```

yields

```
@compile_fun
def foo(a, b):
    return a + b
```

If the function closure includes functions, they are recursively replaced with compiled versions too (only for this closure, this does not modify them otherwise). You may disable this behaviour entirely with `recurse=False`, or exclude some symbols from this recursion with the `except_names=(...)` arg (a tuple of names to exclude).

**IMPORTANT** this decorator is a "goodie" in early stage and has not been extensively tested. Feel free to contribute !

Note that according to [this post](https://stackoverflow.com/a/471227/7262247) compiling does not make the code run any faster.

Known issues: `NameError` may appear if your function code depends on symbols that have not yet been defined. Make sure all symbols exist first ! See [this issue](https://github.com/smarie/python-makefun/issues/47).

## Main features / benefits

 * **Generate functions with a dynamically defined signature**: the signature can be provided as a string or as a `Signature` object, thus making it handy to derive from other functions.
 * **Implement them easily**: the generated functions redirect their calls to the provided implementation function. As long as the signature is compliant, it will work as expected. For example the signature can be specific (`a: int, b=None`), and the implementation more generic (`*args, **kwargs`). Arguments will always be passed as keywords arguments when possible.
 * Replace **`@functools.wraps** so that it correctly preserves signatures, and enable you to easily access named arguments.

## See Also

 - [decorator](https://github.com/micheles/decorator), which largely inspired this code
 - [PEP362 - Function Signature Object](https://www.python.org/dev/peps/pep-0362) 
 - [A blog entry on dynamic function creation](http://block.arch.ethz.ch/blog/2016/11/creating-functions-dynamically/)
 - [functools.wraps](https://docs.python.org/3/library/functools.html#functools.wraps)

### Others

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-makefun](https://github.com/smarie/python-makefun)
