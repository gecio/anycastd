from pathlib import Path

import pytest
import tomli_w


@pytest.fixture
def sample_configuration_file(fs) -> tuple[Path, dict]:
    """A valid sample configuration file.

    Creates a valid sample configuration file within a mocked filesystem.

    Returns:
        The path to the created configuration file as well as expected parsed data.
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
