import tomllib
from pathlib import Path

from pydantic import ValidationError


class ConfigurationError(Exception):
    """There was an error with the configuration file."""

    def __init__(
        self,
        path: Path,
        exc: OSError
        | tomllib.TOMLDecodeError
        | KeyError
        | ValueError
        | ValidationError
        | TypeError,
    ):
        msg = f"Could not read from configuration file {path}"
        match exc:
            case OSError():
                msg += f" due to an I/O error: {exc}"
            case tomllib.TOMLDecodeError():
                msg += f" due to a TOML syntax error: {exc}"
            case KeyError():
                msg += f" due to missing required key: {exc}"
            case ValueError() | ValidationError() | TypeError():
                msg += f": {exc}"
            case _:
                msg += f", an unexpected exception occurred: {exc!r}"
                raise TypeError(msg) from exc  # type: ignore[unused-ignore]

        super().__init__(msg)
