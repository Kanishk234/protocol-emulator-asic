#!/usr/bin/env bash
# R3: check the branch overlay locally before it goes to a branch (works from main).
#   1. Verilator lint of the overlay RTL (blackbox macro).
#   2. The overlay's cocotb suite on the RTL, with the macro's behavioural model.
#   3. The same suite on a Yosys gate-level netlist (macro kept as a blackbox instance, simulated by
#      its model), with Tiny Tapeout's Icarus 13, the way scripts/gl_local.sh does it.
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
"$HERE/fetch_macro.sh" "$MACRO_DIR"

SRC="${R3_SRC:-$HERE/overlay/src}"   # R3_SRC: a mutated copy, for mutation checks
B="$HERE/build"
rm -rf "$B" && mkdir -p "$B/test"
cp test/tb.v "$B/test/"
cp "$HERE/overlay/test/Makefile" "$HERE/overlay/test/test.py" "$B/test/"

echo "=== lint (Verilator -Wall)"
verilator --lint-only -Wall -I"$SRC" --top-module tt_um_tripwire \
  "$SRC/tt_um_tripwire.v" "$SRC/trw_sram.v" "$SRC/RM_IHPSG13_1P_512x16_c2_bm_bist.v"
echo ok

echo "=== RTL: cocotb suite with the macro model"
make -C "$B/test" SRC_DIR="$SRC" MACRO_DIR="$MACRO_DIR" > "$B/rtl.log" 2>&1 || true
grep -E "PASS|FAIL|TESTS=" "$B/rtl.log" | grep -v "^ *$" | tail -8
grep -q failure "$B/test/results.xml" && { echo "check_local: RTL FAIL" >&2; exit 1; }

echo "=== gate level: Yosys netlist (macro blackboxed) + Icarus 13"
yosys -q -l "$B/yosys.log" -p "read_verilog -lib $SRC/RM_IHPSG13_1P_512x16_c2_bm_bist.v; \
  read_verilog -I$SRC $SRC/tt_um_tripwire.v $SRC/trw_sram.v; synth -top tt_um_tripwire -flatten; \
  dfflibmap -liberty $LIB; abc -liberty $LIB; opt_clean; stat -liberty $LIB; \
  select -assert-count 1 t:RM_IHPSG13_1P_512x16_c2_bm_bist; \
  write_verilog -noattr -noexpr $B/test/gate_level_netlist.v" > /dev/null
grep -E "Chip area|RM_IHPSG13|dfrbp" "$B/yosys.log" | tail -4
grep -o "RM_IHPSG13_1P_512x16_c2_bm_bist [^ ]*" "$B/test/gate_level_netlist.v"
rm -rf "$B/test/sim_build" "$B/test/results.xml"
PATH="$IV/usr/bin:$PATH" IVERILOG_VPI_MODULE_PATH="$IV/usr/lib/ivl" COMPILE_ARGS="-B $IV/usr/lib/ivl" \
  make -C "$B/test" GATES=yes SRC_DIR="$SRC" MACRO_DIR="$MACRO_DIR" > "$B/gl.log" 2>&1 || true
grep -E "PASS|FAIL|TESTS=" "$B/gl.log" | tail -8
grep -q failure "$B/test/results.xml" && { echo "check_local: GL FAIL" >&2; exit 1; }
echo "check_local: PASS"
