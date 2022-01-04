from makefun import wraps, partial


def make_async_generator():
    async def f(v):
        yield v

    return f


def make_async_generator_wrapper(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        async for v in f(*args, **kwargs):
            yield v

    return wrapper


def make_async_generator_partial(f, *args, **kwargs):
    return partial(f, *args, **kwargs)
