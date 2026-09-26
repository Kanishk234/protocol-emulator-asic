# Physical design and CI

Status: stub. Version 1 is written in phase 1.

## Hardening flow (how the fabric is integrated: flat or macro)
## Clock target and timing results
## Area breakdown (latest hardening)
Run 36170807513 (a63877d, placeholder adder), from `GDS_logs` `final/metrics.json`:

| Metric | Value |
|---|---|
| Die | 1289.28 × 710.64 µm = 916,214 µm² (template DEF `tt_block_6x4_pgvdd.def`) |
| Core | 902,417 µm² |
| Std cells (excluding fill) | 69 cells, 633 µm², utilisation 0.07 % (52 logic, 1 inverter, 16 timing-repair buffers) |
| Routed wirelength | 1,225 µm; routing DRC 0 after 3 iterations; antenna 0 |
| Magic DRC / LVS | 0 / 0 |
| Timing at 20 ns (worst corner) | setup WS +9.91 ns, hold WS +7.87 ns; no slew/cap violations |
| Power | 62 µW |
| Top-level settings (resolved) | `RT_MAX_LAYER` **Metal4**, density 60 %, CLOCK_PERIOD 20 |

**Consequence for the fabric macro:** the TT CMOS5L top level routes only up to Metal4 and uses TopMetal1 for power, so a fabric macro may need to keep its signals on Metal2–Metal4 (the first tile run used TopMetal1; `docs/reports/tile_cmos5l.md`). The die shape (1289 × 711 µm) fits at most 5 × 3 IHP-size LUT tiles plus edge tiles; 4 × 3 (96 LUT4s) leaves a ~220 µm column for the shell.
## Routing limits and congestion history
## Workflows (what runs where, and triggers)
| Workflow | Trigger | What it runs |
|---|---|---|
| `test` (template) | every push | cocotb pin-level suite in `test/`, Icarus 12 |
| `gds` (template jobs) | push touching `src/`, `arch/`, `macro/`, `test/`, `info.yaml`, `docs/info.md` or the workflow; manual | hardening, precheck, `gl_test`, viewer. Concurrency `gds-<ref>`, **no cancel-in-progress**: a newer push queues behind a running hardening |
| `docs` (template) | template default | datasheet build |
| `fpga` (template) | manual | iCE40 build of the template design |
| `lint` (ours) | every push | `info.yaml`/Makefile source-list sync; Verilator `-Wall` and Icarus `-g2005` lint |

Local equivalents: `scripts/check_all.sh` (lint + all simulation tests), `scripts/gl_local.sh` (gate-level on a Yosys netlist with TT's Icarus 13).

## Measured hardening time
| Date | Commit | Design | `gds` job | precheck | `gl_test` | CI run | Notes |
|---|---|---|---|---|---|---|---|
| 2026-09-25 | a63877d | placeholder adder, 6x4, template `config.json` | 35.1 min | 12.3 min | 0.7 min, pass | 36170807513 | All green. LibreLane 3.1.0.dev3 |

Budget: GitHub stops a job at 6 h. The empty 6x4 tile already costs about 35 min, most of it fixed-cost steps over the empty area, so a filled fabric will take longer; re-measure after the first fabric hardening.
