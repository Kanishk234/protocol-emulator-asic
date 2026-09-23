# TRIPWIRE decisions

Newest at the bottom. Each entry: date, decision, reason, alternatives, status.
A spec change is proposed here first and implemented only after the team agrees.

---

## D-001 (2026-09-22): architecture is TRIPWIRE
- **Decision:** build TRIPWIRE: triggered reflex lanes (no program counter on the fast path), SRAM routines, a multicast channel fabric and timed pin units. See `design/OVERVIEW_TRIPWIRE.md` and `design/ARCHITECTURE.md`.
- **Reason:** novel in the field (triggered execution and the multicast fabric), with a fixed, provable pin-to-pin reaction time and program-level static checks.
- **Alternatives:** PIO-style state machines, a barrel CPU (both well covered by other entries).
- **Status:** accepted.

## D-002 (2026-09-23): top module name `tt_um_tripwire`
- **Decision:** keep `tt_um_tripwire` as the top module.
- **Reason:** team choice; matches the project name.
- **Risk:** Tiny Tapeout asks for a unique name, usually by including the GitHub username. If the shuttle reports a clash, rename to `tt_um_<username>_tripwire` (a mechanical change: `src/`, `info.yaml`, `test/tb.v`).
- **Status:** accepted.

## D-003 (2026-09-23): questions to Jane Street (tile size, SRAM macro)
- **Questions:** (a) is 8x4 available, or should we design for 6x4; (b) are IHP SRAM macros accepted on the target shuttle.
- **Assumption until answered:** 6x4 with the 512x16 SRAM macro, keeping the flop-store fallback (`design/PHYSICAL_DESIGN_AND_CI.md` §3).
- **Status:** Jane Street sign-up form submitted (2026-09-23). Team decision (2026-09-23): **design for 6x4**; the tile question is not being asked for now. The SRAM question is also open. Until answered, the macro is assumed usable, and risk spike R3 (phase 1) proves or disproves it through the real flow, with the flop-store fallback kept.

## D-004 (2026-09-23): local toolchain
- **Decision:**
  - Python always runs from the project venv `.venv` (`scripts/setup_venv.sh`); packages pinned in `requirements-dev.txt` and `test/requirements.txt`.
  - OSS CAD Suite build 20260914 at `~/oss-cad-suite`, its `bin` **appended** to PATH (Verilator 5.053, Yosys 0.69, SymbiYosys, Yices, Boolector, Bitwuzla, mcy).
  - Icarus Verilog is the system package (12.0), the same one the CI `test` job installs from apt; appending the suite keeps it first on PATH.
- **Reason:** local results should match CI; the venv keeps the system Python clean.
- **Status:** accepted.

## D-005 (2026-09-23): no placeholder folders
- **Decision:** `spec/`, `tools/`, `programs/`, `test_internal/`, `formal/` and `macro/` are created when their first real file is added, not up front with placeholder READMEs. The target layout stays as listed in `design/phases/PHASE0_SETUP.md` task 6.
- **Reason:** keep the repo free of empty scaffolding; the layout is not a phase 0 exit item.
- **Note:** `macro/` is in the `gds` trigger paths, so adding it starts a hardening.
- **Status:** accepted.

## D-006 (2026-09-23): phase-gate exception for `ISA.md`
- **Decision:** start `docs/design/ISA.md` (a phase 1 spec task) before the phase 0 exit checklist is complete.
- **Reason:** the remaining phase 0 items are waiting on CI (`gds`, `viewer`/Pages), manual steps (`fpga` run, Jane Street form/email, roles) or a push; none needs design work. Team decision (Krithik).
- **Scope:** design documentation only. No RTL, model, compiler or `spec/tripwire.yaml` work until phase 0 exits. Phase 0 boxes are still ticked only with evidence.
- **Status:** accepted.

## D-007 (2026-09-23): ISA revision in `docs/design/ISA.md`
- **Decision (draft, to be confirmed by the model, D-008):**
  1. **One operation table for reflexes and routines.** Routines keep only sequencing, memory, output and flag instructions of their own. Drops the separate LC-3-style routine op set; resolves Q5.
  2. **Implicit readiness checks.** Reading an input head implies "available", writing an output implies "free", and CALL implies "RB = 0" (as in Triggered Instructions). Removes the `IN`/`OUT` condition fields and the read-without-check bug class.
  3. **Every op produces a flag result** (zero, or the compare/parity/less-than result), written when `DFE` is set. `CMPEQ` and `TSTZ` become `XOR`/`AND` with a zero result; the freed codes go to `LTU` and a reserved OP 15.
  4. **Per-lane constants K0–K3** (host-written while halted, usable as B and as CMPM operands).
  5. **Head `data[15]` test in conditions** (`HE/HV`). EVENT tokens carry their kind/polarity in `data[15]` (START vs STOP, rising vs falling).
  6. Slot grows from 51 to 52 bits; separate `OT`/`KT` tag fields; DST 7 reserved; `MKCTL` passes `A[11:0]`.
