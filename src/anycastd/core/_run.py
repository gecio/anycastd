from collections.abc import Iterable

from anycastd.core._service import Service


def run_services(services: Iterable[Service]) -> None:
    """Run services.

    Args:
        services: The services to run.
    """
    raise NotImplementedError
