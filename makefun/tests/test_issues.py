import sys

import pytest

from makefun import wraps, with_signature


@pytest.mark.skip("known to fail")
def test_wraps_varpositional():
    """ test for https://github.com/smarie/python-makefun/issues/34 """
    def f(a, *args):
        pass

    @wraps(f)
    def foo(*args, **kwargs):
        return f(*args, **kwargs)

    foo('hello', 12)


def test_invalid_signature_str():
    """Test for https://github.com/smarie/python-makefun/issues/36"""

    sig = "(a):"

    @with_signature(sig)
    def foo(a):
        pass


@pytest.mark.skipif(sys.version_info < (3, 0), reason="type hints are not allowed with this syntax in python 2")
def test_invalid_signature_str_py3():
    """Test for https://github.com/smarie/python-makefun/issues/36"""
    sig = "(a) -> int:"

    @with_signature(sig)
    def foo(a):
        pass
