import logging

import nox  # noqa
from pathlib import Path  # noqa
import sys

# add parent folder to python path so that we can import noxfile_utils.py
sys.path.append(str(Path(__file__).parent / "ci_tools"))
from noxfile_utils import PY27, PY37, PY36, PY35, PY38, session_run, power_session, install_reqs, rm_folder, \
    rm_file  # noqa

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


@power_session(envs=ENVS, logsdir=Folders.runlogs)
def tests(session, coverage, pkg_specs):
    """Run the test suite, including test reports generation and coverage reports. """

    # As soon as this runs, we delete the target site and coverage files to avoid reporting wrong coverage/etc.
    rm_folder(Folders.site)
    rm_folder(Folders.reports_root)
    # delete the coverage.xml and .coverage files
    rm_file(Folders.root / ".coverage")
    rm_file(Folders.root / "coverage.xml")

    # uncomment and edit if you wish to uninstall something without deleting the whole env
    # session_run(session, "pip uninstall pytest-asyncio --yes")

    # install all requirements
    install_reqs(session, setup=True, install=True, tests=True, versions_dct=pkg_specs)

    # install self so that it is recognized by pytest
    session_run(session, "pip install -e . --no-deps")

    # finally run all tests
    if not coverage:
        # simple: pytest only
        session_run(session, "python -m pytest -v makefun/tests/")
    else:
        # coverage + junit html reports + badge generation
        install_reqs(session, phase="coverage", phase_reqs=["coverage", "pytest-html", "requests", "xunitparser"],
                     versions_dct=pkg_specs)

        # --coverage + junit html reports
        session_run(session, "coverage run --source makefun "
                             "-m pytest --junitxml={dst}/junit.xml --html={dst}/report.html -v makefun/tests/"
                             "".format(dst=Folders.test_reports))
        session_run(session, "coverage html -d {dst}".format(dst=Folders.coverage_reports))

        # --generates the badge for the test results and fail build if less than x% tests pass
        nox_logger.info("Generating badge for tests coverage")
        session_run(session, "python ci_tools/generate-junit-badge.py 100 %s" % Folders.test_reports)

        # TODO instead of pushing to codecov we could generate the cov reports ourselves
        # session.run(*"coverage run".split(' '))     # this executes pytest + reporting
        # session.run(*"coverage report".split(' '))  # this shows in terminal + fails under XX%, same as --cov-report term --cov-fail-under=70  # noqa
        # session.run(*"coverage html".split(' '))    # same than --cov-report html:<dir>
        # session.run(*"coverage xml".split(' '))     # same than --cov-report xml:<file>


@nox.session(python=[PY37])
def docs(session):
    """Generates the doc and serves it on a local http server. Pass '-- build' to build statically instead."""

    install_reqs(session, phase="docs", phase_reqs=["mkdocs-material", "mkdocs", "pymdown-extensions", "pygments"])

    if session.posargs:
        # use posargs instead of "serve"
        session_run(session, "mkdocs -f .\\docs\\mkdocs.yml %s" % " ".join(session.posargs))
    else:
        session_run(session, "mkdocs serve -f .\\docs\\mkdocs.yml")


@nox.session(python=[PY37])
def publish(session):
    """Deploy the docs on github pages + pushes the coverage. Note: this rebuilds the docs"""

    install_reqs(session, phase="mkdocs", phase_reqs=["mkdocs-material", "mkdocs", "pymdown-extensions", "pygments"])

    # possibly rebuild the docs in a static way (mkdocs serve does not build locally)
    session_run(session, "mkdocs build -f .\\docs\\mkdocs.yml")

    # check that the doc has been generated with coverage
    if not Folders.site_reports.exists():
        raise ValueError("Test reports have not been built yet. Please run 'nox -s tests-3.7' first")

    # publish the docs
    session_run(session, "mkdocs gh-deploy -f .\\docs\\mkdocs.yml")

    # publish the coverage
    # keyring set https://app.codecov.io/gh/smarie/python-makefun token
    import keyring
    codecov_token = keyring.get_password("https://app.codecov.io/gh/smarie/python-makefun", "token")
    install_reqs(session, phase="codecov", phase_reqs=["codecov"])
    # note: do not use --root nor -f ! otherwise "There was an error processing coverage reports"
    session_run(session, 'codecov -t %s' % codecov_token)


@nox.session(python=[PY37])
def release(session):
    """Create a release on github corresponding to the latest tag"""

    # TODO get current tag using setuptools_scm and make sure this is not a dirty/dev one
    from setuptools_scm import get_version
    from setuptools_scm.version import guess_next_dev_version
    version = []

    def my_scheme(version_):
        version.append(version_)
        return guess_next_dev_version(version_)
    current_tag = get_version(".", version_scheme=my_scheme)

    # create the package
    install_reqs(session, phase="setup.py#dist", phase_reqs=["setuptools_scm"])
    rm_folder(Folders.dist)
    session_run(session, "python setup.py sdist bdist_wheel")

    if version[0].dirty or not version[0].exact:
        raise ValueError("You need to execute this action on a clean tag version with no local changes.")

    # publish the package on PyPi
    # keyring set https://upload.pypi.org/legacy/ your-username
    # keyring set https://test.pypi.org/legacy/ your-username
    install_reqs(session, phase="PyPi", phase_reqs=["twine"])
    session_run(session, "twine upload dist/* -u smarie")  # -r testpypi

    # create the github release
    install_reqs(session, phase="release", phase_reqs=["click", "PyGithub"])

    # keyring set https://docs.github.com/en/rest token
    import keyring  # noqa
    gh_token = keyring.get_password("https://docs.github.com/en/rest", "token")
    session_run(session, "python ci_tools/github_release.py -s {gh_token} "
                         "--repo-slug smarie/python-makefun -cf ./docs/changelog.md "
                         "-d https://smarie.github.io/python-makefun/changelog/ {tag}".format(gh_token=gh_token,
                                                                                              tag=current_tag))


# if __name__ == '__main__':
#     # allow this file to be executable for easy debugging in any IDE
#     nox.run(globals())
