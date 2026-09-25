#!/usr/bin/env bash
# Create or refresh the project venv (.venv) from requirements-dev.txt.
# Usage: scripts/setup_venv.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

echo "venv ready: source .venv/bin/activate"
