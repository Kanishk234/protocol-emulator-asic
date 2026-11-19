# Two-lane L4-LOOP and L4-IDLE

This milestone exercises real transmit/receive paths on both existing lanes.
It covers finite LOOP/IDLE workloads for UART, mode0 SPI and I2C. It does not
complete SCALE/PERM or the overall L4/Phase3exit criteria. Production programs,
RTL, physical configuration, macros, encodings and official workflows are unchanged.

[Test-only firmware](../../test_internal/firmware/README.md) is compiled and loaded
through the ordinary host interface. Baseline and idle variants use the exact
same image. There are no injected internal RX tokens or hierarchical RTL accesses.

| Protocol | Actual loop and host result |
|---|---|
| UART | L0 TX/U0/uo0 to ui0/U1/L1 framing check; valid byte returns on HOST_OUT |
| SPI | Existing controller outputs MOSI on uo1, looped to ui0 MISO; L0 handles transfer completion and L1 forwards RX |
| I2C | L0 controller and L1 target share SCL; their separately owned SDA pads are tied open-drain by the environment. Write one byte, repeated START, read it back, NACK and STOP. Three zero ACK tokens and the byte return to the host |

The I2C target holds only the last written byte in r1. It is test firmware, not
additional memory-device support. Costs fit the qualified design: UART1/3slots,
SPI4/1slots, I2C11/12slots; two/four/three units respectively. I2C uses62SRAMwords
for the entry table/controller routines; UART/SPI do not use routines. No area,
clock or timing-constraint changes are involved.

## Metamorphic comparisons

Each model profile sends00 FF 01 80 55 AA 3C C3 with no added idle and with seeds
7129/19317. UART profiles are115200/460800baud; SPI periods50/10/6clocks; I2C
periods500/124/50clocks. These are eight profiles and24complete runs, each with
eight round trips. A one-token host queue is drained every560clocks; the model
queues upstream host commands while the chip accepts them normally.

Random idle is inserted only after a completed frame/group and a fixed settling
guard. The original byte stream and program do not change. Both seeded runs must
return exactly the baseline sequence. Raw wire markers must have the same first
frame start but different later starts, proving that real inter-frame timing was
perturbed, rather than merely extending an idle trace tail. UART guards allow
its final stop bit to finish; I2C waits for the final STOP, not just receipt of
the last data byte. Delays are bounded test stimuli, not a universal idle envelope.

Independent sigrok decodes actual unchanged pad samples. UART TX/RX and SPI
MOSI/MISO must each equal the payload. I2C write/read payloads and repeated
START/STOP counts must match. Pad-drive checks enforce open drain; RX/TX flags
must remain clear. Disconnecting each protocol's loop must fail via timeout or
wrong return data; these three negative controls prevent direct host forwarding
from masquerading as a wire round trip.

Focused Python checks pass11/11in27.75seconds. Each of the eight positive tests
runs three timing variants; the three disconnected controls are separate. The
alternate scheduler also passes11/11in22.04seconds. A new recorder bug was caught
by these checks: its VCD omitted the already-simulated constant tail duration.
The fix writes the actual final sample timestamp, without adding a signal edge
or modifying the waveform. The last byte and STOP must now independently decode.

## Chip-port evidence status

The chip tests run the same fixture with00 FF 55 AA, once with baseline timing
and once with seed7129. Profiles are UART460800, SPIperiod10 and I2Cperiod124.
The real host driver feeds commands and reads replies; actual guard/idle clocks
are held between complete groups. Every captured direction is independently
decoded and host results/flags are checked. The idle variant must move later
wire frame starts and preserve the first start and returned byte sequence.

Verilator passes3/3paired cases with0failures/skips in22.67seconds; Icarus RTL
also passes3/3in109.56seconds. The full non-slow Python suite passes1,175tests
in189.34seconds. Exact official-netlist replay also passes3/3with zero failures/skips
in417.66seconds. All six capture hashes and frame-marker lists match across
Verilator, Icarus RTL and the official netlist. Receipt phase3_metamorphic_loop_idle_result.json records their actual
status and source/image identities. A supplementary audit of all six I2C
chip captures confirms address0x50in both directions,12ACKs/4NACKs and four
START/repeated-START/STOPgroups per capture, without changing any waveform. Exact-netlist replay
uses official44189196098's unchanged artifact, matching PDK and Icarus13without
SDF. These are digital simulated loops, not silicon, analog-pad or external-device
interoperability measurements.

Own unit CI/internal aggregator include the chip suite; pytest/nightly discover
the model checks. The LOOP/IDLE progress is separate from the still-open full L4
checkbox. SCALE must account explicitly for fixed control latency, and PERM must
respect legal routing/rotation premises. No verification requirement is relaxed.

```sh
source .venv/bin/activate
python -m pytest -q -rP tools/kernels/tests/test_metamorphic_loop.py
make -C test_internal/chip COCOTB_TEST_MODULES=test_metamorphic_loop
```
