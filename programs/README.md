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

**Build and run:**
- `cd tools && python -m tripc ../programs/uart.trw -p BAUD=1000000` prints the report (slot/SRAM usage, routine bounds, pre-emption).
- `-o image.json` writes the loadable image.
- In Python, `kernels.load_program(chip, "uart", BAUD=...)` compiles and loads a program into a `tripsim` chip.

**How we know the compiler is right:** `tools/tripc/tests/test_tripc.py` checks that each compiled image is bit-identical to the original hand-assembled kernel (`tools/kernels/*.py`, kept only as a reference), and the protocol tests in `tools/kernels/tests/` run on the compiled programs.
