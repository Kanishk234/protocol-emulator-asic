# Exact133 failed-route topology, October 15

[Run38676688402](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38676688402) reproduces the best control's133 global-routing overflow and exact prior marker report. It exposes concrete long south/east detours for two north-edge macro signals. No route passes and no frozen hardware changes are proposed by this observation.

## Evidence and scope

Downloaded artifact: `build/autonomy_initial_trace/compact-route-trace-38676688402/route_trace/`. Source remains unchanged; native failure GRT-0116 is retained with returncode1. Native resources/demand104726/34728, usage33.16%; overflow by Metal1–4 is13/53/31/36. There are3659 exported native nets. Segment SHA256 `aee9b65f2cfc5f653793de924dedd919a7b68d67fa3ef3febf7ca17e3f1ad7ca`; selected-target SHA256 `f00a6206d105a949428454017fe32fa6553bf07c89428c95ac1d7ead661e37d4`.

Coordinates below are micrometers, converted from authenticated DBU1000. Lengths sum exported planar segments, excluding vias; they describe coarse failed routing, not final wire length, extracted delay or physical acceptance. Macro boundary is x121.44–1241.76/y15.12–684.18, with Metal1–4 full-footprint OBS confirmed by native export38456351705. Geometric OBS intersection at an endpoint can be normal coarse pin snapping; the remote interior crossings below are the informative cases.

| Net | Exported segments | Planar sum µm | Via segments |
|---|---:|---:|---:|
| cell_pad[27] |90|2685.6|47|
| cell_val[27] |83|2707.2|43|
| cell_pad[31] |41|590.4|22|
| cell_val[30] |39|554.4|21|

Both north-pin nets27 travel down from the west shell, across the south corridor at y3.6/10.8, reach x1249.2 beyond the east macro boundary, ascend the east corridor, and return across the north edge at y687.6. Their actual north macro pin rectangles are x770.20–770.60 and777.88–778.28/y683.78–684.18 respectively (native boundary audit). The selected routes prove this topology; they do not establish whether the alternative north-west route has adequate capacity under all other nets.

Concrete remote blocked detours:

- cell_pad[27] has Metal1 x277.2–291.6/y18 and Metal3 x298.8–306/y18, inside the south macro OBS; adjacent vertical Metal2/4 segments cross its southern boundary. Neither location is its north macro pin.
- cell_val[27] and cell_pad[31] share an exported Metal1 segment x298.8–306/y18. All three participate in south zero-capacity markers in the original report. These are separate net allocations, not an electrical short proven by a detailed router.
- cell_val[30] crosses Metal3 x111.6–154.8/y32.4, then Metal2 x154.8/y10.8–32.4. The portions x>121.44/y>15.12 lie inside the macro. Its actual south macro pin is x397.72–398.12/y15.12–15.52; the west logic pin is near x88/y222. This directly confirms the earlier remote-marker inference.

The exported snapped macro endpoints include cell_val[30] x399.6/y18 and the north nets x774 or781.2/y680.4–687.6. These differ from tiny physical pin rectangles by coarse-grid amounts; that alone is not evidence of a pin-placement defect. Failed route segments contain layer information, while congestion markers report Layer `-`; do not assign a physical-layer overflow count to each marker using an XY-only overlap.

## Prior experiments and next bounded diagnostic

D-085 already tested exactly the proposed net-order mechanism: `test_internal/cloud_net_order.py` and `patches/grt_net_order.tcl` compare seed0 with41 while explicitly disabling capacity perturbation. Run38279250531 worsens the original146 control to154 and combined133 to143; seed0 reproduces both controls, with matching resources. D-086 and the progress ledger reject this configuration. **Do not spend another workflow on arbitrary seed42:** this trace establishes a topology symptom but supplies no new evidence that a neighboring seed resolves it. The earlier seed42 proposal is withdrawn after reviewing that experiment.

The existing calibrated D-087 grid is already downloaded: [run38282629603](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38282629603), `build/cloud_grid_observer_38282629603/padded/1-openroad-globalrouting/native-grid.tsv`. Its relocated case authenticates the same source38167697696 and exact marker SHA256 `8e2f5c5003e495d3d347be7d593bb4bbc7801723db2902c3cb530e70a157a1df`, with identical per-layer resources/demand/overflow to38676688402. Therefore another grid-export workflow is unnecessary before analyzing these observations.

A fixed-column/row residual screen of that grid gives concrete competition evidence. On west column index16 (GCell center x118.8µm), inspect vertical layers Metal2/4 over y indices33–94 inclusive (centers241.2–680.4µm). Both layers have usage>=capacity simultaneously at indices61,62,67,68,69,70,71,72: centers442.8,450.0,486.0,493.2,500.4,507.6,514.8,522.0µm. Metal2 minimum residual is−2 tracks; Metal4 is−1. On north row95 (center y687.6µm), horizontal layers Metal1/3 over x indices16–107 inclusive, both layers are simultaneously saturated at indices16,22,23 (centers118.8,162.0,169.2µm). Each sampled capacity is positive; no zero-capacity sample occurs on these two slices. This is an observation of existing allocation, not proof that another column/layer-switching path cannot accommodate rerouting. In particular, the tempting short L-shaped perimeter is already competing at both its west leg and north corner; its geometric length alone does not make it feasible.

