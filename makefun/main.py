from __future__ import print_function
import re
import sys
import itertools

try:  # python 3.3+
    from inspect import signature
except ImportError:
    from funcsigs import signature


# if sys.version >= '3':
#     from inspect import getfullargspec
# else:
#     from inspect import getargspec
#     class getfullargspec(object):
#         "A quick and dirty replacement for getfullargspec for Python 2.X"
#         def __init__(self, f):
#             self.args, self.varargs, self.varkw, self.defaults = getargspec(f)
#             self.kwonlyargs = []
#             self.kwonlydefaults = None
#
#         def __iter__(self):
#             yield self.args
#             yield self.varargs
#             yield self.varkw
#             yield self.defaults
#
#         # getargspec = getargspec


# FUNC_NAME_PTRN = '[_\w][_\w\d]*'
# FUNC_ARGS_PTRN = '.*?'
# FUNC_SIG_PTRN = '\s*def\s*(?P<funcname>' + FUNC_NAME_PTRN + ')\s*\(\s*(?P<params>' + FUNC_ARGS_PTRN + ')\s*\)'
# FUNC_DEF = re.compile(FUNC_SIG_PTRN)
FUNC_DEF = re.compile('\s*def\s*(?P<funcname>[_\w][_\w\d]*)\s*\(\s*(?P<params>.*?)\s*\)')

# ARG_NAME_PTRN = '\*?\*?([_\w][_\w\d]*)'
# FUNC_ARG_PATTERN = ARG_NAME_PTRN + '[^,]*|\*'  # a parameter is either * or a name followed by (hints, defaults...)
# PARAM_DEF = re.compile(FUNC_ARG_PATTERN)
PARAM_DEF = re.compile('\*?\*?([_\w][_\w\d]*)[^,]*|\*')


def create_function(func_signature, func_handler, addsource=True, doc=None, **attrs):
    """
    Creates a function with signature <func_signature> that will call <func_handler> with its arguments in order
    when called.

    :param func_signature:
    :param func_handler:
    :param addsource: a boolean indicating if a '__source__' annotation should be added to the generated function
        (default: True)
    :param doc: if None (default), the doc of func_handler will be used. Otherwise a string representing the docstring.
    :return:
    """

    # match the provided signature
    def_match = FUNC_DEF.match(func_signature)
    if def_match is None:
        raise SyntaxError('not a valid function template\n%s' % func_signature)
    groups = def_match.groupdict()

    # extract function name and parameter names list
    func_name = groups['funcname']
    params_list = groups['params']
    params_names = PARAM_DEF.findall(params_list)

    # create the body of the function to compile
    body = '%s:\n    return _call_(%s)\n' % (func_signature, ', '.join(params_names))

    # define the missing symbols
    evaldict = {'_call_': func_handler}

    # create the function
    f = _make(func_name, params_names, body, evaldict, addsource)

    # add the source annotation if needed
    if addsource:
        attrs['__source__'] = body

    # extract the defaults and kwdefaults from the generated function
    # argspec = getfullargspec(f)
    # kwdefault = getattr(argspec, 'kwonlydefaults', None)
    # defaults = getattr(argspec, 'defaults', ())
    # annotations cant be extracted this way...

    # extract everything needed from the generated function
    s = signature(f)
    annotations = dict()
    defaults = []
    if s.return_annotation is not s.empty:
        annotations['return'] = s.return_annotation
    for p_name, p in s.parameters.items():
        if p.annotation is not s.empty:
            annotations[p_name] = p.annotation
        if p.default is not s.empty:
            defaults.append(p.default)
    kwonlydefaults = None

    # by default the doc is the one from the provided handler
    if doc is None:
        doc = getattr(func_handler, '__doc__', None)

    # update the signature
    _update_signature(f, name=func_name, doc=doc, annotations=annotations,
                      defaults=tuple(defaults), kwonlydefaults=kwonlydefaults,
                      module=_get_callermodule(), **attrs)

    return f


# Atomic get-and-increment provided by the GIL
_compile_count = itertools.count()


def _make(funcname, params_names, body, evaldict=None, addsource=False):
    """
    Make a new function from a given template and update the signature

    :param func_name:
    :param params_names:
    :param body:
    :param evaldict:
    :param addsource:
    :return:
    """
    evaldict = evaldict or {}
    for n in params_names:
        if n in ('_func_', '_call_'):
            raise NameError('%s is overridden in\n%s' % (n, body))

    if not body.endswith('\n'):  # newline is needed for old Pythons
        raise ValueError("body should end with a newline")

    # Ensure each generated function has a unique filename for profilers
    # (such as cProfile) that depend on the tuple of (<filename>,
    # <definition line>, <function name>) being unique.
    filename = '<makefun-gen-%d>' % (next(_compile_count),)
    try:
        code = compile(body, filename, 'single')
        exec(code, evaldict)
    except:
        print('Error in generated code:', file=sys.stderr)
        print(body, file=sys.stderr)
        raise

    # extract the function from compiled code
    func = evaldict[funcname]

    return func


def _update_signature(func, name, doc=None, annotations=None, defaults=(), kwonlydefaults=None, module=None, **kw):
    """
    Update the signature of func with the provided information

    This method merely exists to remind which field have to be filled.

    :param self:
    :param func:
    :param kw:
    :return:
    """
    func.__name__ = name
    func.__doc__ = doc
    func.__dict__ = kw

    func.__defaults__ = defaults
    func.__kwdefaults__ = kwonlydefaults

    func.__annotations__ = annotations
    func.__module__ = module



def _get_callermodule():
    try:
        frame = sys._getframe(2)
    except AttributeError:  # for IronPython and similar implementations
        callermodule = '?'
    else:
        callermodule = frame.f_globals.get('__name__', '?')

    return callermodule
