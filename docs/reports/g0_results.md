# Design-set protocols on G0 (plain fabric)

**Date:** 2026-09-27 · **Architecture:** `arch/warp_g0` (ARCH_VERSION 0x0002), 4 × 3 `LUT4x8_ha` = **96 LUT4+FF** (LCs), 36 IO cells · **Flow:** `tools/compile` (`python -m compile.protocols --arch arch/warp_g0 --set PRIMS=0`), pin maps `protocols/*/pins.yaml`, profiling parameters (`tools/profiling/workload.py`), timing corner `nom_slow_1p08V_125C`, nextpnr seed 1 · Local run, not CI.

## Result (current flow)

| Protocol | Fits? | LCs (nextpnr) | LUTs (of which carry) | FFs | IO cells | Fmax (slow corner) |
|---|---|---|---|---|---|---|
| SPI controller (mode 0, 1 MHz SCK) | **yes** | 86 (90 %) | 76 (11) | 45 | 17 | 68.0 MHz |
| UART (115200 baud) | **no** | 124 (129 %) | 98 (30) | 68 | 15 | - |
| I2C controller (~100 kHz) | **no** | 115 (120 %) | 106 (14) | 58 | 15 | - |
| I2C target (4 registers) | **no** | 184 (192 %) | 142 (16) | 73 | 15 | - |

IO cells include the host channel (`h_*` ports, mapped by name, D-024). Timing is not reported for designs that do not place. All designs in their plain-logic form (`PRIMS=0`), the same sources as on G1 (`docs/reports/g1_results.md`).

## What it means

- **Plain G0 runs one of the four** (the SPI controller, at 90 %). This is the baseline D-008 and D-016 predicted from profiling (`docs/reports/profiling.md`, `capacity.md`), measured with the real flow and place and route.
- **G1 (the timer and shift-register primitives) is required** for a fallback submission that runs UART and I2C; phase 3's specialization is measured against these numbers at equal area (D-004).
- The compile flow, the fabric model and the host channel are proven with smaller designs on G0 (`counter4`, `logic4`, `hostecho`, `test/test_bitstream.py`, RTL 17/17, CI `gl_test` 17/17 in 36353540402).

## History

- **First run** (same date): SPI 95 LCs, no legal placement at 98 %; UART 127, I2C controller 160, I2C target 205. The SPI failure was BUGS #15 (the 8 LCs of a tile share one clock enable and one set/reset; one-flip-flop enables used up tiles). The flow now turns enables and resets used by fewer than 4 flip-flops into logic, which also shrank every design.
- **I2C target 205 → 184:** shared register ports for bus and host, plain flip-flops instead of an inferred memory, no own synchronizers (`protocols/i2c_target/test` passes).
- **I2C controller 160 → 115:** the design lost its own input synchronizers (the shell synchronizes every input, ARCHITECTURE §6) and three wait states (the high-phase timer is held until SCL reads high); same tests pass (`protocols/i2c_ctrl/test`).
- A first run left one `$mux` cell unmapped in the I2C target: the compile flow's `opt -full` after gate mapping ran `opt_share`, which creates coarse muxes nothing maps afterwards. The flow runs plain `opt` there.

## Open
- UART and SPI still carry their own input synchronizers (ARCHITECTURE §6 makes them unnecessary); removing them saves a few LCs each.
