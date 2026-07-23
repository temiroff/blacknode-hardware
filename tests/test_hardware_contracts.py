from __future__ import annotations

import pytest
import threading
from urllib.request import urlopen
import json

from blacknode_hardware import (
    I2CMecanumBase,
    SerialJointSpec,
    JointGroupCommand,
    JointGroupState,
    MobileBaseCommand,
    SafetyGate,
    SafetyLimits,
)
from blacknode_hardware.service import HardwareRuntime
from blacknode_hardware.service.server import create_server


def test_safety_limits_block_excess_speed():
    gate = SafetyGate(SafetyLimits(max_linear_speed=0.1))
    gate.arm()
    with pytest.raises(ValueError):
        gate.validate(MobileBaseCommand(linear_x=0.2))


def test_safety_gate_blocks_stale_commands():
    gate = SafetyGate()
    gate.arm()
    command = MobileBaseCommand(expires_at=10.0)
    with pytest.raises(TimeoutError):
        gate.validate(command, now=11.0)


def test_i2c_kinematics_can_be_checked_without_hardware():
    adapter = I2CMecanumBase()
    assert adapter._wheel_commands(MobileBaseCommand(linear_x=0.1)) == (-40, 40, -40, 40)


def test_joint_command_tracks_freshness():
    command = JointGroupCommand({"joint_1": 0.2}, expires_at=10.0)
    assert command.is_fresh(now=9.0)
    assert not command.is_fresh(now=11.0)


def test_joint_state_serializes_without_hardware():
    state = JointGroupState(device_id="arm-0", joint_names=["joint_1"])
    payload = state.as_dict()
    assert payload["device_id"] == "arm-0"
    assert payload["connected"] is False


def test_serial_joint_position_conversion_is_bounded_and_reversible():
    joint = SerialJointSpec("joint_1", servo_id=1, home_ticks=2048)
    assert round((joint.home_ticks + 512 - joint.home_ticks) * 360 / 4096, 5) == 45.0
    from blacknode_hardware.adapters.serial_joint import degrees_to_ticks, ticks_to_degrees
    assert degrees_to_ticks(45.0, joint) == 2560
    assert ticks_to_degrees(2560, joint) == 45.0


def test_service_reports_unconfigured_hardware_honestly():
    runtime = HardwareRuntime(device_id="pi-device")
    assert runtime.status() == {
        "device_id": "pi-device",
        "connected": False,
        "armed": False,
        "capabilities": [],
        "error": "no hardware adapter configured",
    }
    assert runtime.capabilities()["connected"] is False


def test_service_health_and_status_endpoints():
    server = create_server(HardwareRuntime(device_id="test-device"), port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{base}/health") as response:
            assert json.loads(response.read())["ok"] is True
        with urlopen(f"{base}/status") as response:
            assert json.loads(response.read())["device_id"] == "test-device"
    finally:
        server.shutdown()
        server.server_close()
