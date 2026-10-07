# Compact chip routing: ground-up audit (October 6, 2026)

The compact successor has not passed full-chip physical checks. The frozen
G1 submission fallback has passed its recorded hardening/CI; “routing never
passed” describes the compact exploration, not every WARP implementation.
The earlier best completed compact result was D-040: zero global-routing
overflow,144 final detailed-routing markers and zero antenna violations.
Cloud37516794406 now completes detailed routing with0markers; full geometry
still fails, as recorded below.
The remaining problem is local geometry, not proof of exhausted global
routing capacity. This audit distinguishes measurements from hypotheses.

## Completed hosted result

[37516794406](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37516794406)
reaches0 routing markers at iteration53 after2h47m15s router elapsed, with
antenna nets/pins0 and critical disconnected pins0 (7 noncritical). Full job
elapsed3h16m05s. Later KLayout reports248 errors: M1.a1 and M1.b247.
Magic reports1828; LVS reports67, including power-net mismatches. Extracted
shell setup/hold slack+12.251343397653367/+0.12463458395889776ns at20ns,
but9 slow-corner slew violations remain and the fabric macro is black-boxed.
This is native routing closure, not compact physical/function/timing acceptance.

The saved artifact contains iteration52 ODB with3markers, not the final0 ODB.
Its SHA256 is33dceb8d52df9d5ea8cc3741b71b9b3e1e79ae4fb95b1eb559b3ca3eb40390bc.
[Read-only inventory37545539269](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37545539269)
records rows, cell orientations, Metal1 pins and power rectangles. The width
marker at x31.005–31.055/y704.655–704.815µm contains no pre-fill cell;
the subsequent flow inserts6762 filler cells. Filler/power geometry is a
specific hypothesis, not a proven root cause. Geometry-only replay37545941476
uses the unchanged saved database, retains full marker coordinates/views,
and performs no routing. Its input's3markers prevent treating it as final
route certification. No new route or hardware change is launched here.

37545941476 finishes replay with248 KLayout errors again and retains exact
coordinates and filled physical views. Joining marker edges to its post-fill
DEF and pinned LEF cell dimensions associates all248 with decap fillers:
241 decap8-only,3 decap4-only,2 decap4/8 boundaries,1 decap8/fill2 boundary
and1 decap4/fill2 boundary. Width marker is inside FILLER_185_58/decap8.
D-048 changes only FILL_CELLS to plain fill1/fill2 for the same saved database
and adds LVS checks.37552604692 is pending. Decap reduction's power implications
and final native0-route/physical/timing qualification remain open.

## Evidence chain

The preserved source is
`build/arch_explore/compact_edges_tighter/chip_shared_crc_cfgbranches/runs/compact_local_route/04-openroad-detailedrouting/`:
final `tt_um_warp.odb` SHA256
`5c9b7e56ebf10202b5d5bd41fa4ebb9a3a04e9e1ae9e4b08557149be13c5b2cc`,
and `drt-run-1/tt_um_warp.drc-16.rpt`.
The complete fixed footprint is 6 × 4 tiles, 1289.28 × 710.64 µm;
the macro is 1120.32 × 669.06 µm at (121.44, 15.12). The clock target
remains 20 ns and existing hold margins remain enabled. Starting GRT
reports 3497 instances and 805813.14 µm² of instance area, including
749561 µm² of macro. Final antenna repairs change the instance inventory;
those starting counts are not a final-route area claim.

Read-only `export_route_geometry.tcl` exports transformed instance pin
rectangles and actual cut placement rows. `audit_route_geometry.py`
joins marker bounding boxes within 1 µm and intersects cell/row areas
with fixed bins. Artifacts are under
`build/route_root_audit_20261006/best_final144_audit/`, including a
standalone SVG of the west channel. There are no filler cells in the
exported snapshot. Counts of pin rectangles are not counts of unique pins.

## What the measurements show

All 144 markers are west of the macro: 141 on Metal2, three on Metal3.
They form 17 spatial clusters under the stated 1 µm join rule; this is
not a claim of 17 independent electrical faults. Of 144 marker boxes,
111 overlap the XY projection of a signal-pin rectangle on an implicated
net; 128 are within 1 µm. Most implicated pins are Metal1 while markers
are Metal2, so proximity includes the escape-via projection. It identifies
where to investigate, not a proof that every marker is caused by pin access.

