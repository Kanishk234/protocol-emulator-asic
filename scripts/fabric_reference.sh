#!/usr/bin/env bash
# Activate the project venv and put OSS CAD Suite 2026-06-29 on PATH.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
for tool in FABulous yosys nextpnr-generic iverilog vvp timeout; do
  command -v "$tool" >/dev/null || { echo "missing tool: $tool" >&2; exit 1; }
done
python -c 'import sys; from importlib.metadata import version; assert sys.prefix != sys.base_prefix, "activate the project venv"; assert version("FABulous-FPGA") == "2.2.0", "expected FABulous 2.2.0"'
yosys -V | grep -q '0.66+179.*e74db6dea' || {
  echo 'Use OSS CAD Suite 2026-06-29; newer synth_fabulous is incompatible.' >&2
  exit 1
}
# Upstream Taskfiles do not quote paths. Build outside Windows Documents.
WORK=$(mktemp -d /tmp/warp-reference.XXXXXXXX)
OUT="$ROOT/build/fabric-reference-$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Reference evidence: $OUT"' EXIT
{ yosys -V; nextpnr-generic --version; iverilog -V; python --version;
  python -c 'from importlib.metadata import distributions; print("\n".join(sorted(d.metadata["Name"] + "==" + d.version for d in distributions())))'
} > "$WORK/versions.txt" 2>&1
git rev-parse HEAD > "$WORK/base-commit.txt"
find experiments/fabric_reference -maxdepth 1 -type f -print0 \
  | sort -z | xargs -0 sha256sum > "$WORK/input-sha256.txt"
sha256sum scripts/fabric_reference.sh >> "$WORK/input-sha256.txt"
FABulous create-project "$WORK/reference" > "$WORK/create.log" 2>&1
cp experiments/fabric_reference/reference.fab "$WORK/reference/"
cp experiments/fabric_reference/sequential_16bit_en.v "$WORK/reference/user_design/"
FABulous -p "$WORK/reference" script --type fabulous "$WORK/reference/reference.fab" > "$WORK/counter.log" 2>&1
cp "$WORK/reference/user_design/sequential_16bit_en.bin" "$WORK/counter.bin"
cp "$WORK/reference/user_design/sequential_16bit_en_npnr_log.txt" "$WORK/counter-pnr.log"
# Keep the same fabric and wrapper; the second source has the same interface.
cp experiments/fabric_reference/lfsr.v "$WORK/reference/user_design/sequential_16bit_en.v"
printf 'load_fabric\ncompile_design user_design/sequential_16bit_en.v\nexit\n' > "$WORK/reference/second.fab"
FABulous -p "$WORK/reference" script --type fabulous "$WORK/reference/second.fab" > "$WORK/lfsr.log" 2>&1
cp "$WORK/reference/user_design/sequential_16bit_en.bin" "$WORK/lfsr.bin"
cp "$WORK/reference/user_design/sequential_16bit_en_npnr_log.txt" "$WORK/lfsr-pnr.log"
test -s "$WORK/counter.bin" && test -s "$WORK/lfsr.bin"
if cmp -s "$WORK/counter.bin" "$WORK/lfsr.bin"; then
  echo 'Distinct circuits produced identical bitstreams' >&2; exit 1
fi
for design in counter lfsr; do
  python "$WORK/reference/Test/makehex.py" "$WORK/$design.bin" 16384 "$WORK/$design.hex"
done
python -m tools.fabric_audit.configmem "$WORK/reference/Tile/LUT4AB/LUT4AB_ConfigMem.csv" \
  --frame-width 32 --frames 20 --expected-bits 616 > "$WORK/configmem.json"
sha256sum "$WORK"/*.bin > "$WORK/bitstream-sha256.txt"
find "$WORK/reference/Fabric" "$WORK/reference/Tile" -type f -name '*.v' -print0 \
  | sort -z | xargs -0 sha256sum > "$WORK/fabric-sha256.txt"
cp experiments/fabric_reference/reload_tb.v "$WORK/reference/Test/"
(
  cd "$WORK/reference/Test"
  iverilog -g2012 -s reload_tb -o "$WORK/reload.vvp" build/fabric_files/*.v reload_tb.v
  timeout -k 5s 90s vvp "$WORK/reload.vvp" +cold_b +image_a="$WORK/counter.hex" +image_b="$WORK/lfsr.hex" > "$WORK/cold-lfsr.log" 2>&1
  grep -q '^PASS: cold LFSR' "$WORK/cold-lfsr.log"
  if timeout -k 5s 90s vvp "$WORK/reload.vvp" +image_a="$WORK/lfsr.hex" +image_b="$WORK/lfsr.hex" > "$WORK/negative.log" 2>&1; then
    echo 'Wrong-bitstream negative control unexpectedly passed' >&2; exit 1
  else
    result=$?
    test "$result" -eq 1 || { echo "Negative control did not finish with the expected fatal exit: $result" >&2; exit 1; }
  fi
  grep -q 'FAIL: functional mismatch' "$WORK/negative.log"
  timeout -k 5s 300s vvp "$WORK/reload.vvp" +image_a="$WORK/counter.hex" +image_b="$WORK/lfsr.hex" > "$WORK/reload.log" 2>&1 || {
    result=$?
    echo "Persistent reload failed (exit $result); inspect reload.log. No reload PASS is claimed." >&2
    exit "$result"
  }
  grep -q '^PASS: A/B/A reload' "$WORK/reload.log"
)
echo 'Reference compile, A/B/A reload, negative control and configuration audit: PASS'
