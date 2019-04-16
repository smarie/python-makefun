from makefun import wraps


def test_wraps_varpositional():
    """ test for https://github.com/smarie/python-makefun/issues/34 """
    def f(a, *args):
        pass

    @wraps(f)
    def foo(*args, **kwargs):
        return f(*args, **kwargs)

    foo('hello', 12)
