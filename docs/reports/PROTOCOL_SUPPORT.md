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
| MIDI, DMX512 TX, UART with other framings (7/9 bits, parity) | Expected (firmware) | UART variants: NBITS, `PAR`. A DMX/LIN *break* is a long low, detectable from edge timestamps |
| SMBus / PMBus | Expected (firmware) | I2C + PEC (CRC-8) computed in a routine; the CRC helper would make it cheaper |
| SWD (controller) | **Verified (model)** | `programs/swd.trw`, 12 slots + 3 routines: request, ACK (OK/WAIT), read with parity, write, posted AP reads; no bus contention; sigrok `swd`. SWCLK up to 8.3 MHz (fails at 10 MHz: the ACK framing restart must land within one SWCLK period of the 8th fall). The host computes the write parity and checks the read parity |
| JTAG (controller) | **Verified (model)** | `programs/jtag.trw`, 8 slots: a generic scan engine (TMS + TDI chunks of ≤ 12 clocks, TDO back per chunk), so any TAP path, IR/DR length or chain works. Checked against an IEEE 1149.1 TAP model (IDCODE, USER register, BYPASS) and sigrok `jtag`; TCK up to 12.5 MHz (ideal wires, zero-delay target) |
| PS/2 (host side) | **Verified (model)** | `programs/ps2_host.trw`, 12 slots + 1 routine: both directions, start/stop/parity checks, device ACK check, interleaved traffic; sigrok `ps2`. Needed the RX framing restart (D-020) after the host's own inhibit edge |
| 1-Wire (controller) | **Verified (model)** | `programs/onewire.trw`, 9 slots + 1 routine: reset/presence, PULSE write slots, read slots with `SAMPLE` (D-020), AN126 standard-speed timing; READ ROM with CRC-8 against a DS18B20-like device model; sigrok `onewire_link` + `onewire_network` |
| I2S / PCM / TDM | Expected (firmware) | Linked shifts + pin C as word select/frame sync; 16/24-bit words via NBITS (SETN) |
| IR (NEC) TX/RX | Expected (firmware) | TX: PULSE symbols in pulse-distance form (a fixed mark, then a space that encodes the bit), with the carrier from CLKGEN or an external modulator; RX from edge timestamps |
| Slow Manchester (DALI, etc.) | Expected (firmware) | Encode/decode in routines or from edge timestamps; fine at kbit/s rates |
| WS2812 / WS2812B / SK6812 | **Verified (model)** | `programs/ws2812.trw`, 2 slots; every datasheet tolerance checked by a reference decoder; sigrok `rgb_led_ws281x` |
| DShot150 / 300 / 600 / 1200 | **Verified (model)** | `programs/dshot.trw`: the lane computes the checksum in a routine; frames, checksums and bit timing checked by a reference decoder (sigrok has no DShot decoder) |
| Servo PWM | Expected (firmware) | Plain LEVEL commands with register-derived delays (`MKCTL`); no new primitive needed |
| Quad / dual SPI, 8080 parallel | Needs primitive: **parallel shift** (optional) | Works today at low speed with one unit per line; a unit that shifts N pins at once would make it efficient |
| LIN (target, with auto-baud) | Needs primitive: **runtime period change** | Pin config is host-written while halted; auto-baud needs a CTRL command that sets PERIOD at runtime |
| **CAN** (stretch goal) | Needs primitives: **edge-resync RX**, **bit-stuffing codec**, **readback compare**, **CRC helper** | Resync keeps long frames in phase; stuffing inserts/removes a bit after 5 equal bits; readback compare detects arbitration loss per bit; CRC-15 from the helper |
| **USB low-speed** (stretch, feasibility only) | Needs primitives: the CAN set + **NRZI codec**, **SE0 detection**, **complementary output pair** | 1.5 Mbit/s is 33 clocks per bit: comfortable. The work is the codec path and bus-turnaround timing. Largest effort of any row |
| **10BASE-T Ethernet** | Not feasible | 10 Mbit Manchester needs 20 Mbaud half-bits: 2.5 clocks each at 50 MHz, below what the 2-clock input synchroniser can recover, and not an integer period for TX. It also needs analog line levels/magnetics |

## The primitives that unlock the most (in order of value per cost)
1. ~~PULSE mode~~: done (D-019). WS2812 and DShot are verified on the model.
2. **Edge-resync receiver:** re-anchor the sampling phase on every edge, not only the start edge. Makes long self-clocked frames robust (CAN, USB, DMX, long UART frames at clock mismatch).
3. **Line-coding options in the pin unit:** bit stuffing (CAN, USB, HDLC), NRZI (USB), Manchester (DALI, 10BASE-T-style, some RF). One small state machine between shifter and pin.
4. **Readback compare:** stop driving and raise an EVENT when the sampled bit differs from the driven bit (CAN arbitration, multi-controller I2C, 1-Wire search).
5. **CRC helper** (planned): CRC-5/8/15/16/32 with any polynomial, fed by the fabric in parallel with the protocol lane.
6. Runtime PERIOD command (auto-baud), parallel multi-pin shift.

Timed RX control (`SETN rx`, `SAMPLE`, D-020) was added the same way, for PS/2 and 1-Wire.

Each will go through the model first: build it, write the protocol kernel, measure slots, speed and cost, then decide. That is the same loop that produced D-009 to D-016.
