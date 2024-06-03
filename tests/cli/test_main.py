import logging
import re
from pathlib import Path
from unittest.mock import MagicMock

import anycastd
import pytest
import structlog
from anycastd._cli.main import _get_main_configuration
from structlog.testing import capture_logs

RE_ISO_TIMESTAMP = (
    r"(\d{4})-(\d{2})-(\d{2})"  # date
    r"T(\d{2}):(\d{2}):(\d{2}(?:\.\d*)?)((-(\d{2}):(\d{2})|Z)?)"  # time
)


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

    @pytest.mark.parametrize("is_tty", [True, False])
    def test_no_tty_configures_structlog_console_without_colors(
        self, mocker, anycastd_cli, is_tty: bool
    ):
        """
        When not running in a TTY, the structlog console renderer is configured
        to not use color codes.
        """
        mocker.patch("anycastd._cli.main.IS_TTY", new=is_tty)
        mock_console_renderer = mocker.patch(
            "anycastd._cli.main.structlog.dev.ConsoleRenderer", autospec=True
        )
        # needs to be patched since structlog does not like the mocked renderer above
        mocker.patch("anycastd._cli.main.structlog.configure")

        anycastd_cli("run", "--log-format", "human")

        mock_console_renderer.assert_called_once_with(colors=is_tty)

    @pytest.mark.parametrize("no_color", [True, False])
    def test_no_color_configures_structlog_console_without_colors(
        self, mocker, anycastd_cli, no_color: bool
    ):
        """
        When passing the --no-color argument, the structlog console renderer
        is configured to not use color codes.
        """
        # If this is false, no colors are used regardless of the --no-color argument
        mocker.patch("anycastd._cli.main.IS_TTY", new=True)
        mock_console_renderer = mocker.patch(
            "anycastd._cli.main.structlog.dev.ConsoleRenderer", autospec=True
        )
        # needs to be patched since structlog does not like the mocked renderer above
        mocker.patch("anycastd._cli.main.structlog.configure")
        args = ["run", "--log-format", "human"]
        if no_color:
            args.append("--no-color")

        anycastd_cli(*args)

        mock_console_renderer.assert_called_once_with(colors=not no_color)

    @pytest.mark.parametrize(
        "log_format, expected_first_line, env_overrides",
        [
            (
                "human",
                re.compile(
                    r"^"
                    rf"{RE_ISO_TIMESTAMP}"
                    r"\s\[info\s*\]"  # log level
                    r"\sReading configuration from /etc/anycastd/config.toml."  # event
                    r"\sconfig_path=/etc/anycastd/config.toml"  # config path
                    r"$"
                ),
                {"NO_COLOR": "TRUE"},
            ),
            (
                "json",
                re.compile(
                    r"^{"
                    r'"config_path":"/etc/anycastd/config.toml",'
                    r'"event":"Reading configuration from /etc/anycastd/config.toml.",'
                    r'"level":"info",'
                    rf'"timestamp":"{RE_ISO_TIMESTAMP}"'
                    r"}$"
                ),
                None,
            ),
            (
                "logfmt",
                re.compile(
                    r"^"
                    r"config_path=/etc/anycastd/config.toml"
                    r'\sevent="Reading configuration from /etc/anycastd/config.toml."'
                    r"\slevel=info"
                    rf"\stimestamp={RE_ISO_TIMESTAMP}"
                    r"$"
                ),
                None,
            ),
        ],
    )
    def test_log_output_renders_correctly(
        self,
        anycastd_cli,
        log_format: str,
        expected_first_line: re.Pattern,
        env_overrides: dict[str, str] | None,
    ):
        """The first log line is rendered correctly."""
        result = anycastd_cli("run", "--log-format", log_format, env=env_overrides)
        output_lines = result.stdout.splitlines()
        assert re.fullmatch(expected_first_line, output_lines[0])


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
