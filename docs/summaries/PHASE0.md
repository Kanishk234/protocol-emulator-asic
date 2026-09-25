# Phase 0 summary: setup (in progress)

**Status:** nearly complete (2026-09-25). Open: organizer email (parked by the user), cell/utilisation numbers from the `gds` logs (need a GitHub login to download), and "all CI green on `efpga`" at the phase close.

## Goal
Get a working repository where both flows run end to end on trivial designs: Tiny Tapeout's chip flow (RTL to layout, on IHP CMOS5L at 6x4 tiles) and the FABulous FPGA flow (fabric, user Verilog, bitstream, simulation). Pin every tool version. Find out whether a FABulous fabric can go through Tiny Tapeout at all.

## What we did
- Set up the repo from the CMOS5L template on the `efpga` branch (`main` holds the separate TRIPWIRE design). Filled `info.yaml` and the datasheet so TT's docs check passes, renamed the top module to `tt_um_warp`, fixed the template's gate-level test (BUGS #1).
- Added local scripts (`setup_venv`, `check_all`, `gl_local`) and our own CI workflows: `lint`, and `fabric`, which runs the FABulous flow in CI.
- Ran the full chip flow on the placeholder design in CI: hardening 35 min, precheck and gate-level test green.
- Ran FABulous: built its stock fabric, compiled two different designs to bitstreams, loaded both into the same simulated fabric, and showed each one runs, and that swapping them is detected (locally and in CI).
- Studied Tiny FABulous (an FPGA already on Tiny Tapeout) and PRISM (a Verilog-programmed protocol engine already on IHP).
- Hardened one real FABulous tile (8 LUT4s) on CMOS5L.

## What we found
- **It can be built on our process.** Tiny FABulous shows the path (tiles, then fabric, then chip). One tile routed cleanly on CMOS5L at IHP's size and 97 % density, even though CMOS5L has only 5 metal layers.
- **Capacity is the main constraint.** Each LUT4 costs about 5,100 µm² with everything included, so the 6x4 chip holds about **96 LUT4s**. A plain UART needs about 215. A generic fabric cannot even fit one required protocol, so general hard blocks (counters/timers, shift registers) are needed to fit the design set at all. The fallback is now the generic fabric plus those blocks (D-008).
- **PRISM is close prior art:** Verilog to bitstream on IHP, with a fixed datapath of counters, shifters, CRC and FIFOs. Our case has to rest on what differs: a parallel LUT fabric, no CPU, and a measured, held-out-tested method for choosing the hard blocks.
- Tool pitfalls, now documented: FABulous 2.2 needs an older Yosys (OSS CAD Suite 2026-06-29); its wrapper generator only wires its own demo design; Magic hangs exporting a CMOS5L tile (BUGS #2).

## What's left
Organizer email; the `gds` log numbers; the phase close. Then phase 1: seal the held-out protocols, write the design-set protocols, profile them against a ~96-LUT budget, and harden a small fabric.

## One-line takeaway
Both flows work and a FABulous tile builds on CMOS5L, but only ~96 LUTs fit, so specialization is what makes the chip work at all, not an optional improvement.
