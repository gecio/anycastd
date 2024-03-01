import asyncio
import signal
import sys
from collections.abc import Iterable
from functools import partial
from typing import NoReturn

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
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, partial(signal_handler, sig))

    async with asyncio.TaskGroup() as tg:
        for service in services:
            tg.create_task(service.run())


def signal_handler(signal: signal.Signals) -> NoReturn:
    """Logs the received signal and terminates all tasks."""
    msg = f"Received {signal.name}, terminating."

    logger.info(msg)
    for task in asyncio.all_tasks():
        task.cancel(msg)

    sys.exit(0)
