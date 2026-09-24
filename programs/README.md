# programs

TRIPWIRE firmware in the `.trw` language, compiled by `tools/tripc`. The language is documented at the top of `tools/tripc/compiler.py`.

| Program | Role | Slots | Routines | Verified on the model (simulation) |
|---|---|---|---|---|
| `uart.trw` | UART 8N1, TX + RX in one lane, framing errors reported (also MIDI at 31 250 baud) | 4 | — | Reference line model and sigrok, up to 1 Mbaud; 256-byte loopback |
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
| `can.trw` | CAN 2.0A/B: 11/29-bit IDs, remote frames, arbitration, ACK, error flags, TEC/REC, passive, bus-off | 12 + 12 (2 lanes) | 7 | Reference CAN 2.0 node (error frames, retries) and sigrok `can`, 125 k / 500 k / 1 Mbit/s |
| `dmx.trw` | DMX512-A TX (BREAK, MAB, slots) and RX (break detection) | 5 | 1 | Reference decoder/encoder and sigrok `dmx512` |
| `servo.trw` | RC servo / ESC PWM, 20 ms frames | 2 | 1 | Pulse and period measurement, sigrok `pwm` |
| `ir_nec.trw` | IR NEC TX (38 kHz carrier) and RX (demodulated), repeat codes | 2 + 2 (2 lanes) | 2 | Reference NEC encoder/decoder and sigrok `ir_nec` |
| `smbus.trw` | SMBus controller with PEC computed and checked on chip | 12 | 4 | Reference SMBus device with PEC |
| `lin.trw` | LIN 2.x commander with bus monitor: publish/subscribe, both checksums, slot pacing | 4 + 5 (2 lanes) | 4 | Reference LIN responder and sigrok `lin` |
| `i2s.trw` | I2S controller, 16-bit stereo out and in | 7 | — | Reference I2S receiver/ADC and sigrok `i2s` |
| `hdlc.trw` | HDLC/SDLC framing: flags, zero insertion, FCS-16, aborts | 6 | 2 | Reference ISO/IEC 13239 codec |
| `usb_ls.trw` | USB low-speed device, control endpoint 0 (**feasibility study, not a support claim**) | 6 | 2 | Reference USB 2.0 low-speed host and sigrok `usb_packet` |

**Build and run:**
- `cd tools && python -m tripc ../programs/uart.trw -p BAUD=1000000` prints the report (slot/SRAM usage, routine bounds, pre-emption).
- `-o image.json` writes the loadable image.
- In Python, `kernels.load_program(chip, "uart", BAUD=...)` compiles and loads a program into a `tripsim` chip.

**How we know the compiler is right:** `tools/tripc/tests/test_tripc.py` checks that each compiled image is bit-identical to the original hand-assembled kernel (`tools/kernels/*.py`, kept only as a reference), and the protocol tests in `tools/kernels/tests/` run on the compiled programs.