- **Reason:** research on PIO, PRU, Loom, FlexIO, Propeller 2 smart pins, XMOS, PSoC UDB and Triggered Instructions (sources in `ISA.md` §10). The protocol-specific work belongs in pin units, conditions and the fabric; the op table should be small and shared.
- **Also resolves:** Q1 (urgent slots pre-empt a waiting routine step; non-urgent ones wait at most 1 clock), Q2, Q3, Q4, Q6. See `ISA.md` §8.
- **Status:** accepted as the working draft (team: "make the best choices for now").

## D-008 (2026-09-23): phase 1 is model-first
- **Decision:** reorder phase 1: `ISA.md` draft → `tripsim` (parameterized, cycle-accurate from the start) + a minimal assembler → protocol kernels → measure and ablate (`ISA.md` §9) → freeze `spec/tripwire.yaml`. The same `tripsim` then becomes the golden model for lockstep.
- **Reason:** slot count, register count, OP 15 and the D-007 features are questions only numbers from real protocol programs can answer; freezing first would lock in guesses. Writing the model cycle-accurate from day one avoids a second model, and RTL independence is unaffected (no RTL exists yet).
- **Scope:** still phase 1 work; it starts when phase 0 exits (D-006 covers only `ISA.md`).
- **Status:** accepted (team).

