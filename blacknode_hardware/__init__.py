"""Hardware-neutral contracts and real adapters for Blacknode."""

from .contracts import DeviceState, MobileBaseCommand, MobileBaseProvider
from .safety import SafetyGate, SafetyLimits
try:
    from . import node_types  # noqa: F401  # registers Blacknode nodes
except ModuleNotFoundError as exc:
    # Direct adapter deployments do not need the Blacknode graph runtime.
    if exc.name != "blacknode":
        raise
from .adapters import (
    I2CMecanumBase, I2CMecanumConfig, SerialJointConfig,
    SerialJointGroup, SerialJointSpec, probe_serial,
)
from .joint_group import JointGroupCommand, JointGroupProvider, JointGroupState

__all__ = [
    "DeviceState",
    "MobileBaseCommand",
    "MobileBaseProvider",
    "SafetyGate",
    "SafetyLimits",
    "I2CMecanumBase",
    "I2CMecanumConfig",
    "SerialJointConfig",
    "SerialJointGroup",
    "SerialJointSpec",
    "probe_serial",
    "JointGroupCommand",
    "JointGroupProvider",
    "JointGroupState",
]
