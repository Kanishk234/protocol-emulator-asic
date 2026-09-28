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

## 2026-09-28: Codex (phase 2: D-044/D-045 model confirmation)
Done:
- Added focused D-044 coverage for a port reconfiguration cancelling a same-clock take, and D-045 coverage for no fetch during EXEC/waiting plus RPC advance at fetch.
- Recorded the model confirmation of the D-044 and D-045 readings in `docs/DECISIONS.md`.
- Added a fractional CARRIER check for D-051 P-G26. It exposes a model/spec-reading disagreement for 5.5-clock periods; recorded as proposed D-058 without changing behavior.

Evidence:
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py`: **48 passed**.
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py tools/tripsim/tests/test_pinregs.py`: **67 passed**.
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py -k fractional_carrier`: **1 passed**; rounding the period to whole clocks killed the test.
- Revert mutation removing D-044's take cancellation failed (`port.takes` became 1); removing the D-045 fetch guard failed during EXEC; removing the RPC increment failed the RPC assertion.
- `git diff --check`: clean.

Checklist boxes ticked:
- None. L2 remains unstarted; D-051–D-055 and the count/budget decision are still pending.

Problems / decisions:
- No disagreement with D-044/D-045 readings found. D-057's P-G24/P-G25/P-G28 proposals and D-058's P-G26 proposal remain unresolved; none of their semantics changed.
- The Phase 2 RTL checklist L1 edit is an existing, separate workspace change and is not part of this model session's code changes.

Next:
- Continue focused tests and revert mutations for P-G24–P-G47, recording any contested reading through DECISIONS before changing semantics.
- Obtain the count/budget decision, then audit remaining count-bound tests. Start L2 only after all prerequisites are ready.

---

## 2026-09-28: Codex (phase 2: implement approved D-041 A/B)
Done:
- Recorded Krithik's approval on behalf of both teammates for D-041 A (every pin-config word write restarts that unit and clears sticky flags) and B (pin units stay inactive until the first valid RUN or STEP) in `docs/DECISIONS.md`.
- Implemented restart state and `t_cfg` event epoch in `tools/tripsim/pinunit.py`; pin-config writes through the host map now apply the same rule. The RUN readback reports `live` at generated `HOST_RUN_LIVE_BIT`.
- Gated pin-unit RX/TX compute and commit until `Chip.run()` or an eligible STEP. Updated direct pin-only model fixtures to RUN an empty lane first. Updated P8/H1 in `ARCHITECTURE.md` to record the approved semantics.
- Added D-041 A/B tests; mutation checks that zeroed `t_cfg` and bypassed live gating both failed their focused tests.

Evidence:
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py`: **45 passed**.
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py tools/tripsim/tests/test_pinregs.py`: **64 passed**.
- `source .venv/bin/activate && pytest -q tools/tripsim/tests -k 'not uart_tx_shift_decoded_by_sigrok'`: **106 passed, 2 deselected**.
- With sigrok present, high-rate UART decode and CAN sigrok assertions produce empty decoder output despite passing model-side protocol/reference assertions. A protocol-kernel run without the sigrok assertions was started but interrupted before a final result; kernel-suite status remains unverified.

Checklist boxes ticked:
- None. L2 remains unstarted and no CI run was performed.

Problems / decisions:
- D-041 A/B are approved and implemented. D-046 host pin-config writes now work while all lanes are halted and trigger A; valid RUN/STEP activates units and the RUN status exposes B.
- The initial D-044 F5/invalid-select checks and D-045 fetch timing/ignored-write tests remain, but D-044 same-edge config-vs-take and D-045 no-fetch-while-waiting/RPC mutation coverage are still open.
- D-051–D-055 still need per-reading `test_semantics.py` tests and revert mutations. D-057 records P-G24/P-G25/P-G28 discrepancies as a proposal; no behavior change made for them.
- Lane/unit counts remain the frozen 3/6. The count-bound test assumptions found in `test_pinregs.py` now use the generated feature list; the team budget decision is still needed before any spec count change.
- No BUGS entry was added for empty sigrok output because its root cause was not established in this model session.

Next:
- Complete D-044/D-045 focused tests and mutations; review every P-G24–P-G47 reading in D-051–D-055 and add focused tests/mutations, resolving disagreements through DECISIONS before behavior changes.
- Obtain the area/count decision, audit count-bound tests, and begin L2 only when all model prerequisites pass.

---

## 2026-09-28: Codex + Krithik (phase 2: L1 checklist)
Done:
- Marked Phase 2 exit box 3 (L1 unit tests) complete using the green `unit` workflow on `main` at c2a1c04.

Checklist boxes ticked (evidence):
- [x] L1 unit tests all green: GitHub Actions `unit` run 36456739733.

Problems / decisions:
- None.

Next:
- Run the model-side L2 prerequisites in a session that does not read `src/`; wait for R4 run 7 before deciding the area budget and D-056.

## 2026-09-28: Codex (phase 2: model-side L2 prerequisites)
Done:
- Added address-based `Chip.host_read()` / `host_write()` for the approved D-042 flags, D-044 port/DROPPED registers, and D-046 control/status, lane debug, HOST_IN/HOST_OUT, and SRAM map. Address ranges and names come from generated `HOST_MAP`; port source ordering comes from generated `LEGAL_SOURCES`.
- Made default lane/unit counts derive from the frozen generated fabric and pin feature definitions. Changed `test_pinregs.py` count assumptions to use `PIN_UNIT_FEATURES`.
- Added focused semantics checks for flag W1C, D-044 F5/same-edge load and clear, out-of-range `sel`, D-046 tagged HOST_IN and lane debug, plus D-045 fetch/EXEC timing and ignored running-lane writes.

Evidence:
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py tools/tripsim/tests/test_pinregs.py`: **61 passed**.
- Full `tools/tripsim/tests`: **103 passed, 2 failed** (the same high-rate UART sigrok cases; 1,000,000 and 921,600 baud).
- Mutation checks: forcing D-042 reads to zero failed `test_d042_unit_flags_are_readable_and_write_one_to_clear`; inverting the D-044 F5 sequence snapshot failed `test_d044_host_port_map_f5_and_dropped_clear`.
- Full `tools/tripsim/tests`: **102 passed, 2 failed** in high-rate UART TX sigrok cases (1,000,000 and 921,600 baud, sigrok decoded no bytes); failure reproduced in isolation. Root cause not established, so no BUGS entry or claim that this was pre-existing.

Checklist boxes ticked:
- None. L2 has not started; this session did not establish the required million-clock lockstep or injection evidence.

