# Physical design and CI

Status: v1, written 2026-09-26, chip-level results added 2026-09-27 (first fabric chip through TT's flow: run 36327510268).

**Latest compact experiment (2026-10-06):** cloud37516794406 reaches final
native routing DRC0/antenna0/critical disconnected0. Router elapsed2h47m15s;
whole route/geometry job3h16m05s. Full geometry fails KLayout248 (1 Metal1
width,247 Metal1 spacing), Magic1828 and LVS67. Extracted shell setup/hold
slack+12.251343397653367/+0.12463458395889776ns at20ns, with9 slow-corner
slew violations; macro black-boxed. No compact physical, complete timing or
native-function pass. See compact_route_root_causes.md.

**Macro placement rules learned the hard way (D-019, BUGS #9–#11):** (1) on the power-grid phase, x = 11.52 + 109.92 k; (2) the macro's pin-heavy faces (west, south for this fabric) toward open core; (3) beside the macro, no channel or one wide enough for a full grid stripe pair; (4) no `"//"` keys inside `MACROS`. Check all four locally with TT's merged config before pushing (the local flow reaches detailed routing in ~2 min).

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
**Run 36327510268 (dea2150): 16-LUT fabric macro + spike shell**, from `GDS_logs` `final/metrics.json`:

| Metric | Value |
|---|---|
| Die / core | 916,214 / 902,417 µm² (1289.28 × 710.64 µm) |
| Fabric macro `warp_tiny` | 172,789 µm² (357.12 × 483.84 µm) at (780.96, 113.40) |
| Shell standard cells | 1,380 cells, 27,900 µm² |
| Utilisation (cells + macro) | 22.2 % of the core |
| Routed wirelength | 103.3 mm; routing DRC 0; antenna 0 |
| KLayout DRC (precheck) / Magic DRC / LVS | 0 / 0 / 0 (fabric abstract in LVS) |
| Timing at 20 ns, worst corner | setup WS +12.47 ns (slow), hold WS +0.106 ns (fast); 0 slew/cap violations. Shell only: the fabric is a black box to STA |
| IR drop (worst) | 0.38 mV with the 109.92 µm stripe pitch |
| Power | 1.19 mW |

**Earlier: run 36170807513 (a63877d, placeholder adder):**

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
| 2026-09-26 | e41f05f | 16-LUT fabric macro at (11.52, 7.56) + spike shell | cancelled after ~4.8 h | — | — | 36277723397 | Detailed routing stuck at ~10.5K violations: fabric pin faces against the die edges (BUGS #9) |
| 2026-09-27 | (docs: bugs 9) | macro moved to (890.88, 113.40) | 3 min, fail | — | — | 36292542000 | Config load: `"//"` keys inside MACROS (BUGS #10) |
| 2026-09-27 | (no comment keys) | same, config fixed | 32.6 min | 9.9 min, **fail** | pass | 36293031051 | Pin check: pdngen short channel stripes beside the macro (BUGS #11) |
| 2026-09-27 | dea2150 | **macro at (780.96, 113.40)** | **32.5 min** | **10.7 min, pass (9/9)** | **1.2 min, pass** | **36327510268** | **First fabric chip through TT's flow**: DRC/LVS/antenna 0, Magic DRC 0, timing met |
| 2026-09-27 | acc3af3 | phase 2 shell (SPI host, checked loader, run control) + same 16-LUT macro | 35.6 min | 12.3 min, pass | 2.4 min, **pass 16/16** | 36342012141 | First CI run of real bitstreams on the hardened chip netlist (counter4, logic4, reload). 3,239 std cells / 51,066 µm², 24.8 % utilisation; setup WS +12.04 ns (slow), hold WS +0.117 ns (fast); DRC/LVS/antenna 0, Magic DRC 0 |
| 2026-09-27 | e5b1f98 | shell + **G0** fabric macro (96 LUT4, 1016.64 × 669.06 µm, host channel through the fabric, D-024/D-025) | 45.8 min | 3.8 min, pass | 5.5 min, **pass 17/17** | 36353540402 | First 6x4 chip with the full-size fabric. Shell 3,901 std cells / 59,951 µm²; utilisation 82 % (placeable area beside the macro and its obstruction); setup WS +10.63 ns (slow), hold WS +0.121 ns (fast); routing DRC 0, LVS 0, antenna 0, Magic DRC 0; IR drop 0.77 mV. gl_test incl. counter4, logic4, reload, host channel |
| 2026-09-28 | d6f5dcd | shell + **G1** fabric macro (88 LUT4 + 2 timers + 2 shift registers, same size and ports as G0, D-026/D-027) | 43.6 min | 4.1 min, pass | 6.8 min, **pass 19/19** | 36367067731 | Shell 3,719 std cells / 60,265 µm²; utilisation 82 %; setup WS +10.73 ns (slow), hold WS +0.143 ns (fast); routing DRC 0 (local pre-flight with LibreLane 3.0.0 had 21 on `clk`), LVS 0, antenna 0, Magic DRC 0; IR drop 1.07 mV. gl_test incl. `test_prims` and `test_uart` (hard primitives configured by real bitstreams) |
| (local) | reset fix (BUGS #18) | pre-flight only (LibreLane 3.0.0 Nix) | - | - | - | - | Overflow 37; 36 detailed-routing violations, all on `clk` at the fabric's west-face clock pin (y ≈ 640 µm), as in the G1 switch's pre-flight (21), which CI routed clean: the local router differs from CI's for this net |
| 2026-09-28 | fe4cac8 | same chip (G1); test and tool changes only (protocol chip tests, primitive timing arcs) | 47.8 min | 3.6 min, pass | 12.4 min, **pass 21/21** | 36372341186 | Same metrics as d6f5dcd (3,719 cells, setup +10.73 ns, hold +0.143 ns, DRC/LVS/antenna 0). gl_test adds `test_spi_ctrl` and `test_i2c_ctrl` (design-set SPI and I2C controllers against reference target models) |
| 2026-09-28 | 3047dea | G1 + reset synchronizer (BUGS #18) | 36.8 min | 4.4 min, pass | 6.8 min, **pass 21/21** | 36383587262 | Shell 3,723 std cells / 60,567 µm², utilisation 82 %; setup WS +12.48 ns (slow), hold WS +0.112 ns (fast); routing DRC 0 (local pre-flight had 36 on `clk`), LVS 0, antenna 0, Magic DRC 0; IR drop 0.90 mV |

Budget: GitHub stops a job at 6 h. The empty 6x4 tile already costs about 35 min, most of it fixed-cost steps over the empty area, so a filled fabric will take longer; re-measure after the first fabric hardening.

### Scratch 5 × 3 edge hardening (2026-09-30)

Local tighter-edge `N_IO` run `RUN_2026-09-30_15-14-35` completed at
17:04:01, about 109.4 minutes elapsed, with zero routing/KLayout DRC. The
45.36 µm `S_IO2` run `RUN_2026-09-30_17-04-02` completed around 17:05 with
the same checks clear. These are individual tile runs under concurrent local
load, not CI or complete-chip durations. Narrow north-edge routing can dominate
the batch; do not budget the entire rebuild from the faster south tile.
Evidence is under `build/arch_explore/compact_edges_tighter/` (ignored logs).
The superseded `compact_mask_m1_drt` was stopped. The improved
`compact_narrow_rows_drt` reached 1,059 native violations at iteration 8 before
a daemon restart. Its recovery and the unfinished tighter tile batch were
stopped at the user's request; no complete chip hardening duration or final
routing pass is available. See WORKLOG session 37 for restart inputs.

### Hosted experiment migration (2026-10-06)

Separate `.github/workflows/experiments.yaml` uses standard GitHub-hosted
Ubuntu24.04 runners for compact routing, native mapped-fabric diagnosis and G1
software demonstrations. Template jobs, frozen hardware and `main` are unchanged.
No self-hosted or paid/larger runner is configured. Artifacts expire after one
day. Routing step is bounded to300minutes (job330), native job35, demos40.

D-044 warm restart reaches a complete15-marker iteration8 checkpoint; it ends
locally before final native repair/checkers. Hosted work resumes that separately
hashed experimental asset, not a clean-source rebuild. LibreLane3.1.0.dev3 Docker
and four threads differ from local3.0.0 Nix packaging; OpenROAD source and PDK
revisions remain pinned. No convergence ETA or physical pass follows from15.
Macro-black-box shell STA does not close configured-fabric timing. See
`spikes/cloud/README.md` and `docs/reports/compact_acceptance_and_competitors.md`.

### Compact diagnostic run timing (2026-10-05)

Local `compact_narrow_rows_drt_20261005` completed initial16-iteration
DRT in42m36s, then three antenna repair/reroute passes in32m20s,31m40s
and25m22s:131m58s total DRT wall time, excluding surrounding flow steps.
Source: `build/arch_explore/compact_edges/chip_mask_narrow_rows/runs/compact_narrow_rows_drt_20261005/01-openroad-detailedrouting/openroad-detailedrouting.log`,
each pass's final DRT-0267 summary. Final routing reports716DRC markers
and the checker fails; this is not successful hardening. Later Magic DEF
via-reading errors are additional flow errors, not the cause of the716
TritonRoute violations. Later completed sharedCRC and tighter branch-buffer
routes retain404and144markers respectively; neither passes. The separate
preplaced-diode restart is active. Clock-minimum-Metal3 bounded DRT finishes
in13m08s with3784markers after two optimization iterations (baseline3482),
so that screen is set aside. Local CRC padding is a new bounded diagnostic,
not a completed hardening. Exact runs: `docs/reports/compact_route_diagnosis.md`.

October6: preplaced-diode restart completes three DRT passes in66m00s,
43m58s and64m53s,174m51s total, ending258routing markers/0antenna nets or
pins. The routing checker fails; later incompatible Magic was stopped.
Local CRC padding bounded screen finishes13m22s at3477markers versus3482
baseline. Neither is selected; no compact whole-chip route is currently
running. Full pass durations vary substantially and are not an ETA to zero.

October6 hosted update: G1 workflow37511778153 passes gds/precheck/gl_test/viewer.
Compact route37516794406 started19:09:17UTC; at19:55:17UTC it remains in the
routing step,46minutes after job start (including setup). The step is bounded
to300minutes, job330. This is the unchanged saved-checkpoint route with up
to64 repair iterations, not a completed zero-marker result. Prior compact
131m58s/174m51s attempts explain the possible scale, not an ETA or convergence
guarantee. See hosted experiment report for current status; older "not running"
statements above describe the earlier local runs.
