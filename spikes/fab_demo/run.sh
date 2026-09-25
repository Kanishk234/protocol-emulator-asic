#!/usr/bin/env bash
# Phase 0 FABulous reference demo: one stock fabric, two different user designs.
#
#   1. stock sequential_16bit_en  -> bitstream A, fabric vs its own reference   (must match)
#   2. lfsr_down (this dir)        -> bitstream B, fabric vs its own reference   (must match)
#   3. bitstream B vs the sequential_16bit_en reference                           (must MISMATCH)
#
# Step 3 shows the fabric really runs a different design from B and that the
# comparison can tell the two apart.
#
# Usage: spikes/fab_demo/run.sh     (work dir: build/fab_demo, git-ignored)
# Needs: .venv with FABulous (requirements-dev.txt), OSS CAD Suite 2026-06-29 (docs/VERSIONS.md).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HERE="$ROOT/spikes/fab_demo"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
if [ -d "$HOME/oss-cad-suite/bin" ]; then export PATH="$PATH:$HOME/oss-cad-suite/bin"; fi

PROJ="$ROOT/build/fab_demo"
LOGS="$ROOT/build/fab_demo_logs"
rm -rf "$PROJ" "$LOGS"
mkdir -p "$ROOT/build" "$LOGS"
FABulous create-project "$PROJ" >/dev/null

# Second design and its testbench (the stock one with the design name swapped).
cp "$HERE/lfsr_down.v" "$PROJ/user_design/"
sed 's/sequential_16bit_en/lfsr_down/g' "$PROJ/Test/sequential_16bit_en_tb.v" > "$PROJ/Test/lfsr_down_tb.v"

cat > "$PROJ/warp_demo_a.tcl" <<'EOF'
load_fabric
run_fab
gen_user_design_wrapper user_design/sequential_16bit_en.v user_design/top_wrapper.v
compile_design ./user_design/sequential_16bit_en.v
run_simulation fst ./user_design/sequential_16bit_en.bin
exit
EOF
cat > "$PROJ/warp_demo_b.tcl" <<'EOF'
load_fabric
compile_design ./user_design/lfsr_down.v
run_simulation fst ./user_design/lfsr_down.bin
exit
EOF

echo "=== step 1: fabric + sequential_16bit_en"
FABulous -p "$PROJ" script "$PROJ/warp_demo_a.tcl" > "$LOGS/flow_a.log" 2>&1 || { tail -30 "$LOGS/flow_a.log"; exit 1; }

# FABulous 2.2's gen_user_design_wrapper auto-connects io_in/io_out/io_oeb only for its
# stock demo design; for any other design it leaves them open and Yosys removes the
# whole design. Reuse the stock wrapper and swap the instantiated module instead.
sed -i 's/^sequential_16bit_en user_design_i/lfsr_down user_design_i/' "$PROJ/user_design/top_wrapper.v"
grep -q '^lfsr_down user_design_i (.clk(clk), .io_in(IO' "$PROJ/user_design/top_wrapper.v"

echo "=== step 2: same fabric + lfsr_down"
FABulous -p "$PROJ" script "$PROJ/warp_demo_b.tcl" > "$LOGS/flow_b.log" 2>&1 || { tail -30 "$LOGS/flow_b.log"; exit 1; }
cat "$LOGS/flow_a.log" "$LOGS/flow_b.log" > "$LOGS/flow.log"
for d in sequential_16bit_en lfsr_down; do
  grep -a -m1 "FABULOUS_LC:" "$PROJ/user_design/${d}_npnr_log.txt" | sed "s/^/$d: /" || true
done
for d in sequential_16bit_en lfsr_down; do
  grep -a -m1 "Max frequency for clock" "$PROJ/user_design/${d}_npnr_log.txt" | sed "s/^/$d: /" || true
done
n_ok=$(grep -a -c '^fabric(I_top)' "$LOGS/flow.log")
echo "compared cycles in steps 1+2: $n_ok (each step \$fatal's on any mismatch)"

echo "=== step 3: bitstream B against the sequential_16bit_en reference (expect mismatch)"
T="$PROJ/Test"
mkdir -p "$T/build/fabric_files"
find "$PROJ/Tile" "$PROJ/Fabric" -name '*.v' -type f -exec cp {} "$T/build/fabric_files/" \;
python3 "$T/makehex.py" "$PROJ/user_design/lfsr_down.bin" 16384 "$T/build/cross.hex"
iverilog -g2012 -s sequential_16bit_en_tb -o "$T/build/cross.vvp" \
  "$T"/build/fabric_files/* "$PROJ/user_design/sequential_16bit_en.v" "$T/sequential_16bit_en_tb.v"
if vvp "$T/build/cross.vvp" +bitstream_hex="$T/build/cross.hex" > "$LOGS/cross.log" 2>&1; then
  echo "FAIL: bitstream B matched design A's reference" >&2
  exit 1
fi
grep -q FATAL "$LOGS/cross.log" || { echo "FAIL: cross run did not report a mismatch" >&2; tail "$LOGS/cross.log"; exit 1; }
grep -a -m2 '^fabric(I_top)' "$LOGS/cross.log"
echo "ok: mismatch detected as expected"

echo; echo "fab_demo: PASS"
