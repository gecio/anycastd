from anycastd.healthcheck import Healthcheck
from anycastd.prefix.core import Prefix


class DummyHealthcheck(Healthcheck):
    """A dummy healthcheck to test the abstract base class."""

    async def _check(self) -> bool:
        """Always healthy."""
        return True


class DummyPrefix(Prefix):
    """A dummy prefix to test the abstract base class."""

    async def is_announced(self) -> bool:
        """Always announced."""
        return True

    async def announce(self) -> None:
        """Dummy method."""

    async def denounce(self) -> None:
        """Dummy method."""
