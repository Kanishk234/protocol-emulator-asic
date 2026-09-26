#!/usr/bin/env bash
# L7-style mutation check of the pin unit: each mutant is one injected bug in a copy of src/; the L1
# suite must fail on every one. Usage (in the venv): test_internal/pin/mutate.sh
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="$(mktemp -d)"
# file # sed expression # what it breaks
MUTANTS=(
  "trw_pin_tx.v#s/(tail \&\& (bt_i <= 16'd1))/(tail \&\& (bt_i == 16'd0))/#P3: take one clock late after a shift"
  "trw_pin_tx.v#s/assign late_set = tk_late/assign late_set = 1'b0 \&\& tk_late/#P4: LATE never set"
  "trw_pin_tx.v#s/wire \[7:0\] p_frac = tk_late ? 8'h00 : cf_b;/wire [7:0] p_frac = 8'h00;/#P4: cursor fraction dropped"
  "trw_pin_rx.v#s/wire taint = ftaint || echo;/wire taint = ftaint;/#P13: echo taint ignored"
  "trw_pin_rx.v#s/wire ev = edge_ok \&\& qual_ok;/wire ev = edge_ok;/#P8: EV_QUAL ignored"
  "trw_pin_rx.v#s/(want \&\& !rx_free) || //#4.5: OVERRUN on a full producer"
  "trw_pin_tx.v#s/end else if (!p_first \&\& stretch) begin/end else if (1'b0) begin/#P11: STRETCH ignored"
  "trw_pin_tx.v#s/lk_pre <= tk \&\& h_lk \&\& tx_preload/lk_pre <= 1'b0 \&\& tx_preload/#P9: preload ignored"
  "trw_pin_tx.v#s/wire lk_abort = linked \&\& sel_fall/wire lk_abort = 1'b0 \&\& sel_fall/#P15: deselect abort ignored"
  "trw_pin_rx.v#s/wire \[23:0\] rt_cur = start ? sampleofs : rt;/wire [23:0] rt_cur = start ? sampleofs + 24'd256 : rt;/#P5: sample one clock late"
  "trw_pin_tx.v#s/wire w_fire = w_v \&\& (w_rise ? b_rise : b_fall);/wire w_fire = w_v \&\& (b_rise || b_fall);/#P16: WAIT on either edge"
  "trw_pin_tx.v#s/wire \[0:0\] nlvx = d_hi ? (d_hi_v ^ idle) : due_lvl_v ? (due_lvl ^ idle) : d_lo ? 1'b0 : lvx;/wire [0:0] nlvx = d_hi ? (d_hi_v ^ idle) : d_lo ? 1'b0 : due_lvl_v ? (due_lvl ^ idle) : lvx;/#P4: return-to-IDLE beats a LEVEL on its edge"
)
killed=0
for m in "${MUTANTS[@]}"; do
  IFS="#" read -r file expr what <<< "$m"
  rm -rf "$WORK/src"; cp -r "$ROOT/src" "$WORK/src"
  sed -i "$expr" "$WORK/src/$file"
  if cmp -s "$ROOT/src/$file" "$WORK/src/$file"; then echo "NOT APPLIED: $what"; continue; fi
  (cd "$HERE" && make SRC_DIR="$WORK/src" SIM_BUILD="$WORK/build" COCOTB_RESULTS_FILE="$WORK/r.xml" >"$WORK/log" 2>&1)
  if grep -q "FAIL=0" "$WORK/log"; then echo "SURVIVED: $what"; else
    echo "killed ($(grep -o 'FAIL=[0-9]*' "$WORK/log")): $what"; killed=$((killed+1)); fi
done
echo "mutation: $killed of ${#MUTANTS[@]} killed"
rm -rf "$WORK"
