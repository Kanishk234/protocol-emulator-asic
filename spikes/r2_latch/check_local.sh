#!/usr/bin/env bash
# R2: check the branch overlay locally before it goes to a branch (works from main).
#   1. Verilator lint, the way the lint workflow runs it (source_files, -Isrc).
#   2. The overlay's cocotb suite on the RTL (behavioural clock gates).
#   3. The same suite on a Yosys gate-level netlist (library clock gates, latches) with Tiny
#      Tapeout's Icarus 13, and OpenSTA on that netlist at 20 ns (typ and slow, no wires).
# Needs .venv and the caches scripts/gl_local.sh and spikes/r1_lane/run_r1.sh create.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
if ! command -v yosys >/dev/null && [ -d "$HOME/oss-cad-suite/bin" ]; then
  export PATH="$PATH:$HOME/oss-cad-suite/bin"
fi

PDK_REV="${PDK_REV:-2bbec755dc67ca3db0261c3d6163e15735d66710}"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/tripwire"
export PDK_ROOT="$CACHE/pdk-$PDK_REV"
LIBDIR="$PDK_ROOT/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib"
LIB="$LIBDIR/sg13cmos5l_stdcell_typ_1p20V_25C.lib"
IV="$CACHE/iverilog-13"
OR="$CACHE/openroad"
[ -s "$LIB" ] && [ -x "$IV/usr/bin/iverilog" ] || { echo "run scripts/gl_local.sh once first" >&2; exit 1; }

B="$HERE/build"
rm -rf "$B" && mkdir -p "$B/src" "$B/test"
# The branch's src/: the overlay top, the R1 lane files, the generated defines.
cp "$HERE/overlay/src/"*.v "$B/src/"
cp "$ROOT/spikes/r1_lane/"{trw_lane,trw_alu,trw_slots,trw_cport}.v "$B/src/"
cp "$ROOT/src/trw_defs.vh" "$B/src/"
cp test/tb.v "$B/test/"
cp "$HERE/overlay/test/Makefile" "$HERE/overlay/test/test.py" "$B/test/"
SOURCES=$(sed -n 's/^PROJECT_SOURCES = //p' "$B/test/Makefile")
SRC_ABS=$(for f in $SOURCES; do printf "%s " "$B/src/$f"; done)

echo "=== lint (as the lint workflow runs it)"
(cd "$B" && verilator --lint-only -Wall -Isrc --top-module tt_um_tripwire $(for f in $SOURCES; do echo src/$f; done))
echo ok

echo "=== RTL: cocotb suite"
TRW_DEFS="$B/src/trw_defs.vh" make -C "$B/test" SRC_DIR="$B/src" > "$B/rtl.log" 2>&1 || true
grep -E "\*\* test|TESTS=" "$B/rtl.log" | tail -4
grep -q failure "$B/test/results.xml" && { echo "check_local: RTL FAIL (see $B/rtl.log)" >&2; exit 1; }

echo "=== gate level: Yosys netlist + Icarus 13"
yosys -q -l "$B/yosys.log" -p "read_liberty -lib $LIB; read_verilog -I$B/src $SRC_ABS; \
  synth -top tt_um_tripwire -flatten; dfflibmap -liberty $LIB; abc -liberty $LIB; opt_clean; \
  tee -o $B/stat.txt stat -liberty $LIB; write_verilog -noattr -noexpr $B/test/gate_level_netlist.v" > /dev/null
grep -E "Chip area|lgcp|dlhq|dfrbpq" "$B/stat.txt" | sed 's/^ */  /'
rm -rf "$B/test/sim_build" "$B/test/results.xml"
PATH="$IV/usr/bin:$PATH" IVERILOG_VPI_MODULE_PATH="$IV/usr/lib/ivl" COMPILE_ARGS="-B $IV/usr/lib/ivl" \
  TRW_DEFS="$B/src/trw_defs.vh" make -C "$B/test" GATES=yes SRC_DIR="$B/src" > "$B/gl.log" 2>&1 || true
grep -E "\*\* test|TESTS=" "$B/gl.log" | tail -4
grep -q failure "$B/test/results.xml" && { echo "check_local: GL FAIL (see $B/gl.log)" >&2; exit 1; }

if [ -x "$OR/x/usr/bin/sta" ]; then
  echo "=== OpenSTA on the Yosys netlist (20 ns, ideal clock, no wires)"
  sed -i 's/^\( *\)wire signed /\1wire /' "$B/test/gate_level_netlist.v"
  for corner in typ_1p20V_25C slow_1p08V_125C; do
    cat > "$B/sta_$corner.tcl" <<EOF
read_liberty $LIBDIR/sg13cmos5l_stdcell_$corner.lib
read_verilog $B/test/gate_level_netlist.v
link_design tt_um_tripwire
create_clock -name clk -period 20 [get_ports clk]
set_clock_uncertainty -setup 0.25 [get_clocks clk]
set_input_delay 0 -clock clk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 0 -clock clk [all_outputs]
puts "flop endpoints:"
report_checks -path_delay max -digits 3 -format end -group_count 3 -to [all_registers -edge_triggered -data_pins]
puts "latch endpoints (slack 0 = time borrowed into the transparent phase):"
report_checks -path_delay max -digits 3 -format end -group_count 3 -to [all_registers -level_sensitive -data_pins]
report_worst_slack -min
exit
EOF
    LD_LIBRARY_PATH="$OR/x/usr/lib/x86_64-linux-gnu" TCL_LIBRARY="$OR/x/usr/share/tcltk/tcl8.6" \
      "$OR/x/usr/bin/sta" -no_init -no_splash -exit "$B/sta_$corner.tcl" </dev/null > "$B/sta_$corner.txt" 2>&1 || true
    echo "  $corner: worst flop-endpoint setup slack $(awk '/flop endpoints/{f=1} f && /MET|VIOLATED/{print $(NF-1); exit}' "$B/sta_$corner.txt") ns; $(grep 'worst slack' "$B/sta_$corner.txt") (hold, ideal clock)"
  done
fi
echo "check_local: PASS"
