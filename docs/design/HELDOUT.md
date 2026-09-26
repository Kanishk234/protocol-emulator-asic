# Held-out protocol set (sealed)

**Sealed:** 2026-09-25, phase 1, before any profiling. The commit that adds this file is the seal; its hash goes in the phase 1 checklist.
**Rule (D-003, CLAUDE.md):** until the `hw-freeze` tag at the end of phase 3, nobody writes RTL or reference models for these protocols, profiles them, or tunes the architecture (fabric, hard blocks, I/O cells, routing) with them in mind. If one is touched early, log it in DECISIONS and move it to the design set. In phase 4 each one is written, compiled onto the frozen chip and reported in `docs/reports/heldout_results.md`, failures included.

## The set
| # | Protocol | Why it's in the set | Scope for phase 4 |
|---|---|---|---|
| H1 | **WS2812 (NeoPixel) transmitter** | Timing-coded, output only: each bit is a pulse whose high time encodes 0/1 (~0.4 / 0.8 µs of a 1.25 µs period), plus a ≥50 µs reset gap. Tests fine pulse-width timing with no clock line. | Drive a chain of LEDs from a host-written pixel buffer (GRB, 24 bits per pixel); at least 8 pixels. |
| H2 | **1-Wire controller** | Timing-coded **and** bidirectional on one open-drain line: reset/presence pulse, write-0/write-1 slots, read slots sampled at ~15 µs. Tests open-drain I/O and sampling at a time offset. | Reset + presence detect, byte write, byte read, ROM command `READ ROM` (0x33) against a model device; CRC-8 check of the ROM code optional. |
| H3 | **SWD host (Arm Serial Wire Debug)** | Clocked, with a bidirectional data line and turnaround cycles between host-driven and target-driven phases; odd parity. Tests direction switching and a packet/ACK/data state machine. | Line reset, JTAG-to-SWD sequence, read `DPIDR`, one AP register write and read against a model target; ACK OK/WAIT/FAULT handling. |
| H4 | **CAN 2.0A** | Bit-stuffing (after 5 equal bits), CRC-15, open-drain-style dominant/recessive bus with arbitration and an ACK slot; bit timing from a quantum counter. The hardest of the set; may not fit. | Transmit and receive 11-bit-ID data frames (0–8 bytes) at a rate the chip can reach, with stuffing, CRC and ACK; arbitration loss against a second node. Error frames out of scope. |

Together they cover what the design set (UART, SPI controller, I2C controller, I2C target) does not stress directly: pure pulse-width encoding (H1), time-offset sampling on a shared open-drain line (H2), clocked turnaround (H3), and bit-stuffing with CRC (H4).

## Not in the set (free for the design set or stretch)
PS/2 and JTAG. They stay available as phase 4 stretch protocols (or can join the design set with a DECISIONS entry). They are close to design-set protocols (PS/2 ≈ device-clocked shift register with parity; JTAG ≈ SPI-like clocked shifting), so as held-out tests they would say little.

## Disclosure
The TRIPWIRE design on `main` (a different architecture, by a teammate) has reference models and programs for all four held-out protocols. WARP has not used them. When the set is unsealed in phase 4, WARP writes its own reference models (`tools/refmodels/`) or uses an independent decoder (sigrok), and says which in the results.
