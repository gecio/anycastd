import asyncio
from collections.abc import Iterable

import structlog

from anycastd._configuration import MainConfiguration, config_to_service
from anycastd.core._service import Service

logger = structlog.get_logger()


async def run_from_configuration(configuration: MainConfiguration) -> None:
    """Run anycastd using an instance of the main configuration."""
    services = tuple(config_to_service(config) for config in configuration.services)
    logger.debug("Running services.", services=services)
    await run_services(services)


async def run_services(services: Iterable[Service]) -> None:
    """Run services.

    Args:
        services: The services to run.
    """
    async with asyncio.TaskGroup() as tg:
        for service in services:
            tg.create_task(service.run())
