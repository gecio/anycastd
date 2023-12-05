import datetime

from anycastd.healthcheck._cabourotte.result import get_result
from anycastd.healthcheck._main import Healthcheck


class CabourotteHealthcheck(Healthcheck):
    name: str
    url: str

    def __init__(self, name: str, *, url: str, interval: datetime.timedelta):
        if not isinstance(interval, datetime.timedelta):
            raise TypeError("Interval must be a timedelta.")
        if not isinstance(name, str):
            raise TypeError("Name must be a string.")
        if not isinstance(url, str):
            raise TypeError("URL must be a string.")
        self.name = name
        self.url = url
        self.__interval = interval

    def __repr__(self) -> str:
        return (
            f"CabourotteHealthcheck(name={self.name!r}, url={self.url!r}, "
            f"interval={self.interval!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CabourotteHealthcheck):
            return NotImplemented

        return self.__dict__ == other.__dict__

    @property
    def interval(self) -> datetime.timedelta:
        return self.__interval

    async def _check(self) -> bool:
        """Return whether the healthcheck is healthy or not."""
        result = await get_result(self.name, url=self.url)
        return result.success