Problems / decisions:
- D-044 readings are consistent with model behavior: source `seq` is snapshotted when the host writes the port, an out-of-list `sel` resolves to no source, and config takes precedence because the host configuration is applied before the model's next fabric edge. F5 and invalid `sel` have focused tests; the config/take case still needs a precise same-edge model test and mutation.
- D-045 readings are consistent with the model's registered SRAM rotation and pipeline; focused tests cover fetch-to-EVAL/EXEC and ignored STEP/host writes while running. Mutation coverage is still needed.
- D-051–D-055 readings have not yet each been reviewed and pinned by new `test_semantics.py` tests/mutations. Do not count this prerequisite complete. P-G24, P-G25 and P-G28 were checked in source and recorded in D-057, but still lack focused test/mutation evidence.
- D-057 now records three concrete proposed clarifications from the review: P-G24 zero-tick duration, P-G25 sub-2-clock carrier, and P-G28 BITSYNC event generation/priority. No model behavior was changed for these unresolved comparisons.
- D-041 A/B remain pending. The exact missing decision is Krithik and Kanishk's approval or rejection of: **A**, any write to a pin-unit config word restarts TX/RX/cursor/tick/prescaler and clears sticky flags; **B**, pin units and their producers remain inactive until the first RUN or STEP, including STEP setting `live`.
- Lane/unit spec counts remain 3/6. The team area/budget result (including the pending R4 run 7 / D-056 decision) is still needed before changing those frozen counts. Dynamic count handling is in place; the requested seven count-bound `test_pinregs` cases were not identified in this checkout and remain to audit against the settled budget.
- `host_read`/`host_write` model the register map, not SPI bit timing. Slot/K and owner writes plus packed channel debug readback are now covered. Pin-config writes still await D-041 A/B so their restart/live semantics are not guessed; full D-046 map support is therefore incomplete.

Next:
- Finish the D-046 host address paths and add focused D-044 configuration-vs-take coverage.
- Review every P-G24–P-G47 model reading in D-051–D-055, add one semantics test and a revert mutation per rule, and record disagreements as proposed DECISIONS/spec changes before changing model semantics.
- Obtain D-041 A/B and area/count decisions, finish count-bound tests, then begin L2 lockstep only after all prerequisites pass.

---

