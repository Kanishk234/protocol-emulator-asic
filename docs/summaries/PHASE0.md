# Phase 0: setting up the workshop

**Status:** complete (2026-09-23). All 11 exit-checklist items ticked with evidence (`docs/design/phases/PHASE0_SETUP.md`).

## The goal
Before designing a chip, make sure the whole pipeline from "Verilog file" to "manufacturable chip layout" works, using a trivial design, and that every tool in that chain runs, both on GitHub and on our own machines.

## What we did

**A placeholder chip.** An 8-bit counter that counts while an input pin is high. It has nothing to do with TRIPWIRE; it exists only to push something real through every tool.

**Every automated check on GitHub, all green:**

| Check | What it does | Result |
|---|---|---|
| `test` | Simulates the design and checks the counter really counts | ✅ |
| `gds` | Turns the Verilog into a real chip layout (the GDS file the fab prints from) | ✅ 79 logic cells in the 6x4 tile, timing met with lots of margin, about 30 minutes |
| `precheck` | Tiny Tapeout's "is this manufacturable?" checks | ✅ |
| `gl_test` | Re-runs our tests on the actual gate-level netlist, not on our Verilog | ✅ after a fix (below) |
| `viewer` | Publishes a 3D view of the layout on GitHub Pages | ✅ |
| `docs` | Builds the datasheet | ✅ after filling in `docs/info.md` |
| `fpga` | Builds an FPGA version | ✅ |

**Our local toolchain.** A Python virtual environment (always used for Python), the OSS CAD Suite simulators, and sigrok, an independent protocol decoder we use as a neutral referee throughout the project. Two helper scripts:
- `scripts/check_all.sh` runs every local check in one command;
- `scripts/gl_local.sh` runs the gate-level tests locally, the way CI does.

**The paperwork that keeps us honest.** `DECISIONS.md`, `BUGS.md`, `CLAIMS.md`, `docs/reports/AREA.md` and `WORKLOG.md`, so every choice and every bug is written down with its evidence.

**Early decisions.**
- The top module is `tt_um_tripwire`.
- We design for 6x4 tiles.
- Whether we may use the SRAM memory macro is settled by experiment in Phase 1 rather than by email.

## What we found
- **A bug in Tiny Tapeout's own template (BUGS #1).** The gate-level test failed for *any* design with flip-flops, because the template doesn't load the file that defines the flip-flop models. We reproduced it locally, confirmed the one-line fix, and CI went green on the real netlist.
- **A slow baseline.** Even an empty 6x4 tile takes about 30 minutes to harden, 25 of them spent on one design-rule check. No hardening run will ever be faster than that.
- **GitHub's 6-hour limit applies per job, not per workflow.** The job at risk is the hardening itself.

## In one line
Phase 0 proved we can go from code to a checked, manufacturable layout, and that every tool in that chain works.
