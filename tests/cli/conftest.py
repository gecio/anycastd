from collections.abc import Callable

import pytest
from anycastd._cli.main import app
from click.testing import Result
from typer.testing import CliRunner


@pytest.fixture(scope="session")
def anycastd_cli() -> Callable[..., Result]:
    """A callable that runs anycastd CLI commands."""
    runner = CliRunner(mix_stderr=False)

    def run_cli_command(
        *args: str, input: bytes | str | None = None, catch_exceptions: bool = False
    ) -> Result:
        command = [*args]
        return runner.invoke(
            app, command, input=input, catch_exceptions=catch_exceptions
        )

    return run_cli_command
