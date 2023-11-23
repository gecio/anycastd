import datetime
from typing import Self

from pydantic_settings import BaseSettings

DEFAULT_URL = "http://127.0.0.1:9013"


class CabourotteHealthcheck(BaseSettings):
    """The configuration for a Cabourotte healthcheck.

    Attributes:
        name: The name of the healthcheck.
        url: The URL of the cabourotte http endpoint.
        interval: The interval in seconds at which the healthcheck should be executed.
    """

    name: str
    url: str = DEFAULT_URL
    interval: datetime.timedelta = datetime.timedelta(seconds=5)

    @classmethod
    def from_configuration(cls, config: str | dict) -> Self:
        """Create an instance from the configuration format.

        The configuration can be provided in two formats, a simplified format
        containing only the name of the healthcheck as a string, or a full format
        containing the name as well as other optional options.

        Args:
            config: The configuration for the healthcheck.

        Returns:
            A new CabourotteHealthcheck instance.

        Raises:
            ValidationError: Failed to validate the configuration.
            TypeError: The configuration has an invalid type.
        """
        match config:
            case str():
                return cls.model_validate({"name": config})
            case dict():
                return cls.model_validate(config)
            case _:
                raise TypeError(f"Invalid configuration type {type(config)}")
