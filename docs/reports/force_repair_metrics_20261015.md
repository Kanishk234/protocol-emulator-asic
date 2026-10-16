# Forced-repair metrics: distinguish touched edges from the whole chip

Run38849978485 does not establish a controlled routing improvement or clean
regression: its repeated pin-access credits change203 encoded capacities.
The corrected pin-credit build/retry is the next experiment. This report
analyzes retained outputs read-only; it proposes no new routing knob or patch.

## Authenticated artifact

Local downloaded artifact root:
`build/force108/controlled-native-pair-repair-38849978485/route_force_repair/forced_pair/replay/1-openroad-globalrouting/`.
The files below are relative to that directory and remain ignored raw evidence.

| File | SHA256 |
|---|---|
| `openroad-globalrouting.log` | `727854c0173bac28a35c0574e7e8d26f3c40f270389ce3cfe4ca46337a5b4198` |
| `initial-segments.txt` | `19b14132c36cfa3e863edc34d0f23e7783694da80f586c438833783337a1da2c` |
| `initial-grid.tsv` | `278fdd4a3e55eea60f586571bae98191e3a07623b2790aeb642e3a83d6c163ae` |
| `native-segments.txt` | `727658b1dd6390ab38c347bc1d0ab6c5368c217f2c07be041945e1aff84960c8` |
| `native-grid.tsv` | `65f6945db965551348aeddd306d211f2910f86fcde4b2b42c0bb91d25c03f4be` |

Initial files match the exact121 checkpoint. The final full calibrated grid
has139 overflow, distributed9/51/32/47 acrossMetal1–4. Source/census/geometry
checks are separate from the failed capacity-control requirement. GRT-0232
occurs before a final native congestion table, so the earlier121 table must
not be relabeled as the final repaired result.

## What the five native incremental passes actually report

The log shows one initial `rerouting 2 nets.` witness, followed by four
expansion passes. The expanded net identities/counts are not present.
Each pass has15 negotiation samples; these are not five native full-chip
acceptance results.

| Pass | Logged cached2D / assigned3D | Logged minimum2D | Interpretation |
|---|---:|---:|---|
| Initial selected pair |21 /24|18, round1|Current touched-edge metric; not a121→24 full-chip improvement|
| Expansion1 |102 /100|62, round0|A different touched-edge census|
| Expansion2 |155 /144|140, round12|A different touched-edge census|
| Expansion3 |151 /139|144, round12|A different touched-edge census|
| Expansion4 |153 /139|139, round12|Native rejection follows|

These values include the capacity-credit confound. Native minimum messages
are scalar history, not evidence that the corresponding tree was saved.
The unchanged native3D maze gate remains closed when cached2D is nonzero.

Pinned OpenROAD source explains the scope. `FastRouteCore::run` starts by
calling `graph2d_.clearUsed()` at FastRoute.cpp1335. Graph2D::clearUsed clears
the horizontal/vertical used-coordinate sets but leaves usage arrays intact.
Positive `updateUsageH/V` inserts coordinates back into those sets. Both
`getOverflow2Dmaze` (maze.cpp1989) and `getOverflow3D` (2137) traverse those
sets, not every coordinate of the fixed chip. During incremental rerouting,
untouched retained demand can therefore lie outside the logged metric.
Conversely `updateDbCongestion` (FastRoute.cpp1203) exports the complete
native grid. A pass's small scalar and the final complete grid have different
measurement scopes even when both are accurate.

The same scope affects expansion discovery: `getOverflowPositions`
(maze.cpp1874) also visits used-coordinate sets; `getCongestionNets` (1969)
finds competing nets near those positions. This is native incremental repair
of a local change, not automatically a census of every original congestion
location. It must not be assumed to select all439 owners identified below.

## Exported route changes, not inferred expansion membership

Canonicalizing each exported segment's endpoint order and sorting its segment
records finds438 of3659 net maps changed between initial and final artifacts.
Both northern target nets change too; final effects are not limited to the
southern seed pair. Sixteen changed names contain `clk`. This is a final
export comparison, not proof of exact native expansion membership: rerouted
nets can produce unchanged segments, and intermediate changes are not retained.

