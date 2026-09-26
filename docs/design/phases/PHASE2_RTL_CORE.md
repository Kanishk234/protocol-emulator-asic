# Phase 2: RTL core

| | |
|---|---|
| **Dates** | Oct 19 → Nov 8, 2026 (planned). Started early, on 2026-09-25, when phase 1 closed. |
| **Goal** | The full TRIPWIRE RTL (lanes, fabric, pin units, SRAM rotation, host port) passing unit tests and lockstep against the model. The required protocols (UART, SPI controller, I2C controller) work through the pins in RTL *and* at gate level. First full 6x4 hardening. |
| **Devices needed** | None |
| **References** | `../ARCHITECTURE.md` (spec v1.0, frozen by D-037), `../VERIFICATION.md` §5–6, `../PHYSICAL_DESIGN_AND_CI.md`, `../../reports/R1_LANE_TIMING.md`, `../../reports/AREA.md` |

**Updated 2026-09-25 with phase 1's findings:**
- the helper units are deferred (D-029), so they are out of this phase;
- the pin units gained PULSE, BITSYNC, carrier, NRZI and the other D-019 to D-027 features;
- R2 and R3 fixed three physical-design inputs (latch SDC exception, local density ~42 % for the slot arrays, the SRAM macro);
- the pin-unit settings turned out large (D-036), so an area estimate comes before the RTL (task 2.0).

---

## 1. Entry criteria
- [x] Phase 1 exit checklist passed: spec frozen (v1.0, D-037), model working, risk decisions made (D-030, D-031, D-034). *(Evidence: `PHASE1_SPEC_MODEL_RISKS.md`, all boxes ticked; CI green on `367aacc`.)*

## 2. Tasks

### 2.0 Area estimate and budget (first, before the RTL)
Phase 1 left three area questions open. Answering them now is cheaper than after the RTL is written:
- whether all six pin units need every option (D-036: 307 configuration bits per unit, 112 of them BITSYNC/CRC);
- whether the host keeps the slot read-back port (~9.4K µm² per lane, D-032);
- how much of the 902K µm² core the design may use, given that the R2 slot array needed a local placement density near 42 %.

Tasks:
1. Synthesize representative building blocks (timers, shift registers, CRC, pad muxes, configuration storage, fabric ports) onto the cmos5l cells. Count how many of each block every part of the chip needs, from the spec, and add up an area per part.
2. Set a budget per part against a utilisation that R2 showed will route.
3. Price the options (heterogeneous pin units, slot read-back, configuration storage in latches, 2 lanes) and record them in `docs/reports/AREA_ESTIMATE.md`.
4. Any change to the frozen spec goes through a DECISIONS entry.

**Status (2026-09-25):** estimate done (`docs/reports/AREA_ESTIMATE.md`). The frozen spec came to ~115 % of the core. Tier 1 decided: D-038 (configuration in latches), D-039 (slots, K and configuration write-only), D-040 (U0–U1 full, U2–U5 lean), which brings it to ~87 %. Next: write and synthesize `trw_pin_unit` first, to replace the estimate's biggest guess, then choose the next cuts (AREA_ESTIMATE §8).

### 2.1 RTL (owner: architecture/RTL; written from the spec, not from `tripsim`)

| Module | Contents |
|---|---|
| `trw_sync.v` | 2-FF synchronisers for all inputs |
| `trw_chan_prod.v`, `trw_chan_port.v` | Producer register (valid/tag/data/seq) and consumer port (sel/en/mode/accept/last_seq, DROPPED); registered release per `ARCHITECTURE.md` §4 and §14 F1–F7 |
| `trw_fabric.v` | Instantiates all producers and ports and the per-consumer legal-source muxes (§4.6, generated table) |
| `trw_slots.v` | Latch slot array (D-034) with library clock gates, plus K0–K3; host write path. No read-back port (D-039) |
| `trw_lane.v` | EVAL (conditions, priority, static updates, pending, reservation), EXEC (operand mux, ALU, writeback), routine controller (RPC, RIR, RB, interruption, CALL), STEP, host register writes (§14 L, R, H rules) |
| `trw_alu.v` | The 16 operations |
| `trw_sram.v` | IHP 512x16 macro wrapper (D-031) plus the fixed 4-way rotation |
| `trw_pin_unit.v` | Parameterised full (U0–U1) or lean (U2–U5, no PULSE, carrier or BITSYNC; D-040). Everything in `ARCHITECTURE.md` §7 and the §14 P-rules: the configuration registers of §7.2 (D-036); TX modes LEVEL, SHIFT, CLKGEN (with STRETCH), PULSE and BITSYNC; the cursor and LATE; CTRL ops 1–11; carrier; RX modes SHIFT_RX, LINKED_RX and BITSYNC (resync, SJW, stuffing, CRC, readback, JAM, NRZI, frame delimiters); the event generator; OVERRUN; pins A, B, C, S and N. Split into sub-modules as needed (`trw_pin_*`) |
| `trw_pin_cfg.v` | Pin configuration latch array (D-038): the §7.2 blocks, write-only (D-039); U2–U5 store only their core fields (D-040) |
| `trw_pins.v` | Pin owner registers, open-drain handling, pad mapping |
| `trw_host.v` | SPI slave, command FSM, the §9 address spaces (including the §7.2 pin configuration and the lane register block), run/halt/step, debug readback, IRQ, HOST_IN/HOST_OUT |
| `tt_um_tripwire.v` | Top level: pad mapping, `_unused` wire |

Not in this phase: the helper units CRC, MATCH, MEM and CAPTURE (deferred by D-029; they return only through a new DECISIONS entry).

