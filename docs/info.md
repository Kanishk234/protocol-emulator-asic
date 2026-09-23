<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

TRIPWIRE is a firmware-programmable protocol emulator (UART, SPI, I2C and more) being built for the Jane Street Protocol Emulator ASIC Competition. It will use lanes of triggered "reflex" instructions, bounded routines in SRAM, a multicast channel fabric and timed pin units.

**Current state (setup phase):** the design is a placeholder 8-bit counter used to bring up the build and test flow. The counter is shown on `uo[7:0]` and advances by one on every clock while `ui[0]` is high. Reset (`rst_n` low) clears it to 0.

## How to test

1. Hold `rst_n` low for a few clocks, then release it. `uo[7:0]` reads 0.
2. Drive `ui[0]` high: `uo[7:0]` counts up once per clock and wraps from 255 to 0.
3. Drive `ui[0]` low: the count holds its value.

## External hardware

None.
