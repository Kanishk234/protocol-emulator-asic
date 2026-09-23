# programs

TRIPWIRE firmware in the `.trw` language, compiled by `tools/tripc`. The language is documented at the top of `tools/tripc/compiler.py`.

| Program | Role | Slots | Routines | Verified on the model (simulation) |
|---|---|---|---|---|
| `uart.trw` | UART 8N1, TX + RX in one lane, framing errors reported | 4 | — | Reference line model and sigrok, up to 1 Mbaud; 256-byte loopback |
| `spi_controller.trw` | SPI controller, mode 0 | 4 | — | Reference target and sigrok, up to 12.5 MHz |
| `spi_target.trw` | SPI target, mode 0 | 3 | — | Reference controller and sigrok, up to 12.5 MHz |
| `i2c_controller.trw` | I2C controller: START/rSTART/STOP, read/write, stretching | 11 | 2 | Reference target and sigrok, 100 kHz / 400 kHz / 1 MHz |
| `i2c_target.trw` | I2C target: address match, read/write | 12 | — | Reference controller and sigrok, 100 kHz / 400 kHz / 1 MHz |
| `ws2812.trw` | WS2812/SK6812 LED strips (PULSE mode) | 2 | — | Datasheet-tolerance reference decoder and sigrok `rgb_led_ws281x` |
| `dshot.trw` | DShot150–1200 motor ESCs; checksum computed in a routine | 2 | 1 | Reference decoder (frames, checksums, bit timing) |
| `ps2_host.trw` | PS/2 host: both directions, parity/framing errors, device ACK check | 12 | 1 | Reference device (Chapweske) and sigrok `ps2` |
| `onewire.trw` | 1-Wire controller: reset/presence, byte write/read (AN126 standard speed) | 9 | 1 | DS18B20-like device (READ ROM + CRC-8) and sigrok `onewire_link`/`onewire_network` |
| `swd.trw` | SWD controller: DP/AP reads and writes, WAIT handling, turnarounds | 12 | 3 | ADIv5 target model and sigrok `swd`, SWCLK up to 8.3 MHz |
| `jtag.trw` | JTAG scan engine: TMS/TDI chunks in, TDO chunks out | 8 | — | IEEE 1149.1 TAP model (IDCODE, USER, BYPASS) and sigrok `jtag`, TCK up to 12.5 MHz |

**Build and run:**
- `cd tools && python -m tripc ../programs/uart.trw -p BAUD=1000000` prints the report (slot/SRAM usage, routine bounds, pre-emption).
- `-o image.json` writes the loadable image.
- In Python, `kernels.load_program(chip, "uart", BAUD=...)` compiles and loads a program into a `tripsim` chip.

**How we know the compiler is right:** `tools/tripc/tests/test_tripc.py` checks that each compiled image is bit-identical to the original hand-assembled kernel (`tools/kernels/*.py`, kept only as a reference), and the protocol tests in `tools/kernels/tests/` run on the compiled programs.