**Starting points:**
- The R1 lane (`spikes/r1_lane/`) was written from the spec alone and may seed `trw_lane.v`, `trw_alu.v` and `trw_slots.v`. It must first change `KT` to follow §14 L8 (D-033), and it must be re-checked against the D-035 rule changes.
- `tools/gen/gen.py` has no Verilog output for the pin configuration layout yet. Add one, so the RTL takes the §7.2 addresses and fields from `spec/tripwire.yaml` and not a hand copy.

**Coding rules:**
- Verilog-2005 subset accepted by Icarus, Verilator, Yosys and LibreLane.
- `default_nettype none`; synchronous active-low reset; no `initial` in synthesisable code.
- Latches only in `trw_slots.v` and `trw_pin_cfg.v` (D-038).
- Every module header states its timing contract.

### 2.2 Verification (owner: verification)
1. **L0:** lint and synthesis-sanity CI green.
2. **L1:** unit tests in `test_internal/` (see the table in `VERIFICATION.md` §6; L1-CRC and L1-MEM are deferred with the helpers). Add a BITSYNC case to L1-PIN-TX and L1-PIN-RX: stuffing, CRC, resync, readback, JAM.
3. **pyuvm environment** skeleton:
   - host agent;
   - UART, SPI and I2C pin agents;
   - sigrok checker;
   - model scoreboard (lockstep through debug taps).
4. **L2 lockstep:** random programs plus stimulus, RTL against `tripsim` every clock. Reach ≥ 10⁶ compared clocks clean. Run the injected-bug check (L2-INJECT).
5. **L3 (pin-level, `test/`):** L3-UART, L3-SPI-C, L3-I2C-C, each against a reference model **and** sigrok.
6. Keep `test/` **gate-level safe**: top-level ports only.

### 2.3 Tools
7. `tools/host`: host library that drives the host SPI protocol. The same API is used by the testbench and, later, real hardware.
8. `tripc`: produces host-write sequences directly usable by the testbench. The image already carries slot words, K, registers and `pin_regs`; add the fabric port registers and the owner registers.

### 2.4 First full hardening (owner: physical/CI)
9. Integrate the SRAM macro config (the R3 recipe, D-031) into `config.json` for 6x4.
10. Move the latch SDC exception from R2 (`PNR_SDC_FILE` with a false path to the latch data pins, D-032) to `main`, with its own DECISIONS entry. Without it the post-CTS resizer spends hours on the latch pins.
11. Set the placement density from task 2.0 and the R2 result (the slot arrays needed ~42 % locally), with a DECISIONS entry.
12. Run `gds`. Record cells, utilisation, WNS (typ/slow/fast), Metal3/total overflow, routing time and total time in `docs/reports/AREA.md`.
13. If routing time is > 4 h or overflow is high, apply the knobs in `../PHYSICAL_DESIGN_AND_CI.md` §5 **before** adding anything else.

### 2.5 Extra cross-checks (D-021, owner: verification)
14. **L0-ASRT:** a `TRW_ASSERT` macro (assert under `FORMAL`, `$fatal` check under `SIM_ASSERT`); first invariants in the fabric and the pin mux.
15. **L-XSIM:** run `test/` and `test_internal/` under both Icarus and Verilator.
16. **L8-EQY feasibility:** try eqy on one module against its cmos5l netlist; log whether the cell models work, or choose the fallback.
17. **L9 H0 spike:**
    - pin an opam switch with Hardcaml;
    - import the channel producer/consumer with `hardcaml_of_verilog`;
    - run one Cyclesim waveform expect test.

    Log go or no-go in DECISIONS.

---

## 3. Deliverables
- `docs/reports/AREA_ESTIMATE.md` and the budget decisions it leads to.
- Complete RTL in `src/`; `info.yaml` source list in sync with `test/Makefile`.
- `test_internal/` unit tests, the pyuvm environment, L2 lockstep, `test/` pin-level L3 tests.
- First 6x4 hardening with an AREA row.
- Bugs logged in `BUGS.md` with the check ID that caught each.

---

## 4. Phase exit checklist (all must pass)
- [ ] Area estimate done (`docs/reports/AREA_ESTIMATE.md`) and its budget decisions recorded in DECISIONS. *(Estimate done; tier 1 decided (D-038–D-040); open until the design fits a routable budget.)*
- [ ] All modules in the table exist and lint clean (`verilator --lint-only -Wall`); latches only where allowed, waived.
- [ ] **L1** unit tests all green (ALU, EVAL, PIPE, CHAN, OVR, PIN-TX, PIN-RX including BITSYNC, ROT, HOST).
- [ ] **L2** lockstep ≥ 10⁶ clocks with zero divergences; L2-INJECT catches both injected bugs.
- [ ] **L3-UART, L3-SPI-C, L3-I2C-C** pass in RTL against reference models and **sigrok**.
- [ ] The same L3 tests pass in **`gl_test`** on the hardened netlist.
- [ ] Full 6x4 `gds` run: DRC/LVS/antenna clean, precheck green, timing met at the typical corner, routing < 4 h.
- [ ] `viewer` deployed; Pages shows the real design.
- [ ] `test`, `docs`, `lint`, `unit` workflows green on `main`.
- [ ] `docs/reports/AREA.md` has the first full-design row.
- [ ] Every bug found so far is in `BUGS.md`.

## 5. Risks in this phase
| Risk | Response |
|---|---|
| The design does not fit at a routable density | Task 2.0 first. Options, cheapest first: drop the slot read-back port, heterogeneous pin units, configuration storage in latches, 2 lanes |
| Lockstep divergences that are spec ambiguities | Fix the semantics section first, then model and RTL; log a DECISIONS entry |
| Routing blow-up on the first hardening | Restrict connectivity, lower density, or drop to 2 lanes before continuing |
| Gate-level failures (X after reset) | Add resets; treat as RTL bugs |
