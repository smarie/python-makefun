from __future__ import print_function
import sys
from inspect import getmodule

import pytest

from makefun import create_function, wraps, partial, with_partial

try:  # python 3.3+
    from inspect import signature, Signature, Parameter
except ImportError:
    from funcsigs import signature, Signature, Parameter


def test_create_facades(capsys):
    """
    Simple test to create multiple functions with the same body
    This corresponds to the answer at
    https://stackoverflow.com/questions/13184281/python-dynamic-function-creation-with-custom-names/55105893#55105893
    :return:
    """

    # generic core implementation
    def generic_impl(f, *args, **kwargs):
        print("This is generic impl called by %s" % f.__name__)
        # here you could use f.__name__ in a if statement to determine what to do
        if f.__name__ == "func1":
            print("called from func1 !")
        return args, kwargs

    my_module = getmodule(generic_impl)

    # generate 3 facade functions with various signatures
    for f_name, f_params in [("func1", "b, *, a"),
                             ("func2", "*args, **kwargs"),
                             ("func3", "c, *, a, d=None")]:
        if f_name in {"func1", "func3"} and sys.version_info < (3, 0):
            # Python 2 does not support function annotations; Python 3.0-3.4 do not support variable annotations.
            pass
        else:
            # the signature to generate
            f_sig = "%s(%s)" % (f_name, f_params)

            # create the function dynamically
            f = create_function(f_sig, generic_impl, inject_as_first_arg=True)

            # assign the symbol somewhere (local context, module...)
            setattr(my_module, f_name, f)

    # grab each function and use it
    if sys.version_info >= (3, 0):
        func1 = getattr(my_module, 'func1')
        assert func1(25, a=12) == ((), dict(b=25, a=12))

    func2 = getattr(my_module, 'func2')
    assert func2(25, a=12) == ((25,), dict(a=12))

    if sys.version_info >= (3, 0):
        func3 = getattr(my_module, 'func3')
        assert func3(25, a=12) == ((), dict(c=25, a=12, d=None))

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)

    if sys.version_info >= (3, 0):
        assert captured.out == """This is generic impl called by func1
called from func1 !
This is generic impl called by func2
This is generic impl called by func3
"""
    else:
        assert captured.out == """This is generic impl called by func2
"""


def test_so_decorator():
    """
    Tests that solution at
    https://stackoverflow.com/questions/739654/how-to-make-a-chain-of-function-decorators/1594484#1594484
    actually works
    """

    # from functools import wraps

    def makebold(fn):
        @wraps(fn)
        def wrapped():
            return "<b>" + fn() + "</b>"

        return wrapped

    def makeitalic(fn):
        @wraps(fn)
        def wrapped():
            return "<i>" + fn() + "</i>"

        return wrapped

    @makebold
    @makeitalic
    def hello():
        """what?"""
        return "hello world"

    assert hello() == "<b><i>hello world</i></b>"
    assert hello.__name__ == "hello"
    help(hello)  # the help and signature are preserved
    assert hasattr(hello, '__wrapped__')


def test_so_facade():
    def create_initiation_function(cls, gen_init):
        # (1) check which signature we want to create
        params = [Parameter('self', kind=Parameter.POSITIONAL_OR_KEYWORD)]
        for mandatory_arg_name in cls.__init_args__:
            params.append(Parameter(mandatory_arg_name, kind=Parameter.POSITIONAL_OR_KEYWORD))
        for default_arg_name, default_arg_val in cls.__opt_init_args__.items():
            params.append(Parameter(default_arg_name, kind=Parameter.POSITIONAL_OR_KEYWORD, default=default_arg_val))
        sig = Signature(params)

        # (2) create the init function dynamically
        return create_function(sig, generic_init)

    # ----- let's use it

    def generic_init(self, *args, **kwargs):
        """Function to initiate a generic object"""
        assert len(args) == 0
        for name, val in kwargs.items():
            setattr(self, name, val)

    class my_class:
        __init_args__ = ["x", "y"]
        __opt_init_args__ = {"my_opt": None}

    my_class.__init__ = create_initiation_function(my_class, generic_init)

    # check
    o1 = my_class(1, 2)
    assert vars(o1) == {'y': 2, 'x': 1, 'my_opt': None}

    o2 = my_class(1, 2, 3)
    assert vars(o2) == {'y': 2, 'x': 1, 'my_opt': 3}

    o3 = my_class(my_opt='hello', y=3, x=2)
    assert vars(o3) == {'y': 3, 'x': 2, 'my_opt': 'hello'}


