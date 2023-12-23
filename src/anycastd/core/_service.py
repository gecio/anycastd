import asyncio
from dataclasses import dataclass

from anycastd.healthcheck import Healthcheck
from anycastd.prefix import Prefix


@dataclass
class Service:
    """An anycasted service.

    Services are the main abstraction used in anycastd.
    They represent services that are architected to be highly available
    through the usage of multiple backends whose service prefixes are
    announced through BGP only when their health checks report the underlying
    service to be healthy.

    ```
    ┌─[SRV-DNS01]─────────────────────────────────────────────────────────────────────┐
    ╎                                                                                 ╎
    ╎  +++++++++++++++++++++++++                        ┌──────────┐                  ╎
    ╎  + Service               +                   ┌──> │ HLTH CHK │ ▲ ───────────┐   ╎
    ╎  +           ┌───────────────────────────────┤    └──────────┘              │   ╎
    ╎  + IF healthy•:          +                   │    ┌──────────┐              │   ╎
    ╎  +     announce prefixes +                   ├──> │ HLTH CHK │ ▲ ───────────┤   ╎
    ╎  + ELSE:           •─────────────────────┐   │    └──────────┘              │   ╎
    ╎  +     denounce prefixes +               │   │    ┌──────────┐              │   ╎
    ╎  +++++++++++++++++++++++++               │   └──> │ HLTH CHK │ ▲ ───────────┤   ╎
    ╎                                          │        └──────────┘              │   ╎
    ╎                                          │                                  │   ╎
    ╎  ┌─[ROUTING SVC]───────────────────┐     │        ┌─[DNS SVC]────────┐      │   ╎
    ╎  │ ┌──────────────────────────┐    │     │        │    ┌──┐  ┌─┐     │ ◀────┤   ╎
    ╎  │ │ Prefix                   │ <──│─────┤        │  ──┘  └──┘ └──── │      │   ╎
    ╎  │ │ 2001:db8::b19:bad:53/128 │    │     │        │                  │      │   ╎
    ╎  │ └──────────────────────────┘    │     │        │ ⎕⎕⎕⎕⎕⎕▊▊▊▊▊▊▊▊⎕⎕ │ ◀────┤   ╎
    ╎  │ ┌──────────────────────────┐    │     │        │ ⎕⎕⎕⎕⎕⎕⎕⎕▊▊▊⎕⎕⎕⎕⎕ │      │   ╎
    ╎  │ │ Prefix                   │ <──│─────┘        │ ▊⎕⎕⎕⎕⎕⎕⎕⎕⎕⎕⎕⎕⎕⎕⎕ │      │   ╎
    ╎  │ │ 203.0.113.53/32          │    │              │ ▊⎕⎕⎕⎕⎕⎕⎕⎕⎕⎕⎕⎕▊▊▊ │ ◀────┘   ╎
    ╎  │ └──────────────────────────┘    │              │ ▊⎕⎕⎕⎕⎕⎕⎕⎕⎕⎕▊▊▊▊▊ │          ╎
    ╎  └─────────────────────────────────┘              └──────────────────┘          ╎
    └─────────────────────────────────────────────────────────────────────────────────┘
    ```
    """

    name: str
    prefixes: tuple[Prefix, ...]
    health_checks: tuple[Healthcheck, ...]

    def __post_init__(self) -> None:
        if not all(isinstance(_, Prefix) for _ in self.prefixes):
            raise TypeError("Prefixes must implement the Prefix protocol")
        if not all(isinstance(_, Healthcheck) for _ in self.health_checks):
            raise TypeError("Health checks must implement the Healthcheck protocol")

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
