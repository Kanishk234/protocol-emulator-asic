# R1 training connectivity census

Input: authenticated placed user netlists from [39471254787](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39471254787), source5f03060, seed1. These are actual G1 fabric placements, not chip shell or configuration distribution. `tools/profiling/connectivity.py` reads nextpnr endpoint bits, directions and BEL coordinates; constants are excluded. Inputs and full results retained ignored under build/r1_connectivity. Eight focused checker tests pass, including invalid/unplaced data and exact pin/coordinate examples.

| Personality | Signal bits with cell endpoints | Multi-tile bits | Maximum sink pins on one bit |
|---|---:|---:|---:|
| UART | 82 | 54 | 23 |
| SPI controller | 96 | 63 | 27 |
| I2C controller | 114 | 81 | 34 |
| WS2812 | 78 | 45 | 24 |
| 1-Wire | 129 | 90 | 25 |
| SWD | 89 | 59 | 17 |

Counts include clock, reset, I/O and primitive endpoints; they are not arbitrary-data-only fanout. Tile-group summaries also retain 1x1/2x1/1x2/2x2 endpoint grouping anchored to current coordinates. Coarser grouping necessarily reduces the group count; that alone demonstrates no routing improvement, resource saving or winning cluster size. Candidate-specific placement and actual interconnect constraints must be measured. Tile bounding spans are coordinate proxies, not routed length.

This establishes reusable source-bound inputs for a topology/tool screen. It does not measure chip configuration fanout, switch/configuration area, available tracks, physical pin access, clock/NDR usage or simultaneous-workload placement (those workloads do not fit G1). No candidate graph or physical change selected. Next: configuration/switch cost census and explicit generator/nextpnr representation for one routing control and at most two variants, followed by actual workload compilation and representative hardening.
