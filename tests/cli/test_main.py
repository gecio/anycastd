import logging
from pathlib import Path
from unittest.mock import MagicMock

import anycastd
import pytest
import structlog
from anycastd._cli.main import _get_main_configuration
from structlog.testing import capture_logs


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

    @pytest.mark.parametrize(
        "arg, level",
        [
            ("debug", logging.DEBUG),
            ("info", logging.INFO),
            ("warning", logging.WARNING),
            ("error", logging.ERROR),
        ],
    )
    def test_log_level_configures_structlog(self, anycastd_cli, arg: str, level: int):
        """Structlog is configured with the correct log level filter."""
        anycastd_cli("run", "--log-level", arg)
        wrapper_class = structlog.get_config()["wrapper_class"]
        assert wrapper_class == structlog.make_filtering_bound_logger(level)

    @pytest.mark.parametrize(
        "arg, processor",
        [
            ("human", structlog.dev.ConsoleRenderer),
            ("json", structlog.processors.JSONRenderer),
            ("logfmt", structlog.processors.LogfmtRenderer),
        ],
    )
    def test_log_format_configures_structlog(self, anycastd_cli, arg: str, processor):
        """Structlog is configured with the correct rendering processor.

        Structlog is configured with a rendering processor matching the specified
        log format as the last processor.
        """
        anycastd_cli("run", "--log-format", arg)
        last_processor = structlog.get_config()["processors"][-1]
        assert isinstance(last_processor, processor)


def test_reading_configuration_is_logged(mocker):
    """Reading the configuration is logged."""
    path = Path("/path/to/config.toml")
    mocker.patch("anycastd._cli.main.MainConfiguration", autospec=True)

    with capture_logs() as logs:
        _get_main_configuration(path)

    assert logs[0]["event"] == f"Reading configuration from {path.as_posix()}."
    assert logs[0]["log_level"] == "info"
    assert logs[0]["config_path"] == path.as_posix()
    assert (
        logs[1]["event"] == f"Successfully read configuration file {path.as_posix()}."
    )
    assert logs[1]["log_level"] == "debug"
    assert logs[1]["config_path"] == path.as_posix()
