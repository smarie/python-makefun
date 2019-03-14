from makefun import with_partial


def test_doc():
    def foo(x, y):
        """
        a `foo` function

        :param x:
        :param y:
        :return:
        """
        return x + y

    from makefun import partial
    bar = partial(foo, x=12)
    bar.__name__ = 'bar'
    help(bar)
    assert bar(1) == 13


def test_partial():
    """Tests that `with_partial` works"""

    @with_partial(a='hello')
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

    assert foo.__doc__ == """<This function is equivalent to 'foo(x, y, a=hello)', see original 'foo' doc below.>

        a `foo` function

        :param x:
        :param y:
        :param a:
        :return:
        """
