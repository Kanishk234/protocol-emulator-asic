#!/usr/bin/env bash
# R2: turn the current checkout into the lane + latch-array smoke project. Run it ONLY on the
# branch spike/r2-latch (it refuses to run anywhere else): it replaces src/tt_um_tripwire.v,
# info.yaml, test/Makefile and test/test.py, and copies the R1 lane files (spikes/r1_lane) into src/.
# src/config.json stays the template's. It changes files only; committing is up to you.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"

branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" != "spike/r2-latch" ]; then
  echo "apply_to_branch: on '$branch'; run this on spike/r2-latch only" >&2
  exit 1
fi

cp -r "$HERE/overlay/." "$ROOT/"
cp "$ROOT/spikes/r1_lane/"{trw_lane,trw_alu,trw_slots,trw_cport}.v "$ROOT/src/"
git status --short
echo "apply_to_branch: done. Check with: git diff --stat; then commit and push the branch."
