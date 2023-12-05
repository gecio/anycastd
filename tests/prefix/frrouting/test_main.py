from ipaddress import IPv6Network
from pathlib import Path

from anycastd._executor import LocalExecutor
from anycastd.prefix._frrouting.main import FRRoutingPrefix


def test_repr(example_networks, example_vrfs):
    """The repr of a FRRouting prefix is correct."""
    vtysh = Path("/usr/bin/vtysh")
    executor = LocalExecutor()
    prefix = FRRoutingPrefix(
        example_networks,
        vrf=example_vrfs,
        vtysh=vtysh,
        executor=executor,
    )
    assert repr(prefix) == (
        f"FRRoutingPrefix(prefix={example_networks!r}, vrf={example_vrfs!r}, "
        f"vtysh={vtysh!r}, executor={executor!r})"
    )


def test_equal():
    """Two prefixes with the same attributes are equal."""
    prefix1 = FRRoutingPrefix(
        prefix=IPv6Network("2001:db8::/32"), vrf="42", executor=LocalExecutor()
    )
    prefix2 = FRRoutingPrefix(
        prefix=IPv6Network("2001:db8::/32"), vrf="42", executor=LocalExecutor()
    )
    assert prefix1 == prefix2


def test_non_equal():
    """Two prefixes with different attributes are not equal."""
    prefix1 = FRRoutingPrefix(
        prefix=IPv6Network("2001:db8::/32"), vrf="42", executor=LocalExecutor()
    )
    prefix2 = FRRoutingPrefix(
        prefix=IPv6Network("2001:db8::/32"), vrf="43", executor=LocalExecutor()
    )
    assert prefix1 != prefix2
