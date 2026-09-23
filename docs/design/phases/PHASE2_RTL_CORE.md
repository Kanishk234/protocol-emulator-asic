# Phase 2: RTL core

| | |
|---|---|
| **Dates** | Oct 19 → Nov 8, 2026 |
| **Goal** | The full TRIPWIRE RTL (lanes, fabric, pin units, helpers, SRAM rotation, host port) passing unit tests and lockstep against the model. The required protocols (UART, SPI controller, I2C controller) work through the pins in RTL *and* at gate level. First full 6x4 hardening. |
| **Devices needed** | None |
| **References** | `../ARCHITECTURE.md`, `../VERIFICATION.md` §5–6, `../PHYSICAL_DESIGN_AND_CI.md` |

---

## 1. Entry criteria
- Phase 1 exit checklist passed: spec frozen, model working, risk decisions made.

## 2. Tasks

### 2.1 RTL (owner: architecture/RTL; written from the spec, not from `tripsim`)

| Module | Contents |
|---|---|
| `trw_sync.v` | 2-FF synchronisers for all inputs |
| `trw_chan_prod.v`, `trw_chan_port.v` | Producer register (valid/tag/data/seq) and consumer port (sel/en/mode/last_seq); release logic per `ARCHITECTURE.md` §4 |
| `trw_fabric.v` | Instantiates all producers and ports and the per-consumer legal-source muxes (generated table) |
| `trw_slots.v` | Latch (or flop) slot array; host write path |
| `trw_lane.v` | EVAL (conditions, priority, static updates, pending, reservation), EXEC (operand mux, ALU, writeback), routine controller (RPC, RB, interruption) |
| `trw_alu.v` | The 16 operations |
| `trw_sram.v` | Macro wrapper plus the fixed 4-way rotation arbiter; fallback implementation behind a parameter |
| `trw_pin_unit.v` | TX (cursor, LEVEL/OE/GAP/SYNC/CLK/SETN, SHIFT, CLKGEN with stretch, PULSE, LATE) and RX (SHIFT_RX + autorearm, LINKED_RX, EDGE_TS, COND_EDGE, OVERRUN) |
| `trw_pins.v` | Pin owner registers, open-drain handling, pad mapping |
| `trw_crc.v`, `trw_match.v`, `trw_mem.v`, `trw_capture.v` | Helper units |
| `trw_host.v` | SPI slave, command FSM, address spaces, debug readback, IRQ, FIFOs |
| `tt_um_tripwire.v` | Top level: pad mapping, `_unused` wire |

**Coding rules:**
- Verilog-2005 subset accepted by Icarus, Verilator, Yosys and LibreLane.
- `default_nettype none`; synchronous active-low reset; no `initial` in synthesisable code.
- Latches only in `trw_slots.v`.
- Every module header states its timing contract.

### 2.2 Verification (owner: verification)
1. **L0:** lint and synthesis-sanity CI green.
2. **L1:** unit tests in `test_internal/` (see the table in `VERIFICATION.md` §6).
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
8. `tripc`: produces host-write sequences directly usable by the testbench.

### 2.4 First full hardening (owner: physical/CI)
9. Integrate the SRAM macro config (or fallback) into `config.json` for 6x4.
10. Run `gds`. Record cells, utilisation, WNS (typ/slow/fast), Metal3/total overflow, routing time and total time in `docs/reports/AREA.md`.
11. If routing time is > 4 h or overflow is high, apply the knobs in `../PHYSICAL_DESIGN_AND_CI.md` §5 **before** adding anything else.

---

## 3. Deliverables
- Complete RTL in `src/`; `info.yaml` source list in sync with `test/Makefile`.
- `test_internal/` unit tests, the pyuvm environment, L2 lockstep, `test/` pin-level L3 tests.
- First 6x4 hardening with an AREA row.
- Bugs logged in `BUGS.md` with the check ID that caught each.

---

## 4. Phase exit checklist (all must pass)
- [ ] All modules in the table exist and lint clean (`verilator --lint-only -Wall`); latches only in `trw_slots.v`, waived.
- [ ] **L1** unit tests all green (ALU, EVAL, PIPE, CHAN, OVR, PIN-TX, PIN-RX, CRC, MEM, ROT, HOST).
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
| Lockstep divergences that are spec ambiguities | Fix the semantics section first, then model and RTL; log a DECISIONS entry |
| Routing blow-up on the first hardening | Restrict connectivity, lower density, or drop to 2 lanes before continuing |
| Gate-level failures (X after reset) | Add resets; treat as RTL bugs |