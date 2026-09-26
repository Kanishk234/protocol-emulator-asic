#!/usr/bin/env bash
# Pin-unit area and timing (docs/reports/PIN_UNIT_RTL.md): Yosys onto the cmos5l cells (typ liberty, the
# R1 recipe: synth -flatten, dfflibmap, abc, plain mapping), then OpenSTA at the typ and slow corners.
#
# Usage: synth/pin/run_pin.sh [period_ns]     (default 20; needs the liberty and OpenSTA cached by
#                                             spikes/r1_lane/run_r1.sh)
# Output: synth/pin/build/ (git-ignored): netlists, stat_*.txt, sta_*.txt, summary.txt
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
TYP="$LIBDIR/sg13cmos5l_stdcell_typ_1p20V_25C.lib"
OR="$CACHE/openroad"
[ -s "$TYP" ] && [ -x "$OR/x/usr/bin/sta" ] || { echo "run spikes/r1_lane/run_r1.sh once first" >&2; exit 1; }
export LD_LIBRARY_PATH="$OR/x/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export TCL_LIBRARY="$OR/x/usr/share/tcltk/tcl8.6"
STA() { "$OR/x/usr/bin/sta" -no_init -no_splash -exit "$@" </dev/null 2>&1 | grep -v "tclreadline" || true; }

UNIT="$ROOT/src/trw_pin_io.v $ROOT/src/trw_pin_tx.v $ROOT/src/trw_pin_rx.v $ROOT/src/trw_pin_unit.v"
CFG="$ROOT/src/trw_pin_cfg.v"
ALL="$CFG $UNIT $HERE/trw_pin_meas.v"
mkdir -p build

echo "=== lint (Verilator -Wall)"
verilator --lint-only -Wall -I"$ROOT/src" --top-module trw_pin_unit $UNIT
for f in 0 1; do verilator --lint-only -Wall -I"$ROOT/src" --top-module trw_pin_cfg -GFULL=$f $CFG; done
echo ok

# synth <label> <top> <chparam-args> <files>: flat area; writes build/stat_<label>.txt
synth() {
  local label=$1 top=$2 par=$3; shift 3
  yosys -q -l "build/yosys_$label.log" -p "read_liberty -lib $TYP; read_verilog -DSYNTHESIS -I$ROOT/src $*; \
    hierarchy -top $top $par; synth -top $top -flatten; dfflibmap -liberty $TYP; abc -liberty $TYP; opt_clean; \
    tee -o build/stat_$label.txt stat -liberty $TYP; write_verilog -noattr -noexpr build/net_$label.v" \
    >/dev/null 2>&1 || { tail -20 "build/yosys_$label.log"; exit 1; }
  sed -i 's/^\( *\)wire signed /\1wire /' "build/net_$label.v"
}
area()  { awk '/Chip area for module/ {a=$NF} END {print a}' "build/stat_$1.txt"; }
cells() { awk '$NF=="cells" || $2=="cells" {c=$1} END {print c}' "build/stat_$1.txt"; }
count() { awk -v p="$2" '$0 ~ p {s+=$1} END {print s+0}' "build/stat_$1.txt"; }

SUMMARY=build/summary.txt
printf "%-12s %8s %10s %6s %7s %5s\n" block cells area_um2 flops latches icg > "$SUMMARY"
for f in 0 1; do
  synth "cfg$f"  trw_pin_cfg  "-chparam FULL $f" "$CFG"
  synth "unit$f" trw_pin_unit "-chparam FULL $f" "$UNIT"
  synth "meas$f" trw_pin_meas "-chparam FULL $f" "$ALL"
done
synth prod meas_prod "" "$HERE/trw_pin_meas.v"
for l in cfg0 cfg1 unit0 unit1 prod meas0 meas1; do
  printf "%-12s %8s %10s %6s %7s %5s\n" "$l" "$(cells $l)" "$(area $l)" \
    "$(count $l 'sg13cmos5l_(s?df|dfrb)')" "$(count $l 'sg13cmos5l_dlhq')" "$(count $l 'sg13cmos5l_lgcp')" >> "$SUMMARY"
done

# per-submodule split of the lean and full unit (hierarchical run, no flatten)
for f in 0 1; do
  yosys -q -p "read_liberty -lib $TYP; read_verilog -DSYNTHESIS -I$ROOT/src $UNIT; hierarchy -top trw_pin_unit -chparam FULL $f; \
    synth -top trw_pin_unit; dfflibmap -liberty $TYP; abc -liberty $TYP; opt_clean; \
    tee -o build/stat_hier_unit$f.txt stat -liberty $TYP" >/dev/null 2>&1
done

echo "=== STA at $PERIOD ns"
printf "\n%-6s %-16s %-4s %10s %10s  %s\n" net corner cfg arrival slack "worst path to a flop (first net -> last net)" >> "$SUMMARY"
for f in 0 1; do
  for corner in typ_1p20V_25C slow_1p08V_125C; do
    for cs in 0 1; do
      out="build/sta_meas${f}_${corner}_cfg$cs.txt"
      PIN_LIB="$LIBDIR/sg13cmos5l_stdcell_$corner.lib" PIN_NET="build/net_meas$f.v" PIN_PERIOD="$PERIOD" \
        PIN_CFG_STATIC=$cs STA sta_pin.tcl > "$out"
      grep -q "==== summary" "$out" || { echo "STA failed, see $out" >&2; tail -5 "$out" >&2; exit 1; }
      arr=$(awk '/==== worst path to a flop/{f=1} f && /data arrival time/{print $1; exit}' "$out")
      slk=$(awk '/==== worst path to a flop/{f=1} f && /slack/{print $1; exit}' "$out")
      sp=$(awk '/==== worst path to a flop/{f=1} f && /\(net\)/{print $1; exit}' "$out")
      ep=$(awk '/==== worst path to a flop/{f=1} /==== ten worst/{f=0} f && /\(net\)/{e=$1} END{print e}' "$out")
      printf "%-6s %-16s %-4s %10s %10s  %s -> %s\n" "meas$f" "$corner" "$cs" "$arr" "$slk" "$sp" "$ep" >> "$SUMMARY"
    done
  done
done
echo "(cfg 1 = configuration latches are false-path startpoints; reg-to-reg paths; setup uncertainty 0.25 ns)" >> "$SUMMARY"
echo; cat "$SUMMARY"
echo; for f in 0 1; do echo "--- hierarchy, FULL=$f"; grep -E "^=== |Chip area" "build/stat_hier_unit$f.txt"; done
echo "run_pin: done (reports in synth/pin/build/)"
