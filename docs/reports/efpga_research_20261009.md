# eFPGA research and bounded improvement plan

**Audit date:** 2026-10-09. Research hypotheses, not a successor selection or
performance claim. Frozen G1 remains the fallback; compact experiments do not
qualify it automatically. No hardware, upstream source, reference model,
held-out workload or cloud workflow was changed by this report.

## What matters for the competition

The current [organizer brief](https://blog.janestreet.com/protocol-emulator-asic-competition/)
still specifies CMOS5L, 6×4 tiles and January 18, 2027; 8×4 remains a possible
future expansion. It emphasizes reprogrammability, functionality and
verification. A reproducible loaded protocol, documented limitations and an
interesting parallel demonstration are useful even if compaction fails.

WARP's design-set profiling identifies counter, shift, storage and control
costs, rather than establishing that more LUTs alone solve the problem. Read
[profiling](profiling.md), [G1 limits](g1_limits.md) and the
[equal-area comparison](architecture_comparison.md) before changing resources.
Existing nextpnr frequency estimates are models; they do not establish
configured extracted timing. The comparison includes shell, configuration,
routing, footprint and the same clock target under D-004.

D-037 permits separate successor exploration; it does not authorize silently
changing the architecture contract or promoting an experimental macro. The
old held-out set was already opened after G1's freeze and cannot be fresh
independent validation for a successor. This work does not inspect or tune it.
Phase 5 work on frozen G1 can continue; a successor must satisfy its reopened
architecture and physical gates before submission claims change.

## Primary-source findings

| Source checked online | Useful observation | WARP inference and boundary |
|---|---|---|
| [FABulous framework](https://github.com/FPGA-Research/FABulous), [authors' framework paper](https://woset-workshop.github.io/PDFs/2021/a15.pdf) | Fabric, tile, routing and configuration choices are customizable; framework supports standard-cell implementations and integrated user tools. Upstream warns against production use of development branches. | Keep the pinned 2.2.0 toolchain while isolating experiments. A new resource needs synthesis mapping, P&R, bit generation and loaded tests, not just RTL. |
| [Tiny FABulous SKY26a](https://github.com/mole99/tt-fabulous-sky-26a), [tile library](https://github.com/mole99/fabulous-tiles) | Hierarchical tile/fabric/top hardening, real-upload simulation and GL modes are documented. SKY130 dimensions and flow choices belong to that project. | Reuse the validation pattern, not its clock or geometry assumptions. Keep actual programmed-native checks distinct from fast emulation. Preserve strict WARP checks even if another project permits congestion. |
| [HeiChips IHP tapeout](https://github.com/HeiChips/heichips25-tapeout) | An IHP SG13G2 FABulous fabric connects user blocks, I/O and memory, with global buffers and system reset. | Useful reference for general interfaces, hard resources and clocks. It is not evidence that its memory fits WARP CMOS5L or that SG13G2 layouts can be copied. This is an IHP reference, not a claimed Tiny Tapeout CMOS5L twin. |
| [PRISM project description](https://tinytapeout.com/chips/ttihp26b/tt_um_pettit_prism_lite), [source repository](https://github.com/kdp1965/ihp26b-um-pettit-prism-lite) | Programmable state tables, independent shards, generic datapaths and debugging accompany Verilog compilation. Published protocol results explicitly include simulation. | WARP cannot claim Verilog-to-bitstream, multiple engines, CRC or capture as new. Demonstrate concurrent arbitrary user logic and timed protocol behavior; compare total area before claiming a spatial-fabric advantage. |
| [Authors' “How to Shrink My FPGAs” manuscript](https://pure.manchester.ac.uk/ws/portalfiles/portal/207833524/FPGA_2020_FABulous_optimizations_1_.pdf) | Configuration-bit assignment and tile-interface ordering are physical optimization variables; configuration and user-routing geometry interact. | A different configuration mapping must also update bitstream mapping. Port reordering is a separate experiment from switch/FF changes and requires all affected tiles/interfaces to agree. Published SKY130/backend gains are not CMOS5L predictions. |
| [2024 custom-cell/congestion study](https://www.sciencedirect.com/science/article/abs/pii/S1879239124002480) | The abstract describes co-optimizing custom cells and configuration connectivity in a FABulous TSMC28nm implementation. | Motivation for measurement only. Custom cells require CMOS5L layout, characterization, DRC/LVS and flow support; small cell area alone does not prove a smaller routable tile. |
| [Pinned OpenROAD resizer documentation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/rsz/README.md), [implementation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/rsz/src/RepairDesign.cc) | `repair_design` handles fanout, capacitance and slew and can resize drivers. Output-port buffering is a different operation. | Use graph/physical evidence to split real high-fanout branches. Do not assume output adapters repair internal configuration loads or that stronger drive fixes a fanout limit. |

These are source-reported observations, not independent competitor measurements.
No competitor code was copied. Any later reuse must check its license, retain
attribution and preserve pinned upstream sources.

## Improvements available on either compact or fallback hardware

| Priority / hypothesis | Bounded experiment | Cost, compromise and acceptance |
|---|---|---|
| 1. Make missing electrical/timing evidence visible | Audit retained report rows against native metric counts; separately inventory clocked endpoints, unconstrained endpoints and selected configuration. | Software-only; no silicon cost. Exact counts do not prove full connectivity, annotated loads or timing. Reject missing/contradictory evidence. New auditor below addresses the report-row part. |
| 2. Bind compiler timing to the actual hardware views | Authenticate each tile's NL/LEF/SPEF and actual configured clock selection; compare representative used LC/primitive arcs to the compiler model at the same corner. | Read-only hosted STA and data processing first. Constraints must represent real operation; do not invent a clock on unused configuration state or treat null-clock tile virtual paths as configured signoff. Keep existing timing rejections open. |
| 3. Measure placement robustness on the design set | Use existing `compile_design(..., seed=...)` or compile CLI `--seed` on UART, SPI controller and I2C controller; report fit failures, resource demand and model timing per seed. | Several cloud user P&R runs, no chip reroute. Same source/parameters/pins/tool versions per comparison. No cherry-picking a single favorable seed; faster model estimates do not establish ASIC rates. Not executed here. |
| 4. Show useful parallel behavior and failure diagnosis | Reproduce existing monitor/capture demonstrations through the real host loader; record host polling/batching, overflow, STOP/reload and externally injected bad traffic. Add a concurrency demo only if it fits unmodified G1. | Host tools, tests and soft user logic; costs fabric resources and host bandwidth. Fit/rate/fault claims need their own run evidence. Do not add dedicated protocol silicon or call simulator traces hardware tests. |
| 5. Strengthen compiler/bitstream correspondence | Preserve source→mapped design→FASM→bitstream hashes and negative tests that deliberately mismatch architecture or configuration mapping. Reuse the existing clean-checkout flow. | Small tool/evidence work and simulations. No fast-mode preinitialized state may substitute for loaded verification. Existing reproduction37690896748 is one useful baseline, not physical signoff. |

All five survive failure of the compact design. Exact clock/fanout issues may
also exist in the fallback and must be audited there rather than presumed fixed.
Existing compiler, shell and demonstrations should be reused before inventing
new overlapping tools; see [the improvement roadmap](../design/COMPETITION_IMPROVEMENT_ROADMAP.md).

## Physical experiments requiring isolated decisions and measurements

| Candidate | Concrete first experiment | Costs and fallback applicability |
|---|---|---|
| Configuration distribution | On copied matched C2, buffer only latch D/GATE branches, keeping existing FrameData/Strobe forwarding paths unchanged. Inspect the full native graph before mutation. | Estimated149 one-stage leaf buffers for49 cfg nets;13 user violations remain. Added cells/wires, latch-data/strobe delay and loading risk. Native loaded tests before one tile route. It could be applied to G1 only as a separately logged/measured change. |
| Configuration remapping / interface permutation | Use the exact passing tile as control. Test one physically motivated mapping or ordering, regenerate compiler/bitgen correspondence, then native equivalence and paired tile routing. | No promised state-count saving. New mappings invalidate old images; pin permutation breaks existing tile-abutment contracts unless all affected views are rebuilt. Requires approval for changed contracts and cannot be patched into frozen G1 silently. |
| Communication-shaped routing | Screen one track/fan-in reduction on the existing design set with identical tool/pin/clock conditions, then compare hardened total footprint if all required designs route. | Fewer muxes/configuration bits may lose routability or concurrency. Needs arch generation, tool graph and bitstream changes. Applies to a successor of either layout, not an immediate fallback software improvement. |
| Fracturable logic / revised LUT size | Screen actual packability and FF/control-set utilization before designing one alternative tile. | Extra select/configuration/output wiring can erase LUT-count gains; LUT6 has64 truth-table bits versus LUT4's16. Equal-area full fabric, mapping and hardened routing required. Not justified by LUT count alone. |
| Generic CRC/LFSR, queue or event tile | Profile only the approved design-set workloads for a reusable operation; screen integration/glue/storage/interface cost before committing a tile slot. | Generality must benefit multiple users; unused blocks displace LUTs. Queues consume storage and routing; event engines require compiler and bitstream integration. Existing timer/shift primitives and event-lane spike are controls. New architecture approval required. |
| Custom mux/configuration cells | Characterize a single CMOS5L cell and legal tile integration before broader custom-cell work. | Highest integration burden: layout, corners, extraction, power connections, DRC/LVS, model and synthesis support. Does not repair a routing-heavy chip by itself. Defer until standard-cell geometry/distribution experiments are exhausted. |

The 149-buffer figure is a graph estimate, not measured area or routing success.
Actual retained C2 reports from 37814078650 contain 32 FrameData, 17 FrameStrobe
and 13 other violations at limit 8 in every corner. Input loads include one existing
forwarding buffer each: FrameData 18×18 + 13×17 + 1×16; FrameStrobe 15×33 + 1×32
+ 1×19. After retaining forwarding loads, groups of at most 8 latch sinks require
82 data + 67 strobe leaf buffers; parent fanout is at most 5. A 130-buffer algebraic
lower bound permits mixed direct/buffered latch paths and is not the recommended
first experiment. Actual capacitance, slew, strobe/data stability and configuration
loading still need measurement. No cell-area gain is claimed.

## Independent evidence tool implemented now

New [audit_fanout_report.py](../../test_internal/audit_fanout_report.py) reads
retained OpenSTA `checks.rpt`, hashes it and emits exact rows/group histograms.
It retains violated rows with blank printed slack, rejects malformed/duplicate
rows, validates supplied slack and requires the explicit native report count
to match the number of rows. It does not waive limits or declare physical pass.

Validation in the project venv: three unittest methods (including six malformed
evidence cases) pass; all three actual 37814078650 corner reports reproduce 62
violations, split 32 data / 17 strobe / 13 other, all at limit 8. Slow report SHA256:
`36ba7da2e956fbb280e132450a67e33d7aad4872c892c655e9f44233ded0fc9f`.
Three real rows have blank slack; they must not be silently dropped.

```sh
source .venv/bin/activate
python test_internal/audit_fanout_report.py --self-test
python test_internal/audit_fanout_report.py --expect-count 62 --expect-limit 8 \
  build/cloud_tile_harden_37814078650/matched-c2-harden-37814078650/run/41-openroad-stapostpnr/nom_*/checks.rpt
```

This is read-only, lightweight evidence processing; it launches no EDA, cloud
job or background terminal. There is no implicit zero-violation acceptance
when a requested limit is checked against an empty table. Native metrics,
complete load census and genuine timing remain separate requirements.

## Sequence and decision gates

Finish the current official/physical diagnostics and retain their actual source
hashes before opening another full-chip route. In parallel, use the new audit
tool and complete frozen-G1 evidence/reproduction work. Next isolate exact
configuration buffering and genuine clock timing on copied tiles. Expand to
complete fabric only after matched native function, ports, DRC/LVS, antenna,
electrical limits and configured timing justify it.

All expensive EDA should run in bounded standard hosted jobs. Start with static
graph checks or user P&R, then one tile, then a full chip only if earlier stages
provide new evidence. Runtime and routing costs are unknown until measured;
do not launch multiple long identical retries or change limits to manufacture
closure. No phase box was ticked by this report; root should record this work
in the session WORKLOG when integrating these two new files.
