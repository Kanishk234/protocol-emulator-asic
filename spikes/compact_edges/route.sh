#!/usr/bin/env bash
# Full shell experiment: retain decoder locality, then release regions for repair.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="${WARP_COMPACT_WORK:-$ROOT/build/arch_explore/compact_edges}"
NIX_ENV="${WARP_COMPACT_NIX_ENV:-$ROOT/build/tile_cmos5l/fabulous-tiles}"
source "$ROOT/.venv/bin/activate"
export PDK=ihp-sg13cmos5l
export PDK_ROOT="${PDK_ROOT:-$HOME/.cache/warp/pdk-full}"
export TILE_LIBRARY=tiny
warp_prepare_args=(--work "$WORK" --y "${WARP_COMPACT_Y:-15.12}" --local-decode --vertical-halo 3.78)
export WARP_COMPACT_CHIP_DIR="${WARP_COMPACT_CHIP_DIR:-chip_local_decode}"
export WARP_COMPACT_EARLY_RELEASE="${WARP_COMPACT_EARLY_RELEASE:-0}"
export WARP_COMPACT_MIN_LAYER="${WARP_COMPACT_MIN_LAYER:-Metal2}"
export WARP_COMPACT_DENSITY="${WARP_COMPACT_DENSITY:-95}"
export WARP_COMPACT_ROUTABILITY="${WARP_COMPACT_ROUTABILITY:-0}"
export WARP_COMPACT_PADDING="${WARP_COMPACT_PADDING:-0}"
export WARP_LOCALIZE_CRC_SPI="${WARP_LOCALIZE_CRC_SPI:-0}"
export WARP_LOCALIZE_CRC_SPI_GUIDE="${WARP_LOCALIZE_CRC_SPI_GUIDE:-0}"
export WARP_LOCALIZE_CRC_ONLY="${WARP_LOCALIZE_CRC_ONLY:-0}"
if [[ "${WARP_CFG_BRANCH_DIODES:-0}" == 1 && "${WARP_CFG_BRANCH_BUFFERS:-0}" != 1 ]]; then
    echo "WARP_CFG_BRANCH_DIODES requires WARP_CFG_BRANCH_BUFFERS=1" >&2
    exit 2
fi
if [[ "${WARP_COMPACT_MASK_STROBES:-0}" == 1 ]]; then
    warp_prepare_args+=(--mask-unused-strobes)
fi
if [[ "${WARP_COMPACT_SHARED_CRC:-0}" == 1 ]]; then
    warp_prepare_args+=(--shared-word-crc)
fi
case "$WARP_COMPACT_MIN_LAYER" in
    Metal1|Metal2) ;;
    *) echo "WARP_COMPACT_MIN_LAYER must be Metal1 or Metal2" >&2; exit 2 ;;
esac
"$ROOT/.venv/bin/python" "$ROOT/spikes/compact_edges/prepare_chip.py" \
    "${warp_prepare_args[@]}" --chip-dir "$WARP_COMPACT_CHIP_DIR"
export WARP_COMPACT_ROOT="$ROOT" WARP_COMPACT_WORK="$WORK"
read -r WARP_LOCALIZE_NORTH_HEIGHT WARP_LOCALIZE_SOUTH_HEIGHT < <(
    "$ROOT/.venv/bin/python" - <<'PY'
import json, os
from pathlib import Path
manifest = json.loads((Path(os.environ["WARP_COMPACT_WORK"]) / "manifest.json").read_text())
print(round(manifest["north_height_um"] * 1000), round(manifest["south_height_um"] * 1000))
PY
)
export WARP_LOCALIZE_NORTH_HEIGHT WARP_LOCALIZE_SOUTH_HEIGHT
export WARP_COMPACT_MAX_OVERFLOW="${WARP_COMPACT_MAX_OVERFLOW:-0}"
cd "$NIX_ENV"
warp_eda_runner=(nix develop --accept-flake-config --command bash)
if [[ -n "${WARP_COMPACT_EDA_BIN:-}" ]]; then
    test -x "$WARP_COMPACT_EDA_BIN/librelane"
    export PATH="$WARP_COMPACT_EDA_BIN:$PATH"
    warp_eda_runner=(bash)
fi
"${warp_eda_runner[@]}" -c '
    set -euo pipefail
    cd "$WARP_COMPACT_WORK/$WARP_COMPACT_CHIP_DIR"
    python3 - <<PY
import json, os
from pathlib import Path
path = Path("config.json")
config = json.loads(path.read_text())
config["RT_MIN_LAYER"] = os.environ["WARP_COMPACT_MIN_LAYER"]
density = float(os.environ["WARP_COMPACT_DENSITY"])
if not 0 < density <= 100:
    raise ValueError("WARP_COMPACT_DENSITY must be greater than zero and at most 100")
config["PL_TARGET_DENSITY_PCT"] = density
mode = os.environ["WARP_COMPACT_ROUTABILITY"]
if mode not in ("0", "1"):
    raise ValueError("WARP_COMPACT_ROUTABILITY must be 0 or 1")
config["PL_ROUTABILITY_DRIVEN"] = mode == "1"
padding = int(os.environ["WARP_COMPACT_PADDING"])
if padding < 0 or padding > 4 or padding % 2:
    raise ValueError("WARP_COMPACT_PADDING must be 0, 2 or 4 sites")
