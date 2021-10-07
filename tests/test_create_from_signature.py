import sys

import pytest

from makefun import create_function

try:  # python 3.3+
    from inspect import signature, Signature, Parameter
except ImportError:
    from funcsigs import signature, Signature, Parameter


def my_handler(*args, **kwargs):
    """This docstring will be used in the generated function by default"""
    print("my_handler called !")
    return args, kwargs


def test_positional_only():
    """Tests that as of today one cannot create positional-only functions"""

    params = [Parameter('a', kind=Parameter.POSITIONAL_ONLY),
              Parameter('args', kind=Parameter.VAR_POSITIONAL),
              Parameter('kwargs', kind=Parameter.VAR_KEYWORD)]

    func_signature = Signature(parameters=params)

    if sys.version_info < (3, 8):
        with pytest.raises(SyntaxError):
            create_function(func_signature, my_handler, func_name="foo")
    else:
        dynamic_fun =create_function(func_signature, my_handler, func_name="foo")
        assert "\n" + dynamic_fun.__source__ == """
def foo(a, /, *args, **kwargs):
    return _func_impl_(a, *args, **kwargs)
"""
        assert dynamic_fun(0, 1) == ((0, 1), {})
