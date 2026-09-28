# Held-out protocols on the frozen chip (phase 4)

**Chip:** G1 as frozen (`hw-freeze` → 3047dea; 88 LUT4 + 2 timers + 2 shift registers, D-033). **Set:** `docs/design/HELDOUT.md`, sealed 2026-09-25 before profiling, unsealed 2026-09-28 after the freeze; nothing in the architecture was chosen with these in mind (D-003). **Method per protocol:** an independent reference model written first from the protocol's own specification (`tools/refmodels/`), then the user design, RTL tests against the model in both forms (hard primitives / plain logic), compile onto the frozen fabric and onto G0 (the plain-LUT baseline at equal area) with the same flow, and a chip-level test through the host interface. Fmax is nextpnr's estimate at the slow corner (a model, `tools/timing/README.md`), not a claim.

| # | Protocol | Fits G1? | G1 LCs (timers, shifts) | G1 Fmax | G0 LCs (plain) | G0 Fmax | RTL tests | Chip test | Limits found |
|---|---|---|---|---|---|---|---|---|---|
| H1 | WS2812 transmitter | **yes** | 32 of 88 (2, 1) | 54.3 MHz | 82 of 96 | 55.9 MHz | 3/3 both forms vs datasheet decoder | `test_ws2812` (8 LEDs through the host channel) | no on-chip pixel buffer: the host must stream a byte per ~10 µs (a bit-banged board host cannot) |
| H2 | 1-Wire controller | **yes** | 77 of 88 (2, 1) | 54.5 MHz | 126 of 96: **no fit** | - | 5/5 both forms vs reference device | `test_onewire` (READ ROM, CRC-8, open-drain pin) | ROM search not supported; standard speed only |
| H3 | SWD host (bit engine + host packets) | **yes** | 44 of 88 (1, 1) | 54.4 MHz | 61 of 96 | 56.0 MHz | 4/4 both forms vs reference target, driven by the host library | `test_swd` (connect, DPIDR, AP write/read, WAIT) | packets, parity and ACK handling in host software, not in the fabric |
| H4 | CAN 2.0A | **no** | 207 of 88 (2, 1) | - | 241 of 96: no fit | - | 3/3 both forms vs reference nodes (TX+ACK, RX with stuffing, arbitration + retry) | none (does not fit) | about 2.4 × the fabric: frame parser (bit position arithmetic, CRC-15, stuffing, DLC-dependent field ends) |

## H1: WS2812 (NeoPixel) transmitter
- **Reference:** `tools/refmodels/ws2812.py`, a decoder written from the WS2812B datasheet (T0H 0.4 µs / T1H 0.8 µs ±150 ns, period 1.25 µs ±600 ns, reset > 50 µs); it reports every pulse outside the windows.
- **Design:** `protocols/ws2812`. The timer's `half` load (made for UART mid-bit sampling) gives a 0-bit's high time from the 1-bit's RELOAD, so one timer covers both pulse widths.
- **Found while testing:** a design bug (a frame's last byte could chain straight into the next frame without the latch gap; fixed) and a timing restructure (the period timer's enable tied high: 42.5 → 54.3 MHz on G1).
- **Generalization:** the primitives cut the design from 82 LCs (G0) to 32 (G1).

## H2: 1-Wire controller
- **Reference:** `tools/refmodels/onewire.py`, a device written from the 1-Wire standard-speed timing (AN126, DS18B20 datasheet): presence 30 µs after the reset's release for 120 µs, write slots sampled at 30 µs, read-slot 0s held for 30 µs, READ ROM with CRC-8; checked against an ideal master written from the same timing.
- **Design:** `protocols/onewire`. Both timers used: a 1 µs tick, and a microsecond one-shot whose `half` load gives the 480 µs reset pulse and full load the 960 µs recovery, so the slot counter only counts to 70.
- **Found while testing:** the first version needed 116 LCs (a 10-bit microsecond counter compared against seven times, reply multiplexing); restructured with the second timer and a leaner host interface: 77 LCs. A 7-bit counter wrapping during the 960 µs recovery re-sampled presence (caught by the reference device; fixed with a sample-once flag).
- **Generalization:** fits G1 (77 of 88), not G0 (126 of 96): the primitives decide whether it runs.

## H3: SWD host
- **Reference:** `tools/refmodels/swd.py`, a DP + AP target written from ADIv5 (line reset, JTAG-to-SWD 0xE79E, request parity/stop/park, turnaround cycles, ACK OK/WAIT/FAULT with WAIT and FAULT injection, DPIDR/CTRL/SELECT/RDBUFF, posted AP reads); checked against an ideal host written from the same spec.
- **Design:** `protocols/swd`: the fabric is the physical layer (bit engine: WRITE n bits, READ n bits, TURN); the packets are `tools/board/swd.py`. **Honest scope:** the protocol decisions (parity, ACK, retries) run in host software, as in a debug probe's firmware, not in the fabric. The engine leaves 44 of 88 logic cells free, so moving parity and the packet sequence into the fabric looks possible but was not done.
- **Generalization:** fits both fabrics (G1 44, G0 61); the primitives save 17 LCs here.

## H4: CAN 2.0A
- **Reference:** `tools/refmodels/can.py`, a node written from the Bosch CAN 2.0 specification (base data frames, stuffing including after the CRC, CRC-15, arbitration, ACK slot, EOF + intermission, bus integration, hard synchronization); tested node to node, with arbitration and a lone transmitter getting no ACK.
- **Design:** `protocols/can`: one frame parser for both roles, both timers (sample point, bit boundary), the shift register for the bytes. Correct in RTL against the reference (both forms). **Does not fit:** 207 LCs on G1, 241 on G0 (the primitives save 34 LCs, not enough); the held-out list expected this as possible ("the hardest of the set; may not fit").
- **Found while testing:** a transmit bug (the first bit of every byte after the first went out from the old shift register when a new byte was loaded; the reference receiver decoded a valid frame with the wrong bits, which the byte-level check caught; fixed).

## Summary
| | H1 WS2812 | H2 1-Wire | H3 SWD | H4 CAN |
|---|---|---|---|---|
| runs on the frozen chip | yes | yes | yes (bit engine + host packets) | **no** |
| G1 LCs / 88 | 32 | 77 | 44 | 207 |
| G0 LCs / 96 (plain logic) | 82 | 126 (no fit) | 61 | 241 (no fit) |
| hard blocks used (timers, shifts) | 2, 1 | 2, 1 | 1, 1 | 2, 1 |
| Fmax model (G1) | 54.3 MHz | 54.5 MHz | 54.4 MHz | - |

- **Three of four held-out protocols run on the frozen chip**; the design set (UART, SPI, I2C controller) was the only thing the architecture was tuned on (D-003).
- **The primitives generalized:** every held-out design uses the timer and the shift register, in ways the design set did not (a pulse-width generator from the timer's `half` load; a microsecond one-shot for a 480 µs pulse; an SWD bit clock; a CAN sample point). They cut the logic by 17–50 LCs per protocol, and they decide whether 1-Wire fits (77 vs 126).
- **What limits generality:** capacity. CAN's frame parser is ~2.4 × the fabric; 1-Wire uses 88 % of it. Timing is not the limit once designs avoid combinational paths through a timer (WS2812: 42.5 → 54.3 MHz by tying the period timer's enable high).
- **Honest scope notes:** SWD's packet logic runs in host software; WS2812 needs a host that streams a byte per ~10 µs (no pixel buffer); CAN has no error frames; nothing is tested on hardware.
