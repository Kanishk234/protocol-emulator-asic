#!/usr/bin/env bash
# Whole-chip area and pre-layout timing (trw_chip): Yosys onto the cmos5l cells (typ liberty; synth -flatten,
# dfflibmap, abc, the R1/R4 recipe) with the SRAM macro as a blackbox, then OpenSTA at typ and slow.
# Usage: synth/chip/run_chip.sh [period_ns]   (default 20; needs the liberty, macro and OpenSTA caches that
#        scripts/gl_local.sh, spikes/r3_sram/fetch_macro.sh and spikes/r1_lane/run_r1.sh create)
# Output: synth/chip/build/ (git-ignored): netlist, stat_flat.txt, stat_hier.txt, sta_*.txt
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
PERIOD="${1:-20}"
if ! command -v yosys >/dev/null && [ -d "$HOME/oss-cad-suite/bin" ]; then
  export PATH="$PATH:$HOME/oss-cad-suite/bin"
fi
PDK_REV="${PDK_REV:-2bbec755dc67ca3db0261c3d6163e15735d66710}"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/tripwire"
LIBDIR="$CACHE/pdk-$PDK_REV/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib"
MACRO_DIR="$CACHE/macro-$PDK_REV/RM_IHPSG13_1P_512x16_c2_bm_bist"
OR="$CACHE/openroad"
[ -s "$LIBDIR/sg13cmos5l_stdcell_typ_1p20V_25C.lib" ] && [ -x "$OR/x/usr/bin/sta" ] \
  || { echo "run scripts/gl_local.sh and spikes/r1_lane/run_r1.sh once first" >&2; exit 1; }
"$ROOT/spikes/r3_sram/fetch_macro.sh" "$MACRO_DIR" >/dev/null
B="$HERE/build"; rm -rf "$B"; mkdir -p "$B"
S="$ROOT/src"
FILES="trw_chip.v trw_sync.v trw_fabric.v trw_chan_port.v trw_chan_prod.v trw_host.v trw_spi.v trw_lane.v trw_alu.v
       trw_slots.v trw_sram.v trw_pin_cfg.v trw_pin_io.v trw_pin_tx.v trw_pin_rx.v trw_pin_unit.v trw_pins.v"
LIB="$LIBDIR/sg13cmos5l_stdcell_typ_1p20V_25C.lib"
YS="read_liberty -lib $LIB; read_verilog -lib $ROOT/spikes/r3_sram/overlay/src/RM_IHPSG13_1P_512x16_c2_bm_bist.v;
    read_verilog -DSYNTHESIS -I$S $(for f in $FILES; do printf '%s ' "$S/$f"; done)"
yosys -q -l "$B/yosys_hier.log" -p "$YS; synth -top trw_chip; dfflibmap -liberty $LIB; abc -liberty $LIB;
  opt_clean; tee -o $B/stat_hier.txt stat -liberty $LIB" >/dev/null 2>&1
yosys -q -l "$B/yosys.log" -p "$YS; synth -top trw_chip -flatten; dfflibmap -liberty $LIB; abc -liberty $LIB;
  opt_clean; tee -o $B/stat_flat.txt stat -liberty $LIB; write_verilog -noattr -noexpr $B/net.v" >/dev/null 2>&1
grep -E "Chip area for (module|top)" "$B/stat_hier.txt" | sed 's/^ *//'
grep -E " cells$|sg13cmos5l_(dfrbpq|dlhq|lgcp)_|RM_IHP|Chip area" "$B/stat_flat.txt" | sed 's/^ */  flat: /'
sed 's/^\( *\)wire signed /\1wire /' "$B/net.v" > "$B/net_sta.v"
export LD_LIBRARY_PATH="$OR/x/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export TCL_LIBRARY="$OR/x/usr/share/tcltk/tcl8.6"
for corner in typ_1p20V_25C slow_1p08V_125C; do
  CHIP_LIB="$LIBDIR/sg13cmos5l_stdcell_$corner.lib" CHIP_MACRO_LIB="$MACRO_DIR/RM_IHPSG13_1P_512x16_c2_bm_bist_$corner.lib" \
  CHIP_NET="$B/net_sta.v" CHIP_PERIOD="$PERIOD" "$OR/x/usr/bin/sta" -no_init -no_splash -exit "$HERE/sta_chip.tcl" \
    </dev/null 2>&1 | grep -v tclreadline > "$B/sta_$corner.txt" || true
  w=$(awk '/==== worst path to a flop/{f=1} f && /slack/{print $1; exit}' "$B/sta_$corner.txt")
  m=$(awk '/==== worst path from the SRAM/{f=1} f && /slack/{print $1; exit}' "$B/sta_$corner.txt")
  echo "  $corner: worst flop slack $w ns; worst from SRAM output $m ns"
done
