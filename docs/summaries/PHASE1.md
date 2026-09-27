# Phase 1 summary: profile, specify, de-risk

**Status:** complete (2026-09-27). Every exit item passed; the template `fpga` workflow no longer applies (D-020).

## Goal
Find out, with measurements, what protocol logic actually needs and whether it fits on a 6x4 Tiny Tapeout chip; build the riskiest physical piece (a FABulous FPGA fabric on IHP CMOS5L, through Tiny Tapeout's own checks) early; write the specs everything else follows.

## What we did
- **Sealed the held-out protocols first** (WS2812, 1-Wire, SWD, CAN; commit 0171cf7), before any profiling, so they can later test whether the chip is general or just tuned to what we measured.
- **Wrote the four design-set protocols as user designs** (UART, SPI controller, I2C controller, I2C target): each with a reference model written first from the protocol spec, RTL tests in several configurations, and sigrok's decoders as an independent second check. All pass locally and in CI.
- **Profiled them** on generic LUT fabrics and attributed every LUT to what it does (`docs/reports/profiling.md`), then estimated capacity from measured numbers (`docs/reports/capacity.md`).
- **Built the physical path end to end**: hardened every FABulous tile type on CMOS5L, stitched a 16-LUT fabric (DRC clean), put it inside the Tiny Tapeout chip with FABulous's configuration loader, and got it through TT's hardening, precheck (9/9) and gate-level test (CI run 36327510268).
- **Wrote the specs**: ARCHITECTURE v1 (pins, host interface, loading with version/length/CRC checks, run control and parking, fabric resources, primitives), VERIFICATION v1 (check layers, formal properties with bounds), PHYSICAL_DESIGN_AND_CI v1 (flow, placement rules, results).

## What we found
- **Capacity decides everything.** One LUT4 costs ~5,100 µm² with its configuration and routing, so the chip holds ~96 LUT4s. A plain UART needs 144, the I2C target 240.
- **The LUTs go to the same few things in every protocol:** counters for bit timing (23 %), shift registers (17 %), storage (21 %, mostly the I2C target's register map). That is the case for a few *generic* primitives (a timer, a shift register), not protocol blocks. With them, UART, SPI and the I2C controller fit; the I2C target does not yet (D-016: GO for the specialized eFPGA; the I2C target stays open).
- **The physical flow works, and we know its traps:** Magic in our LibreLane is too old for the CMOS5L rules (worked around); TT's power rules needed a fabric power grid that lines up with the chip's (D-017); and a macro must be placed on that grid, with its pin-heavy faces toward open space and no narrow channel beside it (three failed CI runs taught those, BUGS #9–#11). A local run of TT's flow now catches these in minutes before pushing.
- **Prior art:** PRISM (a Verilog-programmed protocol engine on IHP) exists; WARP's case rests on a parallel LUT fabric with no CPU and a measured, held-out-tested method.

## What's left (phase 2)
The real shell (SPI host interface, checked loading, run control, host channels: ARCHITECTURE §2–4), the 4 × 3 fabric (G0 baseline and G1 with timers and shift registers), the compile flow from user Verilog to our bitstream, and gate-level tests that load real bitstreams.

## One-line takeaway
Protocols spend their logic on counters and shift registers and the chip holds only ~96 LUTs, so a few generic primitives are what make a protocol FPGA fit on Tiny Tapeout, and a FABulous fabric now passes Tiny Tapeout's real checks on CMOS5L.