| West-channel bin (µm) | Cell area / available row area | Signal-pin rectangles | Markers |
|---|---:|---:|---:|
| x0–50, y300–350 | 94.50% | 1151 | 74 |
| x0–50, y500–550 | 89.24% | 929 | 40 |
| x50–100, y450–500 | 85.31% | 736 | 16 |
| x0–50, y450–500 | 97.86% | 794 | 12 |
| x50–100, y500–550 | 92.35% | 755 | 2 |

The largest cluster has 36 markers at
(36.86, 303.515)–(39.65, 305.24) µm. Nearby implicated A/B/C/Y pins all
belong to one `sg13cmos5l_nor3_1`, `u_shell._1073_`, orientation MX.
Its small input pin rectangles and wrapping output geometry constrain
several escapes within one cell. The next cluster has 24 markers around
the A1/A2 pins of CRC cell `u_shell.u_crc._199_` (`o21ai_1`), carrying
`crc[2]` and `net37`. Sixteen markers involve the clock trunk and a
control-cell B1 pin. These are not exclusively CRC or antenna problems.
`best_cluster_pin_audit.json` records exact implicated nets and pin shapes.

Hold repair consumes space too: the worst 50 × 50 µm bin contains
21 hold cells among 172 cells. That is evidence of a contributor, not
permission to remove needed hold repair. Broad padding can relocate
conflicts without improving the internal pin geometry.

## A confirmed search-budget gap

