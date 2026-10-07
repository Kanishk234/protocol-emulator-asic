# Bugs

## 45: Placement preflight misreads a void successful checker return
- **Date:**2026-10-07.
- **Symptom/check:**37688867787 fails before resizing with custom "Source placement is not legal", without native placement violations.
- **Root cause:** script compares check_placement's empty successful return to numeric0. Pinned OpenROAD dcf36133 Opendp.i defines check_placement_cmd as void; CheckPlacement.cpp raises DPL-0033 on actual violations. Current general documentation's numeric-return description did not match this pinned API.
- **Fix/coverage:** invoke native check directly with retained baseline/candidate placement reports; native errors still fail the job. Source and final checks both retained. Corrected cloud result pending; no placement acceptance inferred from fixing setup.
- **Primary sources:** [pinned command](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/dpl/src/Opendp.i), [pinned failure gate](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/dpl/src/CheckPlacement.cpp).
- **Verified corrected run:**37689324316 succeeds; actual source/final legality checks pass and strict topology/master/movement audit remains. Downloaded result and placement-only ODB hash verified; routes/timing remain unqualified.

## 44: Board loader truncates malformed fields and skips negative chunks
- **Date:**2026-10-07.
- **Symptom/check:** independent audit reproduces negative chunk emitting BEGIN/END without DATA, oversized architecture/word truncation and65536-word length wrapping to0 in tools/board/warp.py. Host BUG42 validation had not reached the board API.
- **Root cause:** MicroPython board transaction builder serialized values without unsigned-width/chunk/length validation; Warp.load queried the device before checking malformed inputs.
- **Fix/coverage:** validate chunk, architecture, every word and16-bit length in both transaction builder and before any device I/O. Meaningful boundary/no-I/O tests and valid maximum-length parity/CRC; project-venv board+host317 tests pass. Existing unit workflow37663965540 passes on675a03c and covers them. No physical/bitstream/SPI format change or real-board claim.

## 43: Isolated Magic count field is empty despite completed checks
- **Date:**2026-10-07.
- **Symptom/check:**37653631748 produces five reports with an empty count field. Full log records five zero-error checks and empty reason lists; workflow green only means reports completed.
- **Root cause:** Magic `drc count total` prints its result instead of returning a Tcl value suitable for interpolation.
- **Fix/coverage:** keep count output in the retained log, label each cell there and write `has_findings` from the returned `drc listall why` list. Check that every baseline and array fixture produces a report. Tcl completeness passes; hosted extended-array verification pending. This reporting correction does not resolve complete-chip DRC.
- **Verified:**37657638270 and37658318703 retain explicit box counts derived from the returned reason lists, including17 ground-boundary boxes. Baseline/no-finding cases report0. These counts measure reports, not chip acceptance.

Format for each entry: number, date, symptom, root cause, the check that caught it, the check that now covers it, fix commit.

## 42: Host loader accepts negative chunk size and truncating fields
- **Date:**2026-10-07.
- **Symptom/check:** load_transactions(words, chunk=-1) builds LOAD_BEGIN/LOAD_END but no LOAD_DATA; words outside32 bits and architecture IDs outside16 bits are truncated by byte packing.
- **Root cause:** transaction builder relied on range/byte helpers without validating the caller's chunk, word or architecture fields.
- **Fix/coverage:** reject non-positive/non-integer chunks, non-unsigned32-bit words and non-unsigned16-bit architecture IDs before building load transactions. Host tests include all three boundaries, valid randomized loads and CRC preservation. Local31 host tests pass; hosted verification pending. No shell/bitstream format change.

## 41: Plain-filler experiment leaves the separate decap selector active
- **Date:**2026-10-07.
- **Symptom/check:**37552604692 reproduces248 KLayout errors and75 LVS errors; intended decap removal did not occur. Result summary has null counts because failed deferred checkers do not write final state_out.
- **Root cause:** fill insertion combines DECAP_CELLS and FILL_CELLS. Only FILL_CELLS was changed; DECAP_CELLS remained sg13cmos5l_decap_*. Exact post-fill DEF has5667 decaps and1095 plain fillers,6762 total. This run does not test the no-decap hypothesis.
- **Fix/coverage:** change only DECAP_CELLS to an empty list in the copied config. Stage filler insertion separately and require zero actual decap instances plus nonzero plain fillers before expensive physical checks. Read KLayout/Netgen metrics from their completed states even when deferred checkers fail. Static inventory/parser checks pass against failed-run evidence; corrected cloud verification pending. Frozen chip/PDK unchanged.

## 38: Functional Liberty import rejects an unused clock-gate cell
- **Date:**2026-10-06.
- **Symptom/check:**37536118708 native UART fails; separate optional SAT stops before solving because sg13cmos5l_lgcp_1 has an internal output without a function.
- **Root cause:** full functional import attempts to model unused Liberty entries whose state-table semantics the importer does not support.
- **Fix/coverage:** ignore incomplete entries at import, then hierarchy-check every instantiated cell so a used missing model still fails.37545251399 verifies import succeeds; no native/model/hardware change or proof success implied.

## 39: Native configuration capture misses renamed latch outputs
- **Date:**2026-10-06.
- **Symptom/check:**37545251399 SAT setup cannot bind aliases removed by cleanup.37545630704 retains aliases and finds counterexamples, but some configuration selectors remain free.
- **Root cause:** capture selected only ConfigMem.*.Q names. Exact netlist audit finds529 configuration latches, with24 outputs without those aliases;530 logical configuration bits include one merged latch. The earlier8707 matching-bit audit is a named-storage subset. Missing constraints invalidate interpreting these counterexamples as a mapped-LUT fault.
- **Fix/coverage:** preserve proof aliases and capture Q directly on every actual sg13cmos5l_dlhq_1 instance. Static529/505/24 cell/alias audit passes. Hosted37546145073 proves all three local constant properties with feasible constraints. No signals are forced in simulation; only the isolated proof constrains observed configuration values. BUG33/native UART remains open.

