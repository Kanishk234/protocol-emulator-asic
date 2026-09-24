# TRIPWIRE work log

Newest entry at the top. One entry per work session.
- Keep entries short.
- Evidence means a CI run ID, a test command and its result, or a file path.
- Raw logs are not committed; link to them instead.

Template:

```
## YYYY-MM-DD: <who> (phase N)
Done:
- ...
Checklist boxes ticked (evidence):
- [x] <item>: <CI run #/command/file>
Problems / decisions:
- ... (DECISIONS D-xxx, BUGS #x)
Next:
- ...
```

---

## 2026-09-24: Krithik + Claude (phase 1: spike lane vs. D-033)
Worked from `ARCHITECTURE.md` §14 as pulled (26bdc86: L8–L11, R5–R6, H1); did not read `tools/`.

Done:
- Checked `spikes/r1_lane/trw_lane.v` against the new rules. It agrees with L8 (BSEL, MKCTL), L9, L11, R5, R6 and H1 (RUN = 0 and all flops reset; the harness, the R2 top and the tb write all 48 slot words before RUN).
- **L8 KT: fixed on `main`** (BUGS #34). KT now keeps the head tag only when ASRC is I0/I1; otherwise OT gives the tag.
  - `tb_r1_lane.v` covers both halves: slot 0 has KT with A = I0 and OT = ERR, and must keep DATA; slot 2 has KT with A = zero, and must emit EVENT.
  - The old behaviour fails the tb ("O1 token tag 0"); the fixed lane passes.
- Not re-applied to `spike/r2-latch`: R2's result does not depend on it, and a push would restart the running hardening.
- `run_r1.sh` re-run: sims PASS, lint clean. ABC mapping noise moved the worst EVAL row to 11.68 ns (flop, unbuffered, slow), slack +7.87. That is below the +8.2 ns the docs claimed, so `R1_LANE_TIMING.md` §3, D-030, the phase checklist evidence, `AREA.md` and `PHASE1.md` now carry the corrected figures (margin 1.67×). The conclusion is unchanged.

- **L10 CALL: fixed on `main`** after Krithik's OK. CALL now ignores DST (no wait, no reservation, no output load) and DFE (no PEND, no flag write). Both fixes are one BUGS entry, #34 (references D-033 and the model's twin #32).
- **Sim checks** (`tb_r1_lane.v`, both slot stores PASS):
  - KT with A = zero gives OT (EVENT); KT with A = I0 keeps the head's DATA over OT = ERR.
  - A CALL with DST = O0 while O0 holds the last, untaken byte, and DFE on f0 = 1: it must fire; O0 stays unchanged; `resv` and `PEND` are 0 in the CALL's own EXEC clock (the old behaviour set and cleared both, invisible at the end); f0 stays 1 (a flag write would store R = 0).
  - H1: nothing fires, is taken or loaded while halted and the slots are being written.
- **Mutation checks:** removing each of the five L10 guards alone fails the tb, and so does the old KT rule. A lane that ignores RUN fails the H1 check (the X from unwritten latches shows as `take xx`).
- **H1 confirmed:** RUN resets to 0 in the harness, the R2 top and the tb; every lane flop has a synchronous reset; the tb writes all 48 slot words plus K0–K3 before RUN, and the R2 test writes all 52 words before RUN.
- `run_r1.sh` re-run: sims PASS, lint clean; worst EVAL this run 10.76 ns (slow). The report's table is this run; the headline keeps the worst across runs (11.68 ns, +7.87).
- Not re-applied to `spike/r2-latch`.

Next:
- R2 run 2 (`gds` 36017019520): cancelled after ~3 h, no artifacts.
  - The resizer fix worked: routing started within minutes.
  - Routing stalled at 8 Metal2 violations in the 27th stubborn-tile pass (live log, D-032).
- Run 3 prepared (D-034): `PL_TARGET_DENSITY_PCT` 52 (not 45: the placer's utilisation is 48.9 %) and `DRT_OPT_ITERS` 20. A non-converging run now fails with `GDS_logs` instead of timing out without them.
- D-034 also states the branch-only config-rule exceptions (DRT_OPT_ITERS, and the SDC keys from run 2) that I had not flagged.
- R2 run 3 (`gds` 36039323359):
  - routing started 4 min in (SDC fix confirmed);
  - pin access clean;
  - density 52 cut the first-pass violations from 8,297 to 33, but the tail held at 26–27 (Metal2/Metal3);
  - pass 5 was a ~1 h stubborn pass, so a cap of 20 would still time out (kill at 00:09 UTC; I first misstated it as 22:09).
- Run 4 first planned as a diagnostic-only run (cap 3). Revised at Krithik's question ("why run a workflow we know will fail?") into an attempt to pass: tile 4x2, density 42, cap 8 (D-034). No RTL or test change.

## 2026-09-24: Krithik + Claude (phase 1: R1 spec gaps G1–G8, model side)
Done:
- Answered the eight spec gaps from the R1 report (§6) from what `tools/tripsim` does, and wrote them into `ARCHITECTURE.md` §14 (new L8–L11, R5–R6, H1), §5.1/§5.2, and the `spec/tripwire.yaml` field descriptions (regenerated ISA tables). D-033.
- The spike agrees with every answer except G6 `KT` with a non-input A (the spec says ignore it; the spike used the latched head tag).
- Two latent tool bugs found by the review and fixed: BUGS #32 (model reserved an output for CALL), #33 (`tripc.load` left unused slots unwritten). tripc now rejects `keep` without an input operand.
- Tests: 197 fast tests pass (`pytest -n auto -m "not slow"`), `gen --check` clean.

Checklist boxes ticked (evidence):
- None. "Zero OPEN items" still needs the second person's §14 review.

Problems / decisions:
- D-033. DECISIONS numbering: D-031/D-032 came from the R2/R3 session; this is D-033, so that session should use D-034 next.

Next:
- Kanishk: review §14, including the new rules, then the "zero OPEN items" box can be ticked.
- R2/R3 session: change the spike's `KT` handling to §14 L8 before the lane becomes phase 2 RTL.

## 2026-09-24: Krithik + Claude (phase 1: R1 risk spike)
Fresh session, RTL context only: read `ARCHITECTURE.md`, `ISA.md`, `spec/tripwire.yaml` and `PHYSICAL_DESIGN_AND_CI.md`; did not read `tools/tripsim` or `tools/kernels`.

Done:
- **`spikes/r1_lane/`** (throwaway RTL, outside `src/`, no CI reads it). It contains:
  - `trw_lane` (12 ready terms, the §4.3 rule, one priority encoder, static updates, EXEC, routine steps);
  - `trw_alu` (16 ops);
  - `trw_slots` (Ibex-style latch array, with a flop variant);
  - `trw_cport` (source mux, F7);
  - `trw_r1_top` (harness: all lane neighbours are registers);
  - `tb_r1_lane` and `run_r1.sh`, `sta.tcl`, README.
- **Tools:** OpenSTA 2.6.0, the standalone `sta` extracted from the OpenROAD 2024-12-14 Ubuntu 22.04 package plus `libtcl8.6` / `tcl-tclreadline` via `apt-get download`, into `~/.cache/tripwire/openroad`. No root needed; `run_r1.sh` does it.
- **Sanity sim** (Icarus, latch and flop slots): ISA §7.1 at 3 clocks per byte, then EVENT: PASS. Verilator `-Wall` clean.
- **Timing at 20 ns** (Yosys onto cmos5l, OpenSTA, before layout):
  - EVAL 3.7–7.3 ns typ, 5.8–11.4 ns slow;
  - worst slack +8.2 ns (flop slots, unbuffered, slow);
  - EXEC at most 10.6 ns.
  - Report: `docs/reports/R1_LANE_TIMING.md`.
- **Area:** ~67K µm² per lane with latch slots (slots 25.5K vs 51.7K as flops). Recorded in `AREA.md` (synthesis-only section).
- **DECISIONS D-030 (accepted):** fire every clock; no fallback in the phase 2 RTL. Recheck against R2's post-route slack.
- **Spec gaps G1–G8** (report §6): places where the text leaves an RTL choice open or disagrees with itself (BSEL reg/k index, routine step pipeline position, blocked routine OUT, PEND set/clear on the same edge, DJNZ and RZ, KT/CALL/f3 corner cases, slot latches without reset, PEND/slot-width/RRET inconsistencies). None affects timing.
- `docs/summaries/PHASE1.md` item 16.

Checklist boxes ticked (evidence):
- [x] R1 decided: `docs/reports/R1_LANE_TIMING.md` (run_r1.sh), D-030 accepted by Krithik ("accept D-030").

Problems / decisions:
- Before layout only: no wires, no CTS. R2's hardening gives post-route numbers for the same logic.
- The clock gate in `trw_slots` is a behavioural latch + AND. For R2 and phase 2, instantiate `sg13cmos5l_lgcp_1`.

Later (R3 set-up):
- D-031: R2/R3 hardenings on throwaway branches (per-ref `gds` concurrency keeps `main` safe); R3 first.
- `spikes/r3_sram/`:
  - branch overlay: 2x2 `info.yaml`, test top with direct word access and an 18-pass walking-ones BIST, `trw_sram` wrapper, macro blackbox, `config.json` with the macro block, Loom's `pdn_cfg.tcl` verbatim (commit c7000671), `test/Makefile` + `test.py`;
  - `fetch_macro.sh` (IHP-Open-PDK 2bbec75, byte counts checked);
  - `check_local.sh`;
  - `apply_to_branch.sh` (refuses to run off `spike/r3-sram`).
- `check_local.sh`: PASS. Lint; 3/3 tests on the RTL and on a Yosys gate-level netlist (TT Icarus 13); flattened instance `u_sram.sram`.
- Mutations: a wrong BIST write is caught (1 test fails); address aliasing is caught (2 tests fail).

- User pushed `spike/r3-sram`. **R3 PASS:** `gds` run 35961480554 (09e8697): gds 7.9 min, precheck 1.7 min, gl_test 0.8 min, viewer green; lint/test/unit/docs green. The macro is kept (D-031).
  - [x] R3 box ticked (run 35961480554).
  - Pages now shows the R3 chip until the next `main` hardening.
  - Numbers from `GDS_logs` (copied to the git-ignored `build/ci/r3/`) are now `AREA.md` row 2:
    - setup +10.95 / +9.23 / +11.23 ns, hold +0.33 / +0.67 / +0.14 ns;
    - 47 % utilisation, 0 overflow, LVS / routing DRC / antenna all 0.
  - The macro's clock-to-output is **6.59 ns slow** (4.29 typ): a phase 2 constraint on the routine decode.
- `docs` on `main` (db974df): one of two identical push-triggered runs failed inside the TT docs action (35962848241), the other passed (35962849222), so the failure is flaky, not ours. Re-run requested.

Later (R2 set-up, D-032):
- `spikes/r2_latch/`: branch overlay for the whole R1 lane on 3x2, with pin-driven I0 producer, O0/O1 subscribers and RIR. Also `test.py` (latch array: two patterns over all 52 words; a program with §7.1, a routine step pair and a K constant), `check_local.sh` and `apply_to_branch.sh`.
- Shared `trw_slots.v`:
  - library ICG `sg13cmos5l_lgcp_1` under `ifdef SYNTHESIS`;
  - a debug read port (~9.4K µm² per lane: a phase 2 question);
  - the upper 11 bits of each slot's 4th word are no longer stored (132 latches that R2's readback had kept).
- `check_local.sh`: PASS. Lint; 2/2 on RTL and gate level (700 latches, 52 `lgcp`); STA pre-layout +10.8 ns (slow, flop endpoints).
- R1 re-run: same conclusion. The ABC mapping moves rows by up to ±1.2 ns between such edits, so the report now uses the final run and carries a ±1.5 ns note. D-030, AREA and the summary are updated to match.

- **R2 run 1 timed out:** `gds` 35962617201 (06d0f3d) was cancelled at the 6 h job limit inside Build GDS, with no artifacts.
  - Job log (`build/ci/r2/`): the post-CTS resizer spent 3 h 21 min on 700 "violating" latch data pins (time borrowing → slack 0.000 < the 0.05 margin).
  - Detailed routing went 8,297 → 21 violations in ~1 h, then 1.5 h of stubborn-tile passes left 14 Metal2 spacing violations.
  - M2/M3 usage 58 % / 55 %, wire length 367 mm.
  - D-032 has the full diagnosis.
  - Run 2 fix, one change: `pnr.sdc` (default + no setup repair on latch data pins) and `signoff.sdc` (default). Checked with OpenSTA locally.

Next:
- User: push the R2 run 2 change (`spikes/r2_latch/overlay/src/{pnr.sdc, signoff.sdc, config.json}`) to `spike/r2-latch`.
- Then: from run 2's artifacts, locate the Metal2 violations and the congestion hot spots, and size the routing cost of the slot array (and of the 52-word read port) for the 6x4 plan.
- (done) User: commit, then create `spike/r2-latch` and push it (spikes/r2_latch/README.md). Record both gds runs when they finish.
- Team: answer G1–G8 in §14 / ISA (the model owner can say what tripsim does).
- R2: a 2x2 TT project around `trw_slots` + `trw_lane` (library ICG, host-write path from pins). Plan: spike branches in this repo (`spike/r2-latch`, `spike/r3-sram`) with `tiles: "2x2"`, never merged; `gds` concurrency is per ref, so they don't cancel `main`.
- R3: the SRAM macro smoke project (PHYSICAL §3 recipe).

## 2026-09-23: Krithik + Claude (phase 1: CI speed, ISA §9 answers, freeze proposals)
Done:
- **CI speed.** The `unit` workflow took about 20 min. Five tests (servo, IR NEC TX/RX, two LIN tests) took 785 of the 906 s, because they simulate 3–10 M clocks each.
  - Marked those five `@pytest.mark.slow` (the marker is registered in `pyproject.toml`).
  - `unit` now runs `pytest -n auto -m "not slow"` with pytest-xdist 3.8.0 (pinned in `requirements-dev.txt`): 183 passed in 37 s locally with 4 workers.
  - New `nightly` workflow (daily plus manual), with two jobs: `full` (everything) and `r1-fallback` (kernels at `TRIPSIM_FIRE_PERIOD=2`).
- **R1 fallback measured.** `Chip` reads `TRIPSIM_FIRE_PERIOD`. All 103 kernel tests pass at fire period 2, in 656 s, including every speed-limit test.
- **`tools/explore/metrics.py`** (`cd tools && python -m explore.metrics`) reports per-lane slots, registers, K, head tests, ALU-flag uses, readiness and ablation bounds for every program. Its table is now `ARCH_EXPLORATION.md` §1a.
- **`ARCH_EXPLORATION.md`** answers every `ISA.md` §9 row: slots, registers + K, ablation, R1, TX/RX NBITS, routine rate, and Q7 throughput.
- **DECISIONS D-029 (proposed):**
  - keep 12 slots, 4 + 4, and every D-007 feature;
  - the R1 fallback is acceptable;
  - close Q1–Q7;
  - a new connectivity table (Lk.I1 needs 9 sources);
  - no helper units in phase 2;
  - host MISO moves to `uo_out[3]` (RP2350 SPI0 RX); pin map follows.

- **D-029 accepted and applied** (Krithik: "go with your recommendations for both").
  - `spec/tripwire.yaml`: host pads `ui4 ui5 ui6 uo3 uo6` (MISO moved from `uo7`, checked against RP2350 datasheet Table 645), and a new `fabric` legal-source table (4-bit `sel`; Lk.I1 has 9 sources).
  - The generator expands the table into `LEGAL_SOURCES` (Python) and a generated table in ARCHITECTURE §4.6. There is no Verilog output yet, so `src/` is unchanged; it is added when the phase 2 RTL needs it.
  - tripc rejects a `connect` outside the table; every program passes (`test_every_program_uses_only_legal_sources`). New gen and tripc tests: 189 fast tests pass in 18 s.
  - ARCHITECTURE §4.3–4.6, §8 (helpers deferred), §9 host pins, §10 pin map, block diagram; ISA §8–9. Zero OPEN items remain.

Checklist boxes ticked (evidence):
- [x] ARCH_EXPLORATION answers every ISA §9 row, with decisions logged (D-029 accepted). Evidence is next to the box.
- "Zero OPEN items" is done, but the box also needs the second person's §14 semantics review, so it stays open.

Next:
- Kanishk: review ARCHITECTURE §14 (cycle-exact semantics), and read D-029.
- R1–R3 spikes (fresh session, RTL-only context); area estimate and cut list for the pin-unit options.
- Check the first `nightly` run (start it by hand with workflow_dispatch).

## 2026-09-23: Krithik + Claude (phase 1: every remaining protocol)
Done:
- New programs, each against a reference model written from its spec (+ sigrok where it has a decoder): MIDI (UART at 31 250 baud), DMX512 TX/RX, servo PWM, IR NEC TX/RX, SMBus with PEC, LIN 2.x commander + monitor, I2S out/in, HDLC, CAN part B + error handling, USB low-speed device (feasibility only).
- General features (DECISIONS D-024..D-028; §14 P8, P21-P30): event timestamps in PRESC ticks, carrier; BITSYNC flag framing, TX CRC register + CRC_XOR, own-edge rule; JAM, readback modes 0-3, listen-only, own-frame bit; NRZI, pin N, OE auto, SE0, DELIM = se0, CRC_SKIP; tripc `table`.
- Reference models: dmx, nec, smbus, lin, i2s, hdlc, can (rewritten: part B, error frames), usb (low-speed host).
- Fixes: BUGS #16-#31 (servo race, IR padding, CAN register race and level-bit test, USB branch polarity, LIN slot pacing, tripc bound and ld/st offsets, BITSYNC own-edge resync and EOP gap, I2S ADC model, HDLC abort, sigrok DMX and CAN decoder limits).
- Mutation checks: 13 of 13 new features caught (carrier, tick timestamps, flag hold-back and abort, CRC_XOR, armed JAM, strict readback, listen-only, NRZI, CRC_SKIP, OE auto, own-edge resync, half-duplex echo). Two first survived (armed JAM, listen-only): the CAN tests now watch our TXD for the error flag and for silence (no ACK) in bus-off. New fast unit tests for carrier and tick timestamps.
- Full suite: 186 passed (before the last two test edits, which pass on their own); `check_all.sh` and `gen.py --check` below.

Checklist boxes ticked (evidence):
- none new (these are stretch protocols beyond the phase 1 checklist).

Problems / decisions:
- The spec YAML and `src/trw_defs.vh` changed (new commands): pushing starts a gds run.
- SRAM use: CAN 353, USB 335, LIN 208 of 512 words; lane slots at most 12 of 12 (CAN, SMBus).

Next:
- Close phase 1: ablations (now with a much longer feature list, and area estimates to decide cuts), zero OPEN items (incl. the §4.6 connectivity table), semantics review, R1-R3 (fresh session), green CI.

## 2026-09-23: Krithik + Claude (phase 1: CAN via BITSYNC)
Done:
- D-023: BITSYNC pin-unit mode (recovered bit clock with hard sync + SJW resync, bit stuffing, CRC ≤ 16 bits with append/check, readback abort/report, `FRAME n`, one-bit override, TX status events) and `pin_s` (sense pad). Spec YAML: `FRAME` (op 9), `LINE` (op 10), `WAIT` [1], `SYNC` text. §14 P20–P26. `tools/tripsim/bitsync.py`.
- `programs/can.trw`: CAN 2.0A controller on 2 lanes (11 + 10 slots, 3 routines), 1 pin unit.
- `tools/protomodels/can.py`: reference CAN 2.0A node (bit timing, stuffing, CRC-15, arbitration, ACK).
- Tests: `test_can.py` (16) and `tripsim/tests/test_bitsync.py` (6, an HDLC-style configuration). sigrok `can` agrees on every frame and ACK. 155 pytest pass; `check_all.sh` PASS; `gen.py --check` clean.
- Engine mutations: 8 of 9 caught; "resync on own dominant edges" is not (a gap, noted in D-023).
- BUGS #10–#15: test-harness host FIFO, two CAN firmware design problems, a pending-flag slot mistake, reference model stuff-after-CRC, override armed by a stuff bit.
- Confirmed last session's open item: the 1-Wire sigrok leg runs and agrees (READ ROM, ROM code).
- Noted: the ARCHITECTURE §4.6 connectivity table does not match the programs (HOST_OUT from O1); marked for the freeze.

Checklist boxes ticked (evidence):
- none new (CAN is a stretch goal beyond the phase 1 checklist).

Next:
- CAN follow-ups if wanted: error frames and error counters, extended IDs, remote frames; a multi-transmitter propagation-delay test for the resync rule.
- Remaining phase 1: ablations, zero OPEN items (incl. the §4.6 table) + semantics review, R1–R3 (fresh session), green CI.

## 2026-09-23: Kanishk + Claude (planning: protocol coverage, FPGA target)
Done:
- Reviewed the model's protocol coverage against the competition brief:
  - required UART/SPI/I2C and the suggested JTAG/SWD/PS/2 are verified on the model;
  - CAN, USB low-speed and 10BASE-T are not.
- D-012 check on the CAN/USB primitives: resync, bit stuffing (N as a setting), NRZI, readback compare and CRC are general. SE0 detection and the complementary pair must be generalized first (multi-pin pattern match, pin-pair mode). Firmware-only CAN to be tried first.
- D-022: the FPGA target is a Basys 3 running the full design; the reduced iCE40 build is dropped (it could not run I2C). Updated PHYSICAL_DESIGN_AND_CI §6/§8, phase 3 items 8–9 and exit box, the phase 4 freeze box, phase 7, and the OVERVIEW/VERIFICATION CI tables. The template's `fpga` workflow is untouched and informational.
- Docs only; no code or CI changes.

Checklist boxes ticked (evidence):
- none

Next:
- CAN on current primitives (firmware-first), then only the primitives it proves necessary.
- Remaining phase 1: ablations, zero OPEN items + semantics review, R1–R3 (fresh session), green CI.
- Phase 3: choose the Basys 3 build path (openXC7 workflow vs local Vivado) and record it in D-022.

## 2026-09-23: Kanishk + Claude (phase 1: verification plan additions)
Done:
- D-021: verification cross-checks added to `docs/design/VERIFICATION.md`:
  - L0-ASRT (in-RTL `TRW_ASSERT` for formal and simulation);
  - L-XSIM (Icarus and Verilator);
  - L8-EQY (eqy, RTL vs netlist);
  - L8-XPROP;
  - L9 Hardcaml (H0 spike, H1 expect tests, H2 independent OCaml model).
- Tasks added:
  - Phase 2 §2.5, items 12–15;
  - Phase 3 §2.8, items 11–13.
- Other doc updates:
  - OVERVIEW §13 item 6 resolved (RTL stays Verilog);
  - `hardcaml` workflow added to the CLAUDE.md list.
- Docs only; no code or CI changes.

Checklist boxes ticked (evidence):
- none

Next:
- Unchanged: remaining phase 1 work (ablations, zero OPEN items + semantics review, R1–R3 in a fresh session, green CI).

## 2026-09-23: Krithik + Claude (phase 1: PS/2, 1-Wire, SWD, JTAG)
Done:
- Four more protocols verified on the model, each against a reference model written from its spec plus sigrok:
  - `programs/ps2_host.trw` (12 slots + 1 routine);
  - `programs/onewire.trw` (9 + 1);
  - `programs/swd.trw` (12 + 3; SWCLK up to 8.3 MHz);
  - `programs/jtag.trw` (8; TCK up to 12.5 MHz).
- D-020: `SETN rx` (timed RX framing restart + run-time RX length) and `SAMPLE` (sample pin A at a chosen time). Spec YAML + generated files, §14 P18/P19, tripsim, unit tests.
- Reference models: `tools/protomodels/ps2.py`, `onewire.py`, `swd.py`, `jtag.py`.
- Mutation checks: SAMPLE delay ignored, SETN rx length ignored, SETN rx without restart, SWD echo kept / no ACK restart / no WAIT before release, JTAG no TDO restart are all caught. "JTAG samples TDO on the fall" is not caught and is benign on this model (zero-delay target + input synchroniser); rise sampling stays.
- BUGS #6–#9 (sigrok ps2 decoder off by one, PS/2 device model, SWD firmware stale words, a test waveform).
- Docs: PROTOCOL_SUPPORT, ARCH_EXPLORATION, programs/README, PHASE1 summary.
- 133 pytest tests pass; `scripts/check_all.sh` PASS; `gen.py --check` clean.

Checklist boxes ticked (evidence):
- none new (these protocols are beyond the phase 1 checklist).

Problems / decisions:
- D-020. The regenerated `src/trw_defs.vh` means the push touches `src/` and starts a gds hardening run.

Next:
- CAN primitive set (edge-resync RX, bit-stuffing codec, readback compare, CRC helper) and a CAN program.
- Remaining phase 1: ablations, zero OPEN items + semantics review, R1–R3 (fresh session), green CI.

## 2026-09-23: Krithik + Claude (phase 1: PULSE mode, WS2812, DShot)
Done:
- D-019: PULSE mode as two-phase symbols per bit value (pulse-width, pulse-distance, Manchester); §14 P17.
- `programs/ws2812.trw` (2 slots) and `programs/dshot.trw` (2 slots + checksum routine).
- `tools/protomodels/pulse.py`: WS2812B datasheet-tolerance decoder and DShot decoder (checksum, timing).
- Tests:
  - WS2812: two frames, zero tolerance violations, sigrok `rgb_led_ws281x` agrees;
  - DShot 150/300/600/1200;
  - a corrupted checksum routine is caught;
  - new unit tests for OE, SYNC, LATE, SETN and the fabric port filter.
- Two injected PULSE bugs are caught. 117 pytest tests pass.
- Honesty notes:
  - my first guard test assumed a checksum bit that wasn't set; it now asserts its premise;
  - sigrok shows WS281x colours reordered to RGB, which the test now accounts for.

Checklist boxes ticked (evidence):
- [x] tripsim passes its own unit tests (every op, channel rules, pending rule, rotation, pin-unit modes): `tools/tripsim/tests/` + `tools/kernels/tests/`, local pytest 117 passed.

Next:
- CAN feature set (edge-resync RX, bit stuffing, readback compare, CRC helper) + a CAN kernel; or quick "expected" programs (SWD, JTAG, PS/2, 1-Wire).
- Remaining phase 1: ablations, zero OPEN items + semantics review, R1–R3 (fresh session), green CI.

## 2026-09-23: Krithik + Claude (phase 1: tripc v0, programs, protocol roadmap)
Done:
- `tools/tripc` v0 (D-018): the `.trw` language, compiler with static checks and report, JSON image, loader, CLI (`python -m tripc`).
- `programs/`: uart, spi_controller, spi_target, i2c_controller, i2c_target. Compiled images are bit-identical to the reference kernels (slots, K, registers, routines at 3 periods). `tools/kernels/*.load()` now compile the programs, so every protocol test runs on compiled firmware.
- `tools/protomodels/uart.py` (8N1 line model). `test_uart.py`: TX vs the model + sigrok at 4 baud rates; RX with a framing error; 256-byte loopback.
- Pad numbering moved into `spec/tripwire.yaml`.
- BUGS #5: the VCD writer dropped a final steady level, so sigrok missed the last byte; fixed.
- `docs/reports/PROTOCOL_SUPPORT.md`: honest roadmap (verified / expected / needs primitive / not feasible).
- 106 pytest tests pass.

Checklist boxes ticked (evidence):
- [x] Spec only place of encodings; lint CI no diff: lint 35921199653, unit 35921199432.
- [x] UART/SPI-controller/I2C-controller programs pass vs reference models and sigrok (and the two sub-boxes): `tools/kernels/tests/test_uart.py`, `test_spi_controller.py`, `test_i2c_controller.py` (local pytest, 106 passed).
- [x] tripc reports for all programs, slots ≤ 12: `test_tripc.py::test_reports_and_slot_budget`.
- [x] Jane Street assumptions stated: D-003.

Next:
- PULSE mode (unlocks WS2812/DShot/servo/IR, and the `tripsim` unit-test box).
- The primitives for CAN (edge-resync RX, bit stuffing, readback compare, CRC helper), then a CAN kernel.
- Remaining phase 1 boxes: ablation rows in ARCH_EXPLORATION, zero OPEN items + a two-person semantics review, R1–R3 (fresh session for RTL), green CI.

## 2026-09-23: Krithik + Claude (phase 1: spec YAML, generator, phase summaries)
Done:
- `docs/summaries/` with plain-language PHASE0.md (complete) and PHASE1.md (in progress). CLAUDE.md: every phase ends with a summary there.
- `spec/tripwire.yaml` (draft 0.1): all encodings in one place.
- `tools/gen/gen.py`: validates the spec and generates `tools/tripwire_spec.py`, `src/trw_defs.vh` and the ISA/ARCHITECTURE tables; `--check` for CI.
- tripsim now imports the generated tables (`isa.py`, `asm.py`, `pinunit.py`); its hand-written copies are gone.
- New CI workflows `lint` (gen check, defs compile, Verilator lint) and `unit` (pytest with sigrok).
- 15 generator tests; the total is 73 pytest tests, and `check_all: PASS`.
- A hand-edited generated table is caught by `--check` (demonstrated).
- Found on the way: YAML 1.1 reads a bare `off` key as `false`. The keys are now quoted, and the generator rejects non-string field names.

Checklist boxes ticked (evidence):
- none yet. "spec/tripwire.yaml is the only place encodings live; the lint CI regenerates and shows no diff" can be ticked once the `lint` workflow runs green on `main`.

Next:
- Push (note: `src/trw_defs.vh` is under `src/`, so this push starts one ~45-minute `gds` run; harmless).
- Tick the spec box from the `lint` run ID.
- Then either `tripc` v0 or the R1–R3 spikes (fresh session for RTL).

## 2026-09-23: Krithik + Claude (phase 1 start: tripsim v0)
Done:
- `tools/tripsim` v0 (model-first, D-008), written from `ARCHITECTURE.md` + `ISA.md` only:
  - encodings and the shared op table, a minimal assembler, the channel fabric, lanes (EVAL/EXEC, pending, implicit checks, urgent pre-emption, routines with the SRAM rotation, LD/ST, CALL/RET);
  - pin units: TX LEVEL/OE/GAP/SYNC/SETN + SHIFT with a drift-free fractional cursor; RX SHIFT_RX + EDGE_TS;
  - host FIFOs, pads with 2-FF synchronisers, VCD output.
- 28 pytest tests (`python -m pytest -q`, now in `check_all.sh`). Headline measurements:
  - pin-to-pin reaction exactly **7 clocks**;
  - count loop 3 clocks/byte;
  - routines 1 step per 4 clocks;
  - sigrok decodes the model's UART TX at 1 M and 921.6 kbaud;
  - UART RX framing check via CMPM.
- Test quality: three injected bugs (no pending rule, TX one clock early, BUGS #2 fix reverted) each caught.
- `ARCHITECTURE.md` §14: draft cycle-exact semantics (rules F1–F6, L1–L7, R1–R4, P1–P5) fixed while writing the model.

Findings:
- BUGS #2 (spec): 1-bit `seq` makes a tap alias after two missed tokens; fix: a counted drop is a take.
- D-009: OP 15 = `MOVB` (d = B), needed to react to an input with a constant in one action; keeps the 7-clock reaction.
- Q7 (open): registered release limits a lane output to 1 token / 3 clocks and HOST_IN→lane to 1 / 2; §4.4's "1 per clock" is not met.

Later the same day (I2C):
- Pin units: LINKED_RX (with RX_TAIL), COND_EDGE, linked TX shift; separate RX/TX link edges (D-010, §14 P6–P8).
- `tools/protomodels/i2c.py`: reference I2C controller written from UM10204.
- `tools/kernels/i2c_target.py`: write-direction I2C target, 9 of 12 slots:
  - passes at 100 kHz, 400 kHz and 1 MHz against the reference controller, and under sigrok `i2c`;
  - ACK queued 7 clocks after the 8th SCL rise; works down to 12 clocks/bit, so about 2x margin on the Fm+ SCL-high minimum;
  - two injected kernel bugs (ACK on the wrong edge, wrong address bits) are caught.
- `docs/reports/ARCH_EXPLORATION.md` started. 33 pytest tests pass.

Later still (SPI):
- Pin units: CLKGEN, TX_ACCEPT tag filter, TX_PRELOAD (D-011, §14 P9–P12).
- `tools/protomodels/spi.py`: reference SPI target, mode 0.
- `tools/kernels/spi_controller.py`: 4 slots, 1 lane, 4 pin units; one lane output multicast to SCK/MOSI/CS by tag:
  - mode 0 correct both ways against the reference target and sigrok `spi`;
  - fastest SCK 16.7 MHz (the MISO synchroniser limits it); 38 clocks/byte at 12.5 MHz.
- BUGS #3: preload race in the model, found by the SPI kernel at 2 of 3 speeds; fixed (P9).
- Test hardening: every unit must end with zero bad tokens. Injected removal of each tag filter or of the preload fix is caught (one earlier "survivor" was a broken injection script).
- R1 fallback priced on the kernels: no loss in the I2C/SPI speed limits; SPI byte rate -9%.
- 38 pytest tests pass.

Later still (generalization, D-012/D-013):
- Team principle recorded: every addition general *and* optimized; no dedicated protocol blocks (D-012, CLAUDE.md, memory).
- Pin units generalized: event generator (replaces EDGE_TS + COND_EDGE), two-phase framing (replaces RX_TAIL), echo suppression, TX length-in-token. ISA: HS head-bit select (slot now 53 bits).
- `tools/kernels/i2c_target.py` is now a full read + write I2C target in **12 slots** (14–18 before):
  - passes at 100 kHz / 400 kHz / 1 MHz and under sigrok;
  - fastest 12 clocks/bit;
  - disabling any of the 4 new primitives fails 5 tests.
- Docs updated in one pass of exact replacements (ARCHITECTURE §7/§14 P8, P13–P14; ISA §2/§4; VERIFICATION; OVERVIEW; PHASE2); generality table added to ARCH_EXPLORATION.

Later still (SPI target):
- D-014: pin C (select/frame) per pin unit: framing reset, abort on deselect, OE gating, events on C (§14 P15). `Chip.settle_inputs()` models pads held stable through reset.
- `tools/protomodels/spi.py`: reference SPI controller (mode 0, edge-exact MISO sampling, configurable CS setup, partial transfers).
- `tools/kernels/spi_target.py`: 3 slots, 2 pin units. Correct both ways vs the reference controller and sigrok. Measured:
  - SCK ≤ 12.5 MHz (MISO on the rise) or 8.33 MHz (on the fall);
  - CS setup ≥ 3 clocks; MISO released ≤ 3 clocks after deselect.
- Honesty catches along the way:
  - the first reference controller sampled MISO one clock late, which flattered us (12.5 MHz with MISO on the fall); fixed to edge-exact;
  - a "lucky" first byte (0xA5 starting with 1) hid the CS-setup limit; test data changed so an undriven line shows;
  - my own test helper overrode CS setup; fixed.
- Removing framing reset, abort or OE gating each fails a test. 48 pytest tests pass.

Later still (I2C controller):
- D-015: tag filters moved to every fabric consumer port (supersedes D-011's pin-unit filter).
- D-016: CLKGEN periods are IDLE half then ACTIVE half; STRETCH; new WAIT command (op 7); echo taint = own shifted bits on the pin.
- `tools/protomodels/i2c.py`: reference I2C target (address, writes, reads, clock stretching).
- `tools/kernels/i2c_controller.py`: 11 slots + 2 routines (repeated START, STOP). Passes 100 kHz / 400 kHz / 1 MHz × {no stretch, 40-clock stretch, longer-than-a-period stretch}, with sigrok and a bus-timing oracle (tLOW, tHIGH ≥ PERIOD/2).
- BUGS #4: kernel START race (a WAIT armed after its edge); fixed by ordering + tBUF.
- Honesty catches along the way:
  - STRETCH-off survived until the timing oracle and a long stretch were added;
  - the reversed START order is equivalent under current timing (recorded, not claimed);
  - the SPI controller limit is 12.5 MHz (the old 16.7 relied on a lopsided duty cycle).
- R1 fallback re-measured on all kernels: no speed limit changes; SPI controller throughput -8%.
- 58 pytest tests pass.

**Every required protocol role (UART TX/RX, SPI controller, SPI target, I2C controller, I2C target) now runs on the model, each checked by sigrok.**

Checklist boxes ticked (evidence):
- none yet. The tripsim box still needs PULSE; the program boxes need `tripc` and the UART/SPI/I2C-controller programs.

Next:
- I2C target read direction (does a full I2C target fit in 12 slots?); SPI target (flash); I2C controller (needs STRETCH).
- Ablations of the D-007 features.
- R1 risk spike (lane RTL at 50 MHz): best done in a fresh session that has not read `tools/tripsim` (independence rule).

## 2026-09-23: Krithik + Claude (phase 0)
Done:
- Top module renamed to `tt_um_tripwire` (`src/tt_um_tripwire.v`); trivial design = 8-bit counter on `uo_out`, enabled by `ui_in[0]`.
- `info.yaml` filled (title, authors Kanishk and Krithik, 50 MHz, 6x4, placeholder pinout); `test/Makefile` and `test/tb.v` updated.
- `test/test.py`: 4 pin-level tests (reset, count, hold, wrap), gate-level safe (relative counts only).
- `gds.yaml` trigger: `paths` filter (`src/**`, `info.yaml`, `macro/**`, the workflow) + `concurrency` cancel-in-progress. Template jobs untouched.
- Folder skeleton created, then removed at the team's request: folders now appear with their first real file (D-005).
- `docs/DECISIONS.md` (D-001..D-005 + open spec questions Q1–Q6 for the P1 freeze), `BUGS.md`, `CLAIMS.md`, `docs/reports/AREA.md`.
- Local loop: `.venv` via `scripts/setup_venv.sh` (versions pinned in `requirements-dev.txt`); OSS CAD Suite 20260914 appended to PATH in `~/.bashrc`; `scripts/check_all.sh` (L0-TT source sync, Verilator lint, Yosys synth/no-latch, cocotb suite).
- CLAUDE.md: venv rule added.

Checklist boxes ticked (evidence):
- [x] Ledgers exist and `.gitignore` excludes build/sim/formal output: files in `docs/`.
- [x] `docs` workflow green: run 35822749773 (bff60b5).
- [x] gds paths filter works: docs/scripts-only push (bff60b5) started no `gds` run; `gds` 35821375890 kept running.
- [x] `check_all.sh` passes and sigrok decodes a UART VCD: `check_all: PASS` (4/4 tests; an injected "ignore enable" bug made 1 test fail), `sigrok_smoke.py` ok.

- After the first push (commit 0786358): `test` green (run 35821375912); `docs` red on every push so far (run 35821375894). Cause: TT `--check-docs` rejects the template placeholder text in `docs/info.md`. Filled in `docs/info.md` for the placeholder counter; `tt_tool.py --check-docs` now passes locally.
- `scripts/sigrok_smoke.py`: writes a UART 8N1 VCD and checks that `sigrok-cli`'s `uart` decoder returns "TRIPWIRE"; added to `check_all.sh`. `check_all.sh` → PASS.

- `docs/design/ISA.md` written early (D-006 exception): research on PIO, PRU, Loom, FlexIO, P2 smart pins, XMOS, PSoC UDB and Triggered Instructions; one shared op table, implicit readiness checks, flag result from every op, K constants, head-bit test (D-007); Q1–Q6 given proposed resolutions. `ARCHITECTURE.md` §5.2/5.3/6.1 now point to it.
- Phase 1 reordered to model-first (D-008); phase 1 doc updated.
- Honesty fixes: V1 relabelled `[OURS]` (a Hardcaml entry already bounds pin timing statically); survey count marked stale; Loom's utilisation corrected to 78.8% (was ~51%).

- Jane Street sign-up form submitted (team). `fpga` dispatched manually: run 35823310537 on 9fdcf93.
- `scripts/gl_local.sh`: local gate-level run with the pinned PDK and TT Icarus 13 (cached in `~/.cache/tripwire`); `gl_local: PASS` 4/4, and it fails with the CI error when the UDP line is removed.
- [x] Jane Street box reworded to "emailed or deferred with a DECISIONS entry" (team decision) and ticked: form submitted, D-003 deferral.
- Roles: team chose to list Kanishk and Krithik as contributors in the README, no per-role split; box ticked.
- `gl_test` failed in gds run 35821375890 (BUGS #1): the template's `test/Makefile` omits the PDK's `sg13cmos5l_udp.v`. Added it. Verified locally with TT Icarus 13 and a Yosys cmos5l netlist: template fails identically, fix passes 4/4. In the same run, `gds` (30.3 min), `precheck` (13.5 min) and `viewer` passed. Only `gl_test` failed.
- [x] `gds` all green: run 35824649426 (9bd6f7d, manual): gds, precheck, gl_test, viewer. BUGS #1 fix confirmed on the hardened netlist. **All phase 0 exit boxes ticked.**
- `docs/reports/AREA.md` row 1 from the `GDS_logs` artifact of run 35824649426: 79 logic cells (8 flops), 0.13% utilisation, setup slack +13.6 ns at the slow corner, zero overflow, DRC/LVS/antenna clean. Magic DRC takes ~25 of the 27 flow-step minutes even on an empty tile.
- Clarified in PHYSICAL_DESIGN_AND_CI §5 and CLAUDE.md: the 6 h limit is per job (the `gds` job), not per workflow.
- Team: design for 6x4; tile-size and SRAM questions not being emailed for now (D-003); R3 settles the SRAM macro.
- [x] `fpga` run once: 35823310537 green.
- [x] Pages viewer live: https://kanishk234.github.io/protocol-emulator-asic/ (gds run 35821375890: `gds` and `viewer` green; `precheck` and `gl_test` still running at time of writing).

Problems / decisions:
- D-002 keeps `tt_um_tripwire` despite TT's uniqueness advice; rename path noted.
- `sigrok-cli` not installed yet (needs sudo).

Next:
- User: `sudo apt install sigrok-cli`; commit and push (triggers first `test`, `docs`, `gds`); enable Pages (Source = GitHub Actions); run `fpga` once by hand; confirm the repo is public.
- User: Jane Street sign-up form + email (D-003); assign roles (then Claude writes them into the README).
- Claude: sigrok UART VCD decode check in `check_all.sh`; record CI results and AREA row 1.

## 2026-09-22: team (phase 0, not started)
Done:
- Research and idea selection (TRIPWIRE).
- Design docs written: `docs/design/` (overview, architecture, verification, physical design & CI, phase 0–7 docs).
- `CLAUDE.md` created.
- Template (cmos5l branch) cloned locally in WSL.

Checklist boxes ticked (evidence):
- none yet

Next:
- Phase 0, task 1: create the GitHub repo from the local template clone, rename the top module to `tt_um_tripwire`, commit the docs.