from abc import ABC, abstractmethod
from ipaddress import IPv4Network, IPv6Network


class BasePrefix(ABC):
    """An IP prefix that can be announced or denounced."""

    _prefix: IPv4Network | IPv6Network

    @abstractmethod
    @property
    def is_announced(self) -> bool:
        """Whether the prefix is currently announced."""

    @abstractmethod
    def announce(self) -> None:
        """Announce the prefix."""

    @abstractmethod
    def denounce(self) -> None:
        """Denounce the prefix."""
