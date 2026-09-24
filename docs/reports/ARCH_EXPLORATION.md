# Architecture exploration (phase 1, DECISIONS D-008)

Numbers from `tools/tripsim` running protocol kernels (`tools/kernels`). Each row names the test that produces it, so every number can be re-run with `python -m pytest -q`.

**Status: in progress.** All numbers are from simulation on the model, with ideal pads and buses (no rise times, no metastability).

## 1. Answers to `ISA.md` §9 so far

| Question | Measured | Evidence | Decision so far |
|---|---|---|---|
| Pin-to-pin reaction (§5.5) | **7 clocks (140 ns)**, exactly as specified | `tripsim/tests/test_pins.py::test_pin_to_pin_reaction_is_seven_clocks` | Claim holds on the model |
| What should OP 15 be? | `MOVB` (d = B): "on an input, send a constant" had no one-action form, and without it the reaction would be 8 clocks | Same test | D-009 |
| Are 12 slots enough? | UART TX: 1. UART RX with framing check: 3. SPI controller: 4. SPI target: 3. I2C controller: 11 + 2 routines. **I2C target, full read + write: 12** (14–18 before D-013) | `test_pins.py`, `kernels/tests/*` | Yes for every required protocol role so far (the largest, the full I2C target, uses exactly 12). Still to measure: device emulation (EEPROM/flash) |
| Flag result from every op (D-007) | Count loop: **3 clocks per byte** (4 with the old compare-only flags) | `tripsim/tests/test_lane.py::test_count_loop_three_clocks_per_byte` | Keep |
| K constants (D-007) | The I2C target keeps its address, mask and pin commands in K, leaving all 4 registers free | `kernels/i2c_target.py` | Keep; register pressure still to measure on larger kernels |
| `data[15]` head test (D-007) | The I2C target tells START from STOP in the condition, so no compare action is needed | `kernels/i2c_target.py` slots 0–1 | Keep |
| I2C ACK deadline | ACK queued **7 clocks** after the 8th SCL rise; SDA goes low 3 clocks after the SCL fall. Works down to 12 clocks per SCL period (SCL high ≥ 6 clocks). Fm+ (1 MHz) guarantees ≥ 13 clocks high, so the margin is about 2x | `test_i2c_target.py::test_i2c_target_speed_margin` | Meets 100 kHz / 400 kHz / 1 MHz with margin |
| SPI controller, mode 0 | Works up to **SCK = 12.5 MHz** (4 clocks per period, symmetric clock; D-016). The earlier 16.7 MHz relied on a lopsided 2:1 duty cycle from odd-period rounding. Above 12.5 MHz, MISO through the 2-clock synchroniser is sampled one bit late against our unsynchronised internal SCK. **4 slots**, 4 pin units, 1 lane | `kernels/tests/test_spi_controller.py` | Meets typical SPI peripheral speeds up to 12.5 MHz; the RX sample delay idea (§4) could reach ~25 MHz. The Q7 fabric limit is not the bottleneck here |
| SPI target, mode 0 (TRIPWIRE clocked by the other side) | **SCK ≤ 12.5 MHz** with MISO changing just after the SCK rise (the pin unit's TX_EDGE); 8.33 MHz with the textbook "change on the fall". CS setup ≥ 3 clocks (60 ns); MISO released ≤ 3 clocks after deselect. **3 slots**, 2 pin units | `kernels/tests/test_spi_target.py` | Every target-side limit comes from the 2-clock input synchroniser. Configuration alone (TX_EDGE) recovers 1.5x |
| I2C controller | Writes, reads with ACK/NACK, repeated START, STOP, NACKed address; **100 kHz / 400 kHz / 1 MHz**, with no stretch, 40-clock stretch and longer-than-a-period stretch. tLOW, tHIGH ≥ PERIOD/2 on the bus. Stretch awareness adds 3 clocks per high phase: 943 kHz at a nominal 1 MHz (a shorter PERIOD compensates). **11 slots + 2 routines** (START/STOP sequences run from SRAM: nothing races a deadline when we own the clock) | `kernels/tests/test_i2c_controller.py` | Meets all standard I2C speeds; first real use of routines |
| WS2812 / DShot (PULSE mode, D-019) | WS2812: 2 slots, every datasheet tolerance met, sigrok agrees. DShot150–1200: 2 slots + a 10-step checksum routine (about 50 clocks, against a 1330-clock frame at DShot600) | `kernels/tests/test_pulse_protocols.py` | Pulse-coded outputs cost almost no lane work |
| PS/2 host (D-020) | Both directions at the 16.7 kHz device clock, parity errors reported, device ACK checked, host send interleaved with device traffic. **12 slots + 1 routine**, 2 pin units. The host's own CLK-low inhibit is a counted fall; `SETN rx` restarts the framing at 100 µs, while CLK is still held | `kernels/tests/test_ps2.py` | Timed RX restart is needed by any protocol where our own line activity would otherwise be counted |
| 1-Wire controller (D-020) | Reset/presence, write slots (PULSE), read slots with `SAMPLE` 15 µs into the slot; exact AN126 timing (every slot 70 µs, low times 6/60 µs). **9 slots + 1 routine**, 1 pin unit | `kernels/tests/test_onewire.py` | Controller-timed sampling needs no clock pin |
| SWD controller | Reads, writes, WAIT + retry, posted AP reads; no bus contention. **12 slots + 3 routines**, 2 pin units. SWCLK up to **8.3 MHz** (period 6); 10 MHz fails because the ACK framing restart must reach the pin unit within one SWCLK period of the 8th fall (routine latency; loading constants first raised the limit from 5 MHz) | `kernels/tests/test_swd.py` | A dedicated "queue the next RX length at a word boundary" option would remove the latency limit; not needed for typical 1–8 MHz probes |
| JTAG controller | Generic scan engine: TMS/TDI chunks ≤ 12 clocks, TDO back per chunk; IDCODE, USER write/readback, BYPASS. **8 slots**, 4 pin units. TCK up to **12.5 MHz** (period 4) with a zero-delay target | `kernels/tests/test_jtag.py` | The TAP walk stays in host software, as in CMSIS-DAP/MPSSE; 4 slots remain for on-chip IR/DR helpers if needed |
| CAN 2.0A (BITSYNC, D-023) | TX/RX/ACK/arbitration at **125 k, 500 k and 1 Mbit/s**; receives a transmitter at ±0.4 % clock; the ACK lands in its slot with 100 and 300 ns transceiver loop delay. **2 lanes (11 + 10 slots) + 3 routines**, 1 pin unit. The same BITSYNC unit runs an HDLC-style configuration at ±2 % drift | `kernels/tests/test_can.py`, `tripsim/tests/test_bitsync.py` | CAN needs two lanes: one owns the unit's command stream (TX), one parses frames and asks for FRAME/ACK. A second per-unit command port would allow one lane; not needed so far |
| MIDI, DMX512, servo, IR NEC, SMBus, LIN, I2S, HDLC | All verified on the model: MIDI on the UART program; DMX 5 slots; servo 2; IR 2 lanes; SMBus 12 (+ PEC table); LIN 4 + 5; I2S 7; HDLC 6 | `kernels/tests/test_simple_protocols.py`, `test_smbus.py`, `test_lin.py`, `test_i2s.py`, `test_hdlc.py` | New hardware only where a general gap showed (D-024 timestamps in ticks + carrier; D-025 flag framing + TX CRC); the rest is firmware |
| CAN 2.0A/B with error handling | Error flags, TEC/REC, passive, bus-off: 12 + 12 slots, 7 routines, 353 of 512 SRAM words | `kernels/tests/test_can_errors.py` | The counters and states are firmware; the unit gives JAM, readback modes and listen-only (D-026) |
| USB low-speed (feasibility) | Enumeration works; response turnaround 6.1–7.1 bit times (limit 7.5) after moving the token check to a single compare against a precomputed expected token | `kernels/tests/test_usb_ls.py` | The lane is fast enough at 1.5 Mbit/s with care; full speed (12 Mbit/s, ~4 clocks per bit) remains out of reach |
| Lane outputs (2) vs protocol outputs | SPI controller needs 3 output streams (MOSI, SCK, CS) | SPI and I2C controller kernels | D-015: consumer-port tag filters let one lane output feed several pin units and the host |
| Routine rate | 1 step per 4 clocks. Urgent reflexes that are ready every clock starve a routine; non-urgent ones do not | `test_lane.py` routine tests | As designed (ISA.md §5.3) |
| R1 fallback (every other clock) | Re-measured on all current kernels: **no speed limit changes**. I2C target 12 clocks/bit; I2C controller passes 100 kHz / 400 kHz / 1 MHz with stretching; SPI controller 12.5 MHz; SPI target 12.5 MHz. SPI controller throughput at 12.5 MHz: 43.5 vs 40.2 clocks per byte (about 8% slower). The 7-clock pin-to-pin reaction does grow with the fallback: every EVAL waits for an even clock | `fastest_*` helpers in `kernels/tests` with `Chip(fire_period=2)` | For the kernels so far, the fallback is **cheap**. That lowers the stakes of R1: if lane timing does not close at 50 MHz, the protocols still meet their speeds. The headline reaction claim would change |

## 2. Findings that changed the spec

| Finding | Where | Result |
|---|---|---|
| A tap with a 1-bit `seq` aliases after missing two tokens and stops seeing new ones | `test_fabric.py` | BUGS #2; §14 F4 (a counted drop is a take) |
| "React to an input with a constant" needed two actions | `test_pins.py` latency kernel | D-009 `MOVB` |
| I2C needs different RX and TX link edges, and the 9th bit as a separate token | I2C target kernel | D-010 (RX_EDGE/TX_EDGE), §14 P6–P8 |
| An SPI target needs a third pin (CS) to frame, abort and tri-state | SPI target kernel | D-014 pin C; §14 P15 |
| One output must feed a pin unit and the host; clocks need stretch and a START hold; STOP needs "after SCL rose"; controller read bytes must not be echo-tainted | I2C controller kernel | D-015 port tag filters (supersede D-011); D-016 CLKGEN shape + STRETCH, WAIT, echo = shifted bits; §14 F7, P11, P13, P16. BUGS #4 (kernel START race) |
| The full I2C target (read + write) needed 14–18 slots with protocol-shaped features | I2C target kernel | D-012 principle; D-013 generalized primitives, which bring it to 12 slots; §14 P8, P13, P14 |
| Our own PS/2 inhibit edge is counted by LINKED_RX; 1-Wire read slots have no clock edge to link to | PS/2 host, 1-Wire kernels | D-020 `SETN rx` (timed framing restart + RX length) and `SAMPLE`; §14 P18, P19 |
| SWD: RX words sampled during a write reached the next transaction's ACK slot | SWD kernel (firmware bug, BUGS #8) | Fixed in firmware with existing features: `rx_echo=false` plus a framing restart per phase |
| CAN: a shared, TX-ordered command stream can block RX commands (FRAME, ACK) behind pending TX data | CAN program (BUGS #11, #12) | RX commands bypass the TX queue in the unit (§14 P25); the program keeps pending TX data out of the lane output ("started" event); the ACK is a one-bit override (§14 P26) |
| An SPI controller needs 3 output streams from a 2-output lane; mode 0 needs bit 0 before the first clock edge | SPI controller kernel | D-011 (TX_ACCEPT, TX_PRELOAD); §14 P9–P12. BUGS #3 (model preload race, found by the same kernel) |
| Fabric throughput below the §4.4 target | `test_lane.py` throughput tests | Q7 open: a lane output takes 1 token per 3 clocks; HOST_IN delivers 1 per 2 clocks to a lane |

## 3. Generality of the primitives (D-012)

Each primitive is judged by the general need it serves and its cost, not by a count. The "uses so far" column is evidence from kernels, not a threshold.

| Primitive | General need | Uses so far (kernels) | Expected elsewhere |
|---|---|---|---|
| Timed shift TX / SHIFT_RX | Self-clocked serial at a fractional rate | UART TX, UART RX | LIN, DMX512, MIDI, 1-Wire slots, Manchester via 2x rate |
| Linked shift TX (+ preload) / LINKED_RX | Serial clocked by another pin | SPI controller (MOSI, MISO), I2C target | SPI target, JTAG, SWD, PS/2, I2S |
| CLKGEN | Generate n clock periods on a cursor | SPI controller | I2C controller (with STRETCH), JTAG, SWD |
| Event generator (+ qualifier, framing reset) | Edge events, optionally qualified | Latency kernel (timestamps), I2C START/STOP | Frame starts (CS, sync pulses), IR/PWM capture, wake-up |
| Pin C select/frame (framing reset, abort, OE gating, events) | Select- or frame-delimited streams | SPI target (CS) | I2S word select, PCM/TDM frame sync, chip-enable buses |
| Two-phase framing | Alternating word lengths | I2C 8 + 1 | Data + parity, command + argument |
| Echo suppression | Half-duplex shared lines | I2C target, SWD (drops words sampled during our request and write phases) | Half-duplex UART, LIN (with RX_ECHO = 1 for collision checks) |
| Consumer-port tag filter (fabric) | One output → several consumers, each keeping its tokens | SPI controller (SCK/MOSI/CS), I2C controller (SCL + host; events off the lane input) | Any protocol with more than 2 output streams; any lane that ignores part of a stream |
| WAIT (pin B edge) | Sequence one pin against another pin's real edge | I2C controller (START/STOP after SCL rises; SCL clocks after the START edge), SWD (release SWDIO at the 8th fall; drive again after turnarounds) | Ready/busy handshakes, DShot telemetry turnaround |
| CLKGEN STRETCH | Clock generation on a shared or stretched clock line | I2C controller | SMBus, PMBus, multi-controller I2C |
| PULSE two-phase symbols | Pulse-width, pulse-distance and Manchester codes | WS2812, DShot | IR NEC, SK6812, servo-like pulse trains, DALI/RF Manchester |
| TX length in the token | Variable-length shifts | I2C target (1-bit ACK, 8-bit byte), PS/2 (10-bit send), SWD (8/12/9-bit), JTAG (1–12-bit chunks) | Odd SPI, bit-banged register formats |
| `SETN rx`: timed RX framing restart + RX length (D-020) | Word framing that must start at a chosen time, or change length at run time | PS/2 (after our inhibit), 1-Wire (1-bit presence, 8-bit bytes), SWD (3/16/2-bit phases), JTAG (per-chunk TDO words) | MDIO, half-duplex SPI, any request/response bus |
| BITSYNC: recovered bit clock + resync, stuffing, CRC, readback, frame length, one-bit override (D-023) | Self-clocked NRZ buses with clock tolerance and in-frame responses | CAN 2.0A; an HDLC-style test configuration (ones stuffing, CRC-16/CCITT) | USB LS (with NRZI), LIN, DMX, SDLC, 1-Wire search |
| Event timestamps in PRESC ticks; CARRIER (D-024) | Long pulse timing; carrier-modulated outputs | IR NEC RX/TX | Servo capture, LIN breaks, RF on-off keying |
| Flag-delimited framing, TX CRC register, own-edge rule (D-025) | Bit-oriented framing; self-clocked TX correctness | HDLC; CAN and USB (own-edge rule) | SDLC, PPP, AX.25 |
| JAM, readback modes, listen-only (D-026) | In-frame responses and error signalling; silent monitoring | CAN (ACK, error flags, bus-off) | J1850-style buses, analyzers |
| NRZI, pin N, OE auto, SE0, CRC skip (D-027) | Differential half-duplex NRZI links | USB low speed (feasibility) | RS-485 half duplex, NRZI RF/SDLC links |
| tripc `table` (D-028) | Lookup tables and initialised variables in SRAM | SMBus PEC, LIN slot table, USB descriptor | 4b5b, gamma, any CRC-by-table |
| `pin_s` sense pad (D-023) | Drive one pad, sense another | CAN TXD/RXD | RS-485 DE/RO, LIN and IrDA transceivers |
| `SAMPLE` (D-020) | Sample a pin at a time we choose, with no clock edge | 1-Wire read slots and presence | Open-drain handshakes, bit-banged slow buses, ADC-style strobes |
| ISA: `MOVB`, `HS`, K constants, flag from every op | React with constants; test flag bits; loop counters | Latency, I2C target, UART RX, count loop | Everywhere |

## 4. Next measurements
- RX sample delay (general form: sample N clocks after the linked edge). It would compensate the input synchroniser when the clock is our own, which could lift the SPI controller from 12.5 to ~25 MHz.
- I2C target EEPROM variant (register pointer, sequential read/write; needs the MEM helper, or routines).
- SPI flash emulation (READ with a 24-bit address): needs the MEM helper or routines; whether Q7 limits streaming.
- Run each kernel with `fire_period = 2` to price the R1 fallback.
- Ablation: turn off each D-007 feature (implicit checks, K, `HE/HV`, flag-from-every-op) and count slots and clocks.
