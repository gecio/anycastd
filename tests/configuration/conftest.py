import datetime
from ipaddress import IPv4Network, IPv6Network
from pathlib import Path

import pytest
import tomli_w
from anycastd._configuration.healthcheck import CabourotteHealthcheck
from anycastd._configuration.main import MainConfiguration, ServiceConfiguration
from anycastd._configuration.prefix import FRRPrefix


@pytest.fixture
def sample_configuration() -> MainConfiguration:
    """A valid sample configuration.

    Returns:
        The configuration instance.
    """
    return MainConfiguration(
        services=(
            ServiceConfiguration(
                name="loadbalancer",
                prefixes=(
                    FRRPrefix(prefix=IPv6Network("2001:db8::aced:a11:7e57")),
                    FRRPrefix(prefix=IPv4Network("203.0.113.84")),
                ),
                checks=(CabourotteHealthcheck(name="loadbalancer"),),
            ),
            ServiceConfiguration(
                name="dns",
                prefixes=(
                    FRRPrefix(prefix=IPv6Network("2001:db8::b19:bad:53")),
                    FRRPrefix(prefix=IPv4Network("203.0.113.53")),
                ),
                checks=(
                    CabourotteHealthcheck(
                        name="dns_v4", interval=datetime.timedelta(seconds=1)
                    ),
                    CabourotteHealthcheck(
                        name="dns_v6", interval=datetime.timedelta(seconds=1)
                    ),
                ),
            ),
        )
    )


@pytest.fixture
def sample_configuration_file(fs) -> tuple[Path, dict]:
    """A valid sample configuration file.

    Creates a configuration file within a mocked filesystem based
    on the above sample configuration.

    Returns:
        The path to the created configuration file as well as it's configuration data.
    """
    path = Path("/path/to/config.toml")
    data = {
        "services": {
            "loadbalancer": {
                "prefixes": {"frrouting": ["2001:db8::aced:a11:7e57", "203.0.113.84"]},
                "checks": {"cabourotte": ["loadbalancer"]},
            },
            "dns": {
                "prefixes": {"frrouting": ["2001:db8::b19:bad:53", "203.0.113.53"]},
                "checks": {
                    "cabourotte": [
                        {"name": "dns_v4", "interval": 1},
                        {"name": "dns_v6", "interval": 1},
                    ]
                },
            },
        }
    }
    fs.create_file(path, contents=tomli_w.dumps(data))

    return path, data


@pytest.fixture
def dummy_config_path() -> Path:
    """A dummy configuration path that does not really exist."""
    return Path("/dummy/test/configuration/path")
