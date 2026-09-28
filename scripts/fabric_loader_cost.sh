#!/usr/bin/env bash
# Bounded wrapper + loader + row-register measurement, fabric side opaque.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "${1:-}" != --runner-snapshot ]; then
  mkdir -p "$ROOT/build"
  runner=$(mktemp "$ROOT/build/fabric-loader-cost-runner.XXXXXXXX.sh")
  cp "${BASH_SOURCE[0]}" "$runner"
  exec bash "$runner" --runner-snapshot "$@"
fi
shift
INPUT=$(realpath "${1:?Usage: fabric_loader_cost.sh build/fabric-reference-RUN}")
PORTS=${2:-all-ports}
case "$PORTS" in
  all-ports) loader_defines='-DLOADER_BOUNDARY' ;;
  word-only) loader_defines='-DLOADER_BOUNDARY -DWORD_ONLY_LOADER' ;;
  *) echo 'Port mode must be all-ports or word-only' >&2; exit 2 ;;
esac
WORK=$(mktemp -d /tmp/warp-loader-cost.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Loader-inclusive evidence: $OUT"' EXIT
cp "${BASH_SOURCE[0]}" "$WORK/runner.sh"
printf 'loader_ports=%s\n' "$PORTS" > "$WORK/run.txt"
for name in wp_image_validator.v wp_validated_reload.v wp_reload_guard.v reference_validated_top.v loader_fixture.v loader_handshake_tb.v wp_loader_boundary.v loader_area_report.py; do
  cp "$ROOT/experiments/fabric_reference/$name" "$WORK/"
done
for name in eFPGA_Config.v ConfigFSM.v Frame_Data_Reg.v config_UART.v bitbang.v; do
  cp "$INPUT/reference/Test/build/fabric_files/$name" "$WORK/"
done
PDK="${XDG_CACHE_HOME:-$HOME/.cache}/warp/pdk-2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell"
IV="${XDG_CACHE_HOME:-$HOME/.cache}/warp/iverilog-13"
cp "$PDK/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib" "$WORK/cells.lib"
python - "$INPUT" "$WORK" <<'PY'
import sys, struct, zlib
from pathlib import Path
out=Path(sys.argv[2])
for name in ("counter", "lfsr"):
    data=Path(sys.argv[1], name+".bin").read_bytes()
    assert len(data)==12024
    out.joinpath(name+".hex").write_text("".join(f"{w:08x}\n" for w in struct.unpack(">3006I",data)))
    out.joinpath(name+".crc").write_text(f"{zlib.crc32(data):08x}")
PY
sha256sum "$WORK"/*.v "$WORK"/*.py "$WORK/runner.sh" "$WORK/cells.lib" "$PDK"/verilog/*.v "$INPUT/counter.bin" "$INPUT/lfsr.bin" > "$WORK/input-sha256.txt"
yosys -V > "$WORK/versions.txt"
"$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -V >> "$WORK/versions.txt" 2>&1
cd "$WORK"
sources="wp_image_validator.v wp_validated_reload.v wp_reload_guard.v reference_validated_top.v loader_fixture.v eFPGA_Config.v ConfigFSM.v Frame_Data_Reg.v config_UART.v bitbang.v"
for variant in word byte; do
  serial=0; defines=(-DWORD_CRC)
  if [ "$variant" = byte ]; then serial=1; defines=(); fi
  # Retain the loader module boundary for reproducible hierarchical diagnostics.
  # No cross-boundary constant propagation claim: inactive serial logic may remain.
  timeout 120s yosys -Q -T -p "read_verilog -lib wp_loader_boundary.v; read_verilog $loader_defines $sources; setattr -mod -set keep_hierarchy 1 eFPGA_top; chparam -set SERIAL_CRC $serial reference_validated_top; synth -top reference_validated_top -flatten; check -assert; read_liberty -lib cells.lib; dfflibmap -liberty cells.lib; abc -liberty cells.lib; opt_clean; check -assert; tee -o $variant-area.json stat -json -liberty cells.lib; write_json $variant-net.json; write_verilog -noattr -noexpr $variant-net.v" > "$variant-synth.log" 2>&1
  "$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -g2012 -DMAPPED_WRAPPER -DMAPPED_LOADER "${defines[@]}" -s loader_handshake_tb -o "$variant.vvp" "$PDK/verilog/sg13cmos5l_udp.v" "$PDK/verilog/sg13cmos5l_stdcell.v" "$variant-net.v" wp_loader_boundary.v loader_handshake_tb.v > "$variant-compile.log" 2>&1
  for design in counter lfsr; do
    timeout 30s "$IV/usr/bin/vvp" "$variant.vvp" +image="$design.hex" +crc="$(cat "$design.crc")" > "$variant-$design.log" 2>&1
    grep '^PASS: loader handshake' "$variant-$design.log"
  done
done
python loader_area_report.py .
