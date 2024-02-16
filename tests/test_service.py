import pytest
from anycastd.core import Service
from pytest_mock import MockerFixture

from tests.dummy import DummyHealthcheck, DummyPrefix


@pytest.fixture
def example_service(ipv4_example_network, ipv6_example_network):
    return Service(
        name="Example Service",
        prefixes=(DummyPrefix(ipv4_example_network), DummyPrefix(ipv6_example_network)),
        health_checks=(DummyHealthcheck(), DummyHealthcheck()),
    )


async def test_run_awaits_status(mocker: MockerFixture, example_service):
    """When run, the service awaits the status of the health checks."""
    mock_is_healthy = mocker.patch.object(example_service, "is_healthy")
    await example_service.run(_only_once=True)
    mock_is_healthy.assert_awaited_once()


async def test_run_announces_when_healthy(mocker: MockerFixture, example_service):
    """When run, all prefixes are announced when the service is healthy."""
    mocker.patch.object(example_service, "is_healthy", return_value=True)
    mock_prefixes = tuple(
        mocker.create_autospec(_, spec_set=True) for _ in example_service.prefixes
    )
    mocker.patch.object(example_service, "prefixes", mock_prefixes)
    await example_service.run(_only_once=True)
    for mock_prefix in mock_prefixes:
        mock_prefix.announce.assert_awaited_once()


async def test_run_denounces_when_unhealthy(mocker: MockerFixture, example_service):
    """When run, all prefixes are denounced when the service is unhealthy."""
    mocker.patch.object(example_service, "is_healthy", return_value=False)
    mock_prefixes = tuple(
        mocker.create_autospec(_, spec_set=True) for _ in example_service.prefixes
    )
    mocker.patch.object(example_service, "prefixes", mock_prefixes)
    await example_service.run(_only_once=True)
    for mock_prefix in mock_prefixes:
        mock_prefix.denounce.assert_awaited_once()


async def test_healthy_when_all_checks_healthy(mocker: MockerFixture, example_service):
    """The service is healthy if all healthchecks are healthy."""
    mock_health_checks = tuple(
        mocker.create_autospec(_, spec_set=True) for _ in example_service.health_checks
    )
    mocker.patch.object(example_service, "health_checks", mock_health_checks)
    for mock_health_check in mock_health_checks:
        mock_health_check.is_healthy.return_value = True
    result = await example_service.is_healthy()
    assert result is True


async def test_unhealthy_when_one_check_unhealthy(
    mocker: MockerFixture, example_service
):
    """The service is unhealthy if one healthcheck is unhealthy."""
    mock_health_checks = tuple(
        mocker.create_autospec(_, spec_set=True) for _ in example_service.health_checks
    )
    mocker.patch.object(example_service, "health_checks", mock_health_checks)
    for mock_health_check in mock_health_checks:
        mock_health_check.is_healthy.return_value = True
    mock_health_checks[1].is_healthy.return_value = False
    result = await example_service.is_healthy()
    assert result is False


async def test_unhealthy_when_all_checks_unhealthy(
    mocker: MockerFixture, example_service
):
    """The service is unhealthy if all healthchecks are unhealthy."""
    mock_health_checks = tuple(
        mocker.create_autospec(_, spec_set=True) for _ in example_service.health_checks
    )
    mocker.patch.object(example_service, "health_checks", mock_health_checks)
    for mock_health_check in mock_health_checks:
        mock_health_check.is_healthy.return_value = False
    result = await example_service.is_healthy()
    assert result is False