The read-only analyzer now also traverses the full peripheral grid using both preferred horizontal layers (Metal1/3) and both vertical layers (Metal2/4), permitting cost-free layer switches at every center. It excludes centers strictly inside native macro OBS and admits one outward access portal for each actual exported snapped macro terminal. Edges require strictly positive capacity-minus-current-usage in at least one applicable layer. This optimistic static graph connects all measured shell terminals into the same1621-center component, but reaches **none** of the four macro portals: north(107,95)/(108,95), south(57,1)/(55,1). Thus simply finding another unused centerline around the fixed current allocation does not repair these paths in this graph.

This is deliberately **not an infeasibility proof**. The current target net's own occupied resources are still included in usage; global negotiation can release them, displace other nets and change the cut. Cost-free vias omit real access constraints, while the single portal exempts its boundary access step and does not prove that step legal. Grid fields are interpreted as preferred-direction edge resources from each indexed center to its positive-axis neighbor, consistent with the calibrated observer's direction convention; aggregate calibration alone does not independently prove every physical edge correspondence. Neither an unreachable portal nor a hypothetical reachable one establishes a legal complete route.

Consequently the next discriminating observation should preserve per-net occupancy or release **only each target net's recorded planar allocation in a read-only accounting model**, then compare residual reachability with the original model. Do not modify the native design or claim the artificial residual model is a negotiated route. Before subtracting occupancy, verify segment-to-edge indexing against exact reported marker coordinates and ensure snapped pin extensions are not incorrectly charged as ordinary routed edges. If own-allocation subtraction opens a short north-west path, staged tree evidence becomes specifically relevant: why was that path not chosen after rip-up? If it stays closed, enumerate the saturated residual cut's actual other-net membership before considering any targeted placement or routing-order intervention. This supplies a concrete measurable next step without another EDA workflow.

A targeted hypothesis remains: for the north-bound nets27, competition in the west/north corridor makes the router select the much longer south/east perimeter. Alternative hypothesis: those detours originate before the negotiated route or layer assignment despite a feasible north-west route. Final segments alone cannot distinguish these. Moving cells or changing capacity now would confound them.

A concrete read-only next experiment should keep best133 exactly and add observation only: capture the four target nets' initial Steiner input/topology, post-negotiation 2D tree, and post-layer-assignment tree; join the already calibrated per-layer capacity/demand grid to the two peripheral alternatives. In particular compare the corridor outside x121.44 from each west endpoint up to y687.6, then east to the north macro pin, against the observed south/east route. Preserve all other nets: isolated-net routing would erase the competition being tested. No pin moves, partial-net route, added halo, changed grid origin or capacity adjustment is supported yet.

The pinned [OpenROAD debug command documentation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/README.md#global-route-debug-mode) distinguishes initial Steiner, rectilinear, negotiated2D and assigned3D trees. Its named-tree display is GUI oriented; a hosted collector must first verify a headless export path in pinned code, or use a minimal attributed runtime instrumentation patch with observation-only proof. Do not presume these switches alone produce useful files. The [pinned GlobalRouter implementation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp) supplies the corresponding callbacks and final route state.

The existing read-only artifacts already establish that cell_pad[27] has only one logical shell endpoint (three Metal1 shapes around x87.2/y235–237.6) and one north macro endpoint; cell_val[27] has two nearby shell loads around x56.0/y259.0 and67.1/y255.0 plus its north macro endpoint. Thus the southern traversal is not serving an undiscovered southern endpoint. A north-west path through the centerline x118.8/y687.6 would have roughly1.14mm rectilinear distance for pad27 before pin-access corrections, versus2.686mm exported planar sum. This is an optimistic geometric comparison, not a legal-route or congestion feasibility claim.

Observation acceptance requires unchanged source/physical-policy hashes, native133 and exact congestion-report hash, plus identical target segment hash to38676688402. If the observer changes routes, reject its causal comparison. The decisive measurement is where the south/east topology first appears and whether each north-west alternative has a continuous finite-capacity path with competing demand counted. If the initial tree already detours with available north-west resources, investigate topology/maze negotiation; if it changes only in3D, inspect layer allocation. If north-west edges are saturated, a separate endpoint/cell-level congestion intervention needs that local evidence before proposing a one-variable edit.

Still missing: staged trees and a full corridor connectivity/capacity analysis rather than two fixed slices and any route passing all downstream checks. Current evidence does not support a specific hardware or placement edit. The west-channel450–550µm concentration and high local cell occupancy remain unresolved by the four-net analysis. Preserve133; no regression or diagnostic counts as physical acceptance.

## Reproduction

Read-only analyzer: `tools/autonomy/route_analysis.py`; it reports strict OBS interior intersections including segments whose endpoints both lie outside. From an activated project venv:

```sh
python tools/autonomy/route_analysis.py build/autonomy_initial_trace/compact-route-trace-38676688402/route_trace/target-segments.json --grid build/cloud_grid_observer_38282629603/padded/1-openroad-globalrouting/native-grid.tsv
pytest -q tools/autonomy/tests/test_route_analysis.py
```

Six focused tests pass locally on October15, including crossing-versus-touching geometry, malformed/diagonal/cross-layer rejection, and residual connectivity across preferred-layer switches with a saturated-edge cut. No local EDA was run, no phase boxes ticked, and the known133 control remains preserved.
