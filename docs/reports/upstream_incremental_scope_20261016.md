# Upstream FastRoute changes relevant to incremental congestion scope

Immutable upstream source confirms that our pinned FastRoute omits a later
used-grid restoration fix. This is directly relevant to the touched-edge
metric/owner-discovery mechanism, but it is not evidence that restoring the
sets will route WARP. The current observer must first reproduce the measured
failed132 state. No tool upgrade, runtime patch or new EDA run accompanies
this research.

## The narrowly relevant fix

Commit
[50d692bea57e0840f2bd738223ea8700fbcb5362](https://github.com/The-OpenROAD-Project/OpenROAD/commit/50d692bea57e0840f2bd738223ea8700fbcb5362),
committer date2026-03-03 19:55:37UTC, adds restoration of used grid coordinates
at the start of incremental FastRoute runs. GitHub's comparison places it
579 commits ahead and zero behind the project pin
`dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`, with that pin as the merge base.
It was merged through
[PR9460](https://github.com/The-OpenROAD-Project/OpenROAD/pull/9460) on
2026-03-04 16:07:04UTC, merge commit
`e41c253aa345a346cd1336983bd43170cde4b2c6`.

Its source changes are small and explicit:

- `FastRouteCore::run` retains the existing used-set clearing, then invokes
  a new Graph2D rebuild helper only when incremental mode is active.
- The helper inserts every positive-usage horizontal edge for
  `0<=x<x_grid-1`, `0<=y<y_grid`, and every positive-usage vertical edge for
  `0<=x<x_grid`, `0<=y<y_grid-1`. These bounds include real preferred boundary
  edges and omit nonphysical endpoints.
- It reads existing usage and updates membership sets; it does not change
  edge capacities, route usage, net costs, routing budgets or physical geometry.

The upstream commit specifically motivates the change by segments introduced
during merged-net operations. Our experiment does not perform those merges.
The separate inference for WARP is nevertheless concrete: fixed routes retain
positive usage across an incremental reroute, while the pinned run unconditionally
clears their used-coordinate membership. The same rebuild scans that retained
usage regardless of how it was created. That makes this a source-supported
future experiment, rather than proof that upstream diagnosed WARP's case.

## Why membership affects routing, not just presentation

At the project pin, `getOverflowPositions`, `getOverflow2Dmaze` and
`getOverflow3D` traverse used-coordinate sets. `getCongestionNets` obtains
positions from that source and then searches route owners near them. Therefore
restoring committed positive-usage coordinates can expose congestion and
owners absent from the incremental pass's touched-only view. It does not
simply relabel a scalar. Membership also determines which edges receive normal
native congestion-history updates. A restoration helper makes no direct
history/cost changes, but subsequent native decisions may legitimately differ.
[Current pinned implementation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/maze.cpp).

This suggests a specific conditional next experiment: after authenticating the
current observer's132 result, compare its exact pass membership and complete
grid metrics with a force-only adaptation of the March rebuild. Preserve the
original full-run default and capacities, use the same initial121 state and
southern pair, and retain the existing bounded expansion limit. Do not combine
it with clock filtering, NDR policy, ordering, budget or placement changes.
The result could improve or regress. Native zero-overflow and all downstream
checks remain mandatory; no outcome is inferred from the source fix alone.

## What immutable current upstream does

For comparison, current upstream resolved during this research to
`d6bc758caed99ca4e58f9168717e57a9da536c10` (2026-10-16 18:00:20UTC).
Its full runs still clear used sets, while incremental runs reconcile existing
membership using `prepareForIncrementalRun`.
[Immutable FastRoute source](https://github.com/The-OpenROAD-Project/OpenROAD/blob/d6bc758caed99ca4e58f9168717e57a9da536c10/src/grt/src/fastroute/src/FastRoute.cpp#L2115).

That optimization comes from
[1f327f4452b953eb82f94ff01be3ec4dbd7ab1c0](https://github.com/The-OpenROAD-Project/OpenROAD/commit/1f327f4452b953eb82f94ff01be3ec4dbd7ab1c0),
September24,2026. It tracks dirty edge membership and reconciles it at incremental
boundaries, avoiding repeated complete scans. Its debug checker compares
membership with an independent full positive-usage scan. This is a broader
optimization with additional mutation tracking; the earlier complete-scan
helper is the simpler source reference for our small controlled experiment.
No performance claim from that upstream optimization applies to WARP.

The current `getOverflowPositions` still traverses used-coordinate sets.
Its owner lookup uses a boolean spatial map, introduced by
[153df984a796e53eeec2a495e32835378fe59b5a](https://github.com/The-OpenROAD-Project/OpenROAD/commit/153df984a796e53eeec2a495e32835378fe59b5a)
on August10,2026. That lookup improves search organization but retains the
position source and bounded radius expansion. It is not a separate fix for
missing committed coordinates and is not selected for backport.

A different May14 change,
[c8385eb48fb1dde1bc5472254d3aed69273eca5e](https://github.com/The-OpenROAD-Project/OpenROAD/commit/c8385eb48fb1dde1bc5472254d3aed69273eca5e),
changes incremental continuation/rejection tests from cached2D status to native
3D overflow. It also changes soft-NDR accounting and excludes clock nets from
congestion-owner expansion. Those are multiple behavior changes. They must not
be silently bundled into a used-set experiment, and this research does not
establish their necessity for the measured132 failure.

## Source hashes and limits

Raw source files were fetched read-only and retained under `/tmp/warp111-*`.

| Immutable source | SHA256 |
|---|---|
| March fix FastRoute.cpp | `54b88c3ee393e62bed99a924778a8109d3bbbe3cb1d25ef65582907880eff731` |
| March fix graph2d.cpp | `32e590bbda42c6c1037b38b8e857971a4eefe80efa9b8dfbdace6382b36f58e6` |
| Current fixed-HEAD GlobalRouter.cpp | `6732dca678cc8de7116ec3a5a3bafb73008d256a376b4371d862442e5c5e2ecb` |
| Current fixed-HEAD FastRoute.cpp | `411f7984eacf689e5f31823c93e5263587b3725086e5441cd4e16406f13bc2f8` |
| Current fixed-HEAD maze.cpp | `5961c839aa0207a7dc9f88a4c83df41a9536e5b668ed96f376fc26ff27e1ed6e` |
| Current fixed-HEAD graph2d.cpp | `38260b321be96395ccc25c44f9d5fe57eca3c7d43ed462a33f7598e930bb7995` |

The unchanged source retains OpenROAD Authors' BSD-3-Clause headers. Preserve
complete upstream license and attribution in any future source/build artifact.
No source survey, upgrade or source-only result qualifies the compact chip.

## Contingent review artifact, not an executed experiment

A separate candidate exists only at
`/tmp/warp_used_grid_rebuild_candidate.patch`, SHA256
`a640b087007a761102f469e3a518213153c374b5c7bc4b4d1e7c606550115c84`.
It applies **after** the current D101 observer patch
`72257372cd11e3ca3cdc9f53bbda13764f2dedf6bf79c2309f56f3006948c864`.
The tracked runtime patch and collector are unchanged by this preparation.

The candidate reuses the March helper's function body byte-for-byte, with its
upstream commit attribution. An explicit forced-repair-only environment option,
`WARP_FORCE_REBUILD_USED_GRIDS=1`, temporarily enables restoration immediately
after the existing used-set clear. Unset preserves the D101 path; every other
value rejects before mode mutation. The prior boolean is saved and restored
by the existing success/error cleanup. Full/ordinary incremental behavior is
unchanged when forced opt-in is not active.

Only positive-usage membership sets are restored; there are no new writes to
capacity, usage, history, cost, seed or budget fields. Subsequent native history
updates may naturally cover more edges, which is the intended algorithmic
experiment, not an observation-only replay. The same binary can therefore
provide default121, unset-option legacy132, then one explicitly selected
membership-restoration comparison after the current observer is authenticated.
Those runs have not been executed here.

Patch dry-run succeeds against copies of the exact pinned sources with D101
applied. No C++ compilation, native regression or EDA was performed. Integration
and execution remain contingent on the ongoing observer's actual equivalence
and membership/full-grid evidence, independent review, and the original source,
capacity, geometry, clock and acceptance guards.
