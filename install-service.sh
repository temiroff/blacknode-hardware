#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
venv_python="$repo_dir/.venv/bin/python"
config="${BLACKNODE_HARDWARE_CONFIG:-$repo_dir/.blacknode-hardware/device.json}"
token_file="${BLACKNODE_AUTH_TOKEN_FILE:-$repo_dir/.blacknode-hardware/auth.token}"
host="${BLACKNODE_HARDWARE_HOST:-0.0.0.0}"
port="${BLACKNODE_HARDWARE_PORT:-8765}"
service_user="$(id -un)"
unit_name="blacknode-hardware.service"
unit_path="/etc/systemd/system/$unit_name"
print_only=false

if [[ "${1:-}" == "--print" ]]; then
  print_only=true
  shift
fi
if (($#)); then
  echo "Usage: ./install-service.sh [--print]"
  exit 2
fi

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This installer is intended for Ubuntu/Linux."
  exit 1
fi
if [[ "$(id -u)" -eq 0 ]]; then
  echo "Run this installer as your normal user, not as root."
  exit 1
fi
if [[ ! -x "$venv_python" ]]; then
  echo "Blacknode Hardware is not set up yet. Run ./setup_ubuntu.sh first."
  exit 1
fi
if [[ ! -f "$config" ]]; then
  echo "No hardware configuration found."
  echo "Run ./configure.sh --servos 6 first."
  exit 1
fi
if [[ ! -f "$token_file" ]]; then
  echo "No pairing token found."
  echo "Run ./pair.sh first."
  exit 1
fi
if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemd is not available on this device."
  exit 1
fi

echo "Validating hardware configuration..."
"$venv_python" "$repo_dir/scripts/configure_device.py" --config "$config" --show
echo
echo "Validating pairing credentials..."
"$venv_python" "$repo_dir/scripts/pair_device.py" \
  --config "$config" \
  --token-file "$token_file" \
  --validate

unit_file="$(mktemp --suffix=.service)"
unit_new="${unit_path}.new"
cleanup() {
  rm -f -- "$unit_file"
}
trap cleanup EXIT

"$venv_python" "$repo_dir/scripts/render_systemd_unit.py" \
  --repo "$repo_dir" \
  --user "$service_user" \
  --host "$host" \
  --port "$port" \
  --config "$config" \
  --auth-token-file "$token_file" > "$unit_file"

if command -v systemd-analyze >/dev/null 2>&1; then
  systemd-analyze verify "$unit_file"
fi

if [[ "$print_only" == true ]]; then
  printf '\n'
  printf '%s\n' "Generated $unit_name"
  printf '%s\n' "==============================="
  command cat "$unit_file"
  exit 0
fi

echo
echo "Installing $unit_name..."
sudo install -m 0644 "$unit_file" "$unit_new"
sudo mv -f -- "$unit_new" "$unit_path"
sudo systemctl daemon-reload
sudo systemctl enable "$unit_name"
if ! sudo systemctl restart "$unit_name"; then
  echo "The service could not start. Stop any manually running ./start.sh and retry."
  sudo systemctl --no-pager --full status "$unit_name" || true
  exit 1
fi

if ! "$repo_dir/service.sh" check --wait 15 --require-hardware; then
  echo
  echo "The service was installed, but validation did not fully pass."
  echo "Run ./service.sh logs to inspect it."
  exit 1
fi

echo
echo "Service installed and enabled at boot."
echo "Re-run ./install-service.sh anytime to update its configuration."
echo "Use ./service.sh status, restart, check, or logs."
