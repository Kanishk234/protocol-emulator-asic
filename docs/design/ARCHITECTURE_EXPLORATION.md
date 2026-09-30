# Architecture exploration: WARP successor

**Status:** exploration authorized by D-037; G1 remains the known-good baseline. No successor architecture has been selected.

## Goal

Find a small, reprogrammable communication fabric that handles varied interfaces well after fabrication. Keep the user-visible protocol behavior programmable and avoid dedicated UART, SPI, I2C, CAN, or USB blocks. Improve the architecture's useful work per unit area, independent concurrency, timing behavior, and ability to inspect or react to signals.

The [competition brief](https://blog.janestreet.com/protocol-emulator-asic-competition/) asks for a general-purpose protocol emulator, calls out unique functionality and design/verification methods, and names UART, SPI, I2C, low-speed USB, 10 Mbit Ethernet, JTAG, SWD, PS/2 and CAN as useful targets. The current brief describes 6x4 as the area limit and says 8x4 is still a possibility; treat 6x4 as the required baseline until the organizer confirms otherwise.

## Why revisit G1

G1 is a good baseline, not yet evidence that WARP is the best architecture for the task:

- It fits UART, SPI controller and I2C controller on its 88 LUT4 cells, plus three held-out designs on the frozen chip. The equal-area comparison is against a plain 96-LUT fabric (`docs/reports/architecture_comparison.md`).
- The current general primitives remove counter and shift-register cost, but control still takes 11–30 LUTs in the three fitting design-set examples. The limiting I2C controller is estimated at 53 MHz against the 50 MHz target (`docs/reports/g1_limits.md`).
- The current showcase proves sequential reconfiguration. It does not show two independently running communication functions or a protocol engine reacting to a separate monitor.
- Other public competition designs describe multiple programmed sequencer lanes and event capture ([Tempo](https://github.com/satyaammu93/jane-street-asic-2026/blob/main/protocol_emulator/README.md), [GP_PAE](https://github.com/sjrai007/gp_pae/blob/main/ARCHITECTURE.md)). Those are project-reported descriptions, not independently verified measurements. We need a measured comparison with these architectural ideas, not a claim based on labels such as eFPGA or PIO.
- The existing held-out protocols have been opened and used to evaluate G1. They are no longer independent test data for a revised architecture.

## Candidate families

Screen candidates cheaply first, then build only the promising ones in FABulous and the physical flow.

| ID | Candidate | Main hypothesis | Main risk |
|---|---|---|---|
| A | G1 baseline: LUT4 fabric + two timers + two shifters | Keep the verified reference point | Limited soft logic, no demonstrated concurrent personalities |
| B | Communication-shaped routing and logic tiles: reduce switch-matrix choices; evaluate alternative LUT width/fracturing and FF controls | Recover area from routes and configuration used by many designs | A smaller routing graph can make placements unroutable; LUT6 truth-table bits and muxes may erase logic savings |
| C | Hybrid eFPGA with generic sequencer tile(s) | Move repetitive pin/timing control into small independent event-driven engines while keeping arbitrary transforms/state in LUT logic | Sequencer state and program memory may consume too much area; compiler and bitstream integration are new work |
| D | Small multi-lane sequencer fabric | Establish the strongest temporal/PIO-style control baseline and test concurrency | Less arbitrary spatial logic and may duplicate published designs without a distinctive WARP advantage |
| E | Custom switch/configuration cells in the existing tile organization | Shrink the large population of routing muxes and configuration storage without changing the user fabric model | Custom transistor cells need CMOS5L layout, DRC, timing characterization, and robust integration |
| F | Generic bit-stream transform primitive (configurable LFSR/CRC, optionally bit insert/remove) | Test whether a shared framing/checksum datapath lets packet protocols use fewer LUTs | Benefit may be too narrow or too small to offset the tile and interconnect cost |
| G | FABulous-specific configuration/interface remapping; retile toward a 5 × 3 logic grid | Physical tile compaction could add a full column (24 LUT4s at one primitive tile) inside the same die | Published gains use a different PDK/back-end; the target tile has little placement/routing margin |
| H | Shared instruction image across multiple generic event engines with private lane state | Amortize code storage and scale repeated endpoints more efficiently | Benefit depends on common firmware; two independent fetch ports and the engine/fabric interface still cost area |

## Initial architecture screen

The current fabric's configuration structure gives a concrete first target. The generated G1 tile RTL reports 566 configuration bits per LUT tile, of which 414 belong to its switch matrix; the primitive tile has 430 total, of which 386 are switch-matrix bits (`macro/warp_g1/rtl/{LUT4x8_ha,PRIM2T2S}_ConfigMem.v` and corresponding `_switch_matrix.v`). G1 has eleven LUT tiles and one primitive tile:

- Total configuration state: `11 × 566 + 430 = 6,656` bits.
- Switch-matrix configuration: `11 × 414 + 386 = 4,940` bits, about 74% of the configuration state.
- LUT/carry/primitive configuration: `6,656 − 4,940 = 1,716` bits.
- The current example bitstream is 722 32-bit words (23,104 transmitted bits), so the routed fabric stores fewer than one in three transmitted bits as configuration state. Frame padding and headers are part of this overhead.

This count does not prove that 74% of tile area is switch matrix: different bits drive muxes and the mux trees themselves also consume area. It does show that reducing the routing graph's mux fan-in, number of tracks, or switch choices is the first fabric-native candidate to measure. Start with a routability sweep, not arbitrary wire deletion. Test each proposed routing pattern on the same protocol matrix and record both configuration-bit count and hardened tile area.

The current LUT6 profiling is also a screen, not an area result. It maps the UART from 144 LUT4s to 102 LUT6s, but each LUT6's 64 truth-table bits are four times the 16 bits of a LUT4; the tile must be built and hardened before deciding whether that trade is favorable (`docs/reports/profiling.md`). FABulous supports custom and fracturable logic tiles, custom switch matrices, and custom configuration/switch cells ([FABulous paper](https://woset-workshop.github.io/PDFs/2021/a15.pdf)). An eFPGA physical-design study reports area and timing gains from custom mux/configuration cells and wiring optimization at 28 nm; its percentages are motivation to measure this in CMOS5L, not predictions for WARP ([study DOI](https://doi.org/10.1016/j.mejo.2024.106544)).

The sequential-engine candidate needs to add something beyond copying current public PIO designs. BitLoom documents deadline-based timing, timestamp capture and four engines; Tempo documents two engines with capture and response. Treat these as useful feature baselines, not verified PPA results ([BitLoom](https://github.com/sheehanmunim/bitloom), [Tempo](https://github.com/satyaammu93/jane-street-asic-2026/blob/main/protocol_emulator/README.md)). The distinctive WARP hypothesis is a **hybrid**: generic independently paced event sequencers for deterministic pin timing, connected to a reconfigurable spatial datapath that can be changed as arbitrary user RTL. Its go/no-go test is whether this composition fits at equal whole-chip area and executes a sequencer-driven link while the LUT fabric performs a second independent task or analyzes captured events.

The generic bit-stream primitive should be screened on shared functions rather than a protocol name. A programmable CRC/LFSR can serve 1-Wire (CRC-8), CAN (CRC-15), USB (CRC-5/CRC-16), and other serial links. First measure the combinational/sequential cost attributed to CRC, framing, and bit insertion/removal in the RTL workload matrix. Do not assume one CRC unit makes CAN fit: the existing CAN design is 207 cells against G1's 88, and a shared CRC will only address part of that cost.

The initial quantitative screen is recorded in [`docs/reports/architecture_screen.md`](../reports/architecture_screen.md). It found that 74.2% of configuration bits are switch-matrix choices and that a simple two-lane, 8-instruction-per-lane sequencer maps to about 1.18 G1 LUT-tile standard-cell areas before routing and integration. These measurements prioritize candidate experiments; neither number establishes a whole-fabric area win.

Broader literature and competitor research changed the candidate priority: first test FABulous-specific configuration and tile-interface remapping, because a 190.4 × 199.08 µm tile could permit a 5 × 3 grid (112 LUT4s with one primitive tile). The same screen suggests sharing an 8-word instruction image across two lanes could reduce a simplified model to 0.83 LUT-tile standard-cell areas before integration. Detailed evidence boundaries and research links are in [`docs/reports/architecture_research.md`](../reports/architecture_research.md).

The leading combined hypothesis is a denser spatial WARP fabric, enabled by CMOS5L-validated tile compaction, plus a compact multi-lane generic event engine that shares its instruction image and connects to user LUT logic. This direction builds on the eFPGA's spatial behavior rather than positioning WARP as another standalone PIO clone. Engines should expose protocol-neutral pin sample/drive/direction, event wait, relative/absolute time, data movement, bounded queues, capture and branch operations. The proof point is user logic in the fabric coordinating an emulator lane with an independent live monitor or transform lane. No candidate is selected yet.

### First event-lane prototype

`spikes/event_lanes/` now contains a written 24-bit instruction format, two-lane RTL, and RAM/static-image simulation tests. The lanes have separate PCs, delays, captured pins, serial shifters, and ready/valid byte channels. With an 8-word image, the writable version maps to 33,451 µm² in SG13G2 typical Liberty. The static version, including an estimated 192 configuration latches, maps to 26,157 µm²; a 16-word static image rises to 37,387 µm². Those are rough cross-library area ratios, not placed results. A third test wires a real one-byte transform/elastic-buffer RTL block between a timed receiver and transmitter and passes concurrently. That user block independently compiles to G1 at 17/88 LUT4s and estimated Fmax 212.77 MHz, but the event-lane signals are only connected through a simulation harness; there is no integrated tile or bitstream path. PRISM already has multiple sequencers and datapaths, so the event engine is only useful to WARP if the arbitrary fabric performs measurable live transformations beside the timed lanes. See `docs/reports/architecture_screen.md`; this remains a candidate, not a selected architecture.

Candidate B is a lower-risk test of the current eFPGA identity. Begin with the existing LUT3/LUT4/LUT6 mapping data, but do not infer area from LUT counts: create and harden a candidate tile with the real configuration latches, switch matrix, routing and IHP library. Existing measurements show LUT6 reduces abstract LUT counts, while its configuration requires four times the bits of a LUT4 (`docs/reports/profiling.md`).

### Current successor priorities (2026-09-30)

The latest physical results make the work order clearer. **First, establish a physically viable 5 × 3 shell integration.** The site-aligned 5 × 3 fabric is 1120.32 × 703.08 µm and has a clean stitched-GDS DRC, but the full shell has not routed. With the east blockage removed and repair disabled, the reduced-configuration proxy at x=121.44 reached global routing with 2,705 total overflow across routing layers and 132,588 µm wirelength. Moving it to x=100.0 under matching settings gave 2,818 overflow and 136,483 µm wirelength; x=90.0 worsened to 2,960 overflow and 147,369 µm (`runs/cfgmacro_x{100,90}_open/37-openroad-globalrouting/`). Among the three tested positions, x=121.44 is best, though still congested. The earlier shorthand 13,770 was the total routing demand, not overflow. At x=121.44, lowering the extra post-CTS hold margin from 0.1 ns to 0 let 281 hold buffers legalize (the 0.1 ns run inserted 446 and failed detailed placement on 13 instances); the matching x=100.0 run inserted 441 and failed on 34 (`runs/cfgmacro_x121_holdmargin0/36-openroad-resizertimingpostcts/`). The zero-margin case reached detailed routing, which ended its 16 configured optimization passes with 536 violations, including 527 Metal4 shorts (`runs/cfgmacro_x121_holdmargin0/38-openroad-detailedrouting/`). DRC XML examples place signal-to-VPWR shorts at x=132.39–134.49 µm, coincident with the macro's VPWR strap at local x=10.95–13.05 µm after x=121.44 placement. This points to a possible signal-pin access/PG abstract conflict that needs LEF/GDS/DEF overlay before attributing the shorts to the fabric routing graph. Global routing still had 2,648 overflow and 163,404 µm wirelength. The result shows that placement margin contributes to legalization failure, but it is neither a route pass nor timing signoff: the run uses a configuration-macro proxy, route-only PDN, and a black-box fabric with no timing model. Keep the 0 ns setting as an experiment, not a production flow choice, until real macro timing and hold signoff are available.

For the architecture itself, keep these as the evidence-ranked improvement paths:

1. **Improve spatial-fabric efficiency and physical locality.** Measure sparse, tile-aware switch graphs and tile pin remaps against the workload route set. G1 spends 4,940 of 6,656 configuration bits (74.2%) on switch choices, but this is not an area fraction; mux count, route completion and congestion decide whether a graph is better. The long east-facing route-guide extents in the current 5 × 3 shell screen make boundary pin placement and local routing a first-order issue. Preserve all routes needed by the workload matrix and compare at equal whole-chip area and clock.
2. **Test a small temporal engine beside arbitrary LUT logic.** The candidate is a few independently paced, protocol-neutral event lanes with shared instruction storage, private lane state, pin sample/drive, timed waits, capture and bounded ready/valid queues. The distinguishing test is a live timed link plus independent user-compiled LUT logic transforming or monitoring it. Current lane area figures are cross-library estimates and the current connection is a simulation harness, so first prove integration, bitstream configuration, area and timing before expanding the ISA or lane count.
3. **Reduce configuration-boundary cost.** Keep configuration distribution or an adapter inside a composite fabric macro where feasible, exposing a compact shell-facing interface. The proxy result suggests hiding hundreds of configuration pins can lower shell routing burden, but the real macro must retain configurable state, legal power access, timing arcs and end-to-end loading through the shell.
4. **Defer dedicated datapath cells until workload evidence supports them.** CRC/LFSR, framing and capture primitives can help multiple links, but profile their shared benefit and full physical cost before adding them. Do not use a protocol-specific controller as a hard block.

The comparison order should be: keep G1 as the executable fallback; first get one compact spatial candidate through real compile/load, full-shell PDN, timing repair, detailed route, DRC and gate-level tests; then compare the temporal hybrid against that candidate at equal total area and clock. A candidate that only fits a reduced proxy, maps well in a different library, or succeeds on one workload is not a reason to replace G1. Use new, sealed held-out protocols for final generality evidence; the already opened set is training data for successor work. Existing sequencer-lane competitors make engine count and instruction-store sharing useful baselines, not novelty claims. The research sources and their limits are listed in [`docs/reports/architecture_research.md`](../reports/architecture_research.md).

## Evaluation method

### Workloads

Build a workload matrix that separates protocol family from endpoint role and implementation style:

- Async serial: UART TX/RX and PS/2 host/device.
- Synchronous serial: SPI master/slave, JTAG, and SWD physical engine.
- Open-drain, clocked bus: I2C controller and a deliberately bounded I2C target.
- Timed pulse/one-wire: WS2812 and 1-Wire.
- Encoded/packetized links: CAN and the competition's low-speed USB / 10BASE-T stretch goals where schedule permits.
- Instrumentation: edge capture, pulse-width/timestamp measurement, trigger-response, and one protocol function running concurrently with a monitor.

Use existing implementations and results as training data. Select a new held-out set from protocols not used to tune the successor, record its exact scope and criteria in a sealed file/commit before architecture work uses it, and open it only for final comparison. Do not reuse the old held-out label for already-open WS2812, 1-Wire, SWD and CAN results.

For each workload record: correctness against an independent model; LUT/FF/configuration-bit use; routed fit; maximum validated line rate; edge-response latency and jitter; pin use; host bandwidth needed; resource contention; and whether the function runs concurrently with another workload. Include realistic endpoint roles (master, target, transmitter, receiver, passive monitor) instead of treating a protocol name as one workload.

### Fair comparison

- Hold total chip area, shell/pin budget and 50 MHz base clock constant. Report separately if the organizers authorize a larger area.
- For throughput and response latency, report both synthesis/timing-model estimates and physical timing evidence. A candidate does not pass a clock target because nextpnr produced a bitstream with timing failure allowed.
- Count configuration storage, switch matrix, routing, sequencer program memory, shell, host link, and clock/reset infrastructure. Compare whole-chip totals, not just fabric logic cells.
- Use the same protocol sources or matched specifications across candidates. Report unsupported roles and host assumptions explicitly.
- Keep G1 runnable and tested as a fallback until a candidate completes the full compile, load, simulation, formal, hardening and gate-level path.

## Proposed gates

1. **Baseline audit:** confirm G1 metrics and exact area from committed reports; catalog supported roles, rates, host service, timing and concurrency. No hardware edit.
2. **Fast screen:** use profiling, Yosys and small RTL models to rank candidates B/C/D by estimated area and critical behavior. Discard candidates that fail the rough area budget before integrating tools.
3. **Fabric prototype:** build at most the top two candidates as separate architecture versions, preserve independent compiler/bitstream tests, and prove the reusable primitives against specifications.
4. **Equal-area comparison:** compile and route the training matrix, including concurrency and capture/response workloads. Select the Pareto-best candidate, or keep G1 if none improves the objective.
5. **Generalization check:** evaluate the sealed protocols without tuning. Report all failures and tradeoffs.
6. **Submission candidate:** harden the chosen complete chip, check timing and routing, load bitstreams through the real shell, and run gate-level protocol tests. Only then update `arch/CURRENT` and replace G1 as the preferred submission.

## Decision rule

Do not optimize for raw protocol count alone. A successor should keep the required UART/SPI/I2C use cases, improve the number of unrelated communication roles that fit, and demonstrate a distinct capability such as simultaneous protocol emulation plus triggered observation. Reject an architecture that wins only by assuming a protocol-specific hard block, a larger shell/pin budget, unmeasured timing, or data from its test set.

The output of this exploration is an evidence-based architecture choice and a functioning implementation. It is not a prediction that any one design will win the competition.
