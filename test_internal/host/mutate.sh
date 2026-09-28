#!/usr/bin/env bash
# L7-style mutation check of the host: each mutant is one injected bug in a copy of src/; the L1-HOST suite
# must fail on every one. Usage (in the venv): test_internal/host/mutate.sh [ONLY=<text>]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="$(mktemp -d)"
# file # sed expression # what it breaks
MUTANTS=(
  "trw_host.v#s/            out_pend <= (ra == \`TRW_HA_HOST_OUT) \&\& hout_avail \&\& (!st_seen || st_av);/            out_pend <= (ra == \`TRW_HA_HOST_OUT) \&\& hout_avail;/#BUGS #48: a token arriving after the status is taken"
  "trw_host.v#s/    assign hout_take = rd_done \&\& out_pend;/    assign hout_take = rd_ack \&\& (ra == \`TRW_HA_HOST_OUT) \&\& hout_avail;/#BUGS #47: a prefetch takes HOST_OUT"
  "trw_host.v#s/            step <= w_step ? (wd\[NL-1:0\] \& ~run) : {NL{1'b0}};/            step <= w_step ? wd[NL-1:0] : {NL{1'b0}};/#H2: STEP reaches a running lane"
  "trw_host.v#s/assign slot_we\[g\]  = w_sl \&\& (o_sl\[9:8\] == g) \&\& !run\[g\];/assign slot_we[g]  = w_sl \&\& (o_sl[9:8] == g);/#9: slot writes to a running lane"
  "trw_host.v#s/assign clr_late\[g\]    = w_uf \&\& (o_uf\[2:0\] == g) \&\& wd\[1\];/assign clr_late[g]    = w_uf \&\& (o_uf[2:0] == g) \&\& wd[0];/#D-042: LATE cleared by bit 0"
  "trw_host.v#s/            irq <= |(irq_st \& irq_en);/            irq <= |irq_st;/#D-046: IRQ ignores the enable"
  "trw_host.v#s/    wire w_sl   = wr \&\& (o_sl < \`TRW_HA_SLOTS_N) \&\& (o_sl\[3:2\] == 2'd0);/    wire w_sl   = wr \&\& (o_sl < \`TRW_HA_SLOTS_N);/#9: slot address bits [3:2] alias"
  "trw_host.v#s/\`TRW_HL_CHANNELS:     lane_word = {10'd0, ld\[103\], ld\[105\], ld\[102\], ld\[104\], ld\[143:142\]};/\`TRW_HL_CHANNELS:     lane_word = {10'd0, ld[105], ld[103], ld[104], ld[102], ld[143:142]};/#D-046: channel bits swapped"
  "trw_host.v#s/    assign hin_tok      = {o_hi\[1:0\], wd};/    assign hin_tok      = {2'd0, wd};/#D-046: HOST_IN tag ignored"
  "trw_host.v#s/    assign mem_en    = host_slot \&\& hp_v;/    assign mem_en    = hp_v;/#R1: SRAM access off the host slot"
  "trw_host.v#s/                live <= live || (wd\[NL-1:0\] != {NL{1'b0}});/                live <= (wd[NL-1:0] != {NL{1'b0}});/#D-041 B: live drops with RUN"
  "trw_host.v#s/    wire w_ln   = wr \&\& (o_ln < NL \* \`TRW_HA_LANE_STRIDE) \&\& (o_ln\[4:0\] <= \`TRW_HL_STATE);/    wire w_ln   = wr \&\& (o_ln < NL * \`TRW_HA_LANE_STRIDE);/#E2: read-only lane words writable"
  "trw_pins.v#s/else if (own_we \&\& !HOSTPAD\[own_waddr\])/else if (own_we)/#7.1: owner of a host pad writable"
)
killed=0
for m in "${MUTANTS[@]}"; do
  IFS="#" read -r file expr what <<< "$m"
  [ -n "${ONLY:-}" ] && [[ "$what" != *"$ONLY"* ]] && continue
  rm -rf "$WORK/src"; cp -r "$ROOT/src" "$WORK/src"
  sed -i "$expr" "$WORK/src/$file"
  if cmp -s "$ROOT/src/$file" "$WORK/src/$file"; then echo "NOT APPLIED: $what"; continue; fi
  (cd "$HERE" && make SRC_DIR="$WORK/src" SIM_BUILD="$WORK/build" COCOTB_RESULTS_FILE="$WORK/r.xml" >"$WORK/log" 2>&1)
  if grep -q "FAIL=0" "$WORK/log"; then echo "SURVIVED: $what"; else
    echo "killed ($(grep -o 'FAIL=[0-9]*' "$WORK/log" || echo 'build error')): $what"; killed=$((killed+1)); fi
done
echo "mutation: $killed of ${#MUTANTS[@]} killed"
rm -rf "$WORK"
