# WARP: evidence report

For a reader with 20 minutes. Every number has a source: a CI run ID (GitHub Actions on `efpga`), a report in `docs/reports/`, or a named local script. Claims and their status: `docs/CLAIMS.md`. **Nothing here is measured on silicon or a board; all results are simulation, formal proof, or physical-design reports.**

Key CI runs: [frozen-chip GDS, precheck and gate-level tests (36383587262)](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36383587262), [Phase 4 GDS and gate-level tests (36451108163)](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36451108163), [Phase 4 fabric tests and co-simulation (36451328356)](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36451328356), [protocol tests (36451328364)](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36451328364), [formal F1/F2/F4 (36383587298)](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36383587298).

## 1. The problem and the constraint

The competition asks for a chip that can be reprogrammed after fabrication to speak hardware protocols (UART, SPI, I2C to start), on Tiny Tapeout (IHP 130 nm CMOS5L). Most entries are expected to be small CPUs. WARP instead puts a small **FPGA fabric** on the chip, and chooses what that fabric contains from measurements.

The hard constraint is area. On CMOS5L one FABulous LUT4 costs about **5,090 µm²** once its configuration latches, switch matrix and routing are counted (C2, `docs/reports/tile_cmos5l.md`), so a 6x4 Tiny Tapeout project holds roughly **96 LUT4s** next to the management shell.

## 2. What protocol logic is spent on

