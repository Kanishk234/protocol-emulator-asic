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
| DShot and HDLC | The L3 cases check the waveforms with project models. They have no direct sigrok protocol check. |

Eighteen cases now contain sigrok calls. DShot and HDLC remain the two
protocol-level gaps in this L3 file. The installed decoder set contains
`ir_nec` but has no decoder directory named for DShot or HDLC. The UART RX
and PS/2 host-to-device gaps concern direction coverage within protocols
that already have one sigrok-checked direction.
