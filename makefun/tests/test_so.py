import sys
from inspect import getmodule

from makefun import create_function, wraps


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
