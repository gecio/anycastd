from collections.abc import Iterable
from pathlib import Path
from tomllib import TOMLDecodeError
from typing import Self

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

    def __init__(self, spec: str, path: Path | None = None):
        super().__init__(spec, path)

    @classmethod
    def from_decode_error(cls, exc: TOMLDecodeError, path: Path | None = None) -> Self:
        """Create an instance from a decoding error."""
        spec = f"TOML syntax error: {exc}"
        return cls(spec, path)

    @classmethod
    def from_key_error(cls, exc: KeyError, path: Path | None = None) -> Self:
        """Create an instance from a key error."""
        spec = f"missing required key {exc}"
        return cls(spec, path)

    @classmethod
    def from_validation_error(
        cls, exc: ValidationError, path: Path | None = None
    ) -> Self:
        """Create an instance from a pydantic validation error.

        This will currently only report the first error that occurred while validating
        the configuration, while ideally we would report all of them at once.
        """
        first_error = exc.errors()[0]
        spec: str | None = None

        match exc.title:
            case "InvalidField":
                match first_error["type"]:
                    case "extra_forbidden":
                        field_name = first_error["loc"][0]
                        spec = f"invalid field '{field_name}'"
            case "InvalidFieldType":
                field_name = first_error["loc"][0]
                input = first_error["input"]
                msg = first_error["msg"]
                spec = f"invalid input '{input}' for field '{field_name}': {msg}"
            case "MultipleRequiredFields":
                field_name = first_error["loc"][0]
                spec = f"missing required field '{field_name}'"

        if spec is None:
            spec = str(exc)

        return cls(spec, path)

    @classmethod
    def from_invalid_simple_format(
        cls, name: str, required_fields: Iterable[str], path: Path | None = None
    ) -> Self:
        """Create an instance on an invalid simplified configuration."""
        spec = (
            f"invalid configuration value type for {name}: "
            "expecting a dictionary containing the fields {}".format(
                ", ".join(required_fields),
            )
        )
        return cls(spec, path)


class ConfigurationFileUnreadableError(ConfigurationError):
    """The configuration file could not be read."""

    def __init__(self, exc: OSError, path: Path):
        self.path = path
        super().__init__(f"I/O error: {exc}", path)
