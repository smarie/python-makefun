from makefun import create_function


def test_basic():
    """
    Tests that we can create a simple dynamic function from a signature string, redirected to a generic handler.
    """

    # let's create a dynamic function with this signature
    func_signature = "def foo(b: int, a: float = 0)"

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
    assert dynamic_fun.__annotations__ == {'a': float, 'b': int}
    assert dynamic_fun.__defaults__ == (0, )
    assert dynamic_fun.__kwdefaults__ is None
    assert vars(dynamic_fun) == {'__source__': 'def foo(b: int, a: float = 0):\n    return _call_(b, a)\n'}

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
