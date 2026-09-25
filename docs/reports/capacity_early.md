# Early capacity estimate (phase 0, synthesis only)

**Date:** 2026-09-25 · **Status:** estimate from synthesis, not a hardening. Not a claim; it decides what to measure next.
**Inputs:** FABulous 2.2 stock `LUT4AB` tile (8 × LUT4+FF, frame-based latch config) generated in `build/fab_demo` by `spikes/fab_demo/run.sh`; Yosys 0.66+179 onto `sg13cmos5l_stdcell_typ_1p20V_25C.lib` (PDK 2bbec75): `synth -flatten; dfflibmap; abc; stat -liberty`.

## One LUT4AB tile (8 LUT4s)
| Part | Count | Area (µm²) |
|---|---|---|
| Configuration latches (`$_DLATCH_P_`, left unmapped by `dfflibmap`; costed as `sg13cmos5l_dlhq_1`, 30.84 µm²) | 616 | 19,000 |
| Everything else (332 `mux4`, 62 `mux2`, 8 flops, glue) | | 16,904 |
| **Tile cell area** | | **~35,900** |
| **Per LUT4** | 77 config bits | **~4,500** |

Configuration bits dominate (53 %). Cell area only: no fillers, no routing overhead, generic mux mapping (FABulous's custom-mux cells may do somewhat better).

## What fits in 6x4
6x4 core area: 902,417 µm² (TRIPWIRE phase 0 hardening, run 35824649426). Usable cell area depends on the placement density the fabric routes at:

| Placement density | Cell area | minus shell (~30K) and IO/terminator tiles (~20 %) | LUT4AB tiles | **LUT4s** |
|---|---|---|---|---|
| 42 % (TRIPWIRE latch spike R2 needed this) | 379K | ~279K | ~7.8 | **~60** |
| 55 % | 496K | ~373K | ~10.4 | **~80** |
| 60 % | 541K | ~409K | ~11.4 | **~90** |

Cross-check: Tiny FABulous fits 128 LUT4s in SKY130 8x4 (705K µm² die), and the IHP `mux4`/latch cells are larger than SKY130 HD's, so 60–100 LUT4s in our 902K µm² is consistent.

## What the design set needs
Scratch UART (8N1 TX + RX, 16-bit baud divisor register, 2-flop synchronizer), `build/capacity/uart_scratch.v`, not a deliverable, through `synth_fabulous`:
**215 LUTs (9 LUT2, 73 LUT3, 133 LUT4) + 87 flops, i.e. about 215 logic cells.**
The divisor register and the two 16-bit bit-timers are 48 of the 87 flops and most of the LUTs. (A first run gave 172 LUTs because the scratch file tied the divisor input to 0; fixed.)

## Reading
- A **generic** fabric at 6x4 holds roughly 60–90 LUT4s. **One UART needs about 2.5–3.5 times that.** SPI and the I2C controller/target are expected to be similar or larger (phase 1 measures them).
- The biggest consumer is exactly the kind of thing D-002 allows as a hard primitive: loadable counters/timers and shift registers. A hard 16-bit loadable down-counter is roughly 1–2K µm² of cells (16 flops at 49 µm² plus logic), versus roughly 16–32 fabric cells (~70–140K µm²).
- So specialization is **not an optimization at this size; it is what makes the design set fit at all.** This challenges D-005 (G0, a generic fabric, as the fallback): see D-008.

## Next measurements (to firm this up)
1. Harden one LUT4AB tile on cmos5l with the `FABulousTile` flow: real area including routing and density.
2. Profile the four design-set protocols (phase 1) on LUT4, with and without hard counters/shift registers.
3. Try smaller routing (fewer wires per channel) and fewer config bits per LUT; the stock tile is sized for a general-purpose FPGA.
