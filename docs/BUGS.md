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
- **Root cause:** not yet known. The 4 via rules are the power-grid vias OpenROAD generates for the Metal4/TopMetal1 grid; Magic's CMOS5L tech file (PDK 2bbec75) apparently has no matching via rule.
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
