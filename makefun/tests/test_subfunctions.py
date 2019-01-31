from pytest_cases import cases_data, THIS_MODULE, case_tags

from makefun.main import separate_positional_and_kw, extract_params_names


@case_tags('pos_kw_extractor')
def case_simple():
    param_names = ['a', 'b']
    pos_only = []
    kw_only = []
    rest = ['a', 'b']
    return param_names, pos_only, kw_only, rest


@case_tags('pos_kw_extractor')
def case_lone_star():
    param_names = ['a', '*', 'b']
    pos_only = ['a']
    kw_only = ['b']
    rest = []
    return param_names, pos_only, kw_only, rest


@case_tags('pos_kw_extractor')
def case_varargs():
    param_names = ['*args', '**kwargs']
    pos_only = ['*args']
    kw_only = ['**kwargs']
    rest = []
    return param_names, pos_only, kw_only, rest


@cases_data(module=THIS_MODULE, has_tag='pos_kw_extractor')
def test_pos_kw_extractor(case_data):
    """ Tests that the `separate_positional_and_kw` function works correctly """
    param_names, pos_only, kw_only, rest = case_data.get()

    p, k, r = separate_positional_and_kw(param_names)

    assert p == pos_only
    assert k == kw_only
    assert r == rest


# ---------------------------


@case_tags('params_regex')
def case_simple():
    params_str = "b, a = 0"
    param_names = ['b', 'a']
    return params_str, param_names


@case_tags('params_regex')
def case_simple_with_star():
    params_str = "b, *, a = 0"
    param_names = ['b', '*', 'a']
    return params_str, param_names


@case_tags('params_regex')
def case_with_type_comments_and_newlines():
    params_str = "b,      # type: int\n" \
                 "a = 0,  # type: float\n"
    param_names = ['b', 'a']
    return params_str, param_names


@cases_data(module=THIS_MODULE, has_tag='params_regex')
def test_params_regex(case_data):
    """ Tests that the `PARAM_DEF` regexp works correctly """

    params_str, param_names = case_data.get()

    p = extract_params_names(params_str)

    assert p == param_names
