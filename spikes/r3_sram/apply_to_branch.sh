#!/usr/bin/env bash
# R3: turn the current checkout into the SRAM smoke project. Run it ONLY on the branch
# spike/r3-sram (it refuses to run on main): it replaces src/tt_um_tripwire.v, info.yaml,
# test/Makefile and test/test.py, adds src/{trw_sram.v, RM_...v, config.json, pdn_cfg.tcl}, and
# vendors the macro views into macro/. It changes files only; committing is up to you.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"

branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" != "spike/r3-sram" ]; then
  echo "apply_to_branch: on '$branch'; run this on spike/r3-sram only" >&2
  exit 1
fi

cp -r "$HERE/overlay/." "$ROOT/"
"$HERE/fetch_macro.sh" "$ROOT/macro/RM_IHPSG13_1P_512x16_c2_bm_bist"
git status --short
echo "apply_to_branch: done. Check with: git diff --stat; then commit and push the branch."
