from pathlib import Path
from typing import Annotated

import typer

CONFIG_PATH = Path("/etc/anycastd/config.toml")

app = typer.Typer()


@app.callback()
def callback():
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
        ),
    ] = CONFIG_PATH,
) -> None:
    """Run anycastd."""
