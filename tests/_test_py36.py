def make_async_generator():
    """Returns a new async generator function to use in tests."""

    async def f(v):
        yield v

    return f


def make_async_generator_wrapper(async_gen_f):
    """Returns a new async generator function wrapping `f`, to use in tests."""

    async def wrapper(*args, **kwargs):
        async for v in async_gen_f(*args, **kwargs):
            yield v

    return wrapper
