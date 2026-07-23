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
- an in-memory mobile-base provider for development and tests
- a configurable I2C mecanum-base adapter with a mock bus test path
- editor nodes for capability inspection and safe command preview

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

No device SDK is required for package discovery or the mock provider.

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

## Development

```powershell
python -m pytest packages\blacknode-hardware\tests
```

The mock provider is used for hardware-free development. The included I2C
adapter is the first physical hardware path; it requires `smbus2` and a device
profile. Add further providers only after their command, state, shutdown, and
safety contracts pass against the mock provider.
