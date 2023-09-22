from ipaddress import IPv4Network, IPv6Network

import pytest
from anycastd.prefix.base import BasePrefix

IPV4_EXAMPLE_NETWORK = IPv4Network("192.0.2.0/24")
IPV6_EXAMPLE_NETWORK = IPv6Network("2001:db8::/32")


class DummyPrefix(BasePrefix):
    """A dummy prefix to test the abstract base class."""

    async def is_announced(self) -> bool:
        """Never announced."""
        return True

    async def announce(self) -> None:
        """Dummy method."""

    async def denounce(self) -> None:
        """Dummy method."""


def test__init___non_network_raises_type_error():
    """Passing a non network prefix raises a TypeError."""
    with pytest.raises(TypeError):
        DummyPrefix("2001:db8::/32")


@pytest.mark.parametrize("network", [IPV4_EXAMPLE_NETWORK, IPV6_EXAMPLE_NETWORK])
def test__init__ip_network(network: IPv4Network | IPv6Network):
    """IPv4Network and IPv6Network prefixes are accepted."""
    DummyPrefix(network)


@pytest.mark.parametrize("network", [IPV4_EXAMPLE_NETWORK, IPV6_EXAMPLE_NETWORK])
def test__repr__(network: IPv4Network | IPv6Network):
    """The repr of a subclassed prefix is correct."""
    prefix = DummyPrefix(network)
    assert repr(prefix) == f"DummyPrefix({network!r})"
