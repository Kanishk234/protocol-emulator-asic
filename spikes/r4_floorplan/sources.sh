#!/usr/bin/env bash
# R4: assemble the branch's src/ into <dir> (used by apply_to_branch.sh and check_local.sh), so there
# is one list of what goes on the chip. Sources stay single-sourced on main:
#   spikes/r4_floorplan/overlay/src   top, host stub, fabric (generated), sequencer stub, config.json
#   src/                              trw_defs.vh and the pin unit (trw_pin_*.v)
#   spikes/r1_lane                    lane, ALU, latch slot array
#   spikes/r3_sram/overlay/src        trw_sram.v, the macro blackbox, pdn_cfg.tcl
#   spikes/r2_latch/overlay/src       pnr.sdc, signoff.sdc (the latch exception)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
DST="$1"
mkdir -p "$DST"
cp "$HERE"/overlay/src/* "$DST/"
cp "$ROOT"/src/trw_defs.vh "$ROOT"/src/trw_pin_{cfg,io,tx,rx,unit}.v "$DST/"
cp "$ROOT"/spikes/r1_lane/{trw_lane,trw_alu,trw_slots}.v "$DST/"
cp "$ROOT"/spikes/r3_sram/overlay/src/{trw_sram.v,RM_IHPSG13_1P_512x16_c2_bm_bist.v,pdn_cfg.tcl} "$DST/"
cp "$ROOT"/spikes/r2_latch/overlay/src/{pnr.sdc,signoff.sdc} "$DST/"
