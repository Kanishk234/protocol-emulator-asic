#!/usr/bin/env bash
# Isolated word validator + guard; cached images, no fabric rebuild.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "${1:-}" != --runner-snapshot ]; then
  mkdir -p "$ROOT/build"
  runner=$(mktemp "$ROOT/build/fabric-validator-runner.XXXXXXXX.sh")
  cp "${BASH_SOURCE[0]}" "$runner"
  exec bash "$runner" --runner-snapshot "$@"
fi
shift
INPUT=$(realpath "${1:?Usage: fabric_validator.sh build/fabric-reference-RUN}")
VARIANT=${2:-word}
case "$VARIANT" in word) defines=(); serial=0 ;; byte) defines=(-DBYTE_CRC); serial=1 ;; *) echo 'CRC variant must be word or byte' >&2; exit 2 ;; esac
WORK=$(mktemp -d /tmp/warp-validator.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Validator evidence: $OUT"' EXIT
cp "${BASH_SOURCE[0]}" "$WORK/runner.sh"
printf 'CRC variant=%s\n' "$VARIANT" > "$WORK/run.txt"
for file in wp_image_validator.v wp_validated_reload.v wp_reload_guard.v validator_tb.v validator_vectors.py frame_snapshot.py; do
  cp "$ROOT/experiments/fabric_reference/$file" "$WORK/"
done
python "$WORK/validator_vectors.py" "$INPUT" "$WORK"
sha256sum "$WORK"/*.v "$WORK"/*.py "$WORK/runner.sh" "$INPUT/counter.bin" "$INPUT/lfsr.bin" > "$WORK/input-sha256.txt"
iverilog -V > "$WORK/versions.txt" 2>&1
yosys -V >> "$WORK/versions.txt"
cd "$WORK"
sources=(wp_image_validator.v wp_validated_reload.v wp_reload_guard.v)
# Synthesizable sources must parse as Verilog-2005; only the TB uses SV conveniences.
iverilog -g2005 -s wp_validated_reload -o syntax.vvp "${sources[@]}"
iverilog -g2012 "${defines[@]}" -s validator_tb -o rtl.vvp "${sources[@]}" validator_tb.v
timeout 40s vvp rtl.vvp > rtl.log 2>&1
grep '^PASS: validated reload' rtl.log
PDK="${XDG_CACHE_HOME:-$HOME/.cache}/warp/pdk-2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell"
IV="${XDG_CACHE_HOME:-$HOME/.cache}/warp/iverilog-13"
# Use previously cached PDK/simulator, fail clearly rather than silently skipping GL.
cp "$PDK/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib" cells.lib
sha256sum cells.lib "$PDK"/verilog/*.v >> input-sha256.txt
timeout 90s yosys -Q -T -p "read_verilog ${sources[*]}; chparam -set SERIAL_CRC $serial wp_validated_reload; synth -top wp_validated_reload -flatten; check -assert; read_liberty -lib cells.lib; dfflibmap -liberty cells.lib; abc -liberty cells.lib; opt_clean; check -assert; tee -o area.json stat -json -liberty cells.lib; write_verilog -noattr -noexpr mapped.v" > synth.log 2>&1
"$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -g2012 "${defines[@]}" -DMAPPED_VALIDATOR -s validator_tb -o gl.vvp "$PDK/verilog/sg13cmos5l_udp.v" "$PDK/verilog/sg13cmos5l_stdcell.v" mapped.v validator_tb.v > gl-compile.log 2>&1
"$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -V >> versions.txt 2>&1
timeout 60s "$IV/usr/bin/vvp" gl.vvp > gl.log 2>&1
grep '^PASS: validated reload' gl.log
python - <<'PY'
import json
from pathlib import Path
stats = json.loads(Path("area.json").read_text())
module = stats["modules"]["\\wp_validated_reload"]
cells = module["num_cells_by_type"]
assert all(name.startswith("sg13cmos5l_") or name == "$scopeinfo" for name in cells), cells
report = {"module": "wp_validated_reload", "cells": sum(count for name, count in cells.items() if name != "$scopeinfo"),
          "area_um2": module["area"], "scope": "validator plus guard, no fabric/host/pad muxes/physical routing"}
Path("summary.json").write_text(json.dumps(report, indent=2)+"\n")
print(json.dumps(report))
PY
