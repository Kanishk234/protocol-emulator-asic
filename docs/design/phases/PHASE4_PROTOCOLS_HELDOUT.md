# Phase 4: Protocols, showcase, held-out evaluation

**Dates:** Dec 7 – Dec 22, 2026
**Goal:** show what the frozen chip can do. Everything in this phase is bitstreams and tests, not silicon changes, which is the core claim of the project: new protocols after fabrication.

## Tasks

### Held-out evaluation (the generality test)
- [x] Unseal `HELDOUT.md`. For each held-out protocol: write the user design and an independent reference model, compile onto the frozen fabric, test. (unsealed 2026-09-28 after `hw-freeze`; H1–H4 in `protocols/{ws2812,onewire,swd,can}`, models in `tools/refmodels/{ws2812,onewire,swd,can}.py`; RTL tests pass in both forms; H1–H3 fit and pass chip-level tests through the host interface (`test_ws2812`, `test_onewire`, `test_swd`), H4 does not fit)
- [x] Report every result honestly in `docs/reports/heldout_results.md`: fits or not, resources, rate reached, what limited it. Failures are results too. (3 of 4 run; CAN does not fit, 207 of 88)
- [x] Compare held-out resource use on the final architecture vs. G0 (from a G0 build) to show whether specialization generalized. (`heldout_results.md` summary: G1 saves 17–50 LCs per protocol; 1-Wire fits only on G1)

### Software side (D-032: required by the organizers)
- [ ] Loader for the Tiny Tapeout demo board: a MicroPython module for its RP2040 that speaks the host protocol (ARCHITECTURE §2–3) through the board's pins, sharing its transaction encoding with `tools/host/protocol.py` (tested in simulation against the chip's RTL/gate-level netlist through the same transactions; on hardware only when a board exists). (`tools/board/warp.py` + README; pytest 270 (equal to the reference, byte for byte); `test_board_loader` passes on the fabric RTL locally 2026-09-28; tick with CI `gl_test`)
- [x] One command per step, from source to running protocol: compile (`tools/compile`), load, run, read status; documented end-to-end examples for UART, SPI and I2C (source, pin map, bitstream, host session). (`docs/EXAMPLES.md`; board helpers `tools/board/examples.py`; the board code tested against the chip model: `test_board_loader`, `test_board_examples_spi`, `test_board_examples_i2c`, local 2026-09-28; the guide's compile commands run as written)

### Showcase
- [x] ~~I2C target with fault injection~~ (does not fit, D-035). Replaced (D-036): one chip, six protocols switched at run time through the host interface, each against its reference device (`test_showcase_protocol_switching`: UART, SPI, I2C, WS2812, 1-Wire, SWD in one simulation, no reset; passes on the fabric RTL locally 2026-09-28)
- [x] Concurrency demo if resources allow (e.g. I2C target plus UART at the same time). (Resources do not allow: every pair exceeds 88 LCs or 2+2 hard blocks, D-036; not done)

### Stretch protocols (only after the above)
- [ ] Pick from remaining candidates (JTAG, SWD, PS/2, 1-Wire, CAN). Report fits and failures.

### Robustness and verification depth
- [x] Reconfiguration tests: stop, partial transfer, bad checksum, wrong architecture version, reload, restart; outputs stay parked until a valid start. (test.py: wrong arch, bad CRC, length, sync, empty load, aborted transaction, reload, restart after STOP, parking under inputs (CI `test`/`gl_test`); new `test_corrupt_load_over_running_design`: a corrupt load over a running real design leaves the fabric half-written, the chip in ERROR with every pin parked and RUN refused, then a valid load runs; local 2026-09-28)
- [x] Input phase tests: external protocol edges at varied phases relative to the system clock. (`test_uart_input_phase`: 12 UART bytes with every edge at a random 1–19 ns phase, all received, no flags; RTL simulation does not model metastability)
- [x] Fault injection (mutation) campaign: wrong configuration-bit position, timer off-by-one, lost FIFO item, inverted output-enable. Each must be caught; investigate any that survive. (`scripts/mutation.py`, `docs/reports/mutation.md`: 8 mutants incl. the four named plus shift register wrong end, CRC check off, architecture check off, parking gate removed; all 8 killed by their intended check, local 2026-09-28)
- [x] Bounded equivalence or co-simulation between a protocol's source RTL and its configured-fabric simulation for at least one small design. (`test_internal/cosim`: the UART source RTL next to the chip with uart16 loaded through the host pins, one simulation: TX waveforms identical sample for sample for 4 bytes, RX bytes and flags equal for 6 frames; local 2026-09-28, CI `fabric` step added)

## Phase exit checklist
- [x] `docs/reports/heldout_results.md` covers every held-out protocol
- [ ] Showcase passes its tests from a real bitstream through the host interface (run ID: …)
- [ ] Reconfiguration test suite green (run ID: …)
- [x] Fault-injection results recorded; no unexplained surviving faults (`docs/reports/mutation.md`: 8 of 8 killed)
- [ ] No hardware changes since `hw-freeze` except logged bug fixes
- [ ] All CI workflows green on `efpga`
- [ ] `docs/summaries/PHASE4.md` written
