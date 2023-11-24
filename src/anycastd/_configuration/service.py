from dataclasses import dataclass
from typing import Self

from anycastd._configuration.cabourotte import CabourotteHealthcheck
from anycastd._configuration.frr import FRRPrefix

prefix_classes: dict[str, type] = {
    "frrouting": FRRPrefix,
}

check_classes: dict[str, type] = {
    "cabourotte": CabourotteHealthcheck,
}


@dataclass
class ServiceConfiguration:
    """The configuration for a service."""

    name: str
    prefixes: tuple[FRRPrefix, ...]
    checks: tuple[CabourotteHealthcheck, ...]

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
            try:
                prefix_class = prefix_classes[prefix_type]
            except KeyError as exc:
                raise ValueError(f"Unknown prefix type: {prefix_type}") from exc

            for config in prefix_configs:
                prefixes.append(prefix_class.from_configuration(config))

        checks = []
        for check_type, check_configs in options["checks"].items():
            try:
                check_class = check_classes[check_type]
            except KeyError as exc:
                raise ValueError(f"Unknown check type: {check_type}") from exc

            for config in check_configs:
                checks.append(check_class.from_configuration(config))

        return cls(name=name, prefixes=tuple(prefixes), checks=tuple(checks))
