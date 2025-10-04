#!/bin/bash
set -euo pipefail

# 1) Build and install metadata-client first (dp-client depends on it)
echo "[dp-client] Building and installing metadata-client (dependency) ..."
./scripts/build_and_install_open_api_client.sh

echo "[dp-client] Building package..."
./scripts/build_dp_client.sh

echo "[dp-client] Locating built wheel..."
WHEEL=$(ls -t ./dp-client/dist/dp_client-*.whl 2>/dev/null | head -n1)
if [[ -z "${WHEEL}" ]]; then
  echo "[dp-client] Error: No dp_client wheel found in ./dp-client/dist/. Build may have failed."
  exit 1
fi
echo "[dp-client] Found wheel: ${WHEEL}"

PYVER=$(python -V 2>/dev/null || true)
if [[ -n "${PYVER}" ]]; then
  echo "[dp-client] Installing into Python: ${PYVER}"
else
  echo "[dp-client] Installing wheel (Python version unknown)"
fi
# Install without resolving dependencies since metadata-client was already installed locally above
pip install --no-deps "${WHEEL}" --force-reinstall

echo "[dp-client] Verifying installation..."
python - <<'PY'
import sys
try:
    from importlib import metadata as m
    import dp_client
    ver = m.version("dp-client")
    print(f"[dp-client] Installed successfully: dp-client=={ver}")
    print(f"[dp-client] Module location: {dp_client.__file__}")
except Exception as e:
    print(f"[dp-client] Verification failed: {e}", file=sys.stderr)
    sys.exit(1)
PY

echo "[dp-client] Done. Example quick check:"
echo "  python - <<'PY'"
echo "from dp_client import DPClient" 
echo "print('dp-client import OK, version:', getattr(__import__('dp_client'), '__version__', 'unknown'))" 
echo "PY"
