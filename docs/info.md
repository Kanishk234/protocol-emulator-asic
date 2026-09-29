## How it works

WARP's current anish_branch build is an experimental 16-LUT embedded FPGA,
with a checksum-checked loader and output parking. It replaces the template
adder so the actual fabric can be exercised by the Tiny Tapeout chip flow.
It is not yet a validated UART/SPI/I2C emulator or a tapeout-ready design.

The host uses synchronous parallel bytes: ui[7:0] data; uio[4] valid;
uio[5] begin; uio[6] commit; uio[7] abort. uo[0] is byte-ready, uo[1]
running, uo[2] error and uo[3] image-complete. All host signals must meet
clk setup/hold; this is not an asynchronous SPI interface.

## How to test

Assert begin for a clock, then send the image CRC32 as four big-endian bytes
followed by the 504-byte FSB1 image. Each rising clk edge with valid and ready
accepts one byte. After completion without error, assert commit until running.
Fabric pads are uio[3:0]; before release their output enables are zero.
The counter image uses pad0 reset, pad1 enable and pads2/3 counter outputs.

The shared RTL/gate-level test loads the real image through TT pins, checks
counter behavior, rejects incomplete and wrong-checksum loads, and recovers.
A passing RTL simulation does not establish physical timing or silicon operation.

## External hardware

A synchronous host able to drive the byte/control signals and observe ready,
plus a clock source. No manufactured-hardware result is claimed.
