# Prior art

Read 2026-09-28. Descriptions are from the projects' own pages; nothing here was re-measured by us.

## PRISM lite (Ken Pettit, TTIHP26b, IHP)
Source: https://tinytapeout.com/chips/ttihp26b/tt_um_pettit_prism_lite · repo `kdp1965/ihp26b-um-pettit-prism-lite`.

- **What:** "Programmable Reconfigurable Indexed State Machine": a protocol engine whose states, transitions, inputs and outputs are loaded at run time as a bitstream compiled from **an ordinary Verilog Mealy state machine** ("chroma") by a Yosys backend (`yosys-prism`). Paired with TinyQV (RISC-V) for the higher layers.
- **Programmable part:** 32 states (or 2 × 16-state shards), each a 128-bit State Execution Word: 6 input muxes over 32 inputs, two LUT3s forming if / else-if / else, two LUT2s for conditional outputs, and 21 outputs per shard. The published page describes one state transition per clock.
- **Fixed datapath per shard:** 24/32-bit counter (doubles as a wide shift register), 8-bit counter with compare, 8-bit communication shifter (1–4 bits per shift), constants, a 64-byte FIFO in the smaller build (2 KB SRAM FIFO per shard in the larger build), CRC 8/16/32 (doubles as a counter), Manchester recovery, edge-clocked sampling, four edge-capture flops, timer, interrupt, debugger and optional trace storage.
- **Loading:** the CPU writes the state table through shift chains (CFGMEM peripheral).
- **Shown protocols:** UART, SPI (target; single/quad controller), I2C (controller and target), 1-Wire, WS2812, quadrature encoder, GPIO expander, USB low-speed device; 10BASE-T TX/RX in the 8x4 build with SRAM FIFOs.

**What it means for WARP**
- PRISM already has "users write Verilog, a Yosys backend compiles it to a bitstream, on IHP". We **cannot** claim that as new.
- Its fixed datapath is close to our list of hard-block candidates (counter/timer, shift register, CRC, edge detection, FIFO). That supports the choice (a shipped design converged on it), but any overlap must be cited, and our claim has to rest on how the blocks were **chosen and measured**, not on having them.
- Where we differ, and must show with evidence:
  1. **Execution model:** PRISM advances one state per clock and decides through two LUT3s per state. A LUT fabric evaluates all its logic in parallel every clock (several independent state machines, wide combinational checks) at the cost of density.
  2. **Method:** profiling-driven primitive choice, equal-area comparison against a generic fabric (D-004), and a sealed held-out set (D-003). PRISM publishes no such comparison.
  3. **No CPU.**
- **Risk:** on protocol coverage per area, PRISM is a strong baseline. Our early capacity estimate (`docs/reports/capacity_early.md`: ~60–90 generic LUT4s at 6x4) means a generic fabric would lose badly. A specialized fabric has to close that gap, and we should say honestly how far it gets. A useful phase 3 comparison: our design set on WARP versus PRISM's published list, clearly labelled as a comparison with published claims, not our measurement.
- **Architecture consequence:** two independently running sequencers, shared/configurable state tables, FIFOs, capture, CRC, programmable pins, and Verilog-to-state-table compilation are already present in PRISM's published design. Similar event lanes are also proposed or reported by competition entries. WARP must not present shared instruction memory or lane count as its differentiator. A hybrid candidate earns attention only if it shows arbitrary user LUT logic transforming/monitoring traffic concurrently with timed pin engines, and if the whole composition fits at equal area. Otherwise prioritize improvements to the spatial fabric itself.

## Tiny FABulous (Leo Moser, TT SKY26a)
See `tiny_fabulous.md`. A generic 128-LUT4 FABulous fabric with TT-style pins, no hard blocks and no protocol focus. WARP differs by specializing for protocols and by the shell (checksummed loading, output parking).

## RP2040 PIO / TI PRU (named in the competition brief)
- **PIO:** 4 state machines per block, 9-instruction ISA, 32-instruction shared memory, shift registers, FIFOs, side-set; bit-banging at up to one instruction per clock.
- **PRU:** 32-bit RISC cores with single-cycle I/O and deterministic timing, programmed in C/assembly.
- Both are instruction-driven (sequential). WARP is spatial (logic evaluated in parallel) and programmed in RTL.

## Not yet checked
FABulous IHP tapeouts (the FABulous group's own chips); other TT FPGA entries. Check before any "first" or "novel" wording (CLAUDE.md).
