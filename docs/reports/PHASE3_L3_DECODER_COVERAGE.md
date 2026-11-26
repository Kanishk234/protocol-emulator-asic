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

## Qualified routed evidence

The [required-sigrok 22-case replay](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44123392388) supplies the earlier coverage. The three added checks each passed on the exact [green Phase 2 routed netlist](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44189196098) using Tiny Tapeout Icarus 13. The netlist SHA-256 is `537f41adee4320df81a0b7e907f011510cc578ab3c2a17105e00a80e0bacbcc9`. Sigrok independently emitted one NEC repeat annotation from the captured ui0 waveform. Each targeted result has one pass, zero failures and zero skips among the selected cases.

| Case | Local result XML SHA-256 |
| --- | --- |
| DShot | `bd995416fc74d4b59538970296fc5dbecbe67781989ba663c899f7f4e6d463ef` |
| HDLC | `432955f4642fbdd86f4f9a83e472c8dbf94d20bb0ff8e453e1b5cd5c531af664` |
| NEC repeat | `014288f018cf4755175aa88947cf4128d2968f073b6e493488b670aba93830c6` |
