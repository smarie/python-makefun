import logging
import sys

import pytest

from makefun.main import get_signature_from_string, with_signature

from makefun import wraps

try:  # python 3.3+
    from inspect import signature, Signature, Parameter
except ImportError:
    from funcsigs import signature, Signature, Parameter


def test_non_representable_defaults():
    """ Tests that non-representable default values are handled correctly """

    def foo(logger=logging.getLogger('default')):
        pass

    @wraps(foo)
    def bar(*args, **kwargs):
        pass

    bar()


def test_preserve_attributes():
    """ Tests that attributes are preserved """

    def foo():
        pass

    setattr(foo, 'a', True)

    @wraps(foo)
    def bar(*args, **kwargs):
        pass

    assert bar.a


def test_empty_name_in_string():
    """ Tests that string signatures can now be provided without function name"""
    if sys.version_info < (3, 0):
        str_sig = '(a)'
    else:
        str_sig = '(a:int)'
    func_name, func_sig, func_sig_str = get_signature_from_string(str_sig, locals())
    assert func_name is None
    # to handle type hints in signatures in python 3.5 we have to always remove the spaces
    assert str(func_sig).replace(' ', '') == str_sig
    assert func_sig_str == str_sig + ':'


def test_same_than_wraps_basic():
    """Tests that the metadata set by @wraps is correct"""

    from makefun.tests.test_doc import test_from_sig_wrapper
    from functools import wraps as functools_wraps

    def foo_wrapper(*args, **kwargs):
        """ hoho """
        pass

    functool_wrapped = functools_wraps(test_from_sig_wrapper)(foo_wrapper)

    # WARNING: functools.wraps irremediably contaminates foo_wrapper, we have to redefine it
    def foo_wrapper(*args, **kwargs):
        """ hoho """
        pass

    makefun_wrapped = wraps(test_from_sig_wrapper)(foo_wrapper)
    # compare with the default behaviour of with_signature, that is to copy metadata from the decorated
    makefun_with_signature_inverted = with_signature(signature(test_from_sig_wrapper))(test_from_sig_wrapper)
    makefun_with_signature_normal = with_signature(signature(test_from_sig_wrapper))(foo_wrapper)

    for field in ('__module__', '__name__', '__qualname__', '__doc__', '__annotations__'):
        if sys.version_info < (3, 0) and field in {'__qualname__', '__annotations__'}:
            pass
        else:
            assert getattr(functool_wrapped, field) == getattr(makefun_wrapped, field), "field %s is different" % field
            assert getattr(functool_wrapped, field) == getattr(makefun_with_signature_inverted, field), "field %s is different" % field
            if field != '__annotations__':
                assert getattr(functool_wrapped, field) != getattr(makefun_with_signature_normal, field), "field %s is identical" % field


def tests_wraps_sigchange():
    """ Tests that wraps can be used to change the signature """

    def foo(a):
        """ hoho """
        return a

    @wraps(foo, new_sig="(a, b=0)")
    def goo(*args, **kwargs):
        kwargs.pop('b')
        return foo(*args, **kwargs)

    for field in ('__module__', '__name__', '__qualname__', '__doc__', '__annotations__'):
        if sys.version_info < (3, 0) and field in {'__qualname__', '__annotations__'}:
            pass
        else:
            assert getattr(goo, field) == getattr(foo, field), "field %s is different" % field

    assert str(signature(goo)) == "(a, b=0)"
    assert goo('hello') == 'hello'


@pytest.mark.skipif(sys.version_info < (3, 0), reason="requires python3 or higher")
def test_qualname_when_nested():
    """ Tests that qualname is correctly set when `@with_signature` is applied on nested functions """

    class C:
        def f(self):
            pass
        class D:
            @with_signature("(self, a)")
            def g(self):
                pass

    assert C.__qualname__ == 'test_qualname_when_nested.<locals>.C'
    assert C.f.__qualname__ == 'test_qualname_when_nested.<locals>.C.f'
    assert C.D.__qualname__ == 'test_qualname_when_nested.<locals>.C.D'

    # our mod
    assert C.D.g.__qualname__ == 'test_qualname_when_nested.<locals>.C.D.g'
    assert str(signature(C.D.g)) == "(self, a)"


@pytest.mark.skipif(sys.version_info < (3, 5), reason="requires python 3.5 or higher (non-comment type hints)")
def test_type_hint_error():
    """ Test for https://github.com/smarie/python-makefun/issues/32 """

    from makefun.tests._test_py35 import make_ref_function
    ref_f = make_ref_function()

    @wraps(ref_f)
    def foo(a):
        return a

    assert foo(10) == 10


@pytest.mark.skipif(sys.version_info < (3, 5), reason="requires python 3.5 or higher (non-comment type hints)")
def test_type_hint_error2():
    """ Test for https://github.com/smarie/python-makefun/issues/32 """

    from makefun.tests._test_py35 import make_ref_function2
    ref_f = make_ref_function2()

    @wraps(ref_f)
    def foo(a):
        return a

    assert foo(10) == 10
