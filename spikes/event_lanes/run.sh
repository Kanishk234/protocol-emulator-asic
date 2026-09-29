#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/build/arch_explore"
YOSYS_BIN="${YOSYS_BIN:-$HOME/oss-cad-suite/bin/yosys}"
SG13G2_LIB="${SG13G2_LIB:-$HOME/.cache/warp/pdk-full/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib}"

mkdir -p "$OUT"
iverilog -g2012 -s tb_event_lanes -o "$OUT/event_lanes_tb.vvp" \
  "$ROOT/spikes/event_lanes/warp_event_lane.v" \
  "$ROOT/spikes/event_lanes/warp_event_lanes.v" \
  "$ROOT/spikes/event_lanes/tb_event_lanes.v"
vvp "$OUT/event_lanes_tb.vvp"
iverilog -g2012 -s tb_event_lanes_static -o "$OUT/event_lanes_static_tb.vvp" \
  "$ROOT/spikes/event_lanes/warp_event_lane.v" \
  "$ROOT/spikes/event_lanes/warp_event_lanes_static.v" \
  "$ROOT/spikes/event_lanes/tb_event_lanes_static.v"
vvp "$OUT/event_lanes_static_tb.vvp"
verilator --lint-only --Wall --top-module warp_event_lanes \
  "$ROOT/spikes/event_lanes/warp_event_lane.v" \
  "$ROOT/spikes/event_lanes/warp_event_lanes.v"
verilator --lint-only --Wall --top-module warp_event_lanes_static \
  "$ROOT/spikes/event_lanes/warp_event_lane.v" \
  "$ROOT/spikes/event_lanes/warp_event_lanes_static.v"

for aw in 3 4; do
  for mode in ram static; do
    if [ "$mode" = ram ]; then
      top=warp_event_lanes
      sources="$ROOT/spikes/event_lanes/warp_event_lanes.v"
    else
      top=warp_event_lanes_static
      sources="$ROOT/spikes/event_lanes/warp_event_lanes_static.v"
    fi
    log="$OUT/event_lanes_${mode}_aw${aw}_yosys.log"
    "$YOSYS_BIN" -p "read_verilog $ROOT/spikes/event_lanes/warp_event_lane.v $sources; chparam -set AW $aw $top; hierarchy -top $top; synth -top $top; dfflibmap -liberty $SG13G2_LIB; abc -liberty $SG13G2_LIB; stat -liberty $SG13G2_LIB" \
      > "$log" 2>&1
    printf 'mode=%s AW=%s program words=%s: ' "$mode" "$aw" "$((1 << aw))"
    grep 'Chip area for top module' "$log"
    if [ "$mode" = static ]; then
      latches=$((24 * (1 << aw)))
      logic_area=$(awk '/Chip area for top module/ { area=$NF } END { print area }' "$log")
      awk -v n="$latches" -v a="$logic_area" 'BEGIN { printf "  config latches=%d, mapped latch area=%.2f um^2, combined estimate=%.2f um^2\n", n, n*30.8448, a+n*30.8448 }'
    fi
  done
done
