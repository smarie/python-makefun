from __future__ import print_function
import re
import sys
import itertools
from collections import OrderedDict
from copy import copy

try:  # python 3.3+
    from inspect import signature, Signature, Parameter
except ImportError:
    from funcsigs import signature, Signature, Parameter

try:
    from inspect import iscoroutinefunction
except ImportError:
    # let's assume there are no coroutine functions in old Python
    def iscoroutinefunction(f):
        return False

try:
    from inspect import isgeneratorfunction
except ImportError:
    # assume no generator function in old Python versions
    def isgeneratorfunction(f):
        return False

try:  # python 3.5+
    from typing import Callable, Any, Union, Iterable
except ImportError:
    pass


# macroscopic signature strings checker (we do not look inside params, `signature` will do it for us)
FUNC_DEF = re.compile('(?s)^\s*(?P<funcname>[_\w][_\w\d]*)?\s*'
                      '\(\s*(?P<params>.*?)\s*\)\s*'
                      '((?P<typed_return_hint>->\s*.+)|:\s*#\s*(?P<comment_return_hint>.+))*$')


def create_wrapper(wrapped,
                   wrapper,
                   new_sig=None,               # type: Union[str, Signature]
                   func_name=None,             # type: str
                   inject_as_first_arg=False,  # type: bool
                   add_source=True,             # type: bool
                   add_impl=True,            # type: bool
                   doc=None,                   # type: str
                   qualname=None,              # type: str
                   module_name=None,            # type: str
                   **attrs
                   ):
    """
    Creates a signature-preserving wrapper function.

    See `@makefun.wraps`
    """
    func_name, func_sig, doc, qualname, module_name, all_attrs = _get_args_for_wrapping(wrapped, new_sig, func_name,
                                                                                        doc, qualname, module_name,
                                                                                        attrs)

    return create_function(func_sig, wrapper,
                           func_name=func_name,
                           inject_as_first_arg=inject_as_first_arg,
                           add_source=add_source, add_impl=add_impl,
                           doc=doc, qualname=qualname,
                           module_name=module_name,
                           **all_attrs)


