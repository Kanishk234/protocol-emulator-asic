# Phase 2 summary: baseline fabric and shell

**Status:** complete (2026-09-28). Every exit item passed; all CI workflows green on `efpga` at 2befd16 (gds + precheck + `gl_test` 21/21: 36376994834). One hardware bug found at the very end is logged for the next hardening (BUGS #18: reset release not synchronized).

## Goal
Build the real chip around a real fabric: the shell (SPI host interface, checked configuration loading, run control, host byte channels), a full-size fabric with and without the planned primitives (G0, G1), a compile flow from user Verilog to our bitstream, and tests that load real bitstreams into the hardened chip. Then answer the phase's decision question: is shell + G1 a valid fallback submission?

## What we did
- **Shell** (ARCHITECTURE §2–6): SPI host interface, loader with sync/length/CRC-32/architecture-version checks, run control with pins parked unless running, 2-entry host channel FIFOs, and host software written from the spec.
- **Proved the safety-critical parts** (`docs/reports/formal.md`): outputs isolated while not running (F1, unbounded), bad loads never run (F2, 84 cycles, found BUGS #12), primitives equal their spec (F4, unbounded).
- **Compile flow** (`tools/compile`): pin map → wrapper → Yosys → nextpnr → our own bitstream generator (FABulous's drops the clock-mux bits, BUGS #13) → a bitstream file with a report.
- **G0** (96 LUT4s, 4 × 3 tiles) hardened into the 6x4 chip; getting it to route took a placement study (D-025).
- **G1**: two general hard primitives, a 16-bit timer and an 8-bit shift register with a bit count (D-026, no protocol logic in hardware), in one tile slot at 0.97 × a LUT tile's area; users instantiate them by name, and they are mapped, placed, configured and timed.
- **G1 into the chip** (D-027), hardened: precheck pass, `gl_test` 19/19, including designs that use both primitives and the UART, loaded through the host interface (CI 36367067731).
- **Protocols rewritten to use the primitives** (a `PRIMS` switch keeps the plain form), with SPI and I2C controller tests at chip level against independent reference models.

## What we found
- **The primitives are the difference between a toy and a protocol chip.** In the same area, G0 runs one of the four design-set protocols (SPI) and G1 runs three: UART 29, SPI 47, I2C controller 70 of 88 logic cells (`docs/reports/g1_results.md`). The I2C target (123–169 cells) fits neither; its size is the design itself, not the tools.
- **Logic-cell count is not capacity.** Each 8-cell tile has one clock enable and one reset; designs failed placement with cells to spare until the compile flow turned rarely shared enables into logic (BUGS #15), which also shrank every design.
- **Timing needed its own fix.** nextpnr silently left every path through the primitives untimed (BUGS #17); with arcs from STA of the primitives, checked against STA of the hardened tile (D-028), the estimates dropped (UART 122 → 91, SPI 89 → 78, I2C controller 69 → 53 MHz) but all stay above the 50 MHz clock, the I2C controller only just. These are model estimates, not claims.
- **Simulation of an FPGA fabric has traps silicon does not:** unused routing forms loops that stay X or never settle in a zero-delay simulator, so chip tests run the gate-level shell with the fabric's RTL and settle the routing explicitly (D-023).

## What's left
- BUGS #18 (reset synchronizer): the next hardening's one change.
- Phase 3: specialize and compare variants at equal area (D-004), including whatever lets the I2C target fit (a register-file tile, a larger fabric), and freeze the hardware.

## One-line takeaway
A FABulous fabric with two generic hard primitives now sits inside a Tiny Tapeout chip that passes every check, and it runs UART, SPI and I2C where the same area of plain LUTs runs only SPI.
