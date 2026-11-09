# Current candidate protocol evidence, November 9

Evidence: [cloud run 42690695832](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42690695832),
source `e248408`. Downloaded XML contains the 22 cases below, all passing with
no failures, errors or skips. These are actual compiled-firmware loads through
the simulated SPI host into the prepared two-lane, four-pin-unit core. The
candidate has 12 reflex slots per lane, one full pin unit and 512-word SRAM.
Four separate tests also exercise its actual Tiny Tapeout top. Source identity,
hashes and limits are in [the closure report](CLOSURE_BRANCH_20261109.md).

The cases run separately; this table does not demonstrate simultaneous
protocol operation. They are RTL simulations against reference devices/codecs
and sigrok where supplied by the test, with idealized protocol wires. They do
not establish physical clock/rate closure, SDF behavior, exhaustive protocol
conformance or silicon operation. Tests and precise parameters:
[`test_l3.py`](../../test_internal/chip/test_l3.py).

| Case suffix after `test_l3_` | Exercised behavior |
|---|---|
| `uart_tx` | Host bytes transmitted as UART frames |
| `uart_rx_framing` | Receive bytes and report an injected framing error |
| `midi_tx` | UART-based note, control and program messages |
| `dmx_tx` | Framed packets with BREAK/MAB and slot data |
| `ws2812_tx` | Two packed GRB frames and pulse-timing decoder checks |
| `dshot_tx` | Lane-computed checksum packets at the four tested settings |
| `servo_pwm` | Frame timing and host-controlled pulse-width update |
| `i2s` | Full-duplex stereo samples against independent transmitter/receiver models |
| `spi_controller` | Mode 0 multi-byte transfer against a responding target |
| `i2c_controller` | Write/read, repeated START, NACK and clock stretching |
| `spi_target` | Mode 0 response and received-data/CS reporting |
| `i2c_target` | Writes, address rejection and readback with host-drain spacing |
| `ps2_device_to_host` | Device frames with an injected bad parity bit |
| `ps2_host_to_device` | Request-to-send, parity, stop and device ACK |
| `onewire_read_rom` | Reset/presence, READ ROM and CRC-8 |
| `jtag_idcode` | TAP navigation and 32-bit IDCODE read |
| `smbus_word_pec` | Word write/read with independent PEC checking |
| `swd_dpidr_read_with_wait_retry` | WAIT/retry, DPIDR/parity and turnaround contention checks |
| `hdlc_tx_loopback` | Flags, stuffing, FCS and receive loopback |
| `lin_commander_publish_response` | Protected-ID header and enhanced-checksum response |
| `can_standard_frame_and_ack` | Standard data-frame transmit, ACK and CRC-valid self-monitoring |
| `ir_nec_repeat_rx` | Repeat leader/space detection; not a full NEC message test |

The CAN row is a narrow standard-frame scenario, rather than evidence for every
CAN feature in the older model roadmap. SPI modes 1-3, USB, arbitrary concurrent
combinations and sustained high-rate streams are not established by this run.
I2C target transactions deliberately allow the host to drain responses; the
existing host-throughput limit still applies.

The next physical gates remain the exact 8x4 screen, completed detailed route,
extracted timing/electrical checks and matching final-netlist replay. A passing
row here cannot substitute for any of those gates.
