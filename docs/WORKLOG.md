# Worklog

Newest entry at the top. One entry per session: what was done, boxes ticked (with evidence), next step.

---

## 2026-09-27 (session 6: fabric through TT's flow; phase 1 complete)
**Done:**
- Three CI iterations on the chip-level integration, each failure logged: routing stuck because the fabric's pin faces pointed at the die edges (BUGS #9, run cancelled after ~4.8 h); `"//"` keys inside MACROS (BUGS #10); precheck pin check failed on pdngen's short channel stripes beside the fabric (BUGS #11). Adopted the R3 SRAM spike's macro settings (D-019 rev 2: routing-iteration cap, Magic/LVS handling, port-only black box). Added a local pre-flight: TT's merged config through LibreLane (Nix) up to detailed routing + a full-height power-stripe check (~3 min).
- **CI run 36327510268 (dea2150): `gds` 32.5 min, precheck 9/9, `gl_test` pass**; DRC/LVS/antenna 0, timing met at 50 MHz, IR drop 0.38 mV. Recorded in PHYSICAL_DESIGN_AND_CI, `fabric_tiny.md`, CLAIMS (C1–C3), risk register.
- D-020: template `fpga` workflow not applicable with a hard macro.
**Boxes ticked:** tiny fabric hardened with precheck (task + exit), all CI green on `efpga`, `docs/summaries/PHASE1.md` (final). **Phase 1 complete.**
**Next step:** phase 2 (`docs/design/phases/PHASE2_BASELINE_FABRIC.md`), starting with the shell (SPI host interface + checked loader + run control, ARCHITECTURE §2–4) and the formal properties F1/F2 for it.

## 2026-09-26 (session 5: tiny fabric)
**Done:**
- Magic hang root cause found (BUGS #2): the CMOS5L Magic tech file needs Magic >= 8.3.657; the LibreLane 3.0.0 Nix environment has 8.3.623. Workaround everywhere: skip Magic; KLayout writes the GDS and runs the DRC, OpenROAD writes the LEF (`write_abstract_lef`), unused VIA definitions stripped (the FABulous fabric flow misreads them as the tile size).
- All 9 tile types hardened on CMOS5L (0 routing DRC, 0 antenna each); **16-LUT fabric `warp_tiny` stitched: 357 × 484 µm, KLayout DRC 0**, bitstream spec generated (`docs/reports/fabric_tiny.md`).
- Line endings: my Windows-side Python edits had written CRLF into 14 committed files; all converted back to LF (content unchanged, checked with `git diff --ignore-cr-at-eol`). Edits now go through WSL or the Edit tool.
- The first background tile run was stopped by Claude Code for low memory on the Windows side (not a job failure).
**Boxes ticked:** none yet (the tiny-fabric box needs the chip-level integration + precheck).
**Later the same session:**
- D-017: tile power stripes on a global 109.92 µm grid (2.1 µm wide, per-tile-type offsets) so TT's chip stripes can land on the fabric's power columns (lesson from `main`'s R3 SRAM spike). First attempt put the east tiles' ground stripe outside the tile (arithmetic slip); fixed with grid phase 12.00. All 9 tiles and the fabric re-hardened: power pins are full-height columns exactly on the grid; KLayout DRC 0.
- Placement boundary (IHP 189/4) added to the fabric GDS; macro exported to `macro/warp_tiny/` (GDS, LEF, fabric + 9 tile netlists, fabric RTL, bitstream spec).
- Chip-level RTL (D-018): `tt_um_warp` = `warp_tiny` + `wp_fabric_cfg` (FABulous bitbang + ConfigFSM copied unmodified into `src/fabric_gen/`) + run control/parking. `src/lint.vlt` waives lint only for upstream files and the black box. New pin-level tests (parking, config session). `config.json` (D-019): MACROS, PDN_MACRO_CONNECTIONS, `pdn_cfg.tcl` from `main`'s R3 spike, stripe pitch 109.92 / offset 20.64.
- Local: `check_all` PASS, `gl_local` PASS (4/4 on a Yosys netlist), TT `--check-docs` and `--create-user-config` OK.
**Next step:** push; the CI `gds` run (hardening + precheck + gl_test) is the test of the phase 1 tiny-fabric box.
**While CI ran (run 36277723397):** wrote ARCHITECTURE v1 (pins, SPI host commands + status, loading with version/length/CRC, run states + parking, clock/reset, IO cells, G0/G1 resources, primitive sketches, variants, user Verilog rules; OPEN items marked), VERIFICATION v1 (V0–V7, F1–F4 with bounds, coverage goals), PHYSICAL_DESIGN_AND_CI v1 (three-level flow, known limits), risk register in OVERVIEW, in-progress `docs/summaries/PHASE1.md`. `gh` is installed and logged in (user); run logs/artifacts are fetched with it after runs complete. Boxes ticked: the three specs, the risk register, exit item "specs v1 written".

## 2026-09-25 (session 4: phase 1 starts)
**Done:**
- Phase 0 closed (D-012: organizer email waived by the user). CI green on 7405a2e.
- Held-out set sealed at **0171cf7**: WS2812, 1-Wire, SWD, CAN (D-013, `docs/design/HELDOUT.md`).
- Provisional user-design interface (D-014): pins + host byte channels + status; settings as bitstream parameters by default.
- UART: independent model `tools/refmodels/uart.py` (6 pytest incl. hypothesis) written first; then RTL `protocols/uart/` (tx, rx, top); 8 cocotb tests vs the model and sigrok, DIV 16/13/runtime, all pass; Verilator/Icarus lint clean. First profile: 171 LUTs fixed divisor, 262 runtime (budget ~96). BUGS #3 (harness). `unit` workflow added (D-015); `check_all` runs protocol tests.
**Boxes ticked:** phase 1: held-out chosen + sealed (0171cf7), `protocols/uart/`.
**Later:** `protocols/README.md` states that protocol designs are soft user logic, never silicon (user asked; D-002). SPI controller: model `tools/refmodels/spi.py` (7 pytest) then RTL `protocols/spi_ctrl/`; 24/24 cocotb runs (MODE 0–3, HALF 4/5/7) vs model + sigrok; lint clean; 85 LUTs / 42 FFs. BUGS #4 (model skipped a response; spec `HALF >= 4`, not 3). D-014 revised (`h_wlast`). `check_all` PASS.
**Boxes ticked:** `protocols/spi_ctrl/`.
I2C controller: model `tools/refmodels/i2c.py` (bus, target, decoder; 5 pytest incl. stretching) then RTL `protocols/i2c_ctrl/` (command byte stream); 18/18 cocotb runs (Q 4/2/7) vs model + sigrok; lint clean; 164 LUTs / 65 FFs at ~100 kHz. BUGS #5 (hold time, found in review).
**Boxes ticked:** `protocols/i2c_ctrl/`.
I2C target: reference controller model added to `tools/refmodels/i2c.py` (generator; 2 more pytest incl. stretching), then RTL `protocols/i2c_target/` (4-register map, host command access, dirty bits); 18/18 cocotb runs (Q 4/6/11) incl. sigrok; lint clean; 240 LUTs / 79 FFs. BUGS #6 (harness).
**Boxes ticked:** `protocols/i2c_target/`, reference models + RTL tests, sigrok check. All design-set protocol RTL is done.
Profiling: `tools/profiling/workload.py` (renamed from `profile`, BUGS #7) sweeps LUT3/4/6 ± carry and attributes every LUT to the function of the registers it feeds. UART counters resized to the divisor first (fairness; 171 → 144 LUTs). Result (`docs/reports/profiling.md`): of 648 LUT4s, counters 23 %, storage 21 % (mostly the I2C target's register map), shift 17 %, control 17 %, shared 15 %. Ranked: timer/counter, shift register, host channel in the shell, I/O cell sync/registered/open-drain, register file (1 user). Upper bound: UART/SPI/I2C controller fit ~96 LUTs after ranks 1–4; the I2C target does not without a register file.
**Boxes ticked:** profiling script, profiling report, exit item "profiling.md complete".
Area model `tools/areamodel/` (5 pytest) + primitive sketches (`spikes/primitive_area/`: timer ~2,751 µm², shift ~1,538 µm² incl. config bits). Capacity (`docs/reports/capacity.md`): 4 × 3 tiles fit next to a ~273 µm shell column: 96 LUT4, 88 with one primitive tile (2 timers + 2 shifts). UART/SPI/I2C controller fit; I2C target (~220) does not. **D-016: GO specialized eFPGA**; I2C target/showcase open (register file, smaller map, or showcase on the controller).
**Boxes ticked:** area model, capacity estimate, needs vs capacity, go/no-go decision, 2 exit items.
**Next step:** harden a tiny FABulous fabric (stitched tiles) through the flow with live config; then ARCHITECTURE/VERIFICATION/PHYSICAL v1 and the risk register.

## 2026-09-25 (session 3, continued)
**Done:** fetched the CI `GDS_logs` (user download): die 1289.28 × 710.64 µm, 0 DRC/LVS/antenna, timing met, **top level routes only to Metal4** (TopMetal1 is TT power); recorded in `PHYSICAL_DESIGN_AND_CI.md`. `fpga` run 36201219254 green. D-008 accepted (G1 fallback; goal still full specialization). D-011 (`unit` arrives with the first Python tool). `VERSIONS.md` complete. Phase 0 summary written (in progress).
Tile runs 2–3 (`docs/reports/tile_cmos5l.md`): with signals on Metal2–Metal4 the tile routes at the same size (6 iterations, 0 antenna); run 3 skips Magic (BUGS #2 workaround), KLayout GDS written, **KLayout DRC 0 violations (328 rules)**.
**Boxes ticked:** template workflows green (all four), resource usage, `lint`/`unit` workflows (D-011), `VERSIONS.md` complete, phase 0 summary.
**Open in phase 0:** organizer email (parked by the user); all CI green on `efpga` after the push.
**Next step:** push and confirm CI green. Then phase 1 (after the email closes phase 0, or on the user's call): seal the held-out set first.

## 2026-09-25 (session 3)
**Done:**
- Nix 2.35.2 installed by the user; FOSSi cache configured (`/etc/nix/nix.conf`). LibreLane 3.0.0 + FABulous plugin environment builds in 2.5 min (Nix store 6.9 GB). CMOS5L PDK at TT's revision in `~/.cache/warp/pdk-full`. CI LibreLane version recorded (3.1.0.dev3).
- `fabric` CI run 36196784852 green (FABulous demo in CI).
- **First FABulous tile on CMOS5L** (`spikes/tile_cmos5l`, patch D-010): `LUT4x8_ha` routes at the SG13G2 size/density: 40.7K µm² per 8 LUT4s (~5.1K µm² per LUT4), 97 % utilisation, 0 routing and antenna violations. `docs/reports/tile_cmos5l.md`. Capacity at 6x4: ~96 LUT4s with margin (the synthesis estimate was 60–90). D-008 updated; still stands (UART ~215 cells).
- Magic stream-out hung (BUGS #2); stopped by hand, so no GDS/DRC/STA yet.

**Boxes ticked:** none new (tile hardening is phase 1 evidence; `fab_demo` got its CI run ID).

**Next step:** KLayout stream-out + DRC + STA for the tile (BUGS #2). Close phase 0: organizer email (user), `fpga` workflow run (user clicks), `unit` workflow, phase 0 summary. D-008 decision (user).

## 2026-09-25 (session 2, part 3)
**Done:** `fabric` workflow (`.github/workflows/fabric.yaml`) runs `spikes/fab_demo/run.sh` in CI with the pinned tools (Ubuntu Python 3.12, OSS CAD Suite 2026-06-29, cached). PRISM prior-art notes (`docs/notes/prior_art.md`): Verilog → Yosys → bitstream on IHP already exists there, with a fixed datapath close to our hard-block candidates; our claims must rest on the parallel fabric model and the measured method.
**Boxes ticked:** PRISM notes.
**Next step:** push; record the first `fabric` run ID. Waiting on the user: Nix install (tile hardening), D-008, organizer email. The `main` gate is resolved: every "green on `main`" rule (CLAUDE.md, phase checklists) now says `efpga` (user decision, 2026-09-25).

## 2026-09-25 (session 2, continued)
**Done:**
- `gds` 36170807513 on a63877d fully green: hardening 35.1 min, precheck 12.3 min, `gl_test` pass. Recorded in `PHYSICAL_DESIGN_AND_CI.md`. Cell stats and the CI LibreLane version need the `GDS_logs` artifact (login required).
- Tiny FABulous study: `docs/notes/tiny_fabulous.md`. Tiles → fabric → top, three LibreLane runs, submitted via `custom_gds`. Phase 0 decision point answered: D-009 (yes; our plan: fabric macro integrated by the template `gds` job, as TRIPWIRE's R3 did with the SRAM).
- Early capacity estimate: `docs/reports/capacity_early.md`. ~4.5K µm² per LUT4 (stock LUT4AB tile, cmos5l synthesis), so a generic 6x4 fabric holds ~60–90 LUT4s; a scratch UART needs ~215. Proposed D-008 (the fallback becomes G0 + minimal hard primitives).

**Boxes ticked:** template design green on `test`/`gds`/precheck/`gl_test`; hardening time; Tiny FABulous read + written down; phase 0 decision point (D-009).

**Open in phase 0:** PRISM notes; `unit` workflow (waits for the first Python tool); the template `fpga` workflow has never run (manual); `VERSIONS.md` CI LibreLane version; "all CI green on `main`" (`main` is TRIPWIRE: the gate needs retargeting to `efpga` or a separate repo; the user decides); organizer email; phase 0 summary.

**Next step:** the user decides D-008. Then harden one LUT4AB tile on cmos5l with `FABulousTile` (needs OpenROAD/KLayout/Magic: Nix or the LibreLane container) to replace the synthesis estimate with a real one.

## 2026-09-25 (session 2)
**Done:**
- Fixed the `gds` docs check failure (empty title/author/description/pinout, missing `info.md` sections): filled `info.yaml` (WARP, 6x4, 50 MHz, `tt_um_warp`) and `docs/info.md`. Pinout is provisional (D-006).
- Renamed the placeholder top to `tt_um_warp` (`src/tt_um_warp.v`, `test/tb.v`, `test/Makefile`).
- Took the template `gl_test` UDP fix preemptively (BUGS #1).
- Added `scripts/setup_venv.sh`, `check_all.sh`, `gl_local.sh`, `requirements-dev.txt`, the `lint` workflow, and the `gds` paths filter + non-cancelling concurrency.
- Installed OSS CAD Suite 2026-09-25 to `~/oss-cad-suite`; FABulous-FPGA 2.2.0 into `.venv` (pinned). PATH order D-007; versions in `docs/VERSIONS.md`.
- Deleted the duplicate `docs/OVERVIEW.md` (the user did this).

**Boxes ticked (phase 0):** repo/info.yaml (local `--check-docs` pass; CI `docs` 36170807355 green on a63877d), sign-up form (done by Kanishk), docs skeleton, setup_venv, OSS CAD Suite + PATH (D-007), check_all (PASS), gl_local (PASS).

**Later in the session:**
- The user installed `python3-tk` and pushed (a63877d): `test` 36170807382, `lint` 36170807369, `docs` 36170807355 all green; `gds` 36170807513 still running at session end.
- FABulous demo: OSS CAD Suite 2026-09-25 breaks `synth_fabulous`; switched to 2026-06-29, the release FABulous 2.2 pins. `check_all` and `gl_local` re-passed on it.
- `spikes/fab_demo/run.sh`: stock fabric, two bitstreams (stock counter; our `lfsr_down`), each matches its source for 100 cycles, and B mismatches A's source. Report `docs/reports/fab_demo.md`. Ticked: reference fabric, reference design, second design, FABulous pin, and the exit item "two different bitstreams".
- Found: FABulous's wrapper generator only wires its own demo design (see the report); our compile flow needs its own.

**Next step:** check `gds` 36170807513 (precheck, `gl_test`, hardening time, LibreLane version). Then the Tiny FABulous study (how the fabric went through the TT flow), which answers the phase 0 decision point, and the LUT4AB area / config-bit measurement on cmos5l for the early capacity estimate. The organizer email is still open (the user will send it; low priority). `unit` workflow waits for the first Python tool with tests.

## 2026-09-25
**Done:** Project plan, CLAUDE.md and phase docs created (drafted in a Claude chat, not yet checked against a working repo).
**Boxes ticked:** none.
**Next step:** Phase 0, first task: create the repo from the CMOS5L template.
