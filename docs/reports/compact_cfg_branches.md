# Local configuration-index branches

2026-10-05. Scratch D-040 experiment; frozen G1 unchanged.

Read-only diagnosis found a long frame_idx[1] branch with Metal3 antenna
violations and decoder loads spread across the chip. This variant splits
decoder loads of frame_idx bits0/1 into per-column local buffer branches.
It adds14 non-inverting buf_2 cells,127.008µm² before later repair. Supply
pins connect to VPWR/VGND and the buffers join existing decoder groups.
There are no new user resources, state registers or bitstream fields.

Compared with the existing shared-CRC candidate on the identical
1120.32 × 676.62µm macro,20ns clock target,0.1ns hold margin and21.12µm
row fences:

| Metric | Shared CRC | Shared CRC + local branches |
|---|---:|---:|
| GRT overflow | 93 | 27 |
| Estimated wirelength (µm) | 285,645 | 281,448 |
| Post-CTS hold buffers | 512 | 522 |

Evidence directories under `build/arch_explore/compact_edges/`:
`chip_shared_crc_physical/runs/compact_local_grt` and
`chip_shared_crc_cfgbranches/runs/compact_local_grt`, especially steps09
timing repair and11 global routing. The zero-overflow guard correctly stops
the driver. `cfgbranches_drt_screen` is a separate two-iteration screen with
post-DRT antenna repair disabled; it cannot establish a physical pass.

Actual post-CTS mapped shell, including all14 added buffers, passes real
842-word SPI load, UART transmit/receive and STOP parking:23.92seconds,
`simulation_chip_shared_crc_cfgbranches_mapped_shell/results.xml`.
This uses RTL fabric, Icarus13/cell models, no SDF and existing D-023
combinational-loop handling. It is a functional test, not configuration
setup/hold signoff, full mapped-fabric proof or an exhaustive load proof.

The tighter macro separately completes stitched KLayout DRC0 at
1120.32 × 669.06µm (`compact_edges_tighter/runs/tighter_stitch_20261005`),
and its full SPI/UART/STOP RTL regression passes15.74seconds
(`compact_edges_tighter/simulation/results.xml`). Fresh input-use tracing
confirms160/160 data inputs and92/140 strobes consumed with source hashes.
The matched GRT screen with the same sharedCRC/local-branch shell reaches
zero overflow,276069µm estimated wirelength and522 hold buffers. Its
zero-overflow guard passes and full stock detailed routing starts as
`compact_edges_tighter/chip_shared_crc_cfgbranches/runs/compact_local_route`.
Changing macro geometry is its sole new variable.
No geometry is selected before the full-chip checks.

Optional reproduction: run `spikes/compact_edges/route.sh` with the existing
sharedCRC/locality/Metal1/early-release flags plus `WARP_CFG_BRANCH_BUFFERS=1`,
using a fresh chip directory. The flag is off by default. The branch script
fails on missing nets/cells/supplies and repeat application. Always retain
the overflow guard and all signoff checks for full runs.

The pinned router supports jumper-only repair, but a copied initial-DRT
snapshot probe leaves the same1net/2pin detailed antenna violations. No
full-flow improvement is established; do not present this probe as a fix.
Further details: [routing diagnosis](compact_route_diagnosis.md).

The lead-geometry branch screen begins at5626 initial DRT markers versus
5010 for sharedCRC without branches. This cautions against inferring detailed
routing success from improved GRT; compare completed optimization stages.

## Latest full-route status and restart

The tighter local-branch baseline completes at144 DRC markers and zero
antenna nets/pins; it fails routing. Exact native report and endpoint audit
are in `compact_route_diagnosis.md`.

D-041's separate preplaced-diode variant passes loaded mapped-shell/RTL-fabric
SPI/UART/STOP testing (25.28s), and GRT reaches zero overflow,275796µm
estimated wirelength and514 hold buffers. Its full route was interrupted by
the daemon restart during early optimization. No process survived; incomplete
reports are retained. On2026-10-05 the unchanged experiment restarts from
`runs/compact_local_route/04-openroad-detailedrouting/state_in.json` with fresh
tag `compact_diodes_drt_restart_20261005`, stock checks and the same config.
It remains active and has no final physical/timing pass. The reset/enable/FSM
compiler screens and fault-monitor work use different sources/directories.
