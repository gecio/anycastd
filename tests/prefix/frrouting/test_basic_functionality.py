import pytest
from anycastd.prefix.frrouting import FRRoutingPrefix

pytestmark = [pytest.mark.integration, pytest.mark.frrouting]


@pytest.mark.asyncio
async def test_announce_adds_bgp_network(
    vtysh, example_networks, bgp_prefix_configured
):
    """Announcing adds the corresponding BGP prefix to the configuration."""
    prefix = FRRoutingPrefix(example_networks)

    await prefix.announce()

    assert bgp_prefix_configured(prefix.prefix, vtysh)


@pytest.mark.asyncio
async def test_denounce_removes_bgp_network(
    vtysh, example_networks, example_asn, bgp_prefix_configured, add_bgp_prefix
):
    """Denouncing removes the corresponding BGP prefix from the configuration."""
    prefix = FRRoutingPrefix(example_networks)
    add_bgp_prefix(prefix.prefix, asn=example_asn, vtysh=vtysh)

    await prefix.denounce()

    assert not bgp_prefix_configured(prefix.prefix, vtysh)


@pytest.mark.asyncio
@pytest.mark.parametrize("announced", [True, False])
async def test_announcement_state_reported_correctly(
    vtysh, example_networks, example_asn, add_bgp_prefix, announced: bool
):
    """The announcement state is reported correctly."""
    prefix = FRRoutingPrefix(example_networks)
    if announced:
        add_bgp_prefix(prefix.prefix, asn=example_asn, vtysh=vtysh)

    assert await prefix.is_announced() == announced
