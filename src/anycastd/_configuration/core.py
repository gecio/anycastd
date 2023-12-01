import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from pydantic import ValidationError

from anycastd._configuration.exceptions import ConfigurationError
from anycastd._configuration.service import ServiceConfiguration


@dataclass
class MainConfiguration:
    """The top-level configuration object."""

    services: tuple[ServiceConfiguration, ...]

    @classmethod
    def from_toml_file(cls, path: Path) -> Self:
        """Create a configuration instance from a TOML configuration file.

        Args:
            path: The path to the configuration file.

        Raises:
            ConfigurationError: The configuration could not be read or parsed.
        """
        config = _read_toml_configuration(path)
        try:
            return cls(
                services=tuple(
                    ServiceConfiguration.from_name_and_options(name, options)
                    for name, options in config["services"].items()
                )
            )
        except (KeyError, ValueError, TypeError, ValidationError) as exc:
            raise ConfigurationError(path, exc) from exc


def _read_toml_configuration(path: Path) -> dict:
    """Read a TOML configuration file.

    Args:
        path: The path to the configuration file.

    Returns:
        The parsed configuration data.

    Raises:
        ConfigurationError: The configuration could not be read or parsed.
    """
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigurationError(path, exc) from exc

    return data
