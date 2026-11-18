# Phase 3: showcase protocols and verification depth

| | |
|---|---|
| **Dates** | Started November 18, 2026; original November 29 target needs review against remaining exit gates |
| **Goal** | Demonstrate what makes TRIPWIRE different (fast device emulation, multicast, fixed reaction) with more protocols, and build the novel verification layers: independent oracles, metamorphic tests, core formal proofs and the compiler's deadlock/overrun analysis. Build the full design for the Basys 3 FPGA (D-022). |
| **Devices needed** | None. The Basys 3 bitstream builds without a board. Phase 7 is where a board comes in, if one becomes available. |
| **References** | `../ARCHITECTURE.md` §7–8, 13; `../VERIFICATION.md` §6 (L3–L6); `../PHYSICAL_DESIGN_AND_CI.md` §8 |

---

## 1. Entry criteria
- [x] Phase 2 exit checklist passed; cleanup publication CI green on 82fef00 (test 44261361247, unit 44261361115, lint 44261361015, docs 44261360970, repo-audit 44261361423; nightly 44346919822).

## Planning corrections before implementation

Phase 2 closed November 18 on 8×4, two lanes and four units. The original dates below are planning targets, not completion evidence. MEM and CAPTURE helpers remain deferred by ARCHITECTURE §8; showcase programs must first use existing primitives and SRAM routines. Any helper proposal requires a separate architectural decision and approval before implementation. The stock `fpga` workflow targets the Tiny Tapeout template board; it is not evidence of a Basys 3 build.

## Immediate execution order

1. Correct the ACK setup oracle, add adversarial controls, and revalidate model/RTL/exact official-netlist timing. Completed locally; see `phase3_i2c_ack_revalidation.json` and the memory report. This is a Phase 3 verification correction, not a Phase 2 rollback.
2. Add explicit recovery scenarios beyond the existing complete-byte NACK/STOP cases. In progress: 22 model cases and four representative RTL/exact official-netlist cases pass; the late-byte STOP gap is tracked in [the recovery report](../../reports/PHASE3_I2C_RECOVERY.md). No exhaustive recovery claim.
3. Establish context-specific compiler reaction bounds; continue formal proofs against the actual RTL.
4. Consider any hardware feasibility branch only after a measured workload demonstrates the missing capability. No second PULSE unit or architecture change is approved by this plan.

## Current implementation inventory

The first new firmware personality is `i2c_target_eeprom.trw`; see [its scope and evidence](../../reports/PHASE3_I2C_MEMORY.md). The existing `onewire.trw`, `ps2_host.trw`, `ws2812.trw` and `dshot.trw` already have model/RTL/routed scenarios from Phase 2; audit the additional Phase 3 requirements rather than recreating those programs. L3B-PEER now passes on an independent controller; see [the evidence](../../reports/PHASE3_I2C_PEER.md). SPI flash, the UART multicast showcase, capture replay, metamorphic coverage, formal proofs, compiler analysis and the Basys 3 build remain open. D-021 still records the Hardcaml H0 import decision as not run; resolve it before any conditional H1 work. See [the in-progress summary](../../summaries/PHASE3.md).

## 2. Tasks

### 2.1 Protocol programs (owner: tools/firmware)

| Program | Key checks | Oracles |
|---|---|---|
| `i2c_target_eeprom.trw` (24C02-style, using existing SRAM routines) | Address match/ignore, pointer, sequential read/write, **ACK deadline at 400 kHz and 1 MHz** | Model, sigrok `i2c`, **third-party I2C controller RTL** |
| `spi_target_flash.trw` (READ, FAST_READ) | Max SCK, dummy cycles | Model, sigrok `spi` / `spiflash` |
| `onewire_master.trw` (standard + overdrive) | Reset/presence, ROM commands | Model, sigrok `onewire_link` / `onewire_network` |
| `ps2_rx.trw` | Framing, parity | Model, sigrok `ps2` |
| `ws2812.trw`, `dshot.trw` (PULSE mode) | Pulse widths within spec | Timing checker |
| `uart_bridge_capture.trw` | UART RX multicast and TX loopback; a SRAM capture helper remains deferred | Demonstrates multicast; measure actual lane cost |

- Confirm the ACK reaction bound in the compiler report. Current I2C firmware already uses length-in-token for a single-bit ACK without a separate SETN token; assess that actual path rather than adding the older illustrative SETN sequence.

### 2.2 Independent oracles (owner: verification)
1. **L3B-PEER:** integrate at least one third-party I2C core (controller role) and co-simulate it against our I2C target. Check the licence and record the source.
2. **L3B-DUMPS:** script to fetch selected `sigrok-dumps` captures (UART, I2C, SPI, 1-Wire), convert them to pin stimulus and replay into our RX programs. Our decode must equal sigrok's decode of the same file.

