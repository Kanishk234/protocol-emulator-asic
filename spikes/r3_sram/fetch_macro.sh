#!/usr/bin/env bash
# R3: download the IHP RM_IHPSG13_1P_512x16_c2_bm_bist views into <dir> (default: the cache).
#
# Usage: spikes/r3_sram/fetch_macro.sh [dir]
#
# Source: IHP-Open-PDK at the revision tt-gds-action@ihp-cmos5l pins (= scripts/gl_local.sh).
# The cmos5l PDK has no SRAM of its own: ihp-sg13cmos5l/libs.ref/sg13cmos5l_sram is a symlink to
# ihp-sg13g2/libs.ref/sg13g2_sram, so these are the SG13G2 views (as found by the Loom entry).
# Byte counts are checked against the ones the Loom entry recorded for the same revision.
set -euo pipefail

PDK_REV="${PDK_REV:-2bbec755dc67ca3db0261c3d6163e15735d66710}"
NAME=RM_IHPSG13_1P_512x16_c2_bm_bist
DIR="${1:-${XDG_CACHE_HOME:-$HOME/.cache}/tripwire/macro-$PDK_REV/$NAME}"
BASE="https://raw.githubusercontent.com/IHP-GmbH/IHP-Open-PDK/$PDK_REV/ihp-sg13g2/libs.ref/sg13g2_sram"

mkdir -p "$DIR"
# path under sg13g2_sram | expected bytes
while read -r sub bytes; do
  f="$DIR/$(basename "$sub")"
  if [ ! -s "$f" ]; then
    curl -sfL -o "$f" "$BASE/$sub"
  fi
  got=$(stat -c %s "$f")
  if [ "$got" != "$bytes" ]; then
    echo "fetch_macro: $(basename "$sub") is $got bytes, expected $bytes" >&2
    exit 1
  fi
done <<EOF
gds/$NAME.gds 466654
lef/$NAME.lef 74001
cdl/$NAME.cdl 403966
lib/${NAME}_typ_1p20V_25C.lib 49142
lib/${NAME}_fast_1p32V_m55C.lib 49139
lib/${NAME}_slow_1p08V_125C.lib 49203
verilog/$NAME.v 7504
verilog/RM_IHPSG13_1P_core_behavioral_bm_bist.v 3951
EOF
echo "fetch_macro: $NAME views at $DIR (PDK $PDK_REV)"
