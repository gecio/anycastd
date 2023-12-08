import pytest
from anycastd._configuration.main import MainConfiguration


def test_initialized_from_valid_toml(sample_configuration, sample_configuration_file):
    """An instance with correct values can be created from a TOML file."""
    path, _ = sample_configuration_file
    config = MainConfiguration.from_toml_file(path)
    assert config == sample_configuration


def test_service_configurations_initialized_w_correct_values(mocker):
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
    config = {
        "services": {
            "important-API": important_api_service,
            "important-backend": important_backend_service,
        }
    }
    mock_service_config_ini = mocker.patch(
        "anycastd._configuration.service.ServiceConfiguration.from_name_and_options",
        autospec=True,
    )
    MainConfiguration._from_dict(config)
    mock_service_config_ini.assert_has_calls(
        [
            mocker.call("important-API", important_api_service),
            mocker.call("important-backend", important_backend_service),
        ]
    )


def test_missing_key_raises_error():
    """A configuration with a missing key raises a KeyError."""
    config = {}
    with pytest.raises(KeyError):
        MainConfiguration._from_dict(config)
