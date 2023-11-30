from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from anycastd._cli.output import ExitCode, print_error
from anycastd._configuration import ConfigurationError, MainConfiguration

CONFIG_PATH = Path("/etc/anycastd/config.toml")

app = typer.Typer()


@app.callback()
def callback() -> None:
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