## 40: Cloud evidence omits final physical database and marker coordinates
- **Date:**2026-10-06.
- **Symptom/check:**37516794406 reaches0 native markers, but artifact's latest drt_iter snapshot is iteration52 with3markers. KLayout counts survive while its lyrdb and final zero-route ODB are absent.
- **Root cause:** bounded collector retains intermediate drt_iter ODB and small log/rpt/json/xml files, excluding final physical views and lyrdb.
- **Coverage/workaround:** separate geometry replay37545941476 retains full ignored run directory including physical views and marker databases. Its source remains intermediate3-marker ODB; cannot reconstruct or claim the final0 database from it. Update long-route evidence retention before another route is needed; collector now retains the final completed state views separately, with exact metrics and hashes, plus all lyrdb files. Synthetic regression verifies final0 ODB retention even when the latest intermediate snapshot has3 markers. Hosted retention verification remains pending; it does not recover the missing historical final database.

## 37: Optional native LUT alias raises KeyError through indexed lookup
- **Date:**2026-10-06.
- **Symptom/check:** focused diagnostic37534707478 stops before RUN while looking for LUT_out, an alias removed by synthesis; it does not reach the later UART check.
- **Root cause:** cocotb indexed lookup raises KeyError for missing handles, whereas optional-alias handling catches AttributeError. The pre-push netlist audit had confirmed LUT_out was removed but did not exercise the handle access behavior.
- **Fix/coverage:** use attribute lookup, matching existing optional native probes and their AttributeError handling. Lightweight fake-handle check covers retained and removed names. Hosted37535155011 verifies the correction and reaches actual UART X; BUG33 remains unresolved.

## 36: Diagnostic NOR gate used NAND's inverted input name
- **Date:**2026-10-06.
- **Symptom/check:** native diagnostic37521273371 passes RTL control but stops before RUN with KeyError:A_N in sensitivity filtering.
- **Root cause:** nor2b ports are A/B_N; diagnostic incorrectly reused nand2b's A_N/B convention. Official pinned PDK models are unchanged and not at fault.
- **Fix/coverage:** use A or !B_N for NOR input sensitivity (output inversion does not change sensitivity). Lightweight schema audit invokes filtering for every distinct gate interface in actual mapped fabric; controlling-input checks pass. Hosted rerun pending. This diagnostic error does not resolve or reproduce the later UART failure by itself.
- **Hosted verification:**37521660597 successfully executes filtered traces through the actual later UART X; no KeyError. BUG33 remains open.

---

## 1: Template gate-level source list omits the flip-flop UDPs
- **Date:** 2026-09-25
- **Symptom:** `gl_test` fails at elaboration with `Unknown module type: ihp_dff_r` as soon as the design has flip-flops. (Seen on the TRIPWIRE branch, gds run 35821375890; carried over preemptively since WARP uses the same template.)
- **Root cause:** in the IHP-Open-PDK revision the CMOS5L action pins, the flip-flop UDPs live in `sg13cmos5l_stdcell/verilog/sg13cmos5l_udp.v`, which the upstream `cmos5l` template's `test/Makefile` does not list.
- **Caught by:** `gl_test` (CI).
- **Now covered by:** `gl_test` on every `gds` run, and `scripts/gl_local.sh` once added.
- **Fix:** add the UDP file to the gate-level `VERILOG_SOURCES` in `test/Makefile`. Fix commit: pending.

## 2: Magic stream-out hangs on a FABulous tile in CMOS5L
- **Date:** 2026-09-25
- **Symptom:** LibreLane step `Magic.StreamOut` on the `LUT4x8_ha` tile (`spikes/tile_cmos5l`) prints `DEF read, Line 67..70 (Error): No cut layer specified in VIARULE` (4 errors), then runs at 100 % CPU with an empty log for 9+ minutes; stopped by hand. No GDS produced.
- **Root cause (found 2026-09-26):** a **Magic version mismatch**. The PDK's CMOS5L tech file (2bbec75) says `Magic version 8.3.657 is required by this techfile, but this version of magic is 8.3.623` (the LibreLane 3.0.0 / FABulous-plugin Nix environment), and then fails to parse its `cifinput` section. With a partly loaded tech file Magic cannot read the generated via arrays (`No cut layer specified in VIARULE`) and hangs. Removing the TopMetal1 power grid (4 → 3 errors) did not help, as expected given this cause.
- **Caught by:** the tile hardening spike (manual).
- **Now covered by:** nothing yet. Next: KLayout stream-out for tiles and the fabric (as Tiny FABulous does), and a check that the flow finishes in bounded time.
- **Update (run 2):** hung again in the same way; skipping the step through the tile's `meta.substituting_steps` had no effect, because `tiles.py` builds the flow from a dict and does not apply them.
- **Fix (workaround):** our patch to the tile driver applies step removals; tiles skip Magic and use KLayout stream-out (run 3: GDS written, KLayout DRC 0). Root cause in Magic still open; Magic LEF writing is also skipped, so the fabric needs another LEF source. Fix commit: pending (spike).

## 3: UART test harness: first byte invisible to sigrok, writes during ReadOnly
- **Date:** 2026-09-25
- **Symptom:** `protocols/uart/test`: sigrok decoded `[FF 55 A5 3C 81]` instead of `[00 FF 55 A5 3C 81]` (our model decoded all six); two tests failed with "Attempting settings a value during the ReadOnly phase".
- **Root cause:** test code, not RTL. (a) The recorded TX line started at the edge where the first start bit began, so the VCD had no idle-high → low edge before it and sigrok skipped the frame. (b) The record/collect helpers returned in the ReadOnly phase and the caller then drove a signal.
- **Caught by:** the sigrok leg of `test_tx_back_to_back` (an independent decoder) and cocotb's phase check.
- **Now covered by:** the same tests: the VCD gets 2 bit times of idle first; helpers end with `NextTimeStep()`.
- **Fix:** in the same commit as the tests.

