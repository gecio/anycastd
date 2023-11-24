from typing import Literal, TypeAlias

from anycastd._configuration.healthcheck._cabourotte import CabourotteHealthcheck

Name: TypeAlias = Literal["cabourotte"]
ConfigurationClass: TypeAlias = type[CabourotteHealthcheck]

_type_by_name: dict[Name, ConfigurationClass] = {
    "cabourotte": CabourotteHealthcheck,
}


def get_type_by_name(name: Name) -> ConfigurationClass:
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
