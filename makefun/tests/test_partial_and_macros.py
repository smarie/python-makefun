import functools
import pytest
import sys

import makefun
try:
    from inspect import signature
except ImportError:
    from funcsigs import signature


PY2 = sys.version_info < (3, )


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

    ref_sig_str = "(x=12, y)" if PY2 else "(*, x=12, y)"
    assert str(signature(ref_bar)) == ref_sig_str

    bar = makefun.partial(foo, x=12)

    # same behaviour - except in python 2 where our "KW_ONLY_ARG!" appear
    assert str(signature(bar)).replace("=KW_ONLY_ARG!", "") == str(signature(ref_bar))

    bar.__name__ = 'bar'
    help(bar)
    with pytest.raises(TypeError):
        bar(1)
    assert bar(y=1) == 13

    sig_actual_call = ref_sig_str.replace("*, ", "")

    assert bar.__doc__ \
           == """<This function is equivalent to 'foo%s', see original 'foo' doc below.>

        a `foo` function

        :param x:
        :param y:
        :return:
        """ % sig_actual_call


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

    if not PY2:
        # true keyword-only
        with pytest.raises(TypeError):
            foo(1, 2)

    foo(1, a=2)
    help(foo)

    sig_actual_call = "(x, y='hello', a)"  # if PY2 else "(x, *, y='hello', a)"

    assert foo.__doc__.replace("=KW_ONLY_ARG!", "") \
           == """<This function is equivalent to 'foo%s', see original 'foo' doc below.>

        a `foo` function

        :param x:
        :param y:
        :param a:
        :return:
        """ % sig_actual_call


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
    sig_actual_call = "(b=2)"
    # sig = sig_actual_call if PY2 else "(*, b=2)"

    assert n.__doc__ == """<This function is equivalent to 'f%s', see original 'f' doc below.>
hey""" % sig_actual_call
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


def test_args_order_and_kind():
    """Make sure that the order remains ok"""

    def f(a, b, c, **d):
        return a + b + c + sum(d)

    # reference: functools.partial
    fp_ref = functools.partial(f, b=0)

    # except in python 2, all kwargs following the predefined arg become kw-only
    if sys.version_info < (3,):
        assert str(signature(fp_ref)) == "(a, b=0, c, **d)"
    else:
        assert str(signature(fp_ref)) == "(a, *, b=0, c, **d)"

    # our makefun.partial
    fp = makefun.partial(f, b=0)

    # same behaviour - except in python 2 where our "KW_ONLY_ARG!" appear
    assert str(signature(fp_ref)) == str(signature(fp)).replace("=KW_ONLY_ARG!", "")

    # positional-only behaviour
    if sys.version_info >= (3, 8):
        from ._test_py38 import make_pos_only_f
        f = make_pos_only_f()

        # it is possible to keyword-partialize a positional-only argument...
        fp_ref = functools.partial(f, b=0)

        # but 'signature' does not support it !
        with pytest.raises(ValueError):
            signature(fp_ref)

        # assert str(signature(fp_ref)) == "(c, /, *, d, **e)"

        # so we do not support it
        with pytest.raises(NotImplementedError):
            makefun.partial(f, b=0)

        # assert str(signature(fp_ref)) == str(signature(fp))
