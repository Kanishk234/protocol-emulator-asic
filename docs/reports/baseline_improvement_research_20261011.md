# Baseline WARP improvement research — 2026-10-11

These are ranked hypotheses, not measured improvements or approved hardware changes. Research covers competitors, official tool documentation and architecture papers. Existing monitor, fault injection, capture, seed sweeps and compiler controls are already in our roadmap; extending them is not a new invention. Frozen G1 remains unchanged. A revised architecture must use fresh sealed evaluation workloads because G1's opened held-out set cannot certify a successor independently.

## Main recommendation

Improve usable behavior per existing LUT and per host transaction before adding silicon. Our G1 limits report finds control/glue and primitive input paths more relevant than extra control sets or more copies of timers/shifters. Our user guide explicitly identifies slow MicroPython host service as a streaming bottleneck. A bigger fabric alone will not solve either limitation.

## Primary research and what we can borrow

- [PRISM lite and larger-build description](https://tinytapeout.com/chips/ttihp26b/tt_um_pettit_prism_lite): runtime-loaded state machines, CPU-managed upper layers, reusable datapaths, queues and diagnostics. Learn the separation of wire deadlines from packet policy, queue service and observability. The page mixes lite and larger-build features; SRAM/Ethernet are not lite features and source descriptions are not our measurements.
- [PRISM competition repository](https://github.com/kdp1965/ihp-um-janestreet-prism): explicitly documents SRAM/power-grid placement and configuration columns that obstruct routing. Memory adds physical walls and pin-access costs. Its forked8x4 flow does not establish official upstream8x4 availability for WARP. The organizer SRAM walkthrough URL did not open in this browsing tool; its contents are not claimed reviewed here.
- [Tempo README](https://raw.githubusercontent.com/satyaammu93/jane-street-asic-2026/main/protocol_emulator/README.md): source-reported two independently paced engines, finite queues, timeouts, ownership and timestamp capture. Suggests usability features to assess, not copying its architecture or assuming an area advantage. Its numerical validation claims were not independently reproduced.
- [Raspberry Pi PIO SDK](https://github.com/raspberrypi/pico-sdk/blob/master/src/rp2_common/hardware_pio/include/hardware/pio.h): general shifters, FIFOs and fractional division support many interfaces. Useful design patterns, not evidence WARP needs a PIO CPU.
- [Official triggered logic-analyzer example](https://raw.githubusercontent.com/raspberrypi/pico-examples/master/pio/logic_analyser/logic_analyser.c): trigger, packed samples, paced DMA, explicit restart. Adapt the host transport and buffering discipline while keeping WARP's existing SPI commands.
- [Yosys ABC/ABC9](https://github.com/YosysHQ/yosys/blob/main/docs/source/using_yosys/synthesis/abc.rst): timing-aware mapping can account for hard blocks and unequal arcs. Requires accurate WARP models and compatible pinned synth_fabulous integration; not a drop-in promised gain.
- [FABulous fabric definitions](https://github.com/FPGA-Research/FABulous/blob/main/docs/source/user_guide/building_doc/fabric_definition.md): dedicated connections, custom primitives and supertiles offer structured integration. Every resource still needs compiler/place/route/bitstream/loaded-test support.
- [Tiny FABulous](https://github.com/mole99/tt-fabulous-sky-26a): reproducible tile→fabric→chip build and loaded/emulation distinction. Retain matched-view discipline; copied views do not qualify changed mapping.
- [How to Shrink My FPGAs](https://pure.manchester.ac.uk/ws/portalfiles/portal/207833524/FPGA_2020_FABulous_optimizations_1_.pdf): configuration assignment and interface-wire permutation are physical optimization variables. Rebuild bit mappings and adjacent interfaces together.
- [S44 LUT paper](https://people.eecs.berkeley.edu/~alanmi/publications/2018/fpga18_s44.pdf), [DSLUT](https://arxiv.org/abs/2503.16109), [Double Duty](https://arxiv.org/abs/2507.11709): richer/asymmetric logic and independent arithmetic connectivity can improve the authors' evaluated architectures. Those results do not transfer numerically to CMOS5L, our tiny workloads or our routing. Use as alternatives to screen, not justification for LUT6 everywhere.
- [VTR architecture methodology](https://docs.verilogtorouting.org/en/latest/vpr/): realistic benchmarks, accurate architecture models and capable mapping tools are required. Equal-area hardened comparisons remain WARP's selection gate.

## Ranked ideas on unchanged baseline hardware

| Idea | Why it could help | Cost / first meaningful test |
|---|---|---|
| 1. C/C++ demo-board host transport with precomputed SPI framing and paced DMA | Reduce interpreter and per-byte service latency; make existing streaming examples usable | Preserve SPI CS gaps/opcodes/status and finite FIFO semantics. DMA cannot bypass handshakes. Test against shell model with random backpressure; measure real service only when a board exists. |
| 2. Throughput/buffer planner | Tell users whether baud/event rate, queue depth and host service can coexist | Compute worst-case service and burst budget, expose overflow; do not substitute average bandwidth for deadlines. |
| 3. Primitive-aware HDL library | Reusable wait/shift/sample/timeout building blocks make arbitrary new protocols easier to express efficiently | Wrap existing WP_TIMER/WP_SHIFT semantics, no duplicated hidden counters. Compile actual examples and compare loaded behavior. |
| 4. Automatic primitive recognition | Users should not need manual hard-block instantiation to get efficient designs | Match only exact supported counter/shifter behavior; equivalence and loaded testing prevent incorrect substitutions. |
| 5. Timing-aware compiler mapping | Optimize the real critical path around primitive inputs and LUT pins | Screen ABC9/other timing-aware mapping with authenticated models. Prior seeds/FSM tweaks did not establish gains; preserve unsuccessful results. |
| 6. Width, sharing and FSM lint/advice | Avoid oversized state/data registers, duplicated decoders and preventable LUT cost | Report measured costs and alternatives; binary encoding is not universally better. Existing compiler controls are the baseline. |
| 7. Concurrency resource planner | Explain which independent engines/monitors fit together | UART already consumes both timers and both shifts; do not promise two full UARTs just because LUTs remain. Compile concurrent designs. |
| 8. Autonomous triggered fault injector | Extend existing externally timed bit inversion to trigger→delay→fault scenarios | Narrow initial scope to one design-set protocol and bounded soft state; resource fit and recovery tests required. |
| 9. Triggered event capture with compressed records | Make finite host bandwidth useful through edge deltas, repeats or trigger windows | Build on existing capture/wrap/overflow decoder. Compression has worst-case expansion; preserve explicit loss markers. |
| 10. Protocol bridge / in-flight transformer | Demonstrate spatial logic doing timing and arbitrary data manipulation concurrently | Start with bounded UART stream filter/checksum or SPI response transform; full UART-to-SPI bridge may exhaust hard blocks. Test overlap and backpressure. |
| 11. Parameterized device personalities | Reprogram response rules, timing, error policy and small register maps | Small I2C target scope might fit even though our larger target does not. New result must distinguish feature reduction from compiler/architecture gain. |
| 12. Host-assisted large protocol stacks | Keep immediate bit deadlines on chip; put enumeration, framing policy and large tables on host | Host may handle only operations with sufficient slack. USB turnaround/continuous Ethernet cannot be solved by slow per-byte SPI polling. |
| 13. Reusable timeout/recovery patterns | A stuck input or stretched clock should have bounded, documented behavior | Soft watchdog consumes state/counter resources; test stuck-high/low, reset, STOP and delayed host service. |
| 14. Broader parameter coverage of supported protocols | Modes, baud ratios, stretches, jitter, edge phases and reset mid-frame establish practical usability | Different from claiming a new named protocol; test actual configured images and independent peers. |
| 15. Compiled rate certificate | Ship pin map, resources, allowed clock range, host budget, reset policy and exact evidence with each image | Estimated timing remains labeled; add actual configured timing for claimed rates. |
| 16. Custom bitstream challenge showcase | Let a new external user implement an unanticipated small interface from docs | Fresh sealed evaluation, resource fit and independent tests; human usability feedback is not silicon evidence. |
| 17. Trace-to-replay workflow | Capture an event sequence and compile a bounded replay/response engine | Only supported samples/quantization; no exact analog reproduction or unlimited storage. |

## Hardware experiments for a separately qualified successor

| Idea | Likely benefit / compromise | First selection gate |
|---|---|---|
| 18. Deeper generic host queues and burst commands | Absorb latency and amortize transactions; storage/controller/pin-routing cost | Profile actual arrival/service bursts. Requires shell/spec approval and new host compatibility/version policy. |
| 19. Shared SRAM data buffer | Useful packets, tables and traces without spending many LUT FFs | Full macro/wrapper/arbitration/power-grid footprint in6x4, latency and reset initialization; first compare complete queue cost. No promise it fits. |
| 20. Programmable serial CRC/LFSR primitive | Generic checksum/scrambling across multiple bitstreams | Polynomial/seed/reflection/control/glue costs and actual multi-user demand. Shell's loader CRC is not already a user resource. |
| 21. Capture/compare/edge primitive | Timestamp, pulse measurement, watchdog and scheduled output support | Profile at least several design-set tasks; shared-state contention and input synchronization limit precision. |
| 22. Fractional clock-enable generator | Better average baud ratios without a PLL | Accumulator adds logic; alternating periods introduce jitter. Use synchronous enables, prove bounded phase/interval behavior. |
| 23. Primitive-adjacent local interconnect | Reduce feedback/glue path demand around timers/shifters | Keep multiple placements and workloads routable; fixed links sacrifice flexibility. |
| 24. Configuration-bit and boundary-pin physical remapping | Reduce loading wires and tile congestion | Exact old/new compiler/bitgen mapping, all affected tile interfaces and native loaded tests. No user truth-table simplification. |
| 25. Small dual-output/fracturable LUT experiment | Pack the small control predicates that remain expensive | Extra outputs/FFs/muxes/routes can erase gain; mapper-aware equal-area hardened comparison. LUT4 cannot become an arbitrary LUT6 in software. |
| 26. Independent carry/XOR paths | Counter/add/checksum glue may use less general routing | Existing hard timers already eliminate much counting cost; new profiling must justify resources lost to arithmetic. |
| 27. Tiny shared-code event lanes plus LUT fabric | Sequential waits/timing can complement spatial transforms | Existing event-lane spike is unintegrated; code memory, private state, compiler and arbitration included in cost. Larger architectural risk. |
| 28. Carefully optional I/O sampling modes | Trade synchronization latency against interface performance | Synchronizer bypass creates CDC/metastability obligations and pad uncertainty; not an automatic speed upgrade. |
| 29. Runtime scalar parameter registers | Change delays/masks without complete image reload | New shell→fabric routing/registers and coherency semantics; generic programmable parameters, not hard protocol controllers. |
| 30. Clock-enable and operand isolation | Lower switching in unused resources | Preserve live configuration, deterministic reset and tool support. Power benefit requires switching-based measurement; avoid new derived-clock hazards. |

## What I would avoid for now

PLL/custom analog, custom transistor LUT cells, wholesale LUT6 replacement, a second primitive tile without demand, more control sets, and a large on-chip CPU. These can consume area or verification time without addressing our measured bottlenecks. USB/Ethernet remain stretch investigations, not support claims.8x4 is an optional upgrade only after official availability and clean flow evidence; keep6x4 as the acceptance target.

## Execution recommendation

Start with1–3,8–9 and15 on frozen hardware while physical closure continues. Screen4–6 after accurate timing/primitive models are available. Select at most one hardware candidate from measured demand—likely buffering/queues or local primitive connectivity—rather than hardening a bundle. Record fit, host budget, correctness, physical congestion and timing together. All hardware contract changes need the existing project decision/approval process. None of these research ideas has been implemented or shown to improve WARP by this report.