def create_function(func_signature,             # type: Union[str, Signature]
                    func_impl,                  # type: Callable[[Any], Any]
                    func_name=None,             # type: str
                    inject_as_first_arg=False,  # type: bool
                    add_source=True,            # type: bool
                    add_impl=True,              # type: bool
                    doc=None,                   # type: str
                    qualname=None,              # type: str
                    module_name=None,           # type: str
                    **attrs):
    """
    Creates a function with signature <func_signature> that will call <func_impl> with its arguments when called.
    Arguments are passed as keyword-arguments when it is possible (so all the time, except for var-positional or
    positional-only arguments that get passed as *args. Note that pos-only does not yet exist in python but this case
    is already covered because it is supported by `Signature` objects).

    `func_signature` can be provided:

     - as a string containing the name and signature without 'def' keyword, such as `'foo(a, b: int, *args, **kwargs)'`.
      In which case the name in the string will be used for the `__name__` and `__qualname__` of the created function
      by default
     - as a `Signature` object, for example created using `signature(f)` or handcrafted. In this case the `__name__`
      and `__qualname__` of the created function will be copied from `func_impl` by default.

    All the other metadata of the created function are defined as follows:

     - default `__name__` attribute (see above) can be overriden by providing a non-None `func_name`
     - default `__qualname__` attribute (see above) can be overridden by providing a non-None `qualname`
     - `__annotations__` attribute is created to match the annotations in the signature.
     - `__doc__` attribute is copied from `func_impl.__doc__` except if overridden using `doc`
     - `__module__` attribute is copied from `func_impl.__module__` except if overridden using `module_name`

    Finally two new attributes are optionally created

     - `__source__` attribute: set if `add_source` is `True` (default), this attribute contains the source code of the
     generated function
     - `__func_impl__` attribute: set if `add_impl` is `True` (default), this attribute contains a pointer to
     `func_impl`

    :param func_signature: either a string without 'def' such as "foo(a, b: int, *args, **kwargs)" or "(a, b: int)",
        or a `Signature` object, for example from the output of `inspect.signature` or from the `funcsigs.signature`
        backport. Note that these objects can be created manually too. If the signature is provided as a string and
        contains a non-empty name, this name will be used instead of the one of the decorated function.
    :param func_impl: the function that will be called when the generated function is executed. Its signature should
        be compliant with (=more generic than) `func_signature`
    :param inject_as_first_arg: if `True`, the created function will be injected as the first positional argument of
        `func_impl`. This can be handy in case the implementation is shared between several facades and needs
        to know from which context it was called. Default=`False`
    :param func_name: provide a non-`None` value to override the created function `__name__` and `__qualname__`. If this
        is `None` (default), the `__name__` will default to the one of `func_impl` if `func_signature` is a `Signature`,
        or to the name defined in `func_signature` if `func_signature` is a `str` and contains a non-empty name.
    :param add_source: a boolean indicating if a '__source__' annotation should be added to the generated function
        (default: True)
    :param add_impl: a boolean indicating if a '__func_impl__' annotation should be added to the generated function
        (default: True)
    :param doc: a string representing the docstring that will be used to set the __doc__ attribute on the generated
        function. If None (default), the doc of func_impl will be used.
    :param qualname: a string representing the qualified name to be used. If None (default), the `__qualname__` will
        default to the one of `func_impl` if `func_signature` is a `Signature`, or to the name defined in
        `func_signature` if `func_signature` is a `str` and contains a non-empty name.
    :param module_name: the name of the module to be set on the function (under __module__ ). If None (default),
        `func_impl.__module__` will be used.
    :param attrs: other keyword attributes that should be set on the function
    :return:
    """
    # grab context from the caller frame
    try:
        attrs.pop('_with_sig_')
        # called from `@with_signature`
        frame = _get_callerframe(offset=1)
    except KeyError:
        frame = _get_callerframe()
    evaldict, _ = extract_module_and_evaldict(frame)

    # name defaults
    user_provided_name = True
    if func_name is None:
        func_name = func_impl.__name__
        user_provided_name = False

    # qname default
    user_provided_qname = True
    if qualname is None:
        qualname = getattr(func_impl, '__qualname__', None)
        user_provided_qname = False

    # doc default
    if doc is None:
        doc = getattr(func_impl, '__doc__', None)

    # module name default
    if module_name is None:
        module_name = func_impl.__module__

    # input signature handling
    if isinstance(func_signature, str):
        # transform the string into a Signature and make sure the string contains ":"
        func_name_from_str, func_signature, func_signature_str = get_signature_from_string(func_signature, evaldict)

        # if not explicitly overridden using `func_name`, the name in the string takes over
        if func_name_from_str is not None:
            if not user_provided_name:
                func_name = func_name_from_str
            if not user_provided_qname:
                qualname = func_name

        # fix the signature if needed
        if func_name_from_str is None:
            func_signature_str = func_name + func_signature_str

    elif isinstance(func_signature, Signature):
        # create the signature string
        func_signature_str = get_signature_string(func_name, func_signature, evaldict)

    else:
        raise TypeError("Invalid type for `func_signature`: %s" % type(func_signature))

    # extract all information needed from the `Signature`
    posonly_names, kwonly_names, varpos_names, varkw_names, unrestricted_names = get_signature_params(func_signature)
    params_names = posonly_names + unrestricted_names + varpos_names + kwonly_names + varkw_names

    # Note: in decorator the annotations were extracted using getattr(func_impl, '__annotations__') instead.
    # This seems equivalent but more general (provided by the signature, not the function), but to check
    annotations, defaults, kwonlydefaults = get_signature_details(func_signature)

    # create the body of the function to compile
    assignments = posonly_names + [("%s=%s" % (k, k)) if k[0] != '*' else k
                                   for k in unrestricted_names + varpos_names + kwonly_names + varkw_names]
    params_str = ', '.join(assignments)
    if inject_as_first_arg:
        params_str = "%s, %s" % (func_name, params_str)

    if _is_generator_func(func_impl):
        if sys.version_info >= (3, 3):
            body = "def %s\n    yield from _func_impl_(%s)\n" % (func_signature_str, params_str)
        else:
            from makefun._main_legacy_py import get_legacy_py_generator_body_template
            body = get_legacy_py_generator_body_template() % (func_signature_str, params_str)
    else:
        body = "def %s\n    return _func_impl_(%s)\n" % (func_signature_str, params_str)

    if iscoroutinefunction(func_impl):
        body = ("async " + body).replace('return', 'return await')

    # create the function by compiling code, mapping the `_func_impl_` symbol to `func_impl`
    protect_eval_dict(evaldict, func_name, params_names)
    evaldict['_func_impl_'] = func_impl
    f = _make(func_name, params_names, body, evaldict)

    # add the source annotation if needed
    if add_source:
        attrs['__source__'] = body

    # add the handler if needed
    if add_impl:
        attrs['__func_impl__'] = func_impl

    # update the signature
    _update_fields(f, name=func_name, qualname=qualname, doc=doc, annotations=annotations,
                   defaults=tuple(defaults), kwonlydefaults=kwonlydefaults,
                   module=module_name, **attrs)

    return f


