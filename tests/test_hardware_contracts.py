from __future__ import annotations

import pytest

from blacknode_hardware import (
    I2CMecanumBase,
    JointGroupCommand,
    JointGroupState,
    MobileBaseCommand,
    SafetyGate,
    SafetyLimits,
)


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
