# ruff: noqa: FBT001
from pathlib import Path
from typing import Annotated, Optional

import typer
from pydantic import ValidationError

from anycastd import __version__
from anycastd._cli.output import ExitCode, print_error
from anycastd._configuration import ConfigurationError, MainConfiguration
from anycastd.core import run_from_configuration

CONFIG_PATH = Path("/etc/anycastd/config.toml")

app = typer.Typer(no_args_is_help=True, add_completion=False)


def version_callback(value: bool) -> None:
    """Show the current version and exit."""
    if value:
        typer.echo("anycastd {}".format(__version__))
        raise typer.Exit()


@app.callback()
def callback(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            help=version_callback.__doc__,
            is_eager=True,
            callback=version_callback,
        ),
    ] = None,
) -> None:
    """Manage anycasted services based on status checks."""


@app.command()
def run(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Location of the configuration file.",
            envvar="CONFIG",
            readable=False,
            resolve_path=True,
        ),
    ] = CONFIG_PATH,
) -> None:
    """Run anycastd."""
    main_configuration = _get_main_configuration(config)
    run_from_configuration(main_configuration)


def _get_main_configuration(config: Path) -> MainConfiguration:
    """Get the main configuration object from a path to a TOML file.

    Try to read the configuration file while exiting with an appropriate exit
    code if an error occurs.
    """
    try:
        return MainConfiguration.from_toml_file(config)
    except ConfigurationError as exc:
        match exc.__cause__:
            case FileNotFoundError() | PermissionError():
                exit_code = ExitCode.NOINPUT
            case IsADirectoryError():
                exit_code = ExitCode.IOERR
            case KeyError() | ValueError() | TypeError() | ValidationError():
                exit_code = ExitCode.DATAERR
            case _:
                exit_code = ExitCode.ERR
        print_error(exc, exit_code=exit_code)
