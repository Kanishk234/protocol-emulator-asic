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

Checklist boxes ticked (evidence):
- none yet. The tripsim box still needs STRETCH and PULSE; the program boxes need `tripc` and the UART/SPI/I2C-controller programs.

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