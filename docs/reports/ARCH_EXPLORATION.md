# Architecture exploration (phase 1, DECISIONS D-008)

Numbers from `tools/tripsim` running protocol kernels (`tools/kernels`). Each row names the test that produces it, so every number can be re-run with `python -m pytest -q`.

**Status: in progress.** All numbers are from simulation on the model, with ideal pads and buses (no rise times, no metastability).

## 1. Answers to `ISA.md` §9 so far

| Question | Measured | Evidence | Decision so far |
|---|---|---|---|
| Pin-to-pin reaction (§5.5) | **7 clocks (140 ns)**, exactly as specified | `tripsim/tests/test_pins.py::test_pin_to_pin_reaction_is_seven_clocks` | Claim holds on the model |
| What should OP 15 be? | `MOVB` (d = B): "on an input, send a constant" had no one-action form, and without it the reaction would be 8 clocks | Same test | D-009 |
| Are 12 slots enough? | UART TX: 1. UART RX with framing check: 3. I2C target, write direction: **9** | `test_pins.py`, `kernels/tests/test_i2c_target.py` | Not yet decided: I2C read direction, SPI and the EEPROM variant still to measure |
| Flag result from every op (D-007) | Count loop: **3 clocks per byte** (4 with the old compare-only flags) | `tripsim/tests/test_lane.py::test_count_loop_three_clocks_per_byte` | Keep |
| K constants (D-007) | The I2C target keeps its address, mask and pin commands in K, leaving all 4 registers free | `kernels/i2c_target.py` | Keep; register pressure still to measure on larger kernels |
| `data[15]` head test (D-007) | The I2C target tells START from STOP in the condition, so no compare action is needed | `kernels/i2c_target.py` slots 0–1 | Keep |
| I2C ACK deadline | ACK queued **7 clocks** after the 8th SCL rise; SDA goes low 3 clocks after the SCL fall. Works down to 12 clocks per SCL period (SCL high ≥ 6 clocks). Fm+ (1 MHz) guarantees ≥ 13 clocks high, so the margin is about 2x | `test_i2c_target.py::test_i2c_target_speed_margin` | Meets 100 kHz / 400 kHz / 1 MHz with margin |
| Routine rate | 1 step per 4 clocks. Urgent reflexes that are ready every clock starve a routine; non-urgent ones do not | `test_lane.py` routine tests | As designed (ISA.md §5.3) |
| R1 fallback (every other clock) | Not measured on the protocol kernels yet | — | To do |

## 2. Findings that changed the spec

| Finding | Where | Result |
|---|---|---|
| A tap with a 1-bit `seq` aliases after missing two tokens and stops seeing new ones | `test_fabric.py` | BUGS #2; §14 F4 (a counted drop is a take) |
| "React to an input with a constant" needed two actions | `test_pins.py` latency kernel | D-009 `MOVB` |
| I2C needs different RX and TX link edges, and the 9th bit as a separate token | I2C target kernel | D-010 (RX_EDGE/TX_EDGE, RX_TAIL); §14 P6–P8 |
| Fabric throughput below the §4.4 target | `test_lane.py` throughput tests | Q7 open: a lane output takes 1 token per 3 clocks; HOST_IN delivers 1 per 2 clocks to a lane |

## 3. Next measurements
- I2C target read direction, and the EEPROM variant (needs the MEM helper): does it fit in 12 slots?
- SPI controller and SPI target (needs CLKGEN, linked TX on SCK): the maximum SCK, and whether Q7 limits streaming.
- I2C controller (CLKGEN with STRETCH).
- Run each kernel with `fire_period = 2` to price the R1 fallback.
- Ablation: turn off each D-007 feature (implicit checks, K, `HE/HV`, flag-from-every-op) and count slots and clocks.
