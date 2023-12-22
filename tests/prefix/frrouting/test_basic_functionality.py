from pathlib import Path

import pytest
from anycastd._executor import DockerExecutor
from anycastd.prefix import FRRoutingPrefix

from tests.conftest import skip_without_docker

pytestmark = [pytest.mark.integration, pytest.mark.frrouting]


@pytest.fixture
def docker_executor(frr_container) -> DockerExecutor:
    """A docker executor for the FRR container.

    The FRR container is implicitly started by requesting the frr_container fixture.
    """
    return DockerExecutor(docker=Path("/usr/bin/docker"), container=frr_container)


@skip_without_docker
@pytest.mark.asyncio
async def test_announce_adds_bgp_network(  # noqa: PLR0913
    vtysh,
    docker_executor,
    example_networks,
    example_vrfs,
    bgp_prefix_configured,
    remove_bgp_prefix,
    example_asn,
):
    """Announcing adds the corresponding BGP prefix to the configuration."""
    prefix = FRRoutingPrefix(
        example_networks, vrf=example_vrfs, executor=docker_executor
    )
    if example_vrfs:
        vtysh(f"router bgp {example_asn} vrf {example_vrfs}", configure_terminal=True)

    await prefix.announce()

    assert bgp_prefix_configured(prefix.prefix, vtysh=vtysh, vrf=example_vrfs)

    # Clean up
    remove_bgp_prefix(prefix.prefix, asn=example_asn, vtysh=vtysh, vrf=example_vrfs)
    if example_vrfs:
        vtysh(
            f"no router bgp {example_asn} vrf {example_vrfs}", configure_terminal=True
        )


@skip_without_docker
@pytest.mark.asyncio
async def test_denounce_removes_bgp_network(  # noqa: PLR0913
    vtysh,
    docker_executor,
    example_networks,
    example_vrfs,
    example_asn,
    bgp_prefix_configured,
    add_bgp_prefix,
):
    """Denouncing removes the corresponding BGP prefix from the configuration."""
    prefix = FRRoutingPrefix(
        example_networks, vrf=example_vrfs, executor=docker_executor
    )
    add_bgp_prefix(prefix.prefix, asn=example_asn, vtysh=vtysh, vrf=example_vrfs)

    await prefix.denounce()

    assert not bgp_prefix_configured(prefix.prefix, vtysh=vtysh, vrf=example_vrfs)


@skip_without_docker
@pytest.mark.asyncio
@pytest.mark.parametrize("announced", [True, False])
async def test_announcement_state_reported_correctly(  # noqa: PLR0913
    vtysh,
    docker_executor,
    example_networks,
    example_vrfs,
    example_asn,
    add_bgp_prefix,
    remove_bgp_prefix,
    announced: bool,
):
    """The announcement state is reported correctly."""
    prefix = FRRoutingPrefix(
        example_networks, vrf=example_vrfs, executor=docker_executor
    )
    if announced:
        add_bgp_prefix(prefix.prefix, asn=example_asn, vtysh=vtysh, vrf=example_vrfs)

    assert await prefix.is_announced() == announced

    # Clean up
    if announced:
        remove_bgp_prefix(prefix.prefix, asn=example_asn, vtysh=vtysh, vrf=example_vrfs)
