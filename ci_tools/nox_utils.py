import shutil
from collections import namedtuple
from inspect import signature
import logging
import os

from makefun import wraps, remove_signature_parameters
from typing import Sequence, Dict, Union
from pathlib import Path

import nox


nox_logger = logging.getLogger("nox")


PY27, PY35, PY36, PY37, PY38 = "2.7", "3.5", "3.6", "3.7", "3.8"
DONT_INSTALL = "dont_install"


def read_pyproject_toml():
    """
    Reads the `pyproject.toml` and returns

     - a list of setup requirements from [build-system] requires
     - sub-list of these requirements that should be installed with conda, from [tool.my_conda] conda_packages
    """
    if os.path.exists("pyproject.toml"):
        import toml
        nox_logger.debug("\nA `pyproject.toml` file exists. Loading it.")
        pyproject = toml.load("pyproject.toml")
        requires = pyproject['build-system']['requires']
        conda_pkgs = pyproject['tool']['conda']['conda_packages']
        return requires, conda_pkgs
    else:
        raise FileNotFoundError("No `pyproject.toml` file exists. No dependency will be installed ...")


SetupCfg = namedtuple('SetupCfg', ('setup_requires', 'install_requires', 'tests_requires'))


def read_setuptools_cfg():
    """
    Reads the `setup.cfg` file and extracts the various requirements lists

    """
    # see https://stackoverflow.com/a/30679041/7262247
    from setuptools import Distribution
    dist = Distribution()
    dist.parse_config_files()

    # standard requirements
    options_dct = dist.get_option_dict('options')
    setup_reqs = options_dct['setup_requires'][1].strip().splitlines()
    install_reqs = options_dct['install_requires'][1].strip().splitlines()
    tests_reqs = options_dct['tests_require'][1].strip().splitlines()

    return SetupCfg(setup_requires=setup_reqs,
                    install_requires=install_reqs,
                    tests_requires=tests_reqs)


def session_install_any(phase_name: str,
                        session: nox.sessions.Session,
                        pkgs: Sequence[str],
                        use_conda_for: Sequence[str] = (),
                        versions_dct: Dict[str, str] = None,
                        logfile=None
                        ):
    """Install the `pkgs` provided with `session.install(*pkgs)`, except for those present in `use_conda_for`"""

    nox_logger.debug("\nAbout to install *%s* requirements: %s.\n "
                     "Conda pkgs are %s" % (phase_name, pkgs, use_conda_for))

    # use the provided versions dictionary to update the versions
    if versions_dct is None:
        versions_dct = dict()
    pkgs = [pkg + versions_dct.get(pkg, "") for pkg in pkgs if versions_dct.get(pkg, "") != DONT_INSTALL]

    # install on conda... if the session uses conda backend
    if not isinstance(session.virtualenv, nox.virtualenv.CondaEnv):
        conda_pkgs = []
    else:
        conda_pkgs = [pkg_req for pkg_req in pkgs if any(get_req_pkg_name(pkg_req) == c for c in use_conda_for)]
        if len(conda_pkgs) > 0:
            nox_logger.info("[%s] Installing requirements with conda: %s" % (phase_name, conda_pkgs))
            session_conda_install(session, *conda_pkgs, logfile=logfile)

    pip_pkgs = [pkg_req for pkg_req in pkgs if pkg_req not in conda_pkgs]
    # safety: make sure that nothing went modified or forgotten
    assert set(conda_pkgs).union(set(pip_pkgs)) == set(pkgs)
    if len(pip_pkgs) > 0:
        nox_logger.info("[%s] Installing requirements with pip: %s" % (phase_name, pip_pkgs))
        session_install(session, *pip_pkgs, logfile=logfile)


def session_conda_install(session, *conda_pkgs, logfile=None):
    """
    Same as session.conda_install() but uses the log if present explicitly or in a FileHandler.

    :param session:
    :param pip_pkgs:
    :param logfile:
    :return:
    """
    if logfile is not None:
        with open(logfile, "a") as out:
            session.conda_install(*conda_pkgs, silent=False, stdout=out, stderr=out)
    else:
        # get the log file handler if needed
        logfile_stream = get_log_file_stream()

        if logfile_stream is not None:
            session.conda_install(*conda_pkgs, silent=False, stdout=logfile_stream, stderr=logfile_stream)
        else:
            session.conda_install(*conda_pkgs)


