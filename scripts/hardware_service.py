"""Start the device-side service with an optional local hardware configuration."""

from __future__ import annotations

import argparse
from pathlib import Path

from blacknode_hardware.auth import load_auth_token, token_fingerprint
from blacknode_hardware.device_config import load_device_config, serial_monitor_from_config
from blacknode_hardware.service import HardwareRuntime
from blacknode_hardware.service.server import serve


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--device-id")
    parser.add_argument("--config")
    parser.add_argument("--auth-token-file")
    parser.add_argument("--require-auth", action="store_true")
    args = parser.parse_args()
    provider = None
    config_device_id = "device"
    if args.config:
        config = load_device_config(args.config)
        config_device_id = config["device_id"]
        provider = serial_monitor_from_config(config)
        provider.connect()
    auth_token = None
    token_path = Path(args.auth_token_file) if args.auth_token_file else None
    if token_path is None and args.config:
        token_path = Path(args.config).parent / "auth.token"
    if token_path is not None and token_path.exists():
        auth_token = load_auth_token(token_path)
    elif args.require_auth:
        parser.error(f"pairing token not found: {token_path}")
    device_id = args.device_id or config_device_id
    if auth_token:
        print(f"pairing authentication enabled ({token_fingerprint(auth_token)})")
    else:
        print("pairing authentication is not configured; read-only trusted-LAN mode")
    serve(
        HardwareRuntime(provider=provider, device_id=device_id),
        args.host,
        args.port,
        auth_token=auth_token,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
