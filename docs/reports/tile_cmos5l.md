# One FABulous tile hardened on IHP CMOS5L

**Date:** 2026-09-25 · **Local run** (WSL, 16 cores), `build/tile_cmos5l/.../runs/RUN_2026-09-25_17-56-09` (git-ignored) · **Reproduce:** `spikes/tile_cmos5l/run.sh`
**Tools:** LibreLane 3.0.0 + `librelane_plugin_fabulous` (Nix, the tile library's own flake), PDK IHP-Open-PDK 2bbec75 (`ihp-sg13cmos5l`, TT's revision). Tile: `LUT4x8_ha` from `mole99/fabulous-tiles` 7999e5a ("tiny" library, 8 × LUT4 + FF with carry, frame-based latch config), patched for CMOS5L's metal stack (D-010).
**Status:** measurement, not a claim; no CI run. Numbers are LibreLane metrics after step 49 (IR-drop report).

## Setup
The upstream IHP (SG13G2) settings unchanged except for layers: die **219.84 × 185.22 µm**, target density **96 %**, signals up to TopMetal1, power grid Metal4 (vertical) + TopMetal1 (horizontal) at 50 µm pitch as in the PDK's own LibreLane config. CMOS5L has 5 metal layers (M1–M4, TopMetal1); SG13G2 has 7.

## Result
| Metric | Value |
|---|---|
| Die area | 40,718.8 µm² |
| Cell area (incl. fill) / utilisation | 38,033.5 µm² / **97.0 %** |
| **Area per LUT4 (all in: LUT, FF, config latches, switch matrix, routing)** | **~5,090 µm²** |
| Sequential cells (config latches + flops) | 574 cells, 17,850 µm² (44 % of the tile) |
| Combinational (muxes, LUT logic) | 1,029 cells, 15,499 µm² |
| Buffers / timing-repair buffers / antenna diodes | 1,103 / 1,110 / 931 µm² (171 diodes) |
| Detailed-routing violations by iteration | 3497, 2310, 2239, 941, 350, 129, 93, 73, 31, 17, 16, 16, **0** (iteration 12) |
| Antenna violations after routing | 0 nets, 0 pins |
| Routed wirelength | 141 mm (est. before routing: 88 mm) |

**It routes at the SG13G2 size and density despite the missing layers**, although the router needed 12 iterations and 1.6× its wirelength estimate: there is little slack.

