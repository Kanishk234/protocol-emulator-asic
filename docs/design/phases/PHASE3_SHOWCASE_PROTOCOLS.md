# Phase 3: showcase protocols and verification depth

| | |
|---|---|
| **Dates** | Nov 9 → Nov 29, 2026 |
| **Goal** | Demonstrate what makes TRIPWIRE different (fast device emulation, multicast, fixed reaction) with more protocols, and build the novel verification layers: independent oracles, metamorphic tests, core formal proofs and the compiler's deadlock/overrun analysis. Make the `fpga` workflow green with a reduced build. |
| **Devices needed** | None. The `fpga` workflow builds a bitstream without a board. Phase 7 is where a board comes in, if one becomes available. |
| **References** | `../ARCHITECTURE.md` §7–8, 13; `../VERIFICATION.md` §6 (L3–L6); `../PHYSICAL_DESIGN_AND_CI.md` §8 |

---

## 1. Entry criteria
- Phase 2 exit checklist passed.

## 2. Tasks

### 2.1 Protocol programs (owner: tools/firmware)

| Program | Key checks | Oracles |
|---|---|---|
| `i2c_target_eeprom.trw` (24C02-style, uses MEM) | Address match/ignore, pointer, sequential read/write, **ACK deadline at 400 kHz and 1 MHz** | Model, sigrok `i2c`, **third-party I2C controller RTL** |
| `spi_target_flash.trw` (READ, FAST_READ) | Max SCK, dummy cycles | Model, sigrok `spi` / `spiflash` |
| `onewire_master.trw` (standard + overdrive) | Reset/presence, ROM commands | Model, sigrok `onewire_link` / `onewire_network` |
| `ps2_rx.trw` | Framing, parity | Model, sigrok `ps2` |
| `ws2812.trw`, `dshot.trw` (PULSE mode) | Pulse widths within spec | Timing checker |
| `uart_bridge_capture.trw` | UART RX multicast to lane **and** CAPTURE tap; TX loopback | Demonstrates multicast + tap with zero lane cost |

- Adopt the ACK-path improvement noted in `ARCHITECTURE.md` §13 (preload the 1-bit SETN) and confirm the reaction bound in the compiler report.

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
8. A reduced-build parameter set: 1 lane, 8 slots, 2 pin units, SRAM mapped to FPGA RAM.
9. Make the `fpga` workflow build it, or add our own `fpga_reduced` workflow if the template's action can't select the reduced build (`../PHYSICAL_DESIGN_AND_CI.md` §8). Log the decision.

### 2.7 Hardening
10. Harden **each** RTL change from this phase separately, one change per run. Log AREA rows.

---

## 3. Deliverables
- Six new protocol programs with passing pin-level tests.
- Peer co-simulation and dumps replay in CI.
- L4 metamorphic suite; the listed formal proofs in `formal/`.
- `tripc` deadlock/overrun analysis + L6-FUZZ.
- Green `fpga` build (template or ours).

---

## 4. Phase exit checklist (all must pass)
- [ ] I2C target (EEPROM) passes at **400 kHz and 1 MHz**; its ACK deadline is met in every run and matches the compiler's reported bound.
- [ ] SPI target, 1-Wire, PS/2, WS2812 and DShot programs pass their L3 tests in RTL **and** `gl_test`.
- [ ] Every L3 protocol is checked by **sigrok** in addition to our own model.
- [ ] **L3B-PEER:** our I2C target interoperates with a third-party I2C controller core.
- [ ] **L3B-DUMPS:** at least one real capture each for UART, I2C and SPI decodes identically to sigrok.
- [ ] **L4:** all five metamorphic relations pass for UART, SPI and I2C.
- [ ] **Formal:** F-CHAN-1..4, F-SCHED-1..2, F-ROT-1, F-OWN-1, F-PIN-1, F-HOST-1 and F-DEC-1 proven, with each result's bounded/unbounded status recorded in `CLAIMS.md`.
- [ ] `tripc` deadlock/overrun analysis in place; L6-FUZZ has run ≥ 10⁴ random programs with no contradiction.
- [ ] `fpga` workflow (or `fpga_reduced`) green.
- [ ] The latest `gds` run is fully green (gds, precheck, gl_test, viewer); routing < 4 h.
- [ ] `formal` and `unit` workflows green on `main`.

## 5. Risks in this phase
| Risk | Response |
|---|---|
| A third-party core doesn't fit our testbench | Try a second core; if none works, record the attempt and rely on sigrok + dumps |
| Formal proofs don't converge | Reduce the scope (fewer consumers, narrower tokens), prove by induction on the abstract version, state the reduction |
| Slot pressure (a program doesn't fit in 12) | Move non-urgent logic into routines; split across lanes via channels |