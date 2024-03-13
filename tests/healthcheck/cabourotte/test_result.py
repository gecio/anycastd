import datetime
import json
from typing import TypedDict

import httpx
import pytest
import respx
from anycastd.healthcheck._cabourotte.exceptions import (
    CabourotteCheckError,
    CabourotteCheckNotFoundError,
)
from anycastd.healthcheck._cabourotte.result import Result, get_result
from hypothesis import assume, given, strategies
from pytest_mock import MockerFixture

CABOUROTTE_URL = "http://[::1]:9013"

# The result of a healthcheck as returned by the cabourotte API.
_ResultData = TypedDict(
    "_ResultData",
    {
        "name": str,
        "summary": str,
        "success": bool,
        "healthcheck-timestamp": int,
        "message": str,
        "duration": int,
        "source": str,
    },
)


@strategies.composite
def http_error_code(draw) -> httpx.codes:
    """A hypothesis strategy for HTTP error codes."""
    status_code = draw(strategies.sampled_from(httpx.codes))
    assume(httpx.codes.is_error(status_code))
    return status_code


def example_result() -> _ResultData:
    """Return an example result."""
    return {
        "name": "example-api",
        "summary": "HTTP healthcheck on ::1:8080",
        "success": True,
        "healthcheck-timestamp": 1695648161,
        "message": "success",
        "duration": 1,
        "source": "configuration",
    }


@pytest.mark.parametrize("data", [example_result()])
def test_result_from_api_json(data: _ResultData):
    """Results can be created from JSON returned by the cabourotte API."""
    json_ = json.dumps(data)

    result = Result.from_json(json_)

    assert result.name == data["name"]
    assert result.summary == data["summary"]
    assert result.success == data["success"]
    assert result.timestamp == datetime.datetime.fromtimestamp(
        data["healthcheck-timestamp"], datetime.timezone.utc
    )
    assert result.message == data["message"]
    assert result.duration == data["duration"]
    assert result.source == data["source"]


class TestGetResult:
    """Test getting a result from the cabourotte API."""

    @respx.mock
    @pytest.mark.parametrize(
        "name,url",
        [("example-http-check", CABOUROTTE_URL), ("example-dns-check", CABOUROTTE_URL)],
    )
    async def test_get_made_to_correct_url(
        self, name: str, url: str, mocker: MockerFixture
    ):
        """A GET request is made to the correct URL."""
        result_url = url + f"/result/{name}"
        mock_endpoint = respx.get(result_url)
        mocker.patch("anycastd.healthcheck._cabourotte.result.Result.from_json")

        await get_result(name, url=url)

        request = mock_endpoint.calls.last.request
        assert request.method == "GET"
        assert request.url == result_url

    async def test_correct_result_returned(self, respx_mock):
        """The correct result corresponding to API data is returned."""
        json_data = json.dumps(example_result())
        name = "example-api"
        result_url = CABOUROTTE_URL + f"/result/{name}"

        mock_endpoint = respx_mock.get(result_url)
        mock_response = httpx.Response(status_code=200, content=json_data.encode())
        mock_endpoint.return_value = mock_response

        result = await get_result(name, url=CABOUROTTE_URL)

        assert result == Result.from_json(json_data)

    @respx.mock
    async def test_404_status_code_error_raises_check_not_found(self):
        """A 404 status code error raises a CabourotteCheckNotFoundError."""
        name = "example-api"
        result_url = CABOUROTTE_URL + f"/result/{name}"

        mock_response = httpx.Response(status_code=httpx.codes.NOT_FOUND)
        respx.get(result_url).return_value = mock_response

        with pytest.raises(
            CabourotteCheckNotFoundError,
            match=f'An error occurred while requesting the check result for "{name}": '
            "The check could not be found.",
        ):
            await get_result(name, url=CABOUROTTE_URL)

    @respx.mock
    @given(http_error_code())
    async def test_other_status_code_error_raises_cabourotte_check_error(
        self, status_code: httpx.codes
    ):
        """Any other status code error raises a CabourotteCheckError."""
        assume(status_code != httpx.codes.NOT_FOUND)
        name = "example-api"
        result_url = CABOUROTTE_URL + f"/result/{name}"

        mock_response = httpx.Response(status_code=status_code)
        respx.get(result_url).return_value = mock_response

        with pytest.raises(
            CabourotteCheckError,
            match=rf'An error occurred while requesting the check result for "{name}": .*',  # noqa: E501
        ):
            await get_result(name, url=CABOUROTTE_URL)

    @respx.mock
    @pytest.mark.parametrize(
        "side_effect",
        [
            httpx.RequestError,
            httpx.TransportError,
            httpx.TimeoutException,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.PoolTimeout,
            httpx.NetworkError,
            httpx.ConnectError,
            httpx.ReadError,
            httpx.WriteError,
            httpx.CloseError,
            httpx.ProtocolError,
            httpx.LocalProtocolError,
            httpx.RemoteProtocolError,
            httpx.ProxyError,
            httpx.UnsupportedProtocol,
            httpx.DecodingError,
            httpx.TooManyRedirects,
        ],
    )
    async def test_other_request_error_raises_cabourotte_check_error(
        self, side_effect: Exception
    ):
        """Any other request error raises a CabourotteCheckError."""
        name = "example-api"
        result_url = CABOUROTTE_URL + f"/result/{name}"

        respx.get(result_url).side_effect = side_effect

        with pytest.raises(
            CabourotteCheckError,
            match=rf'An error occurred while requesting the check result for "{name}":.*',  # noqa: E501
        ):
            await get_result(name, url=CABOUROTTE_URL)
