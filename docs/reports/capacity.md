# Capacity go/no-go (phase 1)

**Date:** 2026-09-25 · **Status:** estimate from measured tile/die numbers and synthesis; not a claim. Decision recorded as DECISIONS D-016.
**Inputs:** tile hardening `tile_cmos5l.md` (LUT4x8_ha on CMOS5L, Metal2–Metal4, DRC clean: 40,719 µm² per 8 LUT4s); die 1289.28 × 710.64 µm (gds run 36170807513); profiling `profiling.md`; primitive sketches `spikes/primitive_area/` synthesized on `sg13cmos5l_stdcell_typ` + configuration latches. **Model:** `tools/areamodel/model.py` (`python -m areamodel.model` from `tools/`; 5 pytest).

## Supply: what fits on the die
| Grid (LUT-size tiles) | Fits next to a shell column? | LUT4 (0 / 1 / 2 primitive tiles) |
|---|---|---|
| 4 × 3 | yes, fabric 1017 × 669 µm, shell column ~273 µm | **96 / 88 / 80** |
| 5 × 3 | no (53 µm left) | — |
| 4 × 4 | no (too tall) | — |

- A **primitive tile** = 2 timers + 2 shift registers in one tile slot. Estimated 1.07× a LUT tile (same switch matrix assumed; primitives 2,751 µm² per timer and 1,538 µm² per shift register incl. configuration bits, vs ~740 µm² per LUT4 without routing). The 7 % extra must come out of the tile's slack or a slightly taller tile; phase 3 hardens it.
- Timer and shift-register settings (reload value, length, bit order) are **configuration bits**, fixed per bitstream, so they cost no fabric LUTs or routing.

## Demand: each design-set protocol alone (one bitstream at a time)
LUT4 after the primitives (ranks 1–4 of `profiling.md`: timer, shift register, host channel in the shell, I/O-cell sync/registered/open-drain). "Upper bound" assumes each primitive absorbs its whole function; "+30 % glue" allows for the logic that drives the primitives and for imperfect absorption.

| Protocol | Generic LUT4 | With primitives (upper bound) | +30 % glue | Primitives used | Fits 88 (1 primitive tile)? | Fits 80 (2)? |
|---|---|---|---|---|---|---|
| UART | 144 | 38 | ~50 | 2 timers, 2 shift | **yes** | yes |
| SPI controller | 100 | 34 | ~45 | 1 timer, 1 shift | **yes** | yes |
| I2C controller | 164 | 59 | ~77 | 1 timer, 1 shift | **yes** (11 spare) | yes (3 spare) |
| I2C target (4 registers) | 240 | ~170 | ~220 | 1 shift | **no** | no |

Generic fabric alone (96 LUT4): only the SPI controller (100 LUTs) comes close; nothing else fits. This confirms D-008.

## Decision (D-016)
- **GO: pure specialized eFPGA**, not the hybrid fallback. A 4 × 3 fabric with one primitive tile (2 timers + 2 shift registers), the host byte channel in the shell and synchronizer/registered/open-drain I/O cells fits three of the four design-set protocols with margin.
- **Open: the I2C target** (and so the phase 4 showcase, which builds on it). Its register map is ~100 LUTs of storage plus access muxes. Options, to be measured in phase 3 in this order:
  1. a **register-file primitive** (FABulous already has a `RegFile` tile type). Today it has one design-set user, so under D-002 it needs a second user (a FIFO in a user design, or held-out results) or a DECISIONS entry that says why one user is enough;
  2. a **smaller map** (1–2 registers) with the rest held by the host through the shell's byte channel;
  3. accept that the I2C target doesn't fit, and demonstrate the showcase on the I2C controller instead.
- **Not possible at this size:** two protocols at once (e.g. I2C target + UART concurrently). The concurrency demo in phase 4 is dropped unless phase 3 finds room.

## Uncertainty
- Synthesis only; place and route of user designs on the real fabric may need 10–30 % more LUTs (route-throughs, packing).
- The primitive tile is an estimate (same switch matrix assumed); the LUT tile is measured.
- Shell area (~30–50K µm²) is an estimate; it fits the ~273 µm column (~190K µm²) with large margin, so it doesn't move the decision.
