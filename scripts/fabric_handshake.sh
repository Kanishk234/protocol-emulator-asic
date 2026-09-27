#!/usr/bin/env bash
# Small actual-loader regression; fixture replaces the programmable fabric.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT=$(realpath "${1:?Usage: fabric_handshake.sh build/fabric-reference-RUN}")
WORK=$(mktemp -d /tmp/warp-handshake.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Handshake evidence: $OUT"' EXIT
cp "${BASH_SOURCE[0]}" "$WORK/runner.sh"
for name in wp_image_validator.v wp_validated_reload.v wp_reload_guard.v reference_validated_top.v loader_fixture.v loader_handshake_tb.v; do
  cp "$ROOT/experiments/fabric_reference/$name" "$WORK/"
done
for name in eFPGA_Config.v ConfigFSM.v Frame_Data_Reg.v config_UART.v bitbang.v; do
  cp "$INPUT/reference/Test/build/fabric_files/$name" "$WORK/"
done
python - "$INPUT/counter.bin" "$WORK" <<'PY'
import sys, struct, zlib
from pathlib import Path
data = Path(sys.argv[1]).read_bytes()
assert len(data)==12024
out = Path(sys.argv[2])
out.joinpath("counter.hex").write_text("".join(f"{w:08x}\n" for w in struct.unpack(">3006I",data)))
out.joinpath("crc.txt").write_text(f"{zlib.crc32(data):08x}")
PY
sha256sum "$WORK"/*.v "$WORK/runner.sh" "$INPUT/counter.bin" > "$WORK/input-sha256.txt"
iverilog -V > "$WORK/versions.txt" 2>&1
cd "$WORK"
for variant in byte word; do
  defines=(); if [ "$variant" = word ]; then defines=(-DWORD_CRC); fi
  iverilog -g2012 "${defines[@]}" -s loader_handshake_tb -o "$variant.vvp" ./*.v > "$variant-compile.log" 2>&1
  timeout 20s vvp "$variant.vvp" +image=counter.hex +crc="$(cat crc.txt)" > "$variant.log" 2>&1
  grep '^PASS: loader handshake' "$variant.log"
done