We wrote the four design-set protocols (UART, SPI controller, I2C controller, I2C target) as ordinary Verilog and attributed every LUT to what it does (`docs/reports/profiling.md`, synthesis, phase 1): **648 LUT4s** in total, of which **counters 23 %, shift registers 17 %, storage 21 %** (mostly the I2C target's register map). A plain UART alone needs 144 LUT4s, more than the chip holds.

Before profiling we sealed a **held-out set** of four more protocols (WS2812, 1-Wire, SWD, CAN; commit 0171cf7) that no part of the architecture was allowed to see until the hardware was frozen (D-003).

## 3. The architecture, chosen at equal area

The generic hard blocks selected from profiling are a **loadable 16-bit timer** and an **8-bit shift register with a bit count** (D-002, D-026). The three supported design-set protocols use both; the I2C target uses the shift register but does not fit the chip. Two of each fit in one fabric tile slot at **0.97 × a LUT tile's area** (D-026). The chip's fabric **G1** is a 4 × 3 grid with one slot holding them: **88 LUT4 + 2 timers + 2 shift registers**; the baseline **G0** has the same macro with all 12 slots LUT tiles (96 LUT4).

| Fabric (same macro, same area) | Design-set protocols that place and route | Logic cells: UART / SPI / I2C controller / I2C target |
|---|---|---|
| G0: 96 LUT4 | 1 of 4 | 124 / 86 / 115 / 184 |
| **G1: 88 LUT4 + hard blocks** | **3 of 4** | **29 / 47 / 70** / 169 |

Sources: `docs/reports/architecture_comparison.md` (chart `architecture_comparison.svg`), `g1_results.md`, `g0_results.md`; G1 fits checked in CI `fabric` (`compile.protocols --require`, e.g. 36376994866).

Phase 3 then tried three more specializations, each measured and dropped (D-030, D-031, D-034): a faster timer output (no gain for the slowest design), buffering inside the primitive tile (does not fit the tile), a register-file tile (the I2C target would still need 110–123 of 80 cells). Control sets and the number of hard blocks were measured not to be limits (`docs/reports/g1_limits.md`). **G1 is the frozen chip** (`hw-freeze` → 3047dea, D-033); the I2C target does not fit and is not supported (D-035).

## 4. The chip

| | Result | Source |
|---|---|---|
| Tiny Tapeout flow | `gds`, precheck pass; routing DRC 0, LVS 0, antenna 0, Magic DRC 0 | CI 36383587262 (3047dea) |
| Timing at 50 MHz | setup WS +12.48 ns (slow corner), hold WS +0.112 ns (fast) | same run |
| Shell | 3,723 standard cells, 60,567 µm² | same run |
| Fabric macro | 1016.64 × 669.06 µm, 88 LUT4 + 2 + 2 hard blocks | `macro/warp_g1`, D-027 |
| Formal | F1 output isolation (unbounded), F2 loader (BMC depth 84), F4 primitives = specification (unbounded) | CI `formal` 36367067725; `docs/reports/formal.md` |

Hardening history and every intermediate run: `docs/design/PHYSICAL_DESIGN_AND_CI.md`.

## 5. Reprogrammable after fabrication, shown on the hardened netlist

Real bitstreams, compiled from Verilog by `tools/compile`, are loaded through the chip's SPI host port (checked: architecture version, length, CRC-32) into the **gate-level chip netlist** and run: a counter, combinational logic, the host byte channel, both hard primitives, and the UART, SPI controller and I2C controller against independent reference devices. CI `gl_test` 36383587262: **21/21** (the fabric is modelled from its RTL, D-023). A loaded design can be replaced by another without a reset; a corrupt load leaves every pin parked and the chip refusing to run until a good load (`test_corrupt_load_over_running_design`).

**Showcase (D-036):** one simulated chip, never reset, loads **six protocols in turn** (UART, SPI, I2C, WS2812, 1-Wire, SWD) and each works against its reference device (`test_showcase_protocol_switching`; CI `gl_test` 36451108163 and `fabric` 36451328356).

## 6. Generality: the held-out protocols

Opened only after `hw-freeze`; each with a reference model written first from its own specification (`docs/reports/heldout_results.md`):

| Held-out protocol | Frozen chip (88 cells) | Plain G0 (96) | Result |
|---|---|---|---|
| WS2812 | **runs**, 32 cells | 82 | 8 LEDs through the host interface, within the datasheet's timing |
| 1-Wire | **runs**, 77 cells | 126: does not fit | reset/presence, READ ROM with CRC |
| SWD | **runs**, 44 cells | 61 | connect, DPIDR, AP write/read, WAIT; packets in host software |
| CAN 2.0A | does not fit (207) | 241 | correct in RTL only |

Every held-out design used the hard blocks, in ways the design set did not (a pulse-width generator, a 480 µs one-shot, an SWD bit clock, a CAN sample point). Chip-level tests pass in CI `gl_test` 36451108163 and `fabric` 36451328356.

## 7. The software side (D-032)

The organizers asked for the flow from a protocol description to a bitstream, how it is loaded, and working examples (`docs/USER_GUIDE.md`, `docs/EXAMPLES.md`): the compile flow (`tools/compile`: Verilog + pin map → checked bitstream + report), a demo-board loader and protocol helpers (`tools/board`, MicroPython), and UART/SPI/I2C examples. **The board code itself is tested against the chip model** (`test_board_loader`, `test_board_examples_spi`, `test_board_examples_i2c`); it has not run on a board.

## 8. Verification

| Layer | What | Evidence |
|---|---|---|
| Protocol designs | RTL tests against independent reference models (and sigrok), both forms (hard blocks / plain logic), 8 designs | CI `unit` 36451328364 |
| Chip, RTL fabric | chip-level tests loading real bitstreams through the pins | CI `fabric` 36451328356 |
| Chip, gate level | the same tests on the hardened shell netlist with fabric RTL | CI `gl_test` 36451108163 |
| Formal | F1, F2, F4 in CI; F3 FIFO locally at depths 2 and 4 | CI `formal` 36383587298; local `scripts/formal.sh f3_fifo.sby`, 2026-09-28 |
| Shell random transactions | SPI transactions checked against an independent model, with command × state and error coverage | `test_internal/uvm`, local seed 1: 2,288 transactions, 79/79 coverage bins, 0 mismatches (2026-09-28) |
| Co-simulation | the UART as a bitstream vs its source RTL: identical TX waveforms, equal RX | `test_internal/cosim`; CI `fabric` 36451328356 |
| Mutation | 11 planted bugs, all caught | `docs/reports/mutation.md` (local), `scripts/mutation.py` |
| Timing model | primitive timing arcs checked against STA of the hardened primitive tile | `tools/timing/README.md`, D-028 |

Bugs and investigations, with the checks and limits recorded for each: `docs/BUGS.md`.

## 9. Known limits

- **No hardware results**: no silicon, no board; rates are model estimates (Fmax 53–91 MHz for the supported designs, `tools/timing/README.md`), not measurements.
- **Capacity**: 88 cells; the I2C target and CAN do not fit. One bitstream runs at a time, but it can contain concurrent functions: a local UART-plus-event-monitor demonstration fits at 37/88 cells and passes loaded RTL and synthesized gate-shell tests (`docs/reports/g1_uart_monitor.md`, C11); it has no new hardened-netlist/CI result.
- **Fault-control showcase**: the UART/monitor plus externally timed TX line inversion fits at38/88 cells and passes two-case loaded RTL and synthesized-shell suites (`docs/reports/g1_uart_fault_monitor.md`, C12). This controls selected corruption and preserves monitoring; it is not an autonomous fault scheduler or a silicon result.
- **Soft capture**: UART plus a two-entry six-bit timestamp queue fits at83/88cells and passes loaded ordering/overflow/wrap/backpressure/TX/RX/reset tests (`docs/reports/g1_uart_capture.md`, C13). Default timestamps wrap at64clocks; an85-cell option trades four-clock resolution for256-clock wrap, with loaded quantization/wrap checks. The eight-bit stored timestamp version exceeds capacity at91cells. No new hardware or native gate timing evidence.
- **Host link**: one byte per SPI transaction; a protocol needing a byte every few µs (WS2812) needs a fast host.
- **Parked outputs are 0**: active-low signals on `uo_out` pins are asserted while stopped (BUGS #19); use a bidirectional pin with a pull-up.
- **Gate-level fabric**: chip tests simulate the fabric from its RTL, not its hardened netlist (D-023); per-tile netlist-vs-RTL equivalence is not done.
- **Prior art**: FPGA fabrics on Tiny Tapeout exist (Tiny FABulous, SKY130), as does a Verilog-programmed protocol engine on IHP (PRISM); what WARP adds is the measured, held-out-tested choice of architecture (`docs/notes/prior_art.md`).
