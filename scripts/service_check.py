"""Validate the running Blacknode hardware service over its real HTTP API."""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


def color(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text


def get_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    with urlopen(url, timeout=timeout) as response:
        value = json.loads(response.read())
    if not isinstance(value, dict):
        raise ValueError(f"{url} did not return a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--wait", type=float, default=0.0)
    parser.add_argument("--require-hardware", action="store_true")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    deadline = time.monotonic() + max(0.0, args.wait)
    error = ""
    health: dict[str, Any] | None = None
    while True:
        try:
            health = get_json(f"{base_url}/health", timeout=2.0)
            if health.get("ok") is True:
                break
            error = "health endpoint did not report ok"
        except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
            error = str(exc)
        if time.monotonic() >= deadline:
            break
        time.sleep(0.5)

    print("Blacknode Hardware service check")
    print("================================")
    if health is None or health.get("ok") is not True:
        print(f"{color('31', '[FAIL]')} Service: {error or 'not reachable'}")
        return 1
    print(f"{color('32', '[OK]')} Service: {base_url}")

    try:
        status = get_json(f"{base_url}/status")
        capabilities = get_json(f"{base_url}/capabilities")
    except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
        print(f"{color('31', '[FAIL]')} Status: {exc}")
        return 1

    connected = status.get("connected") is True
    marker = color("32", "[OK]") if connected else color("33", "[WARN]")
    print(f"{marker} Hardware: {'connected' if connected else 'not connected'}")
    print(f"  Device ID: {status.get('device_id', 'unknown')}")
    print(f"  Armed: {bool(status.get('armed', False))}")
    print(f"  Calibrated: {bool(status.get('calibrated', False))}")
    print(f"  Joints: {len(status.get('joint_names') or [])}")
    print(f"  Capabilities: {', '.join(capabilities.get('capabilities') or []) or 'none'}")
    if status.get("error"):
        print(f"  Error: {status['error']}")
    if args.require_hardware and not connected:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
