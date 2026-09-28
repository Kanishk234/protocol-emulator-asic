#!/usr/bin/env bash
# Timing arcs of the WARP hard primitives (arch/prims, D-026) for the compile flow's place and
# route (BUGS #17): each primitive is synthesized alone onto the IHP CMOS5L standard cells and
# timed with OpenSTA at the sign-off corner (slow, 1.08 V, 125 C). Output: tools/timing/prims.arcs
# (clock-to-out of every output, setup/hold of every input, combinational input -> output
# delays), which scripts/gen_prim_timing.py turns into nextpnr's placement_estimate.txt.
# Standalone synthesis has no placement or wiring inside the tile, so the arcs are scaled by
# MARGIN (tools/timing/README.md); the tile's routing (switch matrix) is in the pip delays.
#
# Usage: tools/timing/prim_sta.sh     Needs: OSS CAD Suite (Yosys), the Nix LibreLane environment
#        of build/tile_cmos5l/fabulous-tiles (OpenROAD/OpenSTA), the CMOS5L PDK in $PDK_ROOT.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PDK_ROOT="${PDK_ROOT:-$HOME/.cache/warp/pdk-full}"
LIB="$PDK_ROOT/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_slow_1p08V_125C.lib"
W="$ROOT/build/prim_sta"
mkdir -p "$W"
if ! command -v yosys >/dev/null && [ -d "$HOME/oss-cad-suite/bin" ]; then
  export PATH="$PATH:$HOME/oss-cad-suite/bin"
fi

for p in wp_timer wp_shift; do
  yosys -q -p "read_verilog $ROOT/arch/prims/$p.v; synth -top $p -flatten; \
    dfflibmap -liberty $LIB; abc -liberty $LIB; opt_clean; hilomap -singleton \
    -hicell sg13cmos5l_tiehi L_HI -locell sg13cmos5l_tielo L_LO; write_verilog -noattr $W/$p.v"
done

cat > "$W/sta.tcl" <<TCL
read_liberty $LIB
foreach p {wp_timer wp_shift} {
  read_verilog $W/\$p.v
  link_design \$p
  create_clock -name clk -period 100 [get_ports CLK]
  set ins {}
  foreach i [all_inputs] {
    set n [get_full_name \$i]
    if {\$n ne "CLK" && ![string match "ConfigBits*" \$n]} { lappend ins \$i }
  }
  set_input_delay 0 -clock clk \$ins
  set_output_delay 0 -clock clk [all_outputs]
  set_false_path -from [get_ports ConfigBits*]
  set_load 0.01 [all_outputs]
  set_input_transition 0.2 \$ins
  foreach port [get_ports *] {
    set n [get_full_name \$port]
    if {\$n eq "CLK" || [string match "ConfigBits*" \$n]} continue
    if {[get_property \$port direction] eq "input"} {
      # setup: worst input -> flop path (period - slack); hold: worst hold requirement
      set sp [find_timing_paths -from \$port -to [all_registers -data_pins] -path_delay max]
      if {[llength \$sp]} { puts "ARC \$p setup \$n [expr {100.0 - [get_property [lindex \$sp 0] slack]}]" }
      set hp [find_timing_paths -from \$port -to [all_registers -data_pins] -path_delay min]
      if {[llength \$hp]} { puts "ARC \$p hold \$n [expr {-[get_property [lindex \$hp 0] slack]}]" }
      foreach o [get_ports * -filter "direction == output"] {
        set cp [find_timing_paths -from \$port -to \$o -path_delay max]
        if {[llength \$cp]} { puts "ARC \$p comb \$n [get_full_name \$o] [expr {100.0 - [get_property [lindex \$cp 0] slack]}]" }
      }
    } else {
      set op [find_timing_paths -from [all_registers -clock_pins] -to \$port -path_delay max]
      if {[llength \$op]} { puts "ARC \$p clk2out \$n [expr {100.0 - [get_property [lindex \$op 0] slack]}]" }
    }
  }
}
TCL

TILES="$ROOT/build/tile_cmos5l/fabulous-tiles"
# shellcheck disable=SC1091
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
(cd "$TILES" && nix develop --accept-flake-config --command bash -c "if command -v sta >/dev/null; then sta -no_init -no_splash -exit $W/sta.tcl; else echo no-sta; exit 1; fi") \
  > "$W/sta.log" 2>&1 || { tail -20 "$W/sta.log"; exit 1; }
grep '^ARC ' "$W/sta.log" | sed 's/^ARC //' > "$ROOT/tools/timing/prims.arcs"
cat "$ROOT/tools/timing/prims.arcs"
