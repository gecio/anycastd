from enum import StrEnum
from ipaddress import IPv4Network, IPv6Network
from typing import Protocol, TypeAlias, runtime_checkable

VRF: TypeAlias = str | None


class AFI(StrEnum):
    """The IP address family."""

    IPv4 = "ipv4"
    IPv6 = "ipv6"


@runtime_checkable
class Prefix(Protocol):
    """An IP prefix that can be announced or denounced."""

    @property
    def prefix(self) -> IPv4Network | IPv6Network:
        """The IP prefix."""
        ...

    @property
    def afi(self) -> AFI:
        """The address family of the prefix."""
        ...

    async def is_announced(self) -> bool:
        """Whether the prefix is currently announced."""
        ...

    async def announce(self) -> None:
        """Announce the prefix."""
        ...

    async def denounce(self) -> None:
        """Denounce the prefix."""
        ...
