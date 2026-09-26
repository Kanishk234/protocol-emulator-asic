# Protocol user designs (soft logic, not silicon)

Everything in this folder is a **user design**: ordinary Verilog that a user compiles on a host computer into a bitstream and loads into WARP's fabric. None of it is hardware on the chip. Changing protocols means loading a different bitstream.

The chip itself contains only generic resources: LUT4 logic tiles, a small set of **protocol-agnostic primitives** (candidates: loadable counter/timer, shift register, CRC/LFSR, edge detector, FIFO), I/O cells, and the management shell. There is no UART, SPI or I2C block in silicon (DECISIONS D-002). A primitive is added only if profiling shows it helps more than one protocol, with its area cost and its cost to protocols that don't use it recorded in DECISIONS.

These designs serve two purposes:
1. **Workload for the architecture.** The design set (UART, SPI controller, I2C controller, I2C target) is profiled to find what logic recurs across protocols (so far: bit-timing counters and shift registers). That measurement, not the protocol names, decides which generic primitives go into the fabric.
2. **Demonstration.** They show the chip running real protocols from bitstreams. The sealed held-out set (`docs/design/HELDOUT.md`) then tests whether the chosen primitives serve protocols they were not tuned for.

"Controller" and "target" are the protocol roles (the side that drives the clock vs. the side that answers), not hardware blocks.

Each protocol folder has the RTL, a README (scope, rates, known limits) and `test/` (cocotb tests against an independent reference model in `tools/refmodels/`, plus sigrok where it has a decoder).
