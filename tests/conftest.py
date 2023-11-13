from ipaddress import IPv4Network, IPv6Network
from typing import TypeAlias

import pytest

_IP_Prefix: TypeAlias = IPv4Network | IPv6Network
_VRF: TypeAlias = str | None


@pytest.fixture(scope="session")
def example_asn() -> int:
    return 65536


@pytest.fixture(scope="session")
def ipv4_example_network() -> IPv4Network:
    return IPv4Network("192.0.2.0/24")


@pytest.fixture(scope="session")
def ipv6_example_network() -> IPv6Network:
    return IPv6Network("2001:db8::/32")


@pytest.fixture(
    scope="session", params=["ipv4_example_network", "ipv6_example_network"]
)
def example_networks(request) -> _IP_Prefix:
    """Parametrize tests with example prefixes."""
    return request.getfixturevalue(request.param)


@pytest.fixture(params=[None, "vrf-func-test"])
def example_vrfs(request) -> _VRF:
    """Parametrize tests with example VRFs."""
    return request.param
