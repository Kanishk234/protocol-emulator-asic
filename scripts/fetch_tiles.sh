#!/usr/bin/env bash
# Fetch the FABulous tile library at the pinned commit (docs/VERSIONS.md) into build/third_party/.
# Unmodified: the compile flow needs its Yosys primitives/techmaps, the fabric simulation its tile
# and primitive RTL. (The CMOS5L patch in spikes/tile_cmos5l only changes the physical flow.)
# Prints the library path. Usage: LIB=$(scripts/fetch_tiles.sh)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REV=7999e5a
DIR="$ROOT/build/third_party/fabulous-tiles"

if [ ! -d "$DIR/.git" ]; then
  mkdir -p "$(dirname "$DIR")"
  git clone -q https://github.com/mole99/fabulous-tiles "$DIR" >&2
fi
if [ "$(git -C "$DIR" rev-parse --short=7 HEAD)" != "$REV" ]; then
  git -C "$DIR" fetch -q origin >&2 || true
  git -C "$DIR" checkout -q "$REV" >&2
fi
if [ -n "$(git -C "$DIR" status --porcelain)" ]; then
  echo "error: $DIR has local changes; upstream code is never edited in place" >&2
  exit 1
fi
echo "$DIR"
