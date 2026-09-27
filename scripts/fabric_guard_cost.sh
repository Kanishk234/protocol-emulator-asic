#!/usr/bin/env bash
# Isolated CMOS5L mapping experiment; not full-chip area or timing signoff.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT=$(realpath "${1:?Usage: fabric_guard_cost.sh build/fabric-reference-RUN}")
WORK=$(mktemp -d /tmp/warp-guard-cost.XXXXXXXX)
OUT="$ROOT/build/$(basename "$WORK")"
mkdir -p "$OUT"
trap 'cp -a "$WORK"/. "$OUT"/; echo "Cost evidence: $OUT"' EXIT
REV=2bbec755dc67ca3db0261c3d6163e15735d66710
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/warp"
PDK="$CACHE/pdk-$REV/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell"
for file in lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib verilog/sg13cmos5l_stdcell.v verilog/sg13cmos5l_udp.v; do
  mkdir -p "$(dirname "$PDK/$file")"
  if [ ! -s "$PDK/$file" ]; then
    curl -fLsS "https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/$REV/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/$file" -o "$PDK/$file.tmp"
    mv "$PDK/$file.tmp" "$PDK/$file"
  fi
done
IV="$CACHE/iverilog-13"
if [ ! -x "$IV/usr/bin/iverilog" ]; then
  curl -fLsS https://github.com/TinyTapeout/iverilog/releases/download/v13.0/iverilog_13.0-1_amd64.deb -o "$WORK/iverilog13.deb"
  mkdir -p "$IV"
  dpkg-deb -x "$WORK/iverilog13.deb" "$IV"
fi
cp "$PDK/lib/sg13cmos5l_stdcell_typ_1p20V_25C.lib" "$WORK/cells.lib"
cp "$ROOT/experiments/fabric_reference/wp_reload_guard.v" "$ROOT/experiments/fabric_reference/guard_tb.v" "$ROOT/experiments/fabric_reference/hold_cell_tb.v" "$WORK/"
python "$ROOT/patches/reference_reload_hold.py" "$INPUT/reference/Test/build/fabric_files" "$WORK/held"
cp "$INPUT/reference/Test/build/fabric_files/LUT4c_frame_config_dffesr.v" "$WORK/base_cell.v"
cp "$INPUT/reference/Test/build/fabric_files/models_pack.v" "$WORK/models_pack.v"
cp "$WORK/held/LUT4c_frame_config_dffesr.v" "$WORK/hold_cell.v"
sha256sum "$WORK"/*.v "$WORK/cells.lib" "$PDK"/verilog/*.v > "$WORK/input-sha256.txt"
yosys -V > "$WORK/versions.txt"
"$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -V >> "$WORK/versions.txt" 2>&1
cd "$WORK"
for variant in guard base_cell hold_cell; do
  top=LUT4c_frame_config_dffesr
  source="$variant.v models_pack.v"
  if [ "$variant" = guard ]; then top=wp_reload_guard; source=wp_reload_guard.v; fi
  timeout 60s yosys -Q -T -p "read_verilog $source; synth -top $top -flatten; dfflibmap -liberty cells.lib; abc -liberty cells.lib; opt_clean; check; tee -o $variant-area.json stat -json -liberty cells.lib; write_verilog -noattr -noexpr $variant-net.v" > "$variant-synth.log" 2>&1
done
"$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -g2012 -s guard_tb -o guard-gl.vvp "$PDK/verilog/sg13cmos5l_udp.v" "$PDK/verilog/sg13cmos5l_stdcell.v" guard-net.v guard_tb.v > guard-gl-compile.log 2>&1
timeout 10s "$IV/usr/bin/vvp" guard-gl.vvp > guard-gl.log 2>&1
grep '^PASS: guard sequencing' guard-gl.log
"$IV/usr/bin/iverilog" -B "$IV/usr/lib/ivl" -g2012 -s hold_cell_tb -o hold-cell-gl.vvp "$PDK/verilog/sg13cmos5l_udp.v" "$PDK/verilog/sg13cmos5l_stdcell.v" hold_cell-net.v hold_cell_tb.v > hold-cell-gl-compile.log 2>&1
timeout 10s "$IV/usr/bin/vvp" hold-cell-gl.vvp > hold-cell-gl.log 2>&1
grep '^PASS: held/released primitive' hold-cell-gl.log
python - <<'PY'
import json
from pathlib import Path
areas = {}
for variant in ('guard', 'base_cell', 'hold_cell'):
    design = json.loads(Path(f'{variant}-area.json').read_text())['design']
    # Yosys hierarchy metadata is not a physical cell; reject all other unmapped types.
    cells = {name: count for name, count in design['num_cells_by_type'].items() if name != '$scopeinfo'}
    if any(not name.startswith('sg13cmos5l_') for name in cells):
        raise SystemExit(f'Unmapped/unexpected cells: {variant}: {cells}')
    areas[variant] = design['area']
    print(variant, sum(cells.values()), 'cells;', design['area'], 'um^2')
print('LUT/carry hold increment:', areas['hold_cell'] - areas['base_cell'], 'um^2 per isolated cell')
Path('area-summary.json').write_text(json.dumps(areas, indent=2) + '\n')
PY
