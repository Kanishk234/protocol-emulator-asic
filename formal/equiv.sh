#!/usr/bin/env bash
# L8-EQY (VERIFICATION.md): is the Yosys cmos5l netlist of a module equivalent to its RTL?
#   formal/equiv.sh <module> <rtl files...>
# Synthesises the module onto the cmos5l cells (the R1/R4 recipe: flatten, dfflibmap, abc, typ liberty), reads the
# netlist back with cell models built from the liberty `function`s (the PDK's Verilog cell models are not readable
# by Yosys), and proves a miter of RTL vs netlist with SAT (combinational modules; D-050 has what this does not
# cover yet). Exit 0 = proved equivalent. Needs the PDK cache (scripts/gl_local.sh) and the OSS CAD Suite.
set -euo pipefail
TOP="$1"; shift
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PATH:$HOME/oss-cad-suite/bin"
PDK_REV="${PDK_REV:-2bbec755dc67ca3db0261c3d6163e15735d66710}"
LIB="${XDG_CACHE_HOME:-$HOME/.cache}/tripwire/pdk-$PDK_REV/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
yosys -q -p "read_verilog -I$ROOT/src $*; synth -top $TOP -flatten; dfflibmap -liberty $LIB; abc -liberty $LIB;
  opt_clean; write_verilog -noattr $W/net.v" >/dev/null 2>&1
yosys -q -p "read_verilog -I$ROOT/src $*; prep -top $TOP; rename $TOP gold; write_rtlil $W/gold.il" >/dev/null 2>&1
yosys -q -p "read_liberty -ignore_miss_func $LIB; read_verilog $W/net.v; hierarchy -top $TOP; flatten; prep -top $TOP;
  rename $TOP gate; write_rtlil $W/gate.il" >/dev/null 2>&1
yosys -l "$W/miter.log" -p "read_rtlil $W/gold.il; read_rtlil $W/gate.il; miter -equiv -flatten -make_outputs gold gate miter;
  hierarchy -top miter; sat -verify -prove trigger 0 -show-inputs miter" >/dev/null 2>&1 || true
if grep -q "SUCCESS" "$W/miter.log"; then echo "equiv: $TOP netlist == RTL (SAT, all inputs)"; exit 0; fi
echo "equiv: $TOP NOT proved"; grep -A30 "Time Signal" "$W/miter.log" | head -30; exit 1
