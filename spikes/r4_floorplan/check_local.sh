#!/usr/bin/env bash
# R4: check the branch contents locally before they go to a branch (works from main).
#   1. The generated fabric is current; Verilator lint of the whole top (macro blackboxed).
#   2. The branch's cocotb suite on the RTL, with the macro's behavioural model.
#   3. Yosys synthesis onto the cmos5l cells (flat and per module), the cell and area summary.
#   4. The same suite on that gate-level netlist with Tiny Tapeout's Icarus 13 (skip with R4_NO_GL=1).
# Needs .venv and the caches scripts/gl_local.sh creates (PDK models, Icarus 13): run it once first.
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
LIB="$PDK_ROOT/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib"
IV="$CACHE/iverilog-13"
[ -s "$LIB" ] && [ -x "$IV/usr/bin/iverilog" ] || { echo "run scripts/gl_local.sh once first" >&2; exit 1; }
MACRO_DIR="$CACHE/macro-$PDK_REV/RM_IHPSG13_1P_512x16_c2_bm_bist"
"$ROOT/spikes/r3_sram/fetch_macro.sh" "$MACRO_DIR" >/dev/null

B="$HERE/build"
rm -rf "$B" && mkdir -p "$B/test"
python "$HERE/gen_fabric.py" --check
"$HERE/sources.sh" "$B/src"
SRC="$B/src"
cp test/tb.v "$B/test/"
cp "$HERE/overlay/test/Makefile" "$HERE/overlay/test/test.py" "$B/test/"
ln -s "$ROOT/tools" "$B/tools"                    # test.py takes the encodings from tools/tripwire_spec.py
FILES=$(python -c 'import yaml,sys; print(" ".join(yaml.safe_load(open(sys.argv[1]))["project"]["source_files"]))' "$HERE/overlay/info.yaml")

echo "=== lint (Verilator -Wall)"
verilator --lint-only -Wall -I"$SRC" --top-module tt_um_tripwire \
  $(for f in $FILES; do echo "$SRC/$f"; done) "$SRC/RM_IHPSG13_1P_512x16_c2_bm_bist.v"
echo ok

echo "=== RTL: cocotb suite with the macro model"
make -C "$B/test" SRC_DIR="$SRC" MACRO_DIR="$MACRO_DIR" > "$B/rtl.log" 2>&1 || true
grep -E "TESTS=|FAIL " "$B/rtl.log" | tail -8
grep -q failure "$B/test/results.xml" && { echo "check_local: RTL FAIL" >&2; exit 1; }

echo "=== synthesis: Yosys onto cmos5l (typ), macro blackboxed"
YS="read_liberty -lib $LIB; read_verilog -lib $SRC/RM_IHPSG13_1P_512x16_c2_bm_bist.v; \
    read_verilog -DSYNTHESIS -I$SRC $(printf "$SRC/%s " $FILES)"
yosys -q -l "$B/yosys_hier.log" -p "$YS; synth -top tt_um_tripwire; dfflibmap -liberty $LIB; \
  abc -liberty $LIB; opt_clean; tee -o $B/stat_hier.txt stat -liberty $LIB" >/dev/null
yosys -q -l "$B/yosys.log" -p "$YS; synth -top tt_um_tripwire -flatten; dfflibmap -liberty $LIB; \
  abc -liberty $LIB; opt_clean; tee -o $B/stat_flat.txt stat -liberty $LIB; \
  select -assert-count 1 t:RM_IHPSG13_1P_512x16_c2_bm_bist; \
  write_verilog -noattr -noexpr $B/test/gate_level_netlist.v" >/dev/null
grep -E "Chip area for (module|top)" "$B/stat_hier.txt" | sed 's/^ *//'
grep -E " cells$|sg13cmos5l_(dfrbpq|dlhq|lgcp)|RM_IHP|Chip area" "$B/stat_flat.txt" | sed 's/^ */  flat: /'
echo "=== pre-layout STA (OpenSTA, 20 ns, config latches static)"
OR="$CACHE/openroad"
if [ -x "$OR/x/usr/bin/sta" ]; then
  sed 's/^\( *\)wire signed /\1wire /' "$B/test/gate_level_netlist.v" > "$B/net_sta.v"
  for corner in typ_1p20V_25C slow_1p08V_125C; do
    LD_LIBRARY_PATH="$OR/x/usr/lib/x86_64-linux-gnu" TCL_LIBRARY="$OR/x/usr/share/tcltk/tcl8.6" \
    R4_LIB="$(dirname "$LIB")/sg13cmos5l_stdcell_$corner.lib" \
    R4_MACRO_LIB="$MACRO_DIR/RM_IHPSG13_1P_512x16_c2_bm_bist_$corner.lib" \
    R4_NET="$B/net_sta.v" R4_PERIOD=20 "$OR/x/usr/bin/sta" -no_init -no_splash -exit "$HERE/sta.tcl" \
      < /dev/null 2>&1 | grep -v tclreadline > "$B/sta_$corner.txt" || true
    arr=$(awk '/==== worst path to a flop/{f=1} f && /data arrival time/{print $1; exit}' "$B/sta_$corner.txt")
    slk=$(awk '/==== worst path to a flop/{f=1} f && /slack/{print $1; exit}' "$B/sta_$corner.txt")
    echo "  $corner: worst flop path arrival $arr ns, slack $slk ns"
  done
else
  echo "  (OpenSTA not cached: run spikes/r1_lane/run_r1.sh once)"
fi
[ "${R4_NO_GL:-0}" = 1 ] && { echo "check_local: PASS (gate level skipped)"; exit 0; }

echo "=== gate level: Yosys netlist (macro model) + Icarus 13"
rm -rf "$B/test/sim_build" "$B/test/results.xml"
PATH="$IV/usr/bin:$PATH" IVERILOG_VPI_MODULE_PATH="$IV/usr/lib/ivl" COMPILE_ARGS="-B $IV/usr/lib/ivl" \
  make -C "$B/test" GATES=yes SRC_DIR="$SRC" MACRO_DIR="$MACRO_DIR" > "$B/gl.log" 2>&1 || true
grep -E "TESTS=|FAIL " "$B/gl.log" | tail -8
grep -q failure "$B/test/results.xml" && { echo "check_local: GL FAIL" >&2; exit 1; }
echo "check_local: PASS"
