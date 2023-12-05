from ipaddress import IPv4Network, IPv6Network

from tests.dummy import DummyPrefix


def test__init__ip_network(example_networks: IPv4Network | IPv6Network):
    """IPv4Network and IPv6Network prefixes are accepted."""
    DummyPrefix(example_networks)
