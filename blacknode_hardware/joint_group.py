"""Generic joint-group contracts and a hardware-free provider."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Protocol


@dataclass(frozen=True)
class JointGroupCommand:
    positions: dict[str, float]
    issued_at: float = field(default_factory=time.monotonic)
    expires_at: float = 0.0

    def is_fresh(self, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        return self.expires_at <= 0.0 or current <= self.expires_at


@dataclass
class JointGroupState:
    device_id: str
    connected: bool = False
    armed: bool = False
    joint_names: list[str] = field(default_factory=list)
    positions: dict[str, float] = field(default_factory=dict)
    limits: dict[str, dict[str, float]] = field(default_factory=dict)
    error: str = ""
    updated_at: float = field(default_factory=time.time)

    def as_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "connected": self.connected,
            "armed": self.armed,
            "joint_names": list(self.joint_names),
            "positions": dict(self.positions),
            "limits": {name: dict(values) for name, values in self.limits.items()},
            "error": self.error,
            "updated_at": self.updated_at,
        }


class JointGroupProvider(Protocol):
    def state(self) -> JointGroupState: ...

    def arm(self) -> JointGroupState: ...

    def disarm(self) -> JointGroupState: ...

    def command(self, command: JointGroupCommand) -> JointGroupState: ...

    def stop(self) -> JointGroupState: ...


class MockJointGroup:
    """Safe provider for arm workflows without physical hardware."""

    def __init__(
        self,
        device_id: str = "mock-joint-group",
        joint_names: list[str] | None = None,
        limits: dict[str, dict[str, float]] | None = None,
    ) -> None:
        names = list(joint_names or [])
        self._state = JointGroupState(
            device_id=device_id,
            connected=True,
            joint_names=names,
            positions={name: 0.0 for name in names},
            limits={name: dict(values) for name, values in (limits or {}).items()},
        )

    def state(self) -> JointGroupState:
        return self._state

    def arm(self) -> JointGroupState:
        self._state.armed = True
        self._state.updated_at = time.time()
        return self._state

    def disarm(self) -> JointGroupState:
        self.stop()
        self._state.armed = False
        self._state.updated_at = time.time()
        return self._state

    def command(self, command: JointGroupCommand) -> JointGroupState:
        if not self._state.armed:
            raise PermissionError("joint motion is disarmed")
        if not command.is_fresh():
            raise TimeoutError("joint command is stale")
        unknown = sorted(set(command.positions) - set(self._state.joint_names))
        if unknown:
            raise ValueError(f"unknown joints: {', '.join(unknown)}")
        for name, position in command.positions.items():
            limits = self._state.limits.get(name, {})
            low = limits.get("min")
            high = limits.get("max")
            if low is not None and position < low:
                raise ValueError(f"{name} is below its minimum limit")
            if high is not None and position > high:
                raise ValueError(f"{name} is above its maximum limit")
        self._state.positions.update({name: float(value) for name, value in command.positions.items()})
        self._state.updated_at = time.time()
        return self._state

    def stop(self) -> JointGroupState:
        self._state.updated_at = time.time()
        return self._state
