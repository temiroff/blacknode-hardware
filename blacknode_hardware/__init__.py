"""Hardware-neutral contracts and providers for Blacknode."""

from .contracts import DeviceState, MobileBaseCommand, MobileBaseProvider
from .mock import MockMobileBase
from .safety import SafetyGate, SafetyLimits
try:
    from . import node_types  # noqa: F401  # registers Blacknode nodes
except ModuleNotFoundError as exc:
    # Direct adapter deployments do not need the Blacknode graph runtime.
    if exc.name != "blacknode":
        raise
from .adapters import I2CMecanumBase, I2CMecanumConfig

__all__ = [
    "DeviceState",
    "MobileBaseCommand",
    "MobileBaseProvider",
    "MockMobileBase",
    "SafetyGate",
    "SafetyLimits",
    "I2CMecanumBase",
    "I2CMecanumConfig",
]
