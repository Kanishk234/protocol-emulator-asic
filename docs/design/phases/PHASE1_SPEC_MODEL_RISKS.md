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
- [x] `docs/reports/ARCH_EXPLORATION.md` answers every row of `ISA.md` §9 with measured numbers; resulting ISA changes are logged in `DECISIONS.md`. *(Evidence, 2026-09-23: ARCH_EXPLORATION §1 rows for slots, registers + K, OP 15, the D-007 ablation, R1 fallback, TX/RX NBITS, routine rate; §1a table from `python -m explore.metrics`; R1 fallback: `TRIPSIM_FIRE_PERIOD=2 pytest tools/kernels/tests` 103 passed, now the `nightly` `r1-fallback` job. Decisions: D-009, D-020, D-029 (accepted).)*
- [x] `ARCHITECTURE.md` and `ISA.md` have **zero OPEN items**; the semantics section is reviewed by at least two people. *(Evidence, 2026-09-24: zero OPEN items since D-029 (`grep OPEN` finds only the intro's rule for new items). §14 reviewed by Kanishk (D-035: gaps G9–G24, BUGS #35–#37) and by Krithik, who accepted D-035; the R1 spike's gaps G1–G8 are in D-033; the model-side second pass over P20–P29 found G25–G31 and BUGS #38–#39 (D-035 outcome). All answered in §14; `tools/tripsim/tests/test_semantics.py`.)*
- [x] `spec/tripwire.yaml` is the only place encodings live; the `lint` CI regenerates and shows no diff. *(2026-09-24: the pin-unit configuration registers, the last encodings outside it, were added with D-036; the spec is frozen as v1.0, D-037. Evidence: `lint` run 35921199653 and `unit` run 35921199432 green on 0e0028d, 2026-09-23. tripsim imports the generated tables; `tools/gen/tests/test_gen.py::test_model_uses_the_spec`.)*
- [x] `tripsim` passes its own unit tests (every op, the channel rules, the pending rule, the rotation, pin-unit modes). *(Evidence, 2026-09-23, local pytest 117 passed: `tools/tripsim/tests/`. Every op: `test_isa.py`; channel rules incl. tap drops, filters: `test_fabric.py`, `test_pins.py::test_consumer_port_tag_filter`; pending rule and rotation: `test_lane.py`; pin modes: LEVEL/OE/SYNC/LATE, SETN, SHIFT, SHIFT_RX, PULSE (pulse-width, pulse-distance, Manchester), edge events, `test_pins.py`; linked/CLKGEN/STRETCH/WAIT/pin C via `tools/kernels/tests/`. Injected PULSE bugs are caught.)*
- [x] UART (TX+RX), SPI controller and I2C controller programs run on `tripsim` and pass: *(Evidence, 2026-09-23, local `python -m pytest -q`: 106 passed. Programs `programs/uart.trw`, `spi_controller.trw`, `i2c_controller.trw` compiled by tripc: `tools/kernels/tests/test_uart.py`, `test_spi_controller.py`, `test_i2c_controller.py` against `tools/protomodels/` (UART line model, SPI target, I2C target); confirmed in CI by the `unit` workflow on the next push.)*
  - [x] against the protocol reference models; *(UART: `protomodels/uart.py` decode/encode incl. a framing error and a 256-byte loopback; SPI: `protomodels/spi.py` SPITarget; I2C: `protomodels/i2c.py` I2CTarget with clock stretching.)*
  - [x] against **sigrok** decoding of the model's VCD. *(`test_uart_tx` (uart), `test_spi_controller_sigrok` (spi), `test_i2c_controller_sigrok` (i2c).)*
- [x] `tripc` report produced for all three programs, and slot usage fits (≤ 12 per lane). *(`tools/tripc/tests/test_tripc.py::test_reports_and_slot_budget` over all `programs/*.trw`: uart 4, spi_controller 4, i2c_controller 11 + 2 bounded routines; plus spi_target 3, i2c_target 12.)*
- [x] **R1 decided:** EVAL path timing measured; fire rate chosen and logged. *(Evidence, 2026-09-24: `spikes/r1_lane/run_r1.sh`, `docs/reports/R1_LANE_TIMING.md`: EVAL ≤ 7.5 ns typ, ≤ 11.7 ns slow at 20 ns, worst slack +7.9 ns across the re-runs (corrected after the §14 L8 re-run), before layout. Fire rate "every clock": D-030, accepted 2026-09-24. Rechecked against R2's post-route slack.)*
- [x] **R2 decided:** the latch-array test project passed precheck and `gl_test`, or the flop fallback is chosen and logged. *(Evidence, 2026-09-24: `gds` run 36060938609 on `spike/r2-latch` (c4ef059): gds, precheck, gl_test green; latch slots kept (D-032, D-034); `AREA.md` row 3. Post-route EVAL slack +6.94 ns at the slow corner confirms D-030.)*
- [x] **R3 decided:** the SRAM smoke project passed precheck and `gl_test`, or the fallback is chosen and logged. *(Evidence, 2026-09-24: `gds` run 35961480554 on `spike/r3-sram` (09e8697): gds, precheck, gl_test green; the macro is kept (D-031). Project: `spikes/r3_sram/`.)*
- [x] Jane Street answers logged, or the assumptions stated. *(DECISIONS D-003: design for 6x4; SRAM macro assumed usable, settled by R3 with the flop-store fallback kept.)*
- [ ] All CI workflows still green on `main`.

## 5. Risks in this phase
| Risk | Response |
|---|---|
| The spec keeps changing | Timebox; anything unresolved on Oct 14 takes the simplest option and a DECISIONS entry |
| Model and RTL authors drift apart | Everything goes through the semantics section; questions become spec edits, not private agreements |
| A risk test fails | Take the documented fallback; don't debug the flow for more than 3 days on one risk |