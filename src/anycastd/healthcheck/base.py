import datetime
from abc import ABC, abstractmethod


class BaseHealthcheck(ABC):
    """A healthcheck that represents a status."""

    interval: datetime.timedelta

    _last_checked: datetime.datetime | None = None
    _last_healthy: bool = False

    def __init__(self, interval: datetime.timedelta):
        if not isinstance(interval, datetime.timedelta):
            raise TypeError("Interval must be a timedelta.")
        self.interval = interval

    @property
    @abstractmethod
    def is_healthy(self) -> bool:
        """Whether the healthcheck is healthy."""
