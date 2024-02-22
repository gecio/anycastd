import asyncio
from dataclasses import dataclass

import structlog

from anycastd.healthcheck import Healthcheck
from anycastd.prefix import Prefix

logger = structlog.get_logger()


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
        logger.info(f"Starting service {self.name}.", service=self.name)
        while True:
            async with asyncio.TaskGroup() as tg:
                if await self.is_healthy():
                    for prefix in self.prefixes:
                        tg.create_task(prefix.announce())
                else:
                    for prefix in self.prefixes:
                        tg.create_task(prefix.denounce())
            if _only_once:
                break

    async def is_healthy(self) -> bool:
        """Whether the service is healthy.

        True if all health checks are passing, False otherwise.
        If any health check raises an exception, the remaining checks are aborted,
        the exception(s) are logged, and False is returned.
        """
        try:
            async with asyncio.TaskGroup() as tg:
                tasks = tuple(
                    tg.create_task(_.is_healthy()) for _ in self.health_checks
                )
        except ExceptionGroup as exc_group:
            for exc in exc_group.exceptions:
                logger.error(
                    "An unhandled exception occurred while running a health check.",
                    service=self.name,
                    exc_info=exc,
                )
            logger.error(
                "Aborting additional checks and treating the service as unhealthy.",
                service=self.name,
            )
            return False

        results = (_.result() for _ in tasks)
        return all(results)
