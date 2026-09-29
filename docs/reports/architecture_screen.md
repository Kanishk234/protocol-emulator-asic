# Successor architecture screen (initial)

**Date:** 2026-09-28 · **Status:** candidate screen only; G1 remains the baseline. This is not a physical implementation or an architecture selection.

## What the current fabric spends on

Generated G1 tile RTL reports 414 switch-matrix configuration bits out of 566 bits for each LUT tile, and 386 out of 430 for the primitive tile. Across 11 LUT tiles and one primitive tile, that is 4,940 of 6,656 stored bits (74.2%). It is a useful target for a routing experiment, but not a measurement that 74.2% of area is routing: configuration latches, mux trees, and switch choices have different physical costs. Configuration pruning must preserve routes used by a common workload and be checked with the router.

An illustrative 15% reduction in switch choices would remove about 741 configuration bits (11.1% of the total), before framing and alignment. There is no evidence yet that this pruning level preserves routability; it is a sweep point, not a proposed design.

## Generic event sequencer cost probe

To estimate the cost of the hybrid idea before adding it to `arch/`, a temporary, synthesizable RTL model was created under ignored `build/arch_explore/`. Each of two independent lanes has a writable instruction store, program counter, 16-bit countdown timer, 8-bit shift/data path, eight bidirectional pin controls, and generic NOP, pin-write, pin-sample, shift, timer-load, timer-wait/branch, pin-condition branch, and halt operations. The two lanes share the sampled pin bus. This is an intentionally small ISA model, not user-facing RTL or a finished spec.

Yosys 0.66+179 with the PDK's SG13G2 typical 1.20 V / 25 C Liberty produced the following mapped standard-cell area using `synth`, `dfflibmap`, `abc`, and `stat -liberty`:

| Program store | Words per image/lane | Two-lane mapped area | Sequential cell area | G1 LUT-tile standard-cell equivalents |
|---|---:|---:|---:|---:|
| private writable program per lane | 16 | 73,589 µm² | 44,482 µm² | 2.04 |
| private writable program per lane | 8 | 42,553 µm² | 25,572 µm² | 1.18 |
| shared writable program, two read ports | 16 | 47,992 µm² | 25,670 µm² | 1.33 |
| shared writable program, two read ports | 8 | 30,054 µm² | 16,166 µm² | 0.83 |

Reference: G1's hardened LUT tile is 36,047 µm² standard-cell area in a fixed tile footprint, and its primitive tile is 35,094 µm² (`D-026`, `docs/reports/capacity.md`). Sharing one program store across two independently advancing engines cuts this model by about 29–35% relative to separate stores; the 8-word shared image is about 0.83 LUT-tile standard-cell areas. The lanes retain separate PCs, timers, shift registers, and pin state, while the shared image is read through two combinational ports. Host writes use one address/data interface. Yosys mapped the inferred writable program arrays into flip-flops and muxes, not SRAM macros. The model does not yet implement protocol-correct wait/branch timing, lane ownership, FIFOs, line coding, full host safety, or an eFPGA interface. It is only a structural cost probe and is not a plausible final core estimate until repaired and verified.

### Cycle-defined shared-image prototype

The isolated `spikes/event_lanes/` prototype specifies two independently advancing lanes with independent PCs, 16-bit delays, shift/sample/output state and IRQs. Instructions support masked pin drive/release, pin-condition waits, delays, capture, branches, jumps, serial shift-in/out, NOP and halt. `spikes/event_lanes/run.sh` runs the two pin-level Verilog testbenches, warning-clean Verilator lint and 8-/16-word Yosys area screens.

The RAM test proves that one lane can stay blocked on an input while the other serializes four bits and halts; the first then sees the input, waits three clocks, captures, branches and halts. It also checks the RAM write lock, release behavior and shift-in/out ordering. A second test exercises the same lane logic with a static image, standing in for instruction bits held by the fabric's configuration latches. A third harness wires the lane channels through `warp_byte_bridge.v`, a user RTL one-byte elastic buffer with XOR transform, and has lane 1 serialize the transformed byte while both lanes run concurrently. All three testbenches pass. This exercises the proposed interface with actual synthesizable user logic, but the module connection is a simulation harness, not an integrated eFPGA bitstream path.

The existing WARP compile flow also compiles `warp_byte_bridge.v` independently to a G1 bitstream in `spikes/event_lanes/run.sh`: 17/88 LUT4s, 18/36 IOBUFs, a 722-word bitstream, and nextpnr estimated Fmax 212.77 MHz at `nom_slow_1p08V_125C`. The Fmax is a placement/timing-model estimate, not routed or chip timing. This confirms the bridge logic fits the current user fabric; it does not yet show that lane signals are wired to an actual WARP macro.

