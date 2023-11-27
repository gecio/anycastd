import datetime
from ipaddress import IPv4Network, IPv6Network
from pathlib import Path
from types import ModuleType

import pytest
from anycastd._configuration import healthcheck, prefix
from anycastd._configuration.sub import SubConfiguration


@pytest.mark.parametrize(
    "config, expected",
    [
        (
            "example-healthcheck",
            healthcheck.CabourotteHealthcheck(name="example-healthcheck"),
        ),
        ("192.0.2.0/24", prefix.FRRPrefix(prefix=IPv4Network("192.0.2.0/24"))),
        ("2001:db8::/32", prefix.FRRPrefix(prefix=IPv6Network("2001:db8::/32"))),
    ],
)
def test_from_simplified_format(config: str, expected: SubConfiguration):
    """The sub-configuration can be created from it's simplified format.

    A sub-configuration can be created using it's simplified format,
    a string containing the only required option.
    """
    type_ = type(expected)
    result = type_.from_configuration(config)
    assert result == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        (
            {
                "name": "example-healthcheck",
                "url": "http://healthchecks.local",
                "interval": 8,
            },
            healthcheck.CabourotteHealthcheck(
                name="example-healthcheck",
                url="http://healthchecks.local",
                interval=datetime.timedelta(seconds=8),
            ),
        ),
        (
            {
                "prefix": "2001:db8::/32",
                "vrf": 42,
                "vtysh": "/vtysh",
            },
            prefix.FRRPrefix(
                prefix=IPv6Network("2001:db8::/32"),
                vrf=42,
                vtysh=Path("/vtysh"),
            ),
        ),
    ],
)
def test_from_expanded_format(config: dict, expected: SubConfiguration):
    """The sub-configuration can be created from it's full, expanded format.

    A sub-configuration can be created using it's full, expanded format,
    a dictionary containing at least all required options.
    """
    type_ = type(expected)
    result = type_.from_configuration(config)
    assert result == expected


class TestGetByName:
    """The get_type_by_name function works correctly for each config module."""

    @pytest.mark.parametrize(
        "module, name, expected",
        [
            (prefix, "frrouting", prefix.FRRPrefix),
            (healthcheck, "cabourotte", healthcheck.CabourotteHealthcheck),
        ],
    )
    def test_name_returns_correct_type(
        self, module: ModuleType, name: str, expected: type[SubConfiguration]
    ):
        """The correct type is returned for a given name."""
        assert module.get_type_by_name(name) == expected

    @pytest.mark.parametrize(
        "module, kind",
        [
            (prefix, "prefix"),
            (healthcheck, "healthcheck"),
        ],
    )
    def test_unknown_name_raises_error(self, module: ModuleType, kind: str):
        """An unknown name raises a ValueError."""
        name = "invalid"
        with pytest.raises(ValueError, match=f"Unknown {kind} type: {name}"):
            module.get_type_by_name(name)
