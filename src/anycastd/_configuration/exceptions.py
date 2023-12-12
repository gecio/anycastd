from pathlib import Path
from tomllib import TOMLDecodeError

from pydantic import ValidationError


class ConfigurationError(Exception):
    """There was an error with the configuration file."""

    path: Path | None

    def __init__(self, spec: str, path: Path | None):
        msg = "Encountered an error within the configuration"
        if path:
            msg += f" file {path}"
        msg += f":\n    {spec}"

        super().__init__(msg)


class ConfigurationSyntaxError(ConfigurationError):
    """There was a syntax error within the configuration."""

    def __init__(
        self,
        exc: TOMLDecodeError | KeyError | ValidationError,
        path: Path | None = None,
    ):
        match exc:
            case TOMLDecodeError():
                spec = f"TOML syntax error: {exc}"
            case KeyError():
                spec = f"missing required key {exc}"
            case ValidationError():
                spec = f"{exc}"

        super().__init__(spec, path)


class ConfigurationFileUnreadableError(ConfigurationError):
    """The configuration file could not be read."""

    def __init__(self, exc: OSError, path: Path):
        self.path = path
        super().__init__(f"I/O error: {exc}", path)
