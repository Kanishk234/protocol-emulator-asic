# Worklog

Newest entry at the top. One entry per session: what was done, boxes ticked (with evidence), next step.

---

## 2026-09-27 (session 8: G0 chip green in CI; G1 primitives usable; UART, SPI, I2C controller fit G1)
**Done:**
- **G0 chip in CI, all green** (e5b1f98): `gds` + precheck + `gl_test` 17/17 in 36353540402 (45.8 min; setup +10.63 ns, hold +0.121 ns, DRC/LVS/antenna 0, IR drop 0.77 mV); lint, unit, test, docs, formal, fabric green. D-025 evidence and the hardening table updated.
- **G1 hard primitives** (D-026): `wp_timer`, `wp_shift` (`arch/prims/`), proven equal to a spec model (F4, `formal/f4_prims.sby`, k-induction), white-box tested against `tools/refmodels/prims.py`; primitive tile `PRIM2T2S` hardened at 0.97 × a LUT tile; G1 fabric stitched (`macro/warp_g1`, same size and ports as G0, KLayout DRC 0, antenna 0).
- **Compile flow support:** `WP_TIMER`/`WP_SHIFT` wrappers and BEL cell library (`tools/compile/prims/`), mapped, placed and configured (`examples/prims2`: RELOAD and LEN bits in the FASM, accepted by bitgen). `compile.protocols` takes `--arch`, `--only`, `--set`.
- **BUGS #15:** placement failed with free LCs because each LUT tile has one clock enable and one set/reset; the flow now turns enables/resets used by < 4 flip-flops into logic (`dfflegalize -mince/-minsrst`). Every design got smaller.
- **Protocols on the primitives** (`PRIMS=1`; plain form kept): UART, SPI controller, I2C controller rewritten; all RTL tests pass in both forms (UART DIV 16/13/5 + sigrok, SPI 4 modes × 2 speeds, I2C Q 2/4/5). I2C controller also lost its own synchronizers (ARCHITECTURE §6) and three wait states. Unit CI runs the `PRIMS=1` configurations.
- **Results:** G1 places UART 29, SPI 47, I2C controller 70 of 88 LCs (69–124 MHz slow corner); G0 places only SPI (86/96). `docs/reports/g1_results.md`, `g0_results.md` rewritten.
**Boxes ticked:** full 6x4 hardening of shell + G0 (CI 36353540402); protocols compiled onto G0 (`g0_results.md`).
**Later the same session:**
- CI on b438814: `fabric` failed: the committed test bitstreams predate the BUGS #15 flow change, and `prims2` needs G1 (fixed by the G1 switch, which rebuilds them). The `gds` run it started re-hardens the unchanged G0 (arch/prims touched `arch/**`).
- **G1 into the chip (D-027):** `arch/CURRENT` = warp_g1, ARCH_VERSION 0x0003 (shell, host software), `src/warp_g1.v` black box, `config.json` macro files, test stub and settle files regenerated, RTL fabric model includes `arch/prims`. New chip tests `test_prims` (both block types configured by a real bitstream) and `test_uart` (the design-set UART on the primitives through the host interface; test bitstream `uart16`). Local: RTL suite **19/19**, stub 13 + 6 skipped, F1 PASS (k-induction), pytest 63, lint clean.
- **I2C target** rewritten (hard shift register for the bus byte, shared register ports, no own synchronizers): 6/6 tests in both forms at Q 4/6/11; 205 → 184 LCs (G0), 169 (G1); does not fit either, even with 2 registers (123 on G1) — generic Yosys LUT4 mapping agrees, so it is the design's size: phase 3 (register-file tile or larger fabric).
- BUGS #16 (`sda_o` undriven after the rewrite, found by lint): `lint` now checks all protocol designs in both forms.
- G1 pre-flight: overflow 20, stripes OK, 21 detailed-routing violations all on `clk` at the strip above the fabric (G1 LEF identical to G0's; D-027 records it and the fallback). Pushed as d6f5dcd; CI hardening queued behind the G0 re-run.
- **Protocol chip tests:** `test_spi_ctrl` and `test_i2c_ctrl` (reference target models on the pins, open-drain bus for I2C) through the host interface, bitstreams `spi8`, `i2c8`; pass on the fabric RTL. `compile.protocols --require`; the `fabric` workflow compiles every protocol and fails if UART, SPI or I2C controller stops fitting.
- CI on d6f5dcd (G1 in the chip): lint, unit, test, docs, formal, fabric green; gds (G1 hardening) running.
- **BUGS #17 / D-028:** nextpnr left every path through the hard primitives untimed, so the G1 Fmax figures were optimistic. Primitive arcs from OpenSTA (`tools/timing/`, slow corner, ×1.5 margin) into `placement_estimate.txt`; the compile flow now uses nextpnr 0.11.1 (OSS CAD Suite 2026-09-27, `scripts/fetch_nextpnr.sh`), which reads them (identical FASM to 0.10-82 without them). Timed: UART 93–95 MHz, SPI 83.2, I2C controller 58.0, all above 50 MHz. Test bitstreams rebuilt; RTL suite **21/21**; pytest 69.
- **G1 chip green in CI** (36367067731 on d6f5dcd): gds 43.6 min, precheck pass, gl_test **19/19** (incl. `test_prims`, `test_uart`), routing DRC/LVS/antenna 0, setup +10.73 ns, hold +0.143 ns. D-026 and D-027 Accepted; D-029 (G1 is a valid fallback); `docs/reports/formal.md`; `docs/summaries/PHASE2.md` (in progress).
**Boxes ticked:** exit items: shell + G1 hardened, gl_test with real bitstreams, g0_results for every protocol, formal summary, fabric workflow green, decision point.
- **Timing cross-check** (`tools/timing/tile_check.sh`): STA of the hardened `PRIM2T2S` tile against the model. Clock-to-out bounded (6.79 vs 15.17 ns); the timer's in-tile setup (4.0 ns, a NOR with 33 loads) exceeded the standalone arc ×1.5, so setup/combinational margins are now ×3.0 (input side 8.06 vs 12.06 ns). Timed estimates: UART 90.7, SPI 78.0, I2C controller 53.0 MHz. Timing-model box ticked (documented conservative model).
- CI on fe4cac8: `fabric` failed with exit 126: `scripts/fetch_nextpnr.sh` committed without the executable bit (created from Windows); the workflow now runs it with `bash`, and the three new scripts get `git update-index --chmod=+x`. gds (21-test gl_test) running.
- CI gds on fe4cac8 (36372341186): gl_test **21/21** incl. `test_spi_ctrl`, `test_i2c_ctrl` on the hardened chip; pin-level protocol tests box ticked.
**Next (superseded):** push the margin fix + fabric fix + rebuilt bitstreams; all CI green closes phase 2 (then PHASE2.md final).
- **Phase 2 complete (2026-09-28):** all CI green at 2befd16 (gds/precheck/gl_test 21/21 36376994834); exit boxes ticked; `docs/summaries/PHASE2.md` final.
- TT linter warnings reviewed: `PINMISSING` VPWR/VGND on the macro (TT's black box has power pins; power via PDN_MACRO_CONNECTIONS, LVS 0: harmless), `WIDTHTRUNC` on Frame_Data_Reg's Row (32-bit genvar expression into a 5-bit parameter; values fit), `SYNCASYNCNET` on rst_n: BUGS #18.
- BUGS #18 fixed locally: reset synchronizer (+ separate config-path reset flop); full-top lint without waivers clean of SYNCASYNCNET/WIDTHTRUNC; suites 21/21 (RTL) and 13+8 skipped (stub); F1 PASS.
- Pre-flight of the fix: overflow 37, stripes 22/22, 36 detailed-routing violations, all on `clk` where it reaches the fabric's clock pin on the macro's west face (y ≈ 640 µm) and the local router cuts onto the macro's Metal4 blockage. Same net and area as the 21 of the G1 switch, which CI (LibreLane 3.1) routed with 0 violations three times on this floorplan: a local-vs-CI router difference for this net; CI decides. Fallback if CI fails there: room for the clock pin (macro one row lower or a keep-out west of the pin) as its own hardening.
**Phase 3 started (2026-09-28):**
- `tools/profiling/limits.py` + `docs/reports/g1_limits.md`: on G1 the counters/shifting are absorbed; control logic is what is left; control sets (3–7) and primitive count are not limits; every critical path goes through a primitive; the I2C target would not fit even with a register file.
- D-030 candidate 1 (registered terminal count): F4 re-proved, `tc` 2.98 → 0.88 ns at no area cost, but the I2C controller (the worst design) is limited by paths into the timer: 53.0 → 52.1 MHz: not kept alone (parked in build/c1/parked).
- Root of the timer's slow input path: the primitive tile's hardening config (copied from the tile library) disables resizer/repair, so a NOR drives 33 loads unbuffered.
- D-031 candidate 2 (primitive tile with design repair): three local tile runs; repair works only once inserted as a step (the tile driver applied removals only), then detailed placement fails: the 92 %-full tile has no room for buffers. Not feasible; config restored; `tile_check.sh` now picks the newest completed tile run.
- CI on 3047dea (BUGS #18 fix): all green; gds/precheck/gl_test 21/21 (36383587262), setup WS +12.48 ns.
- Organizers' reply (D-032): eFPGA accepted; software side required (flow, loading, UART/SPI/I2C examples); phase 4/5 plans updated.
- `docs/reports/architecture_comparison.md` + chart; D-033 final architecture G1.
- User kept hardware open for the I2C target: D-034 register-file tile measured (169 → 123 LCs, still no fit); user then chose to freeze and drop the I2C target (D-035).
- Phase 3 exit boxes ticked except the tag; `docs/summaries/PHASE3.md` drafted.
**Next:** user tags `hw-freeze` on 3047dea; then phase 4 (unseal the held-out set; demo-board loader; end-to-end examples).
**Next (superseded):** after the G1 hardening result, push the protocol chip tests + timing work (touches `test/` and `macro/`, so one more hardening, which also gives gl_test evidence for the 21 tests); then phase 2 exit: timing cross-check, per-tile equivalence plan, PHASE2 summary.

---

## 2026-09-27 (session 7: phase 2 started: shell, compile flow, real bitstreams)
**Done:**
- **Shell** (ARCHITECTURE §2–6): `wp_spi_target`, `wp_shell` (commands, checked loader, run control, 2-entry host channel FIFOs), `wp_crc32` (bit-serial), `wp_fifo`, `wp_sync`; new top-level pinout; FABulous's bit-bang receiver removed. Spec clarifications D-021.
- **Host software** `tools/host/protocol.py` (from the spec): transactions, STATUS decode, CRC, architecture check before loading.
- **Formal:** F1 output isolation proven unbounded (k-induction); F2 bounded (BMC 84) against an independent shadow loader. The F2 cover trace exposed **BUGS #12** (an empty load reached LOADED), now fixed. New `formal` workflow.
- **Compile flow** `tools/compile/` (D-022): pin map → wrapper → Yosys → nextpnr (slow-corner timing) → WARP bitgen → `.wbit` + report. `arch/warp_tiny/` (fabric.csv, pins.csv, arch.yaml). **BUGS #13**: FABulous's bitgen drops the global-clock mux selects; our generator fixes it and matches upstream word for word elsewhere.
- **Real bitstreams on the whole chip:** `test/test_bitstream.py` loads `counter4` and `logic4` over SPI and checks them at the pins, on the fabric RTL (`WARP_FABRIC=rtl`, new job in `fabric`) and on the hardened macro's gate-level netlists (`GATES=yes`, what CI `gl_test` runs). Gate level needed D-023 (settle X routing loops; no reload over a running configuration).
**Boxes ticked:** host interface, loader, run control, IO cells, host software, compile flow, host rejects other architectures, F1, F2, `gl_test` with two real bitstreams. **CI on acc3af3/2faaa36 all green:** `gds` + precheck + `gl_test` 16/16 36342012141 (35.6 min; shell 3,239 cells / 51,066 µm², setup +12.04 ns, hold +0.117 ns, DRC/LVS/antenna 0), `formal` 36342012194, `fabric` 36342012182, `test` 36342480467, `lint` 36342480574, `unit` 36342480768 (after moving it to Python 3.12), `docs` 36342480572.
**Also (uncommitted at session end, local):** design-set synthesis on the real flow (`python -m compile.fit`, `capacity.md`: UART 129, SPI 96, I2C ctrl 154, I2C target 208 LCs vs G0's 96); `N_IO` tile hardened (0 DRC); G0 fabric stitched (`arch/warp_g0`, 1016.64 × 669.06 µm, D-024 proposed); `spikes/fabric_tiny/run.sh` takes `FABRIC=<name>`.
**Not yet:** host data path into the fabric (FIFOs exist, the current fabric has no channel BELs), G0/G1 fabric, 6x4 hardening, timing model documentation, protocols on G0, `gl_test` evidence from CI.
**Later the same session:** the compile flow's wrapper instantiates IO cells explicitly (needed for the host channel; D-022); the new bitstreams exposed zero-delay hangs in the gate-level fabric model, so `gl_test` now simulates the gate-level shell with the fabric RTL, plus hold-X during loads and settle after (D-023 revised); per-tile netlist-vs-RTL equivalence added to the plan. Local: gl_local 16/16, RTL 16/16, pytest 42, bitstreams reproducible.
**G0 into the chip (later the same session, local, uncommitted at the time of writing):** `arch/CURRENT` = warp_g0 (ARCH_VERSION 0x0002); new top level with all 19 pins and the host channel through the fabric (D-024); black box generated from the macro (`scripts/gen_macro_stub.py`); compile flow maps `h_*` by name; examples `idle` and `hostecho`; RTL suite 17/17 incl. `test_host_channel`; F1 re-proved. Placement took six local pre-flight rounds (new `scripts/preflight.sh`): global-routing overflow 9,290 → 23 via east-channel obstruction, per-column frame decode (`wp_frame_select`), placement density 75 %, routing derate 0.15 (D-025); detailed routing 0 violations, power stripes full height. BUGS #14 (compile flow merged carry chains).
**Next:** push G0 and get the CI hardening + precheck + gl_test green; then G1 primitives and the protocols on G0/G1.
**Earlier next:** G0 into the chip: top-level pin and host-channel wiring (D-024), macro placement in `src/config.json` (D-019 rules), local routing pre-flight, then one CI hardening.

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
