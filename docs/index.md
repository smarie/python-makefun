# makefun

*Small library to dynamically create python functions.*

[![Build Status](https://travis-ci.org/smarie/python-makefun.svg?branch=master)](https://travis-ci.org/smarie/python-makefun) [![Tests Status](https://smarie.github.io/python-makefun/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-makefun/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-makefun/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-makefun) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://smarie.github.io/python-makefun/) [![PyPI](https://img.shields.io/badge/PyPI-makefun-blue.svg)](https://pypi.python.org/pypi/makefun/)

This library was largely inspired by [`decorator`](https://github.com/micheles/decorator), and created mainly to cover [this case](https://github.com/micheles/decorator/pull/58) where the need was to create a function wrapper with a different (but close) signature than the wrapped function.

`makefun` help you create functions dynamically, with accurate and complete signature. The typical use cases are

 - you want to create a function `g` with a signature that is derived from the signature of a function `f` provided at runtime (for example the signature of a user-entered function). For example `g` has the same signature than `f`, or has one additional parameter, etc.
 
 - you want to wrap a function `f` provided at runtime, into some code of your own, and you want to expose the wrapper with the same signature (e.g. to create a function proxy) or with a derived signature (one more argument, etc.)

It currently supports two ways to define the signature of the created function

 - from strings, e.g. `'foo(a, b=1)'`
 - from `Signature` objects, either manually created, or obtained from use of the `inspect.signature` (or its backport `funcsigs.signature`) method.


## Installing

```bash
> pip install makefun
```

## Usage

### 1- Creating functions from string signatures

This example shows how you can dynamically create a function `foo(b, a=0)` that will redirect all of its calls to `my_handler`.

```python
from makefun import create_function

# define the signature. Note: no 'def' keyword here!
func_signature = "foo(b, a=0)"

# define the handler that should be called
def my_handler(*args, **kwargs):
    """This docstring will be used in the generated function by default"""
    print("my_handler called !")
    return args, kwargs

# create the dynamic function
dynamic_fun = create_function(func_signature, my_handler)

# call it and check outputs
args, kwargs = dynamic_fun(2)
assert args == ()
assert kwargs == {'a': 0, 'b': 2}
```

#### PEP484 type hints support

PEP484 type hints are supported in string function definitions:

```python
func_signature = "foo(b: int, a: float = 0) -> str"
dynamic_fun = create_function(func_signature, my_handler)
```

PEP484 type comments are also supported:

```python
func_signature = """
foo(b,      # type: int
    a = 0,  # type: float
    ):
    # type: (...) -> str
"""
dynamic_fun = create_function(func_signature, my_handler)
```

but unfortunately `inspect.signature` is not able to detect them so the generated function does not contain the annotations. See [this example](https://github.com/smarie/python-makefun/issues/7#issuecomment-459353197). 

### 2- Creating functions from `Signature` objects

Another quite frequent case is that you wish to create a function that has the same signature that another one, or with a signature that derives from another one (for example, you wish to add a parameter).

To support these use cases, as well as all use cases where you wish to create functions ex-nihilo with any kind of signature, `create_function` is also able to accept a `Signature` object as input.
 
For example, you can extract the signature from your function using `inspect.signature`, modify it if needed (below we add a parameter), and then pass it to `create_function`:

```python
try:  # python 3.3+
    from inspect import signature, Signature, Parameter
except ImportError:
    from funcsigs import signature, Signature, Parameter

def foo(b, a=0):
    print("foo called: b=%s, a=%s" % (b, a))
    return b, a

# capture the name and signature of existing function `foo`
func_name = foo.__name__
original_func_sig = signature(foo)
print("Original Signature: %s" % original_func_sig)

# modify the signature to add a new parameter
params = list(original_func_sig.parameters.values())
params.insert(0, Parameter('z', kind=Parameter.POSITIONAL_OR_KEYWORD))
func_sig = original_func_sig.replace(parameters=params)
print("New Signature: %s" % func_sig)

# define the handler that should be called
def my_handler(z, *args, **kwargs):
    print("my_handler called ! z=%s" % z)
    # call the foo function 
    output = foo(*args, **kwargs)
    # return augmented output
    return z, output
        
# create a dynamic function with the same signature and name
dynamic_fun = create_function(func_sig, my_handler, func_name=func_name)

# call it
dynamic_fun(3, 2)
```

yields

```
Original Signature: (b, a=0)
New Signature: (z, b, a=0)

my_handler called ! z=3
foo called: b=2, a=0
```

This way you can therefore easily create function wrappers with different signatures: not only adding, but also removing parameters, changing their kind (forcing keyword-only for example), etc. The possibilities are as numerous as the capabilities of the `Signature` objects.


### 3- Advanced topics

#### Variable-length, Positional-only and Keyword-only

By default, all arguments (including the ones which fell back to default values) will be passed to the handler. You can see it by printing the `__source__` field of the generated function:

```python
print(dynamic_fun.__source__)
```

prints the following source code:

```python
def foo(b, a=0):
    return _call_handler_(b=b, a=a)

```

The `__call_handler_` symbol represents your handler. You see that the variables are passed to it *as keyword arguments* when possible (`_call_handler_(b=b)`, not simply `_call_handler_(b)`). However in some cases, the function that you want create has variable-length arguments. In this case the generated function will adapt the way it passes the arguments to your handler, as expected:

```python
func_signature = "foo(a=0, *args, **kwargs)"
dynamic_fun = create_function(func_signature, my_handler)
print(dynamic_fun.__source__)
```

prints the following source code:

```python
def foo(a=0, *args, **kwargs):
    return _call_handler_(a=a, *args, **kwargs)

```

This time you see that `*args` and `kwargs` are passed with their stars.

Positional-only arguments do not exist as of today in python. They can be declared on a `Signature` object, but then the string version of the signature presents a syntax error for the python compiler:

```python
try:  # python 3.3+
    from inspect import Signature, Parameter
except ImportError:
    from funcsigs import Signature, Parameter

params = [Parameter('a', kind=Parameter.POSITIONAL_ONLY),
          Parameter('b', kind=Parameter.POSITIONAL_OR_KEYWORD)]
print(str(Signature(parameters=params)))              
```

yields `(<a>, b)` in python 2 (`funcsigs`) and `(a, /, b)` in python 3 with `inspect`.

If a future python version supports positional-only ([PEP457](https://www.python.org/dev/peps/pep-0457/) and [PEP570](https://www.python.org/dev/peps/pep-0570/)), this library will adapt - no change of code will be required, as long as the string representation of `Signature` objects adopts the correct syntax.


#### Function reference injection

In some scenarios you may share the same handler among several created functions, for example to expose slightly different signatures on top of the same core function.

In that case you may wish your handler to know from which dynamically generated function it is called. For this simply use `inject_as_first_arg=True`, and the called function will be passed as the first argument to your handler:

```python
def generic_handler(f, *args, **kwargs):
    print("This is generic handler called by %s" % f.__name__)
    # here you could use f.__name__ in a if statement to determine what to do
    if f.__name__ == "func1":
        print("called from func1 !")
    return args, kwargs

# generate 2 functions
func1 = create_function("func1(a, b)", generic_handler, inject_as_first_arg=True)
func2 = create_function("func2(a, d)", generic_handler, inject_as_first_arg=True)

func1(1, 2)
func2(1, 2)
```

yields

```
This is generic handler called by func1
called from func1 !
This is generic handler called by func2
```

#### Additional customization

`create_function` can optionally:

 * override the docstring if you pass a non-None `doc` argument
 * add other attributes on the generated function if you pass additional keyword arguments

See `help(create_function)` for details.


## Main features / benefits

 * **Generate functions with a dynamically defined signature**: the signature can be provided as a string or as a `Signature` object, thus making it handy to derive from other functions.
 * **Intercept calls with your handler**: the generated functions redirect their calls to the provided handler function. As long as the signature is compliant, it will work as expected. For example the signature can be specific (`a: int, b=None`), and the handler more generic (`*args, **kwargs`)

## See Also

 - [decorator](https://github.com/micheles/decorator), which largely inspired this code
 - [PEP362 - Function Signature Object](https://www.python.org/dev/peps/pep-0362) 
 - [A blog entry on dynamic function creation](http://block.arch.ethz.ch/blog/2016/11/creating-functions-dynamically/)

### Others

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-makefun](https://github.com/smarie/python-makefun)
