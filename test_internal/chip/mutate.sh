#!/usr/bin/env bash
# L7-style mutation check of the chip-level wiring (SRAM rotation, L1-ROT): each mutant is one injected bug in a
# copy of src/; test_rot must fail on every one. Usage (in the venv): test_internal/chip/mutate.sh [ONLY=<text>]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="$(mktemp -d)"
# file # sed expression # what it breaks
MUTANTS=(
  "trw_chip.v#s/\.host_slot (slot == 2'd3)/.host_slot (1'b1)/#R1: the host uses the SRAM on any slot"
  "trw_chip.v#s/\.my_slot (slot == k)/.my_slot (slot[0] == k[0])/#R1: a lane uses another lane's slot"
)
killed=0
for m in "${MUTANTS[@]}"; do
  IFS="#" read -r file expr what <<< "$m"
  [ -n "${ONLY:-}" ] && [[ "$what" != *"$ONLY"* ]] && continue
  rm -rf "$WORK/src"; cp -r "$ROOT/src" "$WORK/src"
  sed -i "$expr" "$WORK/src/$file"
  if cmp -s "$ROOT/src/$file" "$WORK/src/$file"; then echo "NOT APPLIED: $what"; continue; fi
  (cd "$HERE" && make SRC_DIR="$WORK/src" SIM_BUILD="$WORK/build" COCOTB_TEST_MODULES=test_rot \
     COCOTB_RESULTS_FILE="$WORK/r.xml" >"$WORK/log" 2>&1)
  if grep -q "FAIL=0" "$WORK/log"; then echo "SURVIVED: $what"; else
    echo "killed ($(grep -o 'FAIL=[0-9]*' "$WORK/log" || echo 'build error')): $what"; killed=$((killed+1)); fi
done
echo "mutation: $killed of ${#MUTANTS[@]} killed"
rm -rf "$WORK"
