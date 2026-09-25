#!/usr/bin/env bash
# Phase 0/1 spike: harden one FABulous LUT4x8_ha tile (8 x LUT4+FF, "tiny" tile library) on IHP CMOS5L
# with LibreLane's FABulousTile flow, to measure real area, density and routing per LUT.
#
# Usage: spikes/tile_cmos5l/run.sh [TILE]        (default TILE=LUT4x8_ha; work dir build/tile_cmos5l)
# Needs: Nix with the FOSSi cache (docs/VERSIONS.md), and the CMOS5L PDK at TT's revision in $PDK_ROOT
#        (default ~/.cache/warp/pdk-full; fetch it like tt-gds-action's install_sg13cmos5l.sh).
#
# Upstream: mole99/fabulous-tiles at 7999e5a (the Tiny FABulous submodule), used unedited except for
# cmos5l.patch (DECISIONS D-010): CMOS5L has only M1-M4 + TopMetal1.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HERE="$ROOT/spikes/tile_cmos5l"
TILE="${1:-LUT4x8_ha}"
TILES_REV=7999e5a
W="$ROOT/build/tile_cmos5l"
export PDK=ihp-sg13cmos5l
export PDK_ROOT="${PDK_ROOT:-$HOME/.cache/warp/pdk-full}"
export TILE_LIBRARY=tiny

test -f "$PDK_ROOT/ihp-sg13cmos5l/libs.tech/librelane/config.tcl" || { echo "error: no CMOS5L PDK in $PDK_ROOT" >&2; exit 1; }
# shellcheck disable=SC1091
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh

if [ ! -d "$W/fabulous-tiles/.git" ]; then
  mkdir -p "$W"
  git clone -q https://github.com/mole99/fabulous-tiles "$W/fabulous-tiles"
  git -C "$W/fabulous-tiles" checkout -q "$TILES_REV"
  git -C "$W/fabulous-tiles" apply "$HERE/cmos5l.patch"
fi

cd "$W/fabulous-tiles"
nix develop --accept-flake-config --command bash -c "python3 tiles.py $TILE" 2>&1 | tee "$W/$TILE.log" | grep -E -i 'error|warn|Tile size|density|Done|Flow complete|failed' | tail -40
