import datetime
from typing import Self

import httpx
from pydantic import BaseModel, Field

from anycastd.healthcheck._cabourotte.exceptions import (
    CabourotteCheckError,
    CabourotteCheckNotFoundError,
)


class Result(BaseModel):
    """The result of a healthcheck."""

    name: str
    summary: str
    success: bool
    timestamp: datetime.datetime = Field(alias="healthcheck-timestamp")
    message: str
    duration: int
    source: str

    @classmethod
    def from_json(cls, data: str | bytes | bytearray) -> Self:
        """Create a result from JSON returned by the cabourotte API."""
        return cls.model_validate_json(data)


async def get_result(name: str, *, url: str) -> Result:
    """Get the result of a specific healthcheck.

    Arguments:
        name: The name of the healthcheck.
        url: The URL of the cabourotte API.

    Returns:
        The result of the healthcheck.
    """
    result_url = f"{url}/result/{name}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(result_url)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        if (
            isinstance(exc, httpx.HTTPStatusError)
            and exc.response.status_code == httpx.codes.NOT_FOUND
        ):
            raise CabourotteCheckNotFoundError(name, result_url) from None

        raise CabourotteCheckError(name, result_url, str(exc)) from exc

    return Result.from_json(response.content)
