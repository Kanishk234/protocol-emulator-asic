# SPI controller (design-set protocol)

User design for the WARP fabric (soft logic; see `../README.md`): the SPI side that drives SCK and chip-select.

- **File:** `spi_ctrl_top.v` (user-design top, provisional interface D-014).
- **Modes:** `CPOL`, `CPHA` parameters, all four modes; MSB first; 8-bit bytes; full duplex.
- **Speed:** SCK half period = `HALF` clocks, **`HALF` ≥ 4** (SCK ≤ clk/8): MISO goes through a two-flop synchronizer and a target may take up to one clock to change MISO after its change edge.
- **Host side:** bytes to send on `h_w*`; `h_wlast` ends the transaction after that byte (CS released, then CS stays high for half a period). Between bytes of a transaction CS stays low and SCK idle until the host sends the next byte. Each transfer's received byte goes to a one-byte holding register on `h_r*`. `h_status = {6'b0, overrun, cs_active}` (overrun sticky; the new byte is dropped).
- **Rates:** RTL simulation only; no chip rates claimed.
- **Known limits:** one chip-select; 8-bit words only; no 3-wire (bidirectional MOSI) mode; mode fixed in the bitstream.

## Tests
`test/`: cocotb + Icarus. MISO is driven clock by clock by the independent SPI target model (`tools/refmodels/spi.py`); every run checks what the target received, what the host got back, the waveform decoded by our decoder and by sigrok's `spi` decoder (MOSI and MISO), and that SCK sits at CPOL whenever CS is high.
```
cd test && make MODE=0      # MODE = 0..3, optional HALF=5
```
Covered: two transactions, host stalls between bytes (CS held), random bytes, overrun. Local run 2026-09-25: MODE 0–3 at HALF=4, MODE 1 at HALF=5, MODE 2 at HALF=7: 24/24 pass.

## Resource use (first profile, 2026-09-25, `synth_fabulous`, Yosys 0.66+179)
| Variant | LUTs | FFs |
|---|---|---|
| mode 0, `HALF=4` | 85 | 42 |
| mode 3, `HALF=4` | 85 | 43 |
| mode 0, `HALF=25` | 100 | 45 |
