from abc import ABC, abstractmethod


class BaseHealthcheck(ABC):
    """A healthcheck that represents a status."""

    @abstractmethod
    @property
    def is_healthy(self) -> bool:
        """Whether the healthcheck is healthy."""
