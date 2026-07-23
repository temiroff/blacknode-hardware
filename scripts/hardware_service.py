"""Start the device-side service without a configured hardware adapter."""

from __future__ import annotations

import argparse

from blacknode_hardware.service import HardwareRuntime
from blacknode_hardware.service.server import serve


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--device-id", default="device")
    args = parser.parse_args()
    serve(HardwareRuntime(device_id=args.device_id), args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
