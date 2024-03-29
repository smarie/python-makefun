import sys

import pytest

from makefun import create_function


# Python 2 does not support function annotations; Python 3.0-3.4 do not support variable annotations.
params_type_hints_allowed = sys.version_info.major >= 3 and sys.version_info.minor >= 5

if params_type_hints_allowed:
    type_hints_variants = [False, 1, 2]
else:
    type_hints_variants = [False]


@pytest.mark.parametrize('with_self_ref', [True, False], ids="self_ref={}".format)
@pytest.mark.parametrize('params_type_hints', type_hints_variants, ids="type_hints={}".format)
def test_basic(params_type_hints, with_self_ref):
    """
    Tests that we can create a simple dynamic function from a signature string, redirected to a generic handler.
    """

    if params_type_hints == 1:
        from typing import Any
        func_signature = "foo(b,      # type: int\n" \
                         "    a = 0,  # type: float\n" \
                         "    ):\n    # type: (...) -> Any"
    elif params_type_hints == 2:
        from typing import Any
        func_signature = "foo(b: int, a: float=0) -> Any"
    else:
        func_signature = "foo(b, a=0)"

    # this handler will grab the inputs and return them
    if with_self_ref:
        def identity_handler(facade, *args, **kwargs):
            """test doc"""
            return facade, args, kwargs
    else:
        def identity_handler(*args, **kwargs):
            """test doc"""
            return args, kwargs

    # create the dynamic function
    dynamic_fun = create_function(func_signature, identity_handler, inject_as_first_arg=with_self_ref)

    # a few asserts on the signature
    assert dynamic_fun.__name__ == 'foo'
    assert dynamic_fun.__doc__ == 'test doc'
    assert dynamic_fun.__module__ == test_basic.__module__
    if params_type_hints == 1:
        # unfortunately
        assert dynamic_fun.__annotations__ == {}
    elif params_type_hints == 2:
        assert dynamic_fun.__annotations__ == {'a': float, 'b': int, 'return': Any}
    else:
        assert dynamic_fun.__annotations__ == {}
    assert dynamic_fun.__defaults__ == (0,)
    assert dynamic_fun.__kwdefaults__ is None

    if params_type_hints != 1:
        func_signature = func_signature + ":"
    if with_self_ref:
        src = "def " + func_signature + '\n    return _func_impl_(foo, b=b, a=a)\n'
    else:
        src = "def " + func_signature + '\n    return _func_impl_(b=b, a=a)\n'

    dct = {'__source__': src, '__func_impl__': identity_handler}
    if not params_type_hints_allowed:
        dct['__annotations__'] = dict()
        dct['__kwdefaults__'] = None
    assert vars(dynamic_fun) == dct

    # try to call it !
    if with_self_ref:
        f, args, kwargs = dynamic_fun(2)
        assert f is dynamic_fun
    else:
        args, kwargs = dynamic_fun(2)

    assert args == ()
    assert kwargs == {'a': 0, 'b': 2}


# def test_sig():
    # b_param = Parameter()
    # parameters = OrderedDict(
    #     ((b_param.name, b_param),
    #      (a_param.name, a_param))
    # )
    #
    # s = Signature().replace(parameters=parameters)
    # # s = s.replace(return_annotation=return_annotation)


@pytest.mark.skip("This test is known to fail because inspect.signature does not detect comment type hints")
def test_type_comments():
    """Tests that """

    func_signature = """
foo(b,      # type: int
    a = 0,  # type: float
    ):
    # type: (...) -> str
"""

    def dummy_handler(*args, **kwargs):
        return "hello"

    dynamic_fun = create_function(func_signature, dummy_handler)

    assert dynamic_fun.__annotations__ == {'a': float, 'b': int, 'return': str}


params_type_hints_allowed = sys.version_info.major >= 3 and sys.version_info.minor >= 5
star_followed_by_arg_allowed = sys.version_info.major >= 3


class TestArguments:
    def test_case_simple(self):
        params_str = "b, a = 0"
        # case_simple.__name__ = params_str

        # param_names = ['b', 'a']

        inputs = "12"
        args = ()
        kwargs = {'a': 0, 'b': 12}

        _test_arguments(params_str, inputs, (args, kwargs))

    @pytest.mark.skipif(not star_followed_by_arg_allowed, reason='not allowed in this version of python')
    def test_case_simple_with_star(self):
        params_str = "b, *, a = 0"
        # case_simple_with_star.__name__ = params_str

        # param_names = ['b', '*', 'a']

        inputs = "12"
        args = ()
        kwargs = {'a': 0, 'b': 12}
        _test_arguments(params_str, inputs, (args, kwargs))

    @pytest.mark.skipif(not star_followed_by_arg_allowed, reason='not allowed in this version of python')
    def test_case_simple_with_star_args1(self):
        params_str = "b, *args, a = 0"
        # case_simple_with_star_args1.__name__ = params_str

        # param_names = ['b', 'a']

        inputs = "12"
        # args = ()
        # kwargs = {'a': 0, 'b': 12}
        args = (12,)
        kwargs = {'a': 0}
        _test_arguments(params_str, inputs, (args, kwargs))

    @pytest.mark.skipif(not star_followed_by_arg_allowed, reason='not allowed in this version of python')
    def test_case_simple_with_star_args2(self):
        params_str = "*args, a = 0"
        # case_simple_with_star_args2.__name__ = params_str

        # param_names = ['b', 'a']

        inputs = "12"
        args = (12, )
        kwargs = {'a': 0}
        _test_arguments(params_str, inputs, (args, kwargs))

    def test_case_with_type_comments_and_newlines(self):
        params_str = "b,      # type: int\n" \
                     "a = 0   # type: float\n"
        # test_case_with_type_comments_and_newlines.__name__ = params_str

        # param_names = ['b', 'a']

        inputs = "12"
        args = ()
        kwargs = {'a': 0, 'b': 12}
        _test_arguments(params_str, inputs, (args, kwargs))


def _test_arguments(params_str, inputs, expected):
    """ Tests that the `PARAM_DEF` regexp works correctly """

    def generic_handler(*args, **kwargs):
        return args, kwargs

    f = create_function("foo(%s)" % params_str, generic_handler)

    args, kwargs = eval("f(%s)" % inputs, globals(), locals())

    assert (args, kwargs) == expected
