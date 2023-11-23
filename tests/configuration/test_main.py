from pathlib import Path

import pytest
import tomli_w
from anycastd.configuration.exceptions import ConfigurationError
from anycastd.configuration.main import _read_toml_configuration


@pytest.fixture
def sample_configuration(fs) -> tuple[Path, dict]:
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
                        {"name": "dns_v4", "interval": "1s"},
                        {"name": "dns_v6", "interval": "1s"},
                    ]
                },
            },
        }
    }
    fs.create_file(path, contents=tomli_w.dumps(data))

    return path, data


def test_valid_configuration_read_successfully(sample_configuration):
    """A valid configuration is read sucessfully.

    Given an existing TOML configuration file with valid syntax, the
    content is successfully read and parsed.
    """
    path, data = sample_configuration
    config = _read_toml_configuration(path)
    assert config == data


def test_unreadable_raises_error(fs):
    """An unreadable configuration file raises an error."""
    path = Path("/path/to/unreadable/config.toml")
    fs.create_file(path, 0o000)

    with pytest.raises(ConfigurationError, match="Permission denied"):
        _read_toml_configuration(path)


def test_invalid_syntax_raises_error(fs):
    """A configuration file with invalid syntax raises an error."""
    path = Path("/path/to/invalid-config.toml")
    fs.create_file(path, contents="invalid")

    with pytest.raises(ConfigurationError, match="TOML syntax error"):
        _read_toml_configuration(path)
