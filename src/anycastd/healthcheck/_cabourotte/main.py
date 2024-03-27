import datetime
from dataclasses import dataclass, field

import structlog

from anycastd.healthcheck._cabourotte.exceptions import CabourotteCheckNotFoundError
from anycastd.healthcheck._cabourotte.result import get_result
from anycastd.healthcheck._common import CheckCoroutine, interval_check

logger = structlog.get_logger()


@dataclass
class CabourotteHealthcheck:
    name: str
    url: str = field(kw_only=True)
    interval: datetime.timedelta = field(kw_only=True)

    _check: CheckCoroutine = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.interval, datetime.timedelta):
            raise TypeError("Interval must be a timedelta.")
        if not isinstance(self.name, str):
            raise TypeError("Name must be a string.")
        if not isinstance(self.url, str):
            raise TypeError("URL must be a string.")
        self._check = interval_check(self.interval, self._get_status)

    async def _get_status(self) -> bool:
        """Get the current status of the check as reported by cabourotte."""
        log = logger.bind(name=self.name, url=self.url, interval=str(self.interval))

        log.debug('Cabourotte health check "%s" awaiting check result.', self.name)
        try:
            result = await get_result(self.name, url=self.url)
        except CabourotteCheckNotFoundError as exc:
            log.error(
                'Cabourotte health check "%s" does not exist, '
                "returning an unhealthy status.",
                self.name,
                exc_info=exc,
            )
            return False
        log.debug(
            'Cabourotte health check "%s" received check result.',
            self.name,
            result=result,
        )

        return result.success

    async def is_healthy(self) -> bool:
        """Return whether the healthcheck is healthy or not."""
        return await self._check()
