from typing import overload

from anycastd._configuration.healthcheck import (
    CabourotteHealthcheckConfiguration,
    HealthcheckConfiguration,
)
from anycastd._configuration.prefix import FRRPrefixConfiguration, PrefixConfiguration
from anycastd._configuration.service import ServiceConfiguration
from anycastd._executor import LocalExecutor
from anycastd.core import Service
from anycastd.healthcheck import CabourotteHealthcheck, Healthcheck
from anycastd.prefix import FRRoutingPrefix, Prefix


def config_to_service(config: ServiceConfiguration) -> Service:
    """Convert a service configuration to an actual service instance.

    Args:
        config: The configuration to convert.

    Returns:
        A service instance with the pararmeters from the configuration.
    """
    prefixes: tuple[Prefix, ...] = tuple(
        _sub_config_to_instance(prefix) for prefix in config.prefixes
    )
    health_checks: tuple[Healthcheck, ...] = tuple(
        _sub_config_to_instance(check) for check in config.checks
    )

    return Service(name=config.name, prefixes=prefixes, health_checks=health_checks)


@overload
def _sub_config_to_instance(config: PrefixConfiguration) -> Prefix:
    ...


@overload
def _sub_config_to_instance(config: HealthcheckConfiguration) -> Healthcheck:
    ...


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
