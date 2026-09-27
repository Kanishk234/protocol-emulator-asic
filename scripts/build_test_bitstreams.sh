#!/usr/bin/env bash
# Compile the example user designs (tools/compile/examples) into test/bitstreams/*.wbit, the real
# bitstreams test/test_bitstream.py loads through the host interface (RTL fabric model and CI's
# gl_test, which cannot run the compile flow itself). Deterministic (fixed nextpnr seed);
# `--check` rebuilds and fails if the committed files differ.
# Usage: scripts/build_test_bitstreams.sh [--check]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
if ! command -v nextpnr-generic >/dev/null && [ -d "$HOME/oss-cad-suite/bin" ]; then
  export PATH="$PATH:$HOME/oss-cad-suite/bin"
fi

OUT=test/bitstreams
status=0
mkdir -p "$OUT"
for yml in tools/compile/examples/*.yaml; do
  name=$(basename "$yml" .yaml)
  work="build/compile/$name"
  (cd tools && python -m compile.compile --pins "compile/examples/$name.yaml" -o "../$work" \
      "compile/examples/$name.v")
  if [ "${1:-}" = "--check" ]; then
    if ! cmp -s "$work/$name.wbit" "$OUT/$name.wbit"; then
      echo "error: $OUT/$name.wbit differs from a fresh build" >&2
      status=1
    fi
  else
    cp "$work/$name.wbit" "$OUT/"
    cp "$work/report.json" "$OUT/$name.report.json"
  fi
done
exit $status
