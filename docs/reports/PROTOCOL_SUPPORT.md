# Protocol support roadmap

Which protocols TRIPWIRE can support, how sure we are, and what each one still needs. Updated 2026-09-23.

**Labels (honest by design, CLAUDE.md):**
- **Verified (model):** a `.trw` program runs on `tripsim` against an independent reference model and sigrok. This is simulation only; there is no hardware yet.
- **Expected (firmware):** existing primitives cover it on paper; the program is not yet written or tested.
- **Needs primitive:** a general pin-unit or helper addition is needed first (D-012: general *and* efficient, no protocol blocks).
- **Not feasible:** not planned, with the reason.

Per CLAUDE.md, nothing here claims USB or Ethernet *support*. Those rows are feasibility notes.

## Status

| Protocol | Status | Notes |
|---|---|---|
| UART 8N1 (TX, RX, framing errors) | **Verified (model)** | `programs/uart.trw`, up to 1 Mbaud, fractional baud rates |
| SPI controller, mode 0 | **Verified (model)** | 12.5 MHz; modes 1–3 are TX/RX edge settings (`TX_EDGE`, `RX_EDGE`, CLKGEN idle level) |
| SPI target, mode 0 | **Verified (model)** | 12.5 MHz, CS setup ≥ 60 ns |
| I2C controller (stretching, repeated START) | **Verified (model)** | 100 kHz / 400 kHz / 1 MHz |
| I2C target (read + write) | **Verified (model)** | 100 kHz / 400 kHz / 1 MHz, 12 slots |
| MIDI | **Verified (model)** | `programs/uart.trw` at 31 250 baud, TX and RX; sigrok `midi` decodes note on/off, control and program change |
| DMX512-A (TX and RX) | **Verified (model)** | `programs/dmx.trw`, 5 slots + 1 routine: BREAK/MAB, 250 kbaud 8N2, RX break detection; reference decoder (zero MTBF/MTBP) and sigrok `dmx512` (with a small MTBF/MTBP: BUGS #16) |
| UART with other framings (7/9 bits, parity) | Expected (firmware) | UART variants: NBITS, `PAR` |
| SMBus (PMBus transport) | **Verified (model)** | `programs/smbus.trw`, 12 slots + 4 routines + a 16-word table: the I2C controller plus PEC (CRC-8) computed on chip for writes and checked for reads; reference SMBus device with PEC, 100 and 400 kHz |
| SWD (controller) | **Verified (model)** | `programs/swd.trw`, 12 slots + 3 routines: request, ACK (OK/WAIT), read with parity, write, posted AP reads; no bus contention; sigrok `swd`. SWCLK up to 8.3 MHz (fails at 10 MHz: the ACK framing restart must land within one SWCLK period of the 8th fall). The host computes the write parity and checks the read parity |
| JTAG (controller) | **Verified (model)** | `programs/jtag.trw`, 8 slots: a generic scan engine (TMS + TDI chunks of ≤ 12 clocks, TDO back per chunk), so any TAP path, IR/DR length or chain works. Checked against an IEEE 1149.1 TAP model (IDCODE, USER register, BYPASS) and sigrok `jtag`; TCK up to 12.5 MHz (ideal wires, zero-delay target) |
| PS/2 (host side) | **Verified (model)** | `programs/ps2_host.trw`, 12 slots + 1 routine: both directions, start/stop/parity checks, device ACK check, interleaved traffic; sigrok `ps2`. Needed the RX framing restart (D-020) after the host's own inhibit edge |
| 1-Wire (controller) | **Verified (model)** | `programs/onewire.trw`, 9 slots + 1 routine: reset/presence, PULSE write slots, read slots with `SAMPLE` (D-020), AN126 standard-speed timing; READ ROM with CRC-8 against a DS18B20-like device model; sigrok `onewire_link` + `onewire_network` |
| I2S (controller, 16-bit stereo, out and in) | **Verified (model)** | `programs/i2s.trw`, 7 slots, 4 pin units: WS is a second shifted pattern (changes one BCLK before each MSB); 48/96/192 kHz; reference receiver and ADC models (Philips spec), loopback; sigrok `i2s` |
| PCM / TDM | Expected (firmware) | As I2S with other WS patterns and word lengths |
| IR remote, NEC (TX and RX) | **Verified (model)** | `programs/ir_nec.trw`, 2 lanes: TX with a 38 kHz carrier (D-024) and exact 108 ms frames, sigrok `ir_nec` (carrier detection); RX from edge timestamps in PRESC ticks (frames and repeat codes) |
| Slow Manchester (DALI, etc.) | Expected (firmware) | Encode/decode in routines or from edge timestamps; fine at kbit/s rates |
| WS2812 / WS2812B / SK6812 | **Verified (model)** | `programs/ws2812.trw`, 2 slots; every datasheet tolerance checked by a reference decoder; sigrok `rgb_led_ws281x` |
| DShot150 / 300 / 600 / 1200 | **Verified (model)** | `programs/dshot.trw`: the lane computes the checksum in a routine; frames, checksums and bit timing checked by a reference decoder (sigrok has no DShot decoder) |
| Servo / ESC PWM | **Verified (model)** | `programs/servo.trw`, 2 slots + 1 routine: 500–4000 µs pulses, exactly 20 ms period, width updates between frames; sigrok `pwm` |
| Quad / dual SPI, 8080 parallel | Needs primitive: **parallel shift** (optional) | Works today at low speed with one unit per line; a unit that shifts N pins at once would make it efficient |
| LIN 2.x commander | **Verified (model)** | `programs/lin.trw`, 2 lanes (4 + 5 slots), 4 routines: break/sync/protected ID, publish and subscribe, enhanced and classic checksums on chip, slot pacing (LIN 1.4 x rule), bad checksum and no-response detection; reference LIN responder and sigrok `lin` |
| LIN responder with auto-baud | Needs primitive: **runtime period change** | A responder at a fixed baud rate is firmware; auto-baud needs a CTRL command that sets PERIOD at runtime |
| HDLC / SDLC framing | **Verified (model)** | `programs/hdlc.trw`, 6 slots + 2 routines: flags, zero insertion, FCS-16, aborts (BITSYNC DELIM = flag, D-025); a reference ISO/IEC 13239 codec, ±1 % clock; sigrok has no HDLC decoder |
| **CAN 2.0A/B** (stretch goal) | **Verified (model)** | `programs/can.trw`, 2 lanes (12 + 12 slots), 7 routines, 1 pin unit (BITSYNC, D-023/D-026). 11- and 29-bit IDs, data and remote frames, 125 k / 500 k / 1 Mbit/s, ±0.4 % clock, ACK, arbitration, error flags (stuff, bit, CRC, ACK errors), TEC/REC, error-passive, bus-off with host recovery; a reference CAN 2.0 node (error frames, retransmission) + sigrok `can`. Not yet: overload frames, form-error checks of our own receiver on delimiters, automatic bus-off recovery (128 x 11 recessive bits), CAN FD |
| **USB low-speed** (stretch, **feasibility only, not a support claim**) | Feasibility shown on the model | `programs/usb_ls.trw` (5 + 1 slots, 2 routines) with BITSYNC NRZI, pin N, OE auto, SE0 (D-027): enumerated by a reference USB 2.0 low-speed host (GET_DESCRIPTOR, SET_ADDRESS), turnaround ≤ 7.14 bit times (limit 7.5), bad CRCs ignored, sigrok `usb_packet` decodes every payload byte. Not done: other endpoints and requests, suspend/resume, electrical signalling (no hardware) |
| **10BASE-T Ethernet** | Not feasible | 10 Mbit Manchester needs 20 Mbaud half-bits: 2.5 clocks each at 50 MHz, below what the 2-clock input synchroniser can recover, and not an integer period for TX. It also needs analog line levels/magnetics |

## The primitives that unlock the most (in order of value per cost)
1. ~~PULSE mode~~: done (D-019). WS2812 and DShot are verified on the model.
2. ~~**Edge-resync receiver:**~~ done in BITSYNC (D-023). re-anchor the sampling phase on every edge, not only the start edge. Makes long self-clocked frames robust (CAN, USB, DMX, long UART frames at clock mismatch).
3. **Line-coding options in the pin unit:** bit stuffing is done (BITSYNC, D-023); still to do: NRZI (USB) and Manchester (DALI, some RF).
4. ~~**Readback compare:**~~ done in BITSYNC (D-023). stop driving and raise an EVENT when the sampled bit differs from the driven bit (CAN arbitration, multi-controller I2C, 1-Wire search).
5. **CRC:** a bit-serial CRC ≤ 16 bits is in BITSYNC (D-023). A byte-wide CRC helper on the fabric (CRC-32, SMBus PEC from lanes) is still planned.
6. Runtime PERIOD command (auto-baud), parallel multi-pin shift.

Timed RX control (`SETN rx`, `SAMPLE`, D-020) was added the same way, for PS/2 and 1-Wire.

Each will go through the model first: build it, write the protocol kernel, measure slots, speed and cost, then decide. That is the same loop that produced D-009 to D-016.
