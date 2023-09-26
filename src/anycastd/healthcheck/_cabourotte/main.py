import datetime

from anycastd.healthcheck._cabourotte.result import get_result
from anycastd.healthcheck.base import BaseHealthcheck


class CabourotteHealthcheck(BaseHealthcheck):
    name: str
    url: str

    def __init__(self, name: str, *, url: str, interval: datetime.timedelta):
        super().__init__(interval)
        if not isinstance(name, str):
            raise TypeError("Name must be a string.")
        if not isinstance(url, str):
            raise TypeError("URL must be a string.")
        self.name = name
        self.url = url

    async def _check(self) -> bool:
        """Return whether the healthcheck is healthy or not."""
        result = await get_result(self.name, url=self.url)
        return result.success
