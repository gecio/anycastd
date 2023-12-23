from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import TypeAlias

CheckCoroutine: TypeAlias = Callable[[], Awaitable[bool]]


def interval_check(interval: timedelta, check: CheckCoroutine) -> CheckCoroutine:
    """Wrap a check coroutine to only evaluate it if a given interval has passed.

    Wraps a given check coroutine to only evaluate it if a given interval has passed,
    returning the last result otherwise.

    Args:
        interval: The interval to wait between evaluations.
        check: A check coroutine to be evaluated.

    Returns:
        A coroutine returning either the result of the given check coroutine or the
        last result returned by it if the interval has not passed.
    """
    last_checked: datetime | None = None
    last_healthy: bool = False

    async def _check() -> bool:
        nonlocal last_checked, last_healthy

        if last_checked is None or datetime.now(timezone.utc) - last_checked > interval:
            healthy = await check()

            last_checked = datetime.now(timezone.utc)
            last_healthy = healthy

            return healthy

        return last_healthy

    return _check
