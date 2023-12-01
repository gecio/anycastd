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

    # The _only_once parameter is only used for testing.
    # TODO: Look into a better way to do this.
    async def run(self, *, _only_once: bool = False) -> None:
        """Run the service.

        This will announce the prefixes when all health checks are
        passing, and denounce them otherwise.
        """
        while True:
            if await self.is_healthy():
                await asyncio.gather(*(prefix.announce() for prefix in self.prefixes))
            else:
                await asyncio.gather(*(prefix.denounce() for prefix in self.prefixes))
            if _only_once:
                break

    async def is_healthy(self) -> bool:
        """Whether the service is healthy.

        True if all health checks are passing, False otherwise.
        """
        results = await asyncio.gather(*(_.is_healthy() for _ in self.health_checks))
        return all(results)
