import asyncio
import signal
import sys
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, NoReturn

import structlog

from anycastd._configuration import MainConfiguration, config_to_service
from anycastd.core._service import Service

logger = structlog.get_logger()


async def run_from_configuration(configuration: MainConfiguration) -> None:
    """Run anycastd using an instance of the main configuration."""
    services = tuple(config_to_service(config) for config in configuration.services)
    await run_services(services)


async def run_services(services: Iterable[Service]) -> None:
    """Run services until termination.

    A signal handler is installed to manage termination. When a SIGTERM or SIGINT
    signal is received, graceful termination is managed by the handler.

    Args:
        services: The services to run.
    """
    signal_handler = create_signal_handler(services)
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    async with asyncio.TaskGroup() as tg:
        for service in services:
            tg.create_task(service.run())


def create_signal_handler(
    services: Iterable[Service],
) -> Callable[[signal.Signals, Any], Awaitable[NoReturn]]:
    """Create a signal handler to manage termination.

    Create a signal handler that will log the received signal, terminate all tasks,
    denounce prefixes for all services, and then exit.
    """

    async def _handler(signal: signal.Signals, _: Any) -> NoReturn:
        logger.info("Received %s, terminating.", signal)

        for task in asyncio.all_tasks():
            task.cancel()

        denounce_coros = (service.denounce_all_prefixes() for service in services)
        await asyncio.gather(*denounce_coros)

        sys.exit(0)

    return _handler
