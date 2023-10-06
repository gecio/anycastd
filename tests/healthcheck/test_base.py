import datetime

import pytest
from anycastd.healthcheck.base import BaseHealthcheck
from pytest_mock import MockerFixture

from tests.dummy import DummyHealthcheck


def test__init___non_timedelta_interval_raises_type_error():
    """Passing a non-timedelta interval raises a TypeError."""
    with pytest.raises(TypeError):
        BaseHealthcheck(interval="not a timedelta")  # type: ignore


def test__repr__():
    """The repr of a subclassed healthcheck is correct."""
    check = DummyHealthcheck(interval=datetime.timedelta(seconds=1))
    assert repr(check) == "DummyHealthcheck(interval=datetime.timedelta(seconds=1))"


class TestHealthStatus:
    """Tests for the healthchecks status."""

    @pytest.mark.asyncio
    async def test_never_checked_runs_checks(self, mocker: MockerFixture):
        """When the healthcheck has never been checked, checks are run."""
        healthcheck = DummyHealthcheck(interval=datetime.timedelta(seconds=1))
        healthcheck._last_checked = None
        mock__check = mocker.patch.object(healthcheck, "_check")

        await healthcheck.is_healthy()

        mock__check.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_checked_sets_last_checked(self, mocker: MockerFixture):
        """When the healthcheck is checked, the last checked time is set."""
        healthcheck = DummyHealthcheck(interval=datetime.timedelta(seconds=1))
        healthcheck._last_checked = None
        mocker.patch.object(healthcheck, "_check")

        await healthcheck.is_healthy()

        assert isinstance(healthcheck._last_checked, datetime.datetime)

    @pytest.mark.asyncio
    async def test_checked_sets_last_healthy(self, mocker: MockerFixture):
        """When the healthcheck is checked, the last healthy status is set."""
        healthcheck = DummyHealthcheck(interval=datetime.timedelta(seconds=1))
        healthcheck._last_checked = None
        healthcheck._last_healthy = False
        mocker.patch.object(healthcheck, "_check", return_value=True)

        await healthcheck.is_healthy()

        assert healthcheck._last_healthy is True

    @pytest.mark.asyncio
    async def test_checked_returns_check_output(self, mocker: MockerFixture):
        """When the healthcheck is checked, the check output is returned."""
        healthcheck = DummyHealthcheck(interval=datetime.timedelta(seconds=1))
        healthcheck._last_checked = None
        healthcheck._last_healthy = False
        mocker.patch.object(healthcheck, "_check", return_value=True)

        result = await healthcheck.is_healthy()

        assert result is True

    @pytest.mark.asyncio
    async def test_interval_passed_checks_run(self, mocker: MockerFixture):
        """When the interval has passed, checks are run."""
        interval = datetime.timedelta(seconds=5)
        healthcheck = DummyHealthcheck(interval=interval)
        healthcheck._last_checked = (
            datetime.datetime.now(datetime.timezone.utc) - interval
        )
        mock__check = mocker.patch.object(healthcheck, "_check", return_value=True)

        await healthcheck.is_healthy()

        mock__check.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_interval_not_passed_checks_not_run(self, mocker: MockerFixture):
        """When the interval hasn't passed, no checks are run."""
        interval = datetime.timedelta(seconds=5)
        healthcheck = DummyHealthcheck(interval=interval)
        healthcheck._last_checked = datetime.datetime.now(datetime.timezone.utc) - (
            interval - datetime.timedelta(seconds=1)
        )
        mock__check = mocker.patch.object(healthcheck, "_check", return_value=True)

        await healthcheck.is_healthy()

        mock__check.assert_not_awaited()

    @pytest.mark.parametrize("last_healthy", [True, False])
    @pytest.mark.asyncio
    async def test_checks_not_run_returns_last_healthy(
        self, mocker: MockerFixture, last_healthy: bool
    ):
        """When no checks are run, the last healthy status is returned."""
        healthcheck = DummyHealthcheck(interval=datetime.timedelta(seconds=1))
        healthcheck._last_checked = datetime.datetime.now(datetime.timezone.utc)
        healthcheck._last_healthy = last_healthy
        mocker.patch.object(healthcheck, "_check")

        result = await healthcheck.is_healthy()

        assert result == last_healthy
