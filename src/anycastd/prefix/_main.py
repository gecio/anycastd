from abc import ABC, abstractmethod
from ipaddress import IPv4Network, IPv6Network
from typing import TypeAlias

VRF: TypeAlias = str | None


class Prefix(ABC):
    """An IP prefix that can be announced or denounced."""

    @property
    @abstractmethod
    def prefix(self) -> IPv4Network | IPv6Network:
        """The IP prefix."""
        raise NotImplementedError

    @abstractmethod
    async def is_announced(self) -> bool:
        """Whether the prefix is currently announced.

        This method must be implemented by subclasses and return a boolean
        indicating whether the prefix is currently announced.
        """
        raise NotImplementedError

    @abstractmethod
    async def announce(self) -> None:
        """Announce the prefix.

        This method must be implemented by subclasses and announce the
        prefix if it isn't announced already.
        """
        raise NotImplementedError

    @abstractmethod
    async def denounce(self) -> None:
        """Denounce the prefix.

        This method must be implemented by subclasses and denounce the
        prefix if it is announced.
        """
        raise NotImplementedError
