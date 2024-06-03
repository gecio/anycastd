import datetime
from typing import Literal, TypeAlias

from anycastd._configuration.sub import SubConfiguration


class HealthcheckConfiguration(SubConfiguration):
    """A healthcheck configuration."""


class CabourotteHealthcheckConfiguration(HealthcheckConfiguration):
    """The configuration for a Cabourotte healthcheck.

    Attributes:
        name: The name of the healthcheck.
        url: The URL of the cabourotte http endpoint.
        interval: The interval in seconds at which the healthcheck should be executed.
    """

    name: str
    url: str = "http://127.0.0.1:9013"
    interval: datetime.timedelta = datetime.timedelta(seconds=5)


Name: TypeAlias = Literal["cabourotte"]

_type_by_name: dict[Name, type[HealthcheckConfiguration]] = {
    "cabourotte": CabourotteHealthcheckConfiguration,
}


def get_type_by_name(name: Name) -> type[HealthcheckConfiguration]:
    """Get a healthcheck configuration class by it's name as used in the configuration.

    Args:
        name: The name of the healtcheck type.

    Returns:
        The configuration class for the type of healthcheck.

    Raises:
        ValueError: There is no healthcheck type with the given name.
    """
    try:
        return _type_by_name[name]
    except KeyError as exc:
        raise ValueError(f"Unknown healthcheck type: {name}") from exc
