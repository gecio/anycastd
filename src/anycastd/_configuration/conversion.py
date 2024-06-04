from typing import Any, overload

from anycastd._configuration.healthcheck import (
    CabourotteHealthcheckConfiguration,
    HealthcheckConfiguration,
)
from anycastd._configuration.prefix import FRRPrefixConfiguration, PrefixConfiguration
from anycastd._configuration.service import ServiceConfiguration
from anycastd._executor import LocalExecutor
from anycastd.core._service import Service
from anycastd.healthcheck import CabourotteHealthcheck, Healthcheck
from anycastd.prefix import FRRoutingPrefix, Prefix


def config_to_service(config: ServiceConfiguration) -> Service:
    """Convert a service configuration to an actual service instance.

    Args:
        config: The configuration to convert.

    Returns:
        A service instance with the parameters from the configuration.
    """
    prefixes: tuple[Prefix, ...] = tuple(
        _sub_config_to_instance(prefix) for prefix in config.prefixes
    )
    health_checks: tuple[Healthcheck, ...] = tuple(
        _sub_config_to_instance(check) for check in config.checks
    )

    return Service(name=config.name, prefixes=prefixes, health_checks=health_checks)


@overload
def _sub_config_to_instance(config: PrefixConfiguration) -> Prefix: ...


@overload
def _sub_config_to_instance(config: HealthcheckConfiguration) -> Healthcheck: ...


def _sub_config_to_instance(
    config: PrefixConfiguration | HealthcheckConfiguration,
) -> Prefix | Healthcheck:
    """Convert a subconfiguration to an instance of it's respective type.

    Convert subconfigurations to instances of the repsctive type
    they are describing, e.g. a FRRPrefixConfiguration to a FRRoutingPrefix.

    Args:
        config: The subconfiguration to convert.

    Returns:
        An instance of the respective type the subconfiguration describes.
    """
    match config:
        case FRRPrefixConfiguration():
            return FRRoutingPrefix(**config.model_dump(), executor=LocalExecutor())
        case CabourotteHealthcheckConfiguration():
            return CabourotteHealthcheck(**config.model_dump())
        case _:
            raise NotImplementedError(
                f"Configuration type {type(config)} is not supported."
            )


def dict_w_items_named_by_key_to_flat_w_name_value(
    named_items_dict: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Convert a dictionary containing items named by their key into a flat dictionary.

    Takes a dictionary containing items named by their key and turns it into a
    tuple of flat dictionaries containing the name as a value.

    Example:
    ```python
    >>> named = {"foo": {"bar": "baz"}, "qux": {"quux": "corge"}}
    >>> dict_w_items_named_by_key_to_flat_w_name_value(named)
    ({'name': 'foo', 'bar': 'baz'}, {'name': 'qux', 'quux': 'corge'})
    ```
    """
    # TODO: Handle potential errors.
    items = named_items_dict.items()
    return tuple({"name": name, **content} for name, content in items)
