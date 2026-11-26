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
2. Add explicit recovery scenarios beyond the existing complete-byte NACK/STOP cases. The one-unit example's limited coverage and late-byte gap are tracked in [the recovery report](../../reports/PHASE3_I2C_RECOVERY.md). A separate two-unit firmware option exercises the existing select/abort primitive; see [its coverage and replay status](../../reports/PHASE3_I2C_GUARD.md). No exhaustive recovery claim.
3. Establish context-specific compiler reaction bounds; continue formal proofs against the actual RTL. The [local selection foundation](../../reports/PHASE3_REACTION_SELECTION.md) excludes incompatible competitors and handles both scheduler modes; it does not yet establish an end-to-end ACK clock bound.

   The [conditional ACK token queries](../../reports/PHASE3_ACK_TOKEN_BOUND.md) now check the lane-local compare/flag/submission chain (4 clocks for an address, 2 for write data) against both RTL simulators. Entry invariants, queues and pin scheduling remain outside these bounds; the exit gate remains open.

   The [linked-edge composition](../../reports/PHASE3_ACK_EDGE_BUDGET.md) now adds conservative RX/TX bounds: 8/6 clocks to arm address/write ACKs. Entry premises and deadlines pass 1,120 whole-model observations and 350 internal observations per RTL simulator; 40 port-only ACK checks pass on the exact qualified netlist. Universal queue/arrival and guard-window invariants remain unproved, so the exit gate stays open.

   The [memory-service envelope](../../reports/PHASE3_MEMORY_SERVICE.md) counts encoded SRAM accesses separately from execution steps. It corrects the old store estimate from 48 to 51 clocks; 6,144 model runs and 96 cases per RTL simulator cover the three memory routines. It assumes no reflex interference and does not yet close delimiter/arrival invariants.

   The [delimiter interference sweep](../../reports/PHASE3_DELIMITER_SERVICE.md) adds an explicit finite reflex budget: at most two selected actions gives a 59-clock store envelope. Model and both RTL simulators pass 1,616 injection cases each. Internal multicast/guard model observations and the routine-gated negative control are recorded separately. The wire-origin arrival premise and external-event-to-guard window remain open.

   The subsequent [wire-origin evidence review](../../reports/PHASE3_I2C_DEADLINE_EVIDENCE.md) checks every observed event and memory-service interval in 198 guarded workloads, closing the I2C demonstration checkpoint for the declared tested scope. General arrival proofs belong to the still-open deadlock/overrun analysis checkpoint; no unconditional traffic certificate is claimed. Move on to the remaining showcase and verification deliverables rather than requiring a new universal proof for this finite demonstration gate.
4. Consider any hardware feasibility branch only after a measured workload demonstrates the missing capability. No second PULSE unit or architecture change is approved by this plan.

## Current implementation inventory

The first new firmware personality is `i2c_target_eeprom.trw`; see [its scope and evidence](../../reports/PHASE3_I2C_MEMORY.md). The existing `onewire.trw`, `ps2_host.trw`, `ws2812.trw` and `dshot.trw` already have model/RTL/routed scenarios from Phase 2; audit the additional Phase 3 requirements rather than recreating those programs. L3B-PEER passes on an independent controller; see [the evidence](../../reports/PHASE3_I2C_PEER.md). The new SPI memory personality also passes model/RTL/exact-netlist checks in its declared scope. UART multicast now passes the model, both RTL simulators and exact-netlist replay under its host-service contract. [Three recorded-device replays](../../reports/PHASE3_RECORDED_CAPTURES.md) also pass model, both RTL simulators and exact-netlist checks. The finite D-191metamorphic checkpoint now passes; formal proofs, compiler analysis and the Basys 3 build remain open. D-021 still records the Hardcaml H0 import decision as not run; resolve it before any conditional H1 work. See [the in-progress summary](../../summaries/PHASE3.md).

Inventory review after the guarded I2C milestone:

