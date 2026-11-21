import functools
import inspect
import sys

import pytest

from makefun.main import is_identifier

try:  # python 3.3+
    from inspect import signature, Signature, Parameter
except ImportError:
    from funcsigs import signature, Signature, Parameter

from makefun import wraps, with_signature, partial, create_function


def test_wraps_varpositional_issue_34():
    """ test for https://github.com/smarie/python-makefun/issues/34 """
    def f(a, *args):
        return a, args

    @wraps(f)
    def foo(*args, **kwargs):
        return f(*args, **kwargs)

    assert foo('hello', 12) == ("hello", (12,))


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

    foo._mark = []
    foo._label = 'original'

    @wraps(foo, _label='wrapper')
    def g():
        pass

    assert g._mark is foo._mark
    assert g._label == 'wrapper'
    assert foo._label == 'original'
    assert g.__wrapped__ is foo
    assert not hasattr(foo, '__wrapped__')


def test_issue_62():
    """https://github.com/smarie/python-makefun/issues/62"""

    def f(a, b):
        return a+b

    fp = partial(f, 0)
    assert fp(-1) == -1


def test_issue_63():
    """https://github.com/smarie/python-makefun/issues/63"""
    def a(foo=float("inf")):
        pass

    @with_signature(signature(a))
    def test(*args, **kwargs):
        return a(*args, **kwargs)


def test_issue_66():
    """Chain of @wraps with sig mod https://github.com/smarie/python-makefun/issues/66"""

    def a(foo):
        return foo + 1

    assert a(1) == 2

    # create a first wrapper that is signature-preserving

    @wraps(a)
    def wrapper(foo):
        return a(foo) - 1

    assert wrapper(1) == 1

    # the __wrapped__ attr is here:
    assert wrapper.__wrapped__ is a

    # create a second wrapper that is not signature-preserving

    @wraps(wrapper, append_args="bar")
    def second_wrapper(foo, bar):
        return wrapper(foo) + bar

    assert second_wrapper.__wrapped__ is wrapper
    assert "bar" in signature(second_wrapper).parameters
    assert second_wrapper(1, -1) == 0


def test_issue_pr_67():
    """Test handcrafted for https://github.com/smarie/python-makefun/pull/67"""

    class CustomException(Exception):
        pass

    class Foo(object):
        def __init__(self, a=None):
            if a is None:
                raise CustomException()

        def __repr__(self):
            # this is a valid string but calling eval on it will raise an
            return "Foo()"

    f = Foo(a=1)

    # (1) The object can be represented but for some reason its repr can not be evaluated
    with pytest.raises(CustomException):
        eval(repr(f))

    # (2) Lets check that this problem does not impact `makefun`
    def foo(a=Foo(a=1)):
        pass

    @wraps(foo, prepend_args="r")
    def bar(*args, **kwargs):
        pass

    bar(1)


def test_issue_76():
    def f(a):
        return a + 1

    f2 = create_function("zoo(a)", f, func=f)
    assert f2(3) == 4


@pytest.mark.skipif(sys.version_info < (3, 6), reason="requires python 3.6 or higher (async generator)")
async def test_issue_77_async_generator_wraps():
    import asyncio
    from ._test_py36 import make_async_generator, make_async_generator_wrapper

    f = make_async_generator()
    wrapper = wraps(f)(make_async_generator_wrapper(f))

    assert inspect.isasyncgenfunction(f)
    assert inspect.isasyncgenfunction(wrapper)

    out = await asyncio.ensure_future(wrapper(1).__anext__())
    assert out == 1


@pytest.mark.skipif(sys.version_info < (3, 6), reason="requires python 3.6 or higher (async generator)")
async def test_issue_77_async_generator_partial():
    import asyncio
    from ._test_py36 import make_async_generator

    f = make_async_generator()
    f_partial = partial(f, v=1)

    assert inspect.isasyncgenfunction(f)
    assert inspect.isasyncgenfunction(f_partial)

    out = await asyncio.ensure_future(f_partial().__anext__())
    assert out == 1


