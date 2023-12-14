import pytest
from anycastd._configuration.exceptions import ConfigurationError


def test_unexpected_exception_raises(dummy_config_path):
    """An unexpected exception raises TypeError."""
    exc = Exception("random exception")
    with pytest.raises(TypeError, match="unexpected exception occurred"):
        raise ConfigurationError(dummy_config_path, exc)  # type: ignore


@pytest.mark.parametrize(
    "exc, expected",
    [
        (
            KeyError("this_key_is_required"),
            "due to missing required key: 'this_key_is_required'",
        )
    ],
)
def test_exception_message_mapping(exc: Exception, expected: str, dummy_config_path):
    """The error contains the correct message for the underlying error."""
    with pytest.raises(
        ConfigurationError,
        match=f"Could not read from configuration file {dummy_config_path} {expected}",
    ):
        try:
            raise exc
        except Exception as raised_excpection:
            raise ConfigurationError(
                dummy_config_path, raised_excpection
            ) from raised_excpection