# Reference configuration census

Run `anish-config-20260925-01`, 2026-09-25. This is a source-structure
measurement of upstream FABulous 2.2.0, not WARP physical area or capacity.

## Reproduce

Download the [LUT4AB mapping CSV at the pinned release
commit](https://raw.githubusercontent.com/FPGA-Research/FABulous/432bb2873b83585d5178a8ba411f38254387ce94/fabulous/fabric_files/FABulous_project_template_common/Tile/LUT4AB/LUT4AB_ConfigMem.csv)
into `build/LUT4AB_ConfigMem.csv`. From an activated project venv:

```sh
python -m tools.fabric_audit.configmem build/LUT4AB_ConfigMem.csv \
  --frame-width 32 --frames 20 --expected-bits 616
python -m unittest discover -s tools/fabric_audit -p 'test_*.py' -v
```

Audited input SHA-256:
`3ad7c033ca55110ca6fda7a67f14c4a13047042d75394b8acf307f356223bdb7`.
The audit was run locally with Python 3.12.14. Seven unit tests pass,
including eleven malformed-map cases (duplicates, holes, invalid masks,
missing frames and inconsistent counts). No external Python packages are
needed for the auditor.

## Result

| Quantity, one LUT4AB tile | Count |
|---|---:|
| Frame bit positions, 20 x 32 | 640 |
| Mapped configuration bits, unique indices 0–615 | 616 |
| Padding positions | 24 |
| LUT4 instances in tile definition | 8 |
| LUT truth-table bits, 8 x 16 | 128 |
| Other configuration bits, including modes and routing | 488 |

The [tile definition](https://github.com/FPGA-Research/FABulous/blob/432bb2873b83585d5178a8ba411f38254387ce94/fabulous/fabric_files/FABulous_project_template_common/Tile/LUT4AB/LUT4AB.csv)
contains eight LUT4 primitives plus a mux primitive and switch matrix.
The [LUT primitive](https://github.com/FPGA-Research/FABulous/blob/432bb2873b83585d5178a8ba411f38254387ce94/fabulous/fabric_files/FABulous_project_template_verilog/Tile/LUT4AB/LUT4c_frame_config_dffesr.v)
uses 19 configuration bits: 16 truth-table bits and three mode bits.
The remainder above is deliberately **not** labeled entirely as routing.

Naively counting only truth-table bits undercounts this tile's configuration
by **4.8125x**. Equivalently, 79.2% of its configuration bits are outside
the truth tables. That is a reason to profile routing and modes early,
not proof that 79.2% of chip area is routing or that another LUT size wins.

The CSV's `bits_used_in_frame` field is 32 even on partially populated
frames. The auditor counts the mask and verifies its one-to-one mapping
onto contiguous configuration indices. It rejects a duplicated mapping
even if the total number of entries looks correct.

## Limits

No CMOS5L cell mapping, latch/flop choice, loader, frame-distribution wiring,
I/O/edge tiles, CTS or routing cost is included. Padding positions are
frame capacity, not necessarily implemented storage. The result is not a
bitstream length: packet headers, unused rows/columns and loader framing
add their own transport cost. No 6x4 LUT capacity is claimed.
