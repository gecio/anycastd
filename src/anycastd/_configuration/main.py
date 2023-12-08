import tomllib
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ValidationError

from anycastd._configuration.conversion import (
    dict_w_items_named_by_key_to_flat_w_name_value,
)
from anycastd._configuration.exceptions import (
    ConfigurationError,
    ConfigurationMissingKeyError,
)
from anycastd._configuration.service import ServiceConfiguration


class MainConfiguration(BaseModel):
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
            return cls.from_configuration_dict(config)
        except (KeyError, ValueError, TypeError, ValidationError) as exc:
            raise ConfigurationError(path, exc) from exc

    @classmethod
    def from_configuration_dict(cls, data: dict) -> Self:
        """Create an instance from a dictionary containing configuration data.

        Args:
            data: The configuration data.

        Example:
        ```python
        {
            "services": {
                "important-API": (
                    {
                        "prefixes": {"routingd": ["2001:db8::aced:a11:7e57"]},
                        "checks": {
                            "healthd": [
                                {"interval": "1s", "name": "important-API-healthy"}
                            ]
                        },
                    },
                ),
                "important-backend": {
                    "prefixes": {"bgpd": ["2001:db8::bad:1dea"]},
                    "checks": {"pingd": ["flaky-backend"]},
                },
            }
        }
        ```
        """
        try:
            keyed_services = data["services"]
        except KeyError as exc:
            raise ConfigurationMissingKeyError(exc) from exc

        services = tuple(
            ServiceConfiguration.from_configuration_dict(service_config)
            for service_config in dict_w_items_named_by_key_to_flat_w_name_value(
                keyed_services
            )
        )

        return cls(services=services)


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
