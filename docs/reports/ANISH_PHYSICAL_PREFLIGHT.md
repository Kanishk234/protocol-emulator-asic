# Physical integration checkpoint — 2026-09-28

Physical fit and useful protocol capacity are now the priority over further
isolated loader savings. Neither an eFPGA advantage over CPU/PIO nor a
complete tapeout implementation has been demonstrated.

## Transferable upstream evidence

Read-only review of `origin/main` at `e9da6b8`,
`docs/reports/R4_FLOORPLAN.md`, finds that TRIPWIRE R4 run 5
([36363295528](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36363295528))
reports zero detailed-routing violations, matching LVS, no antenna
violations, typical timing met and gate-level tests passing. Placement
utilization is 47.6%, with 54.9% utilization after the flow. The denser
58.9% placement case did not route. These are results for that particular
design, not a general utilization ceiling for WARP.

Important qualifications: slow-corner setup still misses by 6.01 ns on
437 paths; the report says precheck was still running when written.
Magic DRC includes the SRAM macro baseline. This review did not rerun or
independently verify the CI artifacts, and does not call all signoff green.
No held-out protocol implementation was read or profiled.

The older eFPGA tile report at `origin/efpga` `b45a1d8` concerns the tiny
library's LUT4x8_ha tile, not this branch's larger LUT4AB reference tile.
Its reported DRC-clean tile and estimated 96-LUT chip capacity do not
establish stitched-fabric timing, shell fit or a complete chip. Do not
transfer either tile's area to the other.

## Local flat-tile diagnostic

`scripts/fabric_tile_preflight.sh` snapshots the complete generated tile
dependencies and runs generic flat synthesis plus a separate Yosys check
on the stock and reload-held reference LUT4AB tile. Configuration remains
dynamic; the script does not define EMULATION or constrain a bitstream.

Run `warp-tile-preflight.hbGIhisV` records:

| Variant | Check problems | Logic-loop warnings |
|---|---:|---:|
| Stock | 184 | 184 |
| Reload-held | 189 | 189 |

The gate is **BLOCKED**, and the runner deliberately returns a nonzero
status. These counts describe structural feedback in the programmable
graph, not 184/189 independently proven runtime oscillations. Adding a
hold control does not erase feedback while the hold is released. Existing
two-image behavioral passes do not resolve this generic synthesis issue.

No mapped tile area, placement, routing, timing or new gate-level result is
claimed. The first cost attempt (`warp-tile-cost.CZf5CUtE`) caught a missing
MUX8LUT source dependency; the corrected attempt (`warp-tile-cost.NFDGHvxD`)
stopped at the strict loop check before CMOS5L mapping. Both are retained.

Local tools are available through the existing LibreLane AppImage:
OpenROAD revision `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`, OpenSTA 2.7.0.
This is tool availability, not a validated CMOS5L physical environment.
The cached project PDK subset contains mapping libraries; the complete
CMOS5L physical deck has not been established for this new experiment.

## Next experiment and acceptance

1. Inspect the pinned FABulous tile hardening method for explicit mux
   boundaries and configuration-dependent feedback handling. Separate
   legitimate programmable arcs from undriven/multiple-driver errors;
   avoid blanket suppression of synthesis or timing checks.
2. Select one small, reproducible fabric with dynamic configuration storage,
   its required edge cells and measured reload isolation. Verify loading
   and running a compiled circuit on the mapped implementation.
3. Establish the complete CMOS5L physical deck, Metal4 signal limit and
   real clock/reset/hold distribution. Report per-layer overflow, detailed
   routing, area growth, DRC/LVS status and every timing corner separately.
4. Only then scale useful design-set protocols against an explicit total
   area budget and compare CPU/PIO alternatives with matching semantics.

No phase box is closed. The host contract, broader reload isolation and
organizer/CI gates remain open. Reproduce the diagnostic with the supported
June OSS CAD Suite and activated `.venv-fabric`:

```bash
bash scripts/fabric_tile_preflight.sh build/fabric-reference-warp-reference.OBUfXfus
```
