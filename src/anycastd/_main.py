import asyncio
from dataclasses import dataclass

from anycastd.healthcheck.base import BaseHealthcheck
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

    async def run(self) -> None:
        """Run the service.

        This will announce the prefixes when all health checks are
        passing, and denounce them otherwise.
        """
        while True:
            if all(check.is_healthy for check in self.health_checks):
                asyncio.gather(prefix.announce() for prefix in self.prefixes)
            else:
                asyncio.gather(prefix.denounce() for prefix in self.prefixes)
