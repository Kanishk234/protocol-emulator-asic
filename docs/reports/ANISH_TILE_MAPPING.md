# Reference tile mapping and checker visibility — 2026-09-28

The complete reference LUT4AB tile can be mapped to CMOS5L cells while
retaining all 616 dynamic configuration latches. This removes the assumption
that generic loop warnings alone prevent producing a mapped tile. It does
**not** resolve programmable feedback, physical implementation or timing.

## What the upstream flow actually checks

Pinned source inspection, not a reproduction of the upstream flow:

- [FABulousTile flow](https://github.com/mole99/librelane_plugin_fabulous/blob/dcc038217472822330b33f61fadbc06e0c3cc96d/librelane_plugin_fabulous/fabulous_tile.py)
  removes pre-, mid- and post-PnR STA steps, plus resizer/repair steps.
- [LibreLane synthesis](https://github.com/librelane/librelane/blob/69b2067bd2b5eb89b84649b76e9edaa9e51e6735/librelane/scripts/pyosys/synthesize.py)
  writes `pre_synth_chk.rpt` during procedure lowering, before flattening.
  It also produces later check reports, including after mapping.
- [The synthesis metric parser](https://github.com/librelane/librelane/blob/69b2067bd2b5eb89b84649b76e9edaa9e51e6735/librelane/steps/pyosys.py)
  derives `synthesis__check_error__count` from `pre_synth_chk.rpt`. It does
  not implement a configuration-aware feedback proof.
- The [tile library models](https://github.com/mole99/fabulous-tiles/blob/7999e5a91dab77357fe9d401b6dfb0758f438bf1/models_pack.v)
  retain behavioral muxes/latches. Its
  [custom.v](https://github.com/mole99/fabulous-tiles/blob/7999e5a91dab77357fe9d401b6dfb0758f438bf1/custom.v)
  contains a commented-out loop-breaking black box, not an active fix.

The tile library's flake pins the plugin and LibreLane revisions above.
Reviewed source snapshots are retained under
`build/fabric-flow-review-20260928/`. Tile layout success must therefore be
reported separately from timing and configured-circuit correctness.

## Local experiment

Authoritative run: `warp-tile-mapping.sOBN3KHk`, June OSS CAD Suite
Yosys 0.66+179 `e74db6dea`, CMOS5L typical library from PDK `2bbec75`.
The runner compares the stock tile with the existing hash-checked LUT/carry
hold candidate. Both keep their real configuration memory and switch matrix.

| Check stage | Stock | Held |
|---|---:|---:|
| Hierarchy retained, procedures lowered | 0 | 0 |
| Flattened generic logic | 184 | 189 |
| Mapped cells read as library black boxes | 0 | 0 |
| Mapped cells expanded using Liberty functions | 143 | 173 |

All reported problems are logic-loop warnings; the runner rejects any
other warning. Expanding cell functions exposes feedback again, confirming
that the zero mapped count is a visibility change, not a repair. Counts
depend on graph representation and are not a count of independent runtime
oscillators or a measure of relative safety. The original strict preflight
continues to block its gate; no production flow check is disabled.

## Bounded mapping cost

| Variant | Standard cells | Configuration latches | Liberty area (µm²) |
|---|---:|---:|---:|
| Stock reference tile | 1,334 | 616 | 35,904.2166 |
| Held reference tile | 1,359 | 616 | 36,173.3904 |

The held-minus-stock difference is 269.1738 µm² (about 0.75%) in this
mapping. It includes optimizer changes across the tile, not just eight
copies of the previously isolated clamp measurement. Both netlists contain
616 distinct, variable `ConfigBits` nets and exactly 616 mapped latches;
there are no nonstandard-cell instances after excluding Yosys metadata.

These are pre-layout cell-area sums for the larger reference tile, including
its LUT logic, carry, muxes and configuration latches. They exclude placement
space, physical buffers, clock/hold distribution, edge tiles, loader, host,
power grid and routing. They are not interchangeable with the tiny-library
LUT4x8_ha tile footprint or a chip-capacity estimate.

## Dynamic storage gate-level check

The held mapped tile passes **2,620 frame-write vectors and 5,202 full-bank
comparisons** using TT Icarus 13 and the pinned PDK cell/UDP models.
An independent CSV-based configuration decoder drives actual `FrameData`
and `FrameStrobe` ports. It walks a changed bit over all 640 frame positions
against zero and one backgrounds, including the 24 padding positions.

Data changes while the latch gate is open check transparency. Changing
data after closure checks retention. Comparison starts only after all
20 frames have initialized the bank. A deliberately incorrect expected
bit fails at the first comparison (vector 19, expected exit 1).

`ConfigBits` is a read-only internal witness, not a chip-visible output.
No state is forced/deposited. ReloadHold remains asserted and other tile
inputs are zero. This verifies mapped configuration storage, not execution
of a user circuit, release safety, arbitrary-image isolation or full-fabric
gate-level behavior. Cell-model `ifnone` warnings remain; no SDF is used.

## Reproduce and next gate

Activate `.venv-fabric` and the supported June toolchain, then run:

```bash
bash scripts/fabric_tile_mapping.sh build/fabric-reference-warp-reference.OBUfXfus
```

The runner snapshots itself, sources, CSV, model hashes and tools; preserves
all four check stages, mapped netlists and positive/negative simulation
logs. The earlier exploratory runs `idRwIfGZ` and `4eMRrr9M` remain separate.

Next build a small stitched fabric with real loader and edge connections,
load a compiled design into mapped logic, and check public behavior through
hold release. Then establish configuration-aware timing constraints and
the complete CMOS5L physical environment before routing. The production
Tiny Tapeout top remains the placeholder; no GDS run, phase exit, or clock
target is claimed by this milestone.
