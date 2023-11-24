from typing import Literal, TypeAlias

from anycastd._configuration.healthcheck._cabourotte import CabourotteHealthcheck
from anycastd._configuration.sub import HealthcheckConfiguration

Name: TypeAlias = Literal["cabourotte"]

_type_by_name: dict[Name, type[HealthcheckConfiguration]] = {
    "cabourotte": CabourotteHealthcheck,
}


def get_type_by_name(name: Name) -> type[HealthcheckConfiguration]:
    """Get a healthcheck configuration class by it's name as used in the configuration.

    Args:
        name: The name of the healtcheck type.

    Returns:
        The confiuration class for the type of healthcheck.

    Raises:
        ValueError: There is no healthcheck type with the given name.
    """
    try:
        return _type_by_name[name]
    except KeyError as exc:
        raise ValueError(f"Unknown healthcheck type: {name}") from exc
