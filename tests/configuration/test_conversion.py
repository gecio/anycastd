import datetime
from ipaddress import IPv6Network
from pathlib import Path

import pytest
from anycastd._configuration.conversion import (
    _sub_config_to_instance,
    dict_w_items_named_by_key_to_flat_w_name_value,
)
from anycastd._configuration.healthcheck import (
    CabourotteHealthcheckConfiguration,
    HealthcheckConfiguration,
)
from anycastd._configuration.prefix import FRRPrefixConfiguration, PrefixConfiguration
from anycastd._executor import LocalExecutor
from anycastd.healthcheck import CabourotteHealthcheck, Healthcheck
from anycastd.prefix import FRRoutingPrefix, Prefix


@pytest.mark.parametrize(
    "config,expected",
    [
        (
            CabourotteHealthcheckConfiguration(
                name="test cabourotte healthcheck",
                url="http://[::]:9013",
                interval=datetime.timedelta(minutes=1),
            ),
            CabourotteHealthcheck(
                name="test cabourotte healthcheck",
                url="http://[::]:9013",
                interval=datetime.timedelta(minutes=1),
            ),
        ),
        (
            FRRPrefixConfiguration(
                prefix=IPv6Network("2001:db8::/32"),
                vrf="77",
                vtysh=Path("/run/vtysh"),
            ),
            FRRoutingPrefix(
                prefix=IPv6Network("2001:db8::/32"),
                vrf="77",
                vtysh=Path("/run/vtysh"),
                executor=LocalExecutor(),
            ),
        ),
    ],
)
def test_subconfiguration_converted_to_instance(
    config: PrefixConfiguration | HealthcheckConfiguration,
    expected: Prefix | Healthcheck,
):
    """A subconfiguration can be converted to an instance of the type it represents."""
    converted = _sub_config_to_instance(config)
    assert converted == expected


def test_dict_w_named_to_flat_w_name_value():
    """Dictionaries with named items can be converted to flat dictionaries."""
    named = {"foo": {"bar": "baz"}, "qux": {"quux": "corge"}}
    expected = ({"name": "foo", "bar": "baz"}, {"name": "qux", "quux": "corge"})

    converted = dict_w_items_named_by_key_to_flat_w_name_value(named)

    assert converted == expected
