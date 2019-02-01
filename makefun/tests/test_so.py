import sys

from makefun import create_function


# Python 2 does not support function annotations; Python 3.0-3.4 do not support variable annotations.
python_version = sys.version_info.major


def test_create_facades():
    """
    Simple test to create multiple functions with the same body
    See https://stackoverflow.com/questions/13184281/python-dynamic-function-creation-with-custom-names
    :return:
    """
    def generic_handler(f, *args, **kwargs):
        print("This is generic handler called by %s" % f.__name__)
        # here you could use f.__name__ in a if statement to determine what to do
        if f.__name__ == "func1":
            print("called from func1 !")
        return args, kwargs

    # generate 3 functions
    for f_name, f_params in [("func1", "b, *, a"),
                             ("func2", "*args, **kwargs"),
                             ("func3", "c, *, a, d=None")]:
        if f_name in {"func1", "func3"} and python_version < 3:
            # ignore: syntax not supported
            pass
        else:
            f = create_function("%s(%s)" % (f_name, f_params), generic_handler, inject_as_first_arg=True)
            assert f.__name__ == f_name
            # try to execute
            args, kwargs = f(25, a=12)

            if f_name == "func1":
                assert args == (), f_name + ' args test failed'
                assert kwargs == dict(b=25, a=12), f_name + ' kwargs test failed'
            elif f_name == "func2":
                assert args == (25,), f_name + ' args test failed'
                assert kwargs == dict(a=12), f_name + ' kwargs test failed'
            elif f_name == "func3":
                assert args == (), f_name + ' args test failed'
                assert kwargs == dict(c=25, a=12, d=None), f_name + ' kwargs test failed'
