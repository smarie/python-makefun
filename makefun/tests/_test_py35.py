from asyncio import sleep


def make_native_coroutine_handler():
    """Returns a native coroutine to be used in tests"""

    async def my_native_coroutine_handler(sleep_time):
        await sleep(sleep_time)
        return sleep_time

    return my_native_coroutine_handler
