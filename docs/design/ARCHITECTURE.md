# Architecture (hardware contract)

Status: stub. Version 1 is written in phase 1. RTL, fabric definition and models all follow this document; changes go through DECISIONS.

## Experimental integration contract (ANISH-D11)

The current `anish_branch` TT build is a 16-LUT reference-derived prototype,
not the final protocol architecture. The user authorized replacing the adder
to test the actual chip flow while the phase gates remain open.

All host signals are synchronous to `clk`; there is no asynchronous/SPI CDC.
Drive bytes on ui[7:0], valid on uio[4], begin on uio[5], commit on uio[6],
abort on uio[7]. Ready is uo[0]; each rising edge with valid and ready
accepts one byte. Begin/abort are active-high levels sampled by clk.
After begin, send four CRC32/ISO-HDLC bytes MSB first, then the complete
504-byte image (also MSB first within each word). Wait for image-complete
uo[3], no error uo[2], then commit until running uo[1] becomes high.
Commit with a partial word or unvalidated image cannot release the pads.

Low four uio pins are fabric I/O. Output enables are active-high and zero
until running; begin/abort/reset/deselect park all pads. The demonstration
ABI reserves fabric input0 for active-high synchronous reset and input1
for enable. Reset is asserted during release. This is not yet a general
user-design ABI. The remaining uo bits and high uio output/enables are zero.

Configuration is dynamic; the counter test vector is not wired into silicon.
Malformed uploads require a new begin or abort. Physical timing, safe arbitrary
bitstreams, asynchronous inputs and protocol workload capacity are unproven.

## 1. Top level and pin allocation
## 2. Host interface (commands, framing, status)
## 3. Configuration loading (length, checksum, architecture version, error handling)
## 4. Run control and output parking
## 5. Clocking and reset
## 6. I/O cells (synchronizers, output registers, open-drain)
## 7. Fabric resources (current variant)
## 8. Hard primitives (interface, cycle-by-cycle behavior, corner cases)
## 9. Architecture variants under evaluation
## 10. Supported user Verilog subset
