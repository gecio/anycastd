import pytest
from anycastd._configuration.exceptions import ConfigurationError


def test_unexpected_exception_raises(dummy_config_path):
    """An unexpected exception raises TypeError."""
    exc = Exception("random exception")
    with pytest.raises(TypeError, match="unexpected exception occurred"):
        raise ConfigurationError(dummy_config_path, exc)  # type: ignore
