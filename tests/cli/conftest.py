from collections.abc import Callable, Iterator

import pytest
import structlog
from anycastd._cli.main import app
from click.testing import Result
from typer.testing import CliRunner


@pytest.fixture
def reset_structlog_config() -> Iterator[None]:
    """Reset structlog configuration after running a test.

    This is required for tests that invoke the anycastd CLI, as running it
    initializes the structlog configuration, adding filters that could affect
    other tests.
    """
    yield
    structlog.reset_defaults()


@pytest.fixture
def anycastd_cli(reset_structlog_config) -> Callable[..., Result]:
    """A callable that runs anycastd CLI commands.

    To make sure that this fixture does not affect other tests, state that is
    initialized when running the CLI needs to be reset after using this fixture.

    Example:
    ```python
    >>> result = anycastd_cli("run", "--help")
    >>> assert result.exit_code == 0
    ```
    """
    runner = CliRunner(mix_stderr=False)

    def run_cli_command(
        *args: str,
        input: bytes | str | None = None,
        catch_exceptions: bool = False,
        env: dict[str, str] | None = None,
    ) -> Result:
        command = [*args]
        return runner.invoke(
            app, command, input=input, catch_exceptions=catch_exceptions, env=env
        )

    return run_cli_command
