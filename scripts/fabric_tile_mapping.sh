#!/usr/bin/env bash
# Map a reference tile with dynamic configuration. Generic loops remain reported.
# A clean mapped check is a connectivity check, NOT proof of no physical loops.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "${1:-}" != --runner-snapshot ]; then
  mkdir -p "$ROOT/build"
  runner=$(mktemp "$ROOT/build/fabric-tile-mapping-runner.XXXXXXXX.sh")
  cp "${BASH_SOURCE[0]}" "$runner"
  exec bash "$runner" --runner-snapshot "$@"
fi
shift
INPUT=$(realpath "${1:?Usage: fabric_tile_mapping.sh build/fabric-reference-RUN}")
WORK=$(mktemp -d /tmp/warp-tile-mapping.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Tile mapping evidence: $OUT"' EXIT
cp "${BASH_SOURCE[0]}" "$WORK/runner.sh"
cp "$ROOT/patches/reference_reload_hold.py" "$WORK/"
cp "$ROOT/experiments/fabric_reference/cmos5l_latch_map.v" "$WORK/"
cp "$ROOT/experiments/fabric_reference/tile_storage_vectors.py" "$WORK/"
mkdir -p "$WORK/tools/fabric_audit"
cp "$ROOT/tools/fabric_audit/configmem.py" "$WORK/tools/fabric_audit/"
cp "$INPUT/reference/Tile/LUT4AB/LUT4AB_ConfigMem.csv" "$WORK/configmem.csv"
python "$WORK/reference_reload_hold.py" "$INPUT/reference/Test/build/fabric_files" "$WORK/held"
cp -a "$INPUT/reference/Test/build/fabric_files" "$WORK/base"
PDK="${XDG_CACHE_HOME:-$HOME/.cache}/warp/pdk-2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell"
cp "$PDK/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib" "$WORK/cells.lib"
sha256sum "$WORK"/*.v "$WORK"/*.py "$WORK/runner.sh" "$WORK/cells.lib" "$WORK/base"/*.v "$WORK/held"/*.v > "$WORK/input-sha256.txt"
sha256sum "$WORK/configmem.csv" "$WORK/tools/fabric_audit/configmem.py" "$PDK"/verilog/*.v >> "$WORK/input-sha256.txt"
yosys -V > "$WORK/versions.txt"
cd "$WORK"
for variant in base held; do
  timeout 120s yosys -Q -T -p "read_verilog $variant/LUT4AB.v $variant/LUT4AB_switch_matrix.v $variant/LUT4AB_ConfigMem.v $variant/LUT4c_frame_config_dffesr.v $variant/MUX8LUT_frame_config_mux.v $variant/models_pack.v; hierarchy -check -top LUT4AB; proc; tee -o $variant-hierarchy-check.log check; synth -top LUT4AB -flatten; tee -o $variant-generic-check.log check; write_json $variant-generic.json; read_liberty -lib cells.lib; dfflibmap -liberty cells.lib; techmap -map cmos5l_latch_map.v; abc -liberty cells.lib; opt_clean; tee -o $variant-mapped-check.log check -assert; tee -o $variant-area.json stat -json -liberty cells.lib; write_json $variant-net.json; write_verilog -noattr -noexpr $variant-net.v" > "$variant-synth.log" 2>&1
  # Expand Liberty functions in a separate diagnostic design. This exposes
  # feedback hidden when standard cells are black boxes to the check pass.
  timeout 60s yosys -Q -T -p "read_liberty -ignore_miss_func cells.lib; read_verilog $variant-net.v; hierarchy -check -top LUT4AB; flatten; proc; tee -o $variant-expanded-check.log check" > "$variant-expanded.log" 2>&1
done
python - <<'PY'
import json, re
from pathlib import Path
report = {'scope':'mapped reference tile; feedback/timing/physical gates remain open'}
for variant in ('base', 'held'):
    counts = {}
    for stage in ('hierarchy', 'generic', 'mapped', 'expanded'):
        log = Path(f'{variant}-{stage}-check.log').read_text()
        warnings = re.findall(r'^Warning: (.*)', log, re.M)
        problems = int(re.search(r'Found and reported (\d+) problems',log)[1])
        assert len(warnings) == problems
        # Reject every non-loop warning; retain every loop warning in evidence.
        assert all(w.startswith('found logic loop in module ') for w in warnings), warnings
        counts[stage] = problems
    area = json.loads(Path(f'{variant}-area.json').read_text())['design']
    cells = {k:v for k,v in area['num_cells_by_type'].items() if k != '$scopeinfo'}
    assert all(k.startswith('sg13cmos5l_') for k in cells), cells
    module = json.loads(Path(f'{variant}-net.json').read_text())['modules']['LUT4AB']
    bits = module['netnames']['ConfigBits']['bits']
    assert len(bits) == 616 and len(set(bits)) == 616 and all(isinstance(b,int) for b in bits)
    assert cells.get('sg13cmos5l_dlhq_1') == 616, cells
    report[variant] = {'check_problems_by_stage':counts, 'area_um2':area['area'], 'cells':sum(cells.values()), 'configuration_latches':616}
report['held_minus_base_um2'] = report['held']['area_um2']-report['base']['area_um2']
Path('summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
PY
python tile_storage_vectors.py configmem.csv held-net.json .
IV="${XDG_CACHE_HOME:-$HOME/.cache}/warp/iverilog-13"
"$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -V >> versions.txt 2>&1
"$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -g2012 -s tile_storage_tb -o storage.vvp "$PDK/verilog/sg13cmos5l_udp.v" "$PDK/verilog/sg13cmos5l_stdcell.v" held-net.v tile_storage_tb.v > storage-compile.log 2>&1
timeout 30s "$IV/usr/bin/vvp" storage.vvp > storage.log 2>&1
grep '^PASS: mapped held-tile configuration' storage.log
negative_status=0
timeout 30s "$IV/usr/bin/vvp" storage.vvp +wrong_expected > storage-negative.log 2>&1 || negative_status=$?
printf 'storage 0\nwrong-expected %s\n' "$negative_status" > exit-codes.txt
test "$negative_status" -eq 1
grep -q 'FAIL: tile configuration transparent capture' storage-negative.log
echo 'PASS: wrong-expected negative control; physical and timing gates remain open'
