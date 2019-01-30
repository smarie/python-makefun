# makefun

*Small library to dynamically create python functions.*

[![Build Status](https://travis-ci.org/smarie/python-makefun.svg?branch=master)](https://travis-ci.org/smarie/python-makefun) [![Tests Status](https://smarie.github.io/python-makefun/junit/junit-badge.svg?dummy=8484744)](https://smarie.github.io/python-makefun/junit/report.html) [![codecov](https://codecov.io/gh/smarie/python-makefun/branch/master/graph/badge.svg)](https://codecov.io/gh/smarie/python-makefun) [![Documentation](https://img.shields.io/badge/docs-latest-blue.svg)](https://smarie.github.io/python-makefun/) [![PyPI](https://img.shields.io/badge/PyPI-makefun-blue.svg)](https://pypi.python.org/pypi/makefun/)

This library was largely inspired by [`decorator`](https://github.com/micheles/decorator). It is currently in "experimental" state and might grow if needed later (objective would be ad least to cover [this case](https://github.com/micheles/decorator/pull/58)).

## Installing

```bash
> pip install makefun
```

## Usage

### Creating functions from string definition

This example shows how you can dynamically create a function `def foo(b: int, a: float = 0)` that will redirect all of its calls to `identity_handler`.

```python
from makefun import create_function

# let's create a dynamic function with this signature
func_signature = "def foo(b: int, a: float = 0)"

# this handler will grab the inputs and return them
def identity_handler(*args, **kwargs):
    """test docstring..."""
    return args, kwargs

# create the dynamic function
dynamic_fun = create_function(func_signature, identity_handler)

# try to call it !
assert dynamic_fun(2) == ((2, 0), {})

# see help
help(dynamic_fun)
```

### Creating functions from `inspect.Signature` objects

TODO it seems like an interesting and relatively easy feature to add, among others.

## Main features / benefits

 * **Dynamically generate functions that redirect to generic handlers**: the generated function signature is specific (`a: int, b=None`), but the handler is generic (`*args, **kwargs`)

## See Also

 - [decorator](https://github.com/micheles/decorator), which largely inspired this code
 - [PEP362 - Function Signature Object](https://www.python.org/dev/peps/pep-0362) 

### Others

*Do you like this library ? You might also like [my other python libraries](https://github.com/smarie/OVERVIEW#python)* 

## Want to contribute ?

Details on the github page: [https://github.com/smarie/python-makefun](https://github.com/smarie/python-makefun)
