# UART (design-set protocol)

User design for the WARP fabric: an 8N1 UART transmitter and receiver.

- **Files:** `uart_tx.v`, `uart_rx.v`, `uart_top.v` (user-design top, provisional interface D-014).
- **Format:** 8 data bits, no parity, 1 stop bit, LSB first, idle high.
- **Baud:** `DIV` clocks per bit (≥ 4). `RUNTIME_DIV = 0` fixes it in the bitstream (recompile to change); `RUNTIME_DIV = 1` loads it from `cfg_div` at run time.
- **RX:** two-flop synchronizer; a start bit is confirmed half a bit after the falling edge (shorter glitches ignored); bits sampled one bit time apart; framing error when the stop bit is 0.
- **Host side:** bytes to send on `h_w*` (valid/ready); received bytes in a one-byte holding register on `h_r*`; `h_status = {5'b0, overrun, ferr, tx_busy}` (overrun and ferr sticky until reset; on overrun the new byte is dropped).
- **Rates:** any integer `DIV` ≥ 4 in RTL simulation. Rates on the chip depend on the fabric clock and place-and-route timing; none are claimed yet.
- **Known limits:** no parity, no 2 stop bits, no break detection, no RTS/CTS.

## Tests
`test/`: cocotb + Icarus against the independent model `tools/refmodels/uart.py`; the TX line is also decoded by sigrok's `uart` decoder.
```
cd test && make            # DIV=16
make DIV=13                # odd divisor
make RUNTIME_DIV=1         # runtime divisor
```
Covered: back-to-back TX (model + sigrok), random TX, RX with gaps, RX with ±3 % baud error, framing error, glitch rejection, overrun, runtime divisor change.

## Resource use (2026-09-25, `synth_fabulous`, Yosys 0.66+179)
| Variant | LUTs | FFs |
|---|---|---|
| `RUNTIME_DIV=0`, `DIV=434` | 144 | 68 |
| `RUNTIME_DIV=1`, `DIV=434` | 262 | 98 |

With a fixed divisor the counters are only as wide as `DIV` needs (9 bits for 434); the first version used 16 bits (171 LUTs). Full breakdown: `docs/reports/profiling.md`.
