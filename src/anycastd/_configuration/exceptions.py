import tomllib
from pathlib import Path


class ConfigurationError(Exception):
    """There was an error with the configuration file."""

    def __init__(self, path: Path, exc: Exception):
        msg = f"Could not read configuration file {path}"
        match exc:
            case tomllib.TOMLDecodeError():
                msg += f" due to a TOML syntax error: {exc}"
            case _:
                msg += f": {exc}"

        super().__init__(msg)
