# Architecture exploration (phase 1, DECISIONS D-008)

Numbers from `tools/tripsim` running protocol kernels (`tools/kernels`). Each row names the test that produces it, so every number can be re-run with `python -m pytest -q`.

**Status: in progress.** All numbers are from simulation on the model, with ideal pads and buses (no rise times, no metastability).

## 1. Answers to `ISA.md` §9 so far

| Question | Measured | Evidence | Decision so far |
|---|---|---|---|
| Pin-to-pin reaction (§5.5) | **7 clocks (140 ns)**, exactly as specified | `tripsim/tests/test_pins.py::test_pin_to_pin_reaction_is_seven_clocks` | Claim holds on the model |
| What should OP 15 be? | `MOVB` (d = B): "on an input, send a constant" had no one-action form, and without it the reaction would be 8 clocks | Same test | D-009 |
| Are 12 slots enough? | UART TX: 1. UART RX with framing check: 3. SPI controller: 4. SPI target: 3. **I2C target, full read + write: 12** (14–18 before D-013) | `test_pins.py`, `kernels/tests/test_i2c_target.py` | Not yet decided: I2C read direction, SPI and the EEPROM variant still to measure |
| Flag result from every op (D-007) | Count loop: **3 clocks per byte** (4 with the old compare-only flags) | `tripsim/tests/test_lane.py::test_count_loop_three_clocks_per_byte` | Keep |
| K constants (D-007) | The I2C target keeps its address, mask and pin commands in K, leaving all 4 registers free | `kernels/i2c_target.py` | Keep; register pressure still to measure on larger kernels |
| `data[15]` head test (D-007) | The I2C target tells START from STOP in the condition, so no compare action is needed | `kernels/i2c_target.py` slots 0–1 | Keep |
| I2C ACK deadline | ACK queued **7 clocks** after the 8th SCL rise; SDA goes low 3 clocks after the SCL fall. Works down to 12 clocks per SCL period (SCL high ≥ 6 clocks). Fm+ (1 MHz) guarantees ≥ 13 clocks high, so the margin is about 2x | `test_i2c_target.py::test_i2c_target_speed_margin` | Meets 100 kHz / 400 kHz / 1 MHz with margin |
| SPI controller, mode 0 | Works up to **SCK = 16.7 MHz** (3 clocks per period). At 25 MHz, MISO through the 2-clock synchroniser misses. About 38 clocks per byte at 12.5 MHz (32 for the bits alone); **4 slots**, 4 pin units, 1 lane | `kernels/tests/test_spi_controller.py` | Meets typical SPI flash/peripheral speeds for reads up to 16.7 MHz. The Q7 fabric limit is not the bottleneck here |
| SPI target, mode 0 (TRIPWIRE clocked by the other side) | **SCK ≤ 12.5 MHz** with MISO changing just after the SCK rise (the pin unit's TX_EDGE); 8.33 MHz with the textbook "change on the fall". CS setup ≥ 3 clocks (60 ns); MISO released ≤ 3 clocks after deselect. **3 slots**, 2 pin units | `kernels/tests/test_spi_target.py` | Every target-side limit comes from the 2-clock input synchroniser. Configuration alone (TX_EDGE) recovers 1.5x |
| Lane outputs (2) vs protocol outputs | SPI controller needs 3 output streams (MOSI, SCK, CS) | SPI kernel | D-011: tag filters let one lane output feed several pin units |
| Routine rate | 1 step per 4 clocks. Urgent reflexes that are ready every clock starve a routine; non-urgent ones do not | `test_lane.py` routine tests | As designed (ISA.md §5.3) |
| R1 fallback (every other clock) | I2C target: fastest still 12 clocks/bit (the sweep steps in 2-clock units). SPI controller: fastest SCK still 16.7 MHz (the synchroniser is the limit); at 12.5 MHz, 41.5 vs 38.2 clocks per byte (about 9% slower). The 7-clock pin-to-pin reaction does grow with the fallback: every EVAL waits for an even clock | `fastest_*` helpers in `kernels/tests` with `Chip(fire_period=2)` | For the kernels so far, the fallback is **cheap**. That lowers the stakes of R1: if lane timing does not close at 50 MHz, the protocols still meet their speeds. The headline reaction claim would change |

## 2. Findings that changed the spec

| Finding | Where | Result |
|---|---|---|
| A tap with a 1-bit `seq` aliases after missing two tokens and stops seeing new ones | `test_fabric.py` | BUGS #2; §14 F4 (a counted drop is a take) |
| "React to an input with a constant" needed two actions | `test_pins.py` latency kernel | D-009 `MOVB` |
| I2C needs different RX and TX link edges, and the 9th bit as a separate token | I2C target kernel | D-010 (RX_EDGE/TX_EDGE), §14 P6–P8 |
| An SPI target needs a third pin (CS) to frame, abort and tri-state | SPI target kernel | D-014 pin C; §14 P15 |
| The full I2C target (read + write) needed 14–18 slots with protocol-shaped features | I2C target kernel | D-012 principle; D-013 generalized primitives, which bring it to 12 slots; §14 P8, P13, P14 |
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
| Echo suppression | Half-duplex shared lines | I2C target | 1-Wire, SWD, half-duplex UART, LIN (with RX_ECHO = 1 for collision checks) |
| TX tag filter | One lane output → several pin units | SPI controller (SCK, MOSI, CS) | Any protocol with more than 2 output streams |
| TX length in the token | Variable-length shifts | I2C target (1-bit ACK, 8-bit byte) | SWD (1/3/8/32-bit phases), JTAG, odd SPI |
| ISA: `MOVB`, `HS`, K constants, flag from every op | React with constants; test flag bits; loop counters | Latency, I2C target, UART RX, count loop | Everywhere |

## 4. Next measurements
- I2C target EEPROM variant (register pointer, sequential read/write; needs the MEM helper, or routines).
- SPI flash emulation (READ with a 24-bit address): needs the MEM helper or routines; whether Q7 limits streaming.
- I2C controller (CLKGEN with STRETCH).
- Run each kernel with `fire_period = 2` to price the R1 fallback.
- Ablation: turn off each D-007 feature (implicit checks, K, `HE/HV`, flag-from-every-op) and count slots and clocks.
