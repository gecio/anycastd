import os
import shutil
from typing import List, Optional

import nox

CI = bool(os.getenv("CI"))
PYTHON = ["3.11", "3.12"] if not CI else None
SESSIONS = "ruff", "mypy", "lockfile", "pytest"
EXTERNAL_DEPENDENCY_MARKERS = ["frrouting_daemon_required"]

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
    """Lint code and ensure formatting using ruff."""
    pdm_sync(session, groups=["lint"])
    session.run("ruff", "check", "src", "tests")
    session.run("ruff", "format", "--check", "src", "tests")


@nox.session(python=PYTHON)
def black(session: nox.Session) -> None:
    """Check if style adheres to black."""
    ruff(session)


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
    """Run tests without external dependencies if not running in CI.

    This session will only run tests that do not require external dependencies
    if it is not called from within CI.
    """
    if not CI:
        pytest_no_external_dependencies(session)
    else:
        pytest_full(session)


@nox.session(python=PYTHON)
def pytest_no_external_dependencies(session: nox.Session) -> None:
    """Run pytest tests that have no external dependencies.

    This session only runs tests that do not require external dependencies
    such as real databases, Docker, etc. and thus should be able to run
    on any developer machine.
    """
    pdm_sync(session, self=True, default=True, groups=["test"])
    session.warn(
        "Skipping the following test marker(s) "
        "since they require external dependencies: {}.\n"
        "To run all tests, use `nox -s pytest_full`.".format(
            ", ".join(EXTERNAL_DEPENDENCY_MARKERS)
        )
    )

    markexpr = ""
    for index, marker in enumerate(EXTERNAL_DEPENDENCY_MARKERS):
        if index == 0:
            markexpr += f"not {marker}"
        else:
            markexpr += f" and not {marker}"

    session.run("pytest", "tests", "-m", markexpr, *session.posargs)


@nox.session(python=PYTHON)
def pytest_full(session: nox.Session) -> None:
    """Run all pytest tests.

    This session includes all tests and is intended to be
    run in CI or before a commit.
    """
    pdm_sync(session, self=True, default=True, groups=["test"])
    args = session.posargs if not CI else ["--cov"]
    session.run(
        "pytest",
        "tests",
        "-m",
        # FRRouting tests that run against a FRRouting daemon have their own session
        "not frrouting_daemon_required",
        *args,
    )
    session.notify(
        "pytest_frrouting_daemon_required"
    )  # TODO: Fix that only one session is run


@nox.session(python=PYTHON)
@nox.parametrize(
    "frrouting",
    [
        "7.3.1",
        "7.4.0",
        "7.5.1",
        "8.1.0",
        "8.2.2",
        "8.3.1",
        "8.4.2",
        "8.5.3",
        "9.0.1",
    ],
)
def pytest_frrouting_daemon_required(session: nox.Session, frrouting: str) -> None:
    """Run pytest FRRouting integration tests against a FRRouting daemon.

    This session runs the integration tests that run against a local FRRouting instance
    for all supported FRRouting versions using the FRRouting docker image.
    """
    pdm_sync(session, self=True, default=True, groups=["test"])
    if shutil.which("docker") is None:
        session.error("This session requires Docker to be installed")
    session.env["FRR_VERSION"] = frrouting
    session.run(
        "pytest",
        "tests",
        "-m",
        "frrouting_daemon_required",
        *session.posargs,
    )


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
