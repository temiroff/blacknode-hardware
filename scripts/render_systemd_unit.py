"""Render the systemd unit for the Blacknode hardware service."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


def unit_quote(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("systemd values cannot contain newlines")
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%")
    return f'"{escaped}"'


def working_directory_value(value: str) -> str:
    """Render a WorkingDirectory value without shell-style quotes."""
    if "\n" in value or "\r" in value:
        raise ValueError("systemd values cannot contain newlines")
    if any(character.isspace() for character in value) or "\\" in value or '"' in value:
        raise ValueError("the service repository path cannot contain spaces, quotes, or backslashes")
    return value.replace("%", "%%")


def render_unit(
    *,
    repo: Path,
    user: str,
    host: str,
    port: int,
    config: Path,
) -> str:
    repo = repo.resolve()
    config = config.resolve()
    python = repo / ".venv" / "bin" / "python"
    configure_script = repo / "scripts" / "configure_device.py"
    service_script = repo / "scripts" / "hardware_service.py"

    if not repo.is_absolute() or not config.is_absolute():
        raise ValueError("repository and configuration paths must be absolute")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", user):
        raise ValueError("service user contains unsupported characters")
    if not 1 <= port <= 65535:
        raise ValueError("service port must be from 1 to 65535")

    return "\n".join(
        [
            "[Unit]",
            "Description=Blacknode Hardware Service",
            "Wants=network-online.target",
            "After=network-online.target",
            "StartLimitIntervalSec=60",
            "StartLimitBurst=5",
            "",
            "[Service]",
            "Type=simple",
            f"User={user}",
            f"WorkingDirectory={working_directory_value(str(repo))}",
            'Environment="PYTHONUNBUFFERED=1"',
            (
                f"ExecStartPre={unit_quote(str(python))} "
                f"{unit_quote(str(configure_script))} "
                f"--config {unit_quote(str(config))} --show"
            ),
            (
                f"ExecStart={unit_quote(str(python))} "
                f"{unit_quote(str(service_script))} "
                f"--host {unit_quote(host)} --port {port} "
                f"--config {unit_quote(str(config))}"
            ),
            "Restart=on-failure",
            "RestartSec=2s",
            "TimeoutStopSec=10s",
            "KillSignal=SIGINT",
            "NoNewPrivileges=true",
            "PrivateTmp=true",
            "ProtectSystem=full",
            "UMask=0077",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--user", required=True)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(
        render_unit(
            repo=args.repo,
            user=args.user,
            host=args.host,
            port=args.port,
            config=args.config,
        ),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
