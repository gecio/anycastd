import datetime

import httpx
import pytest
from anycastd.healthcheck._cabourotte.exceptions import CabourotteCheckNotFoundError
from anycastd.healthcheck._cabourotte.main import CabourotteHealthcheck
from anycastd.healthcheck._cabourotte.result import Result
from pytest_mock import MockerFixture
from structlog.testing import capture_logs


def test__init__():
    """A healthcheck can be constructed."""
    healthcheck = CabourotteHealthcheck(
        "test", url="https://example.com", interval=datetime.timedelta(seconds=10)
    )
    assert healthcheck.name == "test"
    assert healthcheck.url == "https://example.com"
    assert healthcheck.interval == datetime.timedelta(seconds=10)


def test__init__non_string_name_raises_type_error():
    """Passing a non-string name raises a TypeError."""
    with pytest.raises(TypeError):
        CabourotteHealthcheck(
            123,  # type: ignore
            url="https://example.com",
            interval=datetime.timedelta(seconds=10),
        )


def test__init__non_string_url_raises_type_error():
    """Passing a non-string URL raises a TypeError."""
    with pytest.raises(TypeError):
        CabourotteHealthcheck(
            "test",
            url=httpx.URL("https://example.com"),  # type: ignore
            interval=datetime.timedelta(seconds=10),
        )


@pytest.mark.parametrize(
    "attributes",
    [
        {
            "name": "test",
            "url": "https://example.com",
            "interval": datetime.timedelta(seconds=30),
        }
    ],
)
def test_repr(attributes: dict):
    """The repr of a Cabourotte healthcheck is correct."""
    healthcheck = CabourotteHealthcheck(**attributes)
    assert repr(healthcheck) == "CabourotteHealthcheck({})".format(
        ", ".join(f"{k}={v!r}" for (k, v) in attributes.items())
    )


def test_equal():
    """Two healthchecks with the same attributes are equal."""
    healthcheck1 = CabourotteHealthcheck(
        "test", url="https://example.com", interval=datetime.timedelta(seconds=10)
    )
    healthcheck2 = CabourotteHealthcheck(
        "test", url="https://example.com", interval=datetime.timedelta(seconds=10)
    )
    assert healthcheck1 == healthcheck2


def test_non_equal():
    """Two healthchecks with different attributes are not equal."""
    healthcheck1 = CabourotteHealthcheck(
        "test", url="https://example.com", interval=datetime.timedelta(seconds=10)
    )
    healthcheck2 = CabourotteHealthcheck(
        "test", url="https://example.com", interval=datetime.timedelta(seconds=20)
    )
    assert healthcheck1 != healthcheck2


async def test_get_status_awaits_get_result(mocker: MockerFixture):
    """The get status method awaits the result of get_result."""
    name = "test"
    url = "https://example.com"
    healthcheck = CabourotteHealthcheck(
        name, url=url, interval=datetime.timedelta(seconds=10)
    )
    mock_get_result = mocker.patch("anycastd.healthcheck._cabourotte.main.get_result")

    await healthcheck._get_status()

    mock_get_result.assert_awaited_once_with(name, url=url)


@pytest.mark.parametrize("success", [True, False])
async def test_get_status_returns_result(success: bool, mocker: MockerFixture):
    """The check method returns True if the result is successful and False otherwise."""
    healthcheck = CabourotteHealthcheck(
        "test", url="https://example.com", interval=datetime.timedelta(seconds=10)
    )

    mock_result = mocker.create_autospec(Result, success=success)
    mocker.patch(
        "anycastd.healthcheck._cabourotte.main.get_result", return_value=mock_result
    )

    assert await healthcheck._get_status() == success


async def test_get_status_logs_error_if_check_does_not_exist(mocker: MockerFixture):
    """The get status method logs an error if the check does not exist."""
    healthcheck = CabourotteHealthcheck(
        "test", url="https://example.com", interval=datetime.timedelta(seconds=10)
    )
    exc = CabourotteCheckNotFoundError("test", "https://example.com")
    mocker.patch(
        "anycastd.healthcheck._cabourotte.main.get_result",
        side_effect=exc,
    )

    with capture_logs() as logs:
        await healthcheck._get_status()

    assert (
        logs[1]["event"] == 'Cabourotte health check "test" does not exist, '
        "returning an unhealthy status."
    )
    assert logs[1]["log_level"] == "error"
    assert logs[1]["exc_info"] == exc


async def test_get_status_returns_false_if_check_does_not_exist(mocker: MockerFixture):
    """The get status method logs an error if the check does not exist."""
    healthcheck = CabourotteHealthcheck(
        "test", url="https://example.com", interval=datetime.timedelta(seconds=10)
    )
    mocker.patch("anycastd.healthcheck._cabourotte.main.get_result", return_value=True)
    mocker.patch(
        "anycastd.healthcheck._cabourotte.main.get_result",
        side_effect=CabourotteCheckNotFoundError("test", "https://example.com"),
    )

    assert await healthcheck._get_status() is False
