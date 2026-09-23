# Phase 1: spec, model and risk tests

| | |
|---|---|
| **Dates** | Oct 5 → Oct 18, 2026 |
| **Goal** | Freeze the exact hardware contract in one machine-readable spec. Build the golden model and a first compiler. Show UART, SPI and I2C working *on the model*. Retire the three biggest hardware risks with small experiments before committing to full RTL. |
| **Devices needed** | None |
| **References** | `../ARCHITECTURE.md`, `../VERIFICATION.md` §4, `../PHYSICAL_DESIGN_AND_CI.md` §3–5 |

---

## 1. Entry criteria
- Phase 0 exit checklist passed.
- The Jane Street answers on tile size and SRAM may still be pending; if so, assume 6x4 plus the macro, with the fallback kept.

## 2. Tasks

**Order (DECISIONS D-008): model first, then freeze.**
1. The `ISA.md` draft (done early under D-006).
2. §2.2: `tripsim` as a parameterized, cycle-accurate architecture model, plus a minimal assembler for slot and routine images.
3. The protocol kernels on it.
4. §2.0: measure and ablate.
5. §2.1: freeze and generate.

The §2.4 risk spikes run in parallel from the start.

### 2.0 Architecture exploration (owner: architecture + verification)
- Run UART, SPI controller, I2C controller, I2C target and SPI target kernels on `tripsim`, written against `ISA.md` with the minimal assembler (the full `.trw` language can come later).
- Answer every row of `ISA.md` §9 with numbers:
  - slots and registers per protocol;
  - reaction latency against protocol deadlines;
  - cost of the R1 "every other clock" fallback;
  - an ablation of each D-007 feature;
  - what OP 15 should be.
- Write the results to `docs/reports/ARCH_EXPLORATION.md`, and log each ISA change it causes in `DECISIONS.md`.

### 2.1 Spec freeze (owner: architecture)
1. Resolve every **OPEN** item in `ARCHITECTURE.md` and `ISA.md`, using the §2.0 results:
   - token tag set;
   - exact reflex slot bit layout and OP encodings;
   - routine opcode table;
   - pin-unit CTRL op table;
   - connectivity (legal-source) table;
   - host address map;
   - host pin map, checked against the TT demo board's RP2040 SPI pins.
2. Write `spec/tripwire.yaml`, the single source for all of the above.
3. Write `tools/gen`, which generates from the YAML:
   - `src/trw_defs.vh` (constants, field positions);
   - `tools/tripc/encoding.py`;
   - `tools/tripsim/decoding.py`;
   - the Markdown tables in `ARCHITECTURE.md`;
   - `formal/props/dec_props.sv` (decode properties).
4. Add a CI step (`lint` workflow) that regenerates and fails on any diff.
5. Add a **cycle-exact semantics section** to `ARCHITECTURE.md`: for each block, what changes on which clock (EVAL/EXEC, channel handshake, rotation, pin cursor). RTL and model both implement this text.

### 2.2 Golden model `tripsim` (owner: verification; must not read RTL)
6. Implement it from `ARCHITECTURE.md` and `ISA.md` (the YAML once it exists), token-level and cycle-accurate. Architecture parameters (lanes, slots, registers, constants, fire rate, D-007 features) are configurable, so §2.0 can compare variants:
   - producer registers and consumer ports;
   - lanes (EVAL/EXEC, pending flags, output reservation);
   - routines and the SRAM rotation;
   - pin units (synchronisers, cursors, TX/RX modes);
   - helpers;
   - the host controller.
7. The host API matches the planned RTL host protocol: load, run/halt/step, read debug, FIFOs.
8. Waveform output: write pad activity to VCD so sigrok can decode model runs.
9. Unit tests for the model itself (pytest).

### 2.3 Compiler `tripc` v0 (owner: tools)
10. Define the minimal TRIPWIRE language (`.trw`): channel graph, reflexes, routines, pin-unit config.
11. `tripc` produces slot images, SRAM image, fabric/pin config writes and a **report**: slot and SRAM usage, routine worst-case steps, and urgent-reflex reaction bounds. The deadlock/overrun analysis comes in phase 3.
12. Write `programs/uart.trw`, `programs/spi_ctrl.trw` and `programs/i2c_ctrl.trw`. Run them on `tripsim` against the protocol reference models (`tools/protomodels`), and check the model's VCD with **sigrok decoders**.

### 2.4 Risk tests (owner: physical/CI + RTL)
13. **R1, lane timing.** Write a throwaway RTL for **one lane**: 12 slots, EVAL/EXEC, ALU, predicate logic, fed by dummy ports. Run Yosys synthesis with the cmos5l liberty and OpenSTA, or a 2x2 CI hardening. Report the EVAL critical path at 20 ns.
    - **Decision:** fire every clock, or fall back to every other clock.
14. **R2, latch slot array.** Harden a small project (2x2) containing the latch slot array through the TT flow: precheck and `gl_test`.
    - **Decision:** latches, or 8 flop slots per lane.
15. **R3, SRAM macro.** A 2x2 smoke project with the 512x16 macro using the recipe in `../PHYSICAL_DESIGN_AND_CI.md` §3: precheck and `gl_test` with a walking-ones test.
    - **Decision:** macro, or fallback store.
16. Record all three results in `DECISIONS.md` and `docs/reports/AREA.md`.

---

## 3. Deliverables
- `spec/tripwire.yaml`, `tools/gen`, and generated files committed.
- `ARCHITECTURE.md` with no OPEN items and a cycle-exact semantics section.
- `tools/tripsim` with tests; `tools/tripc` v0; `tools/protomodels` (UART/SPI/I2C).
- `programs/uart.trw`, `spi_ctrl.trw`, `i2c_ctrl.trw` passing on the model, including sigrok checks.
- Three risk-test reports with decisions.

---

## 4. Phase exit checklist (all must pass)
- [ ] `docs/reports/ARCH_EXPLORATION.md` answers every row of `ISA.md` §9 with measured numbers; resulting ISA changes are logged in `DECISIONS.md`.
- [ ] `ARCHITECTURE.md` and `ISA.md` have **zero OPEN items**; the semantics section is reviewed by at least two people.
- [ ] `spec/tripwire.yaml` is the only place encodings live; the `lint` CI regenerates and shows no diff.
- [ ] `tripsim` passes its own unit tests (every op, the channel rules, the pending rule, the rotation, pin-unit modes).
- [ ] UART (TX+RX), SPI controller and I2C controller programs run on `tripsim` and pass:
  - [ ] against the protocol reference models;
  - [ ] against **sigrok** decoding of the model's VCD.
- [ ] `tripc` report produced for all three programs, and slot usage fits (≤ 12 per lane).
- [ ] **R1 decided:** EVAL path timing measured; fire rate chosen and logged.
- [ ] **R2 decided:** the latch-array test project passed precheck and `gl_test`, or the flop fallback is chosen and logged.
- [ ] **R3 decided:** the SRAM smoke project passed precheck and `gl_test`, or the fallback is chosen and logged.
- [ ] Jane Street answers logged, or the assumptions stated.
- [ ] All CI workflows still green on `main`.

## 5. Risks in this phase
| Risk | Response |
|---|---|
| The spec keeps changing | Timebox; anything unresolved on Oct 14 takes the simplest option and a DECISIONS entry |
| Model and RTL authors drift apart | Everything goes through the semantics section; questions become spec edits, not private agreements |
| A risk test fails | Take the documented fallback; don't debug the flow for more than 3 days on one risk |