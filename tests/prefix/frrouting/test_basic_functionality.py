from pathlib import Path

import pytest
from anycastd._executor import DockerExecutor
from anycastd.prefix.frrouting import FRRoutingPrefix

pytestmark = [pytest.mark.integration, pytest.mark.frrouting]


@pytest.fixture
def docker_executor(frr_container) -> DockerExecutor:
    """A docker executor for the FRR container.

    The FRR container is implicitly started by requesting the frr_container fixture.
    """
    return DockerExecutor(docker=Path("/usr/bin/docker"), container=frr_container)


@pytest.mark.asyncio
async def test_announce_adds_bgp_network(  # noqa: PLR0913
    vtysh,
    docker_executor,
    example_networks,
    bgp_prefix_configured,
    remove_bgp_prefix,
    example_asn,
    vrf,
):
    """Announcing adds the corresponding BGP prefix to the configuration."""
    prefix = FRRoutingPrefix(example_networks, vrf=vrf, executor=docker_executor)

    await prefix.announce()

    assert bgp_prefix_configured(prefix.prefix, vtysh=vtysh, vrf=vrf)

    # Clean up
    remove_bgp_prefix(prefix.prefix, asn=example_asn, vtysh=vtysh, vrf=vrf)


@pytest.mark.asyncio
async def test_denounce_removes_bgp_network(  # noqa: PLR0913
    vtysh,
    docker_executor,
    example_networks,
    example_asn,
    vrf,
    bgp_prefix_configured,
    add_bgp_prefix,
):
    """Denouncing removes the corresponding BGP prefix from the configuration."""
    prefix = FRRoutingPrefix(example_networks, vrf=vrf, executor=docker_executor)
    add_bgp_prefix(prefix.prefix, asn=example_asn, vtysh=vtysh, vrf=vrf)

    await prefix.denounce()

    assert not bgp_prefix_configured(prefix.prefix, vtysh=vtysh, vrf=vrf)


@pytest.mark.asyncio
@pytest.mark.parametrize("announced", [True, False])
async def test_announcement_state_reported_correctly(  # noqa: PLR0913
    vtysh,
    docker_executor,
    example_networks,
    example_asn,
    vrf,
    add_bgp_prefix,
    remove_bgp_prefix,
    announced: bool,
):
    """The announcement state is reported correctly."""
    prefix = FRRoutingPrefix(example_networks, vrf=vrf, executor=docker_executor)
    if announced:
        add_bgp_prefix(prefix.prefix, asn=example_asn, vtysh=vtysh, vrf=vrf)

    assert await prefix.is_announced() == announced

    # Clean up
    if announced:
        remove_bgp_prefix(prefix.prefix, asn=example_asn, vtysh=vtysh, vrf=vrf)
