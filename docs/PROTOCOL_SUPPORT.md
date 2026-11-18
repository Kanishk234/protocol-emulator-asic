# Protocol verification evidence

All 22 cases below passed on the exact official final gate netlist in run [44123392388](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44123392388). Source: `test_internal/chip/test_l3.py`. These are the named scenarios tested, not blanket conformance claims for every mode, speed or fault. The official template GL suite separately passed 3/3 cases.

The maintained manual `protocol-replay` workflow replays this existing suite against a successful official main GDS artifact, using matching software, PDK models, Tiny Tapeout Icarus 13 and independent sigrok decoding. It rejects missing, skipped or failed selected cases. It is functional gate-level simulation without SDF annotation; extracted STA provides timing signoff.

| Existing routed scenario | Evidence |
|---|---|
| `uart_tx` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `uart_rx_framing` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `midi_tx` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `dmx_tx` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `ws2812_tx` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `dshot_tx` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `servo_pwm` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `i2s` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `spi_controller` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `i2c_controller` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `spi_target` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `i2c_target` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `ps2_device_to_host` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `ps2_host_to_device` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `onewire_read_rom` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `jtag_idcode` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `smbus_word_pec` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `swd_dpidr_read_with_wait_retry` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `hdlc_tx_loopback` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `lin_commander_publish_response` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `can_standard_frame_and_ack` | Passed in 22/22 replay; exact scenario in `test_l3.py` |
| `ir_nec_repeat_rx` | Passed in 22/22 replay; exact scenario in `test_l3.py` |

No real-hardware testing is claimed. USB/Ethernet model work is not an ASIC support claim. Formal results apply only to the named properties and bounds in the verification documents. The retained stock FPGA workflow is not evidence of a Basys 3 build. Phase 3 expands independent peers, robustness and showcase evidence using the qualified general primitives.

## Additional Phase 3 showcase

The SRAM-backed I2C memory personality is verified separately from the historical 22-case run. It passes the independent model, chip RTL and the exact official final netlist at 400 kHz and 1 MHz, including the short-high waveform, with required sigrok decoding. See [its scope and hashed evidence](reports/PHASE3_I2C_MEMORY.md). This is volatile immediate-write memory, not full EEPROM conformance; the [independent RTL peer](reports/PHASE3_I2C_PEER.md) now passes, while the compiler-bound task remains open.

A separate [guarded memory personality](reports/PHASE3_I2C_GUARD.md) uses existing U1 and reserved output uo7 for select/abort recovery. Its finite recovery tests and replay status are recorded separately; the original one-unit example retains its documented late-ACK limitation. No hardware or full protocol-conformance claim is added.
