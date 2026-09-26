# I2C target (design-set protocol)

User design for the WARP fabric (soft logic; see `../README.md`): an I2C device with a small register map that a bus controller and the host both access.

- **File:** `i2c_target_top.v` (user-design top, provisional interface D-014).
- **Address:** `ADDR` parameter (7-bit, default `0x42`), fixed in the bitstream.
- **Register map:** `NREGS` 8-bit registers (power of two, ≤ 16; default 4).
  - Bus write `[ADDR+W][pointer][data…]`: pointer taken modulo `NREGS`, data auto-increments with wrap-around; every byte ACKed.
  - Bus read `[ADDR+R]`: bytes from the pointer, auto-increment, until the controller NACKs. A repeated START keeps the pointer.
  - Other addresses: not ACKed, transaction ignored.
- **Bus:** open drain; SDA driven low for ACK and data 0; SCL only read (**no clock stretching**). Inputs two-flop synchronized; each SCL low and high phase must last ≥ 4 clocks (at 50 MHz that allows up to ~3 MHz SCL; standard and fast mode are far slower).
- **Host side:** command bytes on `h_w*`: `0000_iiii` + data byte = write register i; `1000_iiii` = read register i (reply on `h_r*`, clears `dirty[i]`). A bus write and a host write to the same register in the same clock: the bus wins. `h_status = {dirty[3:0], overrun, cmd_err, 0, addressed}`.
- **Rates:** RTL simulation only; no chip rates claimed.
- **Known limits:** no clock stretching, no general call, no 10-bit addresses, pointer wraps silently. The phase 4 showcase adds fault injection (selected NACK, inserted stretch) on top of this design.

## Tests
`test/`: cocotb + Icarus, driven by the independent reference **controller** `tools/refmodels/i2c.py: Controller`; a model target at another address shares the bus in one test. Checks: ACK/NACK and bytes seen by the controller, register contents read back through the host commands, dirty bits, bus events (our decoder + sigrok `i2c` decoder), no SDA change while SCL is high except START/STOP.
```
cd test && make            # Q=4; also Q=6, Q=11 (controller phase length in clocks)
```
Covered: bus write → host read, host write → bus read (with sigrok), auto-increment wrap, other addresses ignored (with a second target on the bus), repeated START keeps the pointer, host command errors. Local run 2026-09-25: 18/18 pass.

## Resource use (first profile, 2026-09-25, `synth_fabulous`, Yosys 0.66+179)
| Variant | LUTs | FFs |
|---|---|---|
| `NREGS=4` | 240 | 79 |
| `NREGS=2` | 192 | 58 |

The register map (8 flops per register plus the bus/host access multiplexers) is the largest part; a small register-file primitive is a candidate to measure in profiling.