### 2.3 Metamorphic tests (L4)
3. L4-LOOP, L4-SCALE, L4-PERM, L4-IDLE, L4-TAP, each for at least UART, SPI and I2C.

### 2.4 Formal (L5, owner: verification)
4. Prove:
   - **F-CHAN-1..4**
   - **F-SCHED-1, F-SCHED-2**
   - **F-ROT-1**
   - **F-OWN-1**
   - **F-PIN-1**
   - **F-HOST-1**
   - **F-DEC-1**

   Unbounded where the table in `VERIFICATION.md` says so.
5. Start **F-SCHED-3** (pin-to-pin ≤ 7 clocks) and **F-ISO-1** (lane isolation). Bounded results are acceptable; state the depth.

### 2.5 Compiler analysis (L6)
6. Add to `tripc`: **deadlock/overrun analysis** for fixed-rate channel graphs, and a warning for data-dependent graphs.
7. **L6-FUZZ:** random programs through `tripc` → `tripsim`. Any program marked deadlock-free must never deadlock in simulation, and every reported reaction bound must be met.

### 2.6 FPGA build (owner: physical/CI)
8. An FPGA synthesis define (slot latches → flops, SRAM → block RAM, MMCM 100 → 50 MHz) and a Basys 3 constraints file. The **full** design, not a reduced one (DECISIONS D-022).
9. Build it for the Basys 3: our own `fpga_basys3` workflow (openXC7) or a local Vivado script with its report in `docs/reports/` (`../PHYSICAL_DESIGN_AND_CI.md` §8). Record the choice in D-022.

### 2.7 Hardening
10. Harden **each** RTL change from this phase separately, one change per run. Log AREA rows.

### 2.8 Extra cross-checks (D-021, owner: verification)
11. **L8-EQY** and **L8-XPROP** in CI (the `formal` and `gds` artefacts respectively).
12. **L9 H1** (if H0 = go):
    - waveform expect tests for the 7-clock reaction, the channel handshake, the pin cursor/LATE and the rotation;
    - pin-level UART/SPI/I2C tests from OCaml;
    - the `hardcaml` workflow.
13. **L9 H2:** start the independent OCaml model of the scheduler and fabric. Its author reads neither `tools/tripsim` nor `src/`.

---

## 3. Deliverables
- Six new protocol programs with passing pin-level tests.
- Peer co-simulation and dumps replay in CI.
- L4 metamorphic suite; the listed formal proofs in `formal/`.
- `tripc` deadlock/overrun analysis + L6-FUZZ.
- A full-design Basys 3 bitstream (D-022).

---

## 4. Phase exit checklist (all must pass)
- [ ] I2C target (EEPROM) passes at **400 kHz and 1 MHz**; its ACK deadline is met in every run and matches the compiler's reported bound.
- [ ] SPI target, 1-Wire, PS/2, WS2812 and DShot programs pass their L3 tests in RTL **and** `gl_test`.
- [ ] Every L3 protocol is checked by **sigrok** in addition to our own model.
- [x] **L3B-PEER:** our I2C target interoperates with a third-party I2C controller core. *(2026-11-18: unmodified MIT-licensed verilog-i2c a65be404; Verilator, Icarus and exact official final netlist each pass both profiles, including measured 1 MHz, required sigrok, wrong-address NACK and wrap checks. Evidence: [peer report](../../reports/PHASE3_I2C_PEER.md), phase3_i2c_peer_result.json. Simulation scope only.)*
- [ ] **L3B-DUMPS:** at least one real capture each for UART, I2C and SPI decodes identically to sigrok.
- [ ] **L4:** all five metamorphic relations pass for UART, SPI and I2C.
- [ ] **Formal:** F-CHAN-1..4, F-SCHED-1..2, F-ROT-1, F-OWN-1, F-PIN-1, F-HOST-1 and F-DEC-1 proven, with each result's bounded/unbounded status recorded in `CLAIMS.md`.
- [ ] `tripc` deadlock/overrun analysis in place; L6-FUZZ has run ≥ 10⁴ random programs with no contradiction.
- [ ] Full-design Basys 3 bitstream builds with timing met at 50 MHz: `fpga_basys3` run ID, or the local Vivado report in `docs/reports/` (D-022).
- [ ] The latest `gds` run is fully green (gds, precheck, gl_test, viewer); routing < 4 h.
- [ ] `formal` and `unit` workflows green on `main`.

## 5. Risks in this phase
| Risk | Response |
|---|---|
| A third-party core doesn't fit our testbench | Try a second core; if none works, record the attempt and rely on sigrok + dumps |
| Formal proofs don't converge | Reduce the scope (fewer consumers, narrower tokens), prove by induction on the abstract version, state the reduction |
| Slot pressure (a program doesn't fit in 12) | Move non-urgent logic into routines; split across lanes via channels |