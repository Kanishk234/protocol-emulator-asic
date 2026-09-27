#!/usr/bin/env bash
# Local pre-flight of the chip hardening (PHYSICAL_DESIGN_AND_CI.md): TT's merged configuration
# through LibreLane up to detailed routing, then the checks that failed CI in phase 1:
#   - the configuration loads (BUGS #10);
#   - placement, power grid and routing complete, with the routing DRC count (BUGS #9);
#   - every vertical Metal4 power stripe spans the block height to within 10 um, as TT's
#     precheck pin check requires (BUGS #11).
# About 3 min for the phase 1 chip; not a substitute for CI (Nix LibreLane 3.0.0 vs CI 3.1.0.dev3,
# no sign-off DRC/LVS). Run it before every push that changes src/, arch/ or macro/.
#
# Usage: scripts/preflight.sh            Output: src/runs/preflight/ (git-ignored)
#        TO=OpenROAD.GlobalRouting scripts/preflight.sh   quick placement check (~6 min):
#        stop after global routing and print its overflow
# Needs: Nix (docs/VERSIONS.md), the tile library checkout in build/tile_cmos5l/fabulous-tiles
#        (its flake provides LibreLane), TT support tools and the full PDK in ~/.cache/warp.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/warp"
TT="$CACHE/tt-support-tools"
PDK_ROOT="${PDK_ROOT:-$CACHE/pdk-full}"
LIB="$ROOT/build/tile_cmos5l/fabulous-tiles"
TAG=preflight
cd "$ROOT"

# shellcheck disable=SC1091
source .venv/bin/activate
# the merged config refers to TT's files under ./tt, where CI checks out tt-support-tools
[ -e tt ] || ln -s "$TT" tt
echo "=== TT merged config (tt_tool --create-user-config --ihp)"
python "$TT/tt_tool.py" --create-user-config --ihp > build/preflight_tt.log 2>&1 \
  || { tail -20 build/preflight_tt.log; exit 1; }

echo "=== LibreLane to detailed routing (Nix)"
# shellcheck disable=SC1091
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
rm -rf "src/runs/$TAG"
(cd "$LIB" && nix develop --accept-flake-config --command bash -c \
  "cd '$ROOT/src' && librelane --pdk ihp-sg13cmos5l --pdk-root '$PDK_ROOT' --manual-pdk \
   --run-tag $TAG --to ${TO:-OpenROAD.DetailedRouting} config_merged.json") > build/preflight.log 2>&1 \
  || { grep -E 'ERROR|Error' build/preflight.log | tail -15; echo "preflight: flow FAILED (build/preflight.log)"; exit 1; }

RUN="src/runs/$TAG"
GRT=$(ls -d "$RUN"/*-openroad-globalrouting 2>/dev/null | head -1)
if [ -n "$GRT" ]; then
  echo "=== global routing (the judge of a placement: overflow should be 0)"
  grep -A8 "Final congestion report" "$GRT/openroad-globalrouting.log" | tail -7
fi
if [ "${TO:-}" = "OpenROAD.GlobalRouting" ]; then
  exit 0
fi
DEF=$(ls -t "$RUN"/*-openroad-detailedrouting/*.def 2>/dev/null | head -1)
[ -n "$DEF" ] || { echo "preflight: no detailed-routing DEF"; exit 1; }
echo "=== checks on $DEF"
python3 - "$DEF" "$RUN" <<'EOF'
import json, re, sys, glob
d, run = sys.argv[1], sys.argv[2]
t = open(d).read()
unit = int(re.search(r"UNITS DISTANCE MICRONS (\d+)", t).group(1))
x0, y0, x1, y1 = (int(v) / unit for v in re.search(r"DIEAREA \( (\d+) (\d+) \) \( (\d+) (\d+) \)", t).groups())
bad, n = [], 0
special = re.search(r"\nSPECIALNETS.*?END SPECIALNETS", t, re.S).group(0)
net = None
for line in special.splitlines():
    hm = re.match(r"\s*- (\S+)", line)
    if hm:
        net = hm.group(1)
    # vertical Metal4 stripe: ( x ya ) ( x yb ) or ( x ya ) ( * yb )
    seg = re.search(r"Metal4 (\d+) \+ SHAPE STRIPE \( (\d+) (\d+) \) \( (\d+|\*) (\d+) \)", line)
    if not seg or net not in ("VPWR", "VGND"):
        continue
    x, ya, x2, yb = seg.group(2), seg.group(3), seg.group(4), seg.group(5)
    if x2 not in ("*", x):
        continue                                  # horizontal
    x, ya, yb = int(x) / unit, int(ya) / unit, int(yb) / unit
    n += 1
    lo, hi = min(ya, yb), max(ya, yb)
    if lo - y0 > 10 or y1 - hi > 10:
        bad.append((net, x, lo, hi))
print(f"vertical Metal4 power stripes: {n}, not spanning the block height: {len(bad)}")
for b in bad[:10]:
    print("  short stripe", b)
metrics = sorted(glob.glob(f"{run}/*-openroad-detailedrouting/*.json")) + sorted(glob.glob(f"{run}/final/metrics.json"))
drc = None
for f in glob.glob(f"{run}/*-openroad-detailedrouting/state_out.json"):
    drc = json.load(open(f)).get("metrics", {}).get("route__drc_errors")
print(f"detailed-routing DRC errors: {drc}")
sys.exit(1 if bad or (drc not in (None, 0)) else 0)
EOF
echo "preflight: PASS"
