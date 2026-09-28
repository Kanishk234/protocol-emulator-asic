#!/usr/bin/env bash
# L7-style mutation check of the ALU: each mutant is one injected bug in a copy of src/; the L1-ALU suite
# must fail on every one. Usage (in the venv): test_internal/alu/mutate.sh [ONLY=<text>]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="$(mktemp -d)"
# file # sed expression # what it breaks
MUTANTS=(
  "trw_alu.v#s/wire \[15:0\] emask = 16'hFFFF >> (4'd15 - f\[7:4\]);/wire [15:0] emask = 16'hFFFF >> (4'd15 - f[7:4] + 4'd1);/#EXT: field one bit short"
  "trw_alu.v#s/\`TRW_OP_SHOR:  d = shl | rf;/\`TRW_OP_SHOR:  d = shl;/#SHOR: r[F[5:4]] not ORed in"
  "trw_alu.v#s/wire        use_f = (op == \`TRW_OP_SHOR) || (op == \`TRW_OP_EXT);/wire        use_f = (op == \`TRW_OP_SHOR);/#EXT: shifts by B instead of F"
  "trw_alu.v#s/\`TRW_OP_MKCTL: d = {f\[7:4\], a\[11:0\]};/\`TRW_OP_MKCTL: d = {f[3:0], a[11:0]};/#MKCTL: wrong command nibble"
  "trw_alu.v#s/\`TRW_OP_LTU:  r = (a < b);/\`TRW_OP_LTU:  r = (a <= b);/#LTU: <= instead of <"
  "trw_alu.v#s/\`TRW_OP_PAR:  r = ^a;/\`TRW_OP_PAR:  r = ^a[14:0];/#PAR: top bit left out"
  "trw_alu.v#s/\`TRW_OP_CMPM: r = ((a \& m) == v);/\`TRW_OP_CMPM: r = ((a \& m) == (v \& m));/#CMPM: V masked too"
  "trw_alu.v#s/default:      r = (d == 16'h0000);/default:      r = (d[7:0] == 8'h00);/#R: zero test on the low byte only"
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
    echo "killed ($(grep -o 'FAIL=[0-9]*' "$WORK/log")): $what"; killed=$((killed+1)); fi
done
echo "mutation: $killed of ${#MUTANTS[@]} killed"
rm -rf "$WORK"
