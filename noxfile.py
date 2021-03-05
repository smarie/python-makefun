import logging
import os
from collections import namedtuple
from inspect import signature

from makefun import wraps, remove_signature_parameters
from typing import Sequence, Dict
from pathlib import Path

import nox


PY27 = "2.7"
PY35 = "3.5"
PY36 = "3.6"
PY37 = "3.7"
PY38 = "3.8"
ALL_PY_VERSIONS = [PY38, PY37, PY36, PY35, PY27]

DONT_INSTALL = "dont_install"

ENVS = {
    PY27: {"pip": ">10"},  # "pytest-html": "1.9.0",
    PY35: {"pip": ">10"},
    PY36: {"pip": ">19"},
    PY37: {"pip": ">19"},
    PY38: {"pip": ">19"},
}


def get_versions_for(python_version):
    """Return a dictionary of version constraints and a boolean flag indicating if a session should be skipped"""
    try:
        env_spec = dict(ENVS[python_version])
    except KeyError:
        # skip
        nox_logger.warning("Environment %r is not defined, skipping..." % python_version)
        return None, True
    else:
        return env_spec, False


# set the default activated sessions, minimal for CI
nox.options.sessions = ["tests"]  # , "docs", "gh_pages"
nox.options.reuse_existing_virtualenvs = True  # this can be done using -r
nox.options.default_venv_backend = "conda"
# os.environ["NO_COLOR"] = "True"  # nox.options.nocolor = True does not work
# nox.options.verbose = True

nox_logger = logging.getLogger("nox")
nox_logger.setLevel(logging.INFO)
runlogs_dir = Path(nox.options.envdir or ".nox") / "_runlogs"
runlogs_dir.mkdir(parents=True, exist_ok=True)


def with_logfile(logs_dir, logfile_handler_arg="logfile_handler"):
    """ A decorator to inject a logfile"""
    def _decorator(f):
        foo_sig = signature(f)
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

            logfile_handler = log_to_file(logfile)

            # inject the log file in the args
            kwargs[logfile_handler_arg] = logfile_handler
            try:
                res = f(**kwargs)
            except Exception as e:
                remove_file_logger()
                logfile.rename(error_logfile)
                raise e
            else:
                remove_file_logger()
                logfile.rename(success_logfile)
                return res

        return _f_wrapper

    return _decorator


@nox.session(python=False, venv_backend="none")
def install_reqs(session, setup=True, install=True, tests=False, versions_dct=None, logfile_handler=None):
    """For debugging/development: install this project's requirements in the currently active environment """

    # Read requirements from pyproject.toml
    toml_setup_reqs, toml_use_conda_for = read_pyproject_toml()
    if setup:
        install_on_pip_or_conda("pyproject.toml#build-system", session, toml_setup_reqs, use_conda_for=toml_use_conda_for,
                                versions_dct=versions_dct, logfile_handler=logfile_handler)

    # Read test requirements from setup.cfg
    setup_cfg = read_setuptools_cfg()
    if setup:
        install_on_pip_or_conda("setup.cfg#setup_requires", session, setup_cfg.setup_requires, use_conda_for=toml_use_conda_for,
                                versions_dct=versions_dct, logfile_handler=logfile_handler)
    if install:
        install_on_pip_or_conda("setup.cfg#install_requires", session, setup_cfg.install_requires, use_conda_for=toml_use_conda_for,
                                versions_dct=versions_dct, logfile_handler=logfile_handler)
    if tests:
        install_on_pip_or_conda("setup.cfg#tests_requires", session, setup_cfg.tests_requires, use_conda_for=toml_use_conda_for,
                                versions_dct=versions_dct, logfile_handler=logfile_handler)


@nox.session(python=ALL_PY_VERSIONS)
@with_logfile(logs_dir=runlogs_dir)
def tests(session, logfile_handler):
    """Run the test suite, including test reports generation and coverage reports. """

    # get the versions to use for this environment
    versions_dct, skip = get_versions_for(session.python)
    if skip:
        nox_logger.warning("Skipping configuration, this is not supported in python version %r" % session.python)
        return

    # session.run(*"pip uninstall pytest-asyncio --yes".split(" "))

    # install all requirements
    install_reqs(session, tests=True, versions_dct=versions_dct, logfile_handler=logfile_handler)

    # install self so that it is recognized by pytest
    run(session, "pip install -e . --no-deps", logfilehandler=logfile_handler)

    # finally run all tests with coverage
    run(session, "python -m pytest -v makefun/tests/", logfilehandler=logfile_handler)


@nox.session(python=[PY37])
def docserve(session):
    """Generates the documentation and serves it on a local http server"""

    session.install(*["mkdocs-material", "mkdocs", "pymdown-extensions", "pygments"])
    session.run(*"mkdocs serve -f .\docs\mkdocs.yml".split(' '))


