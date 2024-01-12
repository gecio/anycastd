from pathlib import Path

import pytest
from anycastd._configuration.exceptions import (
    ConfigurationFileUnreadableError,
    ConfigurationSyntaxError,
)
from anycastd._configuration.main import _read_toml_configuration


def test_valid_configuration_read_successfully(sample_configuration_file):
    """A valid configuration is read successfully.

    Given an existing TOML configuration file with valid syntax, the
    content is successfully read and parsed.
    """
    path, data = sample_configuration_file
    config = _read_toml_configuration(path)
    assert config == data


def test_unreadable_raises_error(fs):
    """An unreadable configuration file raises an error."""
    path = Path("/path/to/unreadable/config.toml")
    fs.create_file(path, 0o000)

    with pytest.raises(ConfigurationFileUnreadableError, match="Permission denied"):
        _read_toml_configuration(path)


def test_invalid_syntax_raises_error(fs):
    """A configuration file with invalid syntax raises an error."""
    path = Path("/path/to/invalid-config.toml")
    fs.create_file(path, contents="invalid")

    with pytest.raises(ConfigurationSyntaxError, match="TOML syntax error"):
        _read_toml_configuration(path)
