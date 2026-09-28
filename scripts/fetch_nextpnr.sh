#!/usr/bin/env bash
# Fetch the nextpnr the compile flow uses (D-028): OSS CAD Suite 2026-09-27, unpacked to
# ~/.cache/warp/ocs-2026-09-27 next to the pinned 2026-06-29 suite (Yosys, FABulous). Only its
# nextpnr-generic is used: it reads timing arcs for the WARP hard primitives
# (macro/<fabric>/fabulous/.FABulous/placement_estimate.txt, BUGS #17).
# Prints the nextpnr-generic path.
set -euo pipefail
TAG=2026-09-27
DEST="${WARP_NEXTPNR_DIR:-$HOME/.cache/warp/ocs-$TAG}"
NP="$DEST/oss-cad-suite/bin/nextpnr-generic"
if [ ! -x "$NP" ]; then
  mkdir -p "$DEST"
  tmp=$(mktemp)
  curl -sfL -o "$tmp" "https://github.com/YosysHQ/oss-cad-suite-build/releases/download/$TAG/oss-cad-suite-linux-x64-${TAG//-/}.tgz"
  tar -xzf "$tmp" -C "$DEST"
  rm -f "$tmp"
fi
"$NP" --version 2>&1 | grep -q "nextpnr-0.11.1-34-gc4fbb55a" || { echo "error: unexpected nextpnr version" >&2; exit 1; }
echo "$NP"
