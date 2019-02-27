import sys
import pytest

try:  # python 3.3+
    from inspect import signature, Signature, Parameter
except ImportError:
    from funcsigs import signature, Signature, Parameter


from makefun import create_function, add_signature_parameters, remove_signature_parameters, with_signature

python_version = sys.version_info.major


def test_from_string():
    """ First example from the documentation: tests that we can generate a function from a string """

    # define the signature
    func_signature = "foo(b, a=0)"

    # define the handler that should be called
    def my_handler(*args, **kwargs):
        """This docstring will be used in the generated function by default"""
        print("my_handler called !")
        return args, kwargs

    # create the dynamic function
    dynamic_fun = create_function(func_signature, my_handler)

    # first check the source code
    ref_src = "def foo(b, a=0):\n    return _call_handler_(b=b, a=a)\n"
    print("Generated Source :\n" + dynamic_fun.__source__)
    assert dynamic_fun.__source__ == ref_src

    # then the behaviour
    args, kwargs = dynamic_fun(2)
    assert args == ()
    assert kwargs == {'a': 0, 'b': 2}

    # second case
    if python_version >= 3:
        func_signature = "foo(b, *, a=0, **kwargs)"
        dynamic_fun = create_function(func_signature, my_handler)

        ref_src = "def foo(b, *, a=0, **kwargs):\n    return _call_handler_(b=b, a=a, **kwargs)\n"
        print(dynamic_fun.__source__)
        assert dynamic_fun.__source__ == ref_src


def test_from_sig():
    """ Tests that we can create a function from a Signature object """

    def foo(b, a=0):
        print("foo called: b=%s, a=%s" % (b, a))
        return b, a

    # capture the name and signature of existing function `foo`
    func_name = foo.__name__
    original_func_sig = signature(foo)
    print("Original Signature: %s" % original_func_sig)

    # modify the signature to add a new parameter
    params = list(original_func_sig.parameters.values())
    params.insert(0, Parameter('z', kind=Parameter.POSITIONAL_OR_KEYWORD))
    func_sig = original_func_sig.replace(parameters=params)
    print("New Signature: %s" % func_sig)

    # define the handler that should be called
    def my_handler(z, *args, **kwargs):
        print("my_handler called ! z=%s" % z)
        # call the foo function
        output = foo(*args, **kwargs)
        # return augmented output
        return z, output

    # create the dynamic function
    dynamic_fun = create_function(func_sig, my_handler, func_name=func_name)

    # check the source code
    ref_src = "def foo(z, b, a=0):\n    return _call_handler_(z=z, b=b, a=a)\n"
    print("Generated Source :\n" + dynamic_fun.__source__)
    assert dynamic_fun.__source__ == ref_src

    # then the behaviour
    assert dynamic_fun(3, 2) == (3, (2, 0))


def test_helper_functions():
    """ Tests that the signature modification helpers work """
    def foo(b, c, a=0):
        pass

    # original signature
    original_func_sig = signature(foo)
    assert str(original_func_sig) == '(b, c, a=0)'

    # let's modify it
    func_sig = add_signature_parameters(original_func_sig,
                                        first=(Parameter('z', Parameter.POSITIONAL_OR_KEYWORD),),
                                        last=(Parameter('o', Parameter.POSITIONAL_OR_KEYWORD, default=True),))
    func_sig = remove_signature_parameters(func_sig, 'b', 'a')
    assert str(func_sig) == '(z, c, o=True)'


def test_injection():
    """ Tests that the function can be injected as first argument when inject_as_first_arg=True """
    def generic_handler(f, *args, **kwargs):
        print("This is generic handler called by %s" % f.__name__)
        # here you could use f.__name__ in a if statement to determine what to do
        if f.__name__ == "func1":
            print("called from func1 !")
        return args, kwargs

    # generate 2 functions
    func1 = create_function("func1(a, b)", generic_handler, inject_as_first_arg=True)
    func2 = create_function("func2(a, d)", generic_handler, inject_as_first_arg=True)

    func1(1, 2)
    func2(1, 2)


def test_var_length():
    """Demonstrates how variable-length arguments are passed to the handler """

    # define the handler that should be called
    def my_handler(*args, **kwargs):
        """This docstring will be used in the generated function by default"""
        print("my_handler called !")
        return args, kwargs

    func_signature = "foo(a=0, *args, **kwargs)"
    dynamic_fun = create_function(func_signature, my_handler)
    print(dynamic_fun.__source__)
    assert dynamic_fun(0, 1) == ((1,), {'a': 0})


def test_positional_only():
    """Tests that as of today positional-only signatures translate to bad strings """

    params = [Parameter('a', kind=Parameter.POSITIONAL_ONLY),
              Parameter('b', kind=Parameter.POSITIONAL_OR_KEYWORD)]

    assert str(Signature(parameters=params)) in {"(<a>, b)", "(a, /, b)"}


def test_with_signature():
    """ Tests that @with_signature works as expected """
    @with_signature("foo(a)")
    def foo(**kwargs):
        return 'hello'

    with pytest.raises(TypeError):
        foo()

    assert str(signature(foo)) == "(a)"
    assert foo('dummy') == 'hello'


def test_with_signature_wrapper(capsys):
    # we want to wrap this function f to add some prints before calls
    def f(a, b):
        return a + b

    # create our wrapper: it will have the same signature than f
    @with_signature(f)
    def f_wrapper(*args, **kwargs):
        # first print something interesting
        print('hello')
        # then call f as usual
        return f(*args, **kwargs)

    assert f_wrapper(1, 2) == 3  # prints `'hello` and returns 1 + 2

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)

    assert captured.out == "hello\n"