def session_install(session, *pip_pkgs, logfile=None):
    """
    Same as session.install() but uses the log if present explicitly or in a FileHandler.

    :param session:
    :param pip_pkgs:
    :param logfile:
    :return:
    """
    if logfile is not None:
        with open(logfile, "a") as out:
            session.install(*pip_pkgs, silent=False, stdout=out, stderr=out)
    else:
        # get the log file handler if needed
        logfile_stream = get_log_file_stream()

        if logfile_stream is not None:
            session.install(*pip_pkgs, silent=False, stdout=logfile_stream, stderr=logfile_stream)
        else:
            session.install(*pip_pkgs)


def get_req_pkg_name(r):
    return r.replace('<', '=').replace('>', '=').replace(';', '=').split("=")[0]


def get_session_id(session):
    return Path(session.bin).name


def log_to_file(file_path):
    for h in list(nox_logger.handlers):
        if isinstance(h, logging.FileHandler):
            h.close()
            nox_logger.removeHandler(h)
    fh = logging.FileHandler(str(file_path), mode='w')
    nox_logger.addHandler(fh)
    return fh


def get_log_file_stream():
    for h in list(nox_logger.handlers):
        if isinstance(h, logging.FileHandler):
            return h.stream
    return None


def remove_file_logger():
    for h in list(nox_logger.handlers):
        if isinstance(h, logging.FileHandler):
            h.close()
            nox_logger.removeHandler(h)


def session_run(
        session,
        command,
        logfile=None,
        **kwargs
):
    """Run a nox session and capture in log file"""

    if isinstance(command, str):
        command = (command).split(' ')

    if logfile is not None:
        # logfile explicitly provided, use it
        with open(logfile, "a") as out:
            session.run(*command, stdout=out, stderr=out, **kwargs)
    else:
        # is there a current log file handler open ? If so use it.
        stream = get_log_file_stream()
        if stream is not None:
            session.run(*command, stdout=stream, stderr=stream, **kwargs)
        else:
            session.run(*command, **kwargs)


def with_logfile(logs_dir: Path,
                 logfile_arg: str = "logfile",
                 logfile_handler_arg: str = "logfilehandler"
                 ):
    """ A decorator to inject a logfile"""

    def _decorator(f):
        # check the signature of f
        foo_sig = signature(f)
        needs_logfile_injection = logfile_arg in foo_sig.parameters
        needs_logfilehandler_injection = logfile_handler_arg in foo_sig.parameters

        # modify the exposed signature if needed
        new_sig = None
        if needs_logfile_injection:
            new_sig = remove_signature_parameters(foo_sig, logfile_arg)
        if needs_logfilehandler_injection:
            new_sig = remove_signature_parameters(foo_sig, logfile_handler_arg)

        @wraps(f, new_sig=new_sig)
        def _f_wrapper(**kwargs):
            # find the session arg
            session = kwargs['session']

            # add file handler to logger
            logfile = logs_dir / ("%s.log" % get_session_id(session))
            error_logfile = logfile.with_name("ERROR_%s" % logfile.name)
            success_logfile = logfile.with_name("SUCCESS_%s" % logfile.name)
            # delete old files if present
            for _f in (logfile, error_logfile, success_logfile):
                if _f.exists():
                    _f.unlink()

            # add a FileHandler to the logger
            logfile_handler = log_to_file(logfile)

            # inject the log file / log file handler in the args:
            if needs_logfile_injection:
                kwargs[logfile_arg] = logfile
            if needs_logfilehandler_injection:
                kwargs[logfile_handler_arg] = logfile_handler

            # finally execute the session
            try:
                res = f(**kwargs)
            except Exception as e:
                # close and detach the file logger and rename as ERROR_....log
                remove_file_logger()
                logfile.rename(error_logfile)
                raise e
            else:
                # close and detach the file logger and rename as SUCCESS_....log
                remove_file_logger()
                logfile.rename(success_logfile)
                return res

        return _f_wrapper

    return _decorator


