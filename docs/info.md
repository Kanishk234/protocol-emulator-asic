<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

WARP is a reprogrammable protocol emulator: a small FPGA fabric, specialized for serial protocols, behind a fixed
management shell. A protocol (UART, SPI, I2C, 1-Wire, WS2812, SWD, ...) is written as ordinary synthesizable
Verilog, compiled on a computer into a bitstream, and loaded into the chip over its host SPI port. Changing the
protocol changes the bitstream, not the silicon.

- **Fabric:** 88 LUT4 + flip-flop logic cells (FABulous, 4 x 3 tiles) and one tile of hard primitives: 2 loadable
  16-bit timers and 2 8-bit shift registers with a bit count, which user designs instantiate by name. One clock
  (the project clock).
- **Shell:** an SPI host interface, a checked loader (architecture version, length, CRC-32, sync word), run control,
  and a byte channel each way between the host and the running design. Every fabric pin is parked (outputs 0,
  bidirectional pins released) and the design is held in reset unless a correctly loaded design is running.
- **Software:** a compile flow (Verilog + pin map to bitstream), a loader for the Tiny Tapeout demo board
  (MicroPython), and example designs for UART, SPI and I2C. See the repository's `docs/USER_GUIDE.md` and
  `docs/EXAMPLES.md`.

All results so far are from simulation (RTL and the gate-level netlist); nothing has been measured on silicon.

## How to test

The host is an SPI controller (mode 0, MSB first, SCK at most clk/8) on `HOST_CS_N`, `HOST_SCK`, `HOST_MOSI`,
`HOST_MISO`. Each transaction starts with an opcode byte, during which the chip returns its STATUS byte
(state in bits 7..5: 0 unconfigured, 1 loading, 2 loaded, 3 running, 4 error). `HOST_IRQ` is high when the host
should read.

1. `0x01` READ_ID: the chip answers `0x57 0x50` ("WP") and the architecture version (`0x0003`).
2. Load a bitstream: `0x10` LOAD_BEGIN (version, length in words), `0x11` LOAD_DATA (words, big-endian), `0x12`
   LOAD_END (CRC-32 of the words). STATUS shows 2 (loaded), or 4 (error; `0x02` READ_STATUS gives the error code).
3. `0x20` RUN: the design drives `FAB_OUT0..5` and the `uio` pins; `0x21` STOP parks them again.
4. Talk to the design: `0x30` CH_WRITE (flags, byte), `0x31` CH_READ, `0x32` USER_STATUS.

From the demo board: copy `tools/board/warp.py` and a `.wbit` file to the RP2040, then
`w = warp.on_demo_board(); w.load_file("uart.wbit"); w.run()`.

## External hardware

The demo board (or any SPI host), and the device for the loaded protocol: a UART adapter, an SPI or I2C device,
WS2812 LEDs, a 1-Wire sensor, an Arm target's SWD port. Open-drain protocols (I2C, 1-Wire) need pull-up resistors
on their `uio` pins.