## 4: SPI target model skipped a response byte; SPI controller spec allowed a too-fast SCK
- **Date:** 2026-09-25
- **Symptom:** (a) `tools/refmodels/spi.py` with the CS-fall and first SCK edge in the same clock missed that edge (CPHA 1); (b) across CS transactions the model skipped a response byte (e.g. host got `C3` instead of `5A`); (c) the SPI controller at `HALF=3` read wrong MISO bytes in every mode.
- **Root cause:** (a, b) model: it handled only one event per clock, and it loaded the next response both when a byte completed and when the next transaction started (CPHA 0 puts the next byte's MSB on the line before knowing whether the transaction continues). (c) spec: MISO passes a two-flop synchronizer (2 clocks) and a target may take 1 clock after its change edge, so the sampling edge must be ≥ 4 clocks after the change edge. The RTL comment said `HALF >= 3`.
- **Caught by:** (a) the model's own hypothesis round-trip test; (b, c) `protocols/spi_ctrl/test` (multi-transaction tests, `HALF=3` run).
- **Now covered by:** `test_target_roundtrip`, `test_responses_continue_across_transactions` (model); the SPI RTL suite at MODE 0–3 with `HALF` 4, 5, 7. Spec changed to `HALF >= 4` (SCK ≤ clk/8).
- **Fix:** in the same commit as the SPI tests.

## 5: I2C controller changed SDA in the same clock as SCL fell (found in review, before any test)
- **Date:** 2026-09-25
- **Symptom:** none observed; found by reading the first draft of `protocols/i2c_ctrl/i2c_ctrl_top.v`: the next data bit (and the ACK release) was driven in the same clock that SCL was pulled low, i.e. zero hold time. The draft also returned the wrong bits of the 9-bit shift register as the reply.
- **Root cause:** the bit sequence had no phase between "SCL low" and "SDA change"; reply bits were taken before the 9th sample was shifted in.
- **Caught by:** design review of the draft.
- **Now covered by:** `check_bus()` in `protocols/i2c_ctrl/test` (SDA may change while SCL is high only at START/STOP) and every reply check. It cannot see zero hold time at one sample per clock, so the fix is structural: a separate `S_B_SET` phase of Q clocks after SCL falls before SDA changes.
- **Also:** the I2C model test `test_nack_on_data_byte` first expected 4 replies for 5 bytes (the test miscounted; the model was right).
- **Fix:** before the first commit of the I2C controller.

## 6: I2C target test harness read host replies one clock late
- **Date:** 2026-09-25
- **Symptom:** `protocols/i2c_target/test`: three tests got `[]` from the host register reads.
- **Root cause:** test code. The design presents a read reply right after the clock edge that takes the command; with `h_rready` held high the reply is consumed at the next edge. The helper looked after that next edge.
- **Caught by:** `test_bus_write_then_host_reads`, `test_auto_increment_wraps`, `test_other_address_ignored`.
- **Now covered by:** the same tests; the helper samples `h_rvalid` right after the accepting edge.
- **Fix:** in the same commit as the tests.

## 7: `tools/profile` package broke every cocotb test
- **Date:** 2026-09-25
- **Symptom:** `protocols/uart/test`: `AttributeError: module 'profile' has no attribute 'run'`, no test ran.
- **Root cause:** the protocol test Makefiles put `tools/` on `PYTHONPATH`; a package named `profile` there shadowed Python's standard-library `profile` module, which cocotb imports.
- **Caught by:** the UART RTL suite (run after resizing the UART counters).
- **Now covered by:** every protocol suite (they import cocotb with `tools/` on the path); the package is `tools/profiling/`.
- **Fix:** renamed before the first commit of the profiler.

## 8: First D-017 stripe offsets put the east tiles' ground stripe outside the tile
- **Date:** 2026-09-26
- **Symptom:** `OpenROAD.GeneratePDN failed` for E_IO4, NE_term, SE_term (68.64 µm wide) after the tile stripe grid change.
- **Root cause:** arithmetic: offset 61.28 put the VPWR stripe at local 63.11–65.21 and VGND 4.1 µm further right, past the core edge (65.76). I had checked the power stripe position but not the ground stripe and the 2.88 µm core margins.
- **Caught by:** the tile flow's power-grid step.
- **Now covered by:** the same step, plus a written constraint in D-017 (every column type must fit a full VPWR+VGND pair: grid phase between 3.9 and 19.3 µm; chosen 12.00) and a pin-position check of every tile LEF before stitching.
- **Fix:** grid phase 12.00 (offsets 9.12 west / 50.40 others), before any commit.

## 9: Chip-level routing could not finish: fabric pins faced the die edge
- **Date:** 2026-09-27
- **Symptom:** CI `gds` run 36277723397: detailed routing still at ~10,500 violations (Metal1 3.6K, Metal2 5.4K, Metal3 1.5K) after 27 iterations, > 3.5 h into the job (log excerpt pasted by the user).
- **Root cause:** placement. The fabric macro sat at (11.52, 7.56), with its west face 8.6 µm from the die edge and its south face 3.8 µm from the bottom, but 152 of its 243 signal pins are on the west face (FrameData[127:0], west IO) and 67 on the south face (FrameStrobe[59:0], clock/reset). Every wire had to escape through a few tracks. I chose the location for the power and track grids only and did not check the macro's pin faces.
- **Caught by:** the chip-level `gds` job (detailed routing did not converge).
- **Now covered by:** the placement rule in D-019 (revision): pin-heavy macro faces must face open core; the pin-face count of the macro LEF is checked before choosing a location. The next `gds` run is the check.
- **Fix:** macro at (890.88, 113.40), same power-grid phase.

## 10: `"//"` comment keys inside a MACROS entry stopped LibreLane at config load
- **Date:** 2026-09-27
- **Symptom:** CI `gds` run 36292542000 failed after 3 min: `One or more keys unrecognized for dataclass Macro: //`.
- **Root cause:** I put `"//"` comment keys inside `MACROS.warp_tiny` in `src/config.json`. LibreLane accepts them at the top level only.
- **Caught by:** LibreLane config loading in CI.
- **Now covered by:** a local run of TT's merged config (`src/config_merged.json` from `tt_tool --create-user-config`) with the Nix LibreLane before pushing: it loads the config and runs through synthesis, floorplan, macro placement, the power grid (all LOOMPDN checks pass), global routing (0 overflow, 3.5 % usage) and detailed routing (0 violations, < 2 min). A comment in `config.json` warns against nested `"//"`.
- **Fix:** comments moved above the block.

## 11: Precheck pin check: pdngen added short power stripes beside the fabric
- **Date:** 2026-09-27
- **Symptom:** CI run 36293031051: `gds` and `gl_test` passed, precheck failed the pin check: `Port VGND/VDPWR is too far from bottom/top edge of module: 98.06 > 10 um` (4 errors).
- **Root cause:** with the fabric at x 890.88, the standard-cell rails in the 38 µm channel between the fabric and the core's east edge were not crossed by any grid stripe (the last pair runs inside the fabric, the next would be off the die). pdngen then adds a short "channel" stripe pair (x 1270.08 / 1274.40, y 98.06–612.58, the fabric's height plus halo), and TT requires every power port to span the block height.
- **Caught by:** TT precheck pin check (`pin_check.py`).
- **Now covered by:** a local stripe check after the power grid (every vertical Metal4 power stripe must reach within 10 µm of the top and bottom edges), run on TT's merged config before pushing. It flags both short stripes in the failed run's final DEF and finds none with the fix. Rule added to D-019: leave either no channel or one wide enough for a full grid stripe pair beside a macro.
- **Fix:** fabric at x = 780.96 (one grid step left): the 148 µm east channel holds a regular stripe pair; 24 full-height stripes, 0 short; routing 0 overflow, 0 DRC locally.