config["DPL_CELL_PADDING"] = padding
max_phi = os.environ.get("WARP_COMPACT_MAX_PHI")
if max_phi:
    config["PL_MAX_PHI_COEFFICIENT"] = float(max_phi)
# Preserve native coordinates/layers even if a diagnostic is stopped early.
config["DRT_SAVE_DRC_REPORT_ITERS"] = 1
config["DRT_SAVE_SNAPSHOTS"] = True
path.write_text(json.dumps(config, indent=2) + "\n")
PY
    librelane --pdk "$PDK" --pdk-root "$PDK_ROOT" --manual-pdk \
        --run-tag compact_local_pdn --to OpenROAD.GeneratePDN config.json \
        > compact_local_pdn.log 2>&1
    python3 - <<PY
import json, os
from pathlib import Path
work = Path.cwd()
state, = (work / "runs/compact_local_pdn").glob("*-openroad-generatepdn/state_out.json")
s = json.loads(state.read_text())
os.environ["WARP_LOCALIZE_INPUT"] = s["odb"]
os.environ["WARP_LOCALIZE_OUTPUT"] = str(work / "decoders_local.odb")
import subprocess
subprocess.run(["openroad", "-exit", os.environ["WARP_COMPACT_ROOT"] + "/spikes/compact_edges/localize_decoders.tcl"], check=True)
s["odb"] = os.environ["WARP_LOCALIZE_OUTPUT"]
(work / "decoders_local_state.json").write_text(json.dumps(s, indent=2) + "\n")
PY
    if [[ "$WARP_COMPACT_EARLY_RELEASE" == 1 ]]; then
        librelane --pdk "$PDK" --pdk-root "$PDK_ROOT" --manual-pdk \
            --run-tag compact_local_gpl --from Odb.RemovePDNObstructions \
            --with-initial-state decoders_local_state.json \
            --to OpenROAD.GlobalPlacement config.json > compact_local_gpl.log 2>&1
        python3 - <<PY
import json, os, subprocess
from pathlib import Path
work = Path.cwd()
state, = (work / "runs/compact_local_gpl").glob("*-openroad-globalplacement/state_out.json")
s = json.loads(state.read_text())
os.environ["WARP_LOCALIZE_INPUT"] = s["odb"]
os.environ["WARP_LOCALIZE_OUTPUT"] = str(work / "decoders_early_released.odb")
os.environ["WARP_LOCALIZE_RELEASE"] = "1"
subprocess.run(["openroad", "-exit", os.environ["WARP_COMPACT_ROOT"] + "/spikes/compact_edges/localize_decoders.tcl"], check=True)
s["odb"] = os.environ["WARP_LOCALIZE_OUTPUT"]
(work / "decoders_early_released_state.json").write_text(json.dumps(s, indent=2) + "\n")
PY
        warp_grt_start=Odb.WriteVerilogHeader
        warp_grt_state=decoders_early_released_state.json
    else
        warp_grt_start=Odb.RemovePDNObstructions
        warp_grt_state=decoders_local_state.json
    fi
    librelane --pdk "$PDK" --pdk-root "$PDK_ROOT" --manual-pdk \
        --run-tag compact_local_grt --from "$warp_grt_start" \
        --with-initial-state "$warp_grt_state" \
        --to OpenROAD.GlobalRouting config.json > compact_local_grt.log 2>&1
    python3 - <<PY
import json, os, subprocess
import re, sys
from pathlib import Path
work = Path.cwd()
state, = (work / "runs/compact_local_grt").glob("*-openroad-globalrouting/state_out.json")
s = json.loads(state.read_text())
log = (state.parent / "openroad-globalrouting.log").read_text()
reports = re.findall(r"Total\s+(\d+)\s+(\d+)\s+([\d.]+)%\s+(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", log)
if not reports:
    raise RuntimeError("No final GRT congestion table; refusing to advance")
overflow = int(reports[-1][-1])
limit = int(os.environ["WARP_COMPACT_MAX_OVERFLOW"])
print(f"Global routing overflow: {overflow}; detailed-route screen limit: {limit}", flush=True)
if overflow > limit:
    sys.exit(3)
os.environ["WARP_LOCALIZE_INPUT"] = s["odb"]
os.environ["WARP_LOCALIZE_OUTPUT"] = str(work / "decoders_released.odb")
os.environ["WARP_LOCALIZE_RELEASE"] = "1"
subprocess.run(["openroad", "-exit", os.environ["WARP_COMPACT_ROOT"] + "/spikes/compact_edges/localize_decoders.tcl"], check=True)
s["odb"] = os.environ["WARP_LOCALIZE_OUTPUT"]
(work / "decoders_released_state.json").write_text(json.dumps(s, indent=2) + "\n")
PY
    librelane --pdk "$PDK" --pdk-root "$PDK_ROOT" --manual-pdk \
        --run-tag compact_local_route --from OpenROAD.RepairDesignPostGRT \
        --with-initial-state decoders_released_state.json \
        --to KLayout.DRC config.json > compact_local_route.log 2>&1
'
