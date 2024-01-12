import datetime
from ipaddress import IPv4Network, IPv6Network
from pathlib import Path
from types import ModuleType

import pytest
from anycastd._configuration import healthcheck, prefix
from anycastd._configuration.exceptions import ConfigurationSyntaxError
from anycastd._configuration.healthcheck import CabourotteHealthcheckConfiguration
from anycastd._configuration.prefix import FRRPrefixConfiguration
from anycastd._configuration.sub import SubConfiguration


@pytest.mark.parametrize(
    "config, expected",
    [
        (
            "example-healthcheck",
            CabourotteHealthcheckConfiguration(name="example-healthcheck"),
        ),
        (
            "192.0.2.0/24",
            FRRPrefixConfiguration(prefix=IPv4Network("192.0.2.0/24")),
        ),
        (
            "2001:db8::/32",
            FRRPrefixConfiguration(prefix=IPv6Network("2001:db8::/32")),
        ),
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
            CabourotteHealthcheckConfiguration(
                name="example-healthcheck",
                url="http://healthchecks.local",
                interval=datetime.timedelta(seconds=8),
            ),
        ),
        (
            {
                "prefix": "2001:db8::/32",
                "vrf": "42",
                "vtysh": "/vtysh",
            },
            FRRPrefixConfiguration(
                prefix=IPv6Network("2001:db8::/32"),
                vrf="42",
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


def test_from_simple_when_multiple_required_fields_raises():
    """Exception raised when multiple fields are required but only a string is given."""

    class MultipleRequiredFields(SubConfiguration):
        first_required_field: str
        second_required_field: str

    value = "value for first field"
    expected = (
        r".*invalid configuration value type for MultipleRequiredFields: "
        "expecting a dictionary containing the fields "
        r"first_required_field, second_required_field.*"
    )

    with pytest.raises(ConfigurationSyntaxError, match=expected):
        MultipleRequiredFields.from_configuration(value)


def test_unknown_field_raises():
    """Exception raised when an unknown field is given."""

    class InvalidField(SubConfiguration):
        required_field: str

    config = {"required_field": "value", "non_existent_field": "value"}
    expected = "invalid field 'non_existent_field'"

    with pytest.raises(ConfigurationSyntaxError, match=expected):
        InvalidField.from_configuration(config)


def test_invalid_field_type_raises():
    """Exception raised when a field has an invalid type."""

    class InvalidFieldType(SubConfiguration):
        must_be_float: float

    name = "must_be_float"
    input = "but is str"
    config = {name: input}
    expected = (
        rf".*invalid input '{input}' for field '{name}': .*should be a valid number.*"
    )

    with pytest.raises(ConfigurationSyntaxError, match=expected):
        InvalidFieldType.from_configuration(config)


def test_missing_required_field_raises():
    """Exception raised when a required field is missing."""

    class MultipleRequiredFields(SubConfiguration):
        first_required_field: str
        second_required_field: str

    config = {"second_required_field": "foo"}
    expected = r".*missing required field 'first_required_field'"

    with pytest.raises(ConfigurationSyntaxError, match=expected):
        MultipleRequiredFields.from_configuration(config)


class TestGetByName:
    """The get_type_by_name function works correctly for each config module."""

    @pytest.mark.parametrize(
        "module, name, expected",
        [
            (prefix, "frrouting", FRRPrefixConfiguration),
            (healthcheck, "cabourotte", CabourotteHealthcheckConfiguration),
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
