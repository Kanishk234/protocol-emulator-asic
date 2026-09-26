#!/usr/bin/env bash
# Static, white-box SCC diagnostic at a completed frame boundary.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT=$(realpath "${1:?Usage: fabric_snapshot.sh build/fabric-reference-RUN [frames_written]}")
COUNT=${2:-33}
WORK=$(mktemp -d /tmp/warp-snapshot.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Snapshot evidence: $OUT"' EXIT
python "$ROOT/experiments/fabric_reference/frame_snapshot.py" "$INPUT/counter.bin" "$INPUT/lfsr.bin" "$COUNT" "$WORK/config.vh" \
  --validate-final-header "$INPUT/reference/user_design/sequential_16bit_en.vh" | tee "$WORK/snapshot.txt"
yosys -V > "$WORK/version.txt"
sha256sum "$INPUT/counter.bin" "$INPUT/lfsr.bin" "$ROOT/experiments/fabric_reference/frame_snapshot.py" > "$WORK/input-sha256.txt"
for source in "$WORK/config.vh" "$INPUT"/reference/Test/build/fabric_files/*.v; do
  cat "$source"
  printf '\n'
done > "$WORK/snapshot.v"
cd "$WORK"
# Remove generated keep attributes only for this diagnostic. There is no
# change to generated RTL, compiler inputs, or the live loader simulation.
timeout -k 5s 240s yosys -Q -T -p 'read_verilog -sv -D EMULATION snapshot.v; hierarchy -top eFPGA; proc; setattr -unset keep; flatten; opt; scc -select; select -write scc-cells.txt; write_json snapshot.json' > yosys.log 2>&1
grep -E 'Found .*SCC|logic loop' yosys.log
