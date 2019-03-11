import logging

from makefun import wraps


def test_non_representable_defaults():
    """ Tests that non-representable default values are handled correctly """

    def foo(logger=logging.getLogger('default')):
        pass

    @wraps(foo)
    def bar(*args, **kwargs):
        pass

    bar()
