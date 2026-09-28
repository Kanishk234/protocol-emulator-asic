#!/usr/bin/env bash
# L7-style mutation check of the channel fabric: each mutant is one injected bug in a copy of src/; the
# L1-CHAN suite must fail on every one. Usage (in the venv): test_internal/chan/mutate.sh [ONLY=<text>]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
WORK="$(mktemp -d)"
# file # sed expression # what it breaks
MUTANTS=(
  "trw_chan_port.v#s/assign blocking = en \&\& !tap;/assign blocking = en;/#4.2: a tap holds its producer"
  "trw_chan_port.v#s/wire drop     = tap \&\& avail \&\& !take \&\& s_load;/wire drop     = 1'b0 \&\& s_load;/#F4: tap drops not counted"
  "trw_chan_port.v#s/end else if (took || filtered || drop) begin/end else if (took || filtered) begin/#F4: a drop does not count as a take (BUGS #2)"
  "trw_chan_port.v#s/last_seq <= w_seq;/last_seq <= s_seq;/#F5: re-pointing uses the old source's seq"
  "trw_chan_port.v#s/wire filtered = present \&\& !accepted;/wire filtered = 1'b0 \&\& accepted;/#F7: a filtered token is not dropped"
  "trw_chan_port.v#s/wire accepted = accept\[s_tok\[17:16\]\];/wire accepted = accept[{s_tok[16], s_tok[17]}];/#F7: tag bits swapped in the mask"
  "trw_chan_port.v#s/dropped <= (dropped == 8'hff) ? 8'hff : dropped + 8'd1;/dropped <= dropped + 8'd1;/#F4: DROPPED wraps"
  "trw_chan_port.v#s/if ({28'd0, sel} == n) begin/if ({29'd0, sel[2:0]} == n) begin/#4.6: sel wraps past the list"
  "trw_chan_prod.v#s/assign free = !valid || all_taken;/assign free = 1'b1 || all_taken || valid;/#F3: producer overwrites an untaken token"
  "trw_fabric.v#0,/(!blk\[0\] ||/s//(1'b1 ||/#4.4: a release term ignores one blocking subscriber"
)
killed=0
for m in "${MUTANTS[@]}"; do
  IFS="#" read -r file expr what <<< "$m"
  [ -n "${ONLY:-}" ] && [[ "$what" != *"$ONLY"* ]] && continue      # ONLY=<text>: just the matching mutants
  rm -rf "$WORK/src"; cp -r "$ROOT/src" "$WORK/src"
  sed -i "$expr" "$WORK/src/$file"
  if cmp -s "$ROOT/src/$file" "$WORK/src/$file"; then echo "NOT APPLIED: $what"; continue; fi
  (cd "$HERE" && make SRC_DIR="$WORK/src" SIM_BUILD="$WORK/build" COCOTB_RESULTS_FILE="$WORK/r.xml" >"$WORK/log" 2>&1)
  if grep -q "FAIL=0" "$WORK/log"; then echo "SURVIVED: $what"; else
    echo "killed ($(grep -o 'FAIL=[0-9]*' "$WORK/log")): $what"; killed=$((killed+1)); fi
done
echo "mutation: $killed of ${#MUTANTS[@]} killed"
rm -rf "$WORK"
