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
positions. If the persistent service is already installed, apply configuration
changes with:

```bash
./service.sh restart
```

## Pair the device

Create a private device token before installing the persistent service:

```bash
./pair.sh
```

The token is stored at `.blacknode-hardware/auth.token`, outside Git, with
owner-only file permissions. Save the displayed token for the Blacknode editor
device connection. Pairing can be inspected or replaced later:

```bash
./pair.sh --show
./pair.sh --rotate
```

Rotation immediately invalidates the previous token and restarts an active
hardware service. `/health` remains public for reachability checks.
`/status`, `/capabilities`, and `/rpc` require:

```text
Authorization: Bearer PAIRING_TOKEN
```

## Development

```powershell
python -m pytest packages\blacknode-hardware\tests
```

The included I2C adapter is the first physical hardware path; it requires
`smbus2` and an explicit device profile. Additional actuator and sensor
protocols belong in separate adapters and must implement the same contracts.
Serial device discovery uses `pyserial` and is installed with the package.

## Run once on a Raspberry Pi

For a foreground test that stops when the terminal closes:

```bash
./start.sh
```

Press `Ctrl+C` before installing the persistent service.

## Install the persistent service

Install and start the systemd service:

```bash
./pair.sh
./install-service.sh
```

The installer:

- validates `.blacknode-hardware/device.json`
- validates the private pairing token
- generates the service with the current repository path and Linux user
- enables automatic startup after reboot
- restarts the service after a failure
- waits for the HTTP service and connected hardware to pass validation

Re-running `install-service.sh` safely updates the existing service definition.
Use the service manager afterward:

```bash
./service.sh status
./service.sh check --require-hardware
./service.sh restart
./service.sh logs
./service.sh follow
./service.sh stop
./service.sh start
```

`status` shows systemd state and performs a live HTTP check. `logs` shows the
latest 100 journal entries; `follow` streams new entries until `Ctrl+C`.

The service uses:

```text
host: 0.0.0.0
port: 8765
```

Allow the port through Ubuntu's firewall once:

```bash
sudo ufw allow 8765/tcp
sudo ufw reload
```

From your PC, the public health URL can be opened directly:

```text
http://PI_IP_ADDRESS:8765/health
```

For example:

```text
http://192.168.1.87:8765/health
```

Use the pairing token for protected endpoints. From PowerShell:

```powershell
$token = Read-Host "Pairing token"
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod http://PI_IP_ADDRESS:8765/status -Headers $headers
Invoke-RestMethod http://PI_IP_ADDRESS:8765/capabilities -Headers $headers
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

Pairing authenticates access but plain HTTP does not encrypt the token or
traffic. Keep the service on a trusted LAN. Use a VPN or HTTPS before internet
exposure, deployment uploads, or motion control.
