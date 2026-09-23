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

## D-018 (2026-09-23): tripc v0 and the `.trw` language; programs/ is the firmware source
- **Decision:**
  - A line-oriented language whose slot syntax mirrors `ISA.md` (`slot urgent: when ADDR, I0 is DATA do CMPM none <- I0, mask K0 val K1 -> f0 then ACKQ`).
  - `#` is always a comment; immediates are plain expressions.
  - Params (overridable, including strings like `MISO_EDGE`) and consts.
- **Output:** a JSON-able image (pins, ownership, connections, per-lane slots/K/registers, SRAM with the entry table) plus a Markdown report:
  - slot/SRAM usage;
  - routine worst-case steps (forward branches + non-nested constant-count DJNZ loops; anything else gets "no static bound");
  - which urgent slots can pre-empt which.
- **Static checks:** undeclared states, a tag/head test on an input the action does not read, f3 writes, >12 slots, 16-bit K/registers, host/unknown pads, unknown pin keys and tags, undefined routines.
- **Source of truth:** `programs/*.trw`; `tools/kernels/*.load()` compiles them. The Python-assembled slots stay only as a bit-exact reference (`tools/tripc/tests`).
- **Also:** pad numbering and host pads moved into `spec/tripwire.yaml` (encodings belong there).
- **Known limits (v0):**
  - pin placement is fixed per program;
  - pin-config keys are validated against tripsim's PinConfig (the host config map is still OPEN in `ARCHITECTURE.md` §9 and belongs in the spec at the freeze);
  - reaction bounds are listed, not computed (phase 3, L6).
- **Status:** accepted.

## D-019 (2026-09-23): PULSE mode as two-phase symbols
- **Decision (general form, D-012):** the architecture's original "T0/T1 high times" becomes a two-phase symbol per bit value: SYMb = (first level, T1 ticks, T2 ticks), for b = 0 and 1 (§14 P17).
- **General need:**
  - pulse-width codes: WS2812/SK6812 LEDs, DShot ESCs;
  - pulse-distance codes: IR NEC, many RF remotes;
  - Manchester, where the first level differs per bit value (DALI, some RF).
  Stateful codes (biphase-mark, NRZI) belong to the line-coding primitive (PROTOCOL_SUPPORT.md item 3).
- **Cost:** 2 × (1 + 12 + 12) = 50 configuration bits per pin unit. Symbol timing uses the existing cursor, so back-to-back tokens join exactly.
- **Evidence:**
  - `tools/tripsim/tests/test_pins.py`: exact symbols, back-to-back join, Manchester and pulse-distance forms;
  - `tools/kernels/tests/test_pulse_protocols.py`: WS2812 (two frames; every datasheet tolerance; sigrok `rgb_led_ws281x`) and DShot150/300/600/1200 (frames, checksum computed by a lane routine, bit timing);
  - injected bugs (per-bit level ignored, phases swapped) are caught.
- **Status:** accepted (draft). Area: to be checked at synthesis. If 50 bits × 6 units is too much, the symbol tables could be shared between units.

## D-020 (2026-09-23): timed RX control: `SETN rx` (restart framing) and `SAMPLE`
- **Decision (general form, D-012):** two TX-stream commands that act on the unit's RX framing, timed by the same cursor as LEVEL/GAP (§14 P18, P19):
  - `SETN` arg bit 5 = 1: set the RX word length (1..16) and restart the RX framing at `max(cursor, earliest)`. Bit 5 = 0 keeps the old meaning (TX NBITS).
  - `SAMPLE delay` (op 8): at `cursor + delay`, sample pin A into the RX framing; `cursor :=` that time.
