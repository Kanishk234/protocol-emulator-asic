# TRIPWIRE claims and evidence

Every claim made in the README or the submission, with its evidence and blind spot.
Evidence status is one of: **proven unbounded**, **proven bounded (depth N)**, **tested**, **simulated only**, **not yet verified**.

Never claim: zero latency, sub-ns timing, USB/Ethernet support, real-hardware testing, or "formally verified" without naming the property and its bound.

| # | Claim | Evidence (check ID, run, file) | Status | Blind spot |
|---|---|---|---|---|
| 1 | The chip RTL runs `programs/uart.trw`, `spi_controller.trw` and `i2c_controller.trw` loaded through its SPI host link: UART TX at 9600, 115200 and 1 Mbaud, UART RX at 115200 and 460800 baud with framing errors reported, SPI controller mode 0 at 1, 5 and 8.3 MHz, I2C controller at 100 kHz, ~400 kHz and 1 MHz with clock stretching (up to longer than an SCL period), NACK and repeated START | L3 on `trw_chip` through the pins (`test_internal/chip/test_l3.py`), each against a reference model (`tools/protomodels`) **and** sigrok's decoder; RTL and the Yosys gate-level netlist (TT Icarus 13), 2026-09-27, local runs (WORKLOG) | simulated only | Not yet on the hardened netlist (the top is not switched, D-047); no hardware. Not covered (the shipped programs do not implement them, D-048): UART parity, SPI modes 1–3 and 16-bit, I2C arbitration loss. Continuous UART RX above ~460 kbaud overruns (see Known limits) |

## Known limits (state them wherever the related claim appears)

- **Host link throughput.** At SCK = clk/8 (the §9 limit) one HOST_OUT read (status and data in one transaction) takes ~560 clocks, so the host drains at most ~89K tokens/s at 50 MHz. A program that turns every received byte into a HOST_OUT token overruns its pin unit (§4.5: the new token is dropped and OVERRUN set) when bytes arrive faster than that: continuous UART RX above ~460 kbaud (a byte every ~1,085 clocks). Found by L3 on the RTL, 2026-09-27. Faster streams need buffering in firmware (a lane or SRAM ring) or a faster host clock.
