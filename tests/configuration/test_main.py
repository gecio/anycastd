from pathlib import Path

import pytest
from anycastd._configuration.exceptions import ConfigurationError
from anycastd._configuration.main import MainConfiguration, _read_toml_configuration


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

    @pytest.fixture
    def mock_toml_reader(self, mocker):
        """A mock for the TOML reader function."""
        return mocker.patch(
            "anycastd._configuration.main._read_toml_configuration", autospec=True
        )

    @pytest.mark.integration
    def test_initialized_from_valid_toml(
        self, sample_configuration, sample_configuration_file
    ):
        """An instance with correct values can be created from a TOML file."""
        path, _ = sample_configuration_file
        config = MainConfiguration.from_toml_file(path)
        assert config == sample_configuration

    def test_reads_toml_file(self, mock_toml_reader, dummy_config_path):
        """TOML is read from the given configuration path."""
        MainConfiguration.from_toml_file(dummy_config_path)
        mock_toml_reader.assert_called_once_with(dummy_config_path)

    def test_service_configurations_initialized_w_correct_values(
        self, mocker, mock_toml_reader, dummy_config_path
    ):
        """Service configuration instances are initialized correctly."""
        important_api_service = (
            {
                "prefixes": {"routingd": ["2001:db8::aced:a11:7e57"]},
                "checks": {
                    "healthd": [{"interval": "1s", "name": "important-API-healthy"}]
                },
            },
        )
        important_backend_service = {
            "prefixes": {"bgpd": ["2001:db8::bad:1dea"]},
            "checks": {
                "pingd": ["flaky-backend"],
            },
        }
        mock_toml_reader.return_value = {
            "services": {
                "important-API": important_api_service,
                "important-backend": important_backend_service,
            }
        }
        mock_service_config_ini = mocker.patch(
            "anycastd._configuration.main.ServiceConfiguration.from_name_and_options",
            autospec=True,
        )

        MainConfiguration.from_toml_file(dummy_config_path)

        mock_service_config_ini.assert_has_calls(
            [
                mocker.call("important-API", important_api_service),
                mocker.call("important-backend", important_backend_service),
            ]
        )

    def test_missing_key_raises_error(self, mock_toml_reader, dummy_config_path):
        """A configuration file with a missing key raises an error."""
        mock_toml_reader.return_value = {}
        with pytest.raises(ConfigurationError, match="missing required key"):
            MainConfiguration.from_toml_file(dummy_config_path)
