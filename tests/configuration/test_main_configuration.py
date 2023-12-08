from anycastd._configuration.main import MainConfiguration


def test_initialized_from_valid_toml(sample_configuration, sample_configuration_file):
    """An instance with correct values can be created from a TOML file."""
    path, _ = sample_configuration_file
    config = MainConfiguration.from_toml_file(path)
    assert config == sample_configuration
