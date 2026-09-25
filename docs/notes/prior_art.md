# Prior art and our actual differentiator

Reviewed 2026-09-25. Author-reported capabilities below have not been
independently reproduced in this branch.

## PRISM

[PRISM's official Tiny Tapeout documentation](https://tinytapeout.com/chips/ttihp26b/tt_um_pettit_prism_lite)
describes a Verilog-compiled, table-driven Mealy state machine beside a
TinyQV host CPU. Its 32 states use 128-bit state words; it can split into
two 16-state machines. Configurable counters, shifters, FIFOs and CRC
hardware supply the datapath. The documentation distinguishes several
physical variants, including different FIFO implementations.

This is a strong comparison for WARP: Verilog programming and hardware
protocol reactions already exist. PRISM spatially fixes its datapath and
time-multiplexes state descriptions; a LUT fabric can express arbitrary
combinational structure and concurrent machines within its resource and
timing limits, but pays for distributed configuration and programmable
routing. Neither choice wins on programmability alone. Do not import
PRISM's protocol list or larger-build capabilities as WARP requirements.

## Other relevant references

* [Tiny FABulous integration review](tiny_fabulous.md): an eFPGA on Tiny
  Tapeout is established prior art. Our process, area and management shell
  still need their own proof.
* [FABulous 2.2.0](https://github.com/FPGA-Research/FABulous/tree/v2.2.0):
  generator, mapper/route interface and bitstream support. Reuse the tool
  foundation; make specialization a measured experiment.
* [RP2040 datasheet, PIO chapter](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf):
  compact instruction-driven I/O is the temporal baseline named by the
  competition. A fabric replaces instruction scheduling with spatial
  resources, but does not eliminate I/O synchronization or buffering.

## What is worth demonstrating

Our proposed contribution is **a measured protocol-oriented fabric with
reproducible source-to-pin verification**, including resource cost to
workloads that do not use each custom primitive. An appealing showcase is
concurrent protocol emulation plus programmable capture/trigger behavior
in the same bitstream, subject to the design-set benchmark and pin budget.
This is a project objective, not a novelty or performance claim.

The evidence must span source RTL, generated bitstream, real loading,
configured fabric behavior and the hardened implementation. A compiler
that emits an attractive resource count is only one part of that chain.
