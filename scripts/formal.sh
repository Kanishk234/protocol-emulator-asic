#!/usr/bin/env bash
# WARP formal checks (docs/design/VERIFICATION.md F1–F3). Usage: scripts/formal.sh [name.sby ...]
# Needs the OSS CAD Suite (SymbiYosys, Yosys, Yices). Output goes to formal/<name>*/ (gitignored).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/formal"

if ! command -v sby >/dev/null && [ -d "$HOME/oss-cad-suite/bin" ]; then
  export PATH="$PATH:$HOME/oss-cad-suite/bin"
fi

jobs=("$@")
[ ${#jobs[@]} -eq 0 ] && jobs=(*.sby)
status=0
for f in "${jobs[@]}"; do
  echo "=== $f ==="
  if sby -f "$f" >"${f%.sby}.log" 2>&1; then
    grep -E "DONE|summary" "${f%.sby}.log" | tail -4
  else
    tail -20 "${f%.sby}.log"
    status=1
  fi
done
exit $status
