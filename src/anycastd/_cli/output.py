from enum import Enum
from typing import NoReturn, overload

import typer
from rich.console import Console
from rich.panel import Panel
from typer.rich_utils import _get_rich_console as _typer_get_rich_console


class ExitCode(Enum):
    """Exit codes as defined by BSD sysexits.h.

    Values are the same as the exit codes defined in sysexits.h.
    https://man.freebsd.org/cgi/man.cgi?query=sysexits

    Values:
        OK: Successful termination.
        ERR: Catchall for general errors.
        DATAERR: The input data was incorrect in some way. This should only be used
          for user's data and not system files.
        NOINPUT: An	input file (not	a system file) did  not	 exist or was not readable.
        NOHOST: The host specified did not exist.
        UNAVAILABLE: A service is unavailable. This can occur if a support program or
          file does not exist.
        IOERR: An error occurred while doing I/O on some file.
        TEMPFAIL: Temporary failure, indicating something that is not really an error.
        PROTOCOL: The remote system returned something that was "not possible" during
          a protocol exchange.
        NOPERM: You did not have sufficient permission to perform the operation. This
            is not intended for file system problems.
        CONFIG: Something was found in an unconfigured or misconfigured state.
    """

    OK = 0
    ERR = 1
    DATAERR = 65
    NOINPUT = 66
    NOHOST = 68
    UNAVAILABLE = 69
    IOERR = 74
    TEMPFAIL = 75
    PROTOCOL = 76
    NOPERM = 77
    CONFIG = 78


@overload
def print_error(msg: str | Exception, *, exit_code: None) -> None:
    ...


@overload
def print_error(msg: str | Exception, *, exit_code: ExitCode) -> NoReturn:
    ...


def print_error(
    msg: str | Exception, *, exit_code: ExitCode | None = None
) -> None | NoReturn:
    """Print an error message to stderr and optionally exit.

    Args:
        msg: The error message to print. A string or an exception that will be
          converted to a string.
        exit_code: An exit code to exit with, or None to not exit.
    """
    stderr = _get_rich_console(stderr=True)
    msg = msg if isinstance(msg, str) else str(msg)

    stderr.print(
        Panel(
            msg,  # TODO: Highlighting
            title="Error",
            title_align="left",
            border_style="red",
        )
    )

    if exit_code is not None:
        raise typer.Exit(exit_code.value)
    return None


def _get_rich_console(*, stderr: bool = False) -> Console:
    """Get a rich console as configured by Typer.

    Args:
        stderr: Print to stderr instead of stdout.
    """
    return _typer_get_rich_console(stderr=stderr)
