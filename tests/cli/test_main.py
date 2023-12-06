from pathlib import Path
from unittest.mock import MagicMock

import anycastd
import pytest


def test_version_displayed_correctly(anycastd_cli):
    """The version is displayed correctly."""
    expected = "anycastd {}\n".format(anycastd.__version__)

    result = anycastd_cli("--version")

    assert result.exit_code == 0
    assert result.stdout == expected


class TestRunCMD:
    """Test the run command."""

    @pytest.fixture
    def mock_configuration(self, mocker):
        """An autospecced mock instance of the MainConfiguration class."""
        return mocker.create_autospec(
            "anycastd._configuration.MainConfiguration", spec_set=True, instance=True
        )

    @pytest.fixture
    def mock_run_from_configuration(self, mocker) -> MagicMock:
        """An autospecced mock of the run_from_configuration function."""
        return mocker.patch("anycastd._cli.main.run_from_configuration", autospec=True)

    @pytest.fixture
    def mock_get_main_configuration(self, mocker, mock_configuration) -> MagicMock:
        """An autospecced mock of the _get_main_configuration function."""
        mock = mocker.patch("anycastd._cli.main._get_main_configuration", autospec=True)
        mock.return_value = mock_configuration
        return mock

    def test_calls_get_main_configuration_w_config_path(
        self, anycastd_cli, mock_get_main_configuration, mock_run_from_configuration
    ):
        """_get_main_configuration is called with the config path."""
        config = Path("/path/to/config.toml")

        anycastd_cli("run", "--config", config.as_posix())

        mock_get_main_configuration.assert_called_once_with(config)

    def test_calls_run_from_configuration(
        self,
        anycastd_cli,
        mock_configuration,
        mock_run_from_configuration,
        mock_get_main_configuration,
    ):
        """run_from_configuration is called.

        Run from configuration is called with the main configuration object
        obtained from the configuration file path.
        """
        anycastd_cli("run")

        mock_run_from_configuration.assert_called_once_with(mock_configuration)
