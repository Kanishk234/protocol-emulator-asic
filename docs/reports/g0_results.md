# Design-set protocols on G0 (plain fabric)

**Date:** 2026-09-27 · **Architecture:** `arch/warp_g0` (ARCH_VERSION 0x0002), 4 × 3 `LUT4x8_ha` = **96 LUT4+FF** (LCs), 36 IO cells · **Flow:** `tools/compile` (`python -m compile.protocols`), pin maps `protocols/*/pins.yaml`, profiling parameters (`tools/profiling/workload.py`), timing corner `nom_slow_1p08V_125C`, nextpnr seed 1 · Local run, not CI.

## Result

| Protocol | Fits? | LCs needed (nextpnr) | LUTs (of which carry) | FFs | IO cells | Why not |
|---|---|---|---|---|---|---|
| SPI controller (mode 0, 1 MHz SCK) | **no** | 95 (98 %) | 74 (11) | 45 | 17 | no legal placement at 98 %: the 8 LCs of a tile share enable/reset/clock resources, so a design needs headroom |
| UART (115200 baud) | **no** | 127 (132 %) | 98 (30) | 68 | 15 | too large |
| I2C controller (~100 kHz) | **no** | 160 (167 %) | 143 (14) | 65 | 15 | too large |
| I2C target (4 registers) | **no** | 205 (214 %) | 191 (16) | 79 | 15 | too large |

IO cells include the host channel (`h_*` ports, mapped by name, D-024). Timing is not reported for designs that do not place.

## What it means

- **None of the design set runs on plain G0.** This is the baseline D-008 and D-016 predicted from profiling (`docs/reports/profiling.md`, `capacity.md`), now measured with the real flow and place and route. The LC counts agree with the synthesis-only estimate (`python -m compile.fit`) within 1–2 LCs.
- **G1 (the timer and shift-register primitives) is required** for a fallback submission that runs protocols, and phase 3's specialization is measured against these numbers at equal area (D-004).
- The compile flow, the fabric model and the host channel are proven with smaller designs on G0 (`counter4`, `logic4`, `hostecho`: 7, 5 and 25 LCs, `test/test_bitstream.py`, RTL 17/17).

## Notes

- A first run left one `$mux` cell unmapped in the I2C target: the compile flow's `opt -full` after gate mapping ran `opt_share`, which creates coarse muxes nothing maps afterwards. The flow now runs plain `opt` there (numbers above). Sharing no longer happens at that point, so the I2C controller is 10 LCs larger than with it (150).

## Open
- Protocol input synchronizers are still in the protocol sources although the shell's IO cells synchronize (ARCHITECTURE §6); removing them saves a few LCs per design.
