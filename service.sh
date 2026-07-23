#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
venv_python="$repo_dir/.venv/bin/python"
unit_name="blacknode-hardware.service"
port="${BLACKNODE_HARDWARE_PORT:-8765}"

usage() {
  echo "Usage: ./service.sh COMMAND"
  echo
  echo "Commands:"
  echo "  status              Show systemd status and service health"
  echo "  start               Start and validate the service"
  echo "  stop                Stop the service"
  echo "  restart             Restart and validate the service"
  echo "  check [OPTIONS]     Check HTTP and hardware status"
  echo "  logs                Show the latest service logs"
  echo "  follow              Follow service logs"
}

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This service manager is intended for Ubuntu/Linux."
  exit 1
fi
if [[ ! -x "$venv_python" ]]; then
  echo "Blacknode Hardware is not set up yet. Run ./setup_ubuntu.sh first."
  exit 1
fi

command_name="${1:-}"
if [[ -z "$command_name" ]]; then
  usage
  exit 2
fi
shift

check_service() {
  "$venv_python" "$repo_dir/scripts/service_check.py" \
    --url "http://127.0.0.1:$port" "$@"
}

case "$command_name" in
  status)
    sudo systemctl --no-pager --full status "$unit_name" || true
    echo
    check_service
    ;;
  start)
    sudo systemctl start "$unit_name"
    check_service --wait 15 "$@"
    ;;
  stop)
    sudo systemctl stop "$unit_name"
    echo "Blacknode Hardware service stopped."
    ;;
  restart)
    sudo systemctl restart "$unit_name"
    check_service --wait 15 "$@"
    ;;
  check)
    check_service "$@"
    ;;
  logs)
    sudo journalctl -u "$unit_name" -n 100 --no-pager
    ;;
  follow)
    sudo journalctl -u "$unit_name" -f
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown command: $command_name"
    usage
    exit 2
    ;;
esac
