# ruff: noqa: FBT001
import asyncio
import logging
import sys
from collections.abc import Callable
from enum import StrEnum, auto
from pathlib import Path
from typing import Annotated, Optional, assert_never

import orjson
import structlog
import typer
from pydantic import ValidationError

from anycastd import __version__
from anycastd._cli.output import ExitCode, print_error
from anycastd._configuration import ConfigurationError, MainConfiguration
from anycastd.core import run_from_configuration

CONFIG_PATH = Path("/etc/anycastd/config.toml")
IS_TTY = sys.stdout.isatty()

logger = structlog.get_logger()
app = typer.Typer(
    no_args_is_help=True, add_completion=False, pretty_exceptions_show_locals=False
)


class LogLevel(StrEnum):
    Debug = auto()
    Info = auto()
    Warning = auto()
    Error = auto()


class LogFormat(StrEnum):
    Human = auto()
    Json = auto()
    Logfmt = auto()


def version_callback(value: bool) -> None:
    """Show the current version and exit."""
    if value:
        typer.echo("anycastd {}".format(__version__))
        raise typer.Exit()


def log_level_callback(level: LogLevel) -> LogLevel:
    """Configure structlog and typer based on the given log level.

    Configures structlog to filter logs and typer to show locals in
    tracebacks based on the given log level.
    """
    match level:
        case LogLevel.Debug:
            std_level = logging.DEBUG
            app.pretty_exceptions_show_locals = True
        case LogLevel.Info:
            std_level = logging.INFO
        case LogLevel.Warning:
            std_level = logging.WARNING
        case LogLevel.Error:
            std_level = logging.ERROR
        case _ as unreachable:
            assert_never(unreachable)
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(std_level))

    return level


def log_format_callback(format: LogFormat) -> LogFormat:
    """Configure structlog rendering based on the given format."""
    processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    logger_factory: Callable[
        ..., structlog.typing.WrappedLogger
    ] = structlog.WriteLoggerFactory()

    match format:
        case LogFormat.Human:
            processors.append(structlog.dev.ConsoleRenderer())
        case LogFormat.Json:
            processors.append(
                structlog.processors.JSONRenderer(serializer=orjson.dumps)
            )
            logger_factory = structlog.BytesLoggerFactory()
        case LogFormat.Logfmt:
            processors.append(structlog.processors.LogfmtRenderer())
        case _ as unreachable:
            assert_never(unreachable)

    structlog.configure(processors=processors, logger_factory=logger_factory)

    return format


@app.callback()
def main(
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
    log_level: Annotated[
        LogLevel,
        typer.Option(
            "--log-level",
            help="Log level.",
            envvar="LOG_LEVEL",
            case_sensitive=False,
            callback=log_level_callback,
        ),
    ] = LogLevel.Info,
    log_format: Annotated[
        LogFormat,
        typer.Option(
            "--log-format",
            help="Log format.",
            envvar="LOG_FORMAT",
            case_sensitive=False,
            callback=log_format_callback,
        ),
    ] = LogFormat.Human if IS_TTY else LogFormat.Json,
) -> None:
    """Run anycastd."""
    main_configuration = _get_main_configuration(config)
    asyncio.run(
        run_from_configuration(main_configuration),
        debug=True if log_level == LogLevel.Debug else False,
    )


def _get_main_configuration(config: Path) -> MainConfiguration:
    """Get the main configuration object from a path to a TOML file.

    Try to read the configuration file while exiting with an appropriate exit
    code if an error occurs.
    """
    log = logger.bind(config_path=config.as_posix())
    log.info(f"Reading configuration from {config}.")
    try:
        parsed = MainConfiguration.from_toml_file(config)
        log.debug(
            f"Successfully read configuration file {config}.", config=dict(parsed)
        )
        return parsed
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