def _is_generator_func(func_impl):
    """
    Return True if the func_impl is a generator
    :param func_impl:
    :return:
    """
    if (3, 5) <= sys.version_info < (3, 6):
        # with Python 3.5 isgeneratorfunction returns True for all coroutines
        # however we know that it is NOT possible to have a generator
        # coroutine in python 3.5: PEP525 was not there yet
        return isgeneratorfunction(func_impl) and not iscoroutinefunction(func_impl)
    else:
        return isgeneratorfunction(func_impl)


class _SymbolRef:
    """
    A class used to protect signature default values and type hints when the local context would not be able
    to evaluate them properly when the new function is created. In this case we store them under a known name,
    we add that name to the locals(), and we use this symbol that has a repr() equal to the name.
    """
    __slots__ = 'varname'

    def __init__(self, varname):
        self.varname = varname

    def __repr__(self):
        return self.varname


def get_signature_string(func_name, func_signature, evaldict):
    """
    Returns the string to be used as signature.
    If there is a non-native symbol in the defaults, it is created as a variable in the evaldict
    :param func_name:
    :param func_signature:
    :return:
    """
    # protect the parameters if needed
    new_params = []
    for p_name, p in func_signature.parameters.items():
        # if default value can not be evaluated, protect it
        default_needs_protection = _signature_symbol_needs_protection(p.default, evaldict)
        new_default = _protect_signature_symbol(p.default, default_needs_protection, "DEFAULT_%s" % p_name, evaldict)

        # if type hint can not be evaluated, protect it
        annotation_needs_protection = _signature_symbol_needs_protection(p.annotation, evaldict)
        new_annotation = _protect_signature_symbol(p.annotation, annotation_needs_protection, "HINT_%s" % p_name,
                                                   evaldict)

        # replace the parameter with the possibly new default and hint
        p = Parameter(p.name, kind=p.kind, default=new_default, annotation=new_annotation)
        new_params.append(p)

    # if return type hint can not be evaluated, protect it
    return_needs_protection = _signature_symbol_needs_protection(func_signature.return_annotation, evaldict)
    new_return_annotation = _protect_signature_symbol(func_signature.return_annotation, return_needs_protection,
                                                      "RETURNHINT", evaldict)

    # copy signature object
    s = Signature(parameters=new_params, return_annotation=new_return_annotation)

    # return the final string representation
    return "%s%s:" % (func_name, s)


