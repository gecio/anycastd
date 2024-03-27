import asyncio
from dataclasses import dataclass, field

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

    _healthy: bool = field(default=False, init=False, repr=False, compare=False)
    _terminate: bool = field(default=False, init=False, repr=False, compare=False)
    _log: structlog.typing.FilteringBoundLogger = field(
        default=logger, init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        if not all(isinstance(_, Prefix) for _ in self.prefixes):
            raise TypeError("Prefixes must implement the Prefix protocol")
        if not all(isinstance(_, Healthcheck) for _ in self.health_checks):
            raise TypeError("Health checks must implement the Healthcheck protocol")
        self._log = logger.bind(
            service_name=self.name,
            service_prefixes=[str(prefix.prefix) for prefix in self.prefixes],
            service_health_checks=[check.name for check in self.health_checks],
        )

    @property
    def healthy(self) -> bool:
        """Whether the service is healthy."""
        return self._healthy

    @healthy.setter
    def healthy(self, new_value: bool) -> None:
        if new_value != self._healthy:
            self._healthy = new_value
            self._log.info(
                'Service "%s" is now considered %s, %s related prefixes.',
                self.name,
                "healthy" if new_value is True else "unhealthy",
                "announcing" if new_value is True else "denouncing",
                service_healthy=self.healthy,
            )

    async def run(self) -> None:
        """Run the service.

        This will announce the prefixes when all health checks are
        passing, and denounce them otherwise. If the returned coroutine is cancelled,
        the service will be terminated, denouncing all prefixes in the process.
        """
        self._log.info(
            'Starting service "%s".', self.name, service_healthy=self.healthy
        )
        try:
            while not self._terminate:
                checks_currently_healthy: bool = await self.all_checks_healthy()

                if checks_currently_healthy and not self.healthy:
                    self.healthy = True
                    await self.announce_all_prefixes()
                elif not checks_currently_healthy and self.healthy:
                    self.healthy = False
                    await self.denounce_all_prefixes()

                await asyncio.sleep(0.05)

        except asyncio.CancelledError:
            self._log.debug(
                'Coroutine for service "%s" was cancelled.',
                self.name,
                service_healthy=self.healthy,
            )
            await self.terminate()

    async def all_checks_healthy(self) -> bool:
        """Runs all checks and returns their cumulative result.

        Returns True if all health checks report as healthy, False otherwise.
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
                self._log.error(
                    "An unhandled exception occurred while running a health check.",
                    service_healthy=self.healthy,
                    exc_info=exc,
                )
            self._log.error(
                "Aborting additional checks and treating the service as unhealthy.",
                service_healthy=False,
            )
            return False

        results = (_.result() for _ in tasks)
        return all(results)

    async def announce_all_prefixes(self) -> None:
        """Announce all prefixes."""
        async with asyncio.TaskGroup() as tg:
            for prefix in self.prefixes:
                tg.create_task(prefix.announce())

    async def denounce_all_prefixes(self) -> None:
        """Denounce all prefixes."""
        async with asyncio.TaskGroup() as tg:
            for prefix in self.prefixes:
                tg.create_task(prefix.denounce())

    async def terminate(self) -> None:
        """Terminate the service and denounce its prefixes."""
        self._terminate = True
        await self.denounce_all_prefixes()
        logger.info('Service "%s" terminated.', self.name, service=self.name)
