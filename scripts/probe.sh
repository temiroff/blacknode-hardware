#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="$repo_dir/.venv"
port="${BLACKNODE_SERIAL_PORT:-}"
baudrate="${BLACKNODE_SERIAL_BAUDRATE:-1000000}"
ids="${BLACKNODE_SERVO_IDS:-1-20}"

if [[ ! -f "$venv_dir/bin/activate" ]]; then
  echo "Blacknode Hardware is not set up yet. Run ./setup_ubuntu.sh first."
  exit 1
fi

if [[ -z "$port" ]]; then
  for candidate in /dev/serial/by-id/* /dev/ttyACM* /dev/ttyUSB*; do
    if [[ -e "$candidate" ]]; then port="$candidate"; break; fi
  done
fi

if [[ -z "$port" ]]; then
  echo "No serial device found. Run ./discover.sh after connecting the device."
  exit 1
fi

# shellcheck disable=SC1091
source "$venv_dir/bin/activate"
echo "Read-only serial actuator probe"
echo "Port: $port"
echo "Baudrate: $baudrate"
echo "Servo IDs: $ids"
python "$repo_dir/scripts/serial_probe.py" --port "$port" --baudrate "$baudrate" --ids "$ids"
