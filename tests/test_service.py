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


async def test_run_awaits_all_checks(mocker: MockerFixture, example_service):
    """When run, the service awaits the status of all its health checks."""
    mock_all_checks_healthy = mocker.patch.object(example_service, "all_checks_healthy")
    await example_service.run(_only_once=True)
    mock_all_checks_healthy.assert_awaited_once()


async def test_run_announces_when_all_checks_healthy(
    mocker: MockerFixture, example_service_w_mock_prefixes
):
    """
    When run, all prefixes are announced if the all_checks_healthy method returns True.
    """
    mocker.patch.object(
        example_service_w_mock_prefixes, "all_checks_healthy", return_value=True
    )
    await example_service_w_mock_prefixes.run(_only_once=True)
    for mock_prefix in example_service_w_mock_prefixes.prefixes:
        mock_prefix.announce.assert_awaited_once()


async def test_run_denounces_when_all_checks_healthy_returns_false(
    mocker: MockerFixture, example_service_w_mock_prefixes
):
    """
    When run, all prefixes are denounced if the all_checks_healthy method returns False.
    """
    mocker.patch.object(
        example_service_w_mock_prefixes, "all_checks_healthy", return_value=False
    )
    await example_service_w_mock_prefixes.run(_only_once=True)
    for mock_prefix in example_service_w_mock_prefixes.prefixes:
        mock_prefix.denounce.assert_awaited_once()


async def test_all_checks_healthy_true_when_all_checks_healthy(
    example_service_w_mock_checks,
):
    """
    The all_checks_healthy method returns True when all health checks report as healthy.
    """
    for mock_health_check in example_service_w_mock_checks.health_checks:
        mock_health_check.is_healthy.return_value = True
    result = await example_service_w_mock_checks.all_checks_healthy()
    assert result is True


async def test_all_checks_healthy_false_when_one_check_unhealthy(
    example_service_w_mock_checks,
):
    """
    The all_checks_healthy method returns False when one health check
    reports as unhealthy.
    """
    for mock_health_check in example_service_w_mock_checks.health_checks:
        mock_health_check.is_healthy.return_value = True
    example_service_w_mock_checks.health_checks[1].is_healthy.return_value = False
    result = await example_service_w_mock_checks.all_checks_healthy()
    assert result is False


async def test_all_checks_healthy_false_when_all_checks_unhealthy(
    example_service_w_mock_checks,
):
    """
    The all_checks_healthy method returns False when all health checks
    reports as unhealthy.
    """
    for mock_health_check in example_service_w_mock_checks.health_checks:
        mock_health_check.is_healthy.return_value = False
    result = await example_service_w_mock_checks.all_checks_healthy()
    assert result is False


async def test_all_checks_healthy_false_when_check_raises(
    example_service_w_mock_checks,
):
    """
    The all_checks_healthy method returns False when a health check raises an exception.
    """
    # All checks return a healthy status
    for mock_health_check in example_service_w_mock_checks.health_checks:
        mock_health_check.is_healthy.return_value = True
    # Except for one raising an exception
    example_service_w_mock_checks.health_checks[1].is_healthy.side_effect = Exception
    result = await example_service_w_mock_checks.all_checks_healthy()
    assert result is False


async def test_all_checks_healthy_logs_exception_raised_by_check(
    example_service, example_service_w_mock_checks
):
    """
    The all_checks_healthy method logs exceptions raised by a health check.
    """
    check_exc = Exception("An error occurred while executing the health check.")
    example_service_w_mock_checks.health_checks[1].is_healthy.side_effect = check_exc

    with capture_logs() as logs:
        await example_service_w_mock_checks.all_checks_healthy()

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


@pytest.mark.parametrize("new_health_status", [True, False])
def test_change_of_service_health_is_logged(example_service, new_health_status: bool):
    """When the service's health changes, the new health status is logged."""
    # Start out with the opposite of what will be set
    example_service.healthy = not new_health_status

    with capture_logs() as logs:
        example_service.healthy = new_health_status

    assert logs[0]["event"] == "Service health changed to {}.".format(
        "healthy" if new_health_status is True else "unhealthy"
    )
    assert logs[0]["log_level"] == "info"
    assert logs[0]["service"] == example_service.name


@pytest.mark.parametrize("current_health_status", [True, False])
def test_set_service_health_without_change_does_not_log(
    example_service, current_health_status: bool
):
    """When the service's health is set to the same value, no log is emitted."""
    # Start out with the same value as what will be set
    example_service.healthy = current_health_status

    with capture_logs() as logs:
        example_service.healthy = current_health_status

    assert logs == []


def test_service_health_set_correctly(example_service):
    """The service's health status can be set correctly."""
    current_health_status = example_service.healthy
    new_health_status = not current_health_status

    example_service.healthy = new_health_status

    assert example_service.healthy == new_health_status


def test_private_health_not_in_repr_or_str(example_service):
    """The private _healthy attribute is not included in the service's repr or str."""
    assert "_healthy" not in repr(example_service)
    assert "_healthy" not in str(example_service)
