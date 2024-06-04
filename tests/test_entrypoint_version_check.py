"""Test the Python version check made by the entrypoint."""

import anycastd.__main__
import pytest

MIN_PYTHON_VERSION = (3, 11)


@pytest.mark.parametrize("supported_version", [MIN_PYTHON_VERSION, (3, 12)])
def test_supported_python_version_runs_app(mocker, supported_version: tuple[int, int]):
    """The CLI app is run on a supported Python version."""
    mocker.patch("sys.version_info", supported_version)
    mock_app = mocker.patch("anycastd._cli.app")

    anycastd.__main__.run()

    mock_app.assert_called_once()


@pytest.mark.parametrize("unsupported_version", [(3, 8), (3, 9), (3, 10)])
def test_unsupported_python_version_exits_with_error(mocker, unsupported_version):
    """The entrypoint exits with an error on an unsupported Python version."""
    mocker.patch("sys.version_info", unsupported_version)

    with pytest.raises(
        SystemExit,
        match=f"Python >= {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} "
        r"is required.*",
    ):
        anycastd.__main__.run()
