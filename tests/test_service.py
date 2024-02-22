import pytest
from anycastd.core import Service
from pytest_mock import MockerFixture
from structlog.testing import capture_logs

from tests.dummy import DummyHealthcheck, DummyPrefix


@pytest.fixture
def example_service(ipv4_example_network, ipv6_example_network):
    return Service(
        name="Example Service",
        prefixes=(DummyPrefix(ipv4_example_network), DummyPrefix(ipv6_example_network)),
        health_checks=(DummyHealthcheck(), DummyHealthcheck()),
    )


@pytest.fixture
def example_service_w_mock_prefixes(mocker: MockerFixture, example_service) -> Service:
    """The example service with prefixes replaced by autospecced mocks."""
    mock_prefixes = tuple(
        mocker.create_autospec(_, spec_set=True) for _ in example_service.prefixes
    )
    mocker.patch.object(example_service, "prefixes", mock_prefixes)
    return example_service


@pytest.fixture
def example_service_w_mock_checks(mocker: MockerFixture, example_service) -> Service:
    """The example service with health checks replaced by autospecced mocks."""
    mock_health_checks = tuple(
        mocker.create_autospec(_, spec_set=True) for _ in example_service.health_checks
    )
    mocker.patch.object(example_service, "health_checks", mock_health_checks)
    return example_service


async def test_run_awaits_status(mocker: MockerFixture, example_service):
    """When run, the service awaits the status of the health checks."""
    mock_is_healthy = mocker.patch.object(example_service, "is_healthy")
    await example_service.run(_only_once=True)
    mock_is_healthy.assert_awaited_once()


async def test_run_announces_when_healthy(
    mocker: MockerFixture, example_service_w_mock_prefixes
):
    """When run, all prefixes are announced when the service is healthy."""
    mocker.patch.object(
        example_service_w_mock_prefixes, "is_healthy", return_value=True
    )
    await example_service_w_mock_prefixes.run(_only_once=True)
    for mock_prefix in example_service_w_mock_prefixes.prefixes:
        mock_prefix.announce.assert_awaited_once()


async def test_run_denounces_when_unhealthy(
    mocker: MockerFixture, example_service_w_mock_prefixes
):
    """When run, all prefixes are denounced when the service is unhealthy."""
    mocker.patch.object(
        example_service_w_mock_prefixes, "is_healthy", return_value=False
    )
    await example_service_w_mock_prefixes.run(_only_once=True)
    for mock_prefix in example_service_w_mock_prefixes.prefixes:
        mock_prefix.denounce.assert_awaited_once()


async def test_healthy_when_all_checks_healthy(example_service_w_mock_checks):
    """The service is healthy if all healthchecks are healthy."""
    for mock_health_check in example_service_w_mock_checks.health_checks:
        mock_health_check.is_healthy.return_value = True
    result = await example_service_w_mock_checks.is_healthy()
    assert result is True


async def test_unhealthy_when_one_check_unhealthy(example_service_w_mock_checks):
    """The service is unhealthy if one healthcheck is unhealthy."""
    for mock_health_check in example_service_w_mock_checks.health_checks:
        mock_health_check.is_healthy.return_value = True
    example_service_w_mock_checks.health_checks[1].is_healthy.return_value = False
    result = await example_service_w_mock_checks.is_healthy()
    assert result is False


async def test_unhealthy_when_all_checks_unhealthy(example_service_w_mock_checks):
    """The service is unhealthy if all healthchecks are unhealthy."""
    for mock_health_check in example_service_w_mock_checks.health_checks:
        mock_health_check.is_healthy.return_value = False
    result = await example_service_w_mock_checks.is_healthy()
    assert result is False


async def test_unhealthy_when_check_raises(example_service_w_mock_checks):
    """The service is unhealthy if a healthcheck raises an exception."""
    # All checks return a healthy status
    for mock_health_check in example_service_w_mock_checks.health_checks:
        mock_health_check.is_healthy.return_value = True
    # Except for one raising an exception
    example_service_w_mock_checks.health_checks[1].is_healthy.side_effect = Exception
    result = await example_service_w_mock_checks.is_healthy()
    assert result is False


async def test_exception_raised_by_check_logged(
    example_service, example_service_w_mock_checks
):
    """When a healthcheck raises an exception, it is logged."""
    check_exc = Exception("An error occurred while executing the health check.")
    example_service_w_mock_checks.health_checks[1].is_healthy.side_effect = check_exc

    with capture_logs() as logs:
        await example_service_w_mock_checks.is_healthy()

    assert (
        logs[0]["event"]
        == "An unhandled exception occurred while running a health check."
    )
    assert logs[0]["log_level"] == "error"
    assert logs[0]["service"] == example_service.name
    assert logs[0]["exc_info"] == check_exc
    assert (
        logs[1]["event"]
        == "Aborting additional checks and treating the service as unhealthy."
    )
    assert logs[1]["log_level"] == "error"
    assert logs[1]["service"] == example_service.name
