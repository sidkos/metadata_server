#!/usr/bin/env bash
set -euo pipefail

# Install all requirement sets used in this repository in one go.
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

PY="${PYTHON_BINARY:-$(command -v python || command -v python3)}"
PIP="$PY -m pip"

if [ -z "$PY" ]; then
  echo "[ERROR] Python interpreter not found in PATH" >&2
  exit 1
fi

echo "[env] Python: $($PY --version 2>&1)"
echo "[env] Pip:    $($PIP --version 2>&1)"

# Optional: keep pip modern to reduce resolver issues
if [ "${UPGRADE_PIP:-1}" = "1" ]; then
  echo "[step] Upgrading pip (can be disabled with UPGRADE_PIP=0)"
  $PIP install --upgrade pip >/dev/null
fi

install_requirements() {
  local file="$1"
  if [ -f "$file" ]; then
    echo "[install] $file"
    $PIP install -r "$file"
  else
    echo "[skip] $file (not found)"
  fi
}

install_requirements "$ROOT/requirements-build-client.txt"

install_requirements "$ROOT/requirements-dev.txt"

install_requirements "$ROOT/requirements.txt"

install_requirements "$ROOT/dp-client/requirements.txt"

echo "[done] All requirement sets processed."