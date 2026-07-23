#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
venv_python="$repo_dir/.venv/bin/python"
config="${BLACKNODE_HARDWARE_CONFIG:-$repo_dir/.blacknode-hardware/device.json}"
token_file="${BLACKNODE_AUTH_TOKEN_FILE:-$repo_dir/.blacknode-hardware/auth.token}"
unit_name="blacknode-hardware.service"
action="${1:-}"
token_existed=false

if [[ ! -x "$venv_python" ]]; then
  echo "Blacknode Hardware is not set up yet. Run ./setup_ubuntu.sh first."
  exit 1
fi
if [[ ! -f "$config" ]]; then
  echo "No hardware configuration found."
  echo "Run ./configure.sh --servos 6 first."
  exit 1
fi
if [[ -f "$token_file" ]]; then
  token_existed=true
fi

cd "$repo_dir"
"$venv_python" "$repo_dir/scripts/pair_device.py" \
  --config "$config" \
  --token-file "$token_file" \
  "$@"

credentials_changed=false
if [[ "$action" == "--rotate" || "$token_existed" == false ]]; then
  credentials_changed=true
fi

if [[ "$credentials_changed" == true ]] && command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet "$unit_name"; then
    echo
    echo "Restarting the hardware service to apply pairing..."
    sudo systemctl restart "$unit_name"
    "$repo_dir/service.sh" check --wait 15 --require-hardware
  else
    echo
    echo "Pairing is ready. Run ./install-service.sh to install the persistent service."
  fi
fi
