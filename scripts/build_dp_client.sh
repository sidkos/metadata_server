#!/bin/bash
set -euo pipefail

PKG_DIR="dp-client"
PKG_NAME="dp-client"

# Ensure Poetry is present
if ! command -v poetry >/dev/null 2>&1; then
  echo "[dp-client] Poetry not found. Installing via pip..."
  pip install poetry
fi

# Read version from repo root setup.py (align with metadata-client)
VERSION=$(grep "__version__" setup.py | awk -F '"' '{print $2}')
if [[ -z "${VERSION}" ]]; then
  echo "[dp-client] Could not determine version from setup.py"
  exit 1
fi

pushd "$PKG_DIR" >/dev/null

# Optionally pin metadata-client dependency.
# If version is 0.0.0 (local-only), avoid exact pin to prevent resolver hitting remote index.
if grep -q '^metadata-client' pyproject.toml; then
  if [[ "${VERSION}" == "0.0.0" ]]; then
    echo "[dp-client] Detected local development version (0.0.0). Using unpinned dependency for metadata-client."
    sed -e "s/^metadata-client *=.*$/metadata-client = \"*\"/" pyproject.toml > pyproject.toml.tmp
  else
    echo "[dp-client] Pinning metadata-client dependency to =${VERSION}"
    sed -e "s/^metadata-client *=.*$/metadata-client = \"=${VERSION}\"/" pyproject.toml > pyproject.toml.tmp
  fi
  mv pyproject.toml.tmp pyproject.toml
fi

# Set the package version
poetry version "${VERSION}"

echo "[dp-client] Installing build dependencies (poetry-core, etc.)"
# Poetry will manage build env; ensure lock is up-to-date is not required for build

echo "[dp-client] Building the dp-client wheel with Poetry"
poetry build

popd >/dev/null

echo "[dp-client] Build complete. Artifacts in ${PKG_DIR}/dist/"