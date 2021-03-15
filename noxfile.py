import logging

import nox  # noqa
from pathlib import Path  # noqa
import sys

# add parent folder to python path so that we can import noxfile_utils.py
# note that you need to "pip install makefun" for this file to work.
sys.path.append(str(Path(__file__).parent / "ci_tools"))
from nox_utils import PY27, PY37, PY36, PY35, PY38, power_session, rm_folder, rm_file, PowerSession  # noqa

ALL_PY_VERSIONS = [PY38, PY37, PY36, PY35, PY27]

ENVS = {
    PY27: {"coverage": False, "pkg_specs": {"pip": ">10"}},
    PY35: {"coverage": False, "pkg_specs": {"pip": ">10"}},
    PY36: {"coverage": False, "pkg_specs": {"pip": ">19"}},
    PY38: {"coverage": False, "pkg_specs": {"pip": ">19"}},
    # IMPORTANT: this should be last so that the folder docs/reports is not deleted afterwards
    PY37: {"coverage": True, "pkg_specs": {"pip": ">19"}},  # , "pytest-html": "1.9.0"
}


# set the default activated sessions, minimal for CI
nox.options.sessions = ["tests"]  # , "docs", "gh_pages"
nox.options.reuse_existing_virtualenvs = True  # this can be done using -r
# if platform.system() == "Windows":  >> always use this for better control
nox.options.default_venv_backend = "conda"
# os.environ["NO_COLOR"] = "True"  # nox.options.nocolor = True does not work
# nox.options.verbose = True

nox_logger = logging.getLogger("nox")
nox_logger.setLevel(logging.INFO)


class Folders:
    root = Path(__file__).parent
    runlogs = root / Path(nox.options.envdir or ".nox") / "_runlogs"
    runlogs.mkdir(parents=True, exist_ok=True)
    dist = root / "dist"
    site = root / "site"
    site_reports = site / "reports"
    reports_root = root / "docs" / "reports"
    test_reports = reports_root / "junit"
    coverage_reports = reports_root / "coverage"
    coverage_xml = coverage_reports / "coverage.xml"


@power_session(envs=ENVS, logsdir=Folders.runlogs)
def tests(session: PowerSession, coverage, pkg_specs):
    """Run the test suite, including test reports generation and coverage reports. """

    # As soon as this runs, we delete the target site and coverage files to avoid reporting wrong coverage/etc.
    rm_folder(Folders.site)
    rm_folder(Folders.reports_root)
    # delete the .coverage files if any (they are not supposed to be any, but just in case)
    rm_file(Folders.root / ".coverage")
    rm_file(Folders.root / "coverage.xml")

    # uncomment and edit if you wish to uninstall something without deleting the whole env
    # session_run(session, "pip uninstall pytest-asyncio --yes")

    # install all requirements
    session.install_reqs(setup=True, install=True, tests=True, versions_dct=pkg_specs)

    # install self so that it is recognized by pytest
    session.run2("pip install -e . --no-deps")

    # check that it can be imported even from a different folder
    session.run2(['python', '-c', '"import os; os.chdir(\'./docs/\'); import makefun"'])

    # finally run all tests
    if not coverage:
        # simple: pytest only
        session.run2("python -m pytest -v makefun/tests/")
    else:
        # coverage + junit html reports + badge generation
        session.install_reqs(phase="coverage", phase_reqs=["coverage", "pytest-html", "requests", "xunitparser"],
                             versions_dct=pkg_specs)

        # --coverage + junit html reports
        session.run2("coverage run --source makefun "
                             "-m pytest --junitxml={dst}/junit.xml --html={dst}/report.html -v makefun/tests/"
                             "".format(dst=Folders.test_reports))
        session.run2("coverage xml -o {covxml}".format(covxml=Folders.coverage_xml))
        session.run2("coverage html -d {dst}".format(dst=Folders.coverage_reports))
        # delete this intermediate file, it is not needed anymore
        rm_file(Folders.root / ".coverage")

        # --generates the badge for the test results and fail build if less than x% tests pass
        nox_logger.info("Generating badge for tests coverage")
        session.run2("python ci_tools/generate-junit-badge.py 100 %s" % Folders.test_reports)

        # TODO instead of pushing to codecov we could generate the cov reports ourselves
        # session.run2("coverage run")     # this executes pytest + reporting
        # session.run2("coverage report")  # this shows in terminal + fails under XX%, same as --cov-report term --cov-fail-under=70  # noqa
        # session.run2("coverage html")    # same than --cov-report html:<dir>
        # session.run2("coverage xml")     # same than --cov-report xml:<file>


