# Compact physical edges for the scratch 5 × 3 fabric

D-037 experiment. This retains 112 LUT4s, two timers and two shifts. Only the
north/south tile heights change; the generated tile RTL is byte-identical to
its phase-aligned source. Frozen `src/`, `arch/` and submission files are untouched.

## Reproduce

This experiment requires the existing ignored phase-aligned scratch library,
its fabric CSV/config, and the candidate wrapper in
`build/arch_explore/chip_5x3_phase_aligned/`. It is not a clean-checkout build.

```sh
source .venv/bin/activate
spikes/compact_edges/run.sh
python spikes/compact_edges/simulate.py
python spikes/compact_edges/prepare_chip.py --local-decode --vertical-halo 3.78
# Or run the staged PDN / decoder placement / route pipeline:
spikes/compact_edges/route.sh
```

`run.sh` uses the pinned Nix development shell and serial tile hardening to
avoid the shared BEL JSON race (BUGS #22). The final command stages the complete
shell, real loader, original power-grid script and conservative Metal1–4 macro
obstructions in `build/arch_explore/compact_edges/chip_local_decode/`.
Run that directory's `config.json` with the same pinned LibreLane environment,
explicit `--pdk ihp-sg13cmos5l --pdk-root "$PDK_ROOT" --manual-pdk`, initially
through `--to OpenROAD.GlobalRouting` before spending time on detailed routing.

`--local-decode` uses the supported `deferred_flatten` synthesis mode: modules
map before flattening, retaining separate column decoder logic in an ordinary
standard-cell netlist. All stock unmapped-cell checks remain enabled.

`localize_decoders.tcl` adds optional exclusive placement regions below each
column to a pre-placement ODB. Set `WARP_LOCALIZE_INPUT` and
`WARP_LOCALIZE_OUTPUT`, then run the pinned OpenROAD with `-exit` and that Tcl
file. Resume placement with a copy of the pre-placement state whose `odb`
points to the output. It checks row-aligned placement with y ≥ 15.12 µm and preserved
cell names. It fixes no cells and disables no placement or timing checks.
The default 10 µm vertical macro halo removes all bottom placement rows;
3.78 µm retains rows there. Final detailed routing/DRC must validate clearance.

## Completed physical and functional evidence

Original macro: 1120.32 × 703.08 µm. Compact macro: **1120.32 × 676.62 µm**,
recovering 26.46 µm of vertical space. Macro area is 758,030.92 µm².
Run `compact_edges_stitch` passed KLayout DRC with zero violations. This is a
macro result, not a full-chip fit or an equal-area architecture comparison.

Every changed tile completed with zero routing and KLayout DRC violations:

| Tile | Height (µm) | Run |
|---|---:|---|
| N_IO | 37.80 | `RUN_2026-09-30_12-28-26` |
| N_IO_C2 | 37.80 | `RUN_2026-09-30_13-53-07` |
| N_IO_C3 | 37.80 | `RUN_2026-09-30_13-54-22` |
| N_IO_C4 | 37.80 | `RUN_2026-09-30_13-55-39` |
| N_IO_C5 | 37.80 | `RUN_2026-09-30_13-56-48` |
| S_IO2 | 49.14 | `RUN_2026-09-30_13-49-03` |
| S_IO2_C2 | 49.14 | `RUN_2026-09-30_13-59-37` |
| S_IO2_C3 | 49.14 | `RUN_2026-09-30_14-01-20` |
| S_IO2_C4 | 49.14 | `RUN_2026-09-30_14-02-55` |
| S_IO2_C5 | 49.14 | `RUN_2026-09-30_14-04-33` |
| NW_term | 37.80 | `RUN_2026-09-30_13-58-01` |
| NE_term_wide | 37.80 | `RUN_2026-09-30_13-58-49` |
| SW_term | 49.14 | `RUN_2026-09-30_14-05-58` |
| SE_term_wide | 49.14 | `RUN_2026-09-30_14-07-12` |

The actual 842-word UART image loaded through the full SPI shell interface,
entered RUN, transmitted `55`, `00`, `C3`, received `69`, and parked after STOP.
Test `load_uart_through_shell` passed in `sim_preview/simulation/results.xml`
(4,513,240 ns simulated). The preview's fabric and chip RTL were checked
byte-identical against the exported compact macro/chip RTL. The test uses the
D-023 simulator settling harness for unused combinational routing; it does not
force configuration bits or user state. This is RTL simulation, not silicon
or gate-level evidence.

Full-shell run `compact_y15` passed both supply-connectivity checks using the
original `src/pdn_cfg.tcl`; no proxy configuration macro or debug power straps.
Placement required 95% target density, routability inflation off and a wider
legalizer displacement search. The latter let hold repair place its buffers
while retaining the 0.1 ns extra hold margin. These settings do not establish
routed timing; the macro still lacks a timing library.

Matched integration screens on the same compact macro and y=15.12 µm:

| Full-shell run | Change | GRT overflow | Wirelength (µm) |
|---|---|---:|---:|
| `compact_y15_displacement` | ordinary early flattening; 10 µm halo | 11,405 | 610,524 |
| `compact_deferred_y15` | deferred flattening; same halo | 9,279 | 548,510 |

These are congestion screens, not routing passes. Deferred flattening retained
per-column decode nets, but most decoder cells still landed at the far sides.
`compact_fenced_y15_v2` demonstrated that the 10 µm halo leaves no legal bottom
rows: its region-aware GPL passed, then stock DPL rejected a decoder cell.
The following additional matched screens completed:

| Full-shell run | Change from deferred run | GRT overflow | Wirelength (µm) |
|---|---|---:|---:|
| `compact_halo_row` | vertical halo 3.78 µm; decoder placement free | 7,880 | 506,664 |
| `compact_fenced_halo_row` | same halo; decoders constrained below each column | 1,523 | 440,546 |

The latter reduces overflow by 86.6% against `compact_y15_displacement`. This
isolates an integration improvement on one macro, not an equal-area comparison
against G1. All four screens retain the 0.1 ns extra hold margin and ordinary
placement/timing repairs. Legalizing hold buffers does not establish routed
hold closure.

The exclusive regions must be released after CTS/GRT to let antenna diodes use
remaining sites there. With the regions retained, `compact_fenced_drt` failed
placement of ten new diodes. Set `WARP_LOCALIZE_RELEASE=1` when invoking
`localize_decoders.tcl` on the GRT ODB; it removes only experiment groups/regions
and retains cell locations. `compact_released_drt` then passed diode placement
and started detailed routing. This diagnostic was stopped after several optimization passes still reported roughly 15,000 violations, to free compute for the improved masked candidate. It has no final DRC result. GRT improvements alone do not establish detailed routability.

The deferred-flattened **mapped shell** also passed the 842-word SPI load,
UART TX/RX and STOP test with Icarus 13 and the template's functional CMOS5L
cell models (`simulation_mapped_shell/results.xml`, 28.10 seconds). The fabric
is generated RTL and no SDF is applied; this is not a full-chip gate-level or
routed timing result. Reproduce with `simulate.py --shell-netlist` pointing at
`compact_deferred_y15/06-yosys-synthesis/tt_um_warp.nl.v`.

Read native router `.drc` files/logs for violation layer counts: the pinned
LibreLane XML converter merges different layers under one category (BUGS #21).
No candidate is selected or promoted; full-chip detailed route, DRC/precheck,
macro timing and gate-level loading remain required.

## Additional screens (2026-09-30)

- `compact_fenced_m1_grt`: allowing Metal1 outside the blocked macro on the
  same placed netlist gives 991 overflow / 434,318 µm wirelength. No detailed
  route result for this layer change yet; the standard Metal2-minimum route
  remains the primary reference.
- `compact_y22_fenced_v2`: shifting the macro upward to y=22.68 µm with the
  same one-row halo and decoder regions gives 3,264 overflow / 465,962 µm.
  The more balanced y=15.12 µm placement remains preferred. An initial resume
  at the power-grid checker skipped the earlier IO placement and failed;
  restarting at `Odb.RemovePDNObstructions` preserves the correct step order.
- A tighter edge-only geometry (north 34.02 µm, south 45.36 µm) is being checked
  in isolated `build/arch_explore/compact_edges_tighter/`. This would yield
  669.06 µm macro height, but must pass both base tiles before variants/stitch.
  Reproduction knobs: `WARP_COMPACT_NORTH_HEIGHT`, `WARP_COMPACT_SOUTH_HEIGHT`
  and `WARP_COMPACT_WORK` for `run.sh`; equivalent CLI flags on `prepare.py`.

The shell-route script was syntax-checked; its individual stages were exercised
in the runs above. Its combined named run sequence has not yet been rerun.

An additional placement screen, `compact_rows_fenced`, puts each real frame-data
row register next to its west-facing macro pins as well as placing the column
decoders below the fabric. Enable `WARP_LOCALIZE_ROWS=1` when adding regions;
the helper checks the 676.62 µm macro geometry. This screen was rejected: it reduced hold buffers from 662 to 309, but crowded the remaining shell and produced 174,271 overflow / 2,023,876 µm wirelength.
Region release also removes these row-register regions before antenna repair.

## Generated-fabric input trace and unused-strobe screen

`input_usage.py` processes and flattens actual generated fabric/tile/primitive
RTL with Yosys, then traces consumed inputs. No user protocol design is part of
this trace. All 160 `FrameData` inputs are consumed; 48 of 140 `FrameStrobe`
inputs are unconsumed. Per-column consumed strobe counts are 4/17/17/17/17/17/3.
The summary records SHA-256 hashes of every source; `prepare_chip.py` refuses
a stale trace or one belonging to another work directory.

```sh
# Activate .venv and expose the pinned EDA environment first.
python spikes/compact_edges/input_usage.py
python spikes/compact_edges/prepare_chip.py --local-decode --vertical-halo 3.78 \
    --chip-dir chip_strobe_mask --mask-unused-strobes
python spikes/compact_edges/simulate.py --chip-dir chip_strobe_mask
```

This wrapper masks only unconsumed macro input strobes. All real configuration
storage, data inputs and consumed strobes remain dynamic, and the bitstream
format stays unchanged. RTL SPI/UART/STOP test passes in
`simulation_chip_strobe_mask/results.xml` (13.90 s). Mapped-shell SPI/UART/STOP also passed (27.17 s) in
`simulation_chip_strobe_mask_mapped_shell/results.xml`. Physical macro pins/GDS are unchanged; unused pins
still require constant-net routing, so fewer decode gates need not improve fit.
The matched early-region-release comparison below separates that placement
choice from the strobe change.

`route.sh` accepts `WARP_COMPACT_Y` and an optional already provisioned pinned
`WARP_COMPACT_EDA_BIN` instead of entering Nix again. By default it advances to
detailed routing only at zero GRT overflow. For an explicit diagnostic route,
set `WARP_COMPACT_MAX_OVERFLOW`; this never disables final DRC/timing checks.
The tighter-edge batch has an automatic continuation queued at y=18.90 µm,
using a diagnostic limit of 1,523, after successful stitch/export.

Matched placement-region release before post-GPL repair (same macro, halo,
clock target and timing checks):

| Run | Wrapper | GRT overflow | Wirelength (µm) |
|---|---|---:|---:|
| `compact_early_release_grt` | full strobes | 1,065 | 426,499 |
| `compact_mask_early_grt` | mask proven unconsumed strobes | 574 | 389,030 |

The masked wrapper reduces overflow by 46.1% in this comparison. Its synthesis
screen is 2,797 cells / 46,751.607 µm² versus 2,816 / 46,992.9222 µm² for the
unmasked deferred shell (`compact_mask_pdn` versus `compact_deferred_y15`, Yosys
state output). These exclude macro area and are not final chip area/timing.
The macro pins/GDS remain unchanged, so this is not an interface pin-count
reduction. Releasing regions before repair lets constant drivers use remaining
bottom sites; both runs use that placement choice. The same masked placed netlist rerouted with Metal1 as the minimum signal
layer reports **161 overflow / 362,577 µm** (`compact_mask_m1_grt_v2`).
The fabric remains obstructed on Metal1–4. This is a congestion screen;
`compact_mask_m1_drt` was stopped after its initial pass reported 10,541
violations and repair was still in progress, to prioritize the better
row-localized placement below. It has no final DRC result.
Metal1 clearance and TT precheck remain unproven.

## Repeat the best placement screen

After `input_usage.py`, the staged driver supports the tested masked wrapper,
release immediately after global placement (before repair inserts constant
drivers), and an explicit Metal1 routing screen:

```sh
WARP_COMPACT_CHIP_DIR=chip_mask_pipeline_check \
WARP_COMPACT_MASK_STROBES=1 WARP_COMPACT_EARLY_RELEASE=1 \
WARP_COMPACT_MIN_LAYER=Metal1 spikes/compact_edges/route.sh
```

Use a fresh chip directory to preserve earlier experiment configs. Defaults
retain the unmasked Metal2-minimum reference and release after GRT. The
zero-overflow guard remains active; a diagnostic override never disables
final DRC checks. The combined optional branch completed in `chip_mask_pipeline_check`: 155
overflow / 362,577 µm. The driver exited 3 at its zero-overflow guard,
as intended, without starting another detailed route.

## Narrower configuration-row fences

The original middle-row fences reserved 61.44 µm of width for about 2,400 µm²
of logic per row, leaving most reserved sites empty and crowding the remaining
shell. With `WARP_LOCALIZE_ROWS=1 WARP_LOCALIZE_ROW_WIDTH=21120` (DBU), the
three middle-row fences shrink to 21.12 µm width; top/bottom row fences retain
their earlier dimensions. All fences are released after GPL before repair.

`chip_mask_narrow_rows/runs/compact_local_grt` reports **67 overflow /
314,294 µm**, versus **155 / 362,577 µm** in the masked Metal1 pipeline without
row fences. Both use the same 676.62 µm macro, y=15.12, 20 ns target, halo and
0.1 ns extra hold margin. Post-CTS repair inserted 605 hold buffers versus
680 in the earlier masked screen. These are placement/congestion results,
not routed timing or a full-chip pass. `compact_narrow_rows_drt` reached 1,059 native violations at completed
iteration 8 before a daemon restart interrupted it. No final route pass exists.

The separate south-only geometry experiment in `compact_south45` retains
37.80 µm north tiles and uses 45.36 µm south tiles. It reuses seven proven
north/corner views and the tighter south base view after checking heights
and byte-identical tile RTL. All six new south variants passed zero routing/KLayout DRC.
`south45_stitch` completed with zero KLayout DRC; actual macro size is
1120.32 × 672.84 µm. At y=18.90 the logic
and north pins retain their existing absolute coordinates while the bottom
shell channel gains 3.78 µm. The 842-word SPI/UART/STOP RTL test passed
(`simulation_chip_mask_m1/results.xml`, 13.78 s). Full-shell routing and
stitched-chip DRC remain open. The reference screen reports 5,542 overflow;
narrower rows give 74 overflow / 331,912 µm. Bounded detailed routing reports
14,837 initial / 14,799 iteration-1 violations, worse than the lead geometry.

`congestion.tcl` produces a separate coordinate diagnostic from a saved
pre-GRT state. Set `WARP_GRT_STEP` to its completed GRT stage directory,
`WARP_GRT_SCRIPTS` to the pinned LibreLane scripts directory, and
`WARP_GRT_REPORT` to a new output path. It does not write back to the original
stage. A standalone diagnostic on `compact_mask_m1_grt_v2` reported 166
overflow; this is not identical to the stock 161-overflow flow result. Its
106 markers include 63 west-region markers; frequently involved nets include
`cell_en[24]`, `cell_en[25]` and `clk`. Actual detailed-route markers remain
necessary to distinguish pin escape issues from ordinary congestion.

South-only changed-tile evidence:

| Tile | Run | Routing / KLayout DRC |
|---|---|---|
| S_IO2_C2 | `RUN_2026-09-30_17-57-36` | 0 / 0 |
| S_IO2_C3 | `RUN_2026-09-30_17-59-54` | 0 / 0 |
| S_IO2_C4 | `RUN_2026-09-30_18-01-13` | 0 / 0 |
| S_IO2_C5 | `RUN_2026-09-30_18-07-08` | 0 / 0 |
| SW_term | `RUN_2026-09-30_18-09-04` | 0 / 0 |
| SE_term_wide | `RUN_2026-09-30_18-10-12` | 0 / 0 |

For row fences on other edge geometries, `route.sh` exports north/south heights
from the manifest. The Tcl checks the resulting full height against the actual
macro before creating regions. `prepare_chip.py` also requires an explicit zero
stitched-macro KLayout DRC metric before staging any chip experiment.


## Paused handoff (2026-09-30, user requested stop)

### Resumed 2026-10-05

The reliable pre-DRT restart is active under fresh run tag
`compact_narrow_rows_drt_20261005`, with the same `config_recovery.json` and
stock checks. Its log is `chip_mask_narrow_rows/compact_narrow_rows_drt_20261005.log`.
No final physical pass is established yet. The earlier paused status below is
historical; the four tighter north variants have not been restarted.

The mapped-fabric audit now checks **every exposed configuration storage bit
against the actual SPI-loaded words**, rather than sampling three tiles.
Run `WARP_COMPACT_DIAG=1` with `simulate.py --chip-dir chip_mask_narrow_rows
--mapped-fabric`. The 2026-10-05 run checks 8,707 bits: zero unknowns and zero
image mismatches. Shell run/reset signals and exposed tile clocks are known
after RUN, while some logic-cell state/output signals remain unknown. The
UART pin test still fails; this is configuration-path evidence, not a native
gate-level fabric pass. Audit assertions never force configuration or state.
Evidence: `gate_image_audit_20261005.log` and
`simulation_chip_mask_narrow_rows_mapped_fabric/test.log` under the work directory.
The matching RTL-fabric SPI/UART/STOP test passes (14.29 s,
`simulation_chip_mask_narrow_rows/results.xml`). Baseline `scripts/check_all.sh`
passes (`build/check_all_20261005.log`); sandboxed sigrok first failed libusb
initialization, addressed by the permitted rerun and BUGS #24 diagnostics.

`report_drc.py` summarizes native router reports by actual layer, marker type,
region center, net incidence and coordinate bins. It rejects unrecognized
markers. For the preserved iteration-8 report:

```sh
source .venv/bin/activate
python spikes/compact_edges/report_drc.py \
  build/arch_explore/compact_edges/chip_mask_narrow_rows/runs/compact_narrow_rows_drt/04-openroad-detailedrouting/drt-run-0/tt_um_warp.drc-8.rpt \
  --macro-bbox 121.44 15.12 1241.76 691.74
```

This reproduces 1,059 markers: Metal2 787, Metal3 250, Metal4 22; 776 shorts
and 283 spacing markers. Centers place 1,046 west of the macro and 13 south.
These count markers, not independent electrical faults. The summary is saved
as `lead_iter8_summary_20261005.json` in the work directory.

Research leads: [FABulous discussion #327](https://github.com/FPGA-Research/FABulous/discussions/327)
documents combinational-loop simulation handling; it supports investigating
the D-023 limitation but does not establish this candidate's correctness.
[OpenROAD global-routing documentation](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html)
describes congestion reports and routing-resource controls. Evaluate any new
placement/resource experiment against native detailed routing, with the same
macro, clock and hold margin; a lower GRT overflow is insufficient for promotion.

All three active experiments were stopped with Ctrl-C: lead DRT recovery,
tighter north tile batch, and Metal2 reservation DRT screen. The latter has no
complete DRT result (GRT: 86 overflow / 313,732 µm). Keep the 676.62 µm,
67-overflow placement as the lead; it still does not pass full-chip routing.

Lead recovery saved a routed iteration-0 snapshot at
`build/arch_explore/compact_edges/chip_mask_narrow_rows/runs/compact_narrow_rows_drt_recovery/01-openroad-detailedrouting/drt_iter0.odb`.
Continuing from that routed snapshot has not been verified. Reliable restart
from the preserved pre-DRT state, with a fresh tag:

```sh
source /home/younix/protocol-emulator-asic/.venv/bin/activate
export PATH=/nix/store/wjrb29pislfhs8lh1nmlg5kibhfqydl9-devshell-dir/bin:$PATH
cd /home/younix/protocol-emulator-asic/build/arch_explore/compact_edges/chip_mask_narrow_rows
librelane --pdk ihp-sg13cmos5l \
  --pdk-root /home/younix/.cache/warp/pdk-full --manual-pdk \
  --run-tag compact_narrow_rows_drt_resume_next \
  --from OpenROAD.DetailedRouting \
  --with-initial-state runs/compact_narrow_rows_drt/04-openroad-detailedrouting/state_in.json \
  --to KLayout.DRC config_recovery.json
```

For `compact_edges_tighter`, finish only N_IO_C4, N_IO_C5, NW_term and NE_term;
completed south/base/N_IO_C2/N_IO_C3 views remain reusable. N_IO_C4 recovery
was interrupted, not passed. No complete 669.06 µm stitched macro exists.

Post-CTS mapped shell plus RTL fabric passes SPI/UART/STOP:
`simulation_chip_mask_narrow_rows_mapped_shell/results.xml` (35.26 s).
Fully mapped fabric diagnostics still fail after RUN with X values, consistent
with the known D-023 settling limitation; no native fabric gate-level pass or
routed timing is claimed. Simulation now explicitly rejects failing XML
(BUGS #23). WORKLOG session 37 records the rejected placement screens and
remaining physical gates.

## 2026-10-05 continuation: shared-word CRC and north tiles

D-039's optional `--shared-word-crc` / `WARP_COMPACT_SHARED_CRC=1` stages an
isolated shell with `wp_crc32_shared_word.v`. Read the existing registered
`cfg_word`, never the byte-assembly wire (BUGS #25). Unit, real SPI/UART/STOP
and existing F2 BMC/cover checks pass; see
[the CRC report](../../docs/reports/compact_shell_crc.md) for bounds and costs.
Its bounded two-iteration DRT screen completed at 2,652 markers versus the
lead's 4,503 at iteration 2. Full stock routing is running under
`chip_shared_crc_physical/runs/shared_crc_full_drt_20261005`. No promotion.

The lead first DRT pass finished at 268 markers, all west, before antenna
repair/rerouting. Its stock flow is still active. The tighter N_IO_C4 tile
completed its recovery successfully; the serial batch continues with N_IO_C5,
NW_term and NE_term_wide. No complete 669.06 µm macro yet.

Mapped diagnostics now trace selected unknown combinational cones using
`WARP_COMPACT_CONE_JSON`. Optional `simulate.py --settle-internal` pulses only
preserved combinational switch-data wires; `--reset-probe` exercises real host
USER_RESET after RUN. Both still fail native mapped UART simulation. Neither
is a fix or proof. FABulous [PR #806](https://github.com/FPGA-Research/FABulous/pull/806)
includes simulation X scrubbing that also clears flops; we have not adopted
state initialization as evidence of real reset correctness.

Research: [Chung et al., How to Shrink My FPGAs](https://pure.manchester.ac.uk/ws/portalfiles/portal/207833524/FPGA_2020_FABulous_optimizations_1_.pdf),
sections IV–V, studies congestion-driven configuration-bit and interface-wire
remapping. A future testable tile experiment could reorder physical frame
assignments using placement coordinates, with matching bitstream-generation
changes and loaded-image checks. This is a research lead, not an implemented
change; current residual chip markers are in the west shell channel, so the
shared-register experiment takes priority. No upstream files were edited.

## Diagnosed configuration-branch experiment (D-040)

`WARP_CFG_BRANCH_BUFFERS=1` adds14 non-inverting buffers to frame_idx[0:1]
in the pre-placement OpenDB, grouped with each column decoder. The optional
path is off by default and supply pins connect to existing rails. Added cell
area127.008µm². Matched sharedCRC GRT overflow93→27, estimated wirelength
285645→281448µm; hold buffers512→522. This is not a route pass. Run artifacts:
`chip_shared_crc_cfgbranches/runs/compact_local_grt`. Its two-iteration
`cfgbranches_drt_screen` disables post-DRT antenna repair only for diagnosis.
Mapped-shell SPI/UART/STOP uses the actual transformed netlist, RTL fabric
and no SDF. See D-040 and `docs/reports/compact_route_diagnosis.md`.

The pinned router's help confirms `-jumper_only`; a read-only copied-snapshot
probe runs but leaves the existing detailed antenna result at1net/2pins.
No jumper-only full-flow improvement is established.

All tighter north variants completed successfully. Stitch/export run
`tighter_stitch_20261005` completes with explicit KLayout macro DRC0.
The earlier lead finished detailed routing at716 markers and reports a
routing-check error; later Magic via-reading errors do not supersede that
physical failure. Retain default signoff checks and frozen G1.

## Pre-placed branch protection (D-041)

Optional `WARP_CFG_BRANCH_DIODES=1` requires `WARP_CFG_BRANCH_BUFFERS=1`.
It adds14 process antenna cells on the source side of the local index
branches, grouped by decoder column,76.2048µm² before repair. Matched tighter
GRT stays0overflow, estimated wirelength276069→275796µm, hold buffers522→514.
Actual transformed mapped-shell SPI/UART/STOP passes25.28s with RTL fabric.
Full stock route is active in `compact_edges_tighter/chip_shared_crc_cfgdiodes`.
No antenna/physical pass yet. The previous tighter branch variant reaches87
first-pass DRC markers but has4antenna nets; its completed repair leaves144
DRC markers with zero antenna nets. It is a failed baseline, no longer active.

## Local CRC placement screen (D-043)

`pad_crc_hotspot.tcl` reads `WARP_PAD_INPUT` and requires fresh output paths
`WARP_PAD_OUTPUT`, `WARP_PAD_DEF`, `WARP_PAD_REPORT`. `WARP_PAD_SITES` defaults
to two sites per side. It requires the measured baseline's12 endpoints on
`net37`/`u_shell.crc[2]`, temporarily anchors remote cells, legalizes, checks
connectivity/anchored positions, restores placement statuses, then writes
the new database. It refuses to overwrite existing outputs. Padding applies
during this legalization; it is not a permanent routing blockage or a promise
that later automatic repair preserves every gap.

Retained run `chip_crc_padding_local_screen/runs/crc_padding_grt` has0overflow,
277632µm estimated wirelength, unchanged3497cells. Two-iteration diagnostic
`crc_padding_drt_screen` is active; no full route or improvement claim yet.
Four-site legalization failed; unrestricted two-site legalization moved too
many remote cells and was not routed. See D-043 and the route diagnosis report.
