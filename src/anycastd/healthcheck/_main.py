import datetime
from abc import ABC, abstractmethod
from typing import final


class Healthcheck(ABC):
    """A healthcheck that represents a status."""

    _last_checked: datetime.datetime | None = None
    _last_healthy: bool = False

    @property
    @abstractmethod
    def interval(self) -> datetime.timedelta:
        """The interval between checks."""
        raise NotImplementedError

    @final
    async def is_healthy(self) -> bool:
        """Whether the healthcheck is healthy.

        Runs a check and returns it's result if the interval has passed or no
        previous check has been run. Otherwise, the previous result is returned.
        """
        if (
            self._last_checked is None
            or datetime.datetime.now(datetime.timezone.utc) - self._last_checked
            > self.interval
        ):
            healthy = await self._check()

            self._last_checked = datetime.datetime.now(datetime.timezone.utc)
            self._last_healthy = healthy

            return healthy

        return self._last_healthy

    @abstractmethod
    async def _check(self) -> bool:
        """Run the healthcheck.

        This method must be implemented by subclasses and return a boolean
        indicating whether the healthcheck passed or failed.
        """
        raise NotImplementedError
