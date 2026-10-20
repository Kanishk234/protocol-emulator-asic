# R1 candidate requirements after the paired baseline

Status: experimental capability specification, October20,2026. No production architecture replacement or topology selection. D-037 governs exploration; frozen G1 remains unchanged.

## Measured starting point

[Hosted39471254787](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39471254787), source5f03060fdcfd881fafee1dd4f068410b8bad2681, attempt1, passes compiler and simulation jobs. Independent artifact audit checks362 source/library hashes and183 case artifacts; all15 native outcomes revalidate. Downloaded21 XML files strictly contain44 executed passes:24 evidence-checker,16 UART+SPI,4 UART+I2C. No skipped/error/failure cases. See reports/fresh_baseline_20261020.md for earlier unchanged single-personality results.

All six existing G1 personalities still compile/place/route. Both new concurrent workload families fail on G1 in every hard/soft variant. Synthesis demand, not placed count:

| Workload | Both hard: cells, timers, shifts | Hard UART/soft second engine | Soft UART/hard second engine | Both soft |
|---|---|---|---|---|
| UART+SPI | 103,3,3 | 138,2,2 | 195,1,1 | 233,0,0 |
| UART+I2C | 123,3,3 | 173,2,2 | 218,1,1 | 270,0,0 |

These are current mappings under the unchanged G1 cell library; different user RTL/compiler packing can change demand. They are not universal lower bounds, physical area measurements or routed timing. Both wrappers preserve external chip pin counts and share the same framed host channel policy. Host framing overhead and head-of-line blocking are documented, not hidden.

## Hard requirements

1. All six supported G1 personalities retain documented behavior and tested settings, with individually compiled/loaded images. No narrower protocol roles or added mandatory host computation to manufacture fit.
2. Same TT6x4 CMOS5L whole-chip envelope and50MHz target, including shell/configuration/routing/clock/power. Maintain real configuration storage and existing safety behavior. A new architecture ID/image format is permitted only with full loader/compiler support and explicit specification.
3. Demonstrate simultaneous UART TX/RX plus SPI controller under the committed benchmark's pin, command, response and servicing rules. Extend the short functional smoke test to sustained traffic and declared long-run servicing/overrun limits before promotion. The benchmark is evidence G1's current implementation does not fit, not proof no optimized G1 implementation could.
4. Physical closure and stronger candidate loaded-mapped-fabric checks: native zero overflow, complete routing, DRC/LVS/antenna/precheck, setup/hold/corners and actual image-loaded behavior. Keep model timing separate from configured timing.
5. Fresh sealed evaluation after freeze. Read HELDOUT_R1_MANIFEST.json only before then; exclude every public-pool role from tuning. Selected bytes stay local while publication approval is pending. Any revealed/touched case loses held-out status and must be logged.

## Resource options to screen, not promised hardware

The initial112–128-cell/two-pair proposal does not fit the measured mixed primary workload. Screen two alternatives at full cost:

- **Additional reusable primitives:** enough soft logic for the103-cell primary demand and preferably123-cell secondary demand, with at least three timers/three shifts. The existing PRIM2T2S tile supplies pairs; provisioning a second tile gives four of each but consumes logic/area. A custom3/3 composition is an experiment requiring tool mapping, area and unused-resource accounting, not a free extra block.
- **Retain two primitive pairs:** enough logic for the138-cell primary demand, or a demonstrated user-RTL/packing improvement that lowers that demand without changing behavior. The173-cell secondary demand is a stretch under this alternative.

A128-cell/three-pair screen is a useful resource hypothesis, not an approved physical specification: primary logic occupancy is103/128 and secondary123/128 before candidate-specific packing/routing. A104-cell/four-pair variant has essentially no logical headroom for the primary workload and fails the current secondary demand; do not call it a strong successor merely because it adds primitives.

The first comparison must include all resource costs. Additional primitives are justified by two distinct concurrent communication workloads, but neither placement feasibility nor a whole-chip area benefit has been demonstrated. Keep unrelated protocol behavior in user RTL.

## Routing and implementation screen

Use one regular routing control and at most two local/global-connectivity variants. First extract actual net fanout, primitive-to-logic/I/O locality and inter-cluster crossing demand from authenticated training artifacts. Keep user-fabric routing demand distinct from shell/configuration congestion in the native chip; both must be addressed.

Select cluster size, routing choices and configuration distribution only after generator/nextpnr/bitstream compatibility and complete cost census. Reserve channels and pin access before filling the outline with logic. Harden representative structures early, then the full real-shell assembly; representative-block success never qualifies the whole chip.

No initial new memory, processor lanes, LUT-size change or protocol hard block. Reuse compiler/shell/tests where appropriate. A protocol-agnostic primitive change needs a decision entry with measured benefit, area cost and cost to nonusers before implementation/promotion. Preserve one-hardware-variable-per-hardening and the bounded campaign budget in FRESH_CANDIDATE_PLAN.md.

## Next gate

Produce a small, source-bound routing/configuration census and written topology/tool-compatibility specification for at most three screens. Reject candidates with no plausible full-area margin before spending full-chip hardening attempts. No full-chip physical attempt has been consumed by these compiler/simulation campaigns.
