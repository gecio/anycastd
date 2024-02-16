from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from anycastd.healthcheck._common import interval_check


class TestIntervalCheck:
    """Test the interval_check check type."""

    @pytest.fixture(params=[True, False])
    def mock_internal_check(self, mocker, request) -> tuple[AsyncMock, bool]:
        """Mock of the check passed to interval_check and the result it returns."""
        check_result = request.param
        return mocker.AsyncMock(return_value=check_result), check_result

    async def test_check_awaited_on_first_call(self, mock_internal_check):
        """
        The check is awaited and its result returned on the first await of the checker.
        """
        internal_check, check_result = mock_internal_check
        checker = interval_check(
            timedelta(seconds=5),
            internal_check,
        )

        result = await checker()

        internal_check.assert_awaited_once()
        assert result == check_result

    async def test_check_awaited_when_interval_passed(
        self, mocker, mock_internal_check
    ):
        """
        The check is awaited and its result returned when the provided interval
        has passed.
        """
        internal_check, check_result = mock_internal_check
        interval = 5
        expected_await_count = 2
        checker = interval_check(
            timedelta(seconds=interval),
            internal_check,
        )
        await checker()  # Will always await the check on the first time

        datetime_interval_passed = datetime.now(timezone.utc) + timedelta(
            seconds=interval
        )

        class FakeDatetime(datetime):
            """Test wrapper for datetime.datetime.
            Required since datetime.datetime cannot be mocked directly.
            """

            def __new__(cls, *args, **kwargs):
                return datetime.__new__(datetime, *args, **kwargs)

            @classmethod
            def now(cls, tz=None):
                return datetime_interval_passed

        mocker.patch("anycastd.healthcheck._common.datetime", FakeDatetime)

        second_await_result = await checker()

        assert internal_check.await_count == expected_await_count
        assert second_await_result == check_result

    async def test_check_not_awaited_when_interval_not_passed_and_run_before(
        self, mock_internal_check
    ):
        """
        The check is not awaited and the last result is returned when the provided
        interval has not passed and the check has been run before.
        """
        internal_check, check_result = mock_internal_check
        checker = interval_check(
            timedelta(seconds=8),
            internal_check,
        )
        await checker()  # Will always await the check on the first time

        second_await_result = await checker()

        internal_check.assert_awaited_once()
        assert second_await_result == check_result
