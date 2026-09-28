# WS2812 (NeoPixel) transmitter: held-out protocol H1

Written in phase 4, after `hw-freeze`, for the frozen chip (`docs/design/HELDOUT.md`; results in `docs/reports/heldout_results.md`). The architecture was never tuned for it.

- **File:** `ws2812_top.v` (user-design top). `PRIMS = 1`: two WARP hard timers (bit period; high time, whose `half` load gives a 0-bit's 0.4 µs from a 1-bit's 0.8 µs RELOAD) and a hard shift register (the byte), ARCHITECTURE §8. `PRIMS = 0`: plain logic, same behaviour.
- **Line:** `dout_o` (FAB_OUT0, `uo_out[2]`), idle low. Bit period `TBIT` clocks, a 1 high for `T1H` clocks, a 0 for about `T1H / 2`; bytes MSB first (send G, R, B per LED). After a frame's last byte, the line stays low for `RESET_BITS` bit periods (the LEDs latch).
- **Rates (50 MHz):** `TBIT = 62` (1.24 µs), `T1H = 40` (0.80 µs; a 0 is 0.40 µs), `RESET_BITS = 45` (56 µs; use ≥ 230 for WS2812B parts that need 280 µs). Other clocks: scale all three.
- **Host:** bytes on `h_w*` (CH_WRITE), `h_wlast` on a frame's last byte. **Streamed, no pixel buffer:** the fabric has no room for one (8 LEDs = 192 bits against 88 logic cells), so the host must deliver each next byte within one byte time (8 bit periods, ~10 µs). If it is late inside a frame, the line stays low (the LEDs latch what they got), the sticky `underrun` flag is set, and the rest goes out as a new frame. `h_status = {6'b0, underrun, busy}`.
- **Consequence for hosts:** a fast host (e.g. a hardware SPI master at the host port's clk/8 limit: a CH_WRITE every ~5 µs) keeps up; the demo board's bit-banged MicroPython loader (`tools/board/warp.py`) does **not** (milliseconds per transaction) and would underrun after each byte. Not tested on hardware.
- **Known limits:** transmit only; one strand; no on-chip buffer.

## Tests
`test/`: cocotb + Icarus against the independent decoder `tools/refmodels/ws2812.py` (written from the WS2812B datasheet: T0H/T1H windows ±150 ns, bit period 1.25 µs ±600 ns, reset > 50 µs): 8 LEDs in one frame, two frames with the latch between them, host underrun. `make` / `make PRIMS=1`.
Chip level: `test/test_bitstream.py::test_ws2812` loads the bitstream through the host interface and checks 8 LEDs on the pin.