def inject_envs_params(envs):
    param_names = None
    for env_py, env_params in envs.items():
        if param_names is None:
            param_names = set(env_params.keys())
        else:
            if param_names != set(env_params.keys()):
                raise ValueError("Environment %r parameters %r does not match parameters in the first environment: %r"
                                 % (env_py, param_names, set(env_params.keys())))

    def _decorator(f):
        # check the signature of f
        foo_sig = signature(f)
        missing = param_names - set(foo_sig.parameters)
        if len(missing) > 0:
            raise ValueError("Session function %r does not contain environment parameter(s) %r" % (f.__name__, missing))

        # modify the exposed signature if needed
        new_sig = None
        if len(param_names) > 0:
            new_sig = remove_signature_parameters(foo_sig, *param_names)

        @wraps(f, new_sig=new_sig)
        def _f_wrapper(**kwargs):
            # find the session arg
            session = kwargs['session']

            # get the versions to use for this environment
            try:
                params_dct = envs[session.python]
            except KeyError:
                nox_logger.warning(
                    "Skipping configuration, this is not supported in python version %r" % session.python)
                return

            # inject the parameters in the args:
            kwargs.update(params_dct)

            # finally execute the session
            return f(**kwargs)

        return _f_wrapper

    return _decorator


def power_session(
        func=None,
        envs=None,
        python=None,
        py=None,
        reuse_venv=None,
        name=None,
        venv_backend=None,
        venv_params=None,
        logsdir=None,
        **kwargs
):
    """A nox.session on steroids"""
    if func is not None:
        return nox.session(func)
    else:
        if envs is not None:
            if py is not None or python is not None:
                raise ValueError("Only one of `envs` and `py/python` should be provided")
            python = list(envs.keys())
        nox_deco = nox.session(python=python, py=py, reuse_venv=reuse_venv, name=name, venv_backend=venv_backend,
                               venv_params=venv_params, **kwargs)

        def combined_decorator(f):
            # apply all decorators in turn
            # @with_logfile
            if logsdir is not None:
                f = with_logfile(logs_dir=logsdir)(f)

            # @inject_envs_params
            if envs is not None:
                f = inject_envs_params(envs)(f)

            # finally @nox.session
            return nox_deco(f)

        return combined_decorator


def install_reqs(
        session,
        # pre wired phases
        setup=False,
        install=False,
        tests=False,
        # custom phase
        phase=None,
        phase_reqs=None,
        versions_dct=None
):
    """For debugging/development: install this project's requirements in the currently active environment """

    # Read requirements from pyproject.toml
    toml_setup_reqs, toml_use_conda_for = read_pyproject_toml()
    if setup:
        session_install_any("pyproject.toml#build-system", session, toml_setup_reqs,
                            use_conda_for=toml_use_conda_for, versions_dct=versions_dct)

    # Read test requirements from setup.cfg
    setup_cfg = read_setuptools_cfg()
    if setup:
        session_install_any("setup.cfg#setup_requires", session, setup_cfg.setup_requires,
                            use_conda_for=toml_use_conda_for, versions_dct=versions_dct)
    if install:
        session_install_any("setup.cfg#install_requires", session, setup_cfg.install_requires,
                            use_conda_for=toml_use_conda_for, versions_dct=versions_dct)
    if tests:
        session_install_any("setup.cfg#tests_requires", session, setup_cfg.tests_requires,
                            use_conda_for=toml_use_conda_for, versions_dct=versions_dct)

    if phase is not None:
        session_install_any(phase, session, phase_reqs, use_conda_for=toml_use_conda_for, versions_dct=versions_dct)


def rm_file(folder: Union[str, Path]
            ):
    """Since on windows Path.unlink throws permission error sometimes, os.remove is preferred."""
    if isinstance(folder, str):
        folder = Path(folder)

    if folder.exists():
        os.remove(str(folder))
        # Folders.site.unlink()  --> possible PermissionError


def rm_folder(folder: Union[str, Path]
              ):
    """Since on windows Path.unlink throws permission error sometimes, shutil is preferred."""
    if isinstance(folder, str):
        folder = Path(folder)

    if folder.exists():
        shutil.rmtree(str(folder))
        # Folders.site.unlink()  --> possible PermissionError
