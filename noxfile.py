import os
from typing import List, Optional

import nox

CI = bool(os.getenv("CI"))
PYTHON = ["3.10", "3.11"] if not CI else None
SESSIONS = "ruff", "mypy", "black", "lockfile", "pytest"

nox.options.sessions = SESSIONS
os.environ.update({"PDM_IGNORE_SAVED_PYTHON": "1"})


def pdm_sync(
    session: nox.Session,
    *,
    self: bool = False,
    default: bool = False,
    editable: bool = True,
    groups: Optional[List[str]] = None,
) -> None:
    """Install dependencies using PDM.

    Args:
        session: The nox session.
        self: Whether to install the package itself.
        default: Whether to install the default dependencies.
        editable: Whether to install packages in editable mode.
        groups: The dependency groups to install.
    """
    cmd = ["pdm", "sync"]
    if not self:
        cmd.append("--no-self")
    if not default:
        cmd.append("--no-default")
    if not editable:
        cmd.append("--no-editable")
    if groups:
        for group in groups:
            cmd.append("-G")
            cmd.append(group)

    session.run(*cmd, external=True)


def pdm_check_lockfile(session: nox.Session) -> None:
    """Check if the lockfile is up-to-date."""
    session.run("pdm", "lock", "--check", external=True)


@nox.session(python=PYTHON)
def ruff(session: nox.Session) -> None:
    """Code Style linting using ruff."""
    pdm_sync(session, groups=["lint"])
    session.run("ruff", "src", "tests")


@nox.session(python=PYTHON)
def black(session: nox.Session) -> None:
    """Check if style adheres to black."""
    pdm_sync(session, groups=["lint"])
    session.run("black", "--check", "src", "tests")


@nox.session(python=PYTHON)
def mypy(session: nox.Session) -> None:
    """Static type checking using mypy."""
    pdm_sync(session, default=True, groups=["typecheck", "type_stubs"])
    session.run("mypy", "src")


@nox.session(python=PYTHON)
def lockfile(session: nox.Session) -> None:
    """Check if the lockfile is up-to-date."""
    pdm_check_lockfile(session)


@nox.session(python=PYTHON)
def pytest(session: nox.Session) -> None:
    """Run fast pytest tests if not running in CI, otherwise run all."""
    if not CI:
        pytest_fast(session)
    else:
        pytest_full(session)


@nox.session(python=PYTHON)
def pytest_fast(session: nox.Session) -> None:
    """Run pytest tests that are fast to execute.

    This session excludes e2e and integration tests since they are slow
    to execute and might require external dependencies.
    It is intended to be run multiple times during development.
    """
    pdm_sync(session, self=True, default=True, groups=["test", "cli"])
    session.warn(
        "Skipping e2e tests for faster execution. "
        "To include them, run `nox -s pytest_full`."
    )
    session.run(
        "pytest", "tests", "-m", "not e2e and not integration", *session.posargs
    )


@nox.session(python=PYTHON)
def pytest_full(session: nox.Session) -> None:
    """Run all pytest tests.

    This session includes all tests and is intended to be
    run in CI or before a commit.
    """
    pdm_sync(session, self=True, default=True, groups=["test", "cli"])
    args = session.posargs if not CI else ["--cov"]
    session.run("pytest", "tests", *args)


@nox.session(python=PYTHON)
def safety(session: nox.Session) -> None:
    """Scan dependencies for known security vulnerabilities using safety."""
    session.install("safety")
    session.run("pdm", "export", "-o", "requirements.txt", external=True)
    session.run("safety", "check", "--file=requirements.txt", "--full-report")


@nox.session(python=PYTHON)
def codecov(session: nox.Session) -> None:
    """Upload codecov coverage data."""
    session.install("coverage", "codecov")
    session.run("coverage", "xml", "--fail-under=0")
    session.run("codecov", "-f", "coverage.xml")
