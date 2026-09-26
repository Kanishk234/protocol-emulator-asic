# Profiling the design set (phase 1)

**Date:** 2026-09-25 · **Status:** measurement from synthesis (not place and route). Not a claim; it decides what phase 3 builds and measures.
**Tool:** `tools/profiling/workload.py` (`python -m profiling.workload` from `tools/`), Yosys 0.66+179 `synth_fabulous -lut K -carry {none,ha}` (OSS CAD Suite 2026-06-29). Local run; raw numbers in `build/profile/profile.json` (not committed).
**Held-out seal:** 0171cf7, before any profiling. Nothing here touched the held-out protocols.

## What was profiled
The four design-set user designs, each at a realistic setting (see each `protocols/*/README.md`):

| Protocol | Setting |
|---|---|
| UART | TX + RX, 8N1, 115200 baud at 50 MHz, divisor fixed in the bitstream (counters sized to the divisor) |
| SPI controller | mode 0, SCK = 1 MHz at 50 MHz |
| I2C controller | ~100 kHz SCL at 50 MHz, START/STOP/repeated START/stretching |
| I2C target | 4-register map, host access, dirty bits |

**Method.** Every LUT is attributed to the *function* of the registers it feeds, by walking forward through combinational logic to flip-flops or output ports. Register → function is a per-protocol table in the tool (`PROTOCOLS`), the one judgement in the method, reviewed against the RTL. A LUT that feeds several functions counts as `shared` (not split, not double counted). Functions: `counter` (timing and bit/edge counters), `shift` (serial shift registers), `storage` (bytes held for the host, register maps), `control` (state machines, flags), `sync` (input synchronizers), `pin` (registered pin outputs), `config` (run-time settings).

**Fairness fix made before these numbers:** the UART first used 16-bit counters for a divisor that needs 9 bits, which inflated the `counter` share (93 → 63 LUTs). It now sizes the counters to the divisor like the other designs do.

## Results

### LUTs per fabric variant (flip-flops don't change)
| Protocol | LUT3 | LUT4 | LUT6 | LUT3+carry | LUT4+carry | LUT6+carry | FFs |
|---|---|---|---|---|---|---|---|
| UART | 202 | **144** | 102 | 199 (+30 carry) | 126 (+30 carry) | 85 (+30 carry) | 68 |
| SPI controller | 147 | **100** | 76 | 143 (+11 carry) | 97 (+11 carry) | 66 (+11 carry) | 45 |
| I2C controller | 238 | **164** | 115 | 253 (+14 carry) | 163 (+14 carry) | 118 (+14 carry) | 65 |
| I2C target | 352 | **240** | 149 | 361 (+16 carry) | 249 (+16 carry) | 158 (+16 carry) | 79 |

### LUT4: LUTs by function
| Protocol | counter | shift | storage | control | sync | pin | shared | total |
|---|---|---|---|---|---|---|---|---|
| UART | 63 | 32 | 9 | 21 | 1 | 1 | 17 | 144 |
| SPI controller | 24 | 23 | 9 | 14 | 2 | 8 | 20 | 100 |
| I2C controller | 48 | 25 | 17 | 36 | 4 | 11 | 23 | 164 |
| I2C target | 15 | 31 | 102 | 37 | 4 | 11 | 40 | 240 |
| **all four** | **150 (23 %)** | **111 (17 %)** | **137 (21 %)** | **108 (17 %)** | **11** | **31** | **100 (15 %)** | **648** |

### LUT4: flip-flops by function
| Protocol | counter | shift | storage | control | sync | pin | total |
|---|---|---|---|---|---|---|---|
| UART | 26 | 16 | 8 | 17 | 1 | 0 | 68 |
| SPI controller | 9 | 15 | 8 | 8 | 2 | 3 | 45 |
| I2C controller | 12 | 17 | 8 | 22 | 4 | 2 | 65 |
| I2C target | 4 | 8 | 42 | 20 | 4 | 1 | 79 |
| **all four** | **51** | **56** | **66** | **67** | **11** | **6** | **257** |

Shared LUTs are mostly control+counter+shift in the controllers (the "bit done" and "next state" logic that reads the counters) and control+storage in the I2C target (register-map writes gated by the state machine). Full table: `build/profile/tables.md`.

