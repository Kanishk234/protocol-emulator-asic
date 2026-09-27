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

**Status: phase 2 in progress.** The shell is complete: an SPI host interface, a checked bitstream loader
(architecture version, length, CRC-32, sync word) feeding FABulous's frame-based configuration logic, run control,
and host byte channels. Fabric outputs and output enables are parked (0) unless a correctly loaded design is running.
The fabric is still the 16-LUT phase 1 macro (2 LUT4x8 tiles plus IO tiles), connected to `FAB_IN0..3`,
`FAB_OUT0..3` and all 8 `uio` pins; the larger fabric comes next.

## How to test

The host is an SPI controller (mode 0, MSB first, SCK at most clk/8) on `HOST_CS_N`, `HOST_SCK`, `HOST_MOSI`,
`HOST_MISO`. Each transaction starts with an opcode byte, during which the chip returns its STATUS byte
(state in bits 7..5: 0 unconfigured, 1 loading, 2 loaded, 3 running, 4 error).

1. `0x01` READ_ID: the chip answers `0x57 0x50` ("WP") and the architecture version (2 bytes).
2. Load: `0x10` LOAD_BEGIN (version, length in words), `0x11` LOAD_DATA (bitstream words, big-endian), `0x12`
   LOAD_END (CRC-32 of the words). STATUS shows 2 (loaded), or 4 (error; `0x02` READ_STATUS gives the error code).
3. `0x20` RUN: the loaded design drives `uo[2..7]` and the `uio` pins. `0x21` STOP parks them again.

The Python host library (`tools/host/protocol.py` in the repository) builds every transaction.

## External hardware

A host that can drive SPI (a microcontroller or USB-SPI adapter), and the peer device for the loaded protocol
(e.g. a UART adapter, SPI or I2C device).
