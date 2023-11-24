from dataclasses import dataclass
from typing import Self

from anycastd._configuration import healthcheck, prefix
from anycastd._configuration.sub import HealthcheckConfiguration, PrefixConfiguration


@dataclass
class ServiceConfiguration:
    """The configuration for a service."""

    name: str
    prefixes: tuple[PrefixConfiguration, ...]
    checks: tuple[HealthcheckConfiguration, ...]

    @classmethod
    def from_name_and_options(cls, name: str, options: dict) -> Self:
        """Create an instance from the configuration format.

        Args:
            name: The name of the service.
            options: The configuration options for the service.

        Returns:
            A new ServiceConfiguration instance.

        Raises:
            KeyError: The configuration is missing a required key.
            ValueError: The configuration contains an invalid value.
        """
        prefixes = []
        for prefix_type, prefix_configs in options["prefixes"].items():
            prefix_class = prefix.get_type_by_name(prefix_type)

            for config in prefix_configs:
                prefixes.append(prefix_class.from_configuration(config))

        checks = []
        for check_type, check_configs in options["checks"].items():
            check_class = healthcheck.get_type_by_name(check_type)

            for config in check_configs:
                checks.append(check_class.from_configuration(config))

        return cls(name=name, prefixes=tuple(prefixes), checks=tuple(checks))
