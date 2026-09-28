# Phase 3 summary: specialize, compare, hardware freeze

**Status:** complete (2026-09-28). Every exit item passed; `hw-freeze` → 3047dea; all CI green on `efpga` at a578359.

## Goal
Specialize the fabric one measured change at a time, compare every variant at equal area, and freeze the hardware on the best one the data supports.

## What we did
- **Measured what limits G1** (`docs/reports/g1_limits.md`, new `tools/profiling/limits.py`): with the timer and shift register in hardware, what is left of each protocol is control logic; control sets (3–7 per design) and the number of primitives are not limits; every critical path goes through a primitive.
- **Candidate 1, a timer with a registered terminal count** (D-030): proven equivalent (F4), `tc` 2.98 → 0.88 ns at no area cost, UART faster, but the slowest design (I2C controller) did not improve. Not kept.
- **Candidate 2, the primitive tile hardened with design repair** (D-031): the timer's slowest path is an unbuffered gate driving 33 loads, but the tile is 92 % full and runs with repair fail placement. Not feasible.
- **Candidate 3, a register file for the I2C target** (D-034): 169 → 123 cells, still far above the 80–88 available. Not kept.
- **Equal-area comparison** (`docs/reports/architecture_comparison.md` + chart) and the final choice: **G1** (D-033), hardened with the reset-synchronizer fix (BUGS #18): precheck pass, setup slack +12.48 ns at 50 MHz, `gl_test` 21/21 (CI 36383587262).
- **Organizers confirmed an eFPGA entry is fine** and asked for the software side (description → bitstream, loading, UART/SPI/I2C examples) (D-032); phase 4 now includes a demo-board loader and end-to-end examples.

## What we found
- G1 is the best of what can be built in this area for the design set: 3 of 4 protocols at equal area, where plain LUTs run 1.
- The limits left are physical and cannot be fixed at 6x4: the I2C target is ~1.5–2 × the fabric even with a register file, and the primitive tile has no room for buffering. The I2C target is therefore not supported (D-035); I2C runs through the controller.
- Timing margin is thin for the I2C controller (53 MHz model vs the 50 MHz clock).

## What's left
- Phase 4: held-out protocols on the frozen chip, the demo-board loader and end-to-end examples (D-032), robustness tests.

## One-line takeaway
Three measured specializations could not beat G1 at equal area, so the chip freezes on G1: UART, SPI and I2C in a Tiny Tapeout-sized fabric, with the one protocol that does not fit (the I2C target) documented rather than hidden.
