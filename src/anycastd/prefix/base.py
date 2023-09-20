from abc import ABC, abstractmethod
from ipaddress import IPv4Network, IPv6Network


class BasePrefix(ABC):
    """An IP prefix that can be announced or denounced."""

    prefix: IPv4Network | IPv6Network

    def __init__(self, prefix: IPv4Network | IPv6Network):
        if not any((isinstance(prefix, IPv4Network), isinstance(prefix, IPv6Network))):
            raise TypeError("Prefix must be an IPv4 or IPv6 network.")
        self.prefix = prefix

    @abstractmethod
    @property
    def is_announced(self) -> bool:
        """Whether the prefix is currently announced."""

    @abstractmethod
    async def announce(self) -> None:
        """Announce the prefix."""

    @abstractmethod
    async def denounce(self) -> None:
        """Denounce the prefix."""