| Target | Initial / final planar segment sum, DBU | Initial / final strict OBS-intersecting segment records |
|---|---:|---:|
| `cell_pad[27]` |2700000 /2656800|7 /4|
| `cell_pad[31]` |554400 /576000|1 /1|
| `cell_val[27]` |2678400 /2692800|1 /1|
| `cell_val[30]` |540000 /525600|1 /1|

These are failed coarse-route diagnostics, not detailed wire length or illegal
physical intersections: boundary pin snapping can intersect OBS projections.

Initial preferred-layer attribution finds103 overflowing grid entries summing
to121 and439 distinct exported net owners, with no ownerless overflowing entry.
Of those439,321 have changed final segment maps and118 have unchanged final
maps. This does not establish that the118 were never rerouted. The initial
attribution uses the existing strict `planar_edges` indexing and calibrated
capacity-minus-usage; it does not interpret encoded capacity as physical tracks.

Do not blindly apply the same preferred-only release helper to the final
export: `u_cfg.frame_idx[1]` has one horizontal Metal2 segment
`133200 18000 Metal2 140400 18000 Metal2`. The strict helper correctly rejects
this nonpreferred record. This observation is not a claim of physical illegality
or an accounting defect; no unsupported final ownership census is inferred.

## Smallest discriminating observation if the corrected trial fails

First inspect the corrected retry's actual grid/capacity guard and native
outcome. Do not launch another run merely to repeat a confounded measurement.
If capacities remain exact and repair still fails, retain the same initial121
and selected southern pair, and add **observation only** at the initial reroute
and each of the existing four expansion boundaries:

- Actual seed/expansion net names, count and a stable sorted identity hash;
  distinguish newly added names from the retained congestion-net set.
- Complete native-grid per-layer overflow and capacity hash after each pass,
  alongside the existing touched-edge2D/3D values. Use the calibrated full-grid
  exporter or a reviewed equivalent, not the last native scalar as a proxy.
- Full segment snapshots after each merged pass, preserving all retained nets;
  independently check unchanged geometry, complete net census and capacities.

Existing `set_debug_level GRT incr 2` prints the **initial** dirty-net list
(GlobalRouter.cpp5694–5699). It does not print the subsequently expanded
`congestion_nets`/`dirty_nets` sets at5748–5759. No existing debug command found
in this source supplies those expanded identities. Logging this flag alone
would not complete the proposed observation. A force-mode-only attributed
observer at those boundaries would require its own review/build identity and
must reproduce the corrected run's final hashes before causal interpretation.

The decision then becomes concrete. If expanded membership stops growing
while whole-grid congestion remains elsewhere, test deterministic inclusion
of actual owners of those missing full-grid overflowing edges, rather than
increasing an arbitrary budget or changing placement. If the same covered
cut remains saturated under joint release, investigate its specific routing
feasibility/negotiation behavior. If whole-grid overflow falls within a pass
but later passes worsen it, examine native checkpoint preservation on those
actual full-grid states. None of these outcomes is established by the139 run.

## Source identity and limits

All references are to upstream commit
`dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`:
[GlobalRouter.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp),
[FastRoute.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/FastRoute.cpp),
[maze.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/maze.cpp),
[graph2d.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/graph2d.cpp).
Source SHA256:

- GlobalRouter.cpp: `71befc6541b5d2b0d22ec021e8c7f2d3edcd2c0dcf4575b0fb28ad21f5e5af83`
- FastRoute.cpp: `3fe281f6b7fbdd20ec46a7b81d38890f1358f09858cf17176739df2f208f7f0e`
- maze.cpp: `2e246dad9c6c07839b6ebceb35e765b2c4c43fdefa49c9041a453c4822bb11b3`
- graph2d.cpp: `2219502cc60e5e3fa32f354fef7ef289a214a2d32143cfd0d7121a2dc7da9599`
- Graph2D.h: `be1eca3c654786e2fb4d5fb86be912d2d2ded31fe5d2bf65a15bf18c4d32dca1`

Read-only local artifact analysis and pinned-source inspection only. No EDA,
new workflow, patch, hardware change or acceptance claim accompanies this report.
