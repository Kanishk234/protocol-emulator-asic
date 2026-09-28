# Bugs

Format for each entry: number, date, symptom, root cause, the check that caught it, the check that now covers it, fix commit.

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
