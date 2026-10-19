# Next routing experiment after complete owner discovery

**Select one bounded intervention: preserve native clock-net routes during
congestion-owner expansion.** Keep the D102 used-grid correction and every
current geometry, capacity, clock, seed and iteration constraint. Add only an
explicit force-mode filter excluding `FrNet::isClock()` nets from expansion.
Do not alter clock routing layers, NDR policy, placement or timing margins.
This is a proposed experiment, not a patch, dispatch or predicted pass.

## What D102 now proves

Build39143345968 and qualification39143364213 complete. The downloaded portable
audit authenticates default121, legacy forced132, and membership-corrected139.
The candidate retains unchanged capacities, physical geometry and net census,
but returns native GRT-0232. Its complete per-pass observations are:

| Pass | Native pass input nets | Complete observed overflow | Initial overflowing-edge owners included |
|---|---:|---:|---:|
|0|2|121|2 of439|
|1|562|145|439 of439|
|2|638|142|439 of439|
|3|695|133|439 of439|
|4|711|139|439 of439|

Sources: `build/repair110_portable_audit.json`,
`build/repair110_candidate_pass_audit.json`, and retained native files under
`build/repair110_result/route_force_repair/rebuilt_pair/replay/1-openroad-globalrouting/`.
The membership correction works; it does not improve routing. The439-owner
result rules out continued failure merely because the initial full-chip
congestion owners were omitted. Frozen G1 and the lower121 routing checkpoint
remain protected. Candidate139 must not replace either.

## New evidence that selects the clock-preserving experiment

Initial native routing explicitly soft-demotes four NDR nets, in order:
`clk`, `delaynet_3_clk`, `clknet_0_clk_regs`, `delaynet_0_clk`.
All four are then present in the first562-net expansion. No further native
GRT-0273 demotion warnings appear during the five incremental passes.

Read-only canonical segment comparison with the initial121 state finds:

| Pass | Input names containing `clk` | Such names with changed segment records |
|---|---:|---:|
|0|0|0|
|1|19|12|
|2|20|13|
|3|23|15|
|4|23|16|

These are **name-based observations**, not a substitute for the router's
native clock classification. They show concrete clock-tree disruption beyond
the two southern seed nets. The proposed filter must use `FrNet::isClock()`;
log the actual native classification and selected/excluded identities so its
meaning is measurable rather than guessed from names.

Pinned source also reveals a relevant accounting risk. `applySoftNDR` sets
both the soft-NDR flag and scalar edge cost to unit cost. Later
`makeFastrouteNet` recomputes track consumption from the database NDR rule,
and `FrNet::reset` assigns that scalar cost while retaining the existing
soft-NDR flag. `getLayerEdgeCost` returns unit cost for a soft net, whereas
`getEdgeCost` returns the stored scalar; congested-NDR discovery skips nets
already marked soft. Thus remaking an already-demoted net can produce
inconsistent scalar/layer treatment unless some other path preserves the
unit scalar. Actual per-net scalar/layer cost snapshots are absent, so this
is a source-supported risk, **not a proven numeric explanation of139**.
Preserving the existing clock routes avoids remaking those clock nets without
bundling a separate cost-accounting change.

Pinned primary references:
[FastRoute.cpp reset and soft-NDR methods](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/FastRoute.cpp),
[DataType.h cost accessors](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/include/DataType.h),
[GlobalRouter.cpp net reconstruction](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp).

## Upstream support and precise adaptation

Immutable upstream commit
[c8385eb48fb1dde1bc5472254d3aed69273eca5e](https://github.com/The-OpenROAD-Project/OpenROAD/commit/c8385eb48fb1dde1bc5472254d3aed69273eca5e),
committer date2026-05-14 23:41:17UTC, explicitly adds a native clock-net
exclusion to `findNetsNearPosition`. Its broader commit also changes3D/2D
continuation and soft-NDR accounting. Select **only** the clock exclusion;
none of those other changes belongs in this comparison.

The project pin currently permits clock nets in `findNetsNearPosition`.
A reviewed force-only opt-in should add the exclusion there, preserving
ordinary/default behavior and the unset-option D102139 control. The initial
southern pair is nonclock; every subsequent expansion adds through this
owner-discovery path, so the restriction has a precise insertion point.
This freezes existing clock-net routes, not entire cells or unrelated signal
nets attached to clock-tree buffers. All other congestion owners remain
eligible. There is no request to change global clock layers or loosen native
capacity constraints.

## One comparison and its acceptance evidence

Use one binary with a strict opt-in and saved/restored mode state. Authenticate
its default121 and opt-in-unset D102139 identities first; then run one fresh
initial121→southern-pair repair with clock-preserving expansion enabled.
Do not continue from an already modified139 routing state. Keep seed,15 native
iterations and four expansion attempts unchanged.

Retain the existing complete per-pass grids, preferred boundary edges, merged
segments, native failures and geometry/capacity identities. Add exact native
clock identities and exclusion counts. Require that no clock-classified net
enters an expansion input set and that every such net's normalized segments
remain identical to its initial121 route at every pass. Require coverage of
the eligible **nonclock** initial congestion owners; do not falsely demand
all439 once clock owners have deliberately been excluded. The complete chip
must still retain all3659 routed net identities; freezing clocks does not omit
their guides or demand.

Compare final complete overflow with both the immediate139 control and the
best121 checkpoint. Lower than139 but still at least121 is not a new best.
Any nonzero overflow remains routing failure. Only zero native overflow with
complete guides/connectivity and original constraints can advance to detailed
routing, extraction, electrical/timing and physical/function checks. If this
single comparison fails, record and reject it; do not sweep neighboring clock
filters, seeds or budgets.

## Why not the other tempting changes now

The per-pass minima do not establish a passing saved route, and the best
complete candidate snapshot remains133, worse than121. Repeating139, merely
raising the budget, or retaining133 as a promoted result lacks support.
A blanket3D-gate bypass cannot negotiate hard-capacity blocked paths and needs
separate unreachable-path recovery. Broad placement and arbitrary ordering
were already rejected. The clock-preserving comparison instead follows an
actual newly exposed expansion effect and one narrowly identified upstream
behavior change.

## Evidence identity and limits

- D102 candidate native log SHA256:
  `b0559678b51aad8843a1115e4a0ade948032a098f39d624118e5c06fd7316ee2`.
- Candidate final segment SHA256:
  `10dffe113661bd822b02fa099b5c536bc87f310bb672999e09e7acac32296a46`.
- Pinned DataType.h SHA256:
  `332baabd51f956ecca65837caade5a59d20f4332748819ad1abf0bdafad051c3`.
- Pinned FastRoute.cpp SHA256:
  `3fe281f6b7fbdd20ec46a7b81d38890f1358f09858cf17176739df2f208f7f0e`.

Read-only source/artifact review only. No source edits, EDA or dispatch. Clock
rerouting and the reset asymmetry are reasons to test this hypothesis; neither
proves that clock preservation will make the chip routable.
