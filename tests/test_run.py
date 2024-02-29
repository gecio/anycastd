import asyncio
import signal

import pytest
from anycastd.core._run import run_services, signal_handler
from anycastd.core._service import Service
from structlog.testing import capture_logs


@pytest.fixture
def mock_services(mocker):
    """A set of mock services."""
    return [mocker.AsyncMock(Service) for _ in range(3)]


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
