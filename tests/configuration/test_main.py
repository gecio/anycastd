from pathlib import Path

import pytest
from anycastd.configuration.exceptions import ConfigurationError
from anycastd.configuration.main import MainConfiguration, _read_toml_configuration


def test_valid_configuration_read_successfully(sample_configuration_file):
    """A valid configuration is read sucessfully.

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

    with pytest.raises(ConfigurationError, match="Permission denied"):
        _read_toml_configuration(path)


def test_invalid_syntax_raises_error(fs):
    """A configuration file with invalid syntax raises an error."""
    path = Path("/path/to/invalid-config.toml")
    fs.create_file(path, contents="invalid")

    with pytest.raises(ConfigurationError, match="TOML syntax error"):
        _read_toml_configuration(path)


class TestMainConfiguration:
    """Tests for the MainConfiguration class."""

    @pytest.mark.integration
    def test_initialized_from_valid_toml(
        self, sample_configuration, sample_configuration_file
    ):
        """An instance with correct values can be created from a TOML file."""
        path, _ = sample_configuration_file
        config = MainConfiguration.from_toml_file(path)
        assert config == sample_configuration
