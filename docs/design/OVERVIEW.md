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
| 2 Baseline fabric + shell | Oct 26 – Nov 15 | Generic fabric (G0) + shell hardened at 6x4, design set running from real bitstreams — this is our fallback submission |
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
| End of phase 2 | Does G0 harden at 6x4, pass precheck, and run the design set? | Shrink the fabric; cut the I2C target to a smaller register map |
| End of phase 3 | Does any specialization beat G0 at equal area? | Report it honestly; freeze the best measured variant (possibly G0) |

## Top risks
| Risk | Early warning | Response |
|---|---|---|
| FABulous fabric does not fit the TT CMOS5L flow | Phase 0/1 tiny fabric fails hardening or precheck | Smallest reproducer, ask organizers/TT community, fall back as above |
| Capacity too small for the design set | Phase 1 profiling vs. measured area per cell | Specialize harder, reduce showcase scope, or hybrid fallback |
| Custom blocks not usable by the tools | Compiled designs don't use the block | Explicit instantiation first; drop the block if integration stalls |
| Routing congestion | Global-routing overflow in hardening | Reduce routing or fabric size; one change per hardening |
| Timing model optimistic | Gate-level/STA disagree with nextpnr estimates | Recharacterize, lower supported clock and rates |
| One builder, finals season | Phases slipping | Recruit a teammate early; cut stretch scope first |
