# R4 spike: a full-size TRIPWIRE floorplan at 6x4

**Question:** at what utilisation does a full-size TRIPWIRE route on the 6x4 tile? DECISIONS D-043; results in `docs/reports/R4_FLOORPLAN.md` and `docs/reports/AREA.md`.

It hardens on the branch **`spike/r4-floorplan`**, which is never merged (as R2/R3, D-031). `main` keeps only this folder.

## What is on the chip
- 3 lanes (R1 lane, latch slots and K, no slot read-back, register debug read) with routine sequencer stubs on the SRAM rotation.
- 6 lean pin units with their configuration latch blocks, producers and pad owners.
- The fabric: 13 producers, 13 consumer ports, legal-source multiplexers generated from the spec (`gen_fabric.py` → `overlay/src/r4_fabric.v`).
- The IHP 512x16 SRAM macro (R3 recipe) with the 4-way rotation.
- A host SPI stub (§9 format). The address map is in `overlay/src/tt_um_tripwire.v`.

Yosys (cmos5l typ): 498.8K µm² of standard cells + the 45.3K macro, ~71 % of the core at the flow's placement.

## Files
| Path | What |
|---|---|
| `overlay/` | Branch files: `info.yaml` (6x4), `src/tt_um_tripwire.v` and the `r4_*` stubs, `src/config.json`, `test/Makefile`, `test/test.py` |
| `sources.sh` | Assembles the branch `src/` from single sources (see its header) |
| `gen_fabric.py` | Generates the fabric wiring from `tools/tripwire_spec.py`; `--check` in `apply_to_branch.sh` and `check_local.sh` |
| `check_local.sh` | Lint, the 5 pin-level tests on RTL, Yosys area, pre-layout STA, the tests on the Yosys gate-level netlist (TT Icarus 13). `R4_NO_GL=1` skips the gate level |
| `apply_to_branch.sh` | Copies everything into the checkout and vendors the macro; refuses to run anywhere but `spike/r4-floorplan` |

## Steps

```
# on main, after committing spikes/r4_floorplan (and the spikes/r1_lane change):
spikes/r4_floorplan/check_local.sh               # expect: check_local: PASS
git checkout -b spike/r4-floorplan
spikes/r4_floorplan/apply_to_branch.sh
git add -A && git commit -m "spike: R4 full-size floorplan (6x4)"
git push -u origin spike/r4-floorplan            # starts gds on the branch (~up to 6 h); main is not affected
git checkout main
```

Then collect the `gds` run on the branch: `GDS_logs` (global routing `39-openroad-globalrouting`, detailed routing `44-openroad-detailedrouting`, `55-openroad-stapostpnr`, `runs/wokwi/final/metrics.json`) into `build/ci/r4/` (not committed), and record the numbers on `main`.
