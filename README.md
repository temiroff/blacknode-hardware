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

Check a target Linux device before connecting hardware:

```bash
python scripts/hardware_doctor.py
python scripts/hardware_doctor.py --probe-address --bus 1 --address 0x7A
```

The default check does not touch the I2C bus. The optional address probe is
read-only and does not send motor commands.

When no physical device is connected, check only the software installation:

```bash
./check.sh --software-only
```

For a guided Ubuntu setup:

```bash
chmod +x scripts/setup_ubuntu.sh
./scripts/setup_ubuntu.sh
```

The setup script installs packages and creates `.venv`. It reports the boot
configuration needed for I2C but does not silently rewrite system files.

Discover connected serial devices:

```bash
./discover.sh
```

## Development

```powershell
python -m pytest packages\blacknode-hardware\tests
```

The included I2C adapter is the first physical hardware path; it requires
`smbus2` and an explicit device profile. Additional actuator and sensor
protocols belong in separate adapters and must implement the same contracts.
Serial device discovery uses `pyserial` and is installed with the package.

## Device service

The first device-side service milestone can be tested before an adapter is
configured:

```bash
python scripts/hardware_service.py
curl http://127.0.0.1:8765/health
curl http://127.0.0.1:8765/status
curl http://127.0.0.1:8765/capabilities
```

It reports an unconfigured device honestly. It does not simulate hardware or
send commands. The direct service command defaults to local-only. The
`start.sh` launcher below intentionally binds to the LAN interface for PC
testing; use it only on a trusted network until authentication is added.

## Start on a Raspberry Pi

From the Pi:

```bash
git pull --ff-only
source .venv/bin/activate
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

To verify the firewall and listener on the Pi:

```bash
sudo ufw status
ss -ltnp | grep 8765
```

From Windows PowerShell:

```powershell
Test-NetConnection PI_IP_ADDRESS -Port 8765
```

The health endpoint can work while the status endpoint reports
`"connected": false`; that means the service is reachable but no physical
hardware adapter has been configured yet.
