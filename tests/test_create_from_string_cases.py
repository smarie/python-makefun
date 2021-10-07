import sys

import pytest

params_type_hints_allowed = sys.version_info.major >= 3 and sys.version_info.minor >= 5
star_followed_by_arg_allowed = sys.version_info.major >= 3


def case_simple():
    params_str = "b, a = 0"
    case_simple.__name__ = params_str

    # param_names = ['b', 'a']

    inputs = "12"
    args = ()
    kwargs = {'a': 0, 'b': 12}

    return params_str, inputs, (args, kwargs)


@pytest.mark.skipif(not star_followed_by_arg_allowed, reason='not allowed in this version of python')
def case_simple_with_star():
    params_str = "b, *, a = 0"
    case_simple_with_star.__name__ = params_str

    # param_names = ['b', '*', 'a']

    inputs = "12"
    args = ()
    kwargs = {'a': 0, 'b': 12}
    return params_str, inputs, (args, kwargs)


@pytest.mark.skipif(not star_followed_by_arg_allowed, reason='not allowed in this version of python')
def case_simple_with_star_args1():
    params_str = "b, *args, a = 0"
    case_simple_with_star_args1.__name__ = params_str

    # param_names = ['b', 'a']

    inputs = "12"
    # args = ()
    # kwargs = {'a': 0, 'b': 12}
    args = (12,)
    kwargs = {'a': 0}
    return params_str, inputs, (args, kwargs)


@pytest.mark.skipif(not star_followed_by_arg_allowed, reason='not allowed in this version of python')
def case_simple_with_star_args2():
    params_str = "*args, a = 0"
    case_simple_with_star_args2.__name__ = params_str

    # param_names = ['b', 'a']

    inputs = "12"
    args = (12, )
    kwargs = {'a': 0}
    return params_str, inputs, (args, kwargs)


def case_with_type_comments_and_newlines():
    params_str = "b,      # type: int\n" \
                 "a = 0   # type: float\n"
    case_with_type_comments_and_newlines.__name__ = params_str

    # param_names = ['b', 'a']

    inputs = "12"
    args = ()
    kwargs = {'a': 0, 'b': 12}
    return params_str, inputs, (args, kwargs)
