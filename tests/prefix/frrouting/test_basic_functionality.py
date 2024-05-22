from pathlib import Path

import pytest
from anycastd._executor import DockerExecutor
from anycastd.prefix import FRRoutingPrefix

from tests.conftest import skip_without_docker

pytestmark = [pytest.mark.integration, pytest.mark.frrouting_daemon_required]


@pytest.fixture
def docker_executor(frr_container_name) -> DockerExecutor:
    """A docker executor for the FRR container."""
    return DockerExecutor(docker=Path("/usr/bin/docker"), container=frr_container_name)


@skip_without_docker
async def test_announce_adds_bgp_network(  # noqa: PLR0913
    frr_container_vtysh,
    frr_container_reset_bgp_config,
    docker_executor,
    example_networks,
    example_vrfs,
    bgp_prefix_configured,
    example_asn,
):
    """Announcing adds the corresponding BGP prefix to the configuration."""
    prefix = FRRoutingPrefix(
        example_networks, vrf=example_vrfs, executor=docker_executor
    )
    if example_vrfs:
        frr_container_vtysh(
            f"router bgp {example_asn} vrf {example_vrfs}", configure_terminal=True
        )

    await prefix.announce()

    assert bgp_prefix_configured(
        prefix.prefix, vtysh=frr_container_vtysh, vrf=example_vrfs
    )


@skip_without_docker
async def test_denounce_removes_bgp_network(  # noqa: PLR0913
    frr_container_vtysh,
    frr_container_reset_bgp_config,
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
    add_bgp_prefix(
        prefix.prefix, asn=example_asn, vtysh=frr_container_vtysh, vrf=example_vrfs
    )

    await prefix.denounce()

    assert not bgp_prefix_configured(
        prefix.prefix, vtysh=frr_container_vtysh, vrf=example_vrfs
    )


@skip_without_docker
async def test_denounce_without_being_announced_does_not_raise(  # noqa: PLR0913
    docker_executor,
    example_networks,
    example_vrfs,
    example_asn,
    add_bgp_prefix,
    remove_bgp_prefix,
    frr_container_vtysh,
    frr_container_reset_bgp_config,
):
    """Denouncing prefixes that are not announced does nothing."""
    prefix = FRRoutingPrefix(
        example_networks, vrf=example_vrfs, executor=docker_executor
    )
    # These two calls are there to ensure that a top level BGP configuration is present.
    add_bgp_prefix(
        prefix.prefix, asn=example_asn, vtysh=frr_container_vtysh, vrf=example_vrfs
    )
    remove_bgp_prefix(
        prefix.prefix, asn=example_asn, vtysh=frr_container_vtysh, vrf=example_vrfs
    )

    await prefix.denounce()


@skip_without_docker
@pytest.mark.parametrize("announced", [True, False])
async def test_announcement_state_reported_correctly(  # noqa: PLR0913
    frr_container_vtysh,
    frr_container_reset_bgp_config,
    docker_executor,
    example_networks,
    example_vrfs,
    example_asn,
    add_bgp_prefix,
    announced: bool,
):
    """The announcement state is reported correctly."""
    prefix = FRRoutingPrefix(
        example_networks, vrf=example_vrfs, executor=docker_executor
    )
    if announced:
        add_bgp_prefix(
            prefix.prefix, asn=example_asn, vtysh=frr_container_vtysh, vrf=example_vrfs
        )

    assert await prefix.is_announced() == announced
