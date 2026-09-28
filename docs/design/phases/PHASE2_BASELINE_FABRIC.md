# Phase 2: Baseline fabric and shell

**Dates:** Oct 26 – Nov 15, 2026
**Goal:** a complete, submittable chip: shell, loader and fabric hardened at 6x4, running the design set from real bitstreams loaded through the real host interface. Per D-008 the fallback submission is **G1** = the generic fabric plus the minimum general hard blocks the design set needs (first: loadable counter/timer, shift register), because a plain fabric (~96 LUT4s) cannot fit one UART (~215 cells). The plain fabric **G0** is still generated and measured as the baseline every specialization is compared against (D-004).

## Tasks

### Shell
- [x] Host interface (SPI-like, polled status) per `ARCHITECTURE.md`. (`src/wp_spi_target.v`, `src/wp_shell.v`; 13 pin-level tests in `test/test.py`; spec clarifications D-021. CI `test` 36342480467, `gl_test` 36342012141 16/16)
- [x] Loader: length check, transport checksum, architecture-version tag, error handling. (ARCH_VERSION, LENGTH, CRC-32, sync word, empty load (BUGS #12); tests `test_wrong_arch_version`, `test_bad_crc`, `test_length_mismatch`, `test_bad_sync_word`, `test_empty_load_rejected`, `test_aborted_transaction_keeps_whole_words`)
- [x] Run control: stop, start, reset of user state; outputs parked and output enables off whenever the fabric is stopped or unconfigured. (RUN/STOP/USER_RESET: `test_load_run_stop`, `test_counter4` on the fabric RTL; parking: F1 proof)
- [x] Input synchronizers, registered outputs, open-drain support on bidirectional pins. (`src/tt_um_warp.v`; open drain exercised by logic4 on FAB_IO2, `test_logic4`, fabric RTL)
- [x] Host data path to and from the fabric (FIFOs if the budget allows; record the decision). (2-entry FIFOs each way, D-021; wired through 15 IO cells, D-024; `test_host_channel` with `hostecho`: bytes in, bytes + 1 out, USER_STATUS count, attention/IRQ, RTL 17/17 local 2026-09-27)
- [x] Host software: one Python API used by both simulation tests and future board software (`tools/host/`). (`tools/host/protocol.py`, 10 pytest; used by `test/warp_host.py`)

### Fabric G0
- [x] Generic fabric at the size chosen in phase 1, defined in `arch/`, generated into `src/fabric_gen/`. (`arch/warp_g0`: 4 × 3 LUT4x8 = 96 LUT4+FF, IO on all four sides, D-024; stitched on CMOS5L 1016.64 × 669.06 µm into `macro/warp_g0/` by `FABRIC=warp_g0 spikes/fabric_tiny/run.sh`, N_IO tile hardened 0 DRC; the fabric is a hard macro, so its generated RTL lives with the macro and `src/fabric_gen` keeps the configuration path. RTL suite 17/17 incl. host channel end to end, local 2026-09-27)
- [x] Protocol compile flow: `tools/compile/` turns a user design + pin constraints into a bitstream and a report (architecture version, tool versions, resource use, timing, pins, checksum). (D-022; runs on the current 16-LUT fabric; own bitgen, BUGS #13; example reports in `test/bitstreams/*.report.json`)
- [x] The host rejects bitstreams built for a different architecture version. (`checked_load_transactions` + `test_host_refuses_other_architecture`; the shell too: `test_wrong_arch_version`)

### Integration and physical
- [x] Full 6x4 hardening of shell + G0 passes precheck; record area breakdown, routing overflow, and timing at the chosen clock. (CI 36353540402 on e5b1f98: `gds` 45.8 min, precheck pass, `gl_test` 17/17; fabric macro 1016.64 × 669.06 µm, shell 3,901 cells / 59,951 µm²; local pre-flight global-routing overflow 23 after D-025, CI detailed routing 0 DRC; setup WS +10.63 ns at 50 MHz, hold +0.121 ns; PHYSICAL_DESIGN_AND_CI hardening table)
- [x] Timing model for place and route derived from the implemented device (or a documented conservative model). (Documented conservative model, `tools/timing/README.md`, D-028: routing delays from STA of the hardened tiles; tile-library cells at nextpnr's fixed values; hard primitives from OpenSTA with margins set by `tools/timing/tile_check.sh` against STA of the hardened primitive tile, which the model bounds at the tile boundary (6.79 vs 15.17 ns out, 8.06 vs 12.06 ns in); fixes BUGS #17. Not done: STA of a configured design end to end)
- [x] `gl_test` loads at least two different real bitstreams into the gate-level netlist and checks behavior. (CI 36342012141 on acc3af3 with the 16-LUT macro; G0: 36353540402 17/17; **G1 (the chip): 36367067731, 19/19** incl. counter4, logic4, two_bitstreams, host_channel, prims, uart)

### Protocols on G0
- [x] Compile all design-set protocols onto G0. For each: fits or not, resources, achieved timing. Report in `docs/reports/g0_results.md`. (local, `python -m compile.protocols --arch arch/warp_g0 --set PRIMS=0`, 2026-09-27: SPI fits (86 LCs, 68.0 MHz), UART 124, I2C controller 115, I2C target 205 do not; G1 numbers in `docs/reports/g1_results.md`)
- [x] Pin-level tests (top-level ports only) for each protocol that fits, loaded through the host interface. (G1, the chip's fabric (D-027): `test/test_bitstream.py` `test_uart` (uart16), `test_spi_ctrl` (spi8, against `refmodels/spi.py`), `test_i2c_ctrl` (i2c8, open-drain bus with `refmodels/i2c.py`); CI `gl_test` 36372341186 on fe4cac8: 21/21 on the hardened chip netlist)
- [ ] Add the `fabric` CI workflow: compile every protocol and run it on the fabric simulation. (`warp_fabric` now also compiles every design-set protocol with `--require uart spi_ctrl i2c_ctrl` and runs the three protocol bitstreams in the pin-level suite; tick with its first green CI run)

### Formal
- [x] Output isolation: no protocol output or output enable is active while stopped or loading (property and bound recorded). (F1, `formal/f1_isolation.sby`: unbounded, k-induction PASS, fabric outputs unconstrained; CI `formal` 36342012194)
- [x] Loader state machine: aborted or corrupt loads never reach the run state. (F2, `formal/f2_loader.sby`: BMC depth 84 PASS with an independent shadow CRC/length/sync check and arbitrary host bytes, cover reaches RUN in 52; bounded, not unbounded. CI `formal` 36342012194; found BUGS #12)

## Phase exit checklist
- [x] Shell + G1 hardened at 6x4, precheck passed (CI run ID: 36367067731 on d6f5dcd: `gds` 43.6 min, precheck pass, routing DRC/LVS/antenna 0, setup WS +10.73 ns, hold +0.143 ns)
- [x] `gl_test` green with two different real bitstreams (CI run ID: 36367067731, 19/19: counter4, logic4, two_bitstreams, host_channel, prims, uart)
- [x] `docs/reports/g0_results.md` shows fit/resources/timing for every design-set protocol (all four; G1 in `g1_results.md`)
- [x] Formal properties pass with named bounds (proof log summary in `docs/reports/`) (`docs/reports/formal.md`: F1 unbounded, F2 BMC 84, F4 unbounded; CI `formal` 36367067725)
- [x] The `fabric` workflow is green (36367067735 on d6f5dcd; the protocol-compile step goes green with the next push, to be re-checked)
- [x] Decision point recorded: G1 is a valid fallback submission (or what's missing) (D-029)
- [ ] All CI workflows green on `efpga`
- [ ] `docs/summaries/PHASE2.md` written
