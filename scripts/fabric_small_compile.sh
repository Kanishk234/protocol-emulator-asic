#!/usr/bin/env bash
# Small reference-derived grid experiment. Compilation is not physical signoff.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT=$(realpath "${1:?Usage: fabric_small_compile.sh build/fabric-reference-RUN}")
WORK=$(mktemp -d /tmp/warp-small-compile.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Small fabric evidence: $OUT"' EXIT
cp "${BASH_SOURCE[0]}" "$WORK/runner.sh"
python -c 'import sys; from importlib.metadata import version; assert sys.prefix != sys.base_prefix; assert version("FABulous-FPGA") == "2.2.0"'
yosys -V | grep -q '0.66+179.*e74db6dea'
{ yosys -V; nextpnr-generic --version; python --version; } > "$WORK/versions.txt" 2>&1
FABulous create-project "$WORK/project" > "$WORK/create.log" 2>&1
cp "$INPUT/reference/fabric.csv" "$WORK/original-fabric.csv"
python - "$WORK" <<'PY'
from pathlib import Path
import sys
work=Path(sys.argv[1])
source=(work/'original-fabric.csv').read_text()
assert source.count('FabricBegin')==1 and source.count('FabricEnd')==1
suffix=source.split('FabricEnd',1)[1]
grid='FabricBegin\nNULL,N_term_single\nW_IO,LUT4AB\nW_IO,LUT4AB\nNULL,S_term_single\nFabricEnd'
(work/'project/fabric.csv').write_text(grid+suffix)
PY
cp "$ROOT/experiments/fabric_reference/small_counter.v" "$WORK/project/user_design/"
printf 'load_fabric\nrun_FABulous_fabric\ngen_user_design_wrapper user_design/small_counter.v user_design/top_wrapper.v\nexit\n' > "$WORK/project/small.fab"
sha256sum "$WORK/runner.sh" "$WORK/original-fabric.csv" "$WORK/project/fabric.csv" "$WORK/project/user_design/small_counter.v" > "$WORK/input-sha256.txt"
timeout 180s FABulous -p "$WORK/project" script --type fabulous "$WORK/project/small.fab" > "$WORK/compile.log" 2>&1
python - "$WORK/project/user_design/top_wrapper.v" <<'PY'
from pathlib import Path
import sys
path=Path(sys.argv[1])
text=path.read_text()
# FABulous 2.2 only auto-connects its specially named default demo.
for port, wire in [('io_in','O'), ('io_out','I'), ('io_oeb','T')]:
    old=f'.{port}()'
    assert text.count(old)==1, (port, text)
    text=text.replace(old, f'.{port}(IO_1_bidirectional_frame_config_pass_{wire})')
path.write_text(text)
PY
printf 'load_fabric\ncompile_design user_design/small_counter.v\nexit\n' > "$WORK/project/compile.fab"
timeout 180s FABulous -p "$WORK/project" script --type fabulous "$WORK/project/compile.fab" >> "$WORK/compile.log" 2>&1
python - "$WORK/project/user_design" <<'PY'
from pathlib import Path
import json, sys
path=Path(sys.argv[1])
features=[line for line in (path/'small_counter.fasm').read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')]
cells=json.loads((path/'small_counter.json').read_text())['modules']['top_wrapper']['cells']
logic=[c for c in cells.values() if 'LUT' in c['type']]
assert features and len(logic)>=2, 'Empty or optimized-away counter'
assert 'Routing 0 arcs.' not in (path/'small_counter_npnr_log.txt').read_text()
data=(path/'small_counter.bin').read_bytes()
assert len(data)==20+2*20*4*(1+2)+4, len(data)
(path.parent.parent/'compile-summary.json').write_text(json.dumps({'logic_cells':len(logic),'fasm_features':len(features),'image_bytes':len(data),'scope':'compilation only; not live or mapped execution'},indent=2)+'\n')
PY
test -s "$WORK/project/user_design/small_counter.bin"
cp "$WORK/project/user_design/small_counter.bin" "$WORK/counter.bin"
sha256sum "$WORK/counter.bin" > "$WORK/bitstream-sha256.txt"
sha256sum "$WORK/project/user_design/top_wrapper.v" >> "$WORK/input-sha256.txt"
echo 'PASS: small counter compilation; loading, mapped execution and physical fit remain unverified'