def _signature_symbol_needs_protection(symbol, evaldict):
    """
    Helper method for signature symbols (defaults, type hints) protection.

    Returns True if the given symbol needs to be protected - that is, if its repr() can not be correctly evaluated with current evaldict.
    :param symbol:
    :return:
    """
    if symbol is not None and symbol is not Parameter.empty and not isinstance(symbol, (int, str, float, bool)):
        # check if the repr() of the default value is equal to itself.
        try:
            deflt = eval(repr(symbol), evaldict)
            needs_protection = deflt != symbol
        except SyntaxError:
            needs_protection = True
    else:
        needs_protection = False

    return needs_protection


def _protect_signature_symbol(val, needs_protection, varname, evaldict):
    """
    Helper method for signature symbols (defaults, type hints) protection.

    Returns either `val`, or a protection symbol. In that case the protection symbol
    is created with name `varname` and inserted into `evaldict`

    :param val:
    :param needs_protection:
    :param varname:
    :param evaldict:
    :return:
    """
    if needs_protection:
        # store the object in the evaldict and insert name
        evaldict[varname] = val
        return _SymbolRef(varname)
    else:
        return val


def get_signature_from_string(func_sig_str, evaldict):
    """
    Creates a `Signature` object from the given function signature string.

    :param func_sig_str:
    :return: (func_name, func_sig, func_sig_str). func_sig_str is guaranteed to contain the ':' symbol already
    """
    # escape leading newline characters
    if func_sig_str.startswith('\n'):
        func_sig_str = func_sig_str[1:]

    # match the provided signature. note: fullmatch is not supported in python 2
    def_match = FUNC_DEF.match(func_sig_str)
    if def_match is None:
        raise SyntaxError('The provided function template is not valid: "%s" does not match '
                          '"<func_name>(<func_args>)[ -> <return-hint>]".\n For information the regex used is: "%s"'
                          '' % (func_sig_str, FUNC_DEF.pattern))
    groups = def_match.groupdict()

    # extract function name and parameter names list
    func_name = groups['funcname']
    if func_name is None or func_name == '':
        func_name_ = 'dummy'
        func_name = None
    else:
        func_name_ = func_name
    # params_str = groups['params']
    # params_names = extract_params_names(params_str)

    # find the keyword parameters and the others
    # posonly_names, kwonly_names, unrestricted_names = separate_positional_and_kw(params_names)

    cmt_return_hint = groups['comment_return_hint']
    if cmt_return_hint is None or len(cmt_return_hint) == 0:
        func_sig_str = func_sig_str + ':'

    # Create a dummy function
    # complete the string if name is empty, so that we can actually use _make
    func_sig_str_ = (func_name_ + func_sig_str) if func_name is None else func_sig_str
    body = 'def %s\n    pass\n' % func_sig_str_
    dummy_f = _make(func_name_, [], body, evaldict)

    # return its signature
    return func_name, signature(dummy_f), func_sig_str


# def extract_params_names(params_str):
#     return [m.groupdict()['name'] for m in PARAM_DEF.finditer(params_str)]


# def separate_positional_and_kw(params_names):
#     """
#     Extracts the names that are positional-only, keyword-only, or non-constrained
#     :param params_names:
#     :return:
#     """
#     # by default all parameters can be passed as positional or keyword
#     posonly_names = []
#     kwonly_names = []
#     other_names = params_names
#
#     # but if we find explicit separation we have to change our mind
#     for i in range(len(params_names)):
#         name = params_names[i]
#         if name == '*':
#             del params_names[i]
#             posonly_names = params_names[0:i]
#             kwonly_names = params_names[i:]
#             other_names = []
#             break
#         elif name[0] == '*' and name[1] != '*':  #
#             # that's a *args. Next one will be keyword-only
#             posonly_names = params_names[0:(i + 1)]
#             kwonly_names = params_names[(i + 1):]
#             other_names = []
#             break
#         else:
#             # continue
#             pass
#
#     return posonly_names, kwonly_names, other_names


