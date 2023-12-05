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