- **General need:**
  - Protocols where our own line activity, or a phase change, would otherwise misalign word framing: PS/2 host-to-device (the host's CLK-low inhibit is a counted falling edge), SWD/JTAG (turnaround and ACK/data phases of different lengths), half-duplex buses in general.
  - Protocols where the *controller* decides when a bit is sampled, with no clock edge to link to: 1-Wire read slots, open-drain "read a bit N µs after I pulled the line", presence detection.
  - Variable RX word lengths at run time without reconfiguration (ACK 3 bits, then data 32 + parity).
- **Cost:** an RX length register (5 bits), a restart strobe from the TX action queue, and one more action kind in the timed queue. No new pins, no new ports.
- **Evidence:**
  - `tools/tripsim/tests/test_pins.py`: `test_setn_rx_restarts_framing_at_the_cursor`, `test_sample_reads_pin_a_at_timed_points`;
  - `tools/kernels/tests/test_ps2.py`: host-to-device sends fail without the `SETN rx` restart (only the first byte gets through) and pass with it.
- **Status:** accepted (draft).

## D-021 (2026-09-23): more verification cross-checks, including Hardcaml
- **Decision:** add to `design/VERIFICATION.md`:
  - **L0-ASRT:** in-RTL assertions through one `TRW_ASSERT` macro, used by both formal and simulation;
  - **L-XSIM:** every cocotb suite runs under both Icarus and Verilator;
  - **L8-EQY:** equivalence check of the RTL against the netlist with eqy;
  - **L8-XPROP:** gate-level checks that nothing stays X after reset;
  - **L9:** Hardcaml as a second verification language:
    - H0: an import spike;
    - H1: waveform expect tests and OCaml pin-level tests;
    - H2: a third, independent OCaml model of the scheduler and fabric, run in lockstep.
- **RTL language:** the RTL stays Verilog. Hardcaml is used for verification only. This closes `OVERVIEW_TRIPWIRE.md` §13 item 6.
- **Reason:**
  - Assertions and eqy are cheap and strong. A simulator mismatch or an X after reset would otherwise reach silicon (BUGS #1 was an X bug).
  - Hardcaml gives a different language, simulator and author, so a spec misreading shared by tripsim and the RTL has another chance to show up. It is also the judges' own tool.
- **Cost:**
  - an opam/OCaml toolchain (pinned) and a `hardcaml/` dune project;
  - a new `hardcaml` workflow;
  - OCaml learning time.

  The import path (`hardcaml_of_verilog` through Yosys) is unproven on our RTL, so H0 decides go or no-go before any further investment. The fallback is trace replay against the OCaml model.
- **Priority:** L9 ranks below L2, L3 and L5 and is cut first if the schedule slips (with a DECISIONS entry).
- **Alternatives:**
  - SystemVerilog UVM testbenches: rejected, they need a commercial simulator (pyuvm covers UVM).
  - Hardcaml RTL: rejected, the RTL, flow and tests are already Verilog.
- **Status:** accepted (team request, 2026-09-23). H0 is not yet run.

## D-022 (2026-09-23): FPGA target is a Basys 3 running the full design; the reduced iCE40 build is dropped
- **Decision:**
  - The FPGA target for the build check (phase 3) and for hardware validation (phase 7A) is a **Digilent Basys 3** (Xilinx Artix-7 XC7A35T), running the **full** design: 3 lanes, 12 slots, 6 pin units.
  - The reduced iCE40UP5K build (1 lane, 8 slots, 2 pin units; PHYSICAL_DESIGN_AND_CI §8, phase 3 items 8–9) is dropped.
- **Reason:**
  - The team has easy access to a Basys 3, so there is no board to buy.
  - The reduced build was specified before the programs existed and cannot run most of them:
    - 8 slots excludes the I2C controller (11), I2C target (12), PS/2 (12), SWD (12) and 1-Wire (9);
    - 2 pin units excludes the SPI controller and JTAG (4 each).
    
    It could not have exercised I2C, a required protocol.
  - The XC7A35T (20,800 LUT6, 41,600 flops, 1,800 Kbit block RAM) should hold the full design. The UP5K (5,280 LUT4) very likely cannot. Both are estimates until the phase 2 RTL is synthesized.
  - Testing the design we tape out is stronger evidence than testing a cut-down copy.
- **FPGA-only differences** (behind a synthesis define; the ASIC build is unchanged):
  - the slot latches in `trw_slots.v` become flops;
  - the SRAM wrapper maps to block RAM;
  - 50 MHz comes from the board's 100 MHz oscillator through an MMCM.
- **CI:**
  - The template's `fpga` workflow (iCE40UP5K, manual dispatch) is left untouched (CLAUDE.md) but **no longer gates any phase**. It is expected to fail once the full design outgrows the UP5K.
  - Its place in the phase 3 and phase 4 exit checklists is taken by a full-design Artix-7 build. There are two ways to run it:
    - our own `fpga_basys3` workflow, using an open-source Artix-7 flow (openXC7);
    - a local Vivado build script whose utilisation and timing report goes in `docs/reports/`.
    
    The choice is open until phase 3 and will be recorded here.
- **Cost:**
  - one synthesis define and a Basys 3 constraints file;
  - a build path outside the template (Vivado is large and awkward on GitHub Actions; openXC7 is less mature).
- **Honesty:** FPGA results are labelled "tested on FPGA (Basys 3)", never silicon; the clock source and the latch-to-flop change are stated with them.
- **Status:** board choice accepted (Kanishk, 2026-09-23). CI mechanism open.

## D-023 (2026-09-23): BITSYNC pin-unit mode (recovered bit clock + line coding + readback), `pin_s`
- **Decision (general form, D-012):** a pin-unit mode where TX and RX share one bit clock recovered from the line, with a line-coding stage between the bit clock and the words (§14 P20–P26):
  - bit timing: hard sync at a frame start (another node's first dominant edge at bus idle, or our own frame start), resync on later edges limited to SJW, once per bit, never on edges we cause while driving dominant; sample point SAMPLEOFS; bus idle after IDLE_BITS recessive samples;
  - bit stuffing (STUFF_N, optionally only runs of one level: STUFF_LVL), inserted on TX and removed on RX, with stuff errors reported;
  - a CRC register (any polynomial ≤ 16 bits, init, expected residue) over the destuffed RX bits; `LINE` appends it to TX; `FRAME n` ends a frame after n destuffed bits, checks the residue and flushes the last word (EVENT if good, ERR if not);
  - readback: compare each driven bit with the sensed line: off / abort on mismatch / report every bit;
  - a one-bit override (`LINE` [4]): drive one bit in another node's frame (ignored in a frame this unit transmits), bypassing the TX queue;
  - TX status events: our frame started / aborted / reported bit;
  - `pin_s` (any mode): sense a different pad than the one driven (TXD/RXD transceivers).
- **General need:** self-clocked NRZ buses with clock tolerance and in-frame responses. CAN (5-bit stuffing, CRC-15, arbitration, ACK); HDLC/SDLC (ones-only stuffing, CRC-16); USB low-speed (6-ones stuffing, CRC5/16, with a future NRZI option); LIN and DMX (resync only); 1-Wire search and multi-controller I2C (readback). The same test suite runs an HDLC-style configuration (`tripsim/tests/test_bitsync.py`) so the mode cannot quietly become CAN-shaped.
- **Rejected alternatives:**
  - A CAN controller block: protocol-shaped (D-012).
  - A length-field extractor in the unit, so DLC-dependent frame lengths need no lane: saves a lane round trip but encodes one family of frame formats; `FRAME n` from the lane is general.
  - A second command port per unit, for RX-side commands from another lane: a bigger fabric change. The CAN program avoids needing one by never parking TX data in front of the unit while a frame waits for the bus (the "started" event).
- **Cost (estimate, to check at synthesis):** a 16-bit CRC register + 16-bit polynomial/init/residue configuration (~64 config bits), two stuffing counters, resync arithmetic on the existing 16.8 period accumulator, a one-token TX bit queue, a 2-token RX skid buffer, a `pin_s` mux (5 bits). One BITSYNC engine could be shared by 2 units if area is tight.
- **Evidence:**
  - `tools/kernels/tests/test_can.py` (16 tests): our frames at 125 k / 500 k / 1 Mbit/s received by a reference CAN 2.0A node and decoded by sigrok `can`; the reference's frames received and ACKed at 3 rates × (nominal, ±0.4 %) clock; arbitration lost then retried; bad CRC reported and not ACKed; the ACK in the right slot when a stuff bit follows the CRC (100 ns and 300 ns loop delay).
  - `tools/tripsim/tests/test_bitsync.py` (6 tests): HDLC-style ones-stuffing + CRC-16/CCITT with ±2 % drift, CRC and stuff errors, TX encoding against a reference encoder, the override in another node's frame vs our own.
  - Mutations caught: no resync, no TX stuffing, no RX destuffing, CRC polynomial ignored, no readback abort, override in our own frame, no post-CRC stuff check, override armed by a stuff bit. **Not caught:** resync on our own dominant edges (it needs a multi-transmitter propagation-delay scenario; noted as a gap).
- **Status:** accepted (draft).

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
