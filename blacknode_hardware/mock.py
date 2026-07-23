"""Hardware-free provider used by tests and workflow previews."""

from __future__ import annotations

import time

from .contracts import DeviceState, MobileBaseCommand
from .safety import SafetyGate


class MockMobileBase:
    def __init__(self, device_id: str = "mock-base", gate: SafetyGate | None = None) -> None:
        self.gate = gate or SafetyGate()
        self._command = MobileBaseCommand()
        self._state = DeviceState(
            device_id=device_id,
            connected=True,
            armed=False,
            capabilities=["mobile_base"],
        )

    def state(self) -> DeviceState:
        return self._state

    def arm(self) -> DeviceState:
        self.gate.arm()
        self._state.armed = True
        self._state.updated_at = time.time()
        return self._state

    def disarm(self) -> DeviceState:
        self.stop()
        self.gate.disarm()
        self._state.armed = False
        self._state.updated_at = time.time()
        return self._state

    def command(self, command: MobileBaseCommand) -> DeviceState:
        self.gate.validate(command)
        self._command = command
        self._state.values["mobile_base_command"] = {
            "linear_x": command.linear_x,
            "linear_y": command.linear_y,
            "angular_z": command.angular_z,
        }
        self._state.updated_at = time.time()
        return self._state

    def stop(self) -> DeviceState:
        self._command = MobileBaseCommand()
        self._state.values["mobile_base_command"] = {
            "linear_x": 0.0,
            "linear_y": 0.0,
            "angular_z": 0.0,
        }
        self._state.updated_at = time.time()
        return self._state
