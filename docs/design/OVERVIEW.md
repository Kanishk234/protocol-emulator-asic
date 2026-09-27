# WARP overview

## What we're building
A protocol emulator chip for the Jane Street ASIC competition (Tiny Tapeout, IHP 130 nm CMOS5L, 6x4 tiles, deadline 2027-01-18, our target 2027-01-11).

The chip is a small embedded FPGA (eFPGA) fabric behind a fixed management shell. A user writes a protocol as ordinary synthesizable Verilog, compiles it on a host computer into a bitstream, and loads it into the chip through the shell. Changing protocols changes the bitstream, not the silicon.

The fabric is **specialized for protocol emulation**. Instead of a general-purpose FPGA, every architectural choice is made for this one domain:

| Dimension | Options we will evaluate |
|---|---|
| Logic cell | LUT3 / LUT4 / fracturable; 1 or 2 flip-flops per LUT |
| Hard blocks | Protocol-agnostic primitives: timers, shift chains, CRC/LFSR, edge detectors, FIFOs |
| I/O cells | Synchronizers, edge detection, open-drain support, sampling features at the pad |
| Memory | None, LUT-based RAM, or an SRAM macro (for user data or configuration) |
| Configuration storage | Latches, flip-flops, SRAM; single or multiple contexts |
| Routing | Amount and pattern of interconnect; local connections between hard blocks, cells and pins |

## Why this can stand out
The brief says the judges favor novel designs, unique functionality, and novel design and verification methodology, and asks what we would do differently from RP2040 PIO or TI PRU. Most entries are expected to be small CPUs. Our answer is a different kind of machine, and our novelty comes from **how the architecture is chosen**, not from simply using an eFPGA (Tiny FABulous and PRISM already exist):

1. **Profile** real protocol RTL and measure which resources it actually uses.
2. **Specialize** the fabric where the profile shows a common need across several protocols.
3. **Compare at equal area** against a generic fabric, showing the coverage/performance tradeoff (a Pareto chart).
4. **Prove generality** on a held-out protocol set that was sealed before any architecture decision.
5. **Verify end to end**: from user Verilog, through the compiler and bitstream, to the loaded gate-level netlist.

## Protocol sets
- **Design set** (profiled, optimized for): UART TX/RX, SPI controller (4 modes), I2C controller (start, repeated start, stop, ACK/NACK, clock stretching), I2C target with a small register map.
- **Held-out set** (sealed in phase 1, evaluated in phase 4): chosen from 1-Wire, WS2812, SWD, PS/2, JTAG, CAN, or others. Recorded in `docs/design/HELDOUT.md`.
- **Showcase**: I2C target with RTL-controlled fault injection (selected NACK, inserted clock stretch), with host-readable status.
- **Not claimed**: low-speed USB and 10 Mbit Ethernet. Mentioned only if a later measurement supports it.

## Evaluation
For every candidate architecture at the same total area and clock target:
- **Coverage**: how many protocols fit (design set, later held-out set).
- **Performance**: maximum validated bit rate per protocol after place and route; reaction latency (cycles from pin event to response) where the protocol needs it.
- **Cost**: total area breakdown (logic, configuration, routing, hard blocks, shell), routing congestion, bitstream size, configuration time.

## Schedule
Dates are targets. Missing a date cuts feature scope before it cuts verification or physical validation. Adjust around exams; phase 4 needs no hardware changes, so it is the safest phase to run during finals.

| Phase | Dates | Outcome |
|---|---|---|
| 0 Setup | Sep 25 – Oct 4 | Repo, pinned tools, template flow and FABulous demo both working |
| 1 Profile, specify, de-risk | Oct 5 – Oct 25 | Held-out set sealed, design-set RTL, profiling data, tiny fabric hardened on CMOS5L, capacity go/no-go |
| 2 Baseline fabric + shell | Oct 26 – Nov 15 | G1 (generic fabric + hard counter/timer + shift register, D-008) + shell hardened at 6x4, design set running from real bitstreams: our fallback submission. G0 (plain fabric) is built and measured as the comparison baseline |
| 3 Specialize, compare, freeze | Nov 16 – Dec 6 | Specialized features added one at a time, equal-area comparison, hardware freeze |
| 4 Protocols and held-out | Dec 7 – Dec 22 | Showcase, held-out results, stretch protocols, reconfiguration and fault tests |
| 5 Evidence and docs | Dec 23 – Jan 5 | Evidence report, user guide, clean-checkout reproduction |
| 6 Submission | Jan 6 – Jan 11 | Submitted; Jan 12–18 is buffer only |
| 7 Hardware (optional) | Any time | FPGA prototyping; post-tapeout bring-up plan |