| Showcase | Existing implementation/evidence | Remaining work |
|---|---|---|
| SPI memory target | New `spi_target_flash.trw` parses READ/FAST_READ and serves a volatile 256-byte SRAM window; model, both RTL simulators and exact official netlist pass; [evidence](../../reports/PHASE3_SPI_MEMORY.md) | Keep its tested 500 kHz limit distinct from the basic transport's rate. The combined protocol gate still requires the remaining showcase audits/extensions. |
| 1-Wire | Original standard image retained; `onewire_master.trw` passes standard/overdrive entry, ROM reads, exit and presence checks on model/both RTL simulators/exact official netlist; [evidence](../../reports/PHASE3_ONEWIRE_OVERDRIVE.md) | Retain ROM-layer/digital scope and the specifically audited decoder warning. Keep the separately recorded PS/2 replay status distinct from this completed milestone. |
| PS/2 | Unchanged `ps2_host.trw`; model start/parity/stop matrix and both RTL simulators pass; [raw-capture evidence](../../reports/PHASE3_PS2_FRAMING.md) | Exact-netlist replay passes 3/3 selected tests; recorder-only pulse removed and unmodified pinned upstream decoder used. Arbitrary partial/missing-clock recovery is outside this finite scope. |
| WS2812 / DShot | Existing PULSE firmware, timing decoders and routed transmit cases | Qualified test-function ASTs and emitted images match. Classic WS2812B table only; DShot has no installed sigrok decoder, so the separate decoder checkpoint remains open. |
| UART multicast | New `uart_bridge_capture.trw`, 3/2 slots, existing U0/U1, no SRAM routine; [evidence](../../reports/PHASE3_UART_MULTICAST.md) | Model, both RTL simulators and exact-netlist replay pass at 115200/460800. Host-drain contract is required; SRAM CAPTURE helper remains deferred. |

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
3. L4-LOOP, L4-SCALE, L4-PERM, L4-IDLE, L4-TAP, each for at least UART, SPI and I2C. The finite D-191scoped checkpoint now passes; see [final SCALE/native-phase evidence](../../reports/PHASE3_METAMORPHIC_SCALE_PHASE.md) and the exit checklist below.

   [Strict fast-path PERM progress](../../reports/PHASE3_METAMORPHIC_PERM.md):24raw-cycle comparisons cover UART, SPI controller and I2C target with declared legal lane/unit mappings; both RTL simulators and the exact official netlist pass3/3paired cases, with identical trace hashes and host checkpoints. A native routine-controller lane move is a retained counterexample unless the SRAM grant phase is matched. D-191was explicitly approved for timing-domain/phase wording; subsequent SCALE/hardware routine-phase evidence closes the finite checkpoint. Unrestricted raw scaling/unaligned invariance remains false and is not claimed.

   [Two-lane LOOP/IDLE progress](../../reports/PHASE3_METAMORPHIC_LOOP_IDLE.md):eight model profiles,24baseline/seeded runs and three disconnected-wire negatives pass with required sigrok. Both RTL simulators and the exact official netlist pass3/3paired protocol cases with no failures/skips. All six capture hashes/frame markers match across simulators. The full Python suite passes1,175tests. This earlier milestone is now combined with final SCALE/phase evidence to close the finite L4checkpoint.

   [L4-TAP progress](../../reports/PHASE3_METAMORPHIC_TAP.md):16positive whole-model pairs compare517,960clocks; three blocking-subscriber negatives are detected. Both RTL simulators and the exact official netlist pass3/3paired protocol cases with no failures/skips; trace hashes and host observation checkpoints match across simulators. The full Python suite passes1,164tests. The concrete UART scale audit distinguishes fixed launch latency from doubled bit intervals; D-191and subsequent SCALE/phase evidence resolve the finite checkpoint without claiming unrestricted global scaling.

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
- [x] I2C target (EEPROM) passes at **400 kHz and 1 MHz**; its ACK deadline is met in every run and matches the compiler's reported bound. *(2026-11-18: guarded volatile SRAM-backed personality; [deadline evidence](../../reports/PHASE3_I2C_DEADLINE_EVIDENCE.md), phase3_i2c_deadline_evidence.json. 828 Python tests; 198 guarded wire/service workloads, 1,586 matched delimiters and 2,354 routines; 4/2-clock lane and 8/6-clock arm bounds checked against actual entry premises. Prior Icarus/Verilator ACK checks and exact official-netlist replay remain bound to identical images in the linked receipts. Finite tested traffic scope, not universal deadlock/arrival proof, analog qualification or full EEPROM/NVM emulation. The original one-unit recovery gap remains documented.)*
- [x] SPI target, 1-Wire, PS/2, WS2812 and DShot programs pass their L3 tests in RTL **and** `gl_test`. *(2026-11-19: [SPI memory](../../reports/PHASE3_SPI_MEMORY.md), [1-Wire standard/overdrive](../../reports/PHASE3_ONEWIRE_OVERDRIVE.md), and [PS/2 framing/raw captures](../../reports/PHASE3_PS2_FRAMING.md), with hashed receipts. PS/2 passes 3/3 selected cases on both RTL simulators and exact official netlist; twenty unrelated cases filtered. WS2812/DShot retain unchanged test-function ASTs and compiled images, qualified RTL unit44189195981 and routed22-case44123392388 evidence. Classic WS2812B table and declared DShot rates/tolerances only. No universal interoperability, silicon or Phase3completion claim; independent-decoder checkpoint remains separate.)*
- [x] Every L3 protocol is checked by **sigrok** in addition to our own model. *(2026-11-26: required-sigrok routed replay 44123392388 plus targeted exact-baseline DShot, HDLC and NEC reruns, each 1/1 with zero failures/skips. [Coverage and receipts](../../reports/PHASE3_L3_DECODER_COVERAGE.md). Protocol-level coverage includes at least one exercised direction per protocol. DShot and HDLC combine independent sigrok edge measurements with separate packet checks.)*
- [x] **L3B-PEER:** our I2C target interoperates with a third-party I2C controller core. *(2026-11-18: unmodified MIT-licensed verilog-i2c a65be404; Verilator, Icarus and exact official final netlist each pass both profiles, including measured 1 MHz, required sigrok, wrong-address NACK and wrap checks. Evidence: [peer report](../../reports/PHASE3_I2C_PEER.md), phase3_i2c_peer_result.json. Simulation scope only.)*
- [x] **L3B-DUMPS:** at least one real capture each for UART, I2C and SPI decodes identically to sigrok. *(2026-11-19: complete STM32 UART/PCA9571 I2C/CC1101 SPI recordings pinned at sigrok-dumps0ad1347; [report](../../reports/PHASE3_RECORDED_CAPTURES.md), phase3_recorded_captures_result.json. Three replays pass on model, both RTL simulators and exact official netlist, no selected failures/skips. Original SR sigrok outputs match42UARTbytes, four I2C items including byte/ACK/START/STOP, and five SPI MOSI bytes. SPI uses bounded existing-SRAM capture after live-host loss was diagnosed; no source-rate change. Python1145PASS; reader/service/capacity checks17PASS in both scheduling modes. Third-party recordings replayed digitally, not TRIPWIRE silicon or full protocol conformance.)*
- [x] **L4:** all five metamorphic relations pass for UART, SPI and I2C, using the explicit timing domains/phase premises approved in D-191 and documented in VERIFICATION.md. *(2026-11-19: [LOOP/IDLE](../../reports/PHASE3_METAMORPHIC_LOOP_IDLE.md), [TAP](../../reports/PHASE3_METAMORPHIC_TAP.md), [strict PERM](../../reports/PHASE3_METAMORPHIC_PERM.md), and [SCALE/native phase](../../reports/PHASE3_METAMORPHIC_SCALE_PHASE.md), with source/image/log/XML/capture receipts. All named cases pass model, both RTL simulators and exact official netlist; final timing suite4/4with no failures/skips. Python1198PASS; SCALE8pairs/815declared interval comparisons, one-edge controls, independent decodes; native routine phase matched by an actual pre-load clock and host TIME check, unaligned counterexample retained. Finite selected rates/modes/mappings/idle seeds, not universal waveform2x, unaligned routine invariance, analog, silicon or whole-chip formal. Hardware/official jobs unchanged.)*
Scoped channel safety/order, conditional ready-consumer progress and tap isolation now have [local unbounded proof evidence](../../reports/PHASE3_FORMAL_CHANNELS.md), plus bounded covers and five rejected RTL mutations. [Native RX overrun indication and producer preservation](../../reports/PHASE3_FORMAL_PIN_RX.md) also pass unbounded proof with reachability and five rejected faults; [Lean sticky flags and merge](../../reports/PHASE3_FORMAL_PIN_UNIT.md) now pass for both parameter sets; [D-192candidate full/BITSYNC integration](../../reports/PHASE3_STATUS_MERGE_FORMAL.md) now passes scoped unbounded proof, but adoption/physical qualification and main F-CHAN-4 remain open. This does not complete the following aggregate gate.

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