## 12: A zero-length load reached LOADED
- **Date:** 2026-09-27
- **Symptom:** the F2 cover run reached RUNNING in 15 cycles, too few for any real load: LOAD_BEGIN with LENGTH 0, then LOAD_END with the CRC of no words (0x00000000), passed every check.
- **Root cause:** the sync-word check ran on the first LOAD_DATA word; with no words there was no first word, so nothing flagged the load. A host could then RUN whatever partial configuration an earlier failed load left in the latches, which ARCHITECTURE §3 forbids.
- **Caught by:** `formal/f2_loader.sby` cover task (the trace length, not an assertion: the shadow loader had the same blind spot).
- **Now covered by:** LOAD_END rejects a load with no words as a format error (0x13); the F2 shadow requires at least one word; pin-level test `test_empty_load_rejected`.
- **Fix:** `src/wp_shell.v` LOAD_END check `fmt_err || wcount == 0`.

## 13: FABulous bitgen drops the global-clock mux selects
- **Date:** 2026-09-27
- **Symptom:** with the real fabric RTL, `counter4` loaded and reached RUNNING but its outputs stayed X; `logic4`, also clocked, worked.
- **Root cause:** `fabulous_bit_gen` 0.3.1 (`_apply_fasm_features`) skips every FASM feature whose name contains "CLK", meant for the bit-less `GCLK_END0.Lx_CLK` pips. It also drops `Xn Ym.N_GBUF_ENDk.GCLK_BEG0`, the select of the LUT tile's 4-input global-clock mux in the tile library. nextpnr routed counter4's clock through GBUF C (mux input 2); the select stayed 0, so the flip-flops never saw a clock. logic4's clock happened to use GBUF A (input 0, the all-zeros default). Stock FABulous fabrics have no such mux, which is presumably why upstream has not hit it; Tiny FABulous's own copy of the script has the skip commented out.
- **Caught by:** `test/test_bitstream.py::test_counter4` on the fabric RTL, then tracing the clock hop by hop from the pad to the LC (GBUF feed, SW_term, N_GBUF, the GCLK mux).
- **Now covered by:** `tools/compile/bitgen.py` (no skip, all rows); `test_gclk_mux_select_is_written`; `test_counter4` (clock through GBUF C). `test_matches_fabulous_bit_gen_except_clk_features` checks our generator equals upstream's on everything else.
- **Fix:** WARP's own bitgen in the compile flow. Upstream not edited (worth reporting to FABulous).

## 14: Compile flow merged two carry chains' start cells
- **Date:** 2026-09-27
- **Symptom:** `hostecho` (two 8-bit adders) failed place and route: `Carry cell ... carry_statrt has illegal multiple fanout on Co net`.
- **Root cause:** the compile flow's `opt_merge -share_all` (added to merge the identical enable/reset LUTs ABC duplicates per flip-flop, D-022) also merged the two adders' identical carry-start `LUT4_HA` cells; one carry output then fed two chains, which the fabric's carry wiring cannot do.
- **Caught by:** building `tools/compile/examples/hostecho` (nextpnr packing).
- **Now covered by:** `opt_merge -share_all t:LUT1 t:LUT2 t:LUT3 t:LUT4` (plain LUTs only); `hostecho` is a committed test bitstream, rebuilt and checked by the `fabric` workflow.
- **Fix:** `tools/compile/compile.py` synthesis script.

