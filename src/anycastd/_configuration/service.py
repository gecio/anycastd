from dataclasses import dataclass
from typing import Self

from anycastd._configuration import healthcheck, prefix
from anycastd._configuration.exceptions import ConfigurationSyntaxError
from anycastd._configuration.healthcheck import HealthcheckConfiguration
from anycastd._configuration.prefix import PrefixConfiguration


@dataclass
class ServiceConfiguration:
    """A service configuration."""

    name: str
    prefixes: tuple[PrefixConfiguration, ...]
    checks: tuple[HealthcheckConfiguration, ...]

    @classmethod
    def from_configuration_dict(cls, data: dict) -> Self:
        """Create an instance from a dictionary containing configuration data.

        Args:
            data: The configuration data.

        Example:
        ```python
        {
            "name": "important-API",
            "prefixes": {"routingd": ["2001:db8::aced:a11:7e57"]},
            "checks": {
                "healthd": [{"interval": "1s", "name": "important-API-healthy"}]
            },
        }
        ```

        Raises:
            ConfigurationSyntaxError: The configuration data has an invalid syntax.
        """
        try:
            name = data["name"]
            keyed_prefixes = data["prefixes"]
            keyed_checks = data["checks"]
        except KeyError as exc:
            raise ConfigurationSyntaxError.from_key_error(exc) from exc

        prefixes = []
        for prefix_type, prefix_configs in keyed_prefixes.items():
            prefix_class = prefix.get_type_by_name(prefix_type)

            for config in prefix_configs:
                prefixes.append(prefix_class.from_configuration(config))

        checks = []
        for check_type, check_configs in keyed_checks.items():
            check_class = healthcheck.get_type_by_name(check_type)

            for config in check_configs:
                checks.append(check_class.from_configuration(config))

        return cls(name=name, prefixes=tuple(prefixes), checks=tuple(checks))
