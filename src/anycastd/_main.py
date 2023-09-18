from dataclasses import dataclass

from anycastd.healtcheck.base import BaseHealthcheck
from anycastd.prefix.base import BasePrefix


@dataclass
class Service:
    """Represents an anycasted service.

    A service is made up of a collection of prefixes that are
    to be advertised when all health checks are passing.
    """

    name: str
    prefixes: tuple[BasePrefix, ...]
    health_checks: tuple[BaseHealthcheck, ...]
