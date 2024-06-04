from typing import NoReturn, overload

import typer
from rich.console import Console
from rich.panel import Panel
from typer.rich_utils import _get_rich_console as _typer_get_rich_console

from anycastd.core import ExitCode


@overload
def print_error(msg: str | Exception, *, exit_code: None) -> None: ...


@overload
def print_error(msg: str | Exception, *, exit_code: ExitCode) -> NoReturn: ...


def print_error(msg: str | Exception, *, exit_code: ExitCode | None = None) -> None:
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
        raise typer.Exit(exit_code)


def _get_rich_console(*, stderr: bool = False) -> Console:
    """Get a rich console as configured by Typer.

    Args:
        stderr: Print to stderr instead of stdout.
    """
    return _typer_get_rich_console(stderr=stderr)
