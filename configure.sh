#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
venv_dir="$repo_dir/.venv"

if [[ ! -f "$venv_dir/bin/activate" ]]; then
  echo "Blacknode Hardware is not set up yet. Run ./setup_ubuntu.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source "$venv_dir/bin/activate"
cd "$repo_dir"
exec python "$repo_dir/scripts/configure_device.py" "$@"