def test_so_sig_preserving(capsys):
    """
    Tests that the answer at
    https://stackoverflow.com/a/55163391/7262247
    is correct
    """
    def my_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._decorator_name_ = 'my_decorator'
        return wrapper

    @my_decorator
    def my_func(x):
        """my function"""
        print('hello %s' % x)

    assert my_func._decorator_name_ == 'my_decorator'
    help(my_func)

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)

    assert captured.out == """Help on function my_func in module makefun.tests.test_so:

my_func(x)
    my function

"""


def test_sig_preserving_2(capsys):
    """
    Checks that answer at
    https://stackoverflow.com/a/55163816/7262247
    works
    """
    def args_as_ints(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print("wrapper executes")
            # convert all to int. note that in a signature-preserving wrapper almost all args will come as kwargs
            args = [int(x) for x in args]
            kwargs = dict((k, int(v)) for k, v in kwargs.items())
            return func(*args, **kwargs)

        return wrapper

    @args_as_ints
    def funny_function(x, y, z=3):
        """Computes x*y + 2*z"""
        return x * y + 2 * z

    print(funny_function("3", 4.0, z="5"))
    # 22
    help(funny_function)
    # Help on function funny_function in module __main__:
    #
    # funny_function(x, y, z=3)
    #     Computes x*y + 2*z

    with pytest.raises(TypeError):
        funny_function(0)  # TypeError: funny_function() takes at least 2 arguments (1 given)

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)

    assert captured.out == """wrapper executes
22
Help on function funny_function in module makefun.tests.test_so:

funny_function(x, y, z=3)
    Computes x*y + 2*z

"""


def test_so_partial(capsys):
    """
    Tests that the answer at
    https://stackoverflow.com/a/55165541/7262247
    is correct
    """
    def foo(a, b, c=1):
        """Return (a+b)*c."""
        return (a + b) * c

    bar10_p = partial(foo, b=10)

    assert bar10_p(0) == 10
    assert bar10_p(0, c=2) == 20

    help(bar10_p)

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)

    assert captured.out == """Help on function foo in module makefun.tests.test_so:

foo(a, c=1)
    <This function is equivalent to 'foo(a, c=1, b=10)', see original 'foo' doc below.>
    Return (a+b)*c.

"""


def test_so_partial2(capsys):
    """
    Tests that the solution at
    https://stackoverflow.com/a/55161579/7262247
    works (the one using makefun only. for the other two, see test.so.py in decopatch project)
    """

    @with_partial(a='hello', b='world')
    def test(a, b, x, y):
        print(a, b)
        print(x, y)

    test(1, 2)
    help(test)

    @with_partial(a='hello', b='world')
    def test(a, b, x, y):
        """Here is a doc"""
        print(a, b)
        print(x, y)

    help(test)

    captured = capsys.readouterr()
    with capsys.disabled():
        print(captured.out)

    ref_str = """hello world
1 2
Help on function test in module makefun.tests.test_so:

test(x, y)
    <This function is equivalent to 'test(x, y, a=hello, b=world)'.>

Help on function test in module makefun.tests.test_so:

test(x, y)
    <This function is equivalent to 'test(x, y, a=hello, b=world)', see original 'test' doc below.>
    Here is a doc

"""

    if (3, 0) <= sys.version_info < (3, 6):
        # in older versions of python, the order of **kwargs is not guaranteed (see PEP 468)
        assert captured.out.replace('a=hello', 'b=world') == ref_str.replace('a=hello', 'b=world')
    else:
        assert captured.out == ref_str
