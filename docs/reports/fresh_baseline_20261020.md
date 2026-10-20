# Fresh-candidate baseline: measured resource requirements

Compiler job in [39470166731](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39470166731) succeeds at fc7a3ac6564c0d9138b6adc63518bc6e581b1847, attempt1. The overall workflow fails separately because the simulation/checker job omits fabulous-fasm; that failure is not a passing RTL job. Fix ad5c445 adds the pinned dependency; retry pending. Current local workload simulation passes16 mode/primitive combinations, and the evidence checker has24 passing tests after portable source-byte verification was added.

## Authenticated compiler outcomes

Same G1, source revision, seed1, slow-corner compiler model and 50MHz assessment target. Concurrent parameters: UART DIV434, SPI HALF25, mode0; two-byte host framing identical in all forms. Physical timing and actual loaded-fabric operation were not measured by this campaign.

| Workload | Fit | Placed cells or synthesis demand | Timers/shifts | Model Fmax MHz |
|---|---|---:|---:|---:|
| UART | yes | 29 placed | 2/2 | 90.71 |
| SPI controller | yes | 47 placed | 1/1 | 77.97 |
| I2C controller | yes | 70 placed | 1/1 | 52.97 |
| WS2812 | yes | 32 placed | 2/1 | 54.34 |
| 1-Wire | yes | 77 placed | 2/1 | 54.48 |
| SWD | yes | 44 placed | 1/1 | 54.35 |
| Four-register I2C target | no | 169 demand | 0/1 | — |
| UART+SPI, both hard-backed | no | 103 demand | 3/3 | — |
| UART+SPI, hard UART/soft SPI | no | 138 demand | 2/2 | — |
| UART+SPI, soft UART/hard SPI | no | 195 demand | 1/1 | — |
| UART+SPI, both soft | no | 233 demand | 0/0 | — |

Rejected cases retain genuine native overcapacity and placement fatals. No nonfit is described as placed/routed. The all-hard concurrent workload exceeds G1's88cells and2/2primitives; the mixed2/2 version exceeds its cells. These are exact workload results, not proof that no other concurrent implementation can fit G1.

## Independent downloaded-artifact audit

Retained ignored directory build/fresh_baseline_hosted. Local direct Git-object audit validates360 source/library hashes against the exact producer revision and pinned fabulous-tiles7999e5a91dab77357fe9d401b6dfb0758f438bf1;139 per-case artifacts match their hashes. All11 cases revalidate native diagnostics/usage, parameters and successful image CRC/version/word counts. Report build/fresh_baseline_hosted/independent-audit.json. Tools are the pinned Yosys0.66+179 e74db6dea and nextpnr0.11.1-34-gc4fbb55a; this remains compiler fit/model evidence, not physical qualification.

## Consequence for R1

Reject the unmeasured assumption that112–128cells plus the original2/2primitives automatically delivers the primary gain. The measured2/2 implementation demands138cells before placement. A3/3 implementation demands103, but needs extra reusable primitives and adequate routing. Existing primitive tiles provide pairs, so screen the area/tool implications of a denser3/3 arrangement versus existing4/4 availability; do not select either without full-cost measurement. A103-cell estimate near a104-cell capacity is not a comfortable routability result.

The combined103 demand exceeds the separate29+47 counts by27cells under this flow, illustrating composition/host/packing cost; do not identify all27 as a measured physical host-arbiter area. Next: UART+I2C characterization and area/connectivity census, fresh evaluation sealing, then a written candidate specification. Production architecture unchanged; no phase box or successor promotion.

## Expanded hosted completion

39470823794 at5796293 completes both corrected jobsSUCCESS; downloaded17XML files strictly verify40passes (24checker+16SPI). Expanded39471254787 at5f03060 completes compiler and both-workload simulationSUCCESS. Downloaded21XML files strictly verify44passes. Independent direct Git-object audit verifies362source/library hashes and183caseartifacts across15cases.

UART+I2C allhard demands123cells/3timers/3shifts; hardUART/softI2C173cells/2pairs; reverse218cells/1pair; bothsoft270cells/0pairs. Allfour fail with native G1 capacity/placement diagnostics. These are synthesis demand, not placed counts. R1_REQUIREMENTS.md records the resulting resource options; no architecture selected or physical gain claimed.