| Image policy | Words | Engine/mux logic area | Image cell area estimate | Combined mapped estimate | Comparison to G1 tile |
|---|---:|---:|---:|---:|---:|
| Runtime writable RAM | 8 | 33,451 µm² | included | 33,451 µm² | 0.93× |
| Static configuration image | 8 | 20,235 µm² | 192 × 30.8448 = 5,922 µm² | 26,157 µm² | 0.73× |
| Runtime writable RAM | 16 | 51,272 µm² | included | 51,272 µm² | 1.42× |
| Static configuration image | 16 | 25,542 µm² | 384 × 30.8448 = 11,844 µm² | 37,387 µm² | 1.04× |

Areas use Yosys/ABC with the SG13G2 typical Liberty; the static-image latch cost uses the area of SG13G2 `sg13g2_dlhq_1`. Ratios compare this library's standard-cell estimates to the measured CMOS5L G1 LUT-tile cell area (36,047 µm²) and are only rough screens. In particular, the static result excludes configuration routing, duplicated Q/QN needs if present, event-tile boundary logic, pin access and placement/routing effects. The RAM version uses DFFs, read muxes and a host write port. Moving the program image into existing-style configuration latches reduces the 8-word combined estimate by about 22% versus writable RAM, while doubling the image to 16 words costs about 43% more even with static configuration. The channel signals are accounted as RTL ports and logic but not as fabric routing resources. Eight words look like the better area point, but may be too little code for useful concurrent workloads. The user transform independently maps to 17/88 LUT4s, but the transform-to-engine path is not yet physically integrated. This is not an equal-area architecture win: the implementation lacks event-tile integration, FIFO buffering and a compiled end-to-end workload suite.

Next, generate an event tile whose instruction latches are part of the FABulous configuration map and whose ready/valid wires route through the existing fabric. Load the bridge bitstream and the engine image together, then run the serial-transform test through the full fabric simulation. Keep the engine output requests separate until a general pin-ownership/merge policy is specified; do not connect two lane outputs directly to pads. Compare the end-to-end hybrid with G1 at equal total area and clock target before considering any hardware change.

### New physical geometry opportunity: fit a 5 × 3 LUT grid

The current model rejects 5 × 3 because its macro leaves only 52.8 µm beside the shell. Keeping the existing 68.64 µm east and west I/O tiles and the estimated minimum 200 µm shell column, the interior LUT-tile width must be at most `(1289.28 − 200 − 2×68.64)/5 = 190.4 µm`, 13.4% narrower than the current 219.84 µm. The fixed die height can support an interior tile height up to `(710.64 − 2×56.70)/3 = 199.08 µm`. That suggests an experimental 190.4 × 199.08 µm tile target. At that geometry, a 5 × 3 grid could provide 112 LUT4s plus 2 timers/2 shifters with one primitive tile, or 104 LUT4s plus 4/4 with two primitive tiles. These are geometry estimates, not a fabric that has routed; the two-primitive option's tile standard-cell area is already close to this tighter slot.

The optimization target is realistic enough to investigate because published FABulous tile work reduced a standard-cell LUT4 tile's area by 21.7% through configuration-cell remapping and tile-interface pin remapping on SkyWater 130 nm using Innovus. This is a relevant method, not a transferable result: WARP uses IHP CMOS5L with fewer usable signal-routing layers and OpenROAD/LibreLane. The WARP tile currently routes at high utilization, so both remapping and congestion/routing margin must be measured. See [the accepted paper](https://pure.manchester.ac.uk/ws/portalfiles/portal/207833524/FPGA_2020_FABulous_optimizations_1_.pdf).

This screen says: **continue the hybrid prototype at 8 or fewer instructions per lane, and compare against replacing a LUT slot**. It does not yet show that the hybrid beats G1 at equal chip area. A full hybrid candidate must preserve useful LUT capacity, configure both the sequencer and fabric safely, and run an unrelated fabric task concurrently with a sequencer-driven link or monitor.

## Research findings that change the experiment

### Can the published tile optimization be run in WARP's pinned flow?

