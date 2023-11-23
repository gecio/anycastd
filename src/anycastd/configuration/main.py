import tomllib
from pathlib import Path

from pydantic_settings import BaseSettings

from anycastd.configuration._cabourotte import CabourotteHealthcheck
from anycastd.configuration._frr import FRRPrefix
from anycastd.configuration.exceptions import ConfigurationError


class ServiceConfiguration(BaseSettings):
    """The configuration for a service."""

    name: str
    prefixes: tuple[FRRPrefix, ...]
    checks: tuple[CabourotteHealthcheck, ...]


class MainConfiguration(BaseSettings):
    """The top-level configuration object."""

    services: tuple[ServiceConfiguration, ...]

    def __init__(self, path: Path):
        """Initialize the configuration using a path to a TOML configuration file.

        Args:
            path: The path to the configuration file.

        Raises:
            ConfigurationError: The configuration could not be read or parsed.
        """
        config = _read_toml_configuration(path)


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