## 2026-09-28 (later): Krithik + Claude (phase 2: R4 run 6 result; count-generic tests; milestone B3)
Done:
- **R4 run 6** (gds 36384571157, the real `trw_chip` at the protocol floor): GPL 56.1 %, **global-routing overflow 5,350** (Metal3 87.3 %), detailed routing 16 violations after 64 iterations in 4 h 53 min, then cancelled by GitHub's 6 h limit in the antenna re-route; no artifacts. Read from the job log. `R4_FLOORPLAN.md` §12, AREA, D-043. The floor as built does not harden inside the TT `gds` job (a local hardening would not count: every entry uses the same workflow).
- **Count-generic tests** (BUGS #52): `tb_chan.v`, `tb_host.v`/`test_host.py`, `test_gen`, `tools/host` and `tripc` tests take the lane/unit counts from the spec. Pass at 3/6 (main: pytest 292, chan 7/7, host 7/7 under Icarus and Verilator) and at 2/4 (branch copy: pytest 285 + the 7 `test_pinregs` cases, all `rtl` suites, pin 52/52 ×2, chip 10/10).
- Area by block at the floor (Yosys, `synth/chip/run_chip.sh`): pin units ~201K, lanes 150K, fabric + producers 35K, host 22K.
- **Milestone B3** (Krithik: B3 first, then the area pass): readback and arbitration, bit errors, JAM responses and armed flags, listen-only, DELIM = flag with the hold-back and aborts, NRZI, SE0 with J, pin N low in SE0, DELIM = se0, OE auto, data[14] "own frame", a one-entry status EVENT register. Tests `test_pin_bs_b3.py` (7) against the reference CANNode (arbitration, ACK, error flags), `protomodels.hdlc` (±1 % drift, bad FCS, abort) and `protomodels.usb` line states (TX bit for bit, RX of four packets). Pin suites 59/59 on both builds under Icarus and Verilator; chip tests 10/10; mutants B3 34/34 and B2 31/31 killed; `scripts/check_all.sh` PASS. Engine 43.2K, full unit ~81.9K; chip 632.2K at spec counts (+7.09 typ / +0.02 slow), **407.6K at the protocol floor**. D-055 (readings P-G36–P-G47). Milestone B is complete.

- **RTL area pass** (behaviour-preserving, Krithik's order after B3): lanes −6.5K each (merged register read/write ports), TX −0.3K each, engine −1.1K; the floor chip 407.6K → **391.7K**. Lane 6/6 + 15/15 mutants; pin 59/59 both builds; milestone-B mutants 70/70 (the lean/full mutant filter fixed: B2/B3 mutants no longer run on the lean build). `R4_FLOORPLAN.md` §14.
- **Flow growth found:** run 6 grew 466.2K → 567.7K before routing (fanout repair +25.3K, clock tree +24K); hold repair was +52.3K at 1,891 endpoints, caused by the 0.25 ns clock uncertainty applying to hold. Locally at the fast corner (run 5's post-CTS netlist): 1,546 violations at 0.25 ns, 29 at 0.10 ns. **D-056 (proposed): hold uncertainty 0.10 ns.** R4 run 7 prepared (run 6's design + that change) in `~/tw-r4`. §13.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- Run 6: the chip must come down ~40–60K µm² (to run 5's ~340K) or change the floor. Needs the team (D-049/D-043); no D-055 written yet.
- 7 `test_pinregs` cases still hard-code U1 full (in `tools/tripsim/`, not read in this RTL session).

Next:
- Push R4 run 7 (hold uncertainty 0.10 ns); read hold endpoints, utilisation after GRT, overflow, DRT time, sign-off hold at every corner. Then D-056 for the team.

## 2026-09-28: Krithik + Claude (phase 2: milestone B2c; engine retimed; R4 run 6 prepared)
Done:
- **Milestone B2c** in `trw_pin_bs.v`: the TX queue (DATA, SYNC, LINE [2]/[6]/[3], WAIT [1]), TX stuffing, the TX CRC with CRC_XOR, our frame start and the join, the own-edge rules; pin A from the engine. Tests `test_pin_bs_tx.py` (5), including three CAN frames decoded and ACKed by the reference `CANNode` on a wired-AND bus. Pin 52/52 on both builds and under Verilator; B2 mutants 30/30 killed; chip tests 10/10. Engine 34.8K, full unit logic 73.8K. D-054 (readings P-G31 to P-G35).
- **Timing:** chip STA showed slow −9.80 ns through the engine (pin → bit-clock sums). Retimed with no behaviour change: +7.65 typ / +0.87 slow at spec counts (BUGS #51).
- **Host** at unit counts other than 6: width fixes (BUGS #50).
- **R4 run 6 prepared** on `spike/r4-floorplan` (worktree `~/tw-r4`, not committed): the real `trw_chip` at the protocol floor, 398.7K µm², ~56.4 % expected, density 59. Lint clean, `test/` 4/4, chip tests 10/10 at the floor's counts. `R4_FLOORPLAN.md` §11, D-043.
- R4 run 5's precheck **passed** (1 h 56 min, the KLayout DRC of the full GDS): run 5 is green end to end, 4 h 54 min in all.

Checklist boxes ticked (evidence):
- None.

Next:
- Push R4 run 6 (branch) when the user decides; read GRT overflow and DRC.
- B3: readback and arbitration, errors, flags, JAM, listen-only, NRZI, SE0, OE auto (P26–P29).

## 2026-09-28: Krithik + Claude (phase 2: milestone B2b; R4 run 5 routes clean)
Done:
- **R4 run 5 routes clean** (36363295528): 0 DRC, LVS match, 0 antenna, typ timing met, slow −6.0 ns (slot latch → flop), `gl_test` pass, `gds` job 2 h 58 min (detailed routing 1 h 58 min). The routable ceiling is between 47.6 % and 58.9 %. `R4_FLOORPLAN.md` §10, AREA row, D-043 result and the next proposal (a run at the protocol floor's size).
- **Milestone B2b** in `trw_pin_bs.v`: RX stuffing and stuff errors, the RX CRC, `FRAME n` and its verdict, `SETN` rx; the engine takes RX commands. Tests `test_pin_bs_frame.py` (6) against the CAN and HDLC reference models. Pin 47/47 both builds; mutants 17/17 lean, 36/36 full (one first-round gap fixed: a stuff error after bit n was detected but not reported). Engine 25.1K, full unit logic 62.3K. D-053.

Checklist boxes ticked (evidence):
- None (run 5 is the stand-in, not the real chip; precheck was still running).

Next:
- B2c: the TX queue, `LINE`/`SYNC`, the TX CRC.
- Team: the budget, with run 5 and the floor (D-049); a run at the floor's size is proposed (D-043).

## 2026-09-28: Krithik + Claude (phase 2: milestone B2a, the BITSYNC receive core)
RTL session, from `ARCHITECTURE.md` §14 P20–P22 and D-023–D-027; `tools/tripsim` not read.

Done:
- `src/trw_pin_bs.v` (new): bit clock, bus idle, frame start with hard sync, resync limited to SJW, RX words. `trw_pin_unit.v` instantiates it in full units and muxes loads (event generator first) and, until B2c, holds pin A recessive and takes nothing in BITSYNC. Added to every source list (pin/chip Makefiles, synthesis scripts, CI lint).
- `test_internal/pin/test_pin_bs.py` (3 tests, both builds): phases, idle drop, ±2 % drift with and without SJW, a 1-clock-late edge. Pin 41/41 both builds; 7 B2 mutants killed; chip lint and tests unchanged.
- Area: a first version was 20.2K; one timer and one signed correction brought it to 16.1K. Full unit logic 54.0K. BITSYNC is heading for ~30K vs ~16.7K estimated (D-052); this raises the D-049 floor by ~2 % of the core.

Checklist boxes ticked (evidence):
- None.

Next:
- B2b: stuffing, the RX CRC, `FRAME` and the verdict (P23, P24).

## 2026-09-28: Krithik + Claude (phase 2: pin-unit milestone B1, PULSE and carrier)
RTL session, from `ARCHITECTURE.md` §7 and §14 P17, P30; `tools/tripsim` not read.

Done:
- Milestone B planned in three stages (`PIN_UNIT_RTL.md` §9): B1 PULSE + carrier, B2 BITSYNC core (P20–P25), B3 BITSYNC readback/JAM/flags/NRZI/SE0 (P26–P29). Krithik agreed that verification-infrastructure items (pyuvm, L9) can wait while the RTL phase needs RTL.
- **B1 done:** `trw_pin_tx.v` (`FULL`): PULSE bursts in whole ticks with back-to-back joining; the carrier with a fractional half-period timer. `trw_pin_unit.v` passes the fields. Lint clean both builds; chip lint and chip tests unchanged.
- `test_internal/pin/test_pin_full.py` (4 tests, both builds); pin suite 38/38 lean and full; `mutate.sh` handles `FULL` and the B1 mutants: 17/17 lean, 21/21 full.
- Area: full unit logic 37.9K µm² (+7.7K).
- D-051: three readings (P-G24–P-G26) for the model side.

Checklist boxes ticked (evidence):
- None.

Next:
- B2: the BITSYNC core (P20–P25).

## 2026-09-28: Krithik + Claude (phase 2: protocol floor, L1-ROT, L0-ASRT, L-XSIM, L8-EQY)
Done:
- **D-049 (proposed), the protocol floor**, from Krithik's constraint that every protocol must stay supported (not at the same time). From the 20 compiled programs: ≥ 2 lanes, ≥ 4 units with U0 full (U1 may be lean), 12 slots, the 512-word SRAM. That is ≈ 395K µm² ≈ 56 % at placement, inside the window R4 has not measured (run 4 47.6 % routed globally, run 3 58.9 % did not).
- **L1-ROT** (`test_internal/chip/test_rot.py`): all three lanes store/load through the SRAM while the host reads; every clock only the slot's owner drives the SRAM; every store lands. `test_internal/chip/mutate.sh`: 2/2 mutants killed. Added to the CI `rtl` job. L1-OVR already existed (`test_pin_rx.py::test_overrun_keeps_the_old_token`).
- **L0-ASRT**: `src/trw_assert.vh` (`TRW_ASSERT`, `TRW_ASSERT_ON`); invariants in `trw_pin_unit` (open drain never drives high; RX never loads a full producer), `trw_pins` (a driven pad has an owner), `trw_lane` (never takes an unavailable input; never loads a full output), `trw_chan_port` (a disabled port shows no token), `trw_chan_prod` (no load while full). `SIM_ASSERT` is on in every `test_internal` Makefile; all suites pass with it; two planted bugs trip their assertions. Under `FORMAL`: `formal/l0_asrt.sby` proves the pads and producer invariants unbounded (k-induction); a planted bug fails the proof. Plain and `SIM_ASSERT` builds lint clean.
- **L-XSIM**: every suite passes under Verilator 5.053 (venv cocotb 2.0.1) as under Icarus: 101 L1 + 10 chip/L3/ROT. The pin Makefile passes parameters per simulator; the chip Makefile uses `--timing -Wno-fatal` for the macro model under Verilator. New CI job `rtl-verilator` (OSS CAD Suite pinned and cached like the `efpga` branch).
- **L8-EQY feasibility (D-050)**: the PDK's Verilog cell models are not readable by Yosys; liberty-derived models + a SAT miter prove the ALU's netlist equivalent (and reject a wrong RTL). `formal/equiv.sh`.

Checklist boxes ticked (evidence):
- None (L1 still needs BITSYNC cases, which wait for milestone B / the budget).

Problems / decisions:
- **Not added: a `formal` workflow.** The `efpga` branch (a separate eFPGA design) already has `.github/workflows/formal.yaml` and `formal/*.sby`; a second one on `main` would collide if it is ever merged. Krithik and the teammate decide the naming.

Next:
- R4 run 5; the budget with D-049 as its floor; the pyuvm skeleton; the L9 Hardcaml spike.

## 2026-09-27: Krithik + Claude (phase 2: CI for the RTL suites, first claim, BUGS #49)
Done:
- R4 run 5 launched on the branch (`gds` 36363295528, `DRT_OPT_ITERS` 64, e20d390).
- Gate-level run of the chip after the BUGS #48 fix: `test_chip` 5 + `test_l3` 4, **9/9 pass** (TT Icarus 13).
- `docs/CLAIMS.md`: claim 1 (the three L3 programs on the chip RTL, simulated only) and a "Known limits" section (host link throughput: continuous UART RX above ~460 kbaud overruns at SCK = clk/8).
- `unit` workflow: new job `rtl` (VERIFICATION.md §10 puts L1 there): whole-chip Verilator lint, every L1 suite, the pin unit lean and full, the macro model fetch, and `test_chip` + `test_l3` on the chip RTL; results uploaded. First run will show whether Ubuntu 24.04's Verilator 5.020 agrees with the local 5.053.
- BUGS #49: STEP now also makes the pin units live (D-041 B). L1-HOST 7/7, mutant killed.
- `docs/HANDOFF.md` (local, not committed) for the next agent.
- **L3 extended** to every rate the shipped programs support (`test_internal/chip/test_l3.py`): UART TX 9600/115200/1M, UART RX 115200/460800 with a framing error, SPI mode 0 at 1/5/8.3 MHz, I2C 100k/400k/1M with no, short and longer-than-a-period stretching. **4/4 tests (12 configurations) pass on RTL**, reference models + sigrok. `chiplib.start(clock=...)` so a test can reset between configurations without stacking clocks.
- **D-048 (proposed):** judge the phase 2 L3 box on what the shipped programs implement; parity, SPI modes 1–3 / 16-bit and I2C arbitration loss move to phase 3 with the program work they need.

Checklist boxes ticked (evidence):
- None.

Next:
- R4 run 5 result; the area budget; D-048 (L3 scope) with Kanishk.

## 2026-09-27: Krithik + Claude (phase 2: L3 on the chip RTL, R4 run 4 result)
Done:
- **R4 run 4** (36349736069, 2 lanes, density 51) read from `GDS_logs` (`build/ci/r4/run4/`): GPL 47.6 %, **0 global-routing overflow** (Metal3 74.2 %); detailed routing 874 violations after the 4 iterations `DRT_OPT_ITERS` 3 allows (still falling), 1,428 after the antenna re-routes; typ met, slow −5.98 ns; job 2 h 55 min. `R4_FLOORPLAN.md` §9, AREA.md row, D-043 result and run 5 proposal.
- **L3 on the chip RTL** (`test_internal/chip/test_l3.py`, pins only, programs compiled by tripc and loaded with `tools/host`): UART TX at 1 Mbaud and 115200 (reference line model + sigrok `uart`), UART RX at 460800 with a framing error, SPI controller mode 0 at 5 MHz against the reference target (+ sigrok `spi`, both directions), I2C controller at ~400 kHz with 40-clock stretching: writes, a NACKed address, repeated START, reads (+ sigrok `i2c`). **4/4 pass.** Shared helpers in `test_internal/chip/chiplib.py` (host polling that drains HOST_OUT, a pad environment stepping the reference models, a VCD writer, sigrok).
- **BUGS #48** found by L3 and fixed in `trw_host.v`: a status+data burst could take a token the status had not shown. New L1-HOST test and mutant; L1-HOST 6/6.

Checklist boxes ticked (evidence):
- None. L3 passes on the RTL for the cases above, but VERIFICATION.md §6 asks for more (UART 9600 and 8E1/parity, SPI modes 1–3 and 16-bit, I2C 100k/1M and arbitration loss), and the tests belong in `test/` once the top is switched.

Problems / decisions:
- UART RX faster than ~460 kbaud overruns: the host at SCK = clk/8 needs ~560 clocks per HOST_OUT read. A protocol limit of the host link, not of the chip; worth a CLAIMS note.
- Run 5 (proposed): `DRT_OPT_ITERS` back to 64.

Next:
- Team: run 5; then the area budget (the RTL chip at 2 lanes / 6 units is ~62 % at placement; run 4 routed globally at 47.6 %).
- L3: the remaining §6 cases.

## 2026-09-27: Krithik + Claude (phase 2: the whole chip, trw_chip)
RTL session; `tools/tripsim` not read. R4 run 4 still running.

Done:
- **`src/trw_chip.v`**: every block wired (D-047), lane/unit counts generated from the spec (`TRW_LANES` etc.). `src/trw_sram.v` from R3. `trw_pin_cfg.v`: `FULL` test made width-clean for Verilator. Whole chip Verilator `-Wall` clean.
- **Chip tests** (`test_internal/chip/`, pins only, `tools/host` frames at SCK = clk/8): identity/time/SRAM/E2, lane forwarding, UART TX on U0 (full) and U3 (lean), a routine with LD/ST, and `uart.trw` loaded with `tools/host.load_sequence` and looped back. **5/5 RTL, 5/5 gate level** (Yosys netlist, TT Icarus 13).
- `synth/chip/run_chip.sh`: **517.4K µm² + macro (~62 % of the core, ~72 % at placement)**; +10.36 typ / +4.94 slow pre-layout, worst slow path from the SRAM output into EVAL.
- All L1 suites and `pytest` re-run: pass.

Checklist boxes ticked (evidence):
- None. "All modules exist and lint clean" waits for `tt_um_tripwire.v` to become the wrapper (the switch, D-047).

Problems / decisions:
- The chip at spec counts does not fit (~72 % at placement vs. a routable ceiling below ~59 %). `info.yaml` stays on the placeholder until the budget is set.

Next:
- Run 4 result → the area budget (lanes, full units, slots) → the switch: wrapper, `info.yaml`/`test/`, `config.json` (SRAM block, latch SDC, density) with their entries → the first real hardening on `main`.

## 2026-09-27: Krithik + Claude (phase 2: tools/host)
Done:
- **`tools/host`** (phase 2 task 2.3 item 7): §9 frames (`frame_write`, `frame_read`), the D-046 map from `tripwire_spec.py`, `load_sequence(image)` (every §14 H1 write: halt, all 6 unit blocks, all owners, all 13 ports, each used lane's 12 slots + K + r0–r3/STATE, SRAM, RUN), a `Host(xfer)` client (run/halt/step, lane debug block, unit flags, HOST_IN push with the busy check, HOST_OUT pop) and a `RegisterModel` to check sequences offline.
- `tripc` now emits `pin_regs` for every unit (defaults for unused ones), so a load writes every block (task 2.3 item 8 with the ports and owners in `load_sequence`).
- Tests (`tools/host/tests`): frames, encodings, the load sequence of all 20 programs checked register by register, the client against a fake chip. `pytest -m "not slow"`: 292 passed.

Checklist boxes ticked (evidence):
- None.

Next:
- Run 4 result, then the real top: the pin-level tests in `test/` will drive it through `tools/host` frames.

## 2026-09-27: Krithik + Claude (phase 2: host map in the spec, host RTL)
RTL session; `tools/tripsim` not read. R4 run 4 still running.

Done:
- Krithik approved D-042, D-044, D-046. `spec/tripwire.yaml` v1.2 gets `host_map`; `gen.py` generates the Verilog constants (`TRW_HA_*`, `TRW_HL_*`, `TRW_IRQ_*`, ID, version), the Python tables (`HOST_MAP`, …) and the §9 table, with validation (no overlapping blocks, consistent with `pin_config` and the fabric). 1 new generator test; `pytest -m "not slow"`: 269 passed.
- `src/trw_spi.v` (SPI engine from the R4 stub) and `src/trw_host.v` (the map: control, IRQ, write strobes, read multiplexer, SRAM host slot). Verilator `-Wall` clean. 24.8K µm².
- BUGS #47: a prefetch of the next read word took the HOST_OUT token; now taken only when the word is shifted out.
- L1-HOST (`test_internal/host/`): 5 tests through the pads (2-FF, SCK = clk/8), 12/12 mutants killed. All L1 suites re-run after the defs change: chan 7, alu 4, lane 6, slots 2, pins 1, host 5, pin 34 + 34, all pass.

Checklist boxes ticked (evidence):
- None yet: every module of the §2.1 table now exists except the real top; the box needs them wired and linted as one design.

Problems / decisions:
- The R4 branch's host stub still has BUGS #47 (it does not affect run 4, which measures routing).

Next:
- Run 4 result; then the real top (`tt_um_tripwire.v`) with the lane count it gives, `info.yaml`/`test/Makefile`, the SRAM macro and latch SDC in `config.json` (DECISIONS entries), and `tools/host`.

## 2026-09-27: Krithik + Claude (phase 2: slots, pads, host map proposal)
RTL session; `tools/tripsim` not read. R4 run 4 still running.

Done:
- `src/trw_slots.v` from the spike: write-only (the debug read port is gone, D-039), slot word 3 stores its 5 bits. 24.5K µm² (700 latch bits, 52 clock gates), as before. L1 (`test_internal/slots/`): 2 tests on the latch array and the flop build (`FLOPS=1`), both pass.
- `src/trw_sync.v` (2-FF, P1) and `src/trw_pins.v` (owner registers and the pad multiplexer, §7.1; host pads ignore owner writes). L1 (`test_internal/pins/`): 1,500 random clocks against the ownership rule, pass. Verilator `-Wall` clean on all three.
- D-046 (proposed): the full host register map (control/status, lane debug block, HOST_IN/HOST_OUT status, IRQ), so `trw_host.v` can be written.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- The host RTL waits for D-046, D-044 and D-042 (all proposed).

Next:
- Krithik/Kanishk: D-042, D-044, D-046. Then `trw_host.v` and `tools/host`.
- Run 4 result; then the top that wires everything (lane count from run 4).

## 2026-09-27: Krithik + Claude (phase 2: lane and ALU RTL)
RTL session, from `ISA.md` §2–§5 and `ARCHITECTURE.md` §5, §6, §14; `tools/tripsim` not read. R4 run 4 still running.

Done:
- `src/trw_alu.v` (from the R1 spike, unchanged) and **`src/trw_lane.v`**: the R1 lane checked against D-035 and §14 L12, plus the routine controller (RPC, RIR, CALL entry read, BR, DJNZ, LD/ST, OUT, SYS), STEP (H2), host writes to r0–r3/STATE (E2), `out_load` for the fabric (F4). Verilator `-Wall` and Icarus clean.
- Two latent spike bugs fixed on the way: BUGS #45 (BSEL 3), #46 (GETT time).
- L1-ALU (`test_internal/alu/`): 4 tests, 8/8 mutants killed. L1 lane (`test_internal/lane/`): 6 tests covering L1-EVAL (400 random cases against ISA §4.2–4.3) and L1-PIPE, the routine controller, urgent vs routine, halt/STEP/host writes; 15/15 mutants killed.
- Yosys: 51.5K µm² per lane with the ALU (+9.6K vs the spike). AREA.md.

Checklist boxes ticked (evidence):
- None (L1 still lacks OVR, ROT and HOST; the lane is not in the top yet).

Problems / decisions:
- D-045: three readings for the model side (fetched word competes in clock k+1; no fetch while a step is in EXEC or waiting; STEP/host writes ignored while running).
- The fetched-word path (macro clock-to-output into EVAL) is not timed yet.

Next:
- Run 4 result.
- `trw_slots.v` to `src/`, then a top that wires lanes, fabric, pin units and SRAM (and the host), so pre-layout STA and a real `gds` run can start.

## 2026-09-27: Krithik + Claude (phase 2: channel fabric RTL)
RTL session, from `ARCHITECTURE.md` §4 and §14 F1–F7; `tools/tripsim` not read. R4 run 4 (2 lanes) running on the branch meanwhile (`gds` 36349736069).

Done:
- `src/trw_chan_port.v` (consumer port: legal-source mux, en/tap/sel/accept registers, last_seq, DROPPED; F1, F2, F4, F5, F7) and `src/trw_chan_prod.v` (producer register; F3, F6).
- `src/trw_fabric.v` **generated** by `tools/gen/gen.py` from the spec's legal sources (13 ports, 13 release terms); `gen.py` also exports `FABRIC_PRODUCERS` / `FABRIC_CONSUMERS` in `tools/tripwire_spec.py`. 2 new generator tests (38 in `tools/gen/tests`).
- L1-CHAN in `test_internal/chan/`: fabric plus a producer register on all 13 producers, checked against a model of F1–F7 every clock. 7 tests: 0–4 blocking × 0–2 tap subscribers (delivery exactly once and in order, DROPPED exact), registered release, DROPPED saturation and clear, accept filter, re-pointing, sel past the list, 6,000 random clocks. **7/7 pass; `mutate.sh` 10/10 killed.**
- Yosys: fabric 44.4K µm² (AREA.md).
- Not in `info.yaml` / `test/Makefile` yet: the modules join when the top wires them.

Checklist boxes ticked (evidence):
- None (L1 is not complete until ALU, EVAL, PIPE, OVR, ROT and HOST exist).

Problems / decisions:
- D-044 (proposed): port registers at `0x2000 + c`, DROPPED at `0x2040 + c` (write clears), and three readings of F5 / sel / write-vs-take for the model side.
- `pytest -m "not slow"`: 268 passed; `lint`: Verilator `-Wall` and Icarus clean on the three files.

Next:
- Krithik/Kanishk: D-044 (and still D-041 A/B, D-042).
- Run 4 result when it finishes.
- RTL: the host (`trw_host.v`, §9) or moving the R1 lane into `src/` (with an `out_load` output for F4 tap drops on lane producers).

## 2026-09-27: Krithik + Claude (phase 2: R4 run 3 result)
Done:
- R4 run 3 (36327551624, 462bf06, `CTS_APPLY_NDR` = `none`) ran the full flow in 5 h 25 min; `GDS_logs` read locally (`build/ci/r4/run3/`, not committed).
- **Global routing ended (4 min): overflow 4,883, 4,651 on Metal3 (92.8 % usage). Detailed routing: 6,004 violations after the first pass, 12,872 at the end. The full chip does not route at 58.9 % / 65.9 %.** ~74 % of the violations are in the lanes' area (approximate, by net names).
- `R4_FLOORPLAN.md` §7, AREA.md row, D-043 result and run 4 proposal.
- Run 4 approved and set up: `localparam NL = 2` in the R4 top, `gen_fabric.py` reads it; density 51. Yosys 337.4K µm² (−80.3K); `check_local.sh` PASS (lint, 5/5 RTL, 5/5 gate level). `R4_FLOORPLAN.md` §8.
- Checked: all 20 programs use at most 2 lanes (CAN, LIN, IR NEC use 2), so every protocol still runs with 2 lanes, only fewer at once.
- Fixed: the run 3 docs cited D-041 for the area budget; it is `AREA_ESTIMATE.md` / D-038–D-040.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- GitHub's live log stops at ~38.6K lines (in CTS), so a running R4 job cannot be followed; wait for the end.
- LibreLane failed parsing netgen's JSON after the LVS mismatch, so precheck did not run (tool issue, only when LVS already fails).
- Proposed run 4: 2 lanes instead of 3 (D-043). The routable ceiling bears on the area budget (`AREA_ESTIMATE.md`, D-038–D-040).

Next:
- Krithik: commit, then push `spike/r4-floorplan` for run 4; collect `GDS_logs` into `build/ci/r4/run4/`.
- Team: revisit the area budget (`AREA_ESTIMATE.md`) with run 3 and run 4.

## 2026-09-27: Krithik + Claude (phase 2: R4 run 2 result)
Done:
- R4 run 2 (36279959944, ed3b949) read from the job log with `gh api` (cancelled at the 6 h limit, so no `GDS_logs`).
- **Placed at 58.9 %; CTS, hold repair (3,067 buffers) and detailed placement passed; global routing never ended.** It had overflow after 50 iterations and then relaxed the clock NDR one net at a time (GRT-0273) for 5 h 51 min. No overflow figures were printed.
- `R4_FLOORPLAN.md` §6, AREA.md hardening row, D-043 run 2 result and run 3 proposal.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- Any run with global-routing overflow will time out the same way while clock NDRs are on (LibreLane `CTS_APPLY_NDR` = `half` by default).
- Proposed run 3: `CTS_APPLY_NDR` = `none`, same design, to get the overflow numbers (D-043).

Next:
- Krithik: approve or change run 3; then Claude edits the branch `config.json` and gives the commands.

## 2026-09-26: Krithik + Claude (phase 2: R4 run 2 setup)
Done:
- Run 1 ID found with `gh`: 36269756517; added to AREA.md and R4_FLOORPLAN.md.
- **R4 run 2 (approved): 4 pin units.** `localparam NU` in the R4 top; `gen_fabric.py` reads it and leaves out the absent units' TX ports; density 73 → 62.
- `check_local.sh`: PASS (lint clean, 5/5 RTL, 5/5 gate level). Yosys 417.7K µm² (−81K); expected GPL ~60 %; slack +10.28 typ / +5.08 slow.
- D-043 run 2 entry, `R4_FLOORPLAN.md` §5, AREA.md synthesis row.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- The `gds` run 36278610622 on `main` came from the P34/P38/P43 RTL push; the pin-unit files are not in `info.yaml`, so it rebuilds the same chip.

Next:
- Krithik: push run 2 on `spike/r4-floorplan`; collect `GDS_logs` into `build/ci/r4/`.

## 2026-09-26: Krithik + Claude (phase 2: R4 run 1 result)
Done:
- Read `GDS_logs` of R4 run 1 (`spike/r4-floorplan`, 1ca1bdc; unpacked in `build/ci/r4/`, not committed).
- **Result: failed at placement, before routing** (DPL-0036 in `ResizerTimingPostCTS`).
  - Global placement utilisation 70.0 % (predicted ~71 %); 70.5 % after the fanout repair and CTS.
  - The hold repair added 3,921 buffers (+10.1 %, 2,315 endpoints), taking it to ~77 %; 43 instances could not be legalized.
  - Setup clean (typ +8.94 ns mid-PnR). Hold at typ is mostly on the SRAM inputs (−0.65 ns, 0.46 ns clock skew).
  - ~5 min of flow time.
- `R4_FLOORPLAN.md` §3–4, AREA.md hardening row, D-043 outcome and the run 2 proposal.
- Also fixed `sources.sh` (it failed when writing into `src/` itself on the branch).

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- The run ID is not in the logs; to add to AREA.md and R4_FLOORPLAN.md.

Next:
- Krithik: approve run 2. Proposed: 4 pin units (a unit-count parameter in the R4 top), density = the new GPL utilisation + 2.

## 2026-09-26: Krithik + Claude (phase 2: pin unit follows D-041)
RTL session, from `ARCHITECTURE.md` §14 P31–P45 (D-041); `tools/tripsim` not read. R4 launched first (branch `spike/r4-floorplan`, 1ca1bdc).

Done:
- **P-G7 → P34 (changed):** a CLK taken in a burst's final-release clock (with STRETCH: the clock the line reads IDLE) extends the burst instead of starting a new one.
- **P-G12 → P38 / P8 (changed):** EV_RESET restarts framing before the event clock's sample, which becomes bit 0 of the new word.
- **P-G20 → P43 (changed):** TX_EDGE code 3 acts as none (timed shift); it made the unit linked on the fall.
- **P-G9 → P36, P-G22 → P44:** the RTL already complied; both are now pinned by tests.
- 7 new L1 tests (34 in all), passing on the lean and full builds. `mutate.sh`: 4 new mutants (old P34/P38/P43/P44), 3 stale ones updated to the FRAC/P38 source, and an `ONLY=` filter; **16 of 16 caught**.
- `PIN_UNIT_RTL.md` §6: the resolution of each gap.

Checklist boxes ticked (evidence):
- None.

Next:
- R4 run 1: collect `GDS_logs`, fill `R4_FLOORPLAN.md` §3–4 and the AREA.md row.
- Proposals A/B (D-041) and D-042 wait for Krithik and Kanishk; the RTL already does A, B and write-1-to-clear.

## 2026-09-26: Krithik + Claude (phase 2: R4 full-size floorplan spike, prepared)
RTL session; did not read `tools/tripsim` or `spikes/area/ae_prims.v`.

Done:
- **D-043:** R4 on branch `spike/r4-floorplan` (never merged), sources in `spikes/r4_floorplan/`. Contents: 3 R1 lanes without slot read-back, with routine sequencer stubs; 6 lean pin units with config latches; the fabric (13 producers, 13 ports, legal-source muxes generated from the spec by `gen_fabric.py`); the SRAM macro with the rotation; a host SPI stub that writes and reads back every block.
- Branch `config.json`: R3's macro block, density 73 (lowest legal, from the R2 synthesis-to-placement ratio), R2's latch SDC, `DRT_OPT_ITERS` 3. Every exception is listed in D-043.
- Size (Yosys, flat): **498.8K µm² + the 45.3K macro, ~71 % of the core at placement**; 2,592 flops, 2,814 latches, 210 clock gates; the per-module numbers match the earlier blocks. Pre-layout slack at 20 ns: +10.63 typ / +5.50 slow.
- `spikes/r4_floorplan/check_local.sh`: lint; 5 pin-level tests through the host stub, on RTL and on the Yosys gate-level netlist; Yosys area; pre-layout STA.
- `trw_lane` (spikes/r1_lane) gains a register debug output, connected in the R1 harness, its tb and the R2 overlay; `run_r1.sh` re-run: PASS, lint clean.
- BUGS #44 (host stub address assembly, caught by the local suite before any push). BUGS: moved the "Note on #1" below rows 41–43, which had landed outside the table.
- `docs/reports/R4_FLOORPLAN.md` (setup; results pending); AREA.md synthesis row.

Results:
- Local: lint clean; RTL 5/5; gate level 5/5 (evidence run of `check_local.sh` at the end of the session, below); `scripts/check_all.sh` on `main`.

Checklist boxes ticked (evidence):
- None (R4 answers a planning question; phase 2 task 2.0 stays open until the budget is decided).

Next:
- Krithik: run the branch commands (`spikes/r4_floorplan/README.md`). The push starts a `gds` run on the branch.
- Then: collect `GDS_logs`, fill `R4_FLOORPLAN.md` §3–4 and the AREA.md hardening row, and choose one change for run 2.
- RTL follow-ups from D-041: P-G7 (CLK in the final-release clock extends the burst), P-G9 (an edge in the clock after a preload is also ignored), and checks of P-G12, P-G20 (unnamed enum codes act as code 0) and P-G22.

## 2026-09-26: Krithik + Claude (phase 2: pin-unit RTL gaps answered, 4-bit fraction check)
Done:
- **The 23 pin-unit RTL gaps (P-G1 to P-G23) are answered in §14** as new rules P31 to P45 (plus edits to P8 and P13), recorded in **D-041**. Where the RTL's reading was better, the model now follows it.
- The model changed in 14 places, each pinned by a test (18 new tests in `test_semantics.py`), and each change was reverted once on purpose to confirm a test fails.
- The review found three real model bugs:
  - BUGS #41: SHIFT_RX stalled when a sample fell in an event clock;
  - BUGS #42: a preloaded bit hidden by a same-edge shift;
  - BUGS #43: CLKGEN drift with an odd PERIOD.
- Evidence: the full suite passed (271); the fast suite passes after the last test change (266); injected reverts of the 18 model changes are all caught (18 of 18); `gen --check` is clean.
- **The RTL must change in two places** (P-G7: a CLK in the final-release clock extends the burst; P-G9: an edge in the clock after a preload is also ignored), and should check three others (P-G12, P-G20, P-G22). Listed in D-041.
- **Proposed, awaiting approval:**
  - D-041 A: a config write restarts the unit;
  - D-041 B: pin units are live only after the first RUN/STEP;
  - D-042: write-1-to-clear status word per unit.
- **4-bit timer fraction, model side:** a new exploration knob, `TRIPSIM_FRAC=4`, rounds every time setting to 1/16 clock. With it, the full suite passes except the one test that checks the encoding is exact at 1/256 (253 of 254). So all 20 protocols work with 4-bit fractions. The RTL session is measuring the area side.

Checklist boxes ticked (evidence):
- None.

Next:
- Krithik/Kanishk: approve or change D-041 A/B and D-042.
- RTL session: the fraction measurement, then R4. Pass it the D-041 changes for the pin unit.
- 4-bit fraction: the RTL measured -1.9K µm² per lean unit (about 1.5 % of the core for six units). Not adopted; kept as a late option, since the model shows every protocol still works.

## 2026-09-26: Krithik + Claude (phase 2: 4-bit timer fraction, measurement)
Done:
- `FRAC` parameter (default 8) on `trw_pin_unit/tx/rx`: the cursor fraction, the burst timer, the SHIFT_RX timer, and the PERIOD/SAMPLEOFS inputs (top FRAC bits). No spec change.
- Threaded through the L1 harness (`make FRAC=4`) and `synth/pin/run_pin.sh` (`FRAC=4`, outputs in `build/frac4/`).
- `PIN_UNIT_RTL.md` §7: lean unit 29,790 → 27,903 µm² (−1.9K, −6 %), 216 → 204 flops, slow-corner slack +6.42 → +6.94 ns. Worth ~1.5 % of the core for six units, so not a big lever; recommendation: don't adopt it on its own.
- Tests: FRAC = 8, 27/27 (same function); FRAC = 4, 24/27 (the three 5.4-clock-period tests fail, as expected on a 1/16 grid). `scripts/check_all.sh` PASS.

Checklist boxes ticked (evidence):
- None.

Next:
- Task 2: the R4 full-size routability spike at 6x4 (branch `spike/r4-floorplan`).

## 2026-09-25: Krithik + Claude (phase 2: pin unit RTL, milestone A)
RTL session: worked from the documents and `spec/tripwire.yaml` only; did not read `tools/tripsim` or `spikes/area/ae_prims.v`.

Done:
- `tools/gen/gen.py`: Verilog output for `pin_config` (field positions, `TRW_PCE_*` enum codes, stored-bit masks per feature, units per feature) and a check that no two defines collide; 3 new generator tests. `src/trw_defs.vh` regenerated.
- RTL, not yet in `info.yaml`/`test/Makefile`: `trw_pin_cfg.v` (latch array, a clock gate per stored word, write-only, `FULL`), `trw_pin_io.v`, `trw_pin_tx.v`, `trw_pin_rx.v`, `trw_pin_unit.v`. Lean feature set for both builds; PULSE, carrier and BITSYNC are milestone B.
- The cursor needs no multiplier: it is kept relative to now in ticks (`PIN_UNIT_RTL.md` §1).
- `test_internal/pin/`: cocotb harness plus 27 L1 tests (L1-PIN-TX 13, L1-PIN-RX 12, L1-OVR 2), expected values from the §14 rules; `mutate.sh` (12 injected bugs, all caught).
- `synth/pin/`: `run_pin.sh` (lint, Yosys area, OpenSTA typ/slow), `ablate.sh` (price per feature), measurement wrapper with a stand-in producer.
- `docs/reports/PIN_UNIT_RTL.md`: numbers, the budget, gaps P-G1–P-G23. AREA.md synthesis row; BUGS #40 (generator define collision, caught by the new test before any RTL used it).

Results:
- Lean unit 29.4K µm² (216 flops), config 5.1K lean / 11.4K full, producer 1.5K. With the estimated port: **38.7K vs the estimate's 41.2K (−6 %)**. The chip at scenario E is ~85 % of the core, so the cuts are still needed.
- The wide timers dominate: the burst timer alone is 8.5K, the SHIFT_RX timer 3.9K.
- Slack at 20 ns +10.8 typ / +5.8 slow with config static. Critical path: burst timer → cursor subtract → `eq`.
- Tests: `make FULL=0` and `FULL=1` both 27/27; `scripts/check_all.sh` PASS; 34 generator tests pass; `gen --check` clean; lint clean.

Checklist boxes ticked (evidence):
- None. "All modules exist and lint clean" needs the whole table; "L1 all green" needs the other blocks and BITSYNC.

Problems / decisions:
- P-G15 (restart on a config write) and P-G16 (`live`) change §14 H1; P-G19 adds a clear mechanism to §9. They need a DECISIONS entry (not written: the user decides; D-041 is still free).

Next:
- Team: choose the next area cuts with `PIN_UNIT_RTL.md` §5 (fraction width, 4 units, 2 lanes).
- Model session: answer P-G1–P-G23 in §14.
- RTL: milestone B (PULSE, carrier, BITSYNC) after the cut decision, since a timer-width change touches BITSYNC too.

## 2026-09-25: Krithik, Kanishk + Claude (phase 2: tier 1 area decisions)
Done:
- **D-038:** pin configuration in a latch array (`trw_pin_cfg.v`); §14 H1: the host writes every unit's block before RUN; CLAUDE.md latch rule updated.
- **D-039:** slots, K and pin configuration are write-only from the host.
- **D-040:** U0–U1 full, U2–U5 lean (no PULSE, carrier, BITSYNC):
  - `pin_config.features` / `units` in the spec, validated by the generator; the §7.2 table shows each field's units;
  - the model and tripc reject a missing feature;
  - lean units don't store the optional fields;
  - `tripc.load` writes all six blocks.
- Area with tier 1: ~781K µm² placed, 87 % of the core (AREA_ESTIMATE scenario E).
- Tests: full suite 251 passed (slow included); `scripts/check_all.sh` PASS; `gen --check` clean. Spec bumped to v1.1 (still frozen).

Checklist boxes ticked (evidence):
- None. The task 2.0 box stays open until the design fits a routable budget.

Next:
- RTL session: `trw_pin_unit` (full and lean) first, synthesized, to replace the estimate's glue guess.
- Then choose the next cuts (a leaner core, 4 units, or 2 lanes) with real numbers.
- Ask Jane Street / Tiny Tapeout about 8x4.

## 2026-09-25: Krithik + Claude (phase 2 start: plan update, area estimate)
Done:
- `docs/HOW_IT_WORKS.md`: plain-language introduction (kitchen analogy); linked from OVERVIEW and CLAUDE.md.
- `PHASE2_RTL_CORE.md` updated with phase 1's findings:
  - helpers out (D-029);
  - pin-unit scope per §7 and the P-rules;
  - R2/R3 physical inputs (latch SDC exception, density ~42 % for the slot arrays, SRAM macro);
  - new task 2.0: area estimate first.
- **Area estimate (task 2.0), `docs/reports/AREA_ESTIMATE.md`:**
  - building blocks synthesized alone (`spikes/area/`), multiplied by counts from the spec;
  - **the frozen spec does not fit: ~109-120 % of the 6x4 core placed.** Pin units are ~84K µm² each, about half of the chip;
  - options priced (latch config, heterogeneous units, a leaner core, 4 units, 2 lanes, no read-back); only nearly all of them together reach a routable ~56-61 %.
- The project `.venv` was missing; recreated with `scripts/setup_venv.sh`.

Checklist boxes ticked (evidence):
- Phase 2 entry criteria (phase 1 complete, CI green on `367aacc`).

Next:
- Team decision on the area options (AREA_ESTIMATE §8): latch config, no slot/config read-back, heterogeneous units now; the rest after measuring.
- RTL session: write `trw_pin_unit` first and synthesize it, to replace the glue guess.
- Ask Jane Street / Tiny Tapeout whether 8x4 will be offered.

## 2026-09-25: Krithik + Claude (phase 1 closed)
Done:
- Pushed the D-035/D-036/D-037 commits (`ffb7d7d`..`367aacc`). The two tripc files missed in the tools commit went in separately as `367aacc`.
- Collected CI on `367aacc`: every workflow passed.

Checklist boxes ticked (evidence):
- "All CI workflows still green on `main`": `test` 36079759567, `unit` 36079759530, `lint` 36079759569, `docs` 36079759587, `gds` 36079759590 (all four jobs), `nightly` 36079785059 (manual) and 36136704498 (scheduled).
- That was the last box: **Phase 1 is complete.** Summary: `docs/summaries/PHASE1.md`.

Next:
- Phase 2, first task: area estimate for pin units, fabric and host, pricing heterogeneous pin units first (D-036).
- Kanishk: read D-036 and the §7.2 table.

## 2026-09-24: Krithik + Claude (phase 1: pin-unit registers, spec freeze)
Done:
- **D-036: pin-unit configuration register layout** in `spec/tripwire.yaml` (`pin_config`):
  - 22 words per unit at `0x3000 + u·0x20`, owners at `0x30C0`;
  - all times are 16.8 clocks, and the sample point is an offset in 1/256 clocks;
  - the generator validates it and emits the ARCHITECTURE §7.2 table;
  - the model runs every configuration through `tripsim/pinregs.py`, and tripc emits `pin_regs` and rejects values that do not fit;
  - `test_pinregs.py`, plus 5 generator validation cases.
- **Area input:** 307 config bits per unit (~1,840 for six units), comparable to all the slot latches. Noted in D-036 for the phase 2 area estimate.
- **D-037: spec frozen, v1.0.**
- Tests: 220 fast tests pass (`-m "not slow"`); `gen --check` clean; full suite result below.

Checklist boxes ticked (evidence):
- None new. "All CI green on `main`" waits for these commits' CI runs.

Next:
- User: commit and push. Then send the run IDs of `test`, `unit`, `lint`, `docs` on the new HEAD, plus one manual `nightly`. `gds` does not run: `src/` is unchanged since run 35942676979.
- Claude: tick the CI box with the run IDs and close Phase 1.
- Kanishk: read D-036 and the §7.2 table.

## 2026-09-24: Kanishk, Krithik + Claude (phase 1: §14 second-person review, D-035)
Done:
- **Kanishk reviewed §14** (with Claude reading `tools/`). He found gaps G9–G24 and model bugs #35–#37, and proposed D-035 items A–P.
- **Krithik accepted D-035.** The two choices went to Claude: E2 = host-writable r0–r3 and STATE while halted; F = one RX load per clock, the loser sets OVERRUN.
- **Applied (model side):**
  - ARCHITECTURE §4.5, §5.1, §6.2, §9 (K at slot index 12; lane register block), §11, §12, §14 (new L12, H2, and text for B, C, E, F–M); ISA §4.4, §5.3; YAML JAM/FRAME text.
  - Model: BUGS #35–#37 fixed; `Chip.step_lane` (H2), and a halted lane makes no SRAM accesses; `Lane.write_reg/write_state/write_k`, which `tripc.load` uses.
- **Second pass over P20–P29, line by line:** G25–G31, answered in the §14 text; BUGS #38 (BITSYNC SETN rx n > 16) and #39 (own-frame bit missing on flag/SE0 frame ends), both fixed.
- **Tests:** new `tools/tripsim/tests/test_semantics.py` (18 tests). A 12-mutation check (each fix reverted in turn) fails a test every time. Full suite: 220 passed, slow tests included; `gen --check` clean.

Checklist boxes ticked (evidence):
- [x] Zero OPEN items + §14 reviewed by two people: D-033, D-035 (accepted), `test_semantics.py`.

Problems / decisions:
- D-035. BUGS #35–#39.
- Kanishk's review found that `spec/tripwire.yaml` has no pin-unit configuration register layout (PERIOD 16.8, SAMPLEOFS, SJW, CRC fields and so on). That is an encoding the RTL, host tools and area estimate all need, so it is done before the spec freeze (next).

Next:
- Pin-unit configuration register layout in `spec/tripwire.yaml` (+ generator, host map), reviewed by both.
- Then the Phase 1 wrap-up: spec `status: frozen`, the CI box with run IDs, the final PHASE1 summary.

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
- **R2 PASSED (run 4, `gds` 36060938609, c4ef059):** gds 73 min, precheck 16.7 min, gl_test 0.8 min, viewer green.
  - Routing reached 0 violations at iteration 5; DRC, LVS and antenna 0; post-CTS resizer 9.5 s.
  - `AREA.md` row 3; latch slots kept.
  - [x] R2 box ticked (run 36060938609).
- **D-030 post-layout recheck:** OpenSTA on the routed netlist + SPEF (hold slacks match the flow's) gives EVAL +11.75 / +6.94 / +13.65 ns (typ/slow/fast), above the 2 ns threshold. Confirmed.
- Phase 2 inputs recorded (D-034, AREA row 3): the latch SDC exception; ~42 % local density for the slot arrays (Metal3 still 66 % used); the read-back mux as the first wiring cut.

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
