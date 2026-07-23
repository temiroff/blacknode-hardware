# blacknode-hardware

Generic hardware contracts and safe device-control foundations for Blacknode.

This package provides the stable boundary between Blacknode workflows and
physical devices. Workflows use capabilities such as `mobile_base`, `camera`,
`range_sensor`, `battery`, and `servo_bus`; replaceable adapters implement
those capabilities for a particular transport or device.

The initial foundation is intentionally hardware-independent:

- capability and device-state contracts
- disarmed-by-default motion authorization
- command freshness and velocity-limit validation
- a configurable I2C mecanum-base adapter
- a generic joint-group contract for real actuator adapters
- an editor node for capability inspection

The next implementation layer can add adapters for USB, serial, I²C, GPIO,
CAN, ROS 2, or a network hardware service without changing workflow names.

## Install

From the Blacknode repository root:

```powershell
blacknode packages install .\packages\blacknode-hardware
```

Or install the package checkout directly during development:

```powershell
pip install -e .\packages\blacknode-hardware
```

No device SDK is required for package discovery or contract inspection.

For a guided Ubuntu setup:

```bash
./setup_ubuntu.sh
./check.sh --software-only
```

The setup script installs packages and creates `.venv`. It reports the boot
configuration needed for I2C but does not silently rewrite system files.

Discover connected serial devices:

```bash
./discover.sh
```

Perform the first real hardware check with a read-only actuator probe:

```bash
./probe.sh --servos 6
```

`--servos 6` scans serial IDs 1 through 6. Without `--servos`, the probe
scans IDs 1 through 20. It reads present positions only and does not enable
torque, write goal positions, or move the arm. Override the connection
defaults when required:

```bash
BLACKNODE_SERIAL_PORT=/dev/ttyACM0 \
BLACKNODE_SERIAL_BAUDRATE=1000000 \
./probe.sh --servos 6
```

## Configure the device

Save the detected serial hardware for the device service:

```bash
./configure.sh --servos 6
```

The configuration is saved atomically to:

```text
.blacknode-hardware/device.json
```

This directory is ignored by Git. Running `configure.sh` again updates the
same configuration, so the device can be reconfigured at any time:

```bash
./configure.sh --show
./configure.sh --servos 7
./configure.sh --port auto
./configure.sh --port /dev/serial/by-id/DEVICE_PATH --baudrate 1000000
./configure.sh --device-id arm-01
```

Settings not included in a reconfiguration command are preserved. Configuration
and status monitoring are read-only and never enable torque or send goal
positions.

## Development

```powershell
python -m pytest packages\blacknode-hardware\tests
```

The included I2C adapter is the first physical hardware path; it requires
`smbus2` and an explicit device profile. Additional actuator and sensor
protocols belong in separate adapters and must implement the same contracts.
Serial device discovery uses `pyserial` and is installed with the package.

## Start on a Raspberry Pi

From the Pi:

```bash
git pull --ff-only
sudo ufw allow 8765/tcp
sudo ufw reload
./start.sh
```

The launcher uses:

```text
host: 0.0.0.0
port: 8765
```

It prints the Pi health URL. From your PC, open:

```text
http://PI_IP_ADDRESS:8765/health
http://PI_IP_ADDRESS:8765/status
http://PI_IP_ADDRESS:8765/capabilities
```

For example:

```text
http://192.168.1.87:8765/health
```

`/status` refreshes all configured servo positions on every request. It
reports both raw ticks and nominal degree values. Until calibration is added,
the response explicitly reports `"calibrated": false`. The service remains
read-only: it cannot arm or move the servos.

To verify the firewall and listener on the Pi:

```bash
sudo ufw status
ss -ltnp | grep 8765
```

From Windows PowerShell:

```powershell
Test-NetConnection PI_IP_ADDRESS -Port 8765
```

The health endpoint can work while status reports `"connected": false`; that
means the service is reachable but one or more configured servos did not
respond. Run `./probe.sh --servos 6` to check the serial connection directly.
