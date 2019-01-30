import sys

import pytest

from makefun import create_function


# Python 2 does not support function annotations; Python 3.0-3.4 do not support variable annotations.
params_type_hints_allowed = sys.version_info.major >= 3 and sys.version_info.minor >= 5

if params_type_hints_allowed:
    type_hints_variants = [True, False]
else:
    type_hints_variants = [False]


@pytest.mark.parametrize('params_type_hints', type_hints_variants)
def test_basic(params_type_hints):
    """
    Tests that we can create a simple dynamic function from a signature string, redirected to a generic handler.
    """

    if params_type_hints:
        func_signature = "def foo(b: int, a: float = 0)"
    else:
        func_signature = "def foo(b, a = 0)"

    # this handler will grab the inputs and return them
    def identity_handler(*args, **kwargs):
        """test doc"""
        return args, kwargs

    # create the dynamic function
    dynamic_fun = create_function(func_signature, identity_handler)

    # a few asserts on the signature
    assert dynamic_fun.__name__ == 'foo'
    assert dynamic_fun.__doc__ == 'test doc'
    assert dynamic_fun.__module__ == test_basic.__module__
    if params_type_hints:
        assert dynamic_fun.__annotations__ == {'a': float, 'b': int}
    else:
        assert dynamic_fun.__annotations__ == {}
    assert dynamic_fun.__defaults__ == (0, )
    assert dynamic_fun.__kwdefaults__ is None

    dct = {'__source__': func_signature + ':\n    return _call_(b, a)\n'}
    if not params_type_hints_allowed:
        dct['__annotations__'] = dict()
        dct['__kwdefaults__'] = None
    assert vars(dynamic_fun) == dct

    # try to call it !
    assert dynamic_fun(2) == ((2, 0), {})


# def test_sig():
    # b_param = Parameter()
    # parameters = OrderedDict(
    #     ((b_param.name, b_param),
    #      (a_param.name, a_param))
    # )
    #
    # s = Signature().replace(parameters=parameters)
    # # s = s.replace(return_annotation=return_annotation)