The installed FABulous-FPGA 2.2.0 Python package contains `TileAreaOptimisation` and a pin placer with `find_min_width`, `find_min_height`, and `balance` modes. However, WARP's CMOS5L tile spike does not call that API: `spikes/tile_cmos5l/run.sh` clones `mole99/fabulous-tiles` at `7999e5a`, whose `tiles.py` sets each macro's `DIE_AREA` from a fixed size table. The corresponding pinned Nix `librelane_plugin_fabulous` source has no `TileAreaOptimisation`, `FABULOUS_OPT_MODE`, or FABulous pin-placement step. The 2.2.0 package also depends on LibreLane 3.0.14, while the Nix tile flow uses LibreLane 3.0.0, OpenROAD dcf36133, and Yosys 0.62. So the optimization modes found in the Python environment are not a drop-in option for the proven CMOS5L run.

This does not rule out the paper's method. It means the next physical experiment needs either (a) a controlled backport of the needed optimization steps and pin placement into an ignored copy of the pinned tile flow, or (b) a sequence of fixed `DIE_AREA` scratch runs with changed pin order and explicit config-cell remapping. Start with a single LUT tile, save its pin/config mapping, and require placement, detailed route, DRC, and timing evidence before attempting a 5 × 3 fabric. Do not mix the FABulous 2.2 flow into G1's deliverable toolchain without a compatibility run.

- FABulous supports custom tiles, LUT variants, custom switch matrices, and custom configuration/switch cells. The design space is not limited to LUT size. The original FABulous paper describes that architecture flexibility: [WOSET 2021 paper](https://woset-workshop.github.io/PDFs/2021/a15.pdf).
- OpenFPGA's published flow likewise makes LUT size/fracturing, mux architecture, configuration memory, hard IP, and routing graph explicit parameters: [WOSET 2020 paper](https://woset-workshop.github.io/PDFs/2020/a19.pdf).
- A 2024 study reports gains from custom mux/configuration cells and routing-congestion optimization at 28 nm. Its numeric results are not CMOS5L predictions, but they support testing switch/configuration implementation as a separate candidate: [Microelectronics Journal study](https://doi.org/10.1016/j.mejo.2024.106544).
- The competition asks for a general purpose emulator and values distinctive function/design. The public brief names UART, SPI, I2C, USB low-speed and 10 Mbit Ethernet, and suggests JTAG, SWD, PS/2 and CAN: [Jane Street competition brief](https://blog.janestreet.com/protocol-emulator-asic-competition/). G1 currently proves sequential personalities. Independent timing engines plus spatial logic could demonstrate an additional capability, but only if the cost screen holds.
- Competitor README/architecture pages describe deadline-driven sequencers, multiple PIO engines, timestamp capture and filters. These are useful comparison ideas, not independently verified area or performance: [Tempo](https://github.com/satyaammu93/jane-street-asic-2026/blob/main/protocol_emulator/README.md), [BitLoom](https://github.com/sheehanmunim/bitloom), [GP_PAE](https://github.com/sjrai007/gp_pae/blob/main/ARCHITECTURE.md).

## Candidate order after deeper research

1. **G1 baseline** — preserve all present measured behavior and comparison evidence.
2. **Physical tile/configuration remapping** — test FABulous configuration-cell placement and tile-interface pin remapping in CMOS5L. Evaluate whether a 190.4 × 199.08 µm target allows a 5 × 3 grid with a ≥200 µm shell column. Check actual floorplan and route slack before full fabric work.
3. **Shared-program lanes coupled to user LUT logic** — repair the structural probe into a cycle-specified event engine; compare shared and private program memories, then map a concurrent lane plus fabric task. Keep the program image protocol-neutral.
4. **Routing graph shaping** — route the same designs across track/fan-in variants after the 5 × 3 question is answered; preserve direct/local paths and prune unsupported choices based on routing evidence.
5. **Trace/trigger and CRC/LFSR features** — add only after memory/area screens show they fit and they enable a concrete new demonstration.
6. **Pure sequencer or larger/fracturable LUT tiles** — controls for the best candidate; compare only with hardened area and representative workload results.

## Reproduction

Temporary inputs and raw logs are ignored in `build/arch_explore/` (`sequencer2_shared.v`, `sequencer2_shared_aw3.v`, `sequencer2_shared_imem.v`, and corresponding Yosys logs). The probe used `/home/younix/oss-cad-suite/bin/yosys` and `/home/younix/.cache/warp/pdk-full/ihp-sg13g2/libs.ref/sg13g2_stdcell/lib/sg13g2_stdcell_typ_1p20V_25C.lib`. This is SG13G2 standard-cell mapping, not a CMOS5L tile hardening result; it is an early size estimate only.
