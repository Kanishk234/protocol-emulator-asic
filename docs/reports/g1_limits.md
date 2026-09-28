# What limits the design set on G1 (phase 3 input)

**Date:** 2026-09-28 · **Architecture:** `arch/warp_g1` (the chip, CI 36376994834) · **Flow:** `python -m compile.protocols` (current sources, `PRIMS=1`), then `python -m profiling.limits` · Local run. The method is phase 1's (`docs/reports/profiling.md`): each LUT is attributed to the function of the registers it feeds; here the hard primitives count as registers of their function (timer = counter, shift register = shift), so the LUTs around them are their glue.

| Protocol | fits G1? | LCs | LUTs: counter / shift / storage / control / sync / pin / shared | FFs | control sets | primitives | Fmax (MHz, model) | critical path |
|---|---|---|---|---|---|---|---|---|
| UART | yes | 29 | 0 / 1 / 1 / 11 / 0 / 2 / 4 | 19 | 3 | 2 shift, 2 timer | 90.7 | through a primitive |
| SPI controller | yes | 47 | 11 / 3 / 2 / 12 / 0 / 5 / 5 | 25 | 4 | 1 shift, 1 timer | 78.0 | through a primitive |
| I2C controller | yes | 70 | 7 / 4 / 9 / 30 / 0 / 11 / 9 | 32 | 3 | 1 shift, 1 timer | 53.0 | through a primitive |
| I2C target | no | 169 | 10 / 4 / 41 / 21 / 0 / 7 / 44 | 61 | 7 | 1 shift | - | - |

(Phase 1, generic LUT4, same designs: counters were 23 % of all LUTs and shift registers 17 %.)

## Findings

1. **Counters and shifting are gone as a cost.** What is left is control (state machines, flags): 11–30 LUTs per design, the largest part everywhere except the I2C target. No general primitive absorbs arbitrary state machines.
2. **Control sets are not the limit any more.** 3–7 per design (after BUGS #15's flow fix) against 11 LUT tiles. A LUT tile with two enable/reset sets would not change what fits.
3. **Primitive count is not the limit for the design set.** Each design fits with the 2 timers + 2 shift registers of one primitive tile (UART uses all four). A second primitive tile would cost 8 LUTs with no design-set user.
4. **Timing is limited by the primitives.** Every critical path goes through a primitive pin; the I2C controller's estimate is 53.0 MHz against the 50 MHz clock. The largest primitive arc is the timer's clock → `tc` (2.98 ns standalone, a 16-bit compare with zero after the counter flops; ×1.5 in the model) and its input setup (×3.0 after the hardened-tile check).
5. **The I2C target does not fit, and a register file would not make it fit.** Its storage is 41 LUTs + 44 FFs (registers, host read data, dirty bits) out of 169 LCs; even if a register-file tile absorbed all of it (and took a LUT slot, leaving 80 LCs), the rest is ~105–110 LCs.

## What this means for phase 3 (candidates, measured)

| Candidate | Measured case | Plan |
|---|---|---|
| **Timer with a registered terminal count** (compute `count == 0` one cycle ahead into a flop, so `tc` is a flop and an AND) | Every design's critical path goes through a primitive; the timer's `tc` arc is the largest | **Measured (D-030):** `tc` 2.98 → 0.88 ns, no area cost, but the worst design (I2C controller) is limited by paths into the timer: 53.0 → 52.1 MHz. Not kept alone |
| **Primitive tile hardened with buffering** (resizer/repair for the primitives' nets; the tile library disables them) | the timer's in-tile input path has a NOR driving 33 loads (2.90 ns) | **Measured (D-031):** not feasible: the tile is 92 % full in the LUT tile's footprint; with design repair inserted, detailed placement fails. Not kept |
| LUT tile with two control sets | 3–7 sets vs 11 tiles: not binding | Record as not pursued (DECISIONS), with this table |
| Second primitive tile | no design-set user; −8 LUTs | Not pursued for the design set; revisit only if phase 4's held-out results show a need (then it is data, not tuning) |
| Register-file tile | does not make the I2C target fit | **Measured (D-034):** registers in two `RAM_32x4_2R_1W`: 169 → 123 LCs (4 registers), 123 → 110 (2); still ~1.5 × the fabric. Not kept |
| IO-cell open-drain mode / registered IO in the fabric | `pin` LUTs 2–11 per design; the shell already registers and synchronizes | Low value; last if time allows |