## Decision points
| When | Question | If the answer is bad |
|---|---|---|
| End of phase 0 | Does a FABulous fabric fit into the TT CMOS5L template flow at all (flat or as a macro)? | Investigate how Tiny FABulous did it; escalate to organizers; if blocked by Oct 10, consider the hybrid fallback |
| End of phase 1 | Using measured area per cell, does the design set fit in the estimated 6x4 capacity with plausible specialization? | Switch to the **hybrid fallback**: small PIO-style sequencers plus a small specialized LUT fabric for bit-level datapath (CRC, bit-stuffing, edge logic). Record in DECISIONS |
| End of phase 2 | Does G1 harden at 6x4, pass precheck, and run the design set? | Shrink the fabric; cut the I2C target to a smaller register map |
| End of phase 3 | Does any specialization beat G0 at equal area? | Report it honestly; freeze the best measured variant (possibly G0) |

Decision point outcomes so far: end of phase 0 → a known path exists (D-009); end of phase 1 → GO for the specialized eFPGA, not the hybrid (D-016).

## Top risks
Updated 2026-09-26 (end of phase 1). Status: **retired**, **open**, **new**.

| Risk | Status and evidence | Early warning | Response |
|---|---|---|---|
| FABulous fabric does not fit the TT CMOS5L flow | **Retired:** a 16-LUT fabric macro passes TT's template flow, precheck 9/9 and `gl_test` (run 36327510268, `fabric_tiny.md`) | The 4 × 3 fabric (larger macro) fails where the small one passed | Same placement rules (PHYSICAL_DESIGN_AND_CI), local pre-flight with TT's merged config |
| Capacity too small for the design set | **Open, quantified:** ~96 LUT4 generic; UART/SPI/I2C controller fit with timer + shift-register primitives, the **I2C target does not** (`capacity.md`) | Phase 2 place-and-route needs more LUTs than synthesis | Register-file primitive, smaller register map, or showcase on the I2C controller (D-016) |
| Custom blocks not usable by the tools | Open | Compiled designs don't use the block | Explicit instantiation first; drop the block if integration stalls |
| **Magic too old for the CMOS5L tech file** | **New, worked around:** Magic 8.3.623 vs the required 8.3.657 (BUGS #2) | A step needs Magic (e.g. LEF) | KLayout GDS + DRC, OpenROAD LEF; a newer Magic when LibreLane's pin moves |
| **Macro power grid in TT's CMOS5L block rules** | **New:** Metal4-only stripes, 2.1 µm, full height; the fabric's power columns must sit under them | `pdn_cfg.tcl` checks fail in CI | Gridded tile power stripes (D-017) and the R3 spike's checked script (D-019) |
| Routing congestion | Low for tiles (0 DRC at 95 % utilisation within Metal2–4) | Global-routing overflow in hardening | Reduce routing or fabric size; one change per hardening |
| Timing model optimistic | Open: nextpnr now reports Fmax from the hardened tiles' pip delays at the slow corner (counter4 162.6 MHz, D-022); how those delays were characterised is not yet documented, and no silicon or STA cross-check | Gate-level/STA disagree with nextpnr estimates | Recharacterize; add margin |
| **Ring oscillation while reconfiguring** | **New (D-023):** a half-written configuration can close an oscillating routing loop (seen in gate-level simulation when loading one design over another) | Load-time current; any design running during a load (impossible by F1/F2 parking) | Accepted: design held in reset and pins parked during loads; option: load an all-zero bitstream first |
| **Fabric macro netlist not checked against its RTL** | **New (D-023):** `gl_test` simulates the fabric from RTL; the gate-level macro ran real bitstreams once in CI (36342012141) | A tile netlist that differs from its RTL (synthesis bug, wrong tile version exported) | Per-tile formal equivalence (EQY) of netlist vs RTL, phase 2/3 |
| Host channel needs many fabric IO BELs | **New:** ~18–29 IOBUFs on the north edge (ARCHITECTURE §7.3) | Not enough IO tiles in the 4 × 3 grid | Narrow `h_status`, serialize the channel, or add IO tiles |
| **Prior art (PRISM)** | **New:** Verilog-programmed protocol engine on IHP exists (`docs/notes/prior_art.md`) | Judges see no difference | Claims rest on the parallel fabric, no CPU, and the measured, held-out-tested method |
| One builder, finals season | Open | Phases slipping | Cut stretch scope first |
