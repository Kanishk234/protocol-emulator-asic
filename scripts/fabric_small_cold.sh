#!/usr/bin/env bash
# Public-port cold loading of the cached small grid; no reload/silicon claim.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT=$(realpath "${1:?Usage: fabric_small_cold.sh build/warp-small-compile.RUN}")
WORK=$(mktemp -d /tmp/warp-small-cold.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Cold-load evidence: $OUT"' EXIT
python -c 'import sys; assert sys.prefix != sys.base_prefix, "activate project venv"'
cp "${BASH_SOURCE[0]}" "$WORK/runner.sh"
cp "$ROOT/experiments/fabric_reference/small_cold_tb.v" "$WORK/"
cp -a "$INPUT/project/Test/build/fabric_files" "$WORK/rtl"
cp "$INPUT/counter.bin" "$WORK/"
# Optional mixed-level validation: both LUT tiles use the cached cell netlist;
# loader, I/O and perimeter remain RTL. Reject mismatched source provenance.
EXTRA=()
if test -n "${2:-}"; then
  MAPPING=$(realpath "$2")
  for file in LUT4AB.v LUT4AB_switch_matrix.v LUT4AB_ConfigMem.v LUT4c_frame_config_dffesr.v MUX8LUT_frame_config_mux.v models_pack.v; do
    cmp "$WORK/rtl/$file" "$MAPPING/base/$file"
  done
  cp "$MAPPING/base-net.v" "$WORK/rtl/LUT4AB.v"
  PDK="${XDG_CACHE_HOME:-$HOME/.cache}/warp/pdk-2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell"
  cp "$PDK/verilog/sg13cmos5l_udp.v" "$PDK/verilog/sg13cmos5l_stdcell.v" "$WORK/"
  EXTRA=("$WORK/sg13cmos5l_udp.v" "$WORK/sg13cmos5l_stdcell.v")
  echo 'Mixed-level: stock LUT tiles mapped, surrounding fabric and loader RTL; no SDF' > "$WORK/scope.txt"
else
  echo 'All RTL cold-load test' > "$WORK/scope.txt"
fi
python - "$WORK" <<'PY'
from pathlib import Path
import hashlib, json, sys
w=Path(sys.argv[1]); data=(w/'counter.bin').read_bytes()
assert len(data)==504
words=[int.from_bytes(data[i:i+4],'big') for i in range(0,len(data),4)]
assert words[:5]==[0x00aaff01,1,0,0,0xfab0fab1]
assert words[-1]==0x00100000
addresses=[words[5+3*i] for i in range(40)]
assert addresses==[(col<<27)|(1<<frame) for col in range(2) for frame in range(20)]
(w/'counter.hex').write_text(''.join(f'{v:08x}\n' for v in words))
(w/'image-audit.json').write_text(json.dumps(dict(bytes=len(data),words=len(words),frames=len(addresses),rows=2,columns=2,sha256=hashlib.sha256(data).hexdigest()),indent=2)+'\n')
PY
IV="${XDG_CACHE_HOME:-$HOME/.cache}/warp/iverilog-13"
IVERILOG=("$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl")
VVP="$IV/usr/bin/vvp"
"${IVERILOG[@]}" -V > "$WORK/versions.txt" 2>&1
find "$WORK/rtl" -type f -name '*.v' -print0 | sort -z | xargs -0 sha256sum > "$WORK/input-sha256.txt"
sha256sum "$WORK/runner.sh" "$WORK/small_cold_tb.v" "$WORK/counter.bin" >> "$WORK/input-sha256.txt"
if test "${#EXTRA[@]}" -gt 0; then sha256sum "${EXTRA[@]}" >> "$WORK/input-sha256.txt"; fi
"${IVERILOG[@]}" -g2012 -s small_cold_tb -o "$WORK/cold.vvp" "${EXTRA[@]}" "$WORK"/rtl/*.v "$WORK/small_cold_tb.v" > "$WORK/compile.log" 2>&1
timeout -k 5s 60s "$VVP" "$WORK/cold.vvp" +image="$WORK/counter.hex" > "$WORK/positive.log" 2>&1
grep -q '^PASS: small cold-load counter 1074 pin checks' "$WORK/positive.log"
if timeout -k 5s 60s "$VVP" "$WORK/cold.vvp" +image="$WORK/counter.hex" +wrong_expected > "$WORK/negative.log" 2>&1; then
  echo 'Negative control unexpectedly passed' >&2; exit 1
else
  result=$?; test "$result" -eq 1
fi
grep -q 'FAIL: pin oracle check=0' "$WORK/negative.log"
echo 'PASS: small fabric cold loading, pin oracle and negative control'
