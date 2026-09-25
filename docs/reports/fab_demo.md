# Phase 0: FABulous reference demo (two bitstreams, one fabric)

**Date:** 2026-09-25 · **Commit:** 1a3ba74 (spike), local run in WSL; **CI:** `fabric` run 36196784852 on bc46bff, green
**Reproduce:** `spikes/fab_demo/run.sh` (work dir `build/fab_demo`, git-ignored). Tool versions: `docs/VERSIONS.md` (FABulous 2.2.0, OSS CAD Suite 2026-06-29).

## What was run
The stock FABulous 2.2 project (`FABulous create-project`, unchanged: frame-based config, LUT4AB / RegFile / DSP / RAM_IO columns, 672 logic cells, default PDK `ihp-sg13g2`) is generated once, then two user designs are compiled to bitstreams and simulated in Icarus. The testbench loads each bitstream through the fabric's own configuration port (`SelfWriteData`/`SelfWriteStrobe`, 32 bits per write) and compares the fabric's pins with the source design, cycle by cycle, for 100 cycles.

| Step | Bitstream | Compared against | Expected | Result |
|---|---|---|---|---|
| 1 | A: stock `sequential_16bit_en` (16-bit counter) | its own source | match | match, 100/100 cycles |
| 2 | B: `spikes/fab_demo/lfsr_down.v` (16-bit LFSR + 8-bit down-counter, 2 output enables) | its own source | match | match, 100/100 cycles |
| 3 | B | A's source | mismatch | mismatch from the first cycle (`0x0fface1` vs `0x0000000`) |

Step 3 shows the fabric really runs a different design from bitstream B and that the comparison can tell them apart.

| Design | Logic cells used | nextpnr Fmax (demo timing model) | Bitstream |
|---|---|---|---|
| A | 32 / 672 | 16.53 MHz | 12,024 bytes |
| B | 32 / 672 | 32.79 MHz | 12,024 bytes |

The Fmax numbers come from FABulous's generic demo timing model, not from an implemented CMOS5L fabric. They are **not** a claim about our chip.

## Findings for our flow
1. **Yosys version matters.** OSS CAD Suite 2026-09-25 fails in `synth_fabulous` (`Global_Clock` and `IO_1_bidirectional_frame_config_pass` not found; `share/yosys/fabulous/` only has `cells_bb.v`). FABulous 2.2 pins 2026-06-29 in its own source; that release works. Any CI job that runs FABulous must pin the same release.
2. **FABulous's wrapper generator only wires its own demo design.** For any other design, `gen_user_design_wrapper` leaves `io_in/io_out/io_oeb` unconnected and Yosys removes the whole design (0 LUTs, fabric outputs all 0). Workaround here: reuse the stock wrapper and swap the module name. Our `tools/compile/` needs its own wrapper generator that maps user ports to the shell's pins.
3. **The stock Taskfile path fails on its own** (`task build-test-design` without the wrapper step: `Global_Clock` not in design). Use the FABulous CLI script flow (`FABulous -p <proj> script <file>.tcl`).
4. Full flow time: about 40 s to generate the fabric, about 1 min to compile a design, about 1 min to simulate (the 16 KB bitstream load dominates).
