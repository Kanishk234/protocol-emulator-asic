# arch/warp_g0: the G0 fabric (architecture version 0x0002)

The plain baseline fabric (ARCHITECTURE §7.1, D-008): 4 × 3 `LUT4x8_ha` tiles = **96 LUT4+FF** with carry chain, from `mole99/fabulous-tiles` 7999e5a, framed by IO tiles on all four sides (D-024). G1 adds the timer and shift-register primitives on the same frame; every specialization is compared against G0 at equal area (D-004).

| File | What |
|---|---|
| `fabric.csv` | FABulous fabric definition: `NW_term, N_IO ×4, NE_term` / `W_IO4, LUT4x8_ha ×4, E_IO4` ×3 / `SW_term, S_IO2 ×4, SE_term`. `TILES/` is the tile library's `tiles/tiny/`. Built by `FABRIC=warp_g0 spikes/fabric_tiny/run.sh`. |
| `pins.csv` | Pin name → IO cell (BEL), the compile flow's pin constraints: the 19 user pins, clock/reset and the host channel (`h_*`, D-024). `src/tt_um_warp.v` wires the same cells. |
| `arch.yaml` | Architecture identity: `arch_version` (checked against the shell's ARCH_VERSION and the host), macro path, configuration rows/columns. |

Generated from this definition by the fabric build, published in `macro/warp_g0/` and never hand-edited: GDS/LEF (1016.64 × 669.06 µm), netlists, fabric and tile RTL, and the compile flow's tool files (`fabulous/`).

`arch/CURRENT` names the architecture the chip is built with; the test harness, scripts and compile flow follow it.
