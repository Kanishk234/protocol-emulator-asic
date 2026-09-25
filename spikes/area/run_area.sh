#!/usr/bin/env bash
# Area estimate, step 1: synthesize each building block in ae_prims.v alone onto the cmos5l
# cells (typ liberty, the R1 recipe) and write build/prims.tsv: block, params, cells, flops, area.
# Step 2 (estimate.py) multiplies them by the counts each chip block needs.
#
# Usage: spikes/area/run_area.sh     (needs the liberty cached by spikes/r1_lane/run_r1.sh)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
if ! command -v yosys >/dev/null && [ -d "$HOME/oss-cad-suite/bin" ]; then
  export PATH="$PATH:$HOME/oss-cad-suite/bin"
fi
PDK_REV="${PDK_REV:-2bbec755dc67ca3db0261c3d6163e15735d66710}"
TYP="${XDG_CACHE_HOME:-$HOME/.cache}/tripwire/pdk-$PDK_REV/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib"
[ -s "$TYP" ] || { echo "run spikes/r1_lane/run_r1.sh once to fetch the liberty" >&2; exit 1; }

mkdir -p build
verilator --lint-only -Wall -Wno-UNUSEDSIGNAL -Wno-DECLFILENAME -Wno-MULTITOP -Wno-WIDTH ae_prims.v

# block  chparam-args  label
JOBS=(
  "ae_timer|-|timer24"
  "ae_cursor|-|cursor"
  "ae_txshift|-|txshift"
  "ae_rxframe|-|rxframe"
  "ae_crc|-|crc16"
  "ae_bitsync|-|bitsync_ctl"
  "ae_pulse|-|pulse"
  "ae_padsel|-|padsel"
  "ae_event|-|event"
  "ae_prod|-|prod"
  "ae_port|-chparam N 7|port7"
  "ae_port|-chparam N 8|port8"
  "ae_port|-chparam N 9|port9"
  "ae_padout|-|padout"
  "ae_cfg|-chparam W 22|cfg22_flop"
  "ae_rdmux|-chparam W 22|rdmux22"
  "ae_rdmux|-chparam W 48|rdmux48"
  "ae_spi|-|spi"
)
printf "label\tcells\tflops\tarea_um2\n" > build/prims.tsv
for j in "${JOBS[@]}"; do
  IFS='|' read -r top par label <<< "$j"
  [ "$par" = "-" ] && par=""
  yosys -q -l "build/$label.log" -p "read_liberty -lib $TYP; read_verilog ae_prims.v; \
    hierarchy -top $top $par; synth -top $top -flatten; dfflibmap -liberty $TYP; \
    abc -liberty $TYP; opt_clean; tee -o build/$label.stat stat -liberty $TYP" >/dev/null 2>&1 \
    || { tail -20 "build/$label.log"; exit 1; }
  area=$(awk '/Chip area for module/ {a=$NF} END {print a}' "build/$label.stat")
  cells=$(awk '$NF=="cells" {c=$1} END {print c}' "build/$label.stat")
  flops=$(awk '/sg13cmos5l_(s?df|dl)/ {s+=$1} END {print s+0}' "build/$label.stat")
  printf "%s\t%s\t%s\t%s\n" "$label" "$cells" "$flops" "$area" >> build/prims.tsv
done
column -t build/prims.tsv
