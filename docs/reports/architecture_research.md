# Architecture research: where WARP can be different

**Date:** 2026-09-28 · **Purpose:** research synthesis to guide the reopened architecture exploration. This document records hypotheses, not a selected design.

## Competition target

The current Jane Street brief explicitly asks for an open-source, general-purpose protocol emulator, says fixed UART/SPI/I2C blocks are not the goal, and asks entrants to show other things their architecture enables. It also names unique functionality and novel design/verification methods as judging interests. The current limit is 6 × 4; 8 × 4 remains unconfirmed. Therefore WARP should optimize for **useful new behaviors per fixed area** and provide direct evidence of what its spatial eFPGA enables. Raw counts of protocol bitstreams are weak evidence if they run only one at a time.

## Architecture landscape

### Established programmable-I/O structures

The RP2040 is instructive for resource sharing: each PIO block has four independent state machines, but the state machines in a block share a small instruction memory. Each retains its own shift state, scratch state, divider, and FIFOs. That amortizes code storage when the same program runs on several pins. The RP2040's official SDK describes the per-machine shift registers, FIFOs, fractional divider, flexible GPIO mapping, and DMA pacing ([Pico SDK PIO hardware documentation](https://www.raspberrypi.com/documentation/pico-sdk/hardware.html)). NXP FlexIO independently demonstrates composition from generic shifters, timers, and pins for UART, SPI, I2C, I2S, displays and PWM ([NXP FlexIO overview](https://www.nxp.com/design/design-center/software/development-software/mcuxpresso-software-and-tools-/specialized-peripherals-for-nxp-microcontrollers%3ASPECIALIZED-PERIPHERALS-MICROCONTROLLERS)).

**WARP implication:** the earlier sequencer area model's per-lane program memories are an avoidable cost when multiple endpoints can run the same code. A temporary synthesis probe shows sharing an 8-word, 24-bit instruction image between two independently advancing lanes reduces mapped area from 42,553 to 30,054 µm² (about 29%); a 16-word image saves about 35%. It keeps a separate PC and data/timer/pin state per lane and needs two instruction read ports. These numbers come from an intentionally incomplete RTL cost probe, without a physically built SRAM or correct protocol timing semantics, so they only establish that shared code memory deserves a proper experiment. The exact results and limitations are in [`architecture_screen.md`](architecture_screen.md).

### Current competition entries

Public project pages describe a rapidly converging design space:

- **Tempo** reports a complete two-engine instruction-based emulator, 64 × 24-bit writable program memory per engine, deadline/timing controls, four-entry data queues, pin ownership, contention diagnostics and timestamp capture. Its README also reports physical and gate-level verification; these are the authors' own results, not an independent reproduction ([Tempo README](https://github.com/satyaammu93/jane-street-asic-2026/blob/main/protocol_emulator/README.md)).
- **BitLoom** describes multiple PIO-style machines with deadline timing, capture and protocol examples ([BitLoom repository](https://github.com/sheehanmunim/bitloom)). Its reported feature set is self-published.
- **Abagel's proposal** describes a time-triggered CPU plus two programmable line-coding lanes, CRC/stuffing, timestamp FIFOs, pin contention monitoring and formal timing/liveness claims. The repository currently labels the architecture as a proposal and lists only a UART transmitter warm-up with three local checks. Its 7–8K-cell block budgets are explicitly estimates, not measured results ([proposal](https://github.com/Abagel-coder/protocol-emulator/blob/main/docs/superpowers/specs/2026-09-15-protocol-emulator-design.md), [project status](https://github.com/Abagel-coder/protocol-emulator)).

**WARP implication:** “two independent lanes,” “absolute deadlines,” “capture,” “generic CRC,” or “formal timing” alone are no longer good differentiators. WARP's credible potential advantage is **spatial programmability coupled directly to temporal I/O**: user-synthesized logic can observe, transform, coordinate and react to generic event streams in parallel with pin engines. That advantage is currently a hypothesis. The showcase should prove one simultaneous example that is difficult for a small sequential core, such as one link emulator reacting to a second live monitor while the LUT fabric applies a user-defined filter/trigger or packet transform.

### eFPGA optimization findings

The most directly applicable result is the FABulous-specific tile optimization study by Chung, Dao, Yu and Koch. It combines configuration-cell placement remapping with tile-interface pin remapping and reports 21.7% area reduction and a 6.1% worst tile latency improvement for its optimized LUT4 CLB. Its physical experiments used SkyWater 130 nm and Cadence Innovus, not IHP CMOS5L and OpenROAD, so the percentages cannot be carried over to WARP ([accepted manuscript](https://pure.manchester.ac.uk/ws/portalfiles/portal/207833524/FPGA_2020_FABulous_optimizations_1_.pdf), [publication record](https://research.manchester.ac.uk/en/publications/how-to-shrink-my-fpgas-optimizing-tile-interfaces-and-the-configu/)).

The same study found that straightening configuration cell placement and choosing tile border pin locations can reduce congestion. It also found frame-based configuration more area-efficient than a conventional shift-register configuration in the studied fabrics. WARP already uses frame-based latches, so a configuration architecture switch to scan/shift chains has poor evidence and should not be a leading candidate. The project’s own G1 tile has 74.2% of configuration bits assigned to switch-matrix choices; that supports studying physical configuration and routing layout, but not assuming equivalent area is recoverable.

The installed FABulous 2.2.0 Python package contains a tile-area optimization flow with `find_min_width`, `find_min_height`, `balance`, and `large` modes, along with a configurable tile-pin placement step. WARP's current CMOS5L spike runner does not call that loop: it uses a fixed size table in the copied `fabulous-tiles/tiles.py` and the generated G1 `ConfigMem.csv` maps feature bits in regular sequential ranges. That gives a concrete route to test the literature: run the supported optimizer from a scratch copy of the WARP LUT tile, with width fixed/minimized under the 199.08 µm row-height ceiling, and compare the optimized feature-bit mapping and border-pin assignment with the current file. The local tile runner's Nix-pinned FABulous plugin predates this API, so the first gate is proving a reproducible flow with the pinned tools before trusting any dimensions.

A classic FPGA architecture paper by DeHon argues that interconnect can dominate programmable-array cost and that maximum LUT utilization is not always the best area point. This supports measuring the routing graph and physical metal pressure together with logic capacity ([Berkeley author-hosted paper](https://brass.cs.berkeley.edu/documents/fixedws_fpga99.pdf)). The newer eFPGA study on custom mux/configuration cells reports gains at 28 nm and likewise emphasizes congestion-aware wiring; that result is useful motivation, not a CMOS5L estimate ([study DOI](https://doi.org/10.1016/j.mejo.2024.106544)). OpenFPGA's published architecture language provides another reference for exploring LUT fracturing, switch topologies, config memory and hard blocks as separable knobs ([OpenFPGA paper](https://woset-workshop.github.io/PDFs/2020/a19.pdf)).

## New candidate: recover a fifth logic column

WARP's measured 4 × 3 fabric is about 1016.64 µm wide and leaves roughly 272.64 µm for the shell column. A 5 × 3 grid at current tile pitch consumes about 1236.48 µm and leaves only 52.8 µm, below the project's 200 µm shell estimate. At fixed die width, preserving the edge tiles and the shell estimate requires the interior tile pitch to fall from 219.84 to at most 190.4 µm. The available die height permits a taller interior tile, up to about 199.08 µm. This gives a test geometry of approximately 190.4 × 199.08 µm per logic tile, against the current 219.84 × 185.22 µm tile.

A 5 × 3 grid could hold 112 LUT4s and the measured 2+2 primitive tile if one slot is reserved, or 104 LUT4s with two primitive slots. The former adds 24 soft LUTs at unchanged timer/shifter capacity relative to G1; the latter adds 16 LUTs and doubles those generic timing/data resources. It may make dual-link concurrency credible. The target slot's area is about 37,903 µm², near the existing LUT tile's 36,047 µm² standard-cell area before repair cells, filler, routing and boundary infrastructure. The two-primitive option is especially tight. This is a physical feasibility experiment, not an architectural conclusion.

**Experiment:** use the newer FABulous tile-area optimization flow only if it can be made reproducible with the pinned CMOS5L tools; otherwise automate a bounded width/height sweep in scratch builds. Optimize LUT and primitive tile interfaces/configuration mapping; harden each candidate in the real CMOS5L flow; then generate a separate 5 × 3 fabric and prove the shell, pin routing, configuration frames and representative concurrent designs. A physical fit is useful only if the bitstream compiler and router can exploit the extra column.

## Architecture directions ranked for investigation

| Rank | Direction | Why it may matter | Required evidence / main risk |
|---:|---|---|---|
| 1 | **FABulous-specific tile and config remapping, with a 5 × 3 target** | Could recover 24 LUTs while preserving WARP's differentiating spatial fabric; strongest directly applicable physical paper | Real tile hardening with CMOS5L layers, then fabric routing and full core fit. The target has little utilization slack. |
| 2 | **Shared-program multi-lane event engines connected to arbitrary LUT logic** | Shared code memory makes parallel instances cheaper; preserves per-lane timing/data state and uses the existing compiler model as a foundation | Repair the cost probe into a cycle-specified ISA, compare shared vs private code, synthesize/harden and show true simultaneous lane + LUT operation. Competition overlap is high unless space-time coupling is explicit. |
| 3 | **Generic event capture, trigger, and scheduled output integrated into the fabric** | Turns the chip into a protocol emulator and reverse-engineering instrument; event/time abstraction spans async, source-synchronous, pulse and line-coded links | Trace RAM/FIFO costs area; timestamp rollover, event loss, and response latency need explicit contracts. Several competitors already describe capture, so show user-programmable fabric reaction as the distinction. |
| 4 | **Routing graph reshaping: local rich links plus only selected long wires** | Cuts mux/configuration burden and can improve physical congestion; small 4 × 3 fabrics do not need large-FPGA global wire populations | Same compiler workload must route across topology variants; fewer tracks can strand control-heavy designs. |
| 5 | **Generic line-code/CRC assists** | Shared bit insertion/removal or programmable polynomial CRC could reduce cost for unrelated encoded links | Size and pin timing must be measured; other entries also plan these, so it is not a headline differentiator by itself. |
| 6 | **LUT6 or fracturable LUT tiles** | Fewer LUTs for some controllers may improve logic capacity | LUT6 truth tables have 4× LUT4 configuration bits; harden area and route before further investment. |

The highest-value combined concept to test is **a denser WARP spatial fabric with a compact, shared-code event engine and event interfaces into the LUT array**. It retains arbitrary user RTL, enables parallel timing engines, and makes the eFPGA useful for custom monitoring/reaction logic. It is a hypothesis to evaluate against G1 and against pure PIO/CPU controls, not a selected replacement.

## Evidence boundaries

1. The contest brief is dynamic; treat 6 × 4 as the target until its official page says otherwise.
2. Competitor pages state their own measurements. Distinguish implemented hardware/physical evidence from proposals and estimates.
3. Literature numbers use different processes, metal stacks and back-end tools. Use them to select experiments, then obtain WARP CMOS5L measurements.
4. Keep the fresh held-out protocol set sealed before any successor tuning, per D-037. Existing WS2812, 1-Wire, SWD and CAN results have already been opened.
5. No new behavior is supported until it maps, routes, survives full-chip hardening, loads from a bitstream and passes end-to-end tests.
