import asyncio
import signal

import pytest
from anycastd.core._run import run_services, signal_handler
from anycastd.core._service import Service
from structlog.testing import capture_logs


@pytest.fixture
def mock_services(mocker):
    """A set of mock services."""
    mock_services = []
    for num in range(3):
        mock_service = mocker.create_autospec(Service)
        mock_service.name = f"Mock Service {num + 1}"
        mock_services.append(mock_service)

    return mock_services


@pytest.fixture
def mock_sys(mocker):
    """A mock sys module."""
    return mocker.patch("anycastd.core._run.sys")


async def test_future_created_for_each_service(mock_services):
    """A future is created for each service."""
    await run_services(mock_services)
    assert all(mock_service.run.called for mock_service in mock_services)


@pytest.mark.parametrize("signal_to_handle", [signal.SIGTERM, signal.SIGINT])
async def test_run_services_installs_signal_handlers(
    mocker, mock_services, signal_to_handle: signal.Signals
):
    """A handler is installed for signals we want to handle."""
    mock_loop = mocker.create_autospec(asyncio.AbstractEventLoop)
    mocker.patch("anycastd.core._run.asyncio.get_event_loop", return_value=mock_loop)

    await run_services(mock_services)

    assert (
        mocker.call(signal_to_handle, mocker.ANY)
        in mock_loop.add_signal_handler.mock_calls
    )


def test_signal_handler_logs_signal(mocker):
    """The signal handler logs the received signal."""
    mocker.patch("anycastd.core._run.asyncio")
    mocker.patch("anycastd.core._run.sys")

    with capture_logs() as logs:
        signal_handler(signal.SIGTERM)

    assert logs[0]["event"] == "Received SIGTERM, terminating."
    assert logs[0]["log_level"] == "info"


def test_signal_handler_cancels_all_tasks(mocker):
    """The signal handler cancels all tasks."""
    tasks = [mocker.create_autospec(asyncio.Task) for _ in range(3)]
    mocker.patch("anycastd.core._run.asyncio.all_tasks", return_value=tasks)
    mocker.patch("anycastd.core._run.sys")

    signal_handler(signal.SIGTERM)

    for task in tasks:
        task.cancel.assert_called_once_with("Received SIGTERM, terminating.")


def test_signal_handler_exits_with_zero(mocker):
    """The signal handler exits with returncode zero."""
    mocker.patch("anycastd.core._run.asyncio")
    mock_sys = mocker.patch("anycastd.core._run.sys")

    signal_handler(signal.SIGTERM)

    mock_sys.exit.assert_called_once_with(0)


async def test_unexpected_service_error_exits_with_software_rc(mock_sys, mock_services):
    """An unexpected service error causes an exit with software(70) error code."""
    for service in mock_services:
        service.run.side_effect = Exception("An unexpected error.")

    await run_services(mock_services)

    assert int(mock_sys.exit.mock_calls[0].args[0]) == 70  # noqa: PLR2004


async def test_unexpected_service_error_logs_error(mocker, mock_sys, mock_services):
    """Unexpected service errors are logged.

    This test uses three mocked services, where the first and third service
    raise an "unexpected" error. The expected behavior is that both errors are logged,
    as well as a message indicating that the daemon panicked as a whole and that
    prefixes may be left in an unwanted state.
    """
    service_one_name = "Example One"
    service_one_exc = Exception("An unexpected error in the first service.")
    service_three_name = "Example Three"
    service_three_exc = Exception("An unexpected error in the third service.")
    mock_services[0].name = service_one_name
    mock_services[0].run.side_effect = service_one_exc
    mock_services[2].name = service_three_name
    mock_services[2].run.side_effect = service_three_exc

    with capture_logs() as logs:
        await run_services(mock_services)

    assert (
        logs[0]["event"] == f'Service "{service_one_name}" encountered an unexpected '
        "and unrecoverable error."
    )
    assert logs[0]["log_level"] == "error"
    assert logs[0]["service_name"] == service_one_name
    assert logs[0]["exc_info"] == service_one_exc

    assert (
        logs[1]["event"] == f'Service "{service_three_name}" encountered an unexpected '
        "and unrecoverable error."
    )
    assert logs[1]["log_level"] == "error"
    assert logs[1]["service_name"] == service_three_name
    assert logs[1]["exc_info"] == service_three_exc

    assert logs[2]["event"] == (
        "Panicked without correctly shutting down services due to unexpected error(s), "
        "possibly leaving prefixes in an unwanted state. Please remediate manually."
    )
    assert logs[2]["log_level"] == "error"
