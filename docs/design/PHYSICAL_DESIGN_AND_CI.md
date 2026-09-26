# Physical design and CI

Status: v1, written 2026-09-26 (end of phase 1). Chip-level results of the first fabric hardening are added when CI run 36277723397 finishes.

## Hardening flow (how the fabric is integrated: flat or macro)
**Macro, three levels** (the Tiny FABulous method, D-009), all on IHP CMOS5L:
1. **Tiles** (`spikes/tile_cmos5l/run.sh <TILE>`, local, Nix LibreLane 3.0.0 + FABulous plugin): each tile type is hardened on its own with the `FABulousTile` flow from `mole99/fabulous-tiles` 7999e5a + `cmos5l.patch` (D-010). Signals on Metal2–Metal4 (TT's chip-level limit); Metal4 power stripes 2.1 µm wide on the 109.92 µm grid (D-017); KLayout writes the GDS, OpenROAD the LEF, Magic is skipped (BUGS #2). ~1–7 min per tile.
2. **Fabric** (`spikes/fabric_tiny/run.sh`, local): the `FABulousFabric` flow stitches the tiles by abutment into one macro, adds the IHP placement boundary (189/4) and exports GDS, LEF, netlists (fabric + tiles), fabric RTL and the bitstream spec to `macro/<fabric>/` (committed). ~8 min for the 16-LUT fabric; KLayout DRC 0.
3. **Chip** (CI `gds` job, TT's LibreLane 3.1.0.dev3): the template flow places the macro from `src/config.json` `MACROS` (on the Metal2/Metal3 track grid), synthesizes the shell around it, and builds the power grid with `src/pdn_cfg.tcl` (from the R3 spike: stripes pass over the macro only inside its same-net power columns, and the step fails otherwise). Precheck and `gl_test` follow.

Why a committed macro instead of hardening the fabric in CI: tile + fabric hardening needs the FABulous LibreLane plugin (Nix), which the TT action does not have, and it keeps each `gds` run to one hardware change (CLAUDE.md). The macro is rebuilt locally whenever `arch/` (later) or the tile patch changes.

**Magic:** the Nix LibreLane 3.0.0 environment has Magic 8.3.623; the PDK's CMOS5L tech file needs ≥ 8.3.657. TT's CI has its own newer tools, so chip-level Magic steps run there.

## Clock target and timing results
- Target: `clk` 50 MHz (`CLOCK_PERIOD` 20 ns), shell and user design (ARCHITECTURE §5).
- Shell timing: from the chip-level STA (to be filled from run 36277723397).
- **Fabric timing: not measured yet.** Tiles are hardened without a clock; the fabric flow produces a physical timing model (`FABULOUS_TIMING_MODEL: PHYSICAL`) for nextpnr, used in phase 2 to state each user design's achieved rate.

## Known limits (phase 1)
- No LVS for CMOS5L in the PDK (KLayout LVS disabled in its config); TT's chip-level LVS covers the shell, the macro is checked by DRC and by its netlist.
- Magic-based steps are skipped at tile and fabric level (BUGS #2).
- Power: the chip stripe pitch is 109.92 µm instead of the template's 50 µm (D-019); IR drop to be read from the chip-level run.
- The 16-LUT spike fabric's edge/IO tiles are ~42 % of its area; the 4 × 3 fabric ~20 % (`capacity.md`).
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
| `lint` (ours) | every push | `info.yaml`/Makefile source-list sync; Verilator `-Wall` (with `src/lint.vlt` waivers for upstream and black-box files only) and Icarus `-g2005` lint |
| `unit` (ours) | every push | pytest over `tools/` (models, area model); RTL tests of the four design-set protocols in several configurations, with sigrok |
| `fabric` (ours) | push touching `arch/`, `protocols/`, `spikes/fab_demo/`, `tools/`, requirements | the FABulous two-bitstream demo; later every protocol compiled to a bitstream and run on the fabric simulation |

Local equivalents: `scripts/check_all.sh` (lint + all simulation tests), `scripts/gl_local.sh` (gate-level on a Yosys netlist with TT's Icarus 13).

## Measured hardening time
| Date | Commit | Design | `gds` job | precheck | `gl_test` | CI run | Notes |
|---|---|---|---|---|---|---|---|
| 2026-09-25 | a63877d | placeholder adder, 6x4, template `config.json` | 35.1 min | 12.3 min | 0.7 min, pass | 36170807513 | All green. LibreLane 3.1.0.dev3 |

Budget: GitHub stops a job at 6 h. The empty 6x4 tile already costs about 35 min, most of it fixed-cost steps over the empty area, so a filled fabric will take longer; re-measure after the first fabric hardening.
