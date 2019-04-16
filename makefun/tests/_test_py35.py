from asyncio import sleep


def make_native_coroutine_handler():
    """Returns a native coroutine to be used in tests"""

    async def my_native_coroutine_handler(sleep_time):
        await sleep(sleep_time)
        return sleep_time

    return my_native_coroutine_handler


def make_ref_function():
    """Returns a function with a type hint that is locally defined """

    # the symbol is defined here, so it is not seen outside
    class A:
        pass

    def ref(a: A) -> A:
        pass

    return ref


def make_ref_function2():
    """ """
    from typing import Any

    def ref(a: Any):
        pass

    return ref
