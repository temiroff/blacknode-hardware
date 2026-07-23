"""Hardware capability inspection and safe command preview nodes."""

from __future__ import annotations

from blacknode.node import Any, Bool, Dict, Float, List, Text, node

from .contracts import MobileBaseCommand
from .joint_group import JointGroupCommand, MockJointGroup
from .safety import SafetyGate, SafetyLimits


_CATEGORY = "Hardware"


@node(
    name="HardwareCapabilities",
    component="core",
    category=_CATEGORY,
    description="Report the generic hardware capabilities requested by a device profile.",
    inputs={
        "device_id": Text(default="device"),
        "capabilities": List(default=["mobile_base"]),
        "refresh": Any,
    },
    outputs={"available": Bool, "device_id": Text, "capabilities": List, "state": Dict, "report": Text},
)
def hardware_capabilities(ctx: dict) -> dict:
    device_id = str(ctx.get("device_id") or "device")
    capabilities = [str(value) for value in (ctx.get("capabilities") or [])]
    state = {
        "device_id": device_id,
        "connected": False,
        "armed": False,
        "capabilities": capabilities,
        "provider": "unconfigured",
    }
    return {
        "available": False,
        "device_id": device_id,
        "capabilities": capabilities,
        "state": state,
        "report": "no hardware provider configured; select a provider in the device profile",
    }


@node(
    name="HardwareCommandPreview",
    component="core",
    category=_CATEGORY,
    description="Validate a mobile-base command without sending it to physical hardware.",
    inputs={
        "linear_x": Float(default=0.0),
        "linear_y": Float(default=0.0),
        "angular_z": Float(default=0.0),
        "armed": Bool(default=False),
        "max_linear_speed": Float(default=0.25),
        "max_angular_speed": Float(default=0.75),
    },
    outputs={"valid": Bool, "command": Dict, "error": Text, "report": Text},
)
def hardware_command_preview(ctx: dict) -> dict:
    try:
        command = MobileBaseCommand(
            linear_x=float(ctx.get("linear_x") or 0),
            linear_y=float(ctx.get("linear_y") or 0),
            angular_z=float(ctx.get("angular_z") or 0),
        )
        gate = SafetyGate(
            SafetyLimits(
                max_linear_speed=float(ctx.get("max_linear_speed") or 0.25),
                max_angular_speed=float(ctx.get("max_angular_speed") or 0.75),
            )
        )
        if bool(ctx.get("armed")):
            gate.arm()
        gate.validate(command)
        payload = {
            "linear_x": command.linear_x,
            "linear_y": command.linear_y,
            "angular_z": command.angular_z,
        }
        return {"valid": True, "command": payload, "error": "", "report": "command passed safety preview"}
    except Exception as exc:
        return {"valid": False, "command": {}, "error": str(exc), "report": "command blocked by safety preview"}


@node(
    name="HardwareJointGroupPreview",
    component="core",
    category=_CATEGORY,
    description="Validate a generic joint-position command using a hardware-free provider.",
    inputs={
        "joint_names": List(default=[]),
        "positions": Dict(default={}),
        "limits": Dict(default={}),
        "armed": Bool(default=False),
    },
    outputs={"valid": Bool, "state": Dict, "error": Text, "report": Text},
)
def hardware_joint_group_preview(ctx: dict) -> dict:
    try:
        names = [str(value) for value in (ctx.get("joint_names") or [])]
        limits = dict(ctx.get("limits") or {})
        provider = MockJointGroup(joint_names=names, limits=limits)
        if bool(ctx.get("armed")):
            provider.arm()
        provider.command(JointGroupCommand(positions=dict(ctx.get("positions") or {})))
        return {"valid": True, "state": provider.state().as_dict(), "error": "", "report": "joint command passed preview"}
    except Exception as exc:
        return {"valid": False, "state": {}, "error": str(exc), "report": "joint command blocked by preview"}
