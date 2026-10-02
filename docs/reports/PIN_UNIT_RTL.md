# Pin unit RTL: what it costs (phase 2)

**Question:** how big is a real `trw_pin_unit`, and was the pre-RTL estimate (`AREA_ESTIMATE.md`) right? The estimate's biggest guess was the pin units' control logic ("glue", 45 % ± 15 % of the datapath), and the chip is at ~87 % of the 6x4 core against a routable ~50–60 %.

**Status (2026-09-28): milestone A (lean feature set) done; milestone B in progress: B1 (PULSE, carrier), B2a (the BITSYNC receive core), B2b (RX stuffing, CRC, FRAME) and B2c (the TX queue) done; B3 next (§9).**

**Answer so far:** the lean unit came in **~6 % under the estimate**: 38.7K µm² before layout (unit 29.4K + configuration 5.1K + producer 1.5K + the estimate's 2.7K for the consumer port) against 41.2K. The glue share was ~38 %, inside the guessed range. So the estimate holds, and **the chip is still ~85 % of the core** with real lean units. There is no hidden slack: getting to 50–60 % still needs real cuts. The per-feature prices below say where the lean unit's area goes.

Reproduce (WSL, OSS CAD Suite, liberty and OpenSTA cached by `spikes/r1_lane/run_r1.sh`):
- `synth/pin/run_pin.sh`: lint, Yosys area, OpenSTA (outputs in `synth/pin/build/`, git-ignored);
- `synth/pin/ablate.sh`: the per-feature price list (§4);
- `cd test_internal/pin && make FULL=0` (and `FULL=1`), in the venv: the L1 tests;
- `test_internal/pin/mutate.sh`: the injected-bug check.

---

## 1. What was built

Written from `ARCHITECTURE.md` (§4, §7, §9, §10, §14), `ISA.md` and `spec/tripwire.yaml` only; `tools/tripsim` and `spikes/area/ae_prims.v` were not read.

| File | Contents |
|---|---|
| `src/trw_pin_cfg.v` | The §7.2 block as a latch array (D-038): one library clock gate (`sg13cmos5l_lgcp_1`) per 16-bit word that stores anything, registered write data, the R1/R2 slot-array pattern. Write-only (D-039). `FULL = 0` stores only the core fields (D-040). Bits no field uses are not stored. A write to the block raises `restart` for the unit. |
| `src/trw_pin_io.v` | Pin selects: A (or S), B, C from the 24-pad vector; previous-clock values for edges; "selected" (P15). |
| `src/trw_pin_tx.v` | TX half: token decode, the cursor (P4), one pending and one "due next edge" action per kind (P3), timed SHIFT, CLKGEN with STRETCH and extension (P11), linked SHIFT with preload and abort (P6, P9, P15), WAIT (P16), SETN, SAMPLE and SETN rx (P18, P19), LATE, echo taint. |
| `src/trw_pin_rx.v` | RX half: SHIFT_RX (P5), LINKED_RX, SAMPLE bits, word framing (P13, two-phase, taint and echo, SETN rx restart), event generator with the PRESC tick counter (P8), one load per clock with priority (P19), OVERRUN (§4.5). |
| `src/trw_pin_unit.v` | Configuration fields, the three blocks above, output stage (OD, C_OE, pin N), sticky LATE / OVERRUN. Parameter `FULL`. |
| `tools/gen/gen.py` | New Verilog output: every §7.2 field position (`TRW_PC_<FIELD>_LSB/_MSB/_W`), enum codes (`TRW_PCE_<FIELD>_<VALUE>`), the stored-bit mask per feature (`TRW_PC_MASK_*`) and which units have each feature (`TRW_PC_UNITS_*`). The RTL takes all positions from there. |

**How the cursor avoids a multiplier.** P4 needs `cursor + delay × PRESC`. The unit keeps the cursor *relative to now, in ticks*: E = now − cursor = `eq` × PRESC + `er` clocks (0 ≤ `er` < PRESC), plus the cursor's 8-bit fraction. A delay of d ticks is `eq −= d`; the action is late when `eq ≥ 0` and due at the next edge when E = −1. While a shift or clock burst runs, its own bit timer (16.9 clocks to the next boundary) stands in for the cursor, because a burst ends on a boundary where E is −1 or 0. This costs a 16-bit subtract and an increment instead of an 11 × 8 multiplier and a 24-bit comparison against a wide time base.

**Interface.** The unit reads its consumer port's head (`tx_avail/tag/data`, returns `tx_take`) and loads its producer register (`rx_free` in, `rx_load/tag/data` out), per §4 and §14 F1–F7. The port and producer belong to the fabric; for measurement `synth/pin/trw_pin_meas.v` adds a minimal producer, counted separately. The consumer port was not built (fabric work); its size is the estimate's `port7`, 2.7K µm².

Not in `info.yaml` or `test/Makefile` yet (top-level integration comes later).

## 2. Verification

| Check | Result |
|---|---|
| Lint, `verilator --lint-only -Wall` | clean: the unit (FULL 0 and 1) and `trw_pin_cfg` (FULL 0 and 1); latches only in `trw_pin_cfg.v`, waived there |
| L1-PIN-TX (13 tests, `test_internal/pin/test_pin_tx.py`) | pass, lean and full build. LEVEL/OE/GAP/SYNC with PRESC; LATE; P3 same-edge "later token wins"; LEVEL-mode DATA/EVENT; open drain never drives high; UART SHIFT at 5.4 clocks/bit, back-to-back frames; **4096 bits at a fractional period: every edge exact, mean = PERIOD, jitter ≤ 1 clock**; MSB order, SETN, length-in-token; CLKGEN period shape, extension, odd period; STRETCH with a held line; WAIT (ignores the other edge); linked TX with preload and join; C_OE timing and deselect abort; ignored tokens |
| L1-PIN-RX (12 tests) | pass, lean and full. SHIFT_RX sample points (the pad holds the true bit only in the sampled clock, so any off-by-one fails); AUTOREARM back-to-back and off; LINKED_RX on rise and on fall; 8 + 1 two-phase framing; echo suppression on and off; event timestamps in PRESC ticks; qualified START/STOP with EV_RESET; SAMPLE and SETN rx; deselect holds framing |
| L1-OVR (2 tests) | pass: full producer keeps the old token, OVERRUN sticky and cleared; an EVENT beats a word in the same clock |
| Injected bugs (`mutate.sh`, 12 single-line bugs, one per rule) | **12 of 12 caught.** One survived the first run (WAIT on either edge): the WAIT test now includes the other edge first |
| `scripts/check_all.sh` | PASS (the regenerated `trw_defs.vh` breaks nothing) |
| L0-GEN | 34 generator tests pass, `gen --check` clean |

Expected values are written from the §14 rules, not from the model. Where the rules leave a choice open, the tests pin *this RTL's* choice (§6); lockstep against `tripsim` (L2) will show whether the model chose the same. Not done yet: L-XSIM (Verilator as simulator), gate-level, formal.

## 3. Numbers (milestone A)

Yosys onto the cmos5l cells, typical corner, the R1 recipe (`synth -flatten; dfflibmap; abc`, plain mapping), before layout.

| Block | Area µm² | Flops | Latches | Clock gates |
|---|---|---|---|---|
| `trw_pin_unit`, lean (FULL = 0) | 29,395 | 216 | 0 | 0 |
| — of which TX half | 18,439 | 130 | | |
| — RX half | 9,407 | 80 | | |
| — pin selects | 1,453 | 4 | | |
| `trw_pin_unit`, FULL = 1 | 29,395 | 216 | 0 | 0 |
| `trw_pin_cfg`, lean | 5,073 | 17 | 119 | 9 |
| `trw_pin_cfg`, full | 11,371 | 17 | 307 | 22 |
| producer register (stand-in) | 1,511 | 20 | | |
| wrapper, lean (unit + config + producer) | 35,769 | 252 | 114 | 9 |

- FULL = 1 has no extra logic yet (milestone B), and in the wrapper the full block's optional latches are optimised away because nothing reads them. The full configuration block alone is 11.4K.
- Of the 17 configuration flops, 16 are the registered write data. It could be shared by all six units and the slot arrays (saves ~5 × 0.8K).
- Flops are ~36 % of the unit's area (216 × 49 µm²).
- The lean block stores 114 latch bits in the wrapper (119 in the block alone: the 5 PIN_N bits go to the pad mux, which is not in the wrapper).

**Timing at 20 ns** (OpenSTA, ideal clock, no wires, 0.25 ns uncertainty; paths ending at flops, since latch D pins borrow time by design as in R2). Only the timed-configuration column follows D-066; the static-configuration result is a historical comparison, and the current script now runs timed paths only.

| Corner | Config static comparison (not D-066 signoff) | Config latches timed (D-066 contract) |
|---|---|---|
| typ | +10.83 ns (arrival 8.76) | +9.87 ns |
| slow | **+5.84 ns** (arrival 13.60) | +4.39 ns |

Critical path (both builds): the burst timer `u_tx.bt` → tail / "E = −1" detection (a 16-bit compare on `bt + step`) → the process-derived cursor → the 16-bit `eq − delay` subtract → late / due decision → the cursor increment → `u_tx.eq[12]`. With the configuration timed, it starts at TXMODE in configuration word 0. Both are well inside 20 ns; layout will cost some (R2 lost ~1 ns at the slow corner).

## 4. Where the lean unit's area goes

Marginal cost of each feature, from `synth/pin/ablate.sh`: the feature's decode is tied to 0 in a copy of the RTL and the unit is resynthesized. Baseline 29.7K here (ABC varies ~1 % between runs).

| Without | Saves µm² (before layout) |
|---|---|
| timed SHIFT and CLKGEN together (the 25-bit burst timer and its tail logic) | **8,508** |
| SHIFT_RX (the 24-bit sample timer) | 3,949 |
| CLKGEN alone (STRETCH, extension, half periods) | 2,860 |
| event generator (with the 15-bit tick counter and prescaler) | 2,630 |
| SAMPLE and SETN rx (timed RX actions) | 1,898 |
| linked TX (preload, abort) | 545 |
| timed SHIFT alone (CLKGEN keeps the timer) | 371 |
| WAIT | 354 |
| LINKED_RX | 301 |

The wide timers dominate. The burst timer, the SHIFT_RX timer and the cursor are ~14–16K of the 29K. The things that make protocols *general* (linked modes, WAIT, framing, events) are cheap by comparison.

## 5. Against the estimate, and what it means for the budget

| | Estimate (`AREA_ESTIMATE.md` §3, glue 45 %) | Measured |
|---|---|---|
| Lean unit incl. config, producer and port | 41.2K | **38.7K** (29.4 + 5.1 + 1.5 + 2.7 estimated port) |
| Lean logic only (no config, producer, port) | ~30.9K (21.3K datapath + 45 % glue) | 29.4K: the glue share is ~38 % |
| Configuration, lean / full (latches) | 4.2K / 10.8K | 5.1K / 11.4K (with clock gates and write register) |
| Full unit | 72.2K | milestone B. Projection: 29.4 + 11.4 + the estimate's PULSE / carrier / BITSYNC logic (~24.4K) + 4.2 ≈ 69K |

**Chip, redone with the measured lean unit** (full units still at the estimate; placed = Yosys × 1.30 + the 45.3K SRAM macro, as in `AREA_ESTIMATE.md` §5):

| Scenario | Placed | Share of the 902K core |
|---|---|---|
| E: 3 lanes, 2 full + 4 lean (the current decisions) | ~767K | **~85 %** (estimate: 87 %) |
| G: 3 lanes, 2 full + 2 lean | ~666K | ~74 % |
| H: 2 lanes, 2 full + 2 lean | ~582K | ~64 % |

**What the numbers say:**
1. **No free lunch from the glue guess.** The real lean unit is within 6 % of the estimate, so the gap to a routable 50–60 % must be closed by real cuts, as `AREA_ESTIMATE.md` §7 feared.
2. **The pin-unit core is timer-bound.** A shrink of the core ("option 3") should go after the wide timers, not after the features:
   - **8-bit → 4-bit fractions** (measured in §7: ~1.8K per lean unit, so smaller than guessed here) (PERIOD, SAMPLEOFS, the cursor fraction, the burst and sample timers): every timer and adder loses 4 bits, and each unit stores 8 fewer latch bits. Rough guess: 2–3K per unit, to measure. Cost: period resolution 1/16 clock. At 50 MHz a 115 200 baud UART period is 434.028 clocks: 1/16 gives ~64 ppm error (1/256 gives ~1 ppm), far inside a UART's ~2 % tolerance. It is a spec change (D-036 fields).
   - **Narrower timers**: the 16-bit integer part allows periods up to 65 535 clocks (1.3 ms). A 12-bit integer (4 095 clocks, 82 µs) would save ~8 flops and adder bits per timer, but UART would then stop at ~12.2 kbaud, so **9600 baud would be lost** unless PERIOD were also prescaled. Slow protocols (IR, servo) already use PULSE/LEVEL with PRESC. Needs a check against the 20 programs. Probably not worth it.
   - **Share one timer between TX and RX** only where full duplex is not needed. Not general (UART needs both), so not recommended.
3. **Fewer units or lanes still move the most area.** With the measured lean unit: 4 units ≈ 74 %, 4 units + 2 lanes ≈ 64 %; a core shrink of ~3–5K per unit on top of H brings it to ~60 %.
4. **Milestone B matters for U0–U1 only.** Its projection (~69K) matches the estimate. Measuring it will not change the order of the options above.

## 6. Gaps: choices the documents leave open (P-G*)

Each was decided in the RTL to keep going, and is marked `P-G<n>` in the source where it lives. The model session should answer them in §14, as R1's G1–G8 were (D-033). A different answer means an RTL change.

| Gap | Where | Open question | RTL choice |
|---|---|---|---|
| P-G1 | §7, §14 H1 | Output enable after reset / restart | OE = 1 (driven); the owner register is what keeps an unused unit off the pads |
| P-G2 | §7.1, P29 | Pin N with OD, and its OE | Pin N is push-pull `!level`, with pin A's OE before OD (OD applies to pin A only) |
| P-G3 | P4 | Cursor range: the rules use unbounded times | Cursor offset in signed 16-bit ticks. A cursor more than 32 767 ticks in the past saturates (chains of GAPs from a very old cursor then land later than the unbounded rule). A delay or GAP that would put the cursor more than 32 768 ticks ahead is not taken until time passes |
| P-G4 | P11 | PERIOD/2 when PERIOD is odd in 1/256 | Half periods are exact at 1/512 clock; the cursor after a burst is the final release time, which is on the 1/256 grid |
| P-G5 | P11, P12, §7.3 | CLK with n = 0, CLK outside CLKGEN, DATA/EVENT in CLKGEN, EVENT in SHIFT | Taken and ignored |
| P-G6 | P11 | CLKGEN with PERIOD < 2 clocks (a half period under 1 clock) | Not supported; tripc should reject it |
| P-G7 | P11 | A CLK taken in the clock of the burst's final release; the extension count's width | That CLK starts a new burst (at max(cursor, earliest), so one clock later), not an extension. The count is 9 bits: a CLK that would exceed 511 periods waits |
| P-G8 | P16 | Can a token be taken in the clock the WAIT edge appears? | Yes, with cursor := that clock + 1 |
| P-G9 | P6, P9, P15 | Linked TX edges while deselected; a TX_EDGE in the preload clock | Linked shifts move only on edges while selected; in the preload clock the edge is consumed by the preload |
| P-G10 | §7.4, P5 | SHIFT_RX without AUTOREARM after its word | Stops; a SETN rx re-arms it |
| P-G11 | P19 | A mode sample and a SAMPLE bit in the same clock (two framing bits) | The SAMPLE bit is dropped and OVERRUN set (one framing bit per clock) |
| P-G12 | P8 vs P19 | P8: "a sample due in the same clock [as an event] is skipped"; P19: the word loses the load and sets OVERRUN | P19: the sample enters framing; only a word it completes is discarded (OVERRUN) |
| P-G13 | P3, P18, P19 | Do timed RX actions (SETN rx, SAMPLE) count as pending actions for P3? Does a late SAMPLE set LATE? | Yes, they block later tokens like LEVEL; SAMPLE never sets LATE (P19 does not say so) |
| P-G14 | P13 | "Released lines do not taint" vs open-drain shifts, where a 1 is a release | Taint = the pad register holds one of our shifted bits, whatever OD/OE; return to IDLE, LEVEL or abort clear it |
| P-G15 | §14 H1, P8 (D-035 J) | When do unit registers restart after configuration? | Any write to a unit's block restarts all of the unit's registers (tick counter and sticky flags included). This generalises D-035 J's PRESC-write restart, and it is what keeps gate-level simulation free of X once the latches are written |
| P-G16 | §14 H1 | While the host is still writing configuration, half-written latches can make a unit load or take tokens with X values, which would stick in the fabric at gate level | A `live` input: the unit takes and loads nothing until the chip is live. Proposed rule: `live` = "some lane has been RUN or STEPped since reset" |
| P-G17 | §7.2 | RX_NBITS = 0 means NBITS: the configured field or a SETN tx override? Values 17–31? | The configured NBITS; 17–31 mean 16 (like SETN, P4) |
| P-G18 | §7.1, §10 | Unattached pins (31) and pad numbers 24–30 | 24–30 act as 31. Unattached A reads IDLE, B reads 0, C means always selected (P15) |
| P-G19 | §9 | How the host clears the sticky OVERRUN / LATE | Write-1-to-clear strobes from the host block (not yet in §9) |
| P-G20 | §7.2 | EV_QUAL code 1 is unused | Acts as none |
| P-G21 | §7.3 | WAIT [1] (sample point) outside BITSYNC | Ignored: an edge wait on [0] |
| P-G22 | P6, P3 | Other tokens in linked mode | Taken once all linked bits are out. A LEVEL landing on the same edge as a linked bit loses; it beats a pending return to IDLE |
| P-G23 | P12 | Does a LEVEL-mode DATA/EVENT move the cursor? | Yes, like LEVEL with delay 0 (cursor := its action time) |

**Resolution (D-041, ARCHITECTURE §14 P31–P45; RTL updated 2026-09-26):**
- **P-G7 → P34, changed.** A CLK taken in any clock of a burst, the final-release clock included (and, with STRETCH, the clock the line reads IDLE), now extends it: the next IDLE half starts at that release. `trw_pin_tx.v`: the burst counts as running through its last clock, and the end is cancelled by an extension taken in it.
- **P-G9 → P36, already compliant.** A TX_EDGE in the take clock n finds the unit idle and does nothing; in clock n + 1 the preload has priority and consumes the edge. Now pinned by a test for both clocks.
- **P-G12 → P38 / P8, changed.** EV_RESET now restarts framing *before* the event clock's sample, which becomes bit 0 of the new word. The RTL used to add the sample and then clear it.
- **P-G20 → P43, one change.** TX_EDGE code 3 now acts as none (a timed shift); it used to make the unit linked on the falling edge. The other lean fields were already right: EV_QUAL 1 → none, TXMODE 3–7 → LEVEL. DELIM and STUFF_LVL are BITSYNC fields (milestone B).
- **P-G22 → P44, already compliant.** A LEVEL on an earlier edge leaves the pending return to IDLE in place; on one edge a linked bit beats a LEVEL, which beats the return. Now pinned by a test.
- **Tests:** 7 new (34 L1 tests in all), passing on the lean and full builds. Four new mutants restore the old P34, P38, P43 and P44 behaviour (`mutate.sh`).
- **Cost:** lean unit 30,257 µm² (was 29,790 at FRAC 8, +1.6 %: mostly the P38 base-state multiplexers, at the edge of the ABC noise); still 216 flops. Slow-corner slack at 20 ns +5.50 ns (config static). `run_pin.sh`, 2026-09-26.
- Proposals A (P-G15) and B (P-G16) and D-042 (P-G19) still wait for approval; the RTL already does A, B and write-1-to-clear.

P-G15 and P-G16 are also proposals: they need a sentence in §14 H1 (and P-G19 a register in §9), so they go through a DECISIONS entry, not a silent RTL choice.

## 7. Measurement: a 4-bit timer fraction (2026-09-26)

**Question:** how much would the lean unit shrink if its time arithmetic used 4 fraction bits instead of the spec's 8 (§5, point 2)? **Measurement only**: `spec/tripwire.yaml` and the §7.2 layout are unchanged.

**How:** a parameter `FRAC` (default 8) on `trw_pin_unit`, `trw_pin_tx` and `trw_pin_rx` sets the fraction width of:
- the cursor fraction;
- the burst timer (16.(FRAC+1));
- the SHIFT_RX sample timer (16.FRAC);
- the PERIOD / SAMPLEOFS inputs, of which the unit uses the top FRAC bits of the 8-bit fraction fields.

With FRAC = 8 the RTL is the same function as before: all 27 L1 tests pass. With FRAC = 4, the 3 tests that use a 5.4-clock period fail, since 5.4 is not a multiple of 1/16 clock; the other 24 pass. Same recipe: `FRAC=4 synth/pin/run_pin.sh` (outputs in `synth/pin/build/frac4/`).

| Lean unit (FULL = 0) | FRAC = 8 | FRAC = 4 | Saving |
|---|---|---|---|
| `trw_pin_unit` area µm² | 29,790 | 27,903 | **1,887 (6.3 %)** |
| — TX half / RX half / pin selects | 18,393 / 9,407 / 1,488 | 17,570 / 8,995 / 1,446 | 823 / 412 / 42 |
| flops | 216 | 204 | 12 (TX 8: burst timer 4, cursor fraction 4; RX 4: sample timer) |
| wrapper (unit + config + producer) µm² | 35,723 | 33,977 | 1,747 |
| configuration latches the unit reads | 114 | 106 | 8 (the unused low bits of PERIOD and SAMPLEOFS) |
| slack at 20 ns, typ / slow (config static) | +11.21 / +6.42 ns | +11.51 / +6.94 ns | +0.3 / +0.5 ns |
| slack at 20 ns, typ / slow (config timed) | +9.66 / +4.06 ns | +10.39 / +5.24 ns | |

The critical path is the same at both widths: burst timer → cursor → `eq`.

**Noise:** the FRAC = 8 unit synthesized 395 µm² larger than in §3 (29,790 against 29,395) for an unchanged function, only because the source was parameterized. So ABC mapping moves this block by ~1–1.5 %, and the saving is **~1.7–1.9K µm² per lean unit** before layout, ~2.3–2.5K placed.

**What it means:**
- For the chip: six units at ~1.8K each is ~11K µm² before layout, ~14K placed, **~1.5 % of the core**. It would take scenario E from ~85 % to ~83.5 %. The full units would save a little more (CARRIER and SJW are 16.8 fields too; milestone B), but that doesn't change the picture.
- **Not a big lever.** It is a real but small saving, below the §5 guess of 2–3K. The fraction bits are a small part of the timers: the 16-bit integer parts and the adders around them remain.
- **Precision cost:** periods on a 1/16-clock grid. At 50 MHz a 115 200 baud UART gets ~64 ppm error (1/256: ~1 ppm); fine for any UART, but a spec change to the D-036 fields.
- **My recommendation:** don't adopt it on its own. It is worth doing only as part of a spec revision that is happening anyway. The cuts that move the chip are still fewer units or lanes (§5).

## 8. Next

- **Team decision on the cuts, with these numbers** (§5): fractions and timer widths (a spec change per D-037), 4 units, 2 lanes.
- Milestone B (PULSE P17, carrier P30, BITSYNC P20–P29) for U0–U1, then the same measurements. If a cut changes the timers, do it before B, since BITSYNC reuses them.
- The model session: answer P-G1–P-G23 in §14.

## 9. Milestone B: the full units (U0–U1)

**Why now:** the protocol floor (D-049) keeps U0 full whatever the budget: 7 programs need PULSE, the carrier or BITSYNC (CAN, HDLC, USB-LS, DShot, 1-Wire, WS2812, IR NEC). Written from `ARCHITECTURE.md` §7 and §14 P17–P30 only; `tools/tripsim` not read.

**Plan (each stage with its L1 tests and mutants before the next):**
| Stage | Rules | Contents | State |
|---|---|---|---|
| B1 | P17, P30 | PULSE (per-bit symbols in whole ticks, back-to-back join, cursor = end time); the carrier (50 % toggle while pin A is not IDLE, restart at each change to the active level, fractional period) | **done** |
| B2a | P20–P22 | BITSYNC engine `trw_pin_bs.v`: bit clock, bus idle, frame start with hard sync, resync (SJW), RX word framing | **done** |
| B2b | P23, P24 | stuffing (RX removal, stuff errors), the RX CRC, `FRAME n` and the frame verdict | **done** |
| B2c | P25 | the TX queue with `LINE`/`SYNC`, the TX CRC, `WAIT` [1]; driving pin A from the engine | **done** |
| B3 | P26–P29 | readback modes and arbitration, errors, flag delimiters, `JAM` and listen-only, NRZI, SE0, pin N, OE auto | **done** |

**B1 as built** (`src/trw_pin_tx.v`, parameter `FULL`): PULSE runs as a burst of whole ticks, each bit two phases counted as `pt` ticks and `ps` clocks of the tick (no multiplier); P3's "take when all pending actions are at edges ≤ n+1" extends to the burst's end, so the next DATA token's first bit lands on the end edge. PULSE bits set the echo flag (P40). The carrier is a 16.9-clock half-period timer in the TX half; `lvl` shows IDLE in the off halves (so pin N follows, and C_OE still gates the pad, D-035 H). On a lean unit the PULSE code acts as LEVEL and the carrier fields read 0 (D-040).

**Verification:** `test_internal/pin/test_pin_full.py` (4 tests, both builds): two back-to-back 8-bit PULSE tokens with PRESC = 1, every edge where P17 puts it, the second token joined; MSB order, a GAP after a token (cursor = end time) and a 0-tick phase; the carrier at 10 clocks and at 7.5 clocks (fractional), with IDLE steady and a restart on each activation; the carrier on a PULSE stream (IR NEC style); on the lean build the D-040 fallbacks. Pin suite 38/38 on both builds; `mutate.sh` 17/17 (lean) and 21/21 (full) with 6 new B1 mutants (one first-round survivor was an equivalent mutant and was replaced). Chip lint and chip tests unchanged (10/10).

**Cost:** the full unit's logic grows from 30.2K to **37.9K µm²** (+7.7K for PULSE and the carrier; Yosys cmos5l typ, flat, without the configuration block). The estimate's projection for all three features was ~24.4K, which leaves ~16.7K for BITSYNC.

**B2a as built:** `src/trw_pin_bs.v`, instantiated in full units only; while TXMODE and RXMODE are both `bitsync` it loads the producer (the RX half's event generator keeps priority, P-G28) and, until B2c, the unit takes no tokens and holds pin A recessive. One 1/256-clock timer to the next bit boundary; the sample falls in the clock containing bit start + SAMPLEOFS; hard sync sets the bit start to the frame-start clock; a resync is one signed correction of the timer by min(phase error, SJW).

**B2a verification:** `test_internal/pin/test_pin_bs.py` (3 tests, both builds): frames at PERIOD = 20.5 clocks starting at arbitrary phases, every byte a DATA word, a trailing partial word dropped at idle; a sender 2 % fast then 2 % slow over 48-bit frames: received intact with SJW = 0.15 PERIOD and misread with SJW = 0 (the resync is what saves it); one edge 1 clock late with SJW = 0.3 PERIOD (a resync by the whole SJW would sample the next bit). On the lean build nothing is received. Pin suite 41/41 on both builds; 7 B2 mutants, all killed; chip lint and chip tests unchanged.

**B2a cost, and what it means:** the first version (separate boundary and sample timers) was 20.2K µm²; with one timer and one signed correction the engine is **16.1K**, and the full unit's logic **54.0K** (B1 37.9K). The estimate had ~16.7K for all of BITSYNC; at B2a's rate the finished engine will be nearer 30K. For the protocol floor (D-049, U0 full) that is roughly +13K, about +2 % of the core. Levers, if the budget needs them: only U0 needs the engine (D-049 lets U1 be lean); timer arithmetic in whole clocks for SJW; the CRC width capped by what the programs use (CRC-16, CRC-15, CRC-5).

**B2b as built:** in `trw_pin_bs.v`: a run counter over line bits (stuff bits included); a due stuff bit is removed, an equal bit is a stuff error (ERR `0x1nnn`) that stops the frame's words; the RX CRC (MSB-first LFSR, CRC_WIDTH bits, from CRC_INIT, after CRC_SKIP destuffed bits); words of RX_NBITS (or `SETN` rx) in ORDER; `FRAME n` (now or for the next frame, LATE when it cannot apply) with the verdict at destuffed bit n, EVENT `word[11:0]` if the register equals CRC_RES, else ERR `0x0www`; after n, one more stuff bit is still removed and checked (and a violation reported). The RX commands `FRAME` and `SETN` rx are taken at once; TX tokens still wait for B2c.

**B2b verification:** `test_internal/pin/test_pin_bs_frame.py` (6 tests, both builds). The line is CAN from `tools/protomodels/can.py` (Bosch CAN 2.0, CRC-15, 5-bit stuffing) and, for ones-only stuffing, `tools/protomodels/hdlc.py`: standard and extended frames give the destuffed words and an EVENT verdict; a flipped CRC bit gives ERR; a violated stuff bit gives ERR `0x1nnn` and stops the frame; the next frame is received; FRAME with no frame sets LATE; `SETN` rx to 4-bit words; a stuff bit right after bit n is removed, and its violation reported; STUFF_LVL = 1; CRC_SKIP = 3. Pin suites 47/47 on both builds; mutants 17/17 lean, 36/36 full (the first round found an equivalent mutant, and a real gap: the stuff check after bit n detected an error but did not report it; fixed). Chip lint and chip tests unchanged.

**B2b cost:** the engine is **25.1K µm²** (+9.0K), the full unit's logic **62.3K**. The variable-width CRC (mask and top-bit select) and the 11-bit line/destuffed counters are most of it; a narrower CRC path (widths the programs use: 5, 15, 16) is a lever if needed.

**B2b readings (D-053):**
- **P-G27** ERR `0x1nnn` (stuff error): nnn = the index of the offending line bit in the frame (line bits, stuff bits included, from the first bit = 0).
- **P-G30** at FRAME's bit n the verdict token carries the current word, whether bit n completed it or not; no separate DATA word is emitted for that word.
- The verdict EVENT is `word[11:0]` with data[15:12] = 0 until B3 adds data[14] (our own frame).

**B2c as built:** in `trw_pin_bs.v`: a 16-bit TX shift register (next bit on top) loaded by a DATA word (NBITS or length-in-token, ORDER) or by `LINE` [3] (the TX CRC XOR CRC_XOR, CRC_WIDTH bits, MSB first); a TX token is taken only with no bits queued, so `LINE` [2] (stuffing), [6] (TX CRC := CRC_INIT, before [3]) and [3] act when taken, which is their place in the stream. At each bit boundary the engine drives a due stuff bit, else the next queued bit, else releases the line. The TX CRC takes the data bits sent (not stuff or CRC bits); SYNC also resets it. `SYNC`: the queued bits wait for bus idle and start our frame at the next boundary (EVENT `0x9001`, our bit timing kept); if another node's first bit arrives first and ours is dominant, we join it. The own-edge rules: no resync on an edge to the level we are driving, and no idle while we drive a bit. `WAIT` [1] holds TX tokens until the next sample point. `JAM` is taken at once and ignored, and `LINE` [1:0] and [4] are ignored, until B3. The unit drives pin A from the engine in BITSYNC.

**B2c verification:** `test_internal/pin/test_pin_bs_tx.py` (5 tests, both builds). Pin A on an open-drain pad forms a wired-AND bus with a second node:
- **CAN end to end:** `tools/protomodels/can.py`'s clock-level `CANNode` (the Bosch reference, with its own bit timing, destuffing, CRC-15 check and ACK) sits on the bus and decodes three frames we send with SYNC / LINE / DATA and the TX CRC (standard, extended, and one whose CRC ends in five equal bits, so a stuff bit must precede the `LINE` that stops stuffing). All three are received with a good CRC and ACKed. Every bit of ours is on the PERIOD grid from the start edge, and our own RX reports the start, the words and the verdict.
- **HDLC style:** LSB first, ones-only stuffing, CRC-16 XOR 0xFFFF against `protomodels.hdlc`'s stuffing, the stuff 0 before the flag.
- **Idle:** a 16-bit recessive run of ours does not make the bus idle.
- **Ignored ops and WAIT [1]:** the ignored ops are taken and do nothing; `WAIT` [1] releases in the sample-point clock.
- **Join:** another node's first bit arrives two clocks after bus idle; we join it, and our bits follow the hard-synced clock.
- **CRC reset:** `LINE` [6] in mid-frame (a header outside the CRC) and [6]+[3] in one `LINE`, on a CRC-5.

Pin suites 52/52 on both builds (and under Verilator); mutants: all 30 B2 mutants killed (16 new for B2c); chip tests 10/10.

**Timing (found at chip level, fixed; BUGS #51):** the chip's pre-layout STA after B2c showed the worst path from U0's TX level register through uo0 (which pin units read directly, P7) into the engine's bit-clock arithmetic (four 25-bit sums and compares in series after the pin) and on into a fabric drop counter: typ **+0.84 ns**, slow **−9.80 ns** (D-047 had +10.36 / +4.94). The engine now computes every sum from registered state in parallel (with and without a resync, and the hard-sync case from the configuration), and the edge terms only select among them. Likewise the CRC comparisons for a 0 and a 1 bit and the idle count. No behaviour change: the same 52 tests and 30 mutants pass. The chip is now **+7.65 ns typ, +0.87 ns slow** (spec counts), and the worst path is inside the engine's timer.

**B2c cost:** the engine is **34.8K µm²** (+9.7K, about 1K of it the retiming), the full unit's logic **73.8K**. The whole chip at spec counts is 616.7K µm² (Yosys, flat).

**B3 as built** (`src/trw_pin_bs.v`, `src/trw_pin_unit.v`):
- **Readback (P26):** `LINE` [1:0] sets the mode for the bits queued after it; each bit carries its own mode from the edge it starts on (a stuff bit that of the bit before it), so a `LINE` taken while the last bit of the previous stretch is still on the line does not change how that bit is checked (the CAN program's RTR bit). At the sample of a queued bit we drive: mode 1 on a mismatch emits EVENT `0x8000 | level << 14 | bit << 1`; mode 2 always emits `0xA000 | …`, an error if nobody overrode our level; mode 3 on a mismatch emits `0xB000 | …`, an error. Losing arbitration or an error clears the queue (bits, stuff bit, SE0/J, SYNC wait) and discards DATA and `LINE` tokens until a `SYNC` or `WAIT` [1]; the frame is then not ours any more.
- **Status EVENTs** (`0x9001`, the readback EVENTs, `0xC001`) go through a one-entry register: a frame token (word, verdict, stuff error, abort) keeps the clock, and the EVENT follows as soon as the producer is free.
- **JAM (P28):** a response (n bits of a level from the first bit start after d + 1 non-stuff sample points) is dropped when taken in a frame of ours; an armed JAM (n, level) fires at the first bit start after an error (readback error or stuff error) in any frame, and firing disarms it; [4]+[0] disarms; [1] / [2] switch listen-only on / off ([1] wins). A new response replaces a pending or driving one; arming does not touch a pending response (the CAN program sends a CRC-error flag and re-arms right after). JAM bits bypass the queue and come first at a bit start.
- **Listen-only:** switching it on releases the line at once, clears the queue and any JAM, and starts discarding; a `SYNC` is refused with EVENT `0xC001`; nothing can be driven while it is on (no extra gating on the drive paths: nothing that could drive is accepted).
- **DELIM = flag (P27):** a (STUFF_N + 1)th one is neither data nor a stuff error; the other level after it is a flag (a verdict on the committed bits, EVENT / ERR `0x0www`, then a new frame with a fresh CRC), one more one is an abort (ERR `0x2nnn` if bits were committed; nothing more until the next flag or idle). A hold-back of STUFF_N + 1 destuffed bits commits each bit STUFF_N + 1 bits later, so a flag's leading 0 and its ones never reach the frame, the words or the CRC; FRAME n and CRC_SKIP count committed bits.
- **NRZI, SE0, pin N, OE auto (P29):** NRZI sits between the line and stuffing / CRC on both sides (RX: a data 1 is a sample equal to the previous one; TX: a data 0 changes the line). `LINE` [4] queues SE0 for [11:8] + 1 bits and then one J (idle level) bit after the queued bits (and a due stuff bit); pin N is low during SE0, the complement of pin A otherwise. DELIM = se0: a frame ends with its verdict at the sample where pin S and pin B are both low, and idle never ends it. OE_AUTO: in BITSYNC the pads' output enables follow "a bit of ours is on the line"; our own frames' tokens (words, verdicts, errors) are not reported.
- **data[14]:** the verdict EVENT of a frame of ours (from our frame start or join until the frame ends, another node's frame starts, or our TX stops) has data[14] = 1.

**B3 verification:** `test_internal/pin/test_pin_bs_b3.py` (7 tests, full build; the lean build checks nothing here, D-040):
- **Arbitration:** we join a scripted node's frame and lose on the ID bit that also completes our first RX word: the word, then EVENT `0x800E`, then the winner's words and a verdict without data[14]; nothing driven after the loss, the rest of our tokens discarded; the reference `CANNode` decodes and ACKs the winner; a `SYNC` re-arms and our next frame reaches the node.
- **ACK slot and errors:** a CAN frame with the program's `LINE` sequence (arbitration, strict, CRC, delimiter, ACK slot in mode 2, EOF): with the node ACKing, EVENT `0xA000 | bit << 1` and no error, and a JAM taken in our own frame is dropped; without an ACK, EVENT `0xE000 | …`, no flag when disarmed, and when armed our 6 dominant bits start at the ACK delimiter (the node's own flag follows a bit later); tokens are discarded until `WAIT` [1]; a strict bit error on a forced bit gives EVENT `0xB000 | …` and the armed flag from the next bit.
- **JAM responses** in the reference node's frames: the ACK exactly in the ACK slot (the frame chosen with a stuff bit after its CRC, which the JAM must not count), and the node records its frame as ACKed; after a CRC error, 6 bits after the ACK delimiter; a second response replaces the first.
- **Listen-only:** [1]+[2] (so [1] wins), a SYNC refused with `0xC001`, the frame's tokens discarded, frames still received, a response JAM ignored, nothing driven; [2] and our frame reaches the node; [1] alone refuses again.
- **Flags:** `protomodels.hdlc` frames at +1 % and −1 % bit rate, two flags and then one shared flag between frames, a bad FCS and an abort: every byte, EVENT / ERR `0x0000` at the closing flag, ERR `0x2nnn` after the committed byte of the aborted frame, nothing for opening flags.
- **USB low speed TX:** D- and D+ equal `protomodels.usb.line_states` for a DATA1 packet bit for bit (NRZI, stuffing after six 1s, CRC-16, SE0 SE0 J); the output enables only from our first bit to the J bit; only EVENT `0x9001` reported.
- **USB low speed RX:** four packets at +0.5 % (data with long runs, a bad CRC, a token, an empty data packet): all bytes, EVENT / ERR at SE0 by the CRC-16 after 16 skipped bits, with IDLE_BITS 2 inside packets.
- B2c's HDLC-style test now sets DELIM = flag (its closing flag was a stuff error on our own frame, which since B3 stops our TX) and checks the flag's verdict; the other B2c tests expect data[14] on our own frames.

Pin suites **59/59** on both builds, under Icarus and Verilator; chip tests 10/10; Verilator `-Wall` clean. Mutants: **34/34 B3 mutants killed** (the first round had one equivalent mutant, "[2] wins over [1]", because the test switched listen-only on before sending [1]+[2]; the test now sends [1]+[2] with TX on); the B2 mutants whose target lines changed were updated, **31/31 killed**. `scripts/check_all.sh` PASS.

**B3 timing:** after B3 the chip's slow corner was −1.58 ns pre-layout. The worst path ran from the bit timer through `bnd` and our frame start into the flag hold-back, which shifted inside the frame's priority chain; the hold-back's contents only count through its fill count, so it now shifts on its own. The chip is **+7.09 ns typ, +0.02 ns slow** at spec counts (the worst path, bit timer → `bnd` → the TX queue, is B2c's), and +8.49 / +2.21 at the protocol floor. The pre-layout netlist has no buffering; nets of 25–43 loads account for about 5 ns of that path at slow.

**B3 cost:** the engine is **43.2K µm²** (+8.4K), the full unit's logic **~81.9K**. The whole chip is 632.2K µm² at spec counts and **407.6K** at the protocol floor (B2c: 398.7K), about 57.6 % expected at global placement.

**B3 readings (D-055):**
- **P-G36** a response `JAM` taken while a frame of ours is in progress is dropped (judged when taken).
- **P-G37** ERR `0x2nnn` (abort): nnn = the abort's line bit in the frame, as `0x1nnn` (P-G27).
- **P-G38** `JAM` [0] without [4]: the bit is ignored and the JAM is a response.
- **P-G39** readback applies to the bits from the TX queue (data, CRC, stuff, SE0, J), not to JAM bits.
- **P-G40** a stuff error stops our TX only in a frame of ours (it still fires an armed JAM in any frame).
- **P-G41** status EVENTs wait in a one-entry register behind frame tokens; a second one while it is full is lost with OVERRUN.
- **P-G42** each bit carries the readback mode it was queued under (a stuff bit that of the bit before it); mode 2 reports every bit it covers.
- **P-G43** a response counts its d + 1 non-stuff sample points from the clock after it is taken and starts at the first bit start in a later clock than the last of them; an armed JAM starts at the first bit start in a later clock than the error's sample, and firing disarms it (the CAN program re-arms).
- **P-G44** with DELIM = flag, FRAME n and CRC_SKIP count committed bits, a flag gives a verdict and an abort an ERR only if bits were committed, and the (STUFF_N + 1)th one is neither data nor an error.
- **P-G45** listen-only on releases the line at once, clears the queue, a pending or driving response and a pending armed fire (the arming itself stays); while it is on, `WAIT` [1] does not end the discard.
- **P-G46** "our own frame" lasts from our frame start or join until the frame ends (idle, SE0), another node's frame starts, or our TX stops (arbitration lost, an error, listen-only); a flag does not end it. In the readback EVENTs, level = the sampled line level and bit = the line bit's index in the frame.
- **P-G47** SE0 ends the frame at the sample where pins S and B are both low; that sample is no frame bit; the verdict carries the partial word; the next frame starts only after the bus is idle again (IDLE_BITS recessive samples).

**B2c readings (D-054):**
- **P-G31** `WAIT` [1] releases at the first sample point in a clock after the one it is taken in, and the next token may be taken in that sample point's clock (as P35).
- **P-G32** our frame opens at the bit boundary where we drive a SYNC frame's first bit, or a dominant bit at bus idle. Our bit timing is kept, and the echo of that bit is no frame start. EVENT `0x9001` is loaded at that edge (at a join: in the frame-start clock). Bits without a SYNC do not wait for idle.
- **P-G33** a stuff bit due after the last queued bit goes out at the next bit start even when nothing more is queued.
- **P-G34** the TX run restarts at our frame start: the first bit is a run of 1.
- **P-G35** "a bit we drive" (P20 idle, P22 own edges) means a bit from our queue or a stuff bit; a released line is not driven.

**B2a readings (D-052):**
- **P-G27** (open, for B2b): ERR `0x1nnn` "nnn = line bit" (P23) is read as the frame's line-bit count at the stuff error.
- **P-G28** in BITSYNC the RX half's event generator stays active and wins a clock it loads in; the engine's token is then lost with OVERRUN (P19's "EVENT first").
- **P-G29** the sample that makes the bus idle (the IDLE_BITS-th recessive one) is not a frame bit: a word it would complete is dropped with the frame.

**Readings where the text leaves a choice (for the model side, D-051):**
- **P-G24** PULSE phase of 0 ticks: lasts one clock (the RTL counts phases in clocks; programs use ≥ 6 ticks).
- **P-G25** CARRIER below 2 clocks: the carrier is off.
- **P-G26** carrier edges: the k-th toggle after a change to the active level lands on edge `t + floor(k · CARRIER / 2)` (CARRIER in 1/256 clocks, accumulated exactly), so the duty is 50 % to within one clock.
