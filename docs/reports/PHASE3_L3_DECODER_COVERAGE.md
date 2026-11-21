# Phase 3 L3 decoder coverage

The table inventories direct sigrok checks in the 22 chip cases in
`test_internal/chip/test_l3.py`. It describes test coverage. It does not
credit a run that skipped sigrok or selected other cases.

| Protocol | Direct sigrok coverage |
| --- | --- |
| UART | TX waveform at all three tested baud rates. The RX framing case uses protocol-model stimulus and checks emitted tokens. |
| MIDI, DMX512, WS2812, servo PWM, I²S | Each has a direct decoder check in its L3 case. |
| SPI and I²C | Controller and target cases both have direct decoder checks. |
| PS/2 | Device-to-host includes bytes and parity annotations. Host-to-device uses the independent peer model. |
| 1-Wire, JTAG, SMBus, SWD, LIN, CAN | Each has a direct decoder check in its L3 case. |
| NEC IR | The repeat receive case now captures the actual ui0 level and checks exactly one repeat-code annotation. The device result is checked separately. |
| DShot | Sigrok's timing decoder measures high and low intervals at all four rates. The test reconstructs packet bits from those intervals and checks payload, telemetry, checksum and spacing. |
| HDLC | Sigrok's timing decoder measures the transmit runs. The test reconstructs the flag-delimited bitstream and compares it with the stuffed payload and independently calculated FCS. |

Twenty cases now use sigrok measurements. The installed set has no dedicated
DShot or HDLC decoder, so those two cases pair the generic timing decoder
with waveform checks in the test harness. The UART RX
and PS/2 host-to-device gaps concern direction coverage within protocols
that already have one sigrok-checked direction.

The targeted DShot and HDLC checks passed on the exact B-edge candidate in
Verilator with sigrok enabled. DShot covered five frames at each of four
rates, and HDLC covered the existing 100 kbit/s stuffed-frame loopback.
The updated checks have no new routed-netlist result yet.
