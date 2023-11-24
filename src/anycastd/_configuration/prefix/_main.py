from typing import Literal, TypeAlias

from anycastd._configuration.prefix._frr import FRRPrefix

Name: TypeAlias = Literal["frrouting"]
ConfigurationClass: TypeAlias = type[FRRPrefix]

_type_by_name: dict[Name, ConfigurationClass] = {
    "frrouting": FRRPrefix,
}


def get_type_by_name(name: Name) -> ConfigurationClass:
    """Get a prefix configuration class by it's name as used in the configuration.

    Args:
        name: The name of the prefix type.

    Returns:
        The confiuration class for the type of prefix.

    Raises:
        ValueError: There is no prefix type with the given name.
    """
    try:
        return _type_by_name[name]
    except KeyError as exc:
        raise ValueError(f"Unknown prefix type: {name}") from exc
