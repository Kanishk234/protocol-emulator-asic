# Tiny FABulous fabric stitched on IHP CMOS5L (phase 1)

**Date:** 2026-09-26 · **Local runs** (WSL, Nix LibreLane 3.0.0 + FABulous plugin; PDK 2bbec75) · **Status:** measurement, not a claim.
**Reproduce:** `spikes/tile_cmos5l/run.sh <TILE>` for each tile type, then `spikes/fabric_tiny/run.sh` (or `run.sh --tiles` for both). Tile library: `mole99/fabulous-tiles` 7999e5a + `spikes/tile_cmos5l/cmos5l.patch` (D-010).

## Fabric
`arch/warp_tiny/fabric.csv` (was `spikes/fabric_tiny/warp_tiny.csv`), 3 × 4 FABulous tiles, **16 LUT4+FF**:
```
NW_term  N_term     NE_term
W_IO4    LUT4x8_ha  E_IO4
W_IO4    LUT4x8_ha  E_IO4
SW_term  S_IO2      SE_term      <- SW_term holds the global (clock) buffers, fed through S_IO2
```
Frame-based latch configuration (32 frame bits per row, up to 20 frames per column).

## Tiles (each hardened on its own, signals Metal2–Metal4, Metal4-only power stripes)
| Tile | Size (µm) | Utilisation | Routing DRC | Antenna | Time |
|---|---|---|---|---|---|
| LUT4x8_ha | 219.84 × 185.22 | 94–97 % | 0 | 0 | 6.5 min |
| W_IO4 / E_IO4 | 68.64 × 185.22 | 76 % / 71 % | 0 | 0 | 2–3 min |
| N_term / S_IO2 | 219.84 × 56.70 | 33 % / 60 % | 0 | 0 | ~1 min |
| NW/NE/SW/SE_term | 68.64 × 56.70 | 24–68 % | 0 | 0 | ~1 min |

## Stitched fabric macro `warp_tiny`
| Check | Result |
|---|---|
| Size | **357.12 × 483.84 µm** (172,789 µm²) |
| KLayout DRC (PDK deck `ihp-sg13cmos5l.drc`, deep, `no_recommended`) | **0 violations** |
| Routing DRC (fabric-level nets) | 0 |
| LEF | 245 pins (OpenROAD `write_abstract_lef`) |
| FABulous outputs | `bitStreamSpec.bin/.csv`, `geometry.csv`, `template.pcf`, `warp_tiny.v` |
| Flow time | 8 min |
| LVS | not run (no CMOS5L LVS in the PDK yet) |
| STA | not run in this flow; comes with the chip-level integration |

For 16 LUT4s the edge and IO tiles are ~42 % of the macro; in the planned 4 × 3 fabric they are ~20 % (`capacity.md`).

## Tool problems found and how they are handled
1. **Magic is too old for the CMOS5L tech file** (BUGS #2): the PDK needs Magic ≥ 8.3.657, the LibreLane 3.0.0 Nix environment has 8.3.623; Magic then mis-reads via arrays and hangs. **Workaround:** skip every Magic step; KLayout writes the GDS (and runs the DRC that TT's precheck uses); OpenROAD's `write_abstract_lef` writes the LEF.
2. **OpenROAD's LEF confuses the FABulous fabric flow:** its unused `VIA … CUTSIZE` definitions are read as the tile size (the plugin takes any line containing `SIZE`). **Workaround:** drop VIA definitions that no pin or obstruction uses (none do).
3. **Step removal loses the tile flow's final "save views"** in some runs; our driver saves the views itself.

## Inside the Tiny Tapeout chip (CI run 36327510268, 2026-09-27)
The macro (power stripes re-gridded per D-017, placement boundary 189/4) inside `tt_um_warp` with the spike shell (D-018: FABulous bit-bang loader driving FrameData/FrameStrobe from pins, run control, parking), placed at (780.96, 113.40) with `src/config.json` per D-019:
- `gds` 32.5 min, **precheck 9/9 pass**, **`gl_test` pass** (shell tests on the hardened netlist).
- DRC (KLayout, Magic), LVS (fabric abstract), antenna, routing: all 0. Timing met at 50 MHz (setup +12.47 ns, hold +0.106 ns; shell paths). IR drop 0.38 mV.
- Three failed runs on the way, all placement/config (BUGS #9–#11).

## What this retires, and what it doesn't
- **Retired:** a FABulous fabric can be built on CMOS5L, within TT's Metal4 signal limit and power-grid rules, and submitted through TT's own template flow and precheck, with its configuration storage live (driven from pins by the loader).
- **Not yet:** a real bitstream loaded into this fabric on the gate-level netlist (needs the compile flow for our fabric, phase 2), fabric timing (phase 2), and the real-size 4 × 3 fabric with primitives (phases 2–3).