## What dominates
1. **Counters (23 % of all LUTs, 4 of 4 protocols).** Bit-timing counters (baud divisor, SCK half period, I2C phase) and bit/edge counters. Every design reloads a counter and acts when it reaches zero.
2. **Storage (21 %, but 102 of the 137 LUTs are the I2C target's register map).** The other three spend 9–17 LUTs + 8 FFs each on the same thing: a one-byte holding register with valid/overrun for the host.
3. **Shift registers (17 %, 4 of 4).** 8–10-bit serial shifters, one or two per design.
4. **Control (17 %)** is protocol-specific state machine logic: it is what the LUT fabric is *for*, and no primitive targets it.
5. **Sync + pin (42 LUTs, 17 FFs, 4 of 4):** input synchronizers and registered/open-drain outputs, identical in every design.

**LUT size and carry:** LUT6 cuts the LUT count to ~0.65× of LUT4 and LUT3 raises it to ~1.45×, but a LUT6 has 4× the LUT configuration bits (64 vs 16) and wider input muxes, so which is smaller in *area* needs the area model (next phase 1 task). Half-adder carry chains save 0–18 LUTs per design (most in the UART) at the cost of 11–30 carry cells; only worth it if a carry cell is much cheaper than a LUT.

## Ranked specialization candidates
Savings are **upper bounds**: they assume a primitive absorbs all LUTs and FFs of its function in that design, before the glue logic to use it. Phase 3 measures the real saving with each primitive built, mapped and placed (CLAUDE.md "a block is done only when the tools can use it").

| Rank | Candidate (general primitive) | Absorbs | Protocols that use it | LUT4 saving (upper bound) | Notes |
|---|---|---|---|---|---|
| 1 | **Loadable down-counter / timer** (reload value, enable, terminal-count flag) | `counter` | 4 of 4 | 150 LUTs + 51 FFs total; UART 63, I2C ctrl 48, SPI 24, I2C target 15 | Also serves 1-Wire/WS2812-style pulse timing in principle (held-out; not tuned for) |
| 2 | **Shift register with bit count** (8–10 bit, serial in/out, parallel load/read, "N bits done") | `shift` + bit counters | 4 of 4 | 111 LUTs + 56 FFs (+ the bit-counter part of rank 1) | Bit counters could live here instead of in the timer |
| 3 | **Host byte channel in the shell** (holding register / small FIFO, valid/ready, overrun) | the host-facing part of `storage` | 4 of 4 | ~35 LUTs + 32 FFs (9–17 LUTs + 8 FFs per design) | A **shell** feature, not a fabric primitive: moves identical logic out of every bitstream |
| 4 | **I/O cell features**: input synchronizer, registered output, open-drain mode | `sync`, `pin` | 4 of 4 | 42 LUTs + 17 FFs | Small but free for every design; cheap in the I/O tiles |
| 5 | **Small register file** (e.g. FABulous `RegFile` 32×4) | the I2C target's register map | 1 of 4 | up to ~100 LUTs + 34 FFs, in one design | Only one design-set protocol needs it: fails D-002's "more than one protocol" test unless phase 4 shows more users; keep as an option, don't build first |
| — | Carry chains | part of `counter` | 3 of 4 noticeably | 0–18 LUTs per design | Mostly redundant with rank 1 |

## Does the design set fit ~96 LUT4s?
Budget: ~96 LUT4s at 6x4 (`docs/reports/tile_cmos5l.md`). Rough, subtracting the upper-bound savings of ranks 1–4 from the LUT4 totals (shared LUTs kept):

| Protocol | Generic LUT4 | After ranks 1–4 (upper bound) | Fits ~96? |
|---|---|---|---|
| UART | 144 | 144 − (63 + 32 + 9 + 1 + 1) = **38** | yes, with margin |
| SPI controller | 100 | 100 − (24 + 23 + 9 + 2 + 8) = **34** | yes |
| I2C controller | 164 | 164 − (48 + 25 + 17 + 4 + 11) = **59** | yes |
| I2C target | 240 | 240 − (15 + 31 + ~9 host holding + 4 + 11) = **~170**; **~77** if a register file also takes the other ~93 storage LUTs | **no**, unless the register map moves to a register file or shrinks |

So a fabric with a timer, a shift register, a host channel in the shell and smarter I/O cells plausibly fits three of four designs; the I2C target needs either a register-file primitive (single-user today) or a smaller register map. These are upper bounds; the capacity go/no-go (next) must use measured primitive areas and the glue each needs.

## Limits of this profile
- Synthesis only; place-and-route may need extra LUTs for routing (route-throughs) or fail to pack FFs with LUTs.
- The register → function table is a judgement; changing it moves LUTs between `control` and the others, not the total.
- `shared` LUTs are not credited to any candidate; a primitive may remove some of them too.
- One implementation per protocol, written by one person; another author could land ±20 %.
- The held-out protocols are not in this data by design.
