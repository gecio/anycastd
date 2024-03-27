from dataclasses import dataclass
from ipaddress import IPv4Network, IPv6Network

from anycastd.prefix import Prefix


@dataclass
class DummyHealthcheck:
    """A dummy healthcheck to test the abstract base class."""

    name: str

    async def is_healthy(self) -> bool:
        """Always healthy."""
        return True


class DummyPrefix(Prefix):
    """A dummy prefix to test the abstract base class."""

    def __init__(self, prefix: IPv4Network | IPv6Network, *args, **kwargs):
        self.__prefix = prefix

    @property
    def prefix(self) -> IPv4Network | IPv6Network:
        return self.__prefix

    async def is_announced(self) -> bool:
        """Always announced."""
        return True

    async def announce(self) -> None:
        """Dummy method."""

    async def denounce(self) -> None:
        """Dummy method."""
