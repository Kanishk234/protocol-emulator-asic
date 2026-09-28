# SWD host (Arm Serial Wire Debug): held-out protocol H3

Written in phase 4, after `hw-freeze`, for the frozen chip (`docs/design/HELDOUT.md`; results in `docs/reports/heldout_results.md`). The architecture was never tuned for it.

**Split.** The fabric (`swd_top.v`) is SWD's physical layer: SWCLK, SWDIO driven / released / sampled at the right edges, one-clock turnarounds, bits LSB first. The packets are the host's (`tools/board/swd.py`, from ADIv5): request bits and parity, ACK handling (WAIT retried, FAULT cleared with ABORT and reported), data parity, posted AP reads through RDBUFF. This is how debug probes divide the work between a bit engine and firmware; here the "firmware" runs on the host side of the WARP host channel.

- **Pins:** SWCLK on FAB_OUT0 (`uo_out[2]`); SWDIO on FAB_IO0 (`uio[0]`, driven or released). SWCLK = clk / (2 · `HALF`) (`HALF = 5`: 5 MHz at 50 MHz). The target's data is sampled at the end of SWCLK's low half, the host's data changes at the falling edge.
- **Commands** (`h_w*`, bits 7:5 op, bits 2:0 = n − 1): `0x00 | n−1` WRITE n bits (next byte = data, LSB first), `0x20 | n−1` READ n bits (reply's top n bits), `0x40` TURN (one released cycle). `h_status = {5'b0, err, 0, busy}`.
- **Uses:** a WARP hard timer (SWCLK half period) and a hard shift register (the bits), ARCHITECTURE §8; `PRIMS = 0` plain logic.
- **Known limits:** host-channel bound: every 8 bits cost a host transaction, so throughput is set by the host link, not by SWCLK. Parity and packet logic are in host software, not in the fabric (it would fit: the engine uses 44 of 88 logic cells). No SWD multi-drop (DPv2 TARGETSEL) sequence helper.
- **Pin note:** SWCLK on `uo_out` is parked low while the chip is stopped, which is SWCLK's idle level (BUGS #19 does not apply).

## Tests
`test/`: cocotb + Icarus, the design driven by `tools/board/swd.py` (cocotb bridge/resume) against the independent reference target `tools/refmodels/swd.py` (ADIv5: line reset, JTAG-to-SWD, request parity, turnarounds, ACK OK/WAIT/FAULT, DP and AP registers with posted reads; checked on its own against an ideal host in `tools/refmodels/tests/test_swd.py`): connect + DPIDR, AP write/read, WAIT retried, FAULT reported and cleared. `make` / `make PRIMS=1`.
Chip level: `test/test_bitstream.py::test_swd` does the same through the chip's host interface.
