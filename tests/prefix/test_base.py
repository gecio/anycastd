from ipaddress import IPv4Network, IPv6Network

import pytest

from tests.dummy import DummyPrefix


def test__init___non_network_raises_type_error():
    """Passing a non network prefix raises a TypeError."""
    with pytest.raises(TypeError):
        DummyPrefix("2001:db8::/32")  # type: ignore


def test__init__ip_network(example_networks: IPv4Network | IPv6Network):
    """IPv4Network and IPv6Network prefixes are accepted."""
    DummyPrefix(example_networks)


def test__repr__(example_networks: IPv4Network | IPv6Network):
    """The repr of a subclassed prefix is correct."""
    prefix = DummyPrefix(example_networks)
    assert repr(prefix) == f"DummyPrefix({example_networks!r})"
