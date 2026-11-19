# Real-device capture replay (L3B-DUMPS)

Three complete recordings from sigrok-dumps are pinned at
[0ad13477abc959d37fc9a5acbd23901c371c9c76](https://github.com/sigrokproject/sigrok-dumps/tree/0ad13477abc959d37fc9a5acbd23901c371c9c76).
The manifest binds each SR archive, capture README and upstream license statement.
Raw captures are downloaded into ignored build storage, not committed. See
[reproduction instructions](../../test_internal/captures/README.md).

| Protocol | Recorded hardware | Complete input | Independent result |
|---|---|---|---|
| UART | Olimex STM32-H103 USART1, ChronoVu LA8 | 3,650 samples at 1 MHz; 3.65 ms | 42 bytes: three `Hello World!` CR/LF messages at 115200, 8N1 |
| I2C | NXP PCA9571 access, Hobby Components HCTEST0006 | 150 samples at 2 MHz; 75 us | START, address25/write/ACK, D0/ACK, STOP |
| SPI | AVR/CC1101 traffic, Saleae Logic clone | 497 samples at 16 MHz; 31.0625 us | Five MOSI bytes: F5 00 36 3A 34, mode0 |

These are upstream hardware recordings replayed in simulation. They are not
measurements of fabricated TRIPWIRE, analog pad qualification or complete
PCA9571/CC1101 emulation. Coverage is deliberately finite and small, especially
the I2C and SPI transactions; the rest of the archive is not claimed.

## Timing and oracle independence

The reader preserves every captured sample and all channel levels. Exact integer
arithmetic maps source sample indices onto 50 MHz. Edges are delayed by less than
20 ns without accumulated drift. Entire files are replayed: no rate scaling,
trimming, inversion, idle removal, pulse stretching or ideal bitstream generation.
A constant tail holds the last captured sample while pending work drains. The
bench applies the waveform after normal reset/configuration; its fixed driver
phase offset does not change relative recorded timing.

Sigrok decodes the original SR file independently. UART output is compared byte
for byte. I2C output includes the actual address/RW byte, data, ACK values and
START/STOP order; only the chip's event timestamp is excluded from equality.
SPI compares all decoded MOSI bytes, with original CS gating reception. UART and
I2C use HOST_OUT; SPI uses host SRAM readback. The test's generic `host_tokens`
log count means normalized comparison items for SPI, not HOST_OUT traffic.

Both new receivers own no pads. Every replay clock checks zero UIO output enable.
All expected decoder outputs must be nonempty; missing/modified files, unavailable
decoders, mismatches and RX status flags fail. The reader explicitly rejects
unsupported sample layouts/rates and verifies source hashes before simulation.

## The SPI failure and firmware correction

The first live one-slot SPI forwarder lost3A on RTL. An every-clock model host
had hidden the service constraint. The same original recording through the same
live forwarder with a one-token host queue and1120-clock service reproduces the
missing byte and OVERRUN; every-clock service passes. That negative control is
retained. Its simplified host schedule is not an exact model of every SPI-host
transaction phase.

The corrected firmware uses an existing SRAM store routine. It stores at most
64bytes and never wraps or overwrites code; host reads all64words after traffic,
checking the five payload words and59untouchedFFFFsentinels. Reload before a new
capture. Cost:1lane,3slots,U0,99SRAMwords (32entry+64buffer+3routine). The compiler's
23-clock straight-line store bound has explicit service assumptions and is not a
universal capture-rate guarantee. Model capacity tests cover0/1/64/128bytes and
verify entry/routine regions remain unchanged; excess traffic is outside the
64-byte scope and eventually reports RX overrun. No hardware CAPTURE helper was
added. D-190 records the general need and cost.

## Current evidence

Focused Python checks pass17/17: three original recordings, eight reader/integrity
checks and six buffer/service controls. Verilator passes3/3,0failures/skips in
27.61seconds. Icarus RTL passes3/3in110.09seconds. The final full non-slow Python
regression passes1,145tests in182.84seconds; all17focused checks also pass nightly's
alternate model scheduling mode. Exact official-netlist replay passes3/3with zero failures/skips in287.05seconds.
The L3B-DUMPS checkpoint is checked for these three finite recordings.
The receipt records final status and source/image/log/XML identities. Exact
netlist replay uses official44189196098's unchanged artifact, matching PDK and
Icarus13; it has no SDF and adds no new physical signoff.

Only our unit/nightly workflows, local runner and internal aggregator gain fetch
and replay steps. Official Tiny Tapeout workflows, RTL, macros, physical config,
encodings and previously qualified firmware remain unchanged. No Phase3completion
claim; remaining decoder, metamorphic, formal, compiler and FPGA gates are separate.
