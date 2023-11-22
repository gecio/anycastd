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
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ConfigurationError(path, exc) from exc
