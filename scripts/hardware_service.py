"""Start the device-side service with an optional local hardware configuration."""

from __future__ import annotations

import argparse

from blacknode_hardware.device_config import load_device_config, serial_monitor_from_config
from blacknode_hardware.service import HardwareRuntime
from blacknode_hardware.service.server import serve


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--device-id")
    parser.add_argument("--config")
    args = parser.parse_args()
    provider = None
    config_device_id = "device"
    if args.config:
        config = load_device_config(args.config)
        config_device_id = config["device_id"]
        provider = serial_monitor_from_config(config)
        provider.connect()
    device_id = args.device_id or config_device_id
    serve(HardwareRuntime(provider=provider, device_id=device_id), args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