def get_signature_params(s):
    """
    Utility method to return the parameter names in the provided `Signature` object, by group of kind

    :param s:
    :return:
    """
    posonly_names, kwonly_names, varpos_names, varkw_names, unrestricted_names = [], [], [], [], []
    for p_name, p in s.parameters.items():
        if p.kind is Parameter.POSITIONAL_ONLY:
            posonly_names.append(p_name)
        elif p.kind is Parameter.KEYWORD_ONLY:
            kwonly_names.append(p_name)
        elif p.kind is Parameter.POSITIONAL_OR_KEYWORD:
            unrestricted_names.append(p_name)
        elif p.kind is Parameter.VAR_POSITIONAL:
            varpos_names.append("*" + p_name)
        elif p.kind is Parameter.VAR_KEYWORD:
            varkw_names.append("**" + p_name)
        else:
            raise ValueError("Unknown kind: %s" % p.kind)

    return posonly_names, kwonly_names, varpos_names, varkw_names, unrestricted_names


def get_signature_details(s):
    """
    Utility method to extract the annotations, defaults and kwdefaults from a `Signature` object

    :param s:
    :return:
    """
    annotations = dict()
    defaults = []
    kwonlydefaults = dict()
    if s.return_annotation is not s.empty:
        annotations['return'] = s.return_annotation
    for p_name, p in s.parameters.items():
        if p.annotation is not s.empty:
            annotations[p_name] = p.annotation
        if p.default is not s.empty:
            # if p_name not in kwonly_names:
            if p.kind is not Parameter.KEYWORD_ONLY:
                defaults.append(p.default)
            else:
                kwonlydefaults[p_name] = p.default
    return annotations, defaults, kwonlydefaults


def extract_module_and_evaldict(frame):
    """
    Utility function to extract the module name from the given frame,
    and to return a dictionary containing globals and locals merged together

    :param frame:
    :return:
    """
    try:
        # get the module name
        module_name = frame.f_globals.get('__name__', '?')

        # construct a dictionary with all variables
        # this is required e.g. if a symbol is used in a type hint
        evaldict = copy(frame.f_globals)
        evaldict.update(frame.f_locals)

    except AttributeError:
        # either the frame is None of the f_globals and f_locals are not available
        module_name = '?'
        evaldict = dict()

    return evaldict, module_name


def protect_eval_dict(evaldict, func_name, params_names):
    """
    remove all symbols that could be harmful in evaldict

    :param evaldict:
    :param func_name:
    :param params_names:
    :return:
    """
    try:
        del evaldict[func_name]
    except KeyError:
        pass
    for n in params_names:
        try:
            del evaldict[n]
        except KeyError:
            pass

    return evaldict


# Atomic get-and-increment provided by the GIL
_compile_count = itertools.count()


def _make(funcname, params_names, body, evaldict=None):
    """
    Make a new function from a given template and update the signature

    :param func_name:
    :param params_names:
    :param body:
    :param evaldict:
    :param add_source:
    :return:
    """
    evaldict = evaldict or {}
    for n in params_names:
        if n in ('_func_', '_func_impl_'):
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


def _update_fields(func, name, qualname=None, doc=None, annotations=None, defaults=(), kwonlydefaults=None, module=None, **kw):
    """
    Update the signature of func with the provided information

    This method merely exists to remind which field have to be filled.

    :param self:
    :param func:
    :param kw:
    :return:
    """
    func.__name__ = name

    if qualname is not None:
        func.__qualname__ = qualname

    func.__doc__ = doc
    func.__dict__ = kw

    func.__defaults__ = defaults
    if len(kwonlydefaults) == 0:
        kwonlydefaults = None
    func.__kwdefaults__ = kwonlydefaults

    func.__annotations__ = annotations
    func.__module__ = module


