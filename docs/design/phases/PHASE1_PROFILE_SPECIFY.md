# Phase 1: Profile, specify, de-risk

**Dates:** Oct 5 – Oct 25, 2026
**Goal:** know, with measurements, what protocol logic actually needs and whether it can fit. Retire the biggest physical risk by hardening a tiny fabric on CMOS5L. Write the specs everything else follows.

## Tasks

### Seal the held-out set (do this first)
- [x] Choose 3–4 held-out protocols (candidates: 1-Wire, WS2812, SWD, PS/2, JTAG, CAN). Pick a spread: timing-coded, clocked, bidirectional, and one with CRC or bit-stuffing if possible. (WS2812, 1-Wire, SWD, CAN; D-013)
- [x] Write `docs/design/HELDOUT.md` with the list, the scope of each, and the rule that nothing is written or profiled for them until the hardware freeze. Commit it before any profiling (the commit hash is the seal). (seal 0171cf7)

### Design-set protocol RTL (as user designs)
- [x] `protocols/uart/`: TX and RX, configurable baud divisor, framing error. (8 cocotb tests vs `tools/refmodels/uart.py` + sigrok, DIV 16/13 and runtime divisor, all pass locally 2026-09-25; CI `unit` 36211778569)
- [x] `protocols/spi_ctrl/`: all four modes, chip select, full duplex. (4 cocotb tests × 6 configurations vs `tools/refmodels/spi.py` + sigrok, 24/24 pass locally 2026-09-25; CI `unit` 36211778569)
- [x] `protocols/i2c_ctrl/`: start, repeated start, stop, ACK/NACK, clock stretching, open-drain outputs. (6 cocotb tests × 3 speeds vs `tools/refmodels/i2c.py` + sigrok, 18/18 pass locally 2026-09-25; CI `unit` 36211778569)
- [x] `protocols/i2c_target/`: address match, small register map, read/write. (6 cocotb tests × 3 bus speeds driven by the reference controller model + sigrok, 18/18 pass locally 2026-09-25; CI `unit` 36211778569)
- [x] Independent reference models in `tools/refmodels/` (written without reading the RTL) and RTL-level tests for each. (`uart.py`, `spi.py`, `i2c.py`: each written before its RTL; 20 pytest; RTL suites in `protocols/*/test`. Honest limit: one author wrote both sides, so independence is by order and by the sigrok cross-check, not by different people.)
- [x] Decode simulation waveforms with `sigrok-cli` protocol decoders as an extra independent check. (sigrok `uart`, `spi`, `i2c` decoders in all four suites)

### Profiling
- [x] `tools/profile/`: a script that synthesizes each protocol with Yosys onto generic LUT fabrics (LUT3, LUT4, LUT6; with and without carry) and reports LUTs, flip-flops, and a breakdown by function (counters, shift registers, comparators, control/FSM, other). (`tools/profiling/workload.py`: named `profiling` because a `profile` package shadows Python's standard `profile` module, which cocotb imports; comparators are counted inside the function they serve)
- [x] Report in `docs/reports/profiling.md`: what dominates, which functions recur across protocols, and a ranked list of specialization candidates with the expected saving for each. (2026-09-25)

### Physical de-risking
- [x] Harden a tiny (~16 LUT) FABulous fabric through the TT CMOS5L flow, with live configuration storage (not optimized away), passing precheck. (16-LUT `warp_tiny` macro in `tt_um_warp`, configuration latches loaded from pins through FABulous's bit-bang loader; CI run 36327510268 on dea2150: `gds`, precheck 9/9, `gl_test` green; DRC/LVS/antenna 0, timing met at 50 MHz. `docs/reports/fabric_tiny.md`)
- [x] From it, measure area per logic cell including configuration and routing; build a simple area model in `tools/areamodel/`. (5,090 µm² per LUT4 from the hardened tile, `tile_cmos5l.md`; `tools/areamodel/model.py` + 5 pytest. The fabric-level number comes with the tiny fabric hardening below.)
- [x] Estimate fabric capacity (logic cells) for 6x4 with the shell, leaving routing margin. (4 × 3 tiles: 96 LUT4, or 88 with one primitive tile; `capacity.md`)

### Capacity go/no-go
- [x] Compare the design set's needs (from profiling) with the estimated capacity, with and without the top specialization candidates. (`capacity.md`)
- [x] Decide in DECISIONS: continue with the pure specialized eFPGA, cut showcase scope, or switch to the hybrid fallback. (D-016: GO specialized eFPGA; I2C target/showcase open)

### Specs
- [x] (v1 written 2026-09-26; open items marked for phase 2) `ARCHITECTURE.md` v1: shell, host interface, pin allocation, load/start/stop/parking contract, clocking, fabric resource list for G0, and the candidate architecture variants to compare in phase 3.
- [x] `VERIFICATION.md` v1: layers, check IDs, tools, what runs in which CI workflow. (v1 written 2026-09-26: V0–V7, F1–F4 with bounds)
- [x] `PHYSICAL_DESIGN_AND_CI.md` v1: how the fabric is hardened and integrated, clock target, known limits. (v1 written 2026-09-26; chip-level numbers added from the first fabric `gds` run)
- [x] Risk register updated in `OVERVIEW.md`. (2026-09-26: statuses + 4 new risks)

## Phase exit checklist
- [x] `HELDOUT.md` committed before profiling (commit hash: 0171cf7; no profiling existed before it)
- [x] All four design-set protocols pass their RTL tests against independent reference models (run IDs: `unit` 36211778569 on a858b2a: UART 3 configs, SPI 6, I2C controller 3, I2C target 3, + pytest)
- [x] `docs/reports/profiling.md` complete with a ranked specialization list (timer/counter, shift register, host channel in the shell, I/O cell features, register file)
- [x] Tiny fabric hardened on CMOS5L, precheck passed (CI run ID: 36327510268; three earlier runs failed and are logged: BUGS #9 routing, #10 config, #11 pin check)
- [x] Area-per-cell measurement and capacity estimate recorded (`tile_cmos5l.md`, `capacity.md`)
- [x] Capacity go/no-go decision recorded in DECISIONS (D-016)
- [x] ARCHITECTURE, VERIFICATION and PHYSICAL_DESIGN_AND_CI v1 written (2026-09-26)
- [x] All CI workflows green on `efpga` (dea2150: `gds` + precheck + `gl_test` 36327510268, `test` 36327510213, `lint` 36327510231, `unit` 36327510252, `docs` 36327510245; `fabric` 36274443123, inputs unchanged since. Template `fpga` (manual iCE40 build) is not applicable to a design with a hard macro: D-020)
- [x] `docs/summaries/PHASE1.md` written (2026-09-27, final)
