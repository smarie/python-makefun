import sys

import pytest

from makefun import with_signature, create_function

try:
    from inspect import iscoroutinefunction
except ImportError:
    # let's assume there are no coroutine functions in old Python
    def iscoroutinefunction(f):
        return False

try:
    from inspect import isgeneratorfunction
except ImportError:
    # assume no generator function in old Python versions
    def isgeneratorfunction(f):
        return False


def test_generator():
    """ Tests that we can use a generator as function_handler in `create_function`"""

    # define the handler that should be called
    def my_generator_handler(b, a=0):
        for i in range(a, b):
            yield i * i

    # create the dynamic function
    dynamic_fun = create_function("foo(a, b)", my_generator_handler)

    assert isgeneratorfunction(dynamic_fun)

    assert list(dynamic_fun(1, 4)) == [1, 4, 9]


def test_generator_with_signature():
    """ Tests that we can write a generator and change its signature: it will still be a generator """

    @with_signature("foo(a)")
    def foo(*args, **kwargs):
        for i in range(1, 4):
            yield i * i

    assert isgeneratorfunction(foo)

    with pytest.raises(TypeError):
        foo()

    assert list(foo('dummy')) == [1, 4, 9]


def test_generator_based_coroutine():
    """ Tests that we can use a generator coroutine as function_handler in `create_function`"""

    # define the handler that should be called
    def my_gencoroutine_handler(first_msg):
        second_msg = (yield first_msg)
        yield second_msg

    # create the dynamic function
    dynamic_fun = create_function("foo(first_msg='hello')", my_gencoroutine_handler)

    # a legacy (generator-based) coroutine is not an asyncio coroutine..
    assert not iscoroutinefunction(dynamic_fun)
    assert isgeneratorfunction(dynamic_fun)

    cor = dynamic_fun('hi')
    first_result = next(cor)
    assert first_result == 'hi'
    second_result = cor.send('chaps')
    assert second_result == 'chaps'
    with pytest.raises(StopIteration):
        cor.send('ola')


@pytest.mark.skipif(sys.version_info < (3, 5), reason="native coroutines with async/await require python3.6 or higher")
def test_native_coroutine():
    """ Tests that we can use a native async coroutine as function_handler in `create_function`"""

    # define the handler that should be called
    from makefun.tests._test_py35 import make_native_coroutine_handler
    my_native_coroutine_handler = make_native_coroutine_handler()

    # create the dynamic function
    dynamic_fun = create_function("foo(sleep_time=2)", my_native_coroutine_handler)

    # check that this is a coroutine for inspect and for asyncio
    assert iscoroutinefunction(dynamic_fun)
    from asyncio import iscoroutinefunction as is_native_co
    assert is_native_co(dynamic_fun)

    # verify that the new function is a native coroutine and behaves correctly
    from asyncio import get_event_loop
    out = get_event_loop().run_until_complete(dynamic_fun(0.1))
    assert out == 0.1
