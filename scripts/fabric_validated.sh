#!/usr/bin/env bash
# Full reference fabric behind the validated word boundary; no new P&R.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "${1:-}" != --runner-snapshot ]; then
  mkdir -p "$ROOT/build"
  runner=$(mktemp "$ROOT/build/fabric-validated-runner.XXXXXXXX.sh")
  cp "${BASH_SOURCE[0]}" "$runner"
  exec bash "$runner" --runner-snapshot "$@"
fi
shift
INPUT=$(realpath "${1:?Usage: fabric_validated.sh build/fabric-reference-RUN}")
VARIANT=${2:-word}
case "$VARIANT" in word) defines=() ;; byte) defines=(-DBYTE_CRC) ;; *) echo 'CRC variant must be word or byte' >&2; exit 2 ;; esac
LOADER=${3:-all-ports}
case "$LOADER" in all-ports) patch_args=() ;; word-only) patch_args=(--word-only-loader) ;; *) echo 'Loader must be all-ports or word-only' >&2; exit 2 ;; esac
WORK=$(mktemp -d /tmp/warp-validated.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Validated fabric evidence: $OUT"' EXIT
cp "${BASH_SOURCE[0]}" "$WORK/runner.sh"
printf 'CRC variant=%s\nLoader=%s\n' "$VARIANT" "$LOADER" > "$WORK/run.txt"
for file in reload_tb.v wp_image_validator.v wp_validated_reload.v wp_reload_guard.v reference_validated_top.v validated_images.py frame_snapshot.py; do
  cp "$ROOT/experiments/fabric_reference/$file" "$WORK/"
done
python "$WORK/validated_images.py" "$INPUT" "$WORK"
cp "$ROOT/patches/reference_reload_hold.py" "$WORK/reference_reload_hold.py"
python "$WORK/reference_reload_hold.py" "$INPUT/reference/Test/build/fabric_files" "$WORK/fabric_files" "${patch_args[@]}"
sha256sum "$WORK/fabric_files"/*.v > "$WORK/fabric-sha256.txt"
sha256sum "$WORK"/*.v "$WORK"/*.py "$WORK/runner.sh" "$ROOT/patches/reference_reload_hold.py" "$INPUT/counter.bin" "$INPUT/lfsr.bin" > "$WORK/input-sha256.txt"
iverilog -V > "$WORK/versions.txt" 2>&1
source "$WORK/crc.env"
iverilog -g2012 "${defines[@]}" -DRELOAD_HOLD -DRELOAD_GUARD -DRELOAD_VALIDATED -s reload_tb -o "$WORK/test.vvp" "$WORK/fabric_files"/*.v "$WORK/wp_image_validator.v" "$WORK/wp_validated_reload.v" "$WORK/wp_reload_guard.v" "$WORK/reference_validated_top.v" "$WORK/reload_tb.v" > "$WORK/compile.log" 2>&1
for scenario in aba-full bab-fast recover-33 recover-199 corrupt duplicate padding loader-reset negative; do
  extra=(+quick +fast_words)
  image_a="$WORK/counter.hex"; metadata_a="$crc_counter"
  expected_exit=0; marker='PASS: A/B/A reload'
  case "$scenario" in
    aba-full) extra=() ;;
    bab-fast) extra+=(+start_b); marker='PASS: B/A/B reload' ;;
    recover-*) extra+=(+interrupt_frames="${scenario#recover-}"); marker='PASS: interrupted-load recovery' ;;
    corrupt) extra+=(+reject_image="$WORK/corrupt.hex" +reject_crc="$crc_lfsr"); marker='PASS: rejected-image recovery' ;;
    duplicate) extra+=(+reject_image="$WORK/duplicate.hex" +reject_crc="$crc_duplicate"); marker='PASS: rejected-image recovery' ;;
    padding) extra+=(+reject_image="$WORK/lfsr.hex" +reject_crc="$crc_lfsr" +reject_bytes=12028); marker='PASS: rejected-image recovery' ;;
    loader-reset) extra+=(+reject_image="$WORK/lfsr.hex" +reject_crc="$crc_lfsr" +reject_error=0 +reset_after_load); marker='PASS: rejected-image recovery' ;;
    negative) extra+=(+cold_a); image_a="$WORK/lfsr.hex"; metadata_a="$crc_lfsr"; expected_exit=1; marker='FAIL: functional mismatch' ;;
  esac
  result=0
  timeout -s INT -k 5s 180s vvp -n "$WORK/test.vvp" "${extra[@]}" +image_a="$image_a" +image_b="$WORK/lfsr.hex" +crc_a="$metadata_a" +crc_b="$crc_lfsr" > "$WORK/$scenario.log" 2>&1 || result=$?
  printf '%s %s\n' "$scenario" "$result" | tee -a "$WORK/exit-codes.txt"
  if [ "$result" -ne "$expected_exit" ] || ! grep -Fq "$marker" "$WORK/$scenario.log"; then
    echo "Validated fabric scenario failed: $scenario"
    exit 1
  fi
done
echo 'PASS: validated full-fabric reload/rejection suite (RTL only, two compiled designs)'
