# Current 8x4 route: clean routing, extracted setup failure

[Run 42693952530](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42693952530)
at `ebf817e`, attempt 1, is **FAILURE**. Its restoration/fresh-screen controls
pass, detailed routing completes with zero final route DRC, and the final
antenna/disconnected-pin checks pass. Extraction completes, but the strict
all-corner gate rejects slow setup. No GDS/precheck or release qualification
is established.

| Extracted corner | Setup worst slack (ns) | Hold worst slack (ns) | Slew/cap/fanout |
|---|---:|---:|---|
| Fast | 0 | 0.283984733 | 0 / 0 / 0 |
| Typical | 0 | 0.501490197 | 0 / 0 / 0 |
| Slow | **-1.982448040** | 0.867065555 | 0 / 0 / 0 |

These values come from the retained `corner_summary.json`, raw setup reports
and electrical summaries. The worst examined path launches at `_49313_`, the
U0 `bitsync_active` configuration latch, and ends at `_46985_`, U0 producer
token bit 14. It traverses configuration control, pad selection/feedback and
receive-state logic, with substantial buffering. This is a measured setup
failure rather than a protocol-simulation failure.

**D-066 explicitly permits reconfiguration after pin units become live.**
Configuration-to-state paths must stay timed. Do not convert this result to a
pass by declaring the configuration static or adding a latch-output false path.

## Evidence handling

The source artifact is `13716989088`, 1,386,788,296 bytes, with API digest
`08c1b4d5ef59066d42f35fc1690fe96d79b95af8fb71cbc6a4200b993605664a`.
The job's failure trace confirms extraction finished and the strict slow-setup
gate rejected it. Locally retrieved 18 selected reports using ZIP ranges
(2,119,151 transferred bytes), with per-entry ZIP CRC verification. This partial
download does **not** independently verify the whole-archive digest. The
diagnostic cloud recovery must hash the complete archive before using it.
Raw outputs stay outside Git and in Actions artifacts.

The success-only final replay workflow 42700728949 refuses this source and does
not run protocol tests. That is expected gate behavior, not permission to
bypass the timing failure. The separate pre-DRT native replay remains valid
within its own scope.

## Next measured decision

A read-only fixed-SPEF probe first reproduces the exact 20 ns failure, then
measures 21, 22, 24 and 25 ns using the same netlist, ODB, parasitics, libraries
and preserved signoff SDC. `CLOCK_PERIOD` changes the stock period-derived
constraints too; this is an operating-point sensitivity study, not a
clock-only mathematical extrapolation or a new physical build.

No production clock, RTL, firmware, spec or acceptance gate changes. The
original 20 ns qualification remains failed regardless of diagnostic results.
The measurements will inform whether to refine the critical control path at
50 MHz or propose a lower declared operating target with matching firmware,
tests, full-flow reproduction and documentation.
