#!/usr/bin/env bash
# Rerun independent tests using already-generated fabric RTL and bitstreams.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT=$(realpath "${1:?Usage: fabric_recheck.sh build/fabric-reference-RUN}")
MODE=${2:-all}
case "$MODE" in all|probe|counter) ;; *) echo 'Mode must be all, probe or counter' >&2; exit 2 ;; esac
WORK=$(mktemp -d /tmp/warp-recheck.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
# Keep logs on the Windows volume even if WSL later removes its /tmp files.
trap 'cp -a "$WORK"/. "$OUT"/; echo "Recheck evidence: $OUT"' EXIT
cp "$INPUT/counter.hex" "$INPUT/lfsr.hex" "$WORK/"
cp "$ROOT/experiments/fabric_reference/reload_tb.v" "$WORK/"
extra=()
if [ "$MODE" = probe ]; then
  cp "$ROOT/experiments/fabric_reference/reload_probe.v" "$WORK/"
  extra=(-s reload_probe "$WORK/reload_probe.v")
fi
sha256sum "$INPUT/counter.bin" "$INPUT/lfsr.bin" "$WORK/reload_tb.v" > "$WORK/input-sha256.txt"
if [ "$MODE" = probe ]; then sha256sum "$WORK/reload_probe.v" >> "$WORK/input-sha256.txt"; fi
iverilog -g2012 -s reload_tb "${extra[@]}" -o "$WORK/test.vvp" "$INPUT"/reference/Test/build/fabric_files/*.v "$WORK/reload_tb.v"
run_case() {
  local name=$1 limit=$2
  shift 2
  local result=0
  timeout -s INT -k 5s "$limit" vvp -n -v "$WORK/test.vvp" "$@" > "$WORK/$name.log" 2>&1 || result=$?
  CASE_RESULT=$result
  printf '%s %s\n' "$name" "$result" | tee -a "$WORK/exit-codes.txt"
}
if [ "$MODE" = probe ]; then
  run_case probe 90s +quick +trace_load +image_a="$WORK/counter.hex" +image_b="$WORK/lfsr.hex"
  grep '^OSCILLATION:' "$WORK/probe.log"
  echo 'Diagnostic only: reload is still a failure.'
  exit 1
fi
if [ "$MODE" = counter ]; then
  run_case cold-counter 180s +cold_a +image_a="$WORK/counter.hex" +image_b="$WORK/lfsr.hex"
  test "$CASE_RESULT" -eq 0
  grep '^PASS: cold counter' "$WORK/cold-counter.log"
  exit 0
fi
run_case cold-lfsr 90s +cold_b +image_a="$WORK/counter.hex" +image_b="$WORK/lfsr.hex"
cold_result=$CASE_RESULT
run_case negative 90s +image_a="$WORK/lfsr.hex" +image_b="$WORK/lfsr.hex"
negative_result=$CASE_RESULT
run_case reload-quick 90s +quick +trace_load +image_a="$WORK/counter.hex" +image_b="$WORK/lfsr.hex"
test "$cold_result" -eq 0
test "$negative_result" -eq 1
test "$CASE_RESULT" -eq 0
grep -q '^PASS: cold LFSR' "$WORK/cold-lfsr.log"
grep -q 'FAIL: functional mismatch' "$WORK/negative.log"
grep -q '^PASS: A/B/A reload' "$WORK/reload-quick.log"
echo 'Cached-image checks: PASS (quick reload; excludes wraparound)'
