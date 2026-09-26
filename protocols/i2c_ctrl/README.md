# I2C controller (design-set protocol)

User design for the WARP fabric (soft logic; see `../README.md`): the I2C side that drives SCL and starts transactions.

- **File:** `i2c_ctrl_top.v` (user-design top, provisional interface D-014).
- **Bus:** open drain (`sda_oe`/`scl_oe` pull low, external pull-ups); inputs two-flop synchronized.
- **Features:** START, repeated START, STOP, byte write with ACK/NACK reply, byte read with ACK or NACK, **clock stretching** (every wait for SCL high reads the bus, so a target holding SCL low simply delays the controller). SDA changes only while SCL is low, Q clocks after SCL falls.
- **Timing:** each SCL low and high phase lasts 2·`Q` clocks (+ synchronizer delay); SCL ≈ clk / (4·`Q` + 3). `Q = 125` → ~100 kHz at 50 MHz. `Q` ≥ 2.
- **Host side:** a command byte stream on `h_w*`:

  | Byte | Command | Reply on `h_r*` |
  |---|---|---|
  | `00xx_xxxx` | START (repeated START if the bus is ours) | none |
  | `01xx_xxxx`, then a data byte | WRITE | `00` ACK / `01` NACK |
  | `10xx_xxx0` / `10xx_xxx1` | READ, answer ACK / NACK | the byte read |
  | `11xx_xxxx` | STOP | none |

  `h_status = {4'b0, err, overrun, last_nack, bus_owned}`; `err` = WRITE/READ/STOP when not allowed (sticky).
- **Rates:** RTL simulation only; no chip rates claimed.
- **Known limits:** single controller (no arbitration or bus-busy detection); 7-bit addresses are built by the host; no timeout on a target stretching forever.

## Tests
`test/`: cocotb + Icarus. The bus is the wired-AND of the controller and one or two independent I2C target models (`tools/refmodels/i2c.py`), clock by clock. Checks: target register contents, host replies, bus events decoded by our decoder and by sigrok's `i2c` decoder, no SDA change while SCL is high except START/STOP, bus released at the end.
```
cd test && make            # Q=4; also Q=2, Q=7
```
Covered: write then read back with repeated START, wrong address NACK, data-byte NACK, clock stretching (13·Q clocks per bit), two targets on one bus, commands without START. Local run 2026-09-25: 18/18 pass (Q = 4, 2, 7).

## Resource use (first profile, 2026-09-25, `synth_fabulous`, Yosys 0.66+179)
| Variant | LUTs | FFs |
|---|---|---|
| `Q=125` (~100 kHz) | 164 | 65 |
| `Q=4` | 149 | 61 |