Every full compact attempt used `DRT_OPT_ITERS=16`, an inherited fail-fast
cap. The exact pinned OpenROAD revision `dcf36133` has 65 schedule stages,
indexed 0–64. Stage17 performs ALL rip-up; stage23 includes NEARDRC;
later stages change clip sizes, search limits and repair costs. The previous
cap excluded those stages. This is a confirmed flow limitation, not proof
that a larger budget will converge. See the
[pinned strategy and main loop](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/dr/FlexDR.cpp#L1506)
and [mode selection](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/dr/FlexDRFlow.cpp).

D-044 runs the stock flow on a copy of the final144-marker state with
only the budget changed to64. A warm start restarts internal iteration0;
it is not continuation at17. It reaches61 markers by iteration3/4, then
26 at the end of iteration5 and again at6, then15 at7 and8. The original NOR cluster is
absent from iteration6; remaining markers concentrate around CRC/SPI pins
and a clock crossing. This is intermediate progress, not final
DRC/antenna/timing success, and does not establish the separate effect of
the larger budget. Intermediate reports are in `schedule64_iter4_audit/`
and `schedule64_iter6_markers.json`. Input provenance/config difference are recorded in
`chip_schedule64/input_manifest.json`. Existing runs/inputs are untouched.

The local invocation ends without completing iteration9 or final repair/checks.
The saved complete `drt_iter8.odb` and matching `drc-8.rpt` are packaged as a
hashed experimental release asset for hosted CI. No heavy local EDA process is
visible at migration. Fifteen is an intermediate count, not a native pass.
The new separate workflow keeps stock native checks and continues physical
checks only after they pass. See [acceptance/research plan](compact_acceptance_and_competitors.md)
and [cloud reproduction limits](../../spikes/cloud/README.md).

## Fixes ordered by evidence

1. Finish D-044 with full stock antenna repair and native routing,
   antenna and disconnected-pin checkers. If native checks reach zero,
   continue extraction/STA and independent geometry checks; routing alone
   cannot close the separate native-fabric functional gate.
2. If the same intra-cell cluster persists, test one larger NOR3 cell,
   preserving function and pin connectivity. The installed PDK's
   `nor3_2` is 4.32 × 3.78 µm versus 2.4 × 3.78 µm for `nor3_1`,
   with wider and differently placed input pins. It costs 7.2576 µm²
   before legalization/repair. Local legalization can still worsen routes
   or timing; measure it and reject if it does. D-045 prepares this backup:
   two anchored legalization attempts fail, but minimal same-row compaction
   passes legal placement/connectivity, shifting13neighbors at most1.92µm.
   GRT remains0overflow (275652µm wirelength,3497instances, rounded reported
   instance area805820µm²). Actual mapped-shell/RTL-fabric SPI-loaded UART
   test passes58.69s. Artifacts: `chip_nor3_pin_screen`; no detailed-route
   improvement is established and no full route is launched for it.
   The unchanged-layout D-044 has already removed the NOR cluster, so
   continue that lead first. A larger `o21ai_2` is
   absent from this PDK, so the CRC conflict needs a different experiment.
3. Inspect pin-access alternatives and surviving clock/pin crossings
   with actual marker/shape evidence. OpenROAD exposes pin-access
   diagnostics and minimum-access-point controls in its
   [official routing documentation](https://openroad.readthedocs.io/en/latest/main/src/drt/README.html).
   Do not change via rules, PDK geometry or waive checks to obtain a pass.
4. Only if these fail, change shell density/distribution with matched
   complete-area/clock measurements. Global overflow zero does not show
   that the local pin escapes are legal.

Rejected completed screens remain useful evidence: preplaced diodes end
at258 markers with zero antenna; clock-Metal3 and local CRC padding fail
to improve their bounded matched comparisons enough to justify full runs.
The old Magic/PDK version mismatch is a separate downstream flow blocker;
it does not explain native shorts or spacing violations. Full results and
durations are in `compact_route_diagnosis.md` and D-041–D-043.

## Toolchain comparison

LibreLane3.1.0.dev3's
[OpenROAD package source](https://github.com/librelane/librelane/blob/3.1.0.dev3/nix/openroad.nix#L46)
pins the same `dcf36133` revision as the local tile-flow environment;
a newer LibreLane label is not evidence of a newer routing algorithm.
Dependency builds, flow scripts and resulting placement/routing context can
still differ. Historical G1 CI artifacts use the same16-stage cap and reach
zero by iteration4; the denser compact candidate does not inherit that result.
Those artifacts report Magic8.3.674, compatible with the PDK's minimum657,
whereas local Nix Magic623 is incompatible. A separately fetched Magic from
the CI-pinned package set can address stream-out compatibility without
changing the running router or claiming a physical pass.

The current upstream discussion of
[non-convergent routing runs](https://github.com/The-OpenROAD-Project/OpenROAD/issues/11537)
also warns that plateauing early does not prove later strategies cannot
help. Our own measured26-marker trajectory is the criterion for subsequent
diagnosis; external reports are context, not WARP verification evidence.


## October7 follow-up: actual filler control and electrical hotspot

Replay37552604692 takes27m34s and reports248 KLayout/75 LVS. Its actual DEF
still has5667 decaps and1095 plain fillers: DECAP_CELLS remained enabled when
FILL_CELLS changed. This did not test decap exclusion. Corrected37648945387
changes only DECAP_CELLS=[] in copied config, audits actual inserted cells,
and continues DRC/LVS only with zero decaps/nonzero plain fillers. No routing,
rule waiver or frozen hardware change. The input still has3 native markers.

Read-only audit of37552604692's slow-corner checks.rpt and exact netlist binds
all9 slew-violation pins to u_cfg.frame_idx[0]: driver u_cfg._54_/Y,
seven WARP_CFG_BRANCH_0/A inputs, and ANTENNA_29/A. Driver master is
sg13cmos5l_a21oi_1. Worst slew2.562529ns exceeds2.507400ns limit by0.055129ns.
The extracted wire-only SPEF capacitance is0.177875pF (PIN_CAP NONE), not the
complete loaded capacitance. The same report lists33 max-fanout violations,
including27 clock-tree outputs, five column-decode outputs and one FSM flop.
Do not equate positive setup/hold with complete electrical/timing acceptance.
Artifact summary: build/route_root_audit_20261007/electrical_hotspot.json,
with report/netlist hashes and all nine actual endpoint bindings.

This identifies a focused next electrical screen: stronger equivalent driver
or an additional legal local buffer, followed by regenerated placement/routing,
extraction and setup/hold/electrical checks. The pinned LEF offers a21oi_2:
2.4x3.78 to3.84x3.78um adds5.4432um2 before downstream repairs. No swap is
installed or improvement claimed; input loading, routing and hold can change.
Clock fanout needs a separate constraint/tree review. Only one physical change
per hardening; the active filler experiment remains untouched.
