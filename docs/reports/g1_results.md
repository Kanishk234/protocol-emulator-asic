# Design-set protocols on G1 (fabric + hard timer and shift register)

**Date:** 2026-09-27 · **Architecture:** `arch/warp_g1` (ARCH_VERSION 0x0003): G0's grid with one LUT-tile slot (X2Y2) replaced by the primitive tile `PRIM2T2S` (D-026) = **88 LUT4+FF** (LCs), **2 × `wp_timer` + 2 × `wp_shift`**, 36 IO cells; macro `macro/warp_g1`, 1016.64 × 669.06 µm (same size and ports as G0; stitched, KLayout DRC 0, antenna 0) · **Flow:** `python -m compile.protocols --arch arch/warp_g1`, designs with `PRIMS: 1` in `protocols/*/pins.yaml`, profiling parameters, slow corner `nom_slow_1p08V_125C`, nextpnr seed 1 · Local run, not CI. Not in the chip yet (the chip is G0).

## Result

| Protocol | Fits? | LCs (nextpnr) | LUTs (carry) | FFs | timers, shifts | IO cells | nextpnr Fmax, slow corner (see Timing) | G0, same sources (`PRIMS=0`) |
|---|---|---|---|---|---|---|---|---|
| UART (115200 baud) | **yes** | 29 (33 %) | 19 (0) | 19 | 2, 2 | 15 | 93.2 MHz | 124 LCs, no fit |
| SPI controller (mode 0, 1 MHz SCK) | **yes** | 47 (53 %) | 38 (5) | 25 | 1, 1 | 17 | 83.2 MHz | 86 LCs, fits |
| I2C controller (~100 kHz) | **yes** | 70 (80 %) | 70 (0) | 32 | 1, 1 | 15 | 58.0 MHz | 115 LCs, no fit |
| I2C target (4 registers) | **no** | 169 | 127 (11) | 61 | 0, 1 | 15 | - | 184 LCs, no fit |
| I2C target (2 registers) | **no** | 123 | 97 (8) | 41 | 0, 1 | 15 | - | 142 LCs, no fit |

The two fabrics take the same chip area: the primitive tile is 0.97 × a LUT tile in the same footprint (D-026), and the macros have identical size. This is a like-for-like comparison of the two fabrics under one compile flow, in the spirit of D-004; the full phase-3 comparison (routing, shell and configuration included, more variants) is still to come.

## Timing

Fmax is nextpnr's estimate at the slow corner (`nom_slow_1p08V_125C`), from nextpnr 0.11.1 (D-028): routing from the pip delays the fabric flow extracted from the hardened tiles; tile library cells at nextpnr's fixed values (LUT 3.00 ns, clock-to-Q 1.00 ns, setup 2.50 ns); the hard primitives from OpenSTA of each primitive at the same corner with a ×1.5 margin (`tools/timing/README.md`). All three designs are above the chip's 50 MHz. The first version of this table left every path through a primitive untimed (BUGS #17: UART 123.5, SPI 88.9, I2C controller 69.2 MHz). This is a model, not a measurement: no cross-check against STA of the hardened primitive tile or of a configured design yet, and no rate is claimed from it (`docs/CLAIMS.md`).

## How the designs use the blocks

Each protocol keeps a plain-logic form (`PRIMS=0`, for G0 and for run-time settings) and a primitive form (`PRIMS=1`), with the same behaviour at the pins; both pass the same RTL tests against the independent reference models (and sigrok for the UART), simulated with the fabric's own primitive RTL (`tools/compile/prims/warp_prims_sim.v` over `arch/prims/`):

- **UART:** TX: bit timer (RELOAD = DIV − 1) + shift register (LEN 9: 8 data bits, then the stop bit shifted in); RX: bit timer loaded with `half` for mid-bit sampling + shift register (LEN 8) holding the byte. Run-time baud (`RUNTIME_DIV=1`) uses the plain logic. Tests: DIV 16, 13, 5.
- **SPI controller:** SCK half-period timer + one shift register for both directions (MSB first; each change edge shifts in the bit sampled at the previous sampling edge). Tests: all four modes, HALF 4 and 7.
- **I2C target:** the bus byte (in and out) and its bit count in one shift register (its `done` replaces the bit counter and a state); rewritten at the same time with one shared read and write port for bus and host (the host waits a clock when the bus uses them), plain flip-flops instead of an inferred memory, and no own synchronizers (205 → 184 LCs on G0, 169 on G1). Tests: Q 4, 6, 11.
- **I2C controller:** one one-shot timer (RELOAD = 2Q − 1; its `half` load gives Q − 1, the other phase length) + a shift register for the data byte, two flip-flops for the ACK bit. Tests: Q 2, 4, 5 (incl. clock stretching, NACK, two targets).

User designs instantiate `WP_TIMER #(.RELOAD, .ONESHOT)` and `WP_SHIFT #(.LEN, .MSB_FIRST)` (`tools/compile/prims/warp_prims.v`); the compile flow maps them to the BELs with one configuration bit per parameter bit, nextpnr places them, and the bitstream sets those bits (checked on `tools/compile/examples/prims2`: RELOAD 5 → `A.RELOAD0`, `A.RELOAD2`; LEN 6 → `C.LEN1`, `C.LEN2`).

## Control sets (BUGS #15)

The first G1 run placed UART and SPI but not the I2C controller (78 of 88 LCs): a LUT tile's 8 LCs share one clock enable and one set/reset, and the design had 12 enable/reset pairs for 11 tiles. The flow now turns enables and resets used by fewer than `MIN_CTRL` flip-flops into logic:

| MIN_CTRL | UART | SPI | I2C controller |
|---|---|---|---|
| 1 (before) | 37 | 51 | 78, **no placement** |
| 2 | 29 | 47 | 70 |
| 4 (chosen) | 29 | 47 | 70 |
| 8 | 29 | 48 | 70 |

## Open
- **I2C target does not fit G1** even with 2 registers (123 of 88 LCs). Yosys's generic LUT4 mapping of the same source gives about the same size (82 LUTs at 2 registers, 103 at 4), so the compile flow is not the cause: the design (bus state machine, host command decoder, register ports, status) is about twice G1's logic. Options for phase 3: the register-file tile variant (ARCHITECTURE §9, D-016) or a larger fabric; I2C itself is covered by the controller.
- The same bitstreams loaded through the host interface on the chip: needs G1 in the chip (next hardware change).
