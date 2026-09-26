#!/usr/bin/env bash
# Phase 1 spike: stitch a tiny FABulous fabric (2 x LUT4x8_ha = 16 LUT4 + IO and edge tiles) on
# IHP CMOS5L with LibreLane's FABulousFabric flow. The tiles must be hardened first with
# spikes/tile_cmos5l/run.sh <TILE> (same patched tile library in build/tile_cmos5l/).
#
# Usage: spikes/fabric_tiny/run.sh [--tiles]     --tiles: harden every tile type first
# Output: build/fabric_tiny/ (GDS, LEF, netlist of the fabric macro + bitstream spec)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HERE="$ROOT/spikes/fabric_tiny"
LIB="$ROOT/build/tile_cmos5l/fabulous-tiles"
W="$ROOT/build/fabric_tiny"
export PDK=ihp-sg13cmos5l
export PDK_ROOT="${PDK_ROOT:-$HOME/.cache/warp/pdk-full}"
# shellcheck disable=SC1091
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh

TILES=$(sed -n 's#^Tile,TILES/\([^/]*\)/.*#\1#p' "$HERE/warp_tiny.csv")
if [ "${1:-}" = "--tiles" ]; then
  for t in $TILES; do
    echo "=== tile $t"
    timeout 1500 "$ROOT/spikes/tile_cmos5l/run.sh" "$t" >/dev/null || { echo "tile $t failed"; exit 1; }
  done
fi

rm -rf "$W"
mkdir -p "$W"
ln -s "$LIB" "$W/fabulous-tiles"
sed 's#TILES/#fabulous-tiles/tiles/tiny/#' "$HERE/warp_tiny.csv" > "$W/warp_tiny.csv"
cp "$HERE/config.yaml" "$W/config.yaml"

cd "$LIB"
nix develop --accept-flake-config --command bash -c \
  "cd '$W' && librelane --pdk $PDK --pdk-root '$PDK_ROOT' --manual-pdk config.yaml --save-views-to '$W/macro'" \
  > "$W/fabric.log" 2>&1 || { tail -30 "$W/fabric.log"; exit 1; }

# LEF abstract with OpenROAD (Magic is skipped, docs/BUGS.md #2); drop unused VIA definitions.
ODB=$(ls "$W"/macro/odb/*.odb)
cat > "$W/write_lef.tcl" <<EOF
read_db {$ODB}
write_abstract_lef -bloat_occupied_layers {$W/macro/lef/warp_tiny.lef}
EOF
mkdir -p "$W/macro/lef"
nix develop --accept-flake-config --command openroad -exit -no_splash "$W/write_lef.tcl" > "$W/lef.log" 2>&1
python3 - "$W/macro/lef/warp_tiny.lef" <<'EOF'
import re, sys
p = sys.argv[1]
lines = open(p).read().split("\n")
used = {m.group(1) for l in lines for m in [re.match(r"^\s+VIA\s+\S+\s+\S+\s+(\S+)", l)] if m}
out, skip = [], None
for l in lines:
    m = re.match(r"^VIA\s+(\S+)", l)
    if skip is None and m and m.group(1) not in used:
        skip = m.group(1); continue
    if skip is not None:
        if l.strip() == f"END {skip}": skip = None
        continue
    out.append(l)
open(p, "w").write("\n".join(out))
EOF
# Placement boundary (IHP 189/4) over the whole macro, from the LEF size
read -r MW MH < <(sed -n 's/^ *SIZE \([0-9.]*\) BY \([0-9.]*\) ;/\1 \2/p' "$W/macro/lef/warp_tiny.lef" | head -1)
nix develop --accept-flake-config --command klayout -b -r "$HERE/add_prboundary.py" \
  -rd gds="$W/macro/gds/warp_tiny.gds" -rd out="$W/macro/gds/warp_tiny.gds" -rd w="$MW" -rd h="$MH" 2>/dev/null

# Export the macro views the chip flow uses into the repo (macro/warp_tiny/)
OUT="$ROOT/macro/warp_tiny"
mkdir -p "$OUT"
cp "$W/macro/gds/warp_tiny.gds" "$W/macro/lef/warp_tiny.lef" "$OUT/"
cp "$W"/macro/nl/warp_tiny.nl.v "$OUT/warp_tiny.nl.v"
cp "$W/macro/fabulous/warp_tiny.v" "$OUT/warp_tiny.v"              # RTL of the fabric (simulation)
cp "$W/macro/fabulous/bitStreamSpec.csv" "$OUT/"
# gate-level netlists of the tiles the fabric netlist instantiates (for LVS and gate-level sim)
mkdir -p "$OUT/tiles"
for t in $TILES; do
  cp "$LIB/tiles/tiny/$t/macro/ihp-sg13cmos5l/nl/$t.nl.v" "$OUT/tiles/"
done
echo "fabric macro: $OUT ($MW x $MH um)"