## 15: Placement failed with free logic cells: too many clock-enable nets for the tiles
- **Date:** 2026-09-27
- **Symptom:** the I2C controller on G1 needed 78 of 88 LCs but nextpnr found no legal placement (`Unable to find legal placement for cell ... FABULOUS_LC`), for every seed. On G0, the SPI controller (95 of 96) failed the same way.
- **Root cause:** the 8 LCs of a `LUT4x8_ha` tile share one clock-enable and one set/reset wire (`J_EN`, `J_SR` in the tile's switch matrix). Yosys mapped every enable it found onto the flip-flops (`-complex-dff`), so the I2C controller had 12 distinct enable/reset pairs, most of them used by a single flip-flop, for 11 LUT tiles. Each pair needs a tile of its own, whatever the LC count says.
- **Caught by:** `python -m compile.protocols` on G1 (place and route), then counting the flip-flops' (E, R) nets in the synthesized netlist.
- **Now covered by:** the compile flow runs `dfflegalize -mince 4 -minsrst 4` between `synth_fabulous`'s stages (`MIN_CTRL` in `tools/compile/compile.py`): an enable or synchronous reset used by fewer than 4 flip-flops becomes LUT logic. The same designs also got smaller (uart 37 → 29 LCs, spi_ctrl 51 → 47, i2c_ctrl places at 70; thresholds 2, 4 and 8 compared, `docs/reports/g1_results.md`). The protocol fit tables are the regression check.
- **Fix:** `tools/compile/compile.py` synthesis script. Consequence for architecture work: LC count alone is not capacity on this tile; the number of control sets is a second limit (phase 3 input).

## 16: I2C target rewrite left sda_o undriven
- **Date:** 2026-09-27 (caught before commit)
- **Symptom:** Verilator: `Signal is not driven: 'sda_o'` in the rewritten `protocols/i2c_target/i2c_target_top.v`; the RTL tests all passed.
- **Root cause:** the rewrite (shared register ports, hard shift register) dropped `assign sda_o = 1'b0`, the open-drain pin's output value. Undriven, it would float in simulation and be left to synthesis on the chip. The tests drive and watch only `sda_oe` (the open-drain model), so they could not see it.
- **Caught by:** a Verilator `-Wall` lint of the design, run by hand; CI linted only `src/`.
- **Now covered by:** the `lint` workflow lints every protocol user design in both forms (`PRIMS=0/1`) with `-Wall`; all 8 are clean (Verilator 5.020, the CI version).
- **Fix:** the assign restored.

## 17: Fmax of designs using the hard primitives left out every path through them
- **Date:** 2026-09-27 (found in review; no rate was claimed from these numbers)
- **Symptom:** `compile` reports and `docs/reports/g1_results.md` gave Fmax for UART (123.5 MHz), SPI (88.9) and I2C controller (69.2) on G1; the critical paths shown were all LUT to LUT, although these designs have paths from the timer's `tc` and the shift register's `q` into logic, and from logic into the blocks' `load`, `step` and `en`.
- **Root cause:** nextpnr's FABulous back end gives timing arcs only to the tile library's own cells (LUT 3.00 ns, clock-to-Q 1.00 ns, setup 2.50 ns, fixed) and times routing with the fabric's extracted pip delays. The WARP primitive BELs (`wp_timer`, `wp_shift`) get no arcs, so their pins are neither start nor end points and every path through them is dropped from the analysis.
- **Caught by:** reading the critical-path reports while documenting the timing model (PHASE2 item).
- **Now covered by:** the report marks the column as incomplete and no rate is claimed; OVERVIEW risk updated; the phase 2 timing-model item stays open until the primitives have timing arcs (or a documented conservative bound) and a configured design is cross-checked by STA.
- **Fix (2026-09-27/28, D-028):** primitive timing arcs from OpenSTA of each primitive synthesized alone (slow corner), written to `placement_estimate.txt`; the compile flow uses nextpnr 0.11.1 (OSS CAD Suite 2026-09-27), which reads it (upstream nextpnr reads per-BEL arcs since 2026-07), and refuses a fabric with primitives but no arcs. Cross-checked against STA of the hardened primitive tile (`tools/timing/tile_check.sh`): the first margin (×1.5) under-covered the timer's in-tile setup (4.0 vs 1.4 ns standalone), so setup/combinational arcs use ×3.0, clock-to-out ×1.5. Result: UART 90.7 MHz, SPI 78.0, I2C controller 53.0 (were 122.0, 88.9, 69.2 with those paths untimed), all above 50 MHz.

## 18: Reset release not synchronized to the clock
- **Date:** 2026-09-28
- **Symptom:** TT's Verilator lint in the `gds` job: `SYNCASYNCNET: Signal flopped as both synchronous and async: 'rst_n'` (present since the phase 2 shell; noticed by the user in the linter summary).
- **Root cause:** the TT `rst_n` pin (driven by the demo board, asynchronous to `clk`) goes unsynchronized to FABulous's `ConfigFSM` as an asynchronous reset and to the shell, the pin logic and the user reset as a synchronous reset. Its release can land at any point of the clock cycle, so flip-flops can leave reset on different cycles, or go metastable (the configuration FSM and its strobe register included). Effect in the worst case: a wrong state right after reset (e.g. a first load that fails and must be retried); no effect once reset has been released cleanly.
- **Caught by:** the TT workflow's lint summary (not an error there); our `lint` waives upstream files (`src/lint.vlt`) and does not run this check on the whole top.
- **Now covered by:** the full-top Verilator `-Wall` lint without waivers reports no `SYNCASYNCNET` (and no `WIDTHTRUNC`); `test/` suite 21/21 on the fabric RTL, black-box mode 13 + 8 skipped; F1 PASS (k-induction). CI 36383587262 on 3047dea: gds, precheck, `gl_test` 21/21, setup WS +12.48 ns.
- **Fix:** `src/tt_um_warp.v`: a 2-flop reset synchronizer (`rst_sync`, no reset of its own); every block is reset from `rst_s_n`, and the configuration path (ConfigFSM's asynchronous reset) from its own copy one flop later (`rst_cfg_n`), so no net is used as both a synchronous and an asynchronous reset. Reset now takes effect 2 clocks after `rst_n` falls and ends 2 clocks after it rises (3 for the configuration path). Also `src/wp_fabric_cfg.v` passes Frame_Data_Reg's `Row` sized to its width (the `WIDTHTRUNC` warning; no logic change). The next hardening's one change.

## 19: Active-low outputs are asserted while the chip is stopped
- **Date:** 2026-09-28
- **Symptom:** `test_board_examples_spi`: the SPI target model saw an empty CS-low transaction before the real one.
- **Root cause:** by design (ARCHITECTURE §4, F1), every fabric output is parked while the chip is not RUNNING: `uo_out[2..7]` at 0 and `uio` released (output enable 0). A user output that is **active low** on a `uo_out` pin, such as the SPI controller's CS_N on FAB_OUT2, is therefore asserted from reset through loading, and again after STOP. No SCK edges happen then (SCK parks at 0 = idle for mode 0/1), so no data moves; but a device that acts on CS alone (e.g. a flash leaving deep power-down) sees it. The parking itself is the chip's safety property and stays; the hardware is frozen.
- **Caught by:** `test/test_bitstream.py::test_board_examples_spi` (a reference target on the pins from reset on).
- **Now covered by:** the test asserts the behaviour (at most one empty transaction before RUN); `docs/EXAMPLES.md` documents it and the fix at the pin-map level.
- **Fix:** user-level: put active-low outputs on bidirectional pins (`FAB_IO*.o` with an enable, plus a pull-up), which park released (high through the pull-up). No hardware change.

## 20: Fabric RTL test reused the idle-fabric simulator from the previous command
- **Date:** 2026-09-28
- **Symptom:** following the README from a clean source export, `scripts/check_all.sh` passed, but the next command, `make -C test WARP_FABRIC=rtl`, failed `test_counter4`: the counter stayed at zero. The second command's log had no Icarus compile step.
- **Root cause:** `test/Makefile` put both the default `stub` model and the `rtl` fabric model in `test/sim_build/rtl`. Cocotb's Makefile saw the executable built for `stub` as current and reused it, even though `WARP_FABRIC` changed.
- **Caught by:** the Phase 5 clean-source README reproduction, in the documented command order.
- **Now covered by:** `test/Makefile` uses `sim_build/$(WARP_FABRIC)` for RTL simulations, so a change between `stub` and `rtl` requires a new compile. The clean-source reproduction reruns the two commands in order.
- **Fix:** separate simulator build directories by fabric model. No chip RTL change.

## 21: LibreLane DRC XML merges violations from different metal layers
- **Date:** 2026-09-30
- **Symptom:** session 34's generated XML reported all 3,384 shorts as `Metal3.Short`, unlike the native router report: 471 Metal2, 1,278 Metal3 and 1,635 Metal4 shorts.
- **Root cause:** pinned LibreLane `common/drc.py::DRC.from_tritonroute` indexes its violation dictionary by violation type alone, retaining the first layer while appending coordinates from subsequent layers. Total counts and coordinates remain useful; the XML category is not reliable for layer attribution.
- **Caught by:** comparison of `cfgmacro_x121_m4obs/39-openroad-detailedrouting/tt_um_warp.drc`, the router log and generated XML.
- **Now covered by:** session 34's corrected layer counts and the compact-edge experiment README explicitly require native router reports for layer attribution. Upstream code is unchanged.
- **Fix:** use the native `.drc` report/router log when reporting layer counts; an upstream converter fix remains open.

## 22: Concurrent FABulous tile parsing corrupts shared primitive JSON
- **Date:** 2026-09-30
- **Symptom:** concurrent north/south scratch tile hardening failed with `JSONDecodeError: Invalid control character` while reading `primitives/IOBUF/fabulous/IOBUF.json`; serial reruns passed.
- **Root cause:** FABulous's `fabric_definition/yosys_obj.py` writes parsed BEL metadata beside the shared primitive. Two tile drivers in the same library can overwrite/read that file concurrently.
- **Caught by:** the compact-edge north/south hardening experiment.
- **Now covered by:** `spikes/compact_edges/run.sh` runs tile drivers sequentially; all 14 changed tiles completed with clear routing and KLayout DRC. Per-tile run IDs are in the experiment README.
- **Fix:** serialize tile parsing in a shared library. Upstream code is unchanged.

## 23: Scratch simulation driver exits successfully after a cocotb failure
- **Date:** 2026-09-30
- **Symptom:** the new hardened-fabric/post-CTS-shell test returned process status 0, but its results XML contained a failed test (`X` in a status read after RUN).
- **Root cause:** `runner.test()` wrote the result XML without raising for that failed test; the scratch driver checked neither test count nor failure/error elements.
- **Caught by:** inspecting `simulation_chip_mask_narrow_rows_mapped_fabric_mapped_shell/results.xml` and `test.log`. Earlier reported passes were checked against their XML and remain valid.
- **Now covered by:** `spikes/compact_edges/simulate.py` explicitly rejects missing testcases and failure/error elements after the simulator finishes.
- **Fix:** validate XML and raise on failure. The hardened-fabric unknown-value issue is separate and remains under investigation; no gate-level pass is claimed for that run.

## 24: I2C decoder failure hid sigrok's environment error
- **Date:** 2026-10-05
- **Symptom:** the I2C controller's independent bus checks passed but the sigrok byte comparison returned an empty list.
- **Root cause:** sandboxed libusb initialization returned `LIBUSB_ERROR_OTHER`; sigrok exited 0 with empty stdout and the harness discarded stderr. This was an execution-environment failure, not an observed RTL fault.
- **Caught by:** `scripts/check_all.sh`, then a diagnostic rerun of `protocols/i2c_ctrl/test`.
- **Now covered by:** `sigrok_decode` rejects an empty decoded byte list and includes stdout/stderr in the assertion. The full check rerun outside the sandbox passes (`build/check_all_20261005.log`).
- **Fix:** retain decoder diagnostics in the test and run libusb-dependent checks with the required execution permission. No RTL change.

## 25: Scratch shared-word CRC read a changing byte-assembly wire
- **Date:** 2026-10-05
- **Symptom:** the scratch CRC passed stable-input unit comparisons but the real 842-word SPI load failed with CRC error `0x12`.
- **Root cause:** the first integration read `{pay, rx_byte}` directly. The shell shifts `pay` on the same edge as word completion, so that concatenation changes immediately after the original CRC would have captured it. Host word spacing alone does not make this wire stable.
- **Caught by:** `simulation_chip_shared_crc/results.xml` real SPI load, before any physical selection.
- **Now covered by:** the full SPI/UART/STOP scratch test and `test_internal/shared_crc_probe.py`, which checks that the actual registered input remains stable throughout CRC processing. The stable-word unit test still compares every cycle to the original CRC and final values to zlib.
- **Fix:** the optional scratch shell connects CRC to the existing `cfg_word` register, updated at the word-complete edge; bit consumption begins on the following edge. The corrected real load/UART test passes (`build/arch_explore/compact_edges/shared_crc_shell_20261005.log`). Frozen G1 is unchanged; the physical experiment is still unselected.

## 26: Independent input monitor misses events on a synthesized gate shell
- **Date:** 2026-10-05
- **Symptom:** Existing SPI-loaded UART+monitor passes RTL fabric/shell testing, but a newly synthesized gate shell with RTL fabric transmits correctly and returns zero event count after20 input pulses.
- **Root cause:** under investigation. Read-only tracing shows synchronized fab_in transitions known, event_previous FF updates, resets/enables known, but the counter enable is zero at sampled clock edges. Mixed gate/RTL input-to-enable scheduling/timing is a hypothesis, not proven silicon behavior. No user state or configuration forced.
- **Caught by:** `build/g1_monitor_gate_20261005/results.xml`, Icarus13/project-venv cocotb; synthesized shell is not the hardened netlist. White-box traces in `probe3.log`/`probe4.log` and `test_internal/uart_monitor_gate_probe.py`.
- **Fix for the observed test:** sample the shell input into one additional fabric FF before forming the edge enable; adds one cycle of observation latency and one LC (36→37). Both actual loaded regressions PASS: `uart_monitor_sampled_20261005/rtl_results.xml` (23.23s) and `g1_monitor_gate_20261005/sampled_results.xml` (33.82s), under `build/`. This resolves the observed mixed-model mismatch; physical timing/root-cause proof remains open. No frozen hardware change.
- **Coverage:** `test/test_uart_monitor.py`, overlapping TX/events, RX/events, counter wrap, framing status and host reset; prospective same test on gate shell. Fix commit: pending.

## 27: Failed compiler rebuild could leave a stale success report
- **Date:** 2026-10-05
- **Symptom:** rebuilding into an existing output directory could fail place/route while retaining `report.json` from an earlier successful design.
- **Root cause:** success reports were written only after completion, with no invalidation when a new build began.
- **Caught by:** a deliberate stale-success report followed by the over-capacity binary-I2C build (95/88 LCs), `build/compiler_fit_diagnostic_20261005/verification.txt`.
- **Fix:** invalidate prior success/failure reports at build start; place/route failures write a separate `failure.json` with utilization and actionable capacity diagnostics.
- **Coverage:** compiler diagnostic regression in `tools/compile/tests/test_diagnostics.py`; actual vendor-tool check above. No hardware change.

## 28: Failed compiler rebuild retained an old loadable image
- **Date:** 2026-10-05
- **Symptom:** invalidating reports alone still left the earlier `.wbit` at the path users would load after a failed rebuild.
- **Root cause:** images were overwritten only on success, without invalidation when rebuilding the same target.
- **Fix:** remove the exact target image after reading the pin-map top/name and before synthesis; preserve differently named images. A subsequent success generates the image normally.
- **Caught/covered by:** extended compiler diagnostic tests and actual95/88-LC binary-I2C failure (`build/compiler_stale_image_20261005/verification.txt`). Fresh successful fault-demo rebuild remains byte-identical to the already loaded/tested image. No chip change.

## 29: Default primitive timing audit could select a newer experimental tile
- **Date:** 2026-10-05
- **Symptom:** default tile timing check selected the latest completed PRIM2T2S run even when its netlist differed from the committed G1 tile; historical run paths were absent.
- **Root cause:** selection used recency and file existence, without binding the routed artifacts to the chip being assessed.
- **Caught by:** fresh audit/source check; committed netlist SHA25613fec76424949b0d25789ca8d0721b74d4acdba5ff93eaeb99dfb4d412f6a170 differs from latest run2c49c0e6dba54229e6d9e267df28dc373a5191258fb08b716bb7ee7ff6973dc0. No completed local run is byte-identical to the committed tile; semantic equivalence of other runs is not established.
- **Fix:** default selects only matching netlists and requires matching SPEF; an explicitly supplied variant is rejected unless `WARP_TIMING_ALLOW_VARIANT=1`, which labels the comparison experimental. A byte mismatch is conservative rejection, not proof of functional difference.
- **Coverage:** `build/primitive_path_audit_20261005/default_missing_artifact_check.log` rejects unavailable matching evidence; explicit missing-artifact and variant checks; shell syntax passes. Historical timing numbers remain historical; no refreshed G1 timing pass claimed.

## 30: Bare OpenDB cell swap crashes the pinned STA callback
- **Date:** 2026-10-06
- **Symptom:** isolated pin-hotspot resize crashes with signal11 before placement; no output database is written.
- **Root cause:** geometry-only helper reads an ODB without Liberty, then calls `dbInst.swapMaster`. The pinned callback `dbStaCbk::inDbInstSwapMasterBefore` reaches `sta::ConcreteCell::portCount` without loaded Liberty cell objects. This is a scratch-tool setup issue, not an observed chip fault.
- **Caught by:** `build/route_root_audit_20261006/chip_nor3_pin_screen/placement.log` stack trace and exit139.
- **Fix/coverage:** require `WARP_SIZE_LIB` and `read_liberty` before `read_db`/swap. Actual rerun `placement_with_liberty.log` reaches detailed placement, which separately reports a local legalization failure; no routing or legalization pass claimed from resolving the crash. Frozen/upstream files untouched.

## 31: Hosted fault-monitor compile omitted its monitor dependency
- **Date:**2026-10-06.
- **Symptom/check:** hosted compact experiments37511778394; monitor compiles/audits and passes loaded RTL in22.72s, then fault synthesis reports missing uart_monitor_top.
- **Root cause:** new cloud driver supplied fault top and UART sources but omitted the intermediate monitor module present in the documented local compile command.
- **Fix:** include protocols/uart_monitor/uart_monitor_top.v only for the fault case. No hardware/compiler change.
- **Coverage:** hosted37512249763 at f671c1b passes all four fresh compile/audit/loaded RTL cases; independently checked four XMLs, exactly one case each, no failure/error/skip. See `docs/reports/hosted_experiments_20261006.md`. The first run remains failed; no native/SDF result is implied.

## 32: Docker no-TTY flag followed eager container launch
- **Date:**2026-10-06.
- **Symptom/check:** compact37512885358 attempt2 route job downloads/verifies inputs and Docker image, then exits with the input device is not a TTY before OpenROAD starts.
- **Root cause:** cloud driver placed docker-no-tty after dockerized; LibreLane's eager container callback launches before later options are applied.
- **Fix:** place docker-no-tty first. No source/PDK/physical checker changes.
- **Coverage:**37516278474 passes container launch and reaches directory validation;37516794406 passes that validation and remains in the routing step. No final routing pass implied. [Pinned CLI contract](https://github.com/librelane/librelane/blob/3.1.0.dev3/librelane/__main__.py).

## 33: Tighter native fabric retains unknown user state after real load
- **Date:**2026-10-06.
- **Symptom/check:**37512885358 attempt2 native job: tighter RTL control passes; actual mapped fabric fails UART recording with X at output. All8707 configuration bits are known and image-matching;26944 CRC processing cycles have stable input. Selected user registers already unknown before RUN despite shell user_reset=1/user_rst_n=0.
- **Root cause:** unresolved. Known configuration is insufficient to distinguish mapped logic/reset behavior from zero-delay combinational/model pessimism. No hardware/model fix claimed.
- **Next coverage:** derive a read-only cone JSON from the exact mapped tile and trace LB register D logic at pre/post RUN; separately probe the real USER_RESET command while retaining ordinary native failure. No configuration or user-state force. Existing D-023 routing harness remains explicitly limited; native/SDF acceptance is open.
- **Follow-up:**37516794406 cone extraction/RTL control pass; native baseline18.81s and real USER_RESET probe19.12s both fail with UART X. Known configuration does not identify the root cause. Next diagnostic follows selected mux branches and actual UART output at Tile_X6Y2, with tile boundaries labeled explicitly.
- **Failure-time evidence:**37519661148 shows UART X at4423540ns persists after same-edge delta-cycle settling. Actual selected output cone reaches Tile_X6Y2.E2END[7]. Next read-only probe follows exact macro connections across tiles and stops at clocked state; no hardware fix established.
- **Isolated state source:**37521660597 filtered UART cone ends at Tile_X2Y3_LUT4x8_ha_C2.Inst_LH_FABULOUS_LC.LUT_flop after41unknown nodes, D=X/RESET_B=1 at failure. Next probe checks that register's exact data/reset paths and configuration selectors. This identifies a source state boundary, not the original cause of unknown state.
- **Timer evidence:**37522773342 timer count becomes configured15/armed1 after RUN, then counter goes entirely unknown while armed remains1. Added first-known-to-X edge watcher with stable pre-edge D/reset snapshots; later feedback X alone does not identify original corruption.
- **Before corruption:**37523983755 at4423490ns timer count remains15, but D inputs are allX with reset pins1. All8707 configuration bits still match the loaded image. Trace follows upstream logic; original cause remains unresolved. Unknown mux selectors are filtered only when Boolean sensitivity proves irrelevance under known inputs.
- **Direct comparison:**37532673220 still reaches trace cap despite selector filtering. Added separate RTL companion sharing real shell/configuration input ports and ordinary D-023 routing pulse; native outputs remain authoritative. Compare timer control/state and tile route vectors without changing actual mapped netlist, configuration or user storage. Hosted verification pending.
- **Matched-input result:**37535155011 reaches UART X with same-input companion snapshots. At4423490ns local timer load/half are unknown while RTL retains count15. Unregistered constant LUTs (X1Y2 LD=0, X2Y1 LB=0/LD=1) have native O=X. Next probe traces those actual mapped cones; neither benign pessimism nor a hardware root cause is established. See compact_native_diagnosis.md for scope and run evidence.
- **Verified local false-X:**37546145073 proves those three constants in actual mapped logic for arbitrary binary tile inputs/user state under all529 observed configuration latch values per tile.37546984612 independently audits all9164 actual latches against loaded frame image, all known/matching at pre-corruption. D-047's five-mux4 candidate passes exhaustive symbolic binary equivalence and2916 partial-input tests in37546784325. Whole native UART remains unresolved; regenerated native candidate37552796495 pending, no physical/timing promotion.

## 34: Hosted LibreLane requires existing forced run directory
- **Date:**2026-10-06.
- **Symptom/check:**37516278474 route passes Docker launch, then CLI rejects nonexistent forced native_route directory before OpenROAD.
- **Root cause:**3.1.0.dev3 validates force-run-dir with exists=True; our fresh cloud root omitted its run directories.
- **Fix/coverage:** create both empty native/geometry run directories under the already freshness-checked output root before invoking CLI.37516794406 passes validation and continues in the routing step; physical checker results pending.

## 35: Distribution Yosys cannot parse PDK model specify syntax
- **Date:**2026-10-06.
- **Symptom/check:**37516278474 native RTL control passes; new read-only cone extraction fails parsing PDK Verilog line43's specify syntax before native tests.
- **Root cause:** distribution Yosys parser does not support this PDK model timing syntax, even when read as black-box library.
- **Fix/coverage:** read signal port directions from the pinned standard-cell Liberty with read_liberty -lib, then read actual tile netlist without mapping/optimization.37516794406 successfully emits actual_tile_cone.json and reaches both native tests. Simulation uses unchanged official Verilog/UDP models. BUG33 remains open; fixing extraction does not qualify hardware.


**BUG33 resynthesis follow-up:**37552796495/37553037381 five-mux candidates
pass actual SPI-loaded native UART. Matched original-LUT resynthesis37553190074
also passes, so a mux-only causal claim is unsupported. Original hardened
netlists still fail; regenerated netlists require matching physical/timing
validation. Next coverage adds real USER_RESET and preserves candidate netlists.
