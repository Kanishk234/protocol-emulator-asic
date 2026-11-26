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