def _get_callerframe(offset=0):
    try:
        # inspect.stack is extremely slow, the fastest is sys._getframe or inspect.currentframe().
        # See https://gist.github.com/JettJones/c236494013f22723c1822126df944b12
        frame = sys._getframe(2 + offset)
        # frame = currentframe()
        # for _ in range(2 + offset):
        #     frame = frame.f_back

    except AttributeError:  # for IronPython and similar implementations
        frame = None

    return frame


def wraps(f,
          new_sig=None,         # type: Union[str, Signature]
          func_name=None,             # type: str
          inject_as_first_arg=False,  # type: bool
          add_source=True,   # type: bool
          add_impl=True,  # type: bool
          doc=None,         # type: str
          qualname=None,    # type: str
          module_name=None,  # type: str
          **attrs
          ):
    """
    Decorator to create a signature-preserving wrapper function.

    It is similar to `functools.wraps`, but relies on a proper dynamically-generated function. Therefore as opposed to
    `functools.wraps`, the wrapper body will not be executed if the arguments provided are not
    compliant with the signature - instead a `TypeError` will be raised before entering the wrapper body.

    `@wraps(f)` is equivalent to

        `@with_signature(signature(f),
                         func_name=f.__name__,
                         doc=f.__doc__,
                         module_name=f.__module__,
                         qualname=f.__qualname__,
                         __wrapped__=f,
                         **f.__dict__,
                         **attrs)`

    In other words, as opposed to `@with_signature`, the metadata (doc, module name, etc.) is provided by the wrapped
    `f`, so that the created function seems to be identical (except for the signature if a non-None `new_sig` is
    provided). If `new_sig` is None, we set the additional `__wrapped__` attribute on the created function, to stay
    compliant with the `functools.wraps` convention.
    See https://docs.python.org/3/library/functools.html#functools.wraps
    """
    func_name, func_sig, doc, qualname, module_name, all_attrs = _get_args_for_wrapping(f, new_sig, func_name, doc,
                                                                                        qualname, module_name, attrs)

    return with_signature(func_sig,
                          func_name=func_name,
                          inject_as_first_arg=inject_as_first_arg,
                          add_source=add_source, add_impl=add_impl,
                          doc=doc,
                          qualname=qualname,
                          module_name=module_name,
                          **all_attrs)


def _get_args_for_wrapping(wrapped, new_sig, func_name, doc, qualname, module_name, attrs):
    """
    Internal method used by @wraps and create_wrapper

    :param wrapped:
    :param new_sig:
    :param func_name:
    :param doc:
    :param qualname:
    :param module_name:
    :param attrs:
    :return:
    """
    # the desired signature
    func_sig = signature(wrapped) if new_sig is None else new_sig

    # the desired metadata
    if func_name is None:
        func_name = wrapped.__name__
    if doc is None:
        doc = wrapped.__doc__
    if qualname is None:
        qualname = getattr(wrapped, '__qualname__', None)
    if module_name is None:
        module_name = wrapped.__module__

    # attributes: start from the wrapped dict, add '__wrapped__' if needed, and override with all attrs.
    all_attrs = copy(wrapped.__dict__)
    if new_sig is None:
        all_attrs['__wrapped__'] = wrapped
    all_attrs.update(attrs)

    return func_name, func_sig, doc, qualname, module_name, all_attrs


