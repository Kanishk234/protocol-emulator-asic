#!/usr/bin/env bash
# Screen loading orders with identical addressed payloads; no new P&R.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "${1:-}" != --runner-snapshot ]; then
  mkdir -p "$ROOT/build"
  runner=$(mktemp "$ROOT/build/fabric-order-runner.XXXXXXXX.sh")
  cp "${BASH_SOURCE[0]}" "$runner"
  exec bash "$runner" --runner-snapshot "$@"
fi
shift
INPUT=$(realpath "${1:?Usage: fabric_order.sh build/fabric-reference-RUN [order]}")
ORDER=${2:-reverse}
MODE=${3:-quick}
case "$MODE" in quick|validate) ;; *) echo 'Mode must be quick or validate' >&2; exit 2 ;; esac
WORK=$(mktemp -d /tmp/warp-order.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
cp "${BASH_SOURCE[0]}" "$WORK/runner.sh"
printf 'order=%s\nmode=%s\ninput=%s\n' "$ORDER" "$MODE" "$INPUT" > "$WORK/run.txt"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Load-order evidence: $OUT"' EXIT
load_options=()
if [ "$ORDER" = hold ] || [ "$ORDER" = guarded ]; then
  cp "$INPUT/counter.hex" "$INPUT/lfsr.hex" "$WORK/"
elif [ "$ORDER" = clear-columns ]; then
  cp "$INPUT/counter.hex" "$INPUT/lfsr.hex" "$WORK/"
  python "$ROOT/experiments/fabric_reference/reorder_frames.py" "$INPUT/counter.bin" "$WORK/clear.bin" clear-columns
  load_options=(+clear_image="$WORK/clear.hex")
else
  for design in counter lfsr; do
    python "$ROOT/experiments/fabric_reference/reorder_frames.py" "$INPUT/$design.bin" "$WORK/$design.bin" "$ORDER"
  done
fi
cp "$ROOT/experiments/fabric_reference/reload_tb.v" "$WORK/"
sha256sum "$WORK/reload_tb.v" "$ROOT/experiments/fabric_reference/reorder_frames.py" "$ROOT/experiments/fabric_reference/frame_snapshot.py" > "$WORK/input-sha256.txt"
sha256sum "$INPUT/counter.bin" "$INPUT/lfsr.bin" >> "$WORK/input-sha256.txt"
sha256sum "$WORK/runner.sh" >> "$WORK/input-sha256.txt"
iverilog -V > "$WORK/simulator-version.txt" 2>&1
fabric_files="$INPUT/reference/Test/build/fabric_files"
defines=()
extra_sources=()
if [ "$ORDER" = hold ] || [ "$ORDER" = guarded ]; then
  python "$ROOT/patches/reference_reload_hold.py" "$fabric_files" "$WORK/fabric_files"
  sha256sum "$ROOT/patches/reference_reload_hold.py" >> "$WORK/input-sha256.txt"
  fabric_files="$WORK/fabric_files"
  defines=(-DRELOAD_HOLD)
  cp "$ROOT/experiments/fabric_reference/hold_cell_tb.v" "$WORK/"
  sha256sum "$WORK/hold_cell_tb.v" >> "$WORK/input-sha256.txt"
  iverilog -g2012 -s hold_cell_tb -o "$WORK/cell.vvp" "$fabric_files/LUT4c_frame_config_dffesr.v" "$fabric_files/models_pack.v" "$WORK/hold_cell_tb.v"
  timeout 10s vvp "$WORK/cell.vvp" > "$WORK/cell.log" 2>&1
  grep '^PASS: held/released primitive' "$WORK/cell.log"
fi
if [ "$ORDER" = guarded ]; then
  defines+=(-DRELOAD_GUARD)
  for name in wp_reload_guard.v reference_guarded_top.v guard_tb.v; do
    cp "$ROOT/experiments/fabric_reference/$name" "$WORK/"
    sha256sum "$WORK/$name" >> "$WORK/input-sha256.txt"
  done
  extra_sources=("$WORK/wp_reload_guard.v" "$WORK/reference_guarded_top.v")
  iverilog -g2012 -s guard_tb -o "$WORK/guard.vvp" "$WORK/wp_reload_guard.v" "$WORK/guard_tb.v"
  timeout 10s vvp "$WORK/guard.vvp" > "$WORK/guard.log" 2>&1
  grep '^PASS: guard sequencing' "$WORK/guard.log"
fi
iverilog -g2012 "${defines[@]}" -s reload_tb -o "$WORK/test.vvp" "$fabric_files"/*.v "${extra_sources[@]}" "$WORK/reload_tb.v"
failed=0
cases=(aba bab)
if [ "$MODE" = validate ]; then cases=(aba-full recover-33 recover-199 negative); fi
for direction in "${cases[@]}"; do
  extra=(+quick)
  expected_exit=0
  image_a="$WORK/counter.hex"
  marker='PASS: A/B/A reload'
  case "$direction" in
    bab) extra+=(+start_b); marker='PASS: B/A/B reload' ;;
    aba-full) extra=() ;;
    recover-*) extra+=(+interrupt_frames="${direction#recover-}"); marker='PASS: interrupted-load recovery' ;;
    negative) extra=(+cold_a); image_a="$WORK/lfsr.hex"; expected_exit=1; marker='FAIL: functional mismatch' ;;
  esac
  result=0
  timeout -s INT -k 5s 180s vvp -n "$WORK/test.vvp" +trace_load "${extra[@]}" "${load_options[@]}" +image_a="$image_a" +image_b="$WORK/lfsr.hex" > "$WORK/$direction.log" 2>&1 || result=$?
  printf '%s %s\n' "$direction" "$result" | tee -a "$WORK/exit-codes.txt"
  if [ "$result" -ne "$expected_exit" ] || ! grep -Fq "$marker" "$WORK/$direction.log"; then failed=1; fi
done
if [ "$failed" -ne 0 ]; then echo 'Loading-order screen FAILED; no repair claimed.'; exit 1; fi
echo "Loading/isolation $MODE checks PASS for these two images only; see case logs for coverage."
