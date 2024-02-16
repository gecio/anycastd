import pytest
from anycastd.core._run import run_services
from anycastd.core._service import Service


@pytest.fixture
def mock_services(mocker):
    """A set of mock services."""
    return [mocker.AsyncMock(Service) for _ in range(3)]


async def test_future_created_for_each_service(mock_services):
    """A future is created for each service."""
    await run_services(mock_services)
    assert all(mock_service.run.called for mock_service in mock_services)
