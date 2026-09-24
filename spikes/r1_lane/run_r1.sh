#!/usr/bin/env bash
# R1 risk spike: simulate, lint, synthesize one lane onto the cmos5l cells, and time it with OpenSTA.
#
# Usage: spikes/r1_lane/run_r1.sh [period_ns]      (default 20)
# Output: spikes/r1_lane/build/ (git-ignored): netlists, yosys logs, sta_<variant>_<corner>.txt
#
# OpenSTA is not in the OSS CAD Suite. This script extracts the standalone `sta` binary from a
# prebuilt OpenROAD package (plus the two Tcl libraries it needs) into the cache, no root needed.
# Liberty files come from the same pinned PDK revision as scripts/gl_local.sh.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$HERE"
PERIOD="${1:-20}"

if ! command -v yosys >/dev/null && [ -d "$HOME/oss-cad-suite/bin" ]; then
  export PATH="$PATH:$HOME/oss-cad-suite/bin"
fi

PDK_REV="${PDK_REV:-2bbec755dc67ca3db0261c3d6163e15735d66710}"   # = scripts/gl_local.sh
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/tripwire"
LIBDIR="$CACHE/pdk-$PDK_REV/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib"
OR_DEB_URL="https://github.com/Precision-Innovations/OpenROAD/releases/download/2024-12-14/openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb"
OR="$CACHE/openroad"

echo "=== liberty (PDK $PDK_REV)"
mkdir -p "$LIBDIR"
for corner in typ_1p20V_25C slow_1p08V_125C fast_1p32V_m40C; do
  f="$LIBDIR/sg13cmos5l_stdcell_$corner.lib"
  [ -s "$f" ] || curl -sfL -o "$f" \
    "https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/$PDK_REV/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_$corner.lib"
done

echo "=== OpenSTA"
if [ ! -x "$OR/x/usr/bin/sta" ]; then
  mkdir -p "$OR"
  (cd "$OR" && curl -sfL -o or.deb "$OR_DEB_URL" && apt-get download libtcl8.6 tcl-tclreadline >/dev/null \
     && rm -rf x && for d in or.deb libtcl8.6_*.deb tcl-tclreadline_*.deb; do dpkg-deb -x "$d" x; done)
fi
export LD_LIBRARY_PATH="$OR/x/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export TCL_LIBRARY="$OR/x/usr/share/tcltk/tcl8.6"
# sta exits 1 after "Failed to load tclreadline.tcl" even when the script ran; judge by the report.
STA() { "$OR/x/usr/bin/sta" -no_init -no_splash -exit "$@" </dev/null 2>&1 | grep -v "tclreadline" || true; }

SRC="trw_r1_top.v trw_lane.v trw_alu.v trw_slots.v trw_cport.v"
mkdir -p build

echo "=== simulation (Icarus): ISA.md §7.1 on the spike lane, latch and flop slot stores"
iverilog -g2005 -I"$ROOT/src" -o build/tb.vvp tb_r1_lane.v trw_lane.v trw_alu.v trw_slots.v trw_cport.v
vvp -n build/tb.vvp | grep tb_r1_lane
iverilog -g2005 -DTRW_SLOTS_FLOPS -I"$ROOT/src" -o build/tbf.vvp tb_r1_lane.v trw_lane.v trw_alu.v trw_slots.v trw_cport.v
vvp -n build/tbf.vvp | grep tb_r1_lane
if vvp -n build/tb.vvp | grep -q FAIL || vvp -n build/tbf.vvp | grep -q FAIL; then
  echo "run_r1: simulation FAIL" >&2; exit 1
fi

echo "=== lint (Verilator -Wall)"
verilator --lint-only -Wall -I"$ROOT/src" --top-module trw_r1_top $SRC
verilator --lint-only -Wall -DTRW_SLOTS_FLOPS -I"$ROOT/src" --top-module trw_r1_top $SRC
echo "ok"

