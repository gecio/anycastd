from typing import overload

from anycastd._configuration.healthcheck import HealthcheckConfiguration
from anycastd._configuration.prefix import PrefixConfiguration
from anycastd.healthcheck import Healthcheck
from anycastd.prefix import Prefix


@overload
def config_to_instance(config: PrefixConfiguration) -> Prefix:
    ...


@overload
def config_to_instance(config: HealthcheckConfiguration) -> Healthcheck:
    ...


def config_to_instance(
    config: PrefixConfiguration | HealthcheckConfiguration
) -> Prefix | Healthcheck:
    """Convert a configuration to an instance of it's respective type."""
