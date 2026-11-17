## How it works

TRIPWIRE is a firmware-programmable protocol emulator for the Jane Street Protocol Emulator ASIC Competition. Two lanes of triggered reflex instructions exchange tokens through a multicast channel fabric. Four timed pin units drive and sample the protocol pads; U0 also provides PULSE, carrier and BITSYNC features. A 512x16 SRAM holds routines and data. Programs and configuration are loaded over the host SPI port.

The integrated design targets 50 MHz on 8x4 IHP CMOS5L tiles. UART, SPI and I2C are exercised with firmware and reference models. The candidate also has a passing 22-case routed protocol replay; this describes tested cases, not complete implementation of every protocol variant. No fabricated-chip measurements are available. Official full-design GDS/precheck qualification is still pending.

## How to test

1. Assert synchronous active-low `rst_n` for several clock cycles, then release it with the host inactive (`ui[4]` high).
2. Connect the host: `ui[4]` is CS_n, `ui[5]` SCK, `ui[6]` MOSI and `uo[3]` MISO. `uo[6]` is IRQ. The other 19 pads are assigned by firmware through owner registers.
3. Use `tools/tripc.py` and `tools/host.py` to compile and load a program from `programs/`, initialize its pin configuration and start its lanes. Reload after power loss or deselection.
4. `test/` exercises UART TX, SPI controller and I2C controller through the Tiny Tapeout ports. Run it from the project virtual environment; see `test/README.md`. The wider suite is in `test_internal/chip/test_l3.py`.

See `docs/design/ARCHITECTURE.md` for the register map, host framing, timing and reset contract, and `docs/CLAIMS.md` for evidence and limitations.

## External hardware

A digital host is required to load programs, normally the demo-board microcontroller. Protocol connections depend on the program. Open-drain buses such as I2C require external pull-ups. Use appropriate external transceivers or level shifting for the attached device and board; the chip supplies digital I/O only.


## Physical verification policy

The SRAM uses the supported CMOS5L KLayout deck on the complete merged GDS,
with zero KLayout DRC violations required. D-185 documents the unsupported Magic
SRAM DRC and abstract-overlap checks being waived; this does not claim zero raw
Magic markers. LVS, timing, electrical, antenna and routing checks remain required.