# Mapping: "plain" is the scripts/gl_local.sh recipe (ABC delay mapping, no buffering or sizing, so
# high-fanout nets are left to the flow's resizer); "sized" adds ABC buffering and gate sizing
# toward a 4 ns target (abc -D 4000 -constr), a rough stand-in for what the resizer does.
TYP="$LIBDIR/sg13cmos5l_stdcell_typ_1p20V_25C.lib"
SUMMARY=build/summary.txt
printf "%-6s %-6s %-16s %-6s %10s %10s %10s %10s\n" slots map corner cfg EVAL_ns EVAL_slk EXEC_ns EXEC_slk > "$SUMMARY"
for variant in latch flop; do
  def=""; [ "$variant" = flop ] && def="-DTRW_SLOTS_FLOPS"
  for map in plain sized; do
    # ABC only buffers and sizes when given -constr (driving cell and output load for its netlist).
    printf "set_driving_cell sg13cmos5l_buf_2\nset_load 0.006\n" > build/abc.constr
    abc="abc -liberty $TYP"
    [ "$map" = sized ] && abc="abc -D 4000 -constr build/abc.constr -liberty $TYP"
    net="build/r1_net_${variant}_$map.v"
    echo "=== synthesis: $variant slots, $map mapping, $(basename "$TYP")"
    yosys -q -l "build/yosys_${variant}_$map.log" -p "read_liberty -lib $TYP; read_verilog $def -I$ROOT/src $SRC; \
      synth -top trw_r1_top -flatten; dfflibmap -liberty $TYP; $abc; opt_clean; \
      tee -o build/stat_flat_${variant}_$map.txt stat -liberty $TYP; write_verilog -noattr -noexpr $net" \
      >/dev/null 2>&1 || { tail -20 "build/yosys_${variant}_$map.log"; exit 1; }
    sed -i 's/^\( *\)wire signed /\1wire /' "$net"   # OpenSTA's parser rejects "signed"
    grep -E "Chip area for module" "build/stat_flat_${variant}_$map.txt" | sed 's/^ */  /'

    for corner in typ_1p20V_25C slow_1p08V_125C; do
      for cfg in 0 1; do
        out="build/sta_${variant}_${map}_${corner}_cfg$cfg.txt"
        R1_LIB="$LIBDIR/sg13cmos5l_stdcell_$corner.lib" R1_NET="$net" \
        R1_PERIOD="$PERIOD" R1_CONFIG_STATIC="$cfg" STA sta.tcl > "$out"
        grep -q "==== summary" "$out" || { echo "STA failed, see $out" >&2; tail -5 "$out" >&2; exit 1; }
        ev_t=$(awk '/==== worst EVAL path/{f=1} f && /data arrival time/{print $1; exit}' "$out")
        ev_s=$(awk '/==== worst EVAL path/{f=1} f && /slack/{print $1; exit}' "$out")
        ex_t=$(awk '/==== worst EXEC path/{f=1} f && /data arrival time/{print $1; exit}' "$out")
        ex_s=$(awk '/==== worst EXEC path/{f=1} f && /slack/{print $1; exit}' "$out")
        printf "%-6s %-6s %-16s %-6s %10s %10s %10s %10s\n" "$variant" "$map" "$corner" "$cfg" \
          "$ev_t" "$ev_s" "$ex_t" "$ex_s" | tee -a "$SUMMARY"
      done
    done
  done
  # Hierarchical run (plain mapping), only for the per-module area split.
  yosys -q -p "read_liberty -lib $TYP; read_verilog $def -I$ROOT/src $SRC; synth -top trw_r1_top; \
    dfflibmap -liberty $TYP; abc -liberty $TYP; opt_clean; tee -o build/stat_hier_$variant.txt stat -liberty $TYP" \
    >/dev/null 2>&1
  grep -E "Chip area for module" "build/stat_hier_$variant.txt" | sed 's/^ */  /'
done
echo "(cfg 1 = host-written configuration is a false-path startpoint; period $PERIOD ns, setup uncertainty 0.25 ns)" >> "$SUMMARY"
echo; cat "$SUMMARY"
echo "run_r1: done (reports in spikes/r1_lane/build/)"
