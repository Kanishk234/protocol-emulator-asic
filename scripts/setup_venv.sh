#!/usr/bin/env bash
# Create or refresh the project venv (.venv) from requirements-dev.txt.
# Usage: scripts/setup_venv.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# FABulous 2.2.0 needs >=3.12; pinned cocotb 2.0.1 supports <=3.13.
# Select an installed compatible interpreter without modifying system Python.
PYTHON_BIN="${WARP_PYTHON:-python3}"
if [ -x .venv/bin/python ]; then
  PYTHON_BIN=.venv/bin/python
fi
"$PYTHON_BIN" -c 'import sys; assert (3, 12) <= sys.version_info[:2] <= (3, 13), "Use Python 3.12 or 3.13 (set WARP_PYTHON); existing .venv must also use that version"'
if [ ! -x .venv/bin/python ]; then
  "$PYTHON_BIN" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

echo "venv ready: source .venv/bin/activate"