## D-009 (2026-09-23): OP 15 = `MOVB` (d = B)
- **Finding (tripsim, first latency kernel):** with implicit readiness checks (D-007), a slot's tag/`data[15]` tests and dequeue apply only to the input it reads as A. "When an EVENT arrives on I0, send a constant pin command" therefore had no one-action form: with A = I0 the result is built from the event's timestamp, and with A = zero the slot ignores I0 and fires without an event. The workaround costs an extra action and would push the 7-clock pin-to-pin reaction to 8.
- **Decision:** the reserved OP 15 becomes `MOVB`: d = B, flag result d == 0. A reads (and may dequeue) the input; B supplies the constant (K, immediate or register).
- **Evidence:** `tools/tripsim/tests/test_pins.py::test_pin_to_pin_reaction_is_seven_clocks` uses `MOVB` and measures exactly 7 clocks.
- **Status:** accepted (draft ISA; the model's ablation can still reverse it).

## D-010 (2026-09-23): separate RX/TX link edges and an RX tail bit
- **Finding (tripsim, I2C target kernel):**
  - I2C samples SDA on SCL rise and changes it on SCL fall, so one shared LINKEDGE field cannot serve both halves of one pin unit.
  - I2C sends 9 clocks per byte. The target must see the 8 data bits *before* the 9th clock (to decide ACK/NACK in time), and must also see the 9th bit (the controller's ACK/NACK when the target transmits).
- **Decision:**
  - LINKEDGE is split into RX_EDGE and TX_EDGE.
  - New RX_TAIL: after RX_NBITS bits, the next bit is emitted as its own DATA token with the bit in `data[15]`, so a reflex can branch on ACK vs NACK with the `HE/HV` test.
  - Rules §14 P6–P8.
- **Evidence:** `tools/kernels/tests/test_i2c_target.py`: the target works against the reference controller at 100 kHz / 400 kHz / 1 MHz and checks out under sigrok `i2c`; 9 of 12 slots used.
- **Status:** accepted (draft).

## D-011 (2026-09-23): TX tag filter per pin unit, and TX preload for linked shifts
*(The tag-filter part is superseded by D-015: filters now live on every fabric consumer port. TX_PRELOAD stands.)*
- **Finding (tripsim, SPI controller kernel):**
  - An SPI controller needs three output streams (MOSI data, SCK clock commands, CS), but a lane has only two output ports. Spending a second lane on CS would cost a third of the chip's lanes.
  - SPI mode 0 (CPHA = 0) needs the first data bit on the wire *before* the first clock edge, which a purely edge-linked shift cannot do.
- **Decision:**
  - **TX_ACCEPT**: a 4-bit tag mask per pin unit. A token whose tag is not accepted is taken and dropped at once, without waiting for the unit to be ready, so it never blocks the other subscribers. One lane output can then be multicast to several units, each picking its tokens by tag. In the SPI kernel: SCK takes CTRL, MOSI takes DATA, CS takes EVENT.
  - **TX_PRELOAD**: a linked shift puts bit 0 out at once when the unit is idle. If the previous shift is still waiting for its final edge, that edge carries bit 0 instead (§14 P9), which is continuous SPI clocking.
  - LEVEL mode also accepts EVENT tokens (drives `data[0]`), so CS can be an EVENT.
- **Evidence:** `tools/kernels/tests/test_spi_controller.py`: mode 0, both directions correct against the reference target and sigrok `spi`, up to SCK = 16.7 MHz. Removing any one unit's filter makes a test fail.
- **Cost:** 4 filter bits + 1 preload bit per pin unit.
- **Status:** accepted (draft).

## D-012 (2026-09-23): design principle: general *and* optimized
- **Principle (team):** everything we add, to the pin units, the ISA, the fabric or anywhere else, should be the most **general** primitive that is still **efficient** for protocols, including ones we have not looked at yet. When a protocol exposes a gap, prefer generalizing an existing primitive over adding a protocol-shaped one, and be willing to change the architecture or ISA to do so. This is a judgement applied to every addition, not a counting rule. No dedicated protocol blocks: protocol logic stays in firmware.
- **How it is applied:** each new feature's DECISIONS entry says which general need it serves, and what makes it efficient (cost in bits, cells, slots or clocks). `ARCH_EXPLORATION.md` keeps a generality table of pin-unit and ISA features.
- **Status:** accepted (team, 2026-09-23).

## D-013 (2026-09-23): generalized pin-unit RX/TX primitives, and a head-bit select
Applying D-012 to the I2C read direction. A full I2C target needed 14–18 slots with the protocol-shaped features; it now fits in **12**.

| Change | General need it serves | Cost |
|---|---|---|
| EDGE_TS + COND_EDGE → one **event generator** (EV_EDGE, EV_QUAL, EV_RESET) | Any "edge of A, optionally while B is at a level": edge timestamps, I2C START/STOP, frame delimiters, wake-up edges | One edge detector + qualifier per unit (it replaces two) |
| RX_TAIL → **two-phase framing** (RX_NBITS2) | Any frame of two alternating word lengths: I2C 8 + 1, data + parity/flag bits, command + argument | A second 4-bit length and a phase bit |
| **Echo suppression** (RX_ECHO = 0) | Any half-duplex shared line (I2C, 1-Wire, SWD, half-duplex UART/LIN): the firmware never sees its own transmission. RX_ECHO = 1 keeps readback for collision/arbitration checks | One taint bit; saves 2–3 slots and an action per byte in the I2C target |
| **Length in the token** (TX_LENTOK) | Variable-length shifts without extra commands: I2C ACK (1) vs byte (8), SWD/JTAG mixed lengths, odd-length SPI | A 4-bit length mux; removes SETN tokens (a slot and an action each) |
| **HS** head-bit select (slot bit 52) | Condition on `data[0]` (flags, parity, ACK bits, LSBs) as well as `data[15]` (event polarity) | 1 slot bit + a 2:1 mux per slot; slot is now 53 bits (fits the 64-bit host view) |
| Event convention: `data[15]` = new pin level | Uniform for every event source, no special START/STOP encoding | None |

- **Evidence:** `tools/kernels/tests/test_i2c_target.py`:
  - read + write, NACK of other addresses, and the controller's NACK on the last read byte, at 100 kHz / 400 kHz / 1 MHz;
  - sigrok confirms written and read bytes, 10 ACKs, 3 NACKs and 5 START/STOP pairs;
  - fastest bus 12 clocks/bit, unchanged.
- **Tests have teeth:** disabling each of echo suppression, the SCL qualifier, length-in-token or HS makes 5 tests fail.
- **Supersedes:** the RX_TAIL part of D-010 (RX_EDGE/TX_EDGE stay).
- **Status:** accepted (draft).

## D-014 (2026-09-23): pin C, a select/frame input per pin unit
- **Finding (tripsim, SPI target kernel):** a clocked target needs a third pin besides data (A) and clock (B): the select (CS). It must restart bit framing, abort a transfer in progress on deselect, tri-state the output while deselected, and tell the firmware where transactions begin and end. None of this could come from pins A/B.
- **Decision (general form, D-012):** optional pin C per unit, with:
  - C_ACTIVE (the level that means selected);
  - while deselected, RX framing is held in reset;
  - the transition to deselected aborts a linked TX shift (pin A back to IDLE);
  - C_OE: pin A is driven only while selected;
  - EV_PIN: the event generator can watch C instead of A.
- **General need:** any select- or frame-delimited serial stream: SPI target CS, I2S word select, PCM/TDM frame sync, chip-enable-gated buses, and output-enable gating on shared lines.
- **Cost:** one more pad select (5 bits) and a few gates per unit.
- **Evidence:** `tools/kernels/tests/test_spi_target.py`:
  - both directions correct against the reference controller and sigrok;
  - an aborted 4-bit transfer leaves the next transfer byte-aligned;
  - removing framing reset, abort or OE gating each fails at least one test.
- **Measured limits of the SPI target (simulation):**
  - SCK ≤ 12.5 MHz with MISO changing just after the SCK rise; 8.33 MHz with the textbook "change on the fall";
  - CS setup ≥ 3 clocks (60 ns);
  - MISO released ≤ 3 clocks after CS rises (output-disable time).
  All three come from the 2-clock input synchroniser.
- **Status:** accepted (draft).

## D-015 (2026-09-23): tag filters on every fabric consumer port (supersedes D-011's TX_ACCEPT)
- **Finding (tripsim, I2C controller kernel):** one lane output needed to feed a pin unit (SCL: CTRL commands) *and* the host (HOST_OUT: received bytes). The D-011 tag filter lived only in pin units, and HOST_OUT is not a pin unit.
- **Decision (general form, D-012):** every consumer port has a 4-bit `accept` tag mask, set by the host with the port's source select. Non-accepted tokens are dropped at the port, as if taken (§14 F7). TX_ACCEPT is removed from pin units.
- **General need:** any multicast where subscribers want different kinds of token: pin units sharing one lane output, host and pin sharing one output, lanes ignoring event streams they do not need.
- **Cost:** 4 bits per consumer port (17 ports), plus a small compare.
- **Evidence:**
  - SPI controller (SCK/MOSI/CS by port filters) and I2C controller (SCL + HOST_OUT on L.O1; SDA events filtered off L.I1) both pass;
  - all earlier tests unchanged.
- **Status:** accepted (draft).

## D-016 (2026-09-23): CLKGEN period shape and STRETCH, WAIT command, echo = shifted bits on the pin
- **Finding (tripsim, I2C controller kernel):**
  1. CLKGEN periods started with the active edge, so an I2C START had no hold time before the first SCL fall, and SPI had only 1 clock of data setup.
  2. A controller must follow a target that holds SCL low (clock stretching).
  3. I2C STOP / repeated START need "SDA changes only after SCL has risen". With stretching, only waiting on the real edge is safe.
  4. The old echo rule ("TX busy") would have tainted a controller's read bytes, since its ACK token must be queued during the byte.
- **Decision:**
  - (1) Each CLKGEN period is **IDLE half, then ACTIVE half** (§14 P11).
  - (2) STRETCH: the IDLE half is timed from when pin A actually reads IDLE.
  - (3) New command **WAIT** (op 7): stop taking tokens until pin B shows an edge, then restart the timeline at that edge (§14 P16).
  - (4) A word is tainted only while one of this unit's *shifted bits* is on the pin (§14 P13).
- **General need:**
  - Clock generation that is safe on shared or stretched clock lines (I2C, SMBus, PMBus).
  - Sequencing one pin's commands against another pin's real edges (STOP/START, SWD/JTAG turnarounds, "wait for ready" lines).
- **Cost:**
  - CLKGEN becomes a small state machine instead of a precomputed schedule;
  - WAIT is a 1-bit edge register + compare;
  - taint is 1 bit.
- **Evidence:** `tools/kernels/tests/test_i2c_controller.py`, at 100 kHz / 400 kHz / 1 MHz, each with no stretch, 40-clock stretch and longer-than-a-period stretch:
  - writes, reads, NACK, repeated START and STOP are correct against the reference target and sigrok;
  - a bus-timing oracle asserts tLOW and tHIGH ≥ PERIOD/2;
  - turning off STRETCH fails 4 tests; making WAIT a no-op fails.
- **Measured costs:**
  - stretch awareness adds 3 clocks per high phase (943 kHz at a nominal 1 MHz);
  - the SPI controller's honest limit with a symmetric clock is 12.5 MHz. The earlier 16.7 MHz relied on a lopsided 2:1 duty cycle from odd-period rounding.
- **Status:** accepted (draft).

## D-017 (2026-09-23): `spec/tripwire.yaml` + generator, as a draft (not yet frozen)
- **Decision:**
  - `spec/tripwire.yaml` now holds every encoding (tags, op table, slot fields and enums, routine formats including signed fields, SYS kinds, pin-unit commands, the TX length-in-token layout), with the descriptions the docs show.
  - `tools/gen/gen.py` validates it: fields tile exactly, codes are unique and fit, and names are strings (the YAML `off`/`on` boolean trap).
  - It generates:
    - `tools/tripwire_spec.py`, which tripsim now imports (its private copies are gone);
    - `src/trw_defs.vh`;
    - the ISA/ARCHITECTURE tables between `GENERATED` markers.
  - `--check` fails on any drift. It runs in `check_all.sh` and the new `lint` workflow; the new `unit` workflow runs pytest.
- **Deviations from the phase 1 plan (task 3):**
  - one shared Python module instead of separate `tripc/encoding.py` and `tripsim/decoding.py`. Encodings are shared by design; independence is about behaviour, not bit positions.
  - `formal/props/dec_props.sv` waits for phase 2: it needs RTL signals to bind to.
- **Status:** `status: draft` in the YAML. It is flipped to `frozen` at the phase 1 spec freeze, after R1–R3, since the hardware experiments may still change slot widths. After that, spec changes need a DECISIONS entry.

---

## Open questions for the phase 1 spec freeze
Q1–Q6 below have **proposed resolutions** in `design/ISA.md` §8 (D-007). They close at the spec freeze once the model confirms them.

Found while reading the design docs; to be settled in `ARCHITECTURE.md` during P1.
- **Q1: routine steps vs. reflexes.** §6.2 says a routine step runs only on a clock when *no* reflex fires; §6.3 and the overview say *urgent* reflexes interrupt routines. What exactly does `U=0` block while RB is set?
- **Q2: CALL is encoded twice**, as `OP=15` and as `DST=7`. Keep one.
- **Q3: `MKCTL` cannot build `LEVEL 1` / `OE 1`.** MKCTL (§5.3) produces `{IMM[7:4], 0, A[10:0]}`, forcing data bit 11 to 0, but the pin-unit `LEVEL` and `OE` ops (§7.3) take their value from bit 11. Options: pass `A[11:0]` through, or take bit 11 from an IMM bit.
- **Q4: routine B format is too narrow.** `cond[11:9]` is 3 bits, but `BF f` / `BNF f` need a branch kind plus a 2-bit flag index, and `DJNZ r` needs a 2-bit register (§6.1). Needs at least 4 bits, or fewer branch kinds / flags.
- **Q5: routines have no compare or bitfield ops.** §4.4 of the overview says routines use the same operations as reflexes, but the R format only covers ops 0–7. There is no `CMPEQ`/`CMPM`/`TSTZ`/`PAR`/`EXT`/`SHOR` in routines, so a routine cannot set a flag from data. The 16 routine opcodes are all used, so adding these needs a sub-opcode field or dropping something.
- **Q7: fabric throughput (found by tripsim).** `ARCHITECTURE.md` §4.4 promised one token per clock per producer. That requires a same-clock path from a consumer's take back to the producer's load, which becomes a combinational loop on lane-to-lane channels. The model uses registered release (§14 F3). Measured: a lane can load one output port at most once every 3 clocks, and HOST_IN can feed a lane at most once every 2 clocks (`test_lane.py` throughput tests). Options: accept this; add a second register (depth 2) on selected producers; or allow a same-clock release only on edges that cannot form loops (pin TX, HOST_OUT). To be decided from the protocol kernels' measured needs.
- **Q6: `OTAG` shares bits with the immediate.** With `OTAG=1` the output tag comes from `IMM[7:6]`, so a slot that emits a CTRL/EVENT/ERR token with `BSEL=1` is limited to immediates 0–63. Decide whether that is acceptable or give the tag its own bits (the slot is 51 bits in a 64-bit host word space, so there is room).
