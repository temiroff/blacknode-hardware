from __future__ import annotations

import pytest
from pathlib import Path
import subprocess
import sys
import threading
from urllib.request import urlopen
import json

from blacknode_hardware import (
    I2CMecanumBase,
    SerialJointConfig,
    SerialJointMonitor,
    SerialJointSpec,
    JointGroupCommand,
    JointGroupState,
    MobileBaseCommand,
    SafetyGate,
    SafetyLimits,
)
from blacknode_hardware.service import HardwareRuntime
from blacknode_hardware.service.server import create_server
from blacknode_hardware.device_config import load_device_config
from scripts.render_systemd_unit import render_unit, unit_quote


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


def test_serial_monitor_exposes_no_write_or_motion_methods():
    monitor = SerialJointMonitor(
        SerialJointConfig(port="/dev/not-opened", joints=(SerialJointSpec("servo_1", 1),))
    )
    assert not hasattr(monitor, "arm")
    assert not hasattr(monitor, "command")
    assert not hasattr(monitor, "stop")


def test_configuration_can_be_replaced_and_preserves_unspecified_settings(tmp_path: Path):
    config_path = tmp_path / "device.json"
    repo_dir = Path(__file__).parents[1]
    first = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.configure_device",
            "--config",
            str(config_path),
            "--port",
            "/dev/serial/by-id/example",
            "--servos",
            "6",
            "--device-id",
            "arm-01",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_dir,
    )
    assert first.returncode == 0, first.stderr

    second = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.configure_device",
            "--config",
            str(config_path),
            "--servos",
            "7",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=repo_dir,
    )
    assert second.returncode == 0, second.stderr
    config = load_device_config(config_path)
    assert config["device_id"] == "arm-01"
    assert config["port"] == "/dev/serial/by-id/example"
    assert len(config["servos"]) == 7


def test_systemd_unit_uses_validated_config_and_failure_restart(tmp_path: Path):
    repo_dir = tmp_path / "blacknode-hardware"
    config_path = repo_dir / ".blacknode-hardware" / "device.json"
    unit = render_unit(
        repo=repo_dir,
        user="alex",
        host="0.0.0.0",
        port=8765,
        config=config_path,
    )
    assert "User=alex" in unit
    assert "ExecStartPre=" in unit
    assert f"--config {unit_quote(str(config_path.resolve()))} --show" in unit
    assert "Restart=on-failure" in unit
    assert "WantedBy=multi-user.target" in unit


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


def test_service_check_distinguishes_service_health_from_hardware_readiness():
    server = create_server(HardwareRuntime(device_id="test-device"), port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    repo_dir = Path(__file__).parents[1]
    command = [
        sys.executable,
        str(repo_dir / "scripts" / "service_check.py"),
        "--url",
        f"http://127.0.0.1:{server.server_port}",
    ]
    try:
        service_only = subprocess.run(command, check=False, capture_output=True, text=True)
        hardware_required = subprocess.run(
            [*command, "--require-hardware"],
            check=False,
            capture_output=True,
            text=True,
        )
        assert service_only.returncode == 0
        assert "[WARN] Hardware: not connected" in service_only.stdout
        assert hardware_required.returncode == 2
    finally:
        server.shutdown()
        server.server_close()
