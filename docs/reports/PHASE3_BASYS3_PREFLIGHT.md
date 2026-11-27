# Phase 3 Artix-7 synthesis preflight

The current two-lane, four-pin-unit design mapped successfully to Artix-7
primitives in Yosys 0.69+24. The runner reads the source list from
`info.yaml`, enables the FPGA storage options, substitutes the FPGA
SRAM wrapper, and checks that the result has one `RAMB18E1`.

| Synthesis resource | Count |
| --- | ---: |
| Estimated logic cells | 7,669 |
| LUT primitives | 9,380 |
| Flip-flops | 4,335 |
| Block RAMs | 1 |

The SRAM comparison passed 11,024 read and hold observations across all
512 addresses against the ASIC behavioral macro and a reference array.

From the repository root, with Icarus and Yosys available on PATH, run:

```bash
source .venv/bin/activate
scripts/check_fpga_sram.sh
python scripts/check_basys3_synthesis.py
```

This preflight excludes board I/O mapping and physical implementation.
D-022 still names three lanes and six pin units. Before closing the
Basys 3 gate, resolve the intended size and validate the board pin map,
clocking, bitstream and 50 MHz routed timing for that target.


The board adapter in `fpga/basys3/tripwire_basys3.v` maps inputs to JA,
outputs to JB and bidirectional pads to JC, each in the header's
1–4, 7–10 order. For the SPI host, CS_n, SCK and MOSI are JA7, JA8 and JA9,
MISO is JB4, and IRQ is JB9. The matching XDC uses the
[Digilent Basys 3 rev B map](https://github.com/Digilent/digilent-xdc/blob/master/Basys-3-Master.xdc).
The clock constraint is 10 ns at W5. The MMCM multiplies by 10 and divides
by 20 to yield 50 MHz. The center button or loss of lock asserts reset,
and the chip leaves reset after two 50 MHz edges. The adapter disables
bidirectional output drivers while reset is asserted.

Use `python scripts/check_basys3_synthesis.py --board` in the project
venv to map the board top. The synthesis check requires one clock
manager, eight bidirectional buffers and one block RAM. A local Icarus
smoke test with behavioral primitive stubs exercised lock and button
reset, synchronized release and direction control. Board implementation
and 50 MHz routed timing remain unverified.

With Vivado and its Artix-7 device support available, run
`python scripts/build_basys3.py` from the project venv. The runner imports
the project's source list and builds for the Basys 3
[XC7A35T-1CPG236C](https://digilent.com/reference/_media/reference/programmable-logic/basys-3/basys3_rm.pdf).
Each run writes its route status, utilization, timing and DRC reports and
routed checkpoint to a fresh directory under `build/`. The Tcl driver
checks the generated 20 ns clock and internal setup and hold slack
before writing the bitstream. Pmod timing depends on external equipment,
so inspect the unconstrained paths in the timing report when planning
a board test. The Tcl driver and XDC ran with stub commands that checked
package-pin uniqueness and verified that negative hold slack and an
incorrect clock period prevent bitstream generation. Vivado was absent
locally, so actual implementation and timing remain open.

The runner also detects Windows Vivado under WSL. It checks the AMD and
legacy Xilinx install layouts on C:, starts the batch file through
`cmd.exe` from `/mnt/c`, and passes translated source and output paths
to Tcl. Windows Vivado 2025.2 opened the WSL source tree and entered
Artix-7 synthesis. The first live run exposed an XDC parsing restriction
and Vivado's MMCM primitive rewrite. The corrected XDC uses explicit
package assignments and timing checks accept the mapped MMCM primitive.

## Routed 50 MHz baseline

Windows Vivado 2025.2 completed implementation and bitstream generation
for the full board design published at `447bd2e`. The local run
`build/basys3-vivado-jv8af139` reported a 20.000 ns generated clock,
+3.063 ns setup slack, +0.102 ns hold slack, zero failing timing endpoints,
and all 12,010 routable nets routed with zero routing errors. Bitstream
DRC reported zero errors. The bitstream SHA-256 is
`b8be343b8a6b58bff4f1eb2b93bdcd8a21cbf0971fb7836e0872500ac4a22c62`,
and the routed timing report SHA-256 is
`48ac5b47e5c3de226f0b6712d08ba259d43c9d193c03eb289882b900df2cc5d1`.
External Pmod timing and physical board testing are outside this result.

Vivado's standalone DRC reported REQP-1840 on the asynchronously asserted
reset path to the block RAM enable. A board-only follow-up registers the
core reset synchronously and retains immediate bidirectional output
disable. Its behavioral smoke test passed and a new Vivado implementation
run has started. The routed numbers above apply to the published baseline.

The synchronous-reset follow-up completed in Vivado 2025.2. All 12,009
routable nets routed without errors. The 20 ns clock met setup and hold
with +3.226 ns and +0.075 ns worst slack and zero failing endpoints.
The DRC report found zero violations, including no REQP-1840, and
bitstream generation succeeded. Local run: `build/basys3-vivado-m0q1g8ok`.

| File | SHA-256 |
| --- | --- |
| Board adapter RTL | `251ac5eb7ea20ac8b8854c7a2cfd7a5fe6370161ce604cc4e35f5e3df57e83f5` |
| Bitstream | `b4b1b215a7160cb2f6bd7730795d1ec97c03fee301bcc5a1f82cb260a915e23f` |
| Timing report | `5b2adc87ac2228c7b3a20250429d994b1442ac1478b2fe63703141ad38856256` |
