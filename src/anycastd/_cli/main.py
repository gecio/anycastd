# ruff: noqa: FBT001, FBT002
import asyncio
import logging
import sys
from enum import StrEnum, auto
from pathlib import Path
from typing import Annotated, Optional, assert_never

import orjson
import structlog
import typer
from pydantic import ValidationError

from anycastd import __version__
from anycastd._cli.output import print_error
from anycastd._configuration import ConfigurationError, MainConfiguration
from anycastd.core import ExitCode, run_from_configuration

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


def configure_logging(level: LogLevel, format: LogFormat, no_color: bool) -> None:
    """Configure logging using structlog.

    Configures structlogs log level filtering and output processing / formatting
    as well as typer to show locals in tracebacks when using the debug log level.
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
        case _ as unknown_level:
            assert_never(unknown_level)

    processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    logger_factory: structlog.typing.WrappedLogger = (
        structlog.BytesLoggerFactory()
        if format == LogFormat.Json
        else structlog.WriteLoggerFactory()
    )

    match format:
        case LogFormat.Human:
            colors: bool = IS_TTY and not no_color
            processors.append(structlog.dev.ConsoleRenderer(colors=colors))
        case LogFormat.Json:
            processors.append(
                structlog.processors.JSONRenderer(serializer=orjson.dumps)
            )
        case LogFormat.Logfmt:
            processors.append(structlog.processors.LogfmtRenderer())
        case _ as unknown_format:
            assert_never(unknown_format)

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(std_level),
        processors=processors,
        logger_factory=logger_factory,
    )


def version_callback(value: bool) -> None:
    """Show the current version and exit."""
    if value:
        typer.echo("anycastd {}".format(__version__))
        raise typer.Exit()


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
        ),
    ] = LogLevel.Info,
    log_format: Annotated[
        LogFormat,
        typer.Option(
            "--log-format",
            help="Log format.",
            envvar="LOG_FORMAT",
            case_sensitive=False,
        ),
    ] = LogFormat.Human if IS_TTY else LogFormat.Json,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Disable color output.", envvar="NO_COLOR"),
    ] = False,
) -> None:
    """Run anycastd."""
    configure_logging(log_level, log_format, no_color)
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
    log.info("Reading configuration from %s.", config.as_posix())
    try:
        parsed = MainConfiguration.from_toml_file(config)
        log.debug(
            "Successfully read configuration file %s.",
            config.as_posix(),
            config=dict(parsed),
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
