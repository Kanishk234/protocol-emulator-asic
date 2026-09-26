#!/usr/bin/env bash
# Marginal area of each lean pin-unit feature: tie the feature's decode to 0 in a copy of the RTL and
# resynthesize trw_pin_unit (Yosys, cmos5l typ, the run_pin.sh recipe). Not a design: a price list.
# Usage: synth/pin/ablate.sh    (liberty cached by spikes/r1_lane/run_r1.sh)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
TYP="${XDG_CACHE_HOME:-$HOME/.cache}/tripwire/pdk-2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib"
WORK="$(mktemp -d)"
V=(
  "baseline#trw_pin_tx.v#s/^//"
  "CLKGEN (incl. STRETCH, extension)#trw_pin_tx.v#s/wire m_clk   = (txmode == \`TRW_PCE_TXMODE_CLKGEN);/wire m_clk = 1'b0;/"
  "linked TX (incl. preload, abort)#trw_pin_tx.v#s/wire linked  = m_shift \&\& (tx_edge != \`TRW_PCE_TX_EDGE_NONE);/wire linked = 1'b0;/"
  "timed SHIFT#trw_pin_tx.v#s/wire tshift  = m_shift \&\& !linked;/wire tshift = 1'b0;/"
  "timed SHIFT and CLKGEN (the burst timer)#trw_pin_tx.v#s/wire tshift  = m_shift \&\& !linked;/wire tshift = 1'b0;/; s/wire m_clk   = (txmode == \`TRW_PCE_TXMODE_CLKGEN);/wire m_clk = 1'b0;/"
  "WAIT#trw_pin_tx.v#s/wire c_wait = t_ctrl \&\& (op == \`TRW_CMD_WAIT);/wire c_wait = 1'b0;/"
  "SAMPLE + SETN rx#trw_pin_tx.v#s/wire c_smp  = t_ctrl \&\& (op == \`TRW_CMD_SAMPLE);/wire c_smp = 1'b0;/; s/wire h_rxs   = c_setn \&\& arg\[5\];/wire h_rxs = 1'b0;/"
  "SHIFT_RX#trw_pin_rx.v#s/wire m_srx = (rxmode == \`TRW_PCE_RXMODE_SHIFT_RX);/wire m_srx = 1'b0;/"
  "LINKED_RX#trw_pin_rx.v#s/wire m_lrx = (rxmode == \`TRW_PCE_RXMODE_LINKED_RX);/wire m_lrx = 1'b0;/"
  "event generator (incl. tick counter)#trw_pin_rx.v#s/wire ev = edge_ok \&\& qual_ok;/wire ev = 1'b0;/"
)
base=""
printf "%-40s %10s %8s\n" "without" "area_um2" "saves"
for v in "${V[@]}"; do
  IFS="#" read -r what file expr <<< "$v"
  rm -rf "$WORK/src"; cp -r "$ROOT/src" "$WORK/src"
  sed -i "$expr" "$WORK/src/$file"
  S="$WORK/src"
  yosys -q -p "read_liberty -lib $TYP; read_verilog -DSYNTHESIS -I$S $S/trw_pin_io.v $S/trw_pin_tx.v $S/trw_pin_rx.v $S/trw_pin_unit.v; \
    synth -top trw_pin_unit -flatten; dfflibmap -liberty $TYP; abc -liberty $TYP; opt_clean; tee -o $WORK/stat.txt stat -liberty $TYP" >/dev/null 2>&1 \
    || { echo "$what: synthesis failed"; continue; }
  a=$(awk '/Chip area for module/ {a=$NF} END {printf "%.0f", a}' "$WORK/stat.txt")
  [ -z "$base" ] && base=$a
  printf "%-40s %10s %8s\n" "$what" "$a" "$((base - a))"
done
rm -rf "$WORK"
