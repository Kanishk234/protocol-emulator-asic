# Phase 1 summary: profile, specify, de-risk (in progress)

**Status:** nearly complete (2026-09-26). Open: the chip-level hardening of the tiny fabric (CI `gds` run 36277723397, then precheck) and "all CI green" at the phase close.

## Goal
Find out, with measurements, what protocol logic actually needs and whether it fits on a 6x4 Tiny Tapeout chip; build the riskiest physical piece (a FABulous fabric on IHP CMOS5L) early; write the specs everything else follows.

## What we did
- **Sealed the held-out protocols first** (WS2812, 1-Wire, SWD, CAN; commit 0171cf7), before any profiling, so they can later test whether the chip is general or just tuned to what we measured.
- **Wrote the four design-set protocols as user designs** (UART, SPI controller, I2C controller, I2C target): each with a reference model written first from the protocol spec, RTL tests in several configurations, and sigrok's decoders as an independent second check. All pass locally and in CI.
- **Profiled them** on generic LUT fabrics and attributed every LUT to what it does (`docs/reports/profiling.md`).
- **Built the physical path**: hardened every FABulous tile type on CMOS5L, stitched a 16-LUT fabric (DRC clean), and put it inside the Tiny Tapeout chip with a configuration loader (`docs/reports/fabric_tiny.md`).
- **Wrote the specs**: ARCHITECTURE v1 (pins, host interface, loading with version/length/CRC checks, run control and parking, fabric resources, primitives), VERIFICATION v1 (check layers, formal properties with bounds), PHYSICAL_DESIGN_AND_CI v1.

## What we found
- **Capacity decides everything.** One LUT4 costs ~5,100 µm² with its configuration and routing, so the chip holds ~96 LUT4s. A plain UART needs 144, the I2C target 240.
- **The LUTs go to the same few things in every protocol:** counters for bit timing (23 %), shift registers (17 %), storage (21 %, mostly the I2C target's register map). That is the case for a few *generic* primitives (a timer, a shift register) rather than protocol blocks. With them, UART, SPI and the I2C controller fit; the I2C target does not yet (D-016: GO for the specialized eFPGA; the I2C target stays open).
- **The tools had traps:** the Magic layout tool shipped with our LibreLane is older than the CMOS5L rules need (worked around with KLayout and OpenROAD), and TT's power-grid rules forced a fabric power grid designed to line up with the chip's (D-017).
- **Prior art:** PRISM (a Verilog-programmed protocol engine on IHP) exists; WARP's case rests on a parallel LUT fabric with no CPU and a measured, held-out-tested method.

## What's left
- The first chip-level hardening with the fabric (running) and its precheck.
- Phase 2: the real shell (ARCHITECTURE §2–4), the 4 × 3 fabric, the compile flow from user Verilog to our bitstream, and gate-level tests with real bitstreams.

## One-line takeaway
Protocols spend their logic on counters and shift registers, the chip can hold only ~96 LUTs, so a few generic primitives are what make a protocol FPGA fit on Tiny Tapeout, and the physical path to build it on CMOS5L now exists.
