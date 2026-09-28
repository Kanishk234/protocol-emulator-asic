#!/usr/bin/env bash
# Generic flat synthesis diagnostic; exit 2 means the physical-flow gate is blocked.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT=$(realpath "${1:?Usage: fabric_tile_preflight.sh build/fabric-reference-RUN}")
WORK=$(mktemp -d /tmp/warp-tile-preflight.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Tile preflight evidence: $OUT"' EXIT
cp "${BASH_SOURCE[0]}" "$WORK/runner.sh"
cp "$ROOT/patches/reference_reload_hold.py" "$WORK/"
python "$WORK/reference_reload_hold.py" "$INPUT/reference/Test/build/fabric_files" "$WORK/held"
cp -a "$INPUT/reference/Test/build/fabric_files" "$WORK/base"
sha256sum "$WORK/base"/*.v "$WORK/held"/*.v "$WORK/runner.sh" "$WORK/reference_reload_hold.py" > "$WORK/input-sha256.txt"
yosys -V > "$WORK/versions.txt"
cd "$WORK"
for variant in base held; do
  timeout 120s yosys -Q -T -p "read_verilog $variant/LUT4AB.v $variant/LUT4AB_switch_matrix.v $variant/LUT4AB_ConfigMem.v $variant/LUT4c_frame_config_dffesr.v $variant/MUX8LUT_frame_config_mux.v $variant/models_pack.v; synth -top LUT4AB -flatten; tee -o $variant-check.log check; write_json $variant-generic.json" > "$variant-synth.log" 2>&1
done
python - <<'PY'
import json, re
from pathlib import Path
report = {}
for variant in ('base', 'held'):
    log = Path(f'{variant}-check.log').read_text()
    count = re.findall(r'Found and reported (\d+) problems', log)
    assert len(count) == 1, log[-1000:]
    report[variant] = {'check_problems':int(count[0]), 'logic_loop_warnings':log.count('Warning: found logic loop')}
report['status'] = 'BLOCKED' if any(v['check_problems'] for v in report.values()) else 'CHECK_CLEAN'
Path('summary.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
raise SystemExit(2 if report['status'] == 'BLOCKED' else 0)
PY
