#!/usr/bin/env bash
# Cross-check of the hard-primitive timing model (tools/timing/README.md) against STA of the
# hardened primitive tile PRIM2T2S (its routed netlist and extracted parasitics, slow-corner
# liberty). At the tile boundary, the hardened tile's worst
#   - clock -> tile output wire (primitive flip-flop, primitive logic, switch matrix) and
#   - tile input wire -> primitive flip-flop (switch matrix, primitive logic, setup)
# must not exceed what the compile flow's model allows for the same paths: the primitive arcs
# (placement_estimate.txt, with margin) plus the worst pip delay nextpnr uses for the switch
# matrix hop (pips.nom_slow_1p08V_125C.txt). Configuration latches are static: false paths.
#
# Usage: tools/timing/tile_check.sh [tile run dir]     Needs: Nix LibreLane env (OpenSTA), the PDK.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TILES="$ROOT/build/tile_cmos5l/fabulous-tiles"
# Default must match the committed tile, not a newer rejected experiment.
warp_fabric="$(cat "$ROOT/arch/CURRENT")"
warp_committed_tile="$ROOT/macro/$warp_fabric/tiles/PRIM2T2S.nl.v"
RUN="${1:-}"
if [ -z "$RUN" ]; then
  for warp_run in "$TILES"/tiles/tiny/PRIM2T2S/runs/*/; do
    if [ -r "$warp_run/final/nl/PRIM2T2S.nl.v" ] &&
       cmp -s "$warp_committed_tile" "$warp_run/final/nl/PRIM2T2S.nl.v" &&
       { [ -z "$RUN" ] || [ "$warp_run/final/nl/PRIM2T2S.nl.v" -nt "$RUN/final/nl/PRIM2T2S.nl.v" ]; }; then
      RUN="$warp_run"
    fi
  done
  if [ -z "$RUN" ]; then
    echo "tile_check: no completed run matches $warp_committed_tile" >&2
    echo "Restore its matching archived netlist/SPEF; newer experimental runs are not evidence for the committed tile." >&2
    exit 1
  fi
fi
for warp_required in "$RUN/final/nl/PRIM2T2S.nl.v" "$RUN/final/spef/nom/PRIM2T2S.nom.spef"; do
  if [ ! -r "$warp_required" ]; then
    echo "tile_check: missing hardened-tile artifact: $warp_required" >&2
    echo "Restore the matching PRIM2T2S netlist and SPEF, or rebuild the tile; pass its completed run directory as the first argument." >&2
    echo "A netlist-only check cannot reproduce the routed timing comparison (tools/timing/README.md)." >&2
    exit 1
  fi
done
if ! cmp -s "$warp_committed_tile" "$RUN/final/nl/PRIM2T2S.nl.v"; then
  if [ "${WARP_TIMING_ALLOW_VARIANT:-0}" != 1 ]; then
    echo "tile_check: supplied netlist differs from the committed tile; set WARP_TIMING_ALLOW_VARIANT=1 only for a labeled experimental comparison." >&2
    exit 1
  fi
  echo "tile_check: EXPERIMENTAL VARIANT; this does not refresh committed-tile timing evidence." >&2
fi
PDK_ROOT="${PDK_ROOT:-$HOME/.cache/warp/pdk-full}"
LIB="$PDK_ROOT/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib"
W="$ROOT/build/prim_sta"
mkdir -p "$W"
cat > "$W/tile.tcl" <<TCL
read_liberty $LIB
read_verilog $RUN/final/nl/PRIM2T2S.nl.v
link_design PRIM2T2S
read_spef $RUN/final/spef/nom/PRIM2T2S.nom.spef
set drv [get_pins -of_objects [get_nets GCLK_BEG] -filter "direction == output"]
create_clock -name clk -period 100 \$drv
set_input_delay 0 -clock clk [all_inputs]
set_output_delay 0 -clock clk [all_outputs]
set_false_path -from [all_registers -level_sensitive]
set_false_path -through [all_registers -level_sensitive]
set_input_transition 0.2 [all_inputs]
set_load 0.01 [all_outputs]
set ffs [all_registers -edge_triggered]
set p [find_timing_paths -from [all_registers -edge_triggered -clock_pins] -to [all_outputs] -path_delay max -group_path_count 1]
if {[llength \$p]} { puts "TILE clk2out_max [expr {100.0 - [get_property [lindex \$p 0] slack]}] [get_full_name [get_property [lindex \$p 0] endpoint]]" }
set p [find_timing_paths -from [all_inputs] -to [all_registers -edge_triggered -data_pins] -path_delay max -group_path_count 1]
if {[llength \$p]} { puts "TILE setup_max [expr {100.0 - [get_property [lindex \$p 0] slack]}] [get_full_name [get_property [lindex \$p 0] startpoint]]" }
report_checks -from [all_registers -edge_triggered -clock_pins] -to [all_outputs] -path_delay max -fields {fanout cap slew} -digits 3
report_checks -from [all_inputs] -to [all_registers -edge_triggered -data_pins] -path_delay max -digits 3
TCL
# shellcheck disable=SC1091
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
(cd "$TILES" && nix develop --accept-flake-config --command bash -c "sta -no_init -no_splash -exit $W/tile.tcl") \
  > "$W/tile.log" 2>&1 || { tail -20 "$W/tile.log"; exit 1; }
grep '^TILE ' "$W/tile.log"

# the model for the same paths
python3 - "$ROOT" <<'EOF'
import re, sys
from pathlib import Path
root = Path(sys.argv[1])
fab = root / "macro" / (root / "arch/CURRENT").read_text().strip() / "fabulous" / ".FABulous"
est = (fab / "placement_estimate.txt").read_text()
c2o = max(float(l.split(",")[3]) for l in est.splitlines() if l.startswith("ClkToOut"))
su = max(float(l.split(",")[3]) for l in est.splitlines() if l.startswith("SetupHold"))
prim_out = re.compile(r"^(TA|TB|SA|SB)_(tc|sout|done|q\d)$")
prim_in = re.compile(r"^(TA|TB|SA|SB)_(rst|load|half|en|step|sin|d\d)$")
pout = pin = 0.0
for line in (fab / "pips.nom_slow_1p08V_125C.txt").read_text().splitlines():
    f = line.split(",")
    if len(f) < 5 or f[0] != "X2Y2":
        continue
    d = float(f[4])
    if prim_out.match(f[1]): pout = max(pout, d)
    if prim_in.match(f[3]): pin = max(pin, d)
# Longest chains of tile-internal pips (a route may take several hops inside the tile): from a
# tile input wire to a primitive input, and from a primitive output to a tile output wire.
from functools import lru_cache
edges = {}
for line in (fab / "pips.nom_slow_1p08V_125C.txt").read_text().splitlines():
    f = line.split(",")
    if len(f) < 5 or f[0] != "X2Y2" or f[2] != "X2Y2":
        continue
    edges.setdefault(f[1], []).append((f[3], float(f[4])))
import sys as _s
_s.setrecursionlimit(100000)

@lru_cache(maxsize=None)
def longest_to_prim_in(w, depth=0):
    if prim_in.match(w):
        return 0.0
    if depth > 12:
        return float("-inf")
    return max((d + longest_to_prim_in(n, depth + 1) for n, d in edges.get(w, [])), default=float("-inf"))

@lru_cache(maxsize=None)
def longest_to_out(w, depth=0):
    best = 0.0 if re.search(r"BEG\d*$", w) else float("-inf")
    if depth > 12:
        return best
    return max([best] + [d + longest_to_out(n, depth + 1) for n, d in edges.get(w, [])])

chain_in = max(longest_to_prim_in(w) for w in edges if re.search(r"END\d*$", w))
chain_out = max(longest_to_out(w) for w in edges if prim_out.match(w))
print(f"MODEL clk2out_max {c2o + chain_out:.3f} (arc {c2o:.3f} + longest pip chain {chain_out:.3f}; one pip {pout:.3f})")
print(f"MODEL setup_max {su + chain_in:.3f} (arc {su:.3f} + longest pip chain {chain_in:.3f}; one pip {pin:.3f})")
EOF
