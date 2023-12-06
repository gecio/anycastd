from typing import overload

from anycastd._configuration.healthcheck import (
    CabourotteHealthcheckConfiguration,
    HealthcheckConfiguration,
)
from anycastd._configuration.prefix import FRRPrefixConfiguration, PrefixConfiguration
from anycastd._executor import LocalExecutor
from anycastd.healthcheck import CabourotteHealthcheck, Healthcheck
from anycastd.prefix import FRRoutingPrefix, Prefix


@overload
def config_to_instance(config: PrefixConfiguration) -> Prefix:
    ...


@overload
def config_to_instance(config: HealthcheckConfiguration) -> Healthcheck:
    ...


def config_to_instance(
    config: PrefixConfiguration | HealthcheckConfiguration,
) -> Prefix | Healthcheck:
    """Convert a configuration to an instance of it's respective type."""
    match config:
        case FRRPrefixConfiguration():
            return FRRoutingPrefix(**config.model_dump(), executor=LocalExecutor())
        case CabourotteHealthcheckConfiguration():
            return CabourotteHealthcheck(**config.model_dump())
        case _:
            raise NotImplementedError(
                f"Configuration type {type(config)} is not supported."
            )
