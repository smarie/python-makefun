from __future__ import print_function
import re
import sys
import itertools
from copy import copy

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
FUNC_DEF = re.compile('(?s)^\s*(?P<funcname>[_\w][_\w\d]*)\s*\(\s*(?P<params>.*?)\s*\)\s*'
                      '((?P<typed_return_hint>->\s*.+)|:\s*#\s*(?P<comment_return_hint>.+))*$')

# ARG_NAME_PTRN = '\*?\*?([_\w][_\w\d]*)'
# FUNC_ARG_PATTERN = ARG_NAME_PTRN + '[^,]*|\*'  # a parameter is either * or a name followed by (hints, defaults...)
# PARAM_DEF = re.compile(FUNC_ARG_PATTERN)
PARAM_DEF = re.compile('(?P<name>\*?\*?[_\w][_\w\d]*|\*)\s*'
                       '(?P<type_hint>:\s*.*?)*\s*'
                       '(?P<default_val>=\s*.*?)*\s*'
                       '(?P<comment_hint>,?\s*#.*?)*\s*'
                       '(?P<final_delim>[,)]|$)')


def create_function(func_signature, func_handler, inject_as_first_arg=False, addsource=True, doc=None, **attrs):
    """
    Creates a function with signature <func_signature> that will call <func_handler> with its arguments in order
    when called.

    :param func_signature:
    :param func_handler:
    :param inject_as_first_arg: if True, the created function will be injected as the first positional argument of the
        function handler. This can be handy in case the handler is shared between several facades and needs to know
        from which context it was called. Default=False
    :param addsource: a boolean indicating if a '__source__' annotation should be added to the generated function
        (default: True)
    :param doc: if None (default), the doc of func_handler will be used. Otherwise a string representing the docstring.
    :return:
    """

    # escape leading newline characters
    if func_signature.startswith('\n'):
        func_signature = func_signature[1:]

    # match the provided signature. note: fullmatch is not supported in python 2
    def_match = FUNC_DEF.match(func_signature)
    if def_match is None:
        raise SyntaxError('The provided function template is not valid: "%s" does not match '
                          '"<func_name>(<func_args>)[ -> <return-hint>]".\n For information the regex used is: "%s"'
                          '' % (func_signature, FUNC_DEF.pattern))
    groups = def_match.groupdict()

    # extract function name and parameter names list
    func_name = groups['funcname']
    params_str = groups['params']
    # params_names = PARAM_DEF.findall(params_list)
    params_names = extract_params_names(params_str)

    # find the keyword parameters and the others
    posonly_names, kwonly_names, unrestricted_names = separate_positional_and_kw(params_names)

    # create the body of the function to compile
    assignments = posonly_names + [("%s=%s" % (k, k)) if k[0:2] != '**' else k
                                   for k in unrestricted_names + kwonly_names]
    p_signature = ', '.join(assignments)
    if inject_as_first_arg:
        p_signature = "%s, %s" % (func_name, p_signature)
    cmt_return_hint = groups['comment_return_hint']
    if cmt_return_hint is None or len(cmt_return_hint) == 0:
        func_signature = func_signature + ':'

    body = 'def %s\n    return _call_handler_(%s)\n' % (func_signature, p_signature)

    # grab information from the caller frame
    frame = _get_callerframe()
    try:
        # get the module name
        modulename = frame.f_globals.get('__name__', '?')

        # construct a dictionary with all variables
        # this is required e.g. if a symbol is used in a type hint
        evaldict = copy(frame.f_globals)
        evaldict.update(frame.f_locals)

    except AttributeError:
        # either the frame is None of the f_globals and f_locals are not available
        modulename = '?'
        evaldict = dict()

    evaldict['_call_handler_'] = func_handler

    # just in case - remove all symbols that could be harmful
    try:
        del evaldict[func_name]
    except KeyError:
        pass
    for n in params_names:
        try:
            del evaldict[n]
        except KeyError:
            pass

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
    kwonlydefaults = dict()
    if s.return_annotation is not s.empty:
        annotations['return'] = s.return_annotation
    for p_name, p in s.parameters.items():
        if p.annotation is not s.empty:
            annotations[p_name] = p.annotation
        if p.default is not s.empty:
            if p_name not in kwonly_names:
                defaults.append(p.default)
            else:
                kwonlydefaults[p_name] = p.default

    # by default the doc is the one from the provided handler
    if doc is None:
        doc = getattr(func_handler, '__doc__', None)

    # update the signature
    _update_signature(f, name=func_name, doc=doc, annotations=annotations,
                      defaults=tuple(defaults), kwonlydefaults=kwonlydefaults,
                      module=modulename, **attrs)

    return f


def extract_params_names(params_str):
    return [m.groupdict()['name'] for m in PARAM_DEF.finditer(params_str)]


def separate_positional_and_kw(params_names):
    """
    Extracts the names that are positional-only, keyword-only, or non-constrained
    :param params_names:
    :return:
    """
    # by default all parameters can be passed as positional or keyword
    posonly_names = []
    kwonly_names = []
    other_names = params_names

    # but if we find explicit separation we have to change our mind
    for i in range(len(params_names)):
        name = params_names[i]
        if name == '*':
            del params_names[i]
            posonly_names = params_names[0:i]
            kwonly_names = params_names[i:]
            other_names = []
            break
        elif name[0] == '*' and name[1] != '*':  #
            # that's a *args. Next one will be keyword-only
            posonly_names = params_names[0:(i + 1)]
            kwonly_names = params_names[(i + 1):]
            other_names = []
            break
        else:
            # continue
            pass

    return posonly_names, kwonly_names, other_names


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
        if n in ('_func_', '_call_handler_'):
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
    if len(kwonlydefaults) == 0:
        kwonlydefaults = None
    func.__kwdefaults__ = kwonlydefaults

    func.__annotations__ = annotations
    func.__module__ = module


def _get_callerframe():
    try:
        frame = sys._getframe(2)
    except AttributeError:  # for IronPython and similar implementations
        frame = None

    return frame