## Not finished: Magic stream-out hangs
Step 50 (`Magic.StreamOut`) printed 4 errors reading the routed DEF (`DEF read, Line 67–70: No cut layer specified in VIARULE`, i.e. the 4 generated power-grid via rules) and then ran at 100 % CPU with an empty log for 9+ minutes. It was stopped by hand. So there is **no GDS, no DRC and no STA** from this run.
- The area, density and routing numbers above do not depend on it.
- For the fabric macro: use KLayout stream-out (`PRIMARY_GDSII_STREAMOUT_TOOL: klayout`, as Tiny FABulous's fabric config does) and find out whether Magic's CMOS5L tech file needs the TopMetal1 via rule. Logged as BUGS #2.

## What it means for capacity (updates `capacity_early.md`)
6x4 core: 902,417 µm². Edge tiles at the IHP sizes: N/S terminators 219.84 × 56.70 µm (12.5K µm²), E/W IO tiles 68.64 × 185.22 µm (12.7K µm²). Shell budget ~50K µm² at normal density.

| Fabric | LUT tiles | Edge tiles | + shell | Share of core | **LUT4s** |
|---|---|---|---|---|---|
| 4 wide × 3 high | 12 × 40.7K = 489K | 8 N/S + 6 E/W = 176K | ~715K | ~79 % | **96** |
| 5 × 3 | 611K | 10 N/S + 6 E/W = 201K | ~862K | ~95 % (too tight) | 120 |
| 4 × 4 | 651K | 8 N/S + 8 E/W = 202K | ~903K | ~100 % (does not fit) | 128 |

So a generic fabric at 6x4 holds about **96 LUT4s** with margin. That is ~1.5× the synthesis estimate (the tiles pack at 97 %, not 42 %), but still well under the ~215 logic cells of the scratch UART. D-008 stands.

## Next
1. Fix or bypass the stream-out (KLayout), then DRC (KLayout, the deck the TT precheck uses) and STA on the tile.
2. The die shape of the 6x4 tile (aspect ratio) decides which grid fits; read it from the template DEF.
3. Phase 1 profiling with hard counters/shift registers against a ~96-LUT budget.

## Update: the TT top level stops at Metal4
The CI hardening of the placeholder (run 36170807513, `resolved.json`) uses `RT_MAX_LAYER: Metal4`; TopMetal1 carries TT's power grid. This tile used TopMetal1 for signals, so it may clash when placed as a macro in the TT top level. **Next run: the same tile with signals on Metal2–Metal4 only** (one change). If it doesn't route at 219.84 × 185.22 µm, grow the tile until it does; that size is the real cost per LUT for our chip.

## Run 2: signals on Metal2–Metal4 only (TT-compatible)
`RUN_2026-09-25_18-39-05`, same tile, size and density; one hardware change: `RT_MAX_LAYER: Metal4` (D-010 revision).

| Metric | Run 1 (to TopMetal1) | **Run 2 (to Metal4)** |
|---|---|---|
| Die | 40,718.8 µm² | 40,718.8 µm² |
| Utilisation | 97.0 % | 94.5 % |
| Routing violations by iteration | 3497 … 0 (12 iterations) | 1790, 1006, 778, 30, 15, 15, **0** (6 iterations) |
| Routed wirelength (estimate) | 141 mm (88 mm) | 119 mm (89 mm) |
| Antenna violations / diodes inserted | 0 / 171 | 0 / 0 |

**The tile routes within TT's layer limit, at the same size, more easily than run 1.** The capacity result stands: ~5,090 µm² per LUT4, **~96 LUT4s** at 6x4 with margin.

Stream-out: `Magic.StreamOut` ran again and hung (BUGS #2), although the tile config lists it under `meta.substituting_steps`. `resolved.json` shows the substitutions, so `tiles.py` (which builds the flow with `Flow.factory.get(...)` and a config dict) does not apply them. Still no GDS, KLayout DRC or STA. Next: apply the step substitutions in our own driver (or run the remaining steps from this run with LibreLane directly).

## Run 3: complete (layout file + DRC clean)
`RUN_2026-09-25_20-04-53`: same hardware as run 2 (`RT_MAX_LAYER: Metal4`); flow fix only: our `tiles.py` now applies the tile's step removals (Magic stream-out/DRC/LEF/extraction, XOR, LVS), so KLayout does the stream-out. **5 min 35 s end to end, no hang.** Routing identical in kind to run 2 (0 violations).

| Check | Result |
|---|---|
| GDS | `50-klayout-streamout/LUT4x8_ha.klayout.gds` (KLayout) |
| KLayout DRC, PDK deck `ihp-sg13cmos5l.drc` (2bbec75), deep mode, `no_recommended` | **0 violations**, 328 rules run, 39 s |
| Routing / antenna | 0 / 0 |
| LVS | not run: the PDK has no CMOS5L LVS yet (`config.tcl`) |
| STA | not run: the tile flow has no STA step and a lone tile has no clock; timing comes with the stitched fabric |
| LEF | not written (was `Magic.WriteLEF`); needed for the fabric macro: next, OpenROAD `write_abstract_lef` or a fixed Magic |

**Conclusion:** a FABulous LUT4 tile builds on CMOS5L within TT's layer limit, DRC-clean, at ~5,090 µm² per LUT4. The 6x4 chip holds ~96 LUT4s with room for the shell.
