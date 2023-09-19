from abc import ABC, abstractmethod


class BaseHealthcheck(ABC):
    """A healthcheck that represents a status."""

    @property
    @abstractmethod
    def is_healthy(self) -> bool:
        """Whether the healthcheck is healthy."""
