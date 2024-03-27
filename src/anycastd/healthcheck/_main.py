from typing import Protocol, runtime_checkable


@runtime_checkable
class Healthcheck(Protocol):
    """A health check representing the status of a component."""

    name: str

    async def is_healthy(self) -> bool:
        """Whether the health checked component is healthy or not."""
        ...
