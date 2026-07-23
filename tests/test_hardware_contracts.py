from __future__ import annotations

import pytest

from blacknode_hardware import (
    I2CMecanumBase,
    I2CMecanumConfig,
    JointGroupCommand,
    MockMobileBase,
    MockJointGroup,
    MobileBaseCommand,
    SafetyGate,
    SafetyLimits,
)


class FakeBus:
    def __init__(self):
        self.writes = []

    def write_i2c_block_data(self, address, register, values):
        self.writes.append((address, register, list(values)))


def test_mock_provider_starts_disarmed():
    provider = MockMobileBase()
    assert provider.state().connected is True
    assert provider.state().armed is False
    with pytest.raises(PermissionError):
        provider.command(MobileBaseCommand(linear_x=0.1))


def test_mock_provider_requires_arm_and_keeps_state():
    provider = MockMobileBase()
    provider.arm()
    state = provider.command(MobileBaseCommand(linear_x=0.1))
    assert state.armed is True
    assert state.values["mobile_base_command"]["linear_x"] == 0.1
    provider.disarm()
    assert provider.state().values["mobile_base_command"]["linear_x"] == 0.0


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


def test_i2c_provider_writes_four_motors_after_arm():
    bus = FakeBus()
    provider = I2CMecanumBase(bus=bus, config=I2CMecanumConfig(motor_register_start=31))
    provider.arm()
    state = provider.command(MobileBaseCommand(linear_x=0.1))
    assert state.values["mobile_base_command"]["wheels"] == [-40, 40, -40, 40]
    assert [write[1] for write in bus.writes] == [31, 32, 33, 34]


def test_i2c_provider_watchdog_stops_all_motors():
    bus = FakeBus()
    provider = I2CMecanumBase(
        bus=bus,
        config=I2CMecanumConfig(command_timeout=0.5),
    )
    provider.arm()
    provider.command(MobileBaseCommand(linear_x=0.1))
    provider.watchdog_tick(now=provider._last_command_at + 1.0)
    assert bus.writes[-4:] == [
        (0x7A, 31, [0]),
        (0x7A, 32, [0]),
        (0x7A, 33, [0]),
        (0x7A, 34, [0]),
    ]


def test_mock_joint_group_is_disarmed_and_enforces_limits():
    provider = MockJointGroup(
        joint_names=["joint_1"],
        limits={"joint_1": {"min": -1.0, "max": 1.0}},
    )
    with pytest.raises(PermissionError):
        provider.command(JointGroupCommand({"joint_1": 0.2}))
    provider.arm()
    provider.command(JointGroupCommand({"joint_1": 0.2}))
    assert provider.state().positions["joint_1"] == 0.2
    with pytest.raises(ValueError):
        provider.command(JointGroupCommand({"joint_1": 2.0}))


def test_mock_joint_group_rejects_unknown_joint():
    provider = MockJointGroup(joint_names=["joint_1"])
    provider.arm()
    with pytest.raises(ValueError, match="unknown joints"):
        provider.command(JointGroupCommand({"joint_2": 0.0}))