def with_signature(func_signature,             # type: Union[str, Signature]
                   func_name=None,             # type: str
                   inject_as_first_arg=False,  # type: bool
                   add_source=True,             # type: bool
                   add_impl=True,            # type: bool
                   doc=None,                   # type: str
                   qualname=None,              # type: str
                   module_name=None,            # type: str
                   **attrs
                   ):
    """
    A decorator for functions, to change their signature. The new signature should be compliant with the old one.

    ```python
    @with_signature(<arguments>)
    def impl(...):
        ...
    ```

    is totally equivalent to `impl = create_function(<arguments>, func_impl=impl)` except for one additional behaviour:

     - If `func_signature` is set to `None`, there is no `TypeError` as in create_function. Instead, this simply
     applies the new metadata (name, doc, module_name, attrs) to the decorated function without creating a wrapper.
     `add_source`, `add_impl` and `inject_as_first_arg` should not be set in this case.

    :param func_signature: the new signature of the decorated function. Either a string without 'def' such as
        "foo(a, b: int, *args, **kwargs)" of "(a, b: int)", or a `Signature` object, for example from the output of
        `inspect.signature` or from the `funcsigs.signature` backport. Note that these objects can be created manually
        too. If the signature is provided as a string and contains a non-empty name, this name will be used instead
        of the one of the decorated function. Finally `None` can be provided to indicate that user wants to only change
        the medatadata (func_name, doc, module_name, attrs) of the decorated function, without generating a new
        function.
    :param inject_as_first_arg: if `True`, the created function will be injected as the first positional argument of
        the decorated function. Default=`False`
    :param func_name: provide a non-`None` value to override the created function `__name__` and `__qualname__`. If this
        is `None` (default), the `__name__` and `__qualname__` will default to the ones of the decorated function if
        `func_signature` is a `Signature`, or to the name defined in `func_signature` if `func_signature` is a `str`
        and contains a non-empty name.
    :param add_source: a boolean indicating if a '__source__' annotation should be added to the generated function
        (default: True)
    :param add_impl: a boolean indicating if a '__func_impl__' annotation should be added to the generated function
        (default: True)
    :param doc: a string representing the docstring that will be used to set the __doc__ attribute on the generated
        function. If None (default), the doc of func_impl will be used.
    :param qualname: a string representing the qualified name to be used. If None (default), the `__qualname__` will
        default to the one of `func_impl` if `func_signature` is a `Signature`, or to the name defined in
        `func_signature` if `func_signature` is a `str` and contains a non-empty name.
    :param module_name: the name of the module to be set on the function (under __module__ ). If None (default),
        `func_impl.__module__` will be used.
    :param attrs: other keyword attributes that should be set on the function
    """
    if func_signature is None:
        # make sure that user does not provide non-default other args
        if inject_as_first_arg or not add_source or not add_impl:
            raise ValueError("If `func_signature=None` no new signature will be generated so only `func_name`, "
                             "`module_name`, `doc` and `attrs` should be provided, to modify the metadata.")
        else:
            def replace_f(f):
                # manually apply all the non-None metadata, but do not call create_function - that's useless
                if func_name is not None:
                    f.__name__ = func_name
                if doc is not None:
                    f.__doc__ = doc
                if qualname is not None:
                    f.__qualname__ = qualname
                if module_name is not None:
                    f.__module__ = module_name
                for k, v in attrs.items():
                    setattr(f, k, v)
                return f
    else:
        def replace_f(f):
            return create_function(func_signature=func_signature,
                                   func_impl=f,
                                   func_name=func_name,
                                   inject_as_first_arg=inject_as_first_arg,
                                   add_source=add_source,
                                   add_impl=add_impl,
                                   doc=doc,
                                   qualname=qualname,
                                   module_name=module_name,
                                   _with_sig_=True,  # special trick to tell create_function that we're @with_signature
                                   **attrs
                                   )

    return replace_f


def remove_signature_parameters(s, *param_names):
    """
    Removes the provided parameters from the signature s (returns a new signature instance).

    :param s:
    :param param_names: a list of parameter names to remove
    :return:
    """
    params = OrderedDict(s.parameters.items())
    for param_name in param_names:
        del params[param_name]
    return s.replace(parameters=params.values())


