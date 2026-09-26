<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

WARP is a reprogrammable protocol emulator. It is a small embedded FPGA (eFPGA) fabric, specialized for serial
protocols, behind a fixed management shell. A protocol (UART, SPI, I2C, ...) is written as ordinary synthesizable
Verilog, compiled on a host computer into a bitstream, and loaded into the chip over the host interface. Changing the
protocol changes the bitstream, not the silicon.

**Status: phase 1 spike.** The current design is a 16-LUT FABulous fabric (2 LUT4x8 tiles plus IO tiles) behind a
minimal shell: a bit-bang configuration port (`CFG_CLK`, `CFG_DATA`) feeding FABulous's frame-based configuration
logic, and run control. Fabric outputs and output enables are parked (0) unless `RUN` is high and no configuration
session is running. The full shell (SPI-like host interface, checked loading, host byte channels) and the larger,
specialized fabric come later.

## How to test

1. Hold `RUN` low. Send the bitstream words over `CFG_CLK`/`CFG_DATA` (FABulous bit-bang protocol: each data bit on a
   rising edge of `CFG_CLK`, a control bit on each falling edge; control pattern `0xFAB1` marks a word, `0xFAB0` ends
   the session). `CFG_ACTIVE` is high during the session.
2. Raise `RUN`. The fabric's outputs drive `uo[2..5]` and the `uio` pins as the loaded design says.

Bitstream generation for this fabric is part of the next development phase.

## External hardware

None for the placeholder. For protocols: the peer device under test (e.g. a UART adapter, SPI or I2C device) and a
host that can drive the SPI-like host interface.
