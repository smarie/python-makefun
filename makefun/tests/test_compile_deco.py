#  Authors: Sylvain Marie <sylvain.marie@se.com>
#
#  Copyright (c) Schneider Electric Industries, 2020. All right reserved.
from textwrap import dedent

import pytest

from makefun import compile_fun, UnsupportedForCompilation, UndefinedSymbolError


def test_compilefun():
    """tests that @compile_fun works correctly"""

    @compile_fun
    def foo(a, b):
        return a + b

    assert foo(5, -5.0) == 0

    ref = """
    @compile_fun
    def foo(a, b):
        return a + b
        """
    assert foo.__source__ == dedent(ref[1:])


def get_code(target):
    try:
        # python 3
        func_code = target.__code__
    except AttributeError:
        # python 2
        func_code = target.func_code
    return func_code


def is_compiled(target):
    fname = get_code(target).co_filename
    return fname != __file__ and 'makefun-gen' in fname


def test_compilefun_nested():
    """tests that @compile_fun correctly compiles nested functions recursively"""

    def foo(a, b):
        return a + b

    @compile_fun
    def bar(a, b):
        assert is_compiled(foo)
        return foo(a, b)

    assert bar(5, -5.0) == 0


@pytest.mark.parametrize("variant", ['all', 'named'], ids="variant={}".format)
def test_compilefun_nested_exclude(variant):
    """tests that the `except_names` argument of @compile_fun works correctly"""

    def foo(a, b):
        return a + b

    if variant == 'all':
        @compile_fun(recurse=False)
        def bar(a, b):
            assert not is_compiled(foo)
            return foo(a, b)
    else:
        @compile_fun(except_names=('foo', ))
        def bar(a, b):
            assert not is_compiled(foo)
            return foo(a, b)

    assert bar(5, -5.0) == 0


def test_compilefun_nameerror():
    """Tests that the `NameError` is raised at creation time and not at call time"""

    with pytest.raises(UndefinedSymbolError):
        @compile_fun
        def fun_requiring_unknown_name(a, b):
            return unknown_name(a, b)

    def unknown_name(a, b):
        return a + b


def test_compilefun_method():
    """Tests that @compilefun works for class methods"""

    class A:
        @compile_fun
        def meth1(self, par1):
            print("in A.meth1: par1 =", par1)

    a = A()
    a.meth1("via meth1")

    class A:
        def __init__(self):
            self.i = 1

        @compile_fun
        def add(self, a):
            return self.i + a

    a = A()
    assert A().add(-1) == 0


def test_compileclass_decorator():
    """tests that applying decorator on a class raises an error """

    with pytest.raises(UnsupportedForCompilation):
        @compile_fun
        class A(object):
            pass


# def test_compileclass_decorator():
#
#     @compile_fun
#     class A(object):
#         pass
#
#     assert A() is not None
#
#     @compile_fun
#     class A(int, object):
#         pass
#
#     assert A() is not None
#
#     @compile_fun
#     class A(object):
#         def __init__(self):
#             pass
#
#     assert A() is not None
#
#     @compile_fun
#     class A(int):
#         pass
#         # def compute(self):
#         #     return self + 2
#
#     assert A(2) + 2 == 4