@power_session(python=[PY37])
def docs(session: PowerSession):
    """Generates the doc and serves it on a local http server. Pass '-- build' to build statically instead."""

    session.install_reqs(phase="docs", phase_reqs=["mkdocs-material", "mkdocs", "pymdown-extensions", "pygments"])

    if session.posargs:
        # use posargs instead of "serve"
        session.run2("mkdocs -f ./docs/mkdocs.yml %s" % " ".join(session.posargs))
    else:
        session.run2("mkdocs serve -f ./docs/mkdocs.yml")


@power_session(python=[PY37])
def publish(session: PowerSession):
    """Deploy the docs+reports on github pages. Note: this rebuilds the docs"""

    session.install_reqs(phase="mkdocs", phase_reqs=["mkdocs-material", "mkdocs", "pymdown-extensions", "pygments"])

    # possibly rebuild the docs in a static way (mkdocs serve does not build locally)
    session.run2("mkdocs build -f ./docs/mkdocs.yml")

    # check that the doc has been generated with coverage
    if not Folders.site_reports.exists():
        raise ValueError("Test reports have not been built yet. Please run 'nox -s tests-3.7' first")

    # publish the docs
    session.run2("mkdocs gh-deploy -f ./docs/mkdocs.yml")

    # publish the coverage - now in github actions only
    # session.install_reqs(phase="codecov", phase_reqs=["codecov", "keyring"])
    # # keyring set https://app.codecov.io/gh/smarie/python-makefun token
    # import keyring  # (note that this import is not from the session env but the main nox env)
    # codecov_token = keyring.get_password("https://app.codecov.io/gh/smarie/python-makefun", "token")
    # # note: do not use --root nor -f ! otherwise "There was an error processing coverage reports"
    # session.run2('codecov -t %s -f %s' % (codecov_token, Folders.coverage_xml))


@power_session(python=[PY37])
def release(session: PowerSession):
    """Create a release on github corresponding to the latest tag"""

    # Get current tag using setuptools_scm and make sure this is not a dirty/dev one
    from setuptools_scm import get_version  # (note that this import is not from the session env but the main nox env)
    from setuptools_scm.version import guess_next_dev_version
    version = []

    def my_scheme(version_):
        version.append(version_)
        return guess_next_dev_version(version_)
    current_tag = get_version(".", version_scheme=my_scheme)

    # create the package
    session.install_reqs(phase="setup.py#dist", phase_reqs=["setuptools_scm"])
    rm_folder(Folders.dist)
    session.run2("python setup.py sdist bdist_wheel")

    if version[0].dirty or not version[0].exact:
        raise ValueError("You need to execute this action on a clean tag version with no local changes.")

    # Did we receive a token through positional arguments ? (nox -s release -- <token>)
    if len(session.posargs) == 1:
        # Run from within github actions - no need to publish on pypi
        gh_token = session.posargs[0]
        publish_on_pypi = False

    elif len(session.posargs) == 0:
        # Run from local commandline - assume we want to manually publish on PyPi
        publish_on_pypi = True

        # keyring set https://docs.github.com/en/rest token
        import keyring  # (note that this import is not from the session env but the main nox env)
        gh_token = keyring.get_password("https://docs.github.com/en/rest", "token")
        assert len(gh_token) > 0

    else:
        raise ValueError("Only a single positional arg is allowed for now")

    # publish the package on PyPi
    if publish_on_pypi:
        # keyring set https://upload.pypi.org/legacy/ your-username
        # keyring set https://test.pypi.org/legacy/ your-username
        session.install_reqs(phase="PyPi", phase_reqs=["twine"])
        session.run2("twine upload dist/* -u smarie")  # -r testpypi

    # create the github release
    session.install_reqs(phase="release", phase_reqs=["click", "PyGithub"])
    session.run2("python ci_tools/github_release.py -s {gh_token} "
                         "--repo-slug smarie/python-makefun -cf ./docs/changelog.md "
                         "-d https://smarie.github.io/python-makefun/changelog/ {tag}".format(gh_token=gh_token,
                                                                                              tag=current_tag))


# if __name__ == '__main__':
#     # allow this file to be executable for easy debugging in any IDE
#     nox.run(globals())
