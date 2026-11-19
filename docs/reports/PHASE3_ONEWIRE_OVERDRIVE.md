# 1-Wire standard and overdrive profiles

`onewire_master.trw` supplies standard (`OVERDRIVE=0`) and overdrive
(`OVERDRIVE=1`) timing profiles on the existing controller primitives. Its
default encoded configuration, slots, constants and SRAM match the retained
`onewire.trw`. Model, Icarus RTL, Verilator and exact official final-netlist
replay pass. Both chip tests pass on each simulator/artifact without failures
or skips. This is functional replay on the unchanged qualified design.

## Interface and timing

DQ is open-drain uio0 with an external pull-up. Host DATA writes a byte, CTRL 0
resets/checks presence, and CTRL 1 reads a byte. Presence returns DATA 0 for an
answer or DATA 1 for none. The host changes profiles only after the pin timeline
is idle. The test keeps the peer alive across those real host reloads.

Configured timings follow [Analog Devices AN126](https://www.analog.com/en/resources/technical-articles/1wire-communication-through-software.html).
Mode entry and device bounds follow the [DS2431 rev16 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/DS2431.pdf).
At the declared 50 MHz clock:

| Quantity | Standard | Overdrive |
|---|---:|---:|
| Timer tick | 1 us | 0.5 us |
| Write-one low / recovery | 6 / 64 us | 1 / 7.5 us |
| Write-zero low / recovery | 60 / 10 us | 7.5 / 2.5 us |
| Read low / sample from slot start | 6 / 15 us | 1 / 2 us |
| Read-slot duration | 70 us | 9 us |
| Reset low | 480 us | 70 us |
| Presence sample after release | 70 us | 8.5 us |
| Reset release-to-next-slot interval | 490 us | 48.5 us |
| Additional pre-reset gap | 0 | 2.5 us |

The pre-reset gap ensures at least 5 us recovery after an immediately preceding
overdrive write-zero. Uniform tenfold scaling would give an invalid 0.6 us
write-one low. The model waveform audit observes 3,500 reset-low clocks,
50/375-clock write low intervals, and 64 read lows of 50 clocks with 450 clocks
between starts. These are ideal digital measurements, not pad characterization.

## Verification

The sequence is standard reset and 0x3C entry, idle reload of the fast profile,
overdrive reset and 0x33 ROM read, then idle reload and standard reset/read.
The peer's mode is never set directly. A standard reset exits overdrive.

The original DS18B20-like standard-only model is unchanged. The new independent
ROM-layer peer implements only 0x33 and 0x3C, with explicit speed state and a
family-0x2D ROM/CRC. It is not an EEPROM-function model. It releases read-zero at
the sampling endpoint, so a late sample cannot pass by relying on a long zero.
Moving the fast sample one 0.5 us tick later breaks readback as intended.

Tests cover all four overdrive presence-delay/width corners, absence, reset
without prior entry, write-slot bounds and pre-reset recovery. A synthetic
previously-low disconnection test corrected a peer drive-state inconsistency
before publication; the final runs use that correction. The full non-slow Python
suite passes **952 tests**. Required sigrok decodes the complete unmodified
standard/overdrive/standard capture, including entry and both complete ROMs.

Icarus and Verilator each pass 2/2 chip tests without failures/skips. They use
only host/pin ports, preserve the peer across reloads, check both ROM reads,
all four presence corners, absence and entry requirements, and require zero pin
status flags. Exact observed reset lows are 24,000 / 3,500 / 24,000 clocks.
Our unit workflow/internal aggregator include the module under both simulators;
official workflows are unchanged.

### Stock decoder recovery warning

An additional link-layer audit retains one stock sigrok warning after the
overdrive reset. The actual capture has 28.48 us high between the presence
pulse ending and the first command slot, and 48.5 us from reset release to that
slot. The decoder replaces the last real rising edge with a synthetic 48 us
reset-window endpoint, then checks recovery against that invented timestamp.
It therefore reports 0.5 us instead of the actual 28.48 us. Both completed RTL
captures and the official gate capture are byte-identical and show the same edge relationship.

An independent ideal waveform control reproduces the warning with 28.5 us
actual recovery / 48.5 us reset high. Adding one microsecond removes it. Both
controls satisfy the actual timing constraints; the false warning comes from
the decoder's bookkeeping. The source hash, raw warning, capture hashes and
controls are retained in the receipt. The stock decoder and tested chip
waveforms are unchanged; semantic decoding and physical-edge assertions remain
active. This explains that specific warning, not arbitrary future warnings.

`phase3_onewire_overdrive_result.json` binds sources, compiled profiles,
waveform/decoder audits and log/XML evidence. The gate replay passes 2/2 tests
in 785.83 seconds using the unchanged official run 44189196098 artifact,
matching PDK models and Icarus 13, without SDF or a new physical run.

## Cost and scope

Each profile uses one lane, nine slots, four K entries, existing full unit U0 and
51 SRAM words including the 19-word reset routine (D-188). Previous 23 firmware
images remain identical; this adds one parameterized program. No RTL, encoding,
macro, physical configuration or official workflow change.

Scope is ideal digital single-peer ROM-layer interaction and tested controller
timing. Multidrop discovery, other device functions, parasite power, RC rise
time, characterized pads and silicon testing are outside this evidence. The
combined protocol checkpoint stays open for the PS/2 framing/capture audit.

```sh
source .venv/bin/activate
python -m pytest -q tools/kernels/tests/test_onewire_overdrive.py
make -C test_internal/chip SIM=verilator COCOTB_TEST_MODULES=test_onewire_overdrive
```