@nox.session(name="deploy-docs", python=[PY37])
def deploy_docs(session):
    """Deploy the docs on github pages. Note: this rebuilds the docs"""

    session.install(*["mkdocs-material", "mkdocs", "pymdown-extensions", "pygments"])
    # session.run(*"coverage run".split(' '))     # this executes pytest + reporting
    # session.run(*"coverage report".split(' '))  # this shows in terminal + fails under XX%, same than --cov-report term --cov-fail-under=70
    # session.run(*"coverage html".split(' '))    # same than --cov-report html:<dir>
    # session.run(*"coverage xml".split(' '))     # same than --cov-report xml:<file>

    session.run(*"coverage run --source makefun -m pytest "
                 "--junitxml=reports/junit/junit.xml --html=reports/junit/report.html "
                 "-v makefun/tests/".split(' '))

    session.run(*"mkdocs gh-deploy -f .\docs\mkdocs.yml".split(' '))


@nox.session(name="deploy-pypi", python=[PY37], venv_backend="venv", reuse_venv=True)
def deploy_pypi(session):
    """Deploy the current wheel on PyPi"""
    "sdist bdist_wheel"


@nox.session(name="deploy-release", python=[PY37], venv_backend="venv", reuse_venv=True)
def gh_release(session):
    """Create a release on github corresponding to the latest tag"""

    # TODO get current tag using setuptools_scm and make sure this is not a dirty/dev one
    current_tag = None
    session.run("python ci_tools/github_release.py "
                # "-s {GITHUB_TOKEN}"
                "--repo-slug smarie/python-makefun "
                "-cf ./docs/changelog.md "
                "-d https://smarie.github.io/python-makefun/changelog/ {TAG}".format(tag=current_tag))


@nox.session(python=[PY37], venv_backend="venv", reuse_venv=True)
def deploy(session):
    """An alias for deploy-docs deploy-pypi gh-release"""

    print("todo")

# if __name__ == '__main__':
#     # allow this file to be executable for easy debugging in any IDE
#     nox.run(globals())


# ------------- our nox helpers -----------

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


def install_on_pip_or_conda(phase_name: str,
                            session: nox.sessions.Session,
                            pkgs: Sequence[str],
                            use_conda_for: Sequence[str] = (),
                            versions_dct: Dict[str, str] = None,
                            logfile=None,
                            logfile_handler=None
                            ):
    """Install the `pkgs` provided with `session.install(*pkgs)`, except for those present in `use_conda_for`"""

    nox_logger.debug("\nAbout to install *%s* requirements: %s.\n "
                     "Conda pkgs are %s" % (phase_name, pkgs, use_conda_for))

    # use the provided versions dictionary to update the versions
    if versions_dct is None:
        versions_dct = dict()
    pkgs = [pkg + versions_dct.get(pkg, "") for pkg in pkgs if versions_dct.get(pkg, "") != DONT_INSTALL]

    conda_pkgs = [pkg_req for pkg_req in pkgs if any(get_req_pkg_name(pkg_req) == c for c in use_conda_for)]
    if len(conda_pkgs) > 0:
        nox_logger.info("[%s] Installing requirements with conda: %s" % (phase_name, conda_pkgs))
        if logfile is not None:
            assert logfile_handler is None, "both can not be non-none"
            with open(logfile, "a") as out:
                session.conda_install(*conda_pkgs, silent=False, stdout=out, stderr=out)
        elif logfile_handler is not None:
            session.conda_install(*conda_pkgs, silent=False, stdout=logfile_handler.stream, stderr=logfile_handler.stream)
        else:
            session.conda_install(*conda_pkgs)

    pip_pkgs = [pkg_req for pkg_req in pkgs if pkg_req not in conda_pkgs]
    # safety: make sure that nothing went modified or forgotten
    assert set(conda_pkgs).union(set(pip_pkgs)) == set(pkgs)
    if len(pip_pkgs) > 0:
        nox_logger.info("[%s] Installing requirements with pip: %s" % (phase_name, pip_pkgs))
        if logfile is not None:
            assert logfile_handler is None, "both can not be non-none"
            with open(logfile, "a") as out:
                session.install(*pip_pkgs, silent=False, stdout=out, stderr=out)
        elif logfile_handler is not None:
            session.install(*pip_pkgs, silent=False, stdout=logfile_handler.stream, stderr=logfile_handler.stream)
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


def remove_file_logger():
    for h in list(nox_logger.handlers):
        if isinstance(h, logging.FileHandler):
            h.close()
            nox_logger.removeHandler(h)


def run(session, command, logfile=None, logfilehandler=None, **kwargs):
    """Run a nox session and capture in log file"""
    if logfile is not None:
        assert logfilehandler is None, "only one should be non-none"
        with open(logfile, "a") as out:
            session.run(*(command).split(' '), stdout=out, stderr=out, **kwargs)
    elif logfilehandler is not None:
        session.run(*(command).split(' '), stdout=logfilehandler.stream, stderr=logfilehandler.stream, **kwargs)
    else:
        session.run(*(command).split(' '), **kwargs)
