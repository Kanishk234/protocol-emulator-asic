# Phase 4: stretch goals and RTL freeze

| | |
|---|---|
| **Dates** | Nov 30 → Dec 6, 2026 (freeze Dec 6, before finals week) |
| **Goal** | Add CAN only if everything before it is green. Close coverage. Prove the per-program properties. Freeze the RTL on a commit where every workflow is green. |
| **Devices needed** | None |
| **References** | `../VERIFICATION.md` §6 (L5b), §7, §11; `../PHYSICAL_DESIGN_AND_CI.md` §9 |

---

## 1. Entry criteria
- Phase 3 exit checklist passed. If it has not fully passed by Nov 30, **skip CAN** and go straight to coverage and freeze.

## 2. Tasks

### 2.1 CAN stretch goal (conditional)
1. `can_node.trw` across 2 lanes:
   - **bit lane:** sampling, destuffing, arbitration readback;
   - **frame lane:** fields, ACK slot, error handling;
   - destuffed bit stream **multicast** to CRC (CRC-15 polynomial) and the frame lane.
2. L3-CAN:
   - two TRIPWIRE-model nodes arbitrating;
   - co-simulation with the **OpenCores CAN controller** RTL as a third node, if its licence and our testbench allow;
   - sigrok `can` on every run.
3. Speeds: 125 kbit/s required, 250/500 kbit/s reported as measured.
4. Any RTL change for CAN is a separate hardening run with an AREA row. **Drop CAN if it threatens the freeze date.**

### 2.2 Program-specific formal (L5b)
5. Formal harness: load the slot images via `$readmemh`, with the pins constrained by protocol assumptions.
6. Prove, for the shipped programs:
   - I2C target ACK before the next SCL fall (400 kHz and 1 MHz settings); no SDA drive while SCL is high except intended START/STOP;
   - UART RX: no OVERRUN at the configured baud with back-to-back frames;
   - SPI target: MISO bit valid at the controller's sample edge.
7. Compare each against the `tripc` report. Log any mismatch in `BUGS.md` and fix it.

### 2.3 Coverage closure
8. Run the functional covergroups from `VERIFICATION.md` §7 and fill the holes with directed or random tests.
9. Verilator line/toggle coverage ≥ 95% line; explain every gap in the report.
10. Long L2 lockstep: ≥ 10⁸ compared clocks, zero divergences (nightly workflow).

### 2.4 RTL freeze (owner: physical/CI)
11. Pick the freeze commit. Run `gds` **by hand** on it (`../PHYSICAL_DESIGN_AND_CI.md` §9).
12. Record the final AREA row; tag `freeze-rtl`; archive the gds artefacts as a release asset.
13. From here, RTL changes only for verification-found bugs, each re-hardened and logged.

---

## 3. Deliverables
- (Optional) CAN program and tests.
- L5b proofs for the shipped programs; coverage report.
- The `freeze-rtl` tag with archived artefacts and final numbers.

---

## 4. Phase exit checklist (all must pass)
- [ ] **Decision logged:** CAN included (with its L3-CAN results), or deferred with the reason.
- [ ] **L5b** proofs pass for the I2C target, UART RX and SPI target programs, and match the `tripc` reports.
- [ ] Functional coverage goals met (every covergroup at target); line coverage ≥ 95%, gaps explained.
- [ ] L2 lockstep ≥ 10⁸ clocks with zero divergences.
- [ ] F-SCHED-3 and F-ISO-1 completed (bounded is acceptable; depth recorded).
- [ ] **Freeze commit:** `test`, `docs`, `gds` (gds, precheck, gl_test, viewer), `lint`, `unit`, `formal` and `fpga` all green on the same commit.
- [ ] `gds` on the freeze commit completed within the 6 h limit; final AREA row recorded.
- [ ] Tag `freeze-rtl` pushed; gds artefacts attached to a release.
- [ ] GitHub Pages shows the frozen design.

## 5. Risks in this phase
| Risk | Response |
|---|---|
| CAN eats the week | It is conditional; drop it at the first sign of slipping |
| The freeze hardening fails or times out | Remove the last change and re-run; the previous green commit is the fallback freeze |
| Finals week | The freeze is placed before it deliberately; nothing after Dec 6 needs RTL work |