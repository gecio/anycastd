import pytest
from anycastd._configuration.core import MainConfiguration
from anycastd._configuration.exceptions import ConfigurationError


@pytest.fixture
def mock_toml_reader(mocker):
    """A mock for the TOML reader function."""
    return mocker.patch(
        "anycastd._configuration.core._read_toml_configuration", autospec=True
    )


@pytest.mark.integration
def test_initialized_from_valid_toml(sample_configuration, sample_configuration_file):
    """An instance with correct values can be created from a TOML file."""
    path, _ = sample_configuration_file
    config = MainConfiguration.from_toml_file(path)
    assert config == sample_configuration


def test_reads_toml_file(mock_toml_reader, dummy_config_path):
    """TOML is read from the given configuration path."""
    MainConfiguration.from_toml_file(dummy_config_path)
    mock_toml_reader.assert_called_once_with(dummy_config_path)


def test_service_configurations_initialized_w_correct_values(
    mocker, mock_toml_reader, dummy_config_path
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
        "anycastd._configuration.service.ServiceConfiguration.from_name_and_options",
        autospec=True,
    )
    MainConfiguration.from_toml_file(dummy_config_path)
    mock_service_config_ini.assert_has_calls(
        [
            mocker.call("important-API", important_api_service),
            mocker.call("important-backend", important_backend_service),
        ]
    )


def test_missing_key_raises_error(mock_toml_reader, dummy_config_path):
    """A configuration file with a missing key raises an error."""
    mock_toml_reader.return_value = {}
    with pytest.raises(ConfigurationError, match="missing required key"):
        MainConfiguration.from_toml_file(dummy_config_path)
