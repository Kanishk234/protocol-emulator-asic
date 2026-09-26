# Pin unit RTL: what it costs (phase 2)

**Question:** how big is a real `trw_pin_unit`, and was the pre-RTL estimate (`AREA_ESTIMATE.md`) right? The estimate's biggest guess was the pin units' control logic ("glue", 45 % ± 15 % of the datapath), and the chip is at ~87 % of the 6x4 core against a routable ~50–60 %.

**Status (2026-09-25): milestone A (lean feature set) done; milestone B (PULSE, carrier, BITSYNC for U0–U1) not started.**

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

**Timing at 20 ns** (OpenSTA, ideal clock, no wires, 0.25 ns uncertainty; paths ending at flops, since latch D pins borrow time by design as in R2):

| Corner | Config latches static (false path) | Config latches timed |
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
   - **8-bit → 4-bit fractions** (not measured yet) (PERIOD, SAMPLEOFS, the cursor fraction, the burst and sample timers): every timer and adder loses 4 bits, and each unit stores 8 fewer latch bits. Rough guess: 2–3K per unit, to measure. Cost: period resolution 1/16 clock. At 50 MHz a 115 200 baud UART period is 434.028 clocks: 1/16 gives ~64 ppm error (1/256 gives ~1 ppm), far inside a UART's ~2 % tolerance. It is a spec change (D-036 fields).
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

P-G15 and P-G16 are also proposals: they need a sentence in §14 H1 (and P-G19 a register in §9), so they go through a DECISIONS entry, not a silent RTL choice.

## 7. Next

- **Team decision on the cuts, with these numbers** (§5): fractions and timer widths (a spec change per D-037), 4 units, 2 lanes.
- Milestone B (PULSE P17, carrier P30, BITSYNC P20–P29) for U0–U1, then the same measurements. If a cut changes the timers, do it before B, since BITSYNC reuses them.
- The model session: answer P-G1–P-G23 in §14.
