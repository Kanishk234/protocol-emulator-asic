# arch/warp_tiny: the 16-LUT phase 1 fabric (architecture version 0x0001)

The fabric currently hardened as the macro `warp_tiny` (D-018): 2 × `LUT4x8_ha` (16 LUT4+FF with carry chain) plus IO and edge tiles from `mole99/fabulous-tiles` 7999e5a. It is the stepping stone the shell and the compile flow are built against; G0/G1 (ARCHITECTURE §7) replace it.

| File | What |
|---|---|
| `fabric.csv` | FABulous fabric definition (tile grid + parameters). `TILES/` is the tile library's `tiles/tiny/`. Built by `spikes/fabric_tiny/run.sh`. |
| `pins.csv` | WARP pin name → IO BEL, the compile flow's pin constraints (ARCHITECTURE §7.2), and where each BEL reaches the chip pins in `src/tt_um_warp.v`. |

Generated from this definition by the fabric build, and published with the macro in `macro/warp_tiny/`: the RTL (`warp_tiny.v`), netlists, GDS/LEF, and the tool files the compile flow reads (`fabulous/.FABulous/pips*.txt`, `bel*.txt`, `bitStreamSpec.bin`). They are regenerated, never hand-edited.
