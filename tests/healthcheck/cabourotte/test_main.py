import datetime

import httpx
import pytest
from anycastd.healthcheck._cabourotte.main import CabourotteHealthcheck
from anycastd.healthcheck._cabourotte.result import Result
from pytest_mock import MockerFixture


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


@pytest.mark.asyncio
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
@pytest.mark.asyncio
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
