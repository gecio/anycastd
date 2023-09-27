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


@pytest.mark.asyncio
async def test__check_awaits_get_result(mocker: MockerFixture):
    """The check method awaits the result of get_result."""
    name = "test"
    url = "https://example.com"
    healthcheck = CabourotteHealthcheck(
        name, url=url, interval=datetime.timedelta(seconds=10)
    )
    mock_get_result = mocker.patch("anycastd.healthcheck._cabourotte.main.get_result")

    await healthcheck._check()

    mock_get_result.assert_awaited_once_with(name, url=url)


@pytest.mark.parametrize("success", [True, False])
@pytest.mark.asyncio
async def test__check_returns_result_success(success: bool, mocker: MockerFixture):
    """The check method returns True if the result is successful and False otherwise."""
    healthcheck = CabourotteHealthcheck(
        "test", url="https://example.com", interval=datetime.timedelta(seconds=10)
    )

    mock_result = mocker.create_autospec(Result, success=success)
    mocker.patch(
        "anycastd.healthcheck._cabourotte.main.get_result", return_value=mock_result
    )

    assert await healthcheck._check() == success
