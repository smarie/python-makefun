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


def test_varpositional2():
    """ test for https://github.com/smarie/python-makefun/issues/38 """

    @with_signature("(a, *args)")
    def foo(a, *args):
        assert a == 'hello'
        assert args == (12, )

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


def test_return_annotation_in_py2():
    """Test for https://github.com/smarie/python-makefun/issues/39"""
    def f():
        pass

    f.__annotations__ = {'return': None}

    @wraps(f)
    def b():
        pass

    b()


def test_init_replaced():

    class Foo(object):
        @with_signature("(self, a)")
        def __init__(self, *args, **kwargs):
            pass

    f = Foo(1)

    class Bar(Foo):
        def __init__(self, *args, **kwargs):
            super(Bar, self).__init__(*args, **kwargs)

    b = Bar(2)
