import sys

import pytest

from makefun import wraps, with_signature, partial


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


def test_issue_55():
    """Tests that no syntax error appears when no arguments are provided in the signature (name change scenario)"""

    # full name change including stack trace

    @with_signature('bar()')
    def foo():
        return 'a'

    assert "bar at" in repr(foo)
    assert foo.__name__ == 'bar'
    assert foo() == 'a'

    # only metadata change

    @with_signature(None, func_name='bar')
    def foo():
        return 'a'

    if sys.version_info >= (3, 0):
        assert "foo at" in repr(foo)
    assert foo.__name__ == 'bar'
    assert foo() == 'a'


def test_partial_noargs():
    """ Fixes https://github.com/smarie/python-makefun/issues/59 """
    def foo():
        pass

    foo._mark = True

    g = partial(foo)
    assert g._mark is True


def test_wraps_dict():
    """Checks that @wraps correctly propagates the __dict__"""

    def foo():
        pass

    foo._mark = True

    @wraps(foo)
    def g():
        pass

    assert g._mark is True


def test_issue_62():
    """https://github.com/smarie/python-makefun/issues/62"""

    def f(a, b):
        return a+b

    fp = partial(f, 0)
    assert fp(-1) == -1
