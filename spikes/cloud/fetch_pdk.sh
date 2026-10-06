#!/usr/bin/env bash
# Same source revision/install method as tt-gds-action@ihp-cmos5l.
set -euo pipefail
: "${PDK_ROOT:?Set PDK_ROOT to an isolated cloud directory}"
warp_pdk_rev=2bbec755dc67ca3db0261c3d6163e15735d66710
mkdir -p "$PDK_ROOT"
git -C "$PDK_ROOT" init -q
git -C "$PDK_ROOT" fetch -q --depth 1 https://github.com/IHP-GmbH/IHP-Open-PDK.git "$warp_pdk_rev"
git -C "$PDK_ROOT" checkout -q FETCH_HEAD
printf 'IHP-Open-PDK %s\n' "$warp_pdk_rev" > "$PDK_ROOT/ihp-sg13cmos5l/SOURCES"