def add_signature_parameters(s,         # type: Signature
                             first=(),  # type: Union[Parameter, Iterable[Parameter]]
                             last=(),   # type: Union[Parameter, Iterable[Parameter]]
                             ):
    """
    Adds the provided parameters to the signature s (returns a new signature instance).

    :param s:
    :param first: a single element or a list of `Parameter` instances to be added at the beginning of the parameter's
        list
    :param last: a single element or a list of `Parameter` instances to be added at the end of the parameter's list
    :return:
    """
    params = OrderedDict(s.parameters.items())
    lst = list(params.values())

    # prepend but keep the order
    try:
        for param in reversed(first):
            if param.name in params:
                raise ValueError("Parameter with name '%s' is present twice in the signature to create" % param.name)
            else:
                lst.insert(0, param)
    except TypeError:
        # a single argument
        if first.name in params:
            raise ValueError("Parameter with name '%s' is present twice in the signature to create" % first.name)
        else:
            lst.insert(0, first)

    # append
    try:
        for param in last:
            if param.name in params:
                raise ValueError("Parameter with name '%s' is present twice in the signature to create" % param.name)
            else:
                lst.append(param)
    except TypeError:
        # a single argument
        if last.name in params:
            raise ValueError("Parameter with name '%s' is present twice in the signature to create" % last.name)
        else:
            lst.append(last)

    return s.replace(parameters=lst)


def with_partial(*preset_pos_args, **preset_kwargs):
    """
    Decorator to 'partialize' a function using `partial`

    :param preset_pos_args:
    :param preset_kwargs:
    :return:
    """
    def apply_decorator(f):
        return partial(f, *preset_pos_args, **preset_kwargs)
    return apply_decorator


def partial(f, *preset_pos_args, **preset_kwargs):
    """

    :param preset_pos_args:
    :param preset_kwargs:
    :return:
    """
    # TODO do we need to mimic `partial`'s behaviour concerning positional args?

    # (1) remove all preset arguments from the signature
    orig_sig = signature(f)
    # first the first n positional
    if len(orig_sig.parameters) <= len(preset_pos_args):
        raise ValueError("Cannot preset %s positional args, function %s has only %s args."
                         "" % (len(preset_pos_args), f.__name__, len(orig_sig.parameters)))
    new_sig = Signature(parameters=tuple(orig_sig.parameters.values())[len(preset_pos_args):],
                        return_annotation=orig_sig.return_annotation)
    # then the keyword
    try:
        new_sig = remove_signature_parameters(new_sig, *preset_kwargs.keys())
    except KeyError as e:
        raise ValueError("Cannot preset keyword argument, it does not appear to be present in the signature of %s: %s"
                         "" % (f.__name__, e))

    if _is_generator_func(f):
        if sys.version_info >= (3, 3):
            from makefun._main_latest_py import make_partial_using_yield_from
            partial_f = make_partial_using_yield_from(new_sig, f, *preset_pos_args, **preset_kwargs)
        else:
            from makefun._main_legacy_py import make_partial_using_yield
            partial_f = make_partial_using_yield(new_sig, f, *preset_pos_args, **preset_kwargs)
    else:
        @wraps(f, new_sig=new_sig)
        def partial_f(*args, **kwargs):
            # since the signature does the checking for us, no need to check for redundancy.
            kwargs.update(preset_kwargs)
            return f(*itertools.chain(preset_pos_args, args), **kwargs)

    # update the doc
    argstring = ', '.join([("%s" % a) for a in preset_pos_args])
    if len(argstring) > 0:
        argstring = argstring + ', '
    argstring = argstring + str(new_sig)[1:-1]
    if len(argstring) > 0:
        argstring = argstring + ', '
    argstring = argstring + ', '.join(["%s=%s" % (k, v) for k, v in preset_kwargs.items()])

    # new_line = new_line + ("-" * (len(new_line) - 1)) + '\n'
    doc = getattr(partial_f, '__doc__', None)
    if doc is None or len(doc) == 0:
        partial_f.__doc__ = "<This function is equivalent to '%s(%s)'.>\n" % (partial_f.__name__, argstring)
    else:
        new_line = "<This function is equivalent to '%s(%s)', see original '%s' doc below.>\n" \
                   "" % (partial_f.__name__, argstring, partial_f.__name__)
        partial_f.__doc__ = new_line + doc

    return partial_f
