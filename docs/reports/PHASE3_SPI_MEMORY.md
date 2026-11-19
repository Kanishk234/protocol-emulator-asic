# SPI memory showcase

`programs/spi_target_flash.trw` serves a host-loaded volatile SRAM window through
READ and FAST_READ commands. It runs on the unchanged qualified chip using one
lane, U0 for linked MOSI reception and U1 for linked MISO transmission. There is
no host refill during transactions and no dedicated protocol hardware.

**Replay status:** model, Icarus RTL, Verilator and the exact official final
netlist pass. Both chip tests pass on each simulator/artifact, without failures
or skips. This is functional replay on the unchanged qualified physical design.

## Declared interface

- Mode 0, MSB first; MOSI ui0, SCK ui1, active-low CS ui2, MISO uio0.
- READ 0x03: three address bytes followed immediately by read data.
- FAST_READ 0x0B: three address bytes, eight dummy clocks, then read data.
- 256 bytes, addressed modulo 256; address bits 23:8 alias and sequential reads
  wrap within the window. Host updates occur while halted.
- Tested operating domain: SCK 500/333/250 kHz at a 50 MHz chip clock, CS setup
  8 clocks (160 ns), inter-transaction CS-high gap 128 clocks (2.56 us).
- Header/dummy MISO is unspecified and may be driven while selected. MISO
  releases after deselection through the synchronized select path.
- Program, erase, status/ID, other modes and nonvolatile retention are outside
  this personality. Unsupported commands are drained until CS resets the parser.

Command framing follows the manufacturer-authored
[Winbond W25Q16JV datasheet, READ and FAST_READ descriptions](https://www.mouser.com/catalog/specsheets/Winbond%20Electronics%20Corporation_08-25-2025_W25Q16JV.pdf).
The demonstrator's capacity, timing and command subset are its own declared
contract, not the complete device's electrical or functional specification.

## Implementation and cost

The parser distinguishes the two opcodes with a masked comparison, consumes
three address bytes, and loads the indexed byte from SRAM. A flag distinguishes
whether a dummy byte must be consumed. Each completed data byte triggers a
bounded increment/mask/read routine that queues the next response.

The first response needs an explicit falling-edge WAIT. Without it, an early
preload can lose its first bit on the final address/dummy falling edge. The
negative control replaces that WAIT with immediate SYNC and reproduces the
data mismatch. Normal continuation uses the existing linked transmitter's
end-of-byte behavior. The accepted speed must leave time to arm the first WAIT.

Resources: 12/12 slots in L0, four K entries, two existing units, 300/512 SRAM
words (32 entry-table words, 256 data words, 12 routine words). L1 is unused.
D-187 records the general need, implementation choice and scope. No RTL, ISA,
macro, physical configuration, source-list or official workflow change.

## Verification

The independent transaction oracle imports no firmware/compiler/RTL. It checks
command/address/dummy boundaries and expected sequential bytes. A second sampled
wire checker validates MOSI framing, each specified MISO data bit, output enable
at sampling and data setup with one observation clock reserved. Functional
readback checks operate separately from the wire assertions.

Model cases cover both commands, multiple rates and addresses, high-address
aliasing, wraparound, dummy contents, unsupported commands containing embedded
opcodes, and all abort lengths 1–48 bits followed by a fresh opposite command
without reset/reload. The WAIT negative control fails as intended. Required
sigrok decoding checks both directions of an unmodified complete-frame capture.
The full non-slow Python regression passes **939 tests**. Four focused model
cases also check the final direct SRAM-rotation phase variation after that run;
the wire waveform is held fixed while the model's initial rotation phase varies.

Icarus and Verilator each pass 2/2 whole-chip pin tests with no failures/skips: twelve complete
read transactions across three rates, followed by 22 abort/recovery pairs in a
single loaded program. The wire checker validates 2,621 data bits. Required
sigrok runs on all complete-frame rate captures. Partial-frame recovery is
checked by the controller and wire oracle; it is not presented as a complete-byte
sigrok decode. Observed setup lower bounds are 45/70/95 clocks at half-periods
50/75/100. At 500 kHz, 45 sampled clocks correspond to 900 ns under the declared
20 ns clock. These are digital observations, not STA slack or pad measurements.

An additional independent `spiflash` decoder audit checks all six unmodified
complete-read captures from Verilator and the official gate netlist: 24 decoded
READ/FAST_READ commands, their 24-bit addresses, both dummy values and 288
payload bytes agree with the independent memory fixture. This is an offline
capture audit, separate from the required `spi` decode assertions in the tests.

A separate model-only speed experiment passes the checked four-transaction
scenario at half-periods 32–50 and finds counterexamples at 20/25/30. It does not
extend the replayed 500 kHz operating limit or establish an exact maximum across
all traffic and phases. Its outcomes are retained in the evidence receipt.

The exact official-final-netlist replay passes the same two pin-level tests in
666.11 seconds: twelve complete-read transactions at three rates and 22
abort/recovery pairs. Its setup observations match the RTL results. Source,
image, log, capture-audit and XML hashes are in `phase3_spi_memory_result.json`.
Gate replay uses the artifact from official run 44189196098, matching PDK models
and Tiny Tapeout Icarus 13; it has no SDF annotation and is not new hardening.

```sh
source .venv/bin/activate
python -m pytest -q tools/kernels/tests/test_spi_flash.py
make -C test_internal/chip SIM=verilator COCOTB_TEST_MODULES=test_spi_flash
```

Our unit workflow and internal aggregator include the new module under both
simulators. Official workflows are unchanged. The existing 22 firmware image
hashes remain identical; this adds a 23rd program. The combined Phase 3 protocol
exit checkbox remains open until its other showcases and all required evidence
pass; no new whole-program proof, exhaustive-abort, silicon or full-flash claim.
