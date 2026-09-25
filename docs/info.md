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

The shell owns the host interface (an SPI-like port on `ui[0..2]`/`uo[0]`), loads and checks the bitstream, and
starts and stops the fabric. While the fabric is stopped or unconfigured, all fabric outputs are parked and every
bidirectional pin is an input. The remaining pins belong to the loaded protocol.

**Status:** design in progress. The current silicon is a placeholder (`uo_out = ui_in + uio_in`); the pinout above
is provisional until the architecture spec is written.

## How to test

Placeholder design: drive `ui_in` and `uio_in`; `uo_out` shows their 8-bit sum.

The final design will be tested by loading a protocol bitstream over the host interface with the host software in
`tools/host/`, starting the fabric, and exercising the protocol pins with a peer device or logic analyzer.

## External hardware

None for the placeholder. For protocols: the peer device under test (e.g. a UART adapter, SPI or I2C device) and a
host that can drive the SPI-like host interface.
