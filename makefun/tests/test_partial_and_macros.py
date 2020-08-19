import functools
import sys

import makefun
try:
    from inspect import signature
except ImportError:
    from funcsigs import signature


def test_doc():
    def foo(x, y):
        """
        a `foo` function

        :param x:
        :param y:
        :return:
        """
        return x + y

    ref_bar = functools.partial(foo, x=12)
    bar = makefun.partial(foo, x=12)

    # not possible: the signature from functools is clunky
    # assert str(signature(ref_bar)) == str(signature(bar))
    PY3 = not sys.version_info < (3, )
    assert str(signature(ref_bar)) == "(x=12, y)" if not PY3 else "(*, x=12, y)"
    # todo we could also add keyword-only..
    assert str(signature(bar)) == "(y, x=12)"

    bar.__name__ = 'bar'
    help(bar)
    assert bar(1) == 13
    assert bar.__doc__ == """<This function is equivalent to 'foo(y, x=12)', see original 'foo' doc below.>

        a `foo` function

        :param x:
        :param y:
        :return:
        """


def test_partial():
    """Tests that `with_partial` works"""

    @makefun.with_partial(y='hello')
    def foo(x, y, a):
        """
        a `foo` function

        :param x:
        :param y:
        :param a:
        :return:
        """
        print(a)
        print(x, y)

    foo(1, 2)
    help(foo)

    assert foo.__doc__ == """<This function is equivalent to 'foo(x, a, y='hello')', see original 'foo' doc below.>

        a `foo` function

        :param x:
        :param y:
        :param a:
        :return:
        """


def test_issue_57():
    def f(b=0):
        """hey"""
        return b

    f.i = 1

    # creating the decorator
    dec = makefun.wraps(functools.partial(f, b=2), func_name='foo')

    # applying the decorator
    n = dec(functools.partial(f, b=1))

    # check metadata
    assert n.i == 1
    # check signature
    assert n.__doc__ == """<This function is equivalent to 'f(b=2)', see original 'f' doc below.>
hey"""
    # check implementation: the default value from the signature (from @wraps) is the one that applies here
    assert n() == 2


def test_create_with_partial():
    def f(b=0):
        """hey"""
        return b

    f.i = 1

    m = makefun.create_function("(b=-1)", functools.partial(f, b=2), **f.__dict__)
    assert str(signature(m)) == "(b=-1)"
    assert m() == -1
    assert m.i == 1
    # the doc remains untouched in create_function as opposed to wraps, this is normal
    assert m.__doc__ == """partial(func, *args, **keywords) - new function with partial application
    of the given arguments and keywords.
"""
