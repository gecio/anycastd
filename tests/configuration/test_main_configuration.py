import pytest
from anycastd._configuration.exceptions import ConfigurationSyntaxError
from anycastd._configuration.main import MainConfiguration


def test_initialized_from_valid_toml(sample_configuration, sample_configuration_file):
    """An instance with correct values can be created from a TOML file."""
    path, _ = sample_configuration_file
    config = MainConfiguration.from_toml_file(path)
    assert config == sample_configuration


def test_missing_required_top_level_field_raises(sample_configuration_dict):
    """Exception raised when a required top-level field is missing."""
    expected = r".*missing required key 'services'.*"
    del sample_configuration_dict["services"]

    with pytest.raises(ConfigurationSyntaxError, match=expected):
        MainConfiguration.from_configuration_dict(sample_configuration_dict)
