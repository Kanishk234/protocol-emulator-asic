# Frozen G1 placement-seed screen

Local run: `compiler_seeds_20261005`, 2026-10-05. Driver:
`spikes/compiler_seeds/run.py`. Sources: unchanged design-set UART, SPI
controller and I2C controller; explicit architecture `arch/warp_g1`.
Pinned project venv and OSS CAD Suite. Per-build tool versions and resources
are recorded in `build/compiler_seeds_20261005/<protocol>/seed<N>/report.json`;
aggregate evidence is `build/compiler_seeds_20261005/summary.json`.

All nine placements route and generate bitstreams. No resource reduction:
UART 29/88 LCs, SPI 47/88, I2C controller 70/88. Each workload has the same
source, parameters, resources and timing model across seeds.

| Workload | Seed 1 model Fmax (MHz) | Seed 2 | Seed 3 |
|---|---:|---:|---:|
| UART | 90.71 | 90.30 | 88.31 |
| SPI controller | 77.97 | 76.77 | 77.36 |
| I2C controller | 52.97 | 52.56 | 52.56 |

Keep seed 1: neither alternate improves model timing on these workloads.
This small screen does not establish a globally optimal seed or achieved
silicon rates. No loaded simulation was performed on these newly generated
images; there is no selected changed placement to promote. It is compilation
evidence only. Future compiler experiments should target logic/resource use,
and retain loaded-behavior checks before claiming an improvement.
