#!/usr/bin/env bash
# L7-style mutation check of the lane: each mutant is one injected bug in a copy of src/; the L1 lane suite
# must fail on every one. Usage (in the venv): test_internal/lane/mutate.sh [ONLY=<text>]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="$(mktemp -d)"
# file # sed expression # what it breaks
MUTANTS=(
  "trw_lane.v#s/                default:       alu_b = {8'd0, ex_imm};/                \`TRW_BSEL_IMM: alu_b = {8'd0, ex_imm};\n                default:       alu_b = 16'd0;/#L12: BSEL 3 reads 0 (the R1 spike's behaviour)"
  "trw_lane.v#s/\`TRW_SYS_GETT:  regs\[16\*rt_fi +: 16\] <= t_lat;/\`TRW_SYS_GETT:  regs[16*rt_fi +: 16] <= time_now;/#R3: GETT reads the time at EXEC (the spike's behaviour)"
  "trw_lane.v#s/    wire        st_v   = rir_v || (ret == 2'd1) || (ret == 2'd3);/    wire        st_v   = rir_v;/#R1: a fetched word competes only from clock k+2"
  "trw_lane.v#s/\&\& (({1'b0, pend} \& fm) == 4'd0);/;/#4.2: pending rule ignored"
  "trw_lane.v#s/            wire call_ok = (op != \`TRW_OP_CALL) || !rb;/            wire call_ok = 1'b1;/#4.2: CALL while a routine runs"
  "trw_lane.v#s/    wire \[11:0\] cand   = ready \& (rt_ok ? urgent : 12'hFFF);/    wire [11:0] cand   = ready;/#4.3: a non-urgent slot beats a waiting step"
  "trw_lane.v#s/                    pend\[s_df\] <= 1'b1;                         \/\/ L9/                    pend[s_df] <= pend[s_df];                   \/\/ L9/#4.4: PEND never set"
  "trw_lane.v#s/                if (s_d_out)\$/                if (1'b0)/#L4: no output reservation"
  "trw_lane.v#s/    wire   do_fet = mem_go \&\& !acc_v \&\& rb \&\& !st_v \&\& !ex_rt; /    wire   do_fet = mem_go \&\& rb \&\& !st_v \&\& !ex_rt; /#R3: a fetch before a pending data access"
  "trw_lane.v#s/            if (rt_djnz)\$/            if (rt_djnz \&\& 1'b0)/#DJNZ does not write rd"
  "trw_lane.v#s/    wire \[AW-1:0\] m_addr = regs\[16\*rt_mra +: AW\] + {{(AW-8){1'b0}}, rt_moff};/    wire [AW-1:0] m_addr = regs[16*rt_mra +: AW];/#R3: LD\/ST offset ignored"
  "trw_lane.v#s/(rt_cond == \`TRW_BR_ALWAYS) ||/(rt_cond[1:0] == 2'd0) ||/#L12: BR condition 4 taken as always"
  "trw_lane.v#s/            if (host_we \&\& !run) begin/            if (host_we) begin/#E2: host writes while running"
  "trw_lane.v#s/    wire       eval_en = run || step;/    wire       eval_en = run;/#H2: STEP ignored"
  "trw_lane.v#s/\`TRW_SYS_CPYF:  if (rt_fi != 2'd3) f\[rt_fi\] <= rz;/\`TRW_SYS_CPYF:  if (rt_fi != 2'd3) f[rt_fi] <= !rz;/#SYS: CPYF copies the inverse of RZ"
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
