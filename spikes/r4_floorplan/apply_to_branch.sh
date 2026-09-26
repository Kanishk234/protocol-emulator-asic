#!/usr/bin/env bash
# R4: turn the current checkout into the full-size floorplan spike. Run it ONLY on the branch
# spike/r4-floorplan (it refuses to run anywhere else): it replaces info.yaml, test/Makefile,
# test/test.py and src/ (tt_um_tripwire.v, config.json, and the files sources.sh lists), and vendors the
# SRAM macro into macro/. It changes files only; committing is up to you.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" != "spike/r4-floorplan" ]; then
  echo "apply_to_branch: on '$branch'; run this on spike/r4-floorplan only" >&2
  exit 1
fi
python3 "$HERE/gen_fabric.py" --check
cp "$HERE/overlay/info.yaml" "$ROOT/info.yaml"
cp "$HERE/overlay/test/Makefile" "$HERE/overlay/test/test.py" "$ROOT/test/"
"$HERE/sources.sh" "$ROOT/src"
cp -r "$ROOT/spikes/r3_sram/overlay/macro" "$ROOT/"          # the macro README (provenance)
[ -f "$ROOT/spikes/r3_sram/overlay/.gitattributes" ] && cp "$ROOT/spikes/r3_sram/overlay/.gitattributes" "$ROOT/"
"$ROOT/spikes/r3_sram/fetch_macro.sh" "$ROOT/macro/RM_IHPSG13_1P_512x16_c2_bm_bist"
git status --short
echo "apply_to_branch: done. Check with: git diff --stat; then commit and push the branch."
