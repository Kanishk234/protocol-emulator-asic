#!/usr/bin/env bash
# Re-harden the smaller boundary, then stitch the unchanged 5 x 3 logic grid.
# Requires the existing phase-aligned scratch library (D-037 exploration).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="${WARP_COMPACT_WORK:-$ROOT/build/arch_explore/compact_edges}"
SOURCE="${WARP_COMPACT_SOURCE:-$ROOT/build/arch_explore/fabric_5x3_phase_aligned/fabulous-tiles}"
NIX_ENV="${WARP_COMPACT_NIX_ENV:-$ROOT/build/tile_cmos5l/fabulous-tiles}"
source "$ROOT/.venv/bin/activate"
export PDK=ihp-sg13cmos5l
export PDK_ROOT="${PDK_ROOT:-$HOME/.cache/warp/pdk-full}"
export TILE_LIBRARY=tiny
"$ROOT/.venv/bin/python" "$ROOT/spikes/compact_edges/prepare.py" --source "$SOURCE" --work "$WORK" \
    --north-height "${WARP_COMPACT_NORTH_HEIGHT:-37.80}" \
    --south-height "${WARP_COMPACT_SOUTH_HEIGHT:-49.14}"
export WARP_COMPACT_WORK="$WORK"
export WARP_COMPACT_ROOT="$ROOT"
cd "$NIX_ENV"
# Serial parsing is required: FABulous writes a shared JSON file beside each
# primitive. Concurrent tile parsing can corrupt those files.
nix develop --accept-flake-config --command bash -c '
    set -euo pipefail
    for warp_tile in N_IO N_IO_C2 N_IO_C3 N_IO_C4 N_IO_C5 \
        S_IO2 S_IO2_C2 S_IO2_C3 S_IO2_C4 S_IO2_C5 \
        NW_term NE_term_wide SW_term SE_term_wide; do
        python3 "$WARP_COMPACT_WORK/run_tile.py" "$warp_tile" \
            > "$WARP_COMPACT_WORK/$warp_tile.log" 2>&1
    done
    cd "$WARP_COMPACT_WORK"
    librelane --pdk "$PDK" --pdk-root "$PDK_ROOT" --manual-pdk \
        config.yaml --save-views-to "$WARP_COMPACT_WORK/macro" \
        > "$WARP_COMPACT_WORK/fabric.log" 2>&1
    python3 "$WARP_COMPACT_ROOT/spikes/compact_edges/export_macro.py" --work "$WARP_COMPACT_WORK"
    python3 "$WARP_COMPACT_ROOT/spikes/compact_edges/prepare_chip.py" --work "$WARP_COMPACT_WORK"
'