@pytest.mark.skipif(sys.version_info < (3, 7, 6), reason="The __wrapped__ behavior in get_type_hints being tested was not added until python 3.7.6.")
def test_issue_85_wrapped_forwardref_annotation():
    import typing
    from . import _issue_85_module

    @wraps(_issue_85_module.forwardref_method, remove_args=["bar"])
    def wrapper(**kwargs):
        kwargs["bar"] = "x"  # python 2 syntax to prevent syntax error.
        return _issue_85_module.forwardref_method(**kwargs)

    # Make sure the wrapper function works as expected
    assert wrapper(_issue_85_module.ForwardRef()).x == "defaultx"

    # Check that the type hints of the wrapper are ok with the forward reference correctly resolved
    expected_annotations = {
        "foo": _issue_85_module.ForwardRef,
        "return": _issue_85_module.ForwardRef,
    }
    assert typing.get_type_hints(wrapper) == expected_annotations


def test_issue_91():
    """This test should work also in python 2 ! """
    assert is_identifier("_results_bag")
    assert is_identifier("hello__bag")


@pytest.mark.parametrize('wrapped, args, expected', [
    (len, ('abc',), 3),
    (str.upper, ('abc',), 'ABC'),
    (functools.partial(len), ('abc',), 3),
    (functools.partial(str.upper), ('abc',), 'ABC'),
])
def test_wraps_builtin_issue_94(wrapped, args, expected):
    """Builtins and their partials do not require a writable attribute dict."""
    @wraps(wrapped, _mark=True)
    def wrapper(*args, **kwargs):
        return wrapped(*args, **kwargs)

    assert wrapper(*args) == expected
    assert signature(wrapper) == signature(wrapped)
    assert wrapper.__wrapped__ is wrapped
    assert wrapper._mark is True
    assert not hasattr(wrapped, '_mark')


def test_wraps_setattr_issue_94():
    """The wrapper_descriptor from the original report can be decorated."""
    class Wrapped(object):
        @wraps(object.__setattr__)
        def __setattr__(self, name, value):
            object.__setattr__(self, name, value + 1)

    instance = Wrapped()
    instance.value = 3
    assert instance.value == 4
    assert signature(Wrapped.__setattr__) == signature(object.__setattr__)
    assert Wrapped.__setattr__.__wrapped__ is object.__setattr__


@pytest.mark.parametrize('use_partial', [False, True])
def test_wraps_slots_issue_94(use_partial):
    """Callable instances with slots also work through functools.partial."""
    class Wrapped(object):
        __slots__ = ()

        def __call__(self, value):
            return value + 1

    wrapped = Wrapped()
    if use_partial:
        wrapped = functools.partial(wrapped)

    @wraps(wrapped)
    def wrapper(*args, **kwargs):
        return wrapped(*args, **kwargs)

    assert wrapper(3) == 4
    assert signature(wrapper) == signature(wrapped)
    assert wrapper.__wrapped__ is wrapped


def test_wraps_class_issue_94():
    """A class's read-only attribute mapping is copied without modification."""
    class Wrapped(object):
        """Wrapped class documentation."""
        _mark = []

        def __init__(self, value):
            self.value = value

    original_attrs = dict(Wrapped.__dict__)

    @wraps(Wrapped)
    def wrapper(*args, **kwargs):
        return Wrapped(*args, **kwargs)

    instance = wrapper(3)
    assert isinstance(instance, Wrapped)
    assert instance.value == 3
    assert signature(wrapper) == signature(Wrapped)
    assert wrapper.__wrapped__ is Wrapped
    assert wrapper.__doc__ == Wrapped.__doc__
    assert wrapper._mark is Wrapped._mark
    assert dict(Wrapped.__dict__) == original_attrs


def test_issue_98():
    class A(str):
        def __str__(self):
            return 'custom str'

        def __repr__(self):
            return 'custom repr'

    def foo(a=A()):
        pass

    @wraps(foo)
    def test(*args, **kwargs):
        return foo(*args, **kwargs)
