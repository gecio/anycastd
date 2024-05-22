"""Ensure that FRRouting behavior we depend on does not change in future versions."""

import pytest

from tests.conftest import skip_without_docker

pytestmark = [pytest.mark.integration, pytest.mark.frrouting_daemon_required]


@skip_without_docker
def test_announcing_prefix_that_is_announced_is_successful(  # noqa: PLR0913
    frr_container_vtysh,
    frr_container_reset_bgp_config,
    example_networks,
    example_vrfs,
    example_asn,
    add_bgp_prefix,
):
    """
    A prefix can be announced again without error, even if it is already announced.
    """
    add_bgp_prefix(
        example_networks, asn=example_asn, vtysh=frr_container_vtysh, vrf=example_vrfs
    )

    result = add_bgp_prefix(
        example_networks, asn=example_asn, vtysh=frr_container_vtysh, vrf=example_vrfs
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@skip_without_docker
async def test_denouncing_prefix_that_is_not_announced_returns_expected_rc_and_stdout(  # noqa: PLR0913
    frr_container_vtysh,
    frr_container_reset_bgp_config,
    example_networks,
    example_vrfs,
    example_asn,
    bgp_prefix_configured,
    remove_bgp_prefix,
):
    """
    When denouncing a prefix that is not announced, vtysh exits with a return
    code of 1 and prints an expected error message to stdout.
    """
    assert not bgp_prefix_configured(
        example_networks, vtysh=frr_container_vtysh, vrf=example_vrfs
    )

    result = remove_bgp_prefix(
        example_networks,
        asn=example_asn,
        vtysh=frr_container_vtysh,
        vrf=example_vrfs,
        check=False,
    )

    assert result.returncode == 1
    assert "Can't find static route specified" in result.stdout
    assert result.stderr == ""
