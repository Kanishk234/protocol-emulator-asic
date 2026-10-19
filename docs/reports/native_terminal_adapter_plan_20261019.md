# Minimal native terminal, via and exterior adapter plan

This is a read-only source plan, contingent on successful native collection, exact checkpoint identity and raw usage reconciliation. Build39304728263 succeeded; build success alone does not establish any of those gates. The first qualification39331153087 encountered root-owned0600 artifact permissions; retry39331845906 is pending at revision6b19d03 when this plan is written. No C++ extension, solver invocation, hardware edit or new trial follows from this report.

## Admission before extraction

Require successful native completion/inventory checks, all protected121/132/139 controls, `native_checkpoint` exact equality of all three initial snapshots and the unchanged default initial/final snapshot, and a clean `native_corridor` weighted STEP-multiset reconciliation on the selected initial snapshot. Preserve raw edge costs, clock/soft-NDR flags, layer limits and uint16 discrepancies. A mismatch is an observation to diagnose, not permission to invent fixed background demand. Keep native authentication and physical acceptance false.

Check union versus multiplicity before using the current oracle. It charges one per-net layer demand per occupied edge; native release may charge repeated tree-step occurrences. If those differ, a union adapter does not reproduce the selected native state. A future candidate can change topology, but releasing old demand and charging the new witness must be independently checked under the declared rule. Do not deduplicate the old state until the ledger fits.

## Smallest additional observation, using pinned state

Source contract is OpenROAD `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`, retaining existing patches. Relevant functions are in [GlobalRouter.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp), [FastRoute.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/FastRoute.cpp), [utility.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/utility.cpp), [maze3D.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/maze3D.cpp) and [DataType.h](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/include/DataType.h).

The minimal extension would export existing values at the same idle initial checkpoint, with exclusive files and completion counts. Do not call route rebuilding, `updatePinAccessPoints`, `makeFastrouteNet`, or incremental initialization to obtain them.

| Join | Exact pinned source state | Check required |
|---|---|---|
| Database net to live net | Existing FrNet slot, `getDbNet()->getId()`, name, and GlobalRouter `db_net_map_` | Unique name/ID/slot, complete classified route inventory, no guessed joins |
| Physical pin to native coarse pin | GlobalRouter `Net::getPins()`; `Pin::isPort()`, `getBTerm()`/`getITerm()`, `getName()`, `isDriver()`, `getOnGridPosition()`, `getConnectionLayer()` | Export physical identity, current grid position and connection layer; account for every membership in each deduplicated FrNet pin |
| Coarse-pin construction | `findFastRoutePins()` and `makeFastrouteNet()` | Reproduce connection-layer clamping to `getNetMaxRoutingLayer`, grid-origin/tile division, x/y/layer deduplication and root selection; compare exact FrNet PIN ordering/index/driver |
| Tree terminal access | `sttrees_[id].nodes`, `node_to_pin_idx`; TreeNode `x,y,stackAlias,botL,topL,hID,lID`; TreeEdge endpoint aliases already exported | Export maps and node access state with bounds/completeness checks; preserve distinct pins sharing x/y at different layers |
| Terminal via stack | `getViaStackRange(netID,nodeID,bot,top)` logic | Independently derive the min/max FrNet pin layer among pins with that tree-node x/y; compare any exported result and reject missing/sentinel ranges |
| Layer and physical geometry | Actual technology routing level/name/direction, DBU, raw grid origin/pitch and existing reporting axes/geometry | Join zero-based native layers to one-based database routing levels; retain all real H/V boundary edges |

`findFastRoutePins()` uses C++ signed integer division, which truncates toward zero; Python floor division is different for negative positions. Its validity test admits `pinY==-1`, while the current explicit-graph parser requires real node coordinates `y>=0`. There is no evidence yet that WARP has such a pin. If observed, retain it as an unsupported terminal contract and inspect native clamping/access semantics; do not relax bounds blindly.

Root selection is subtle: when a driver pin collapses onto a tuple already seen, the source does not update `root_idx` in that duplicate branch. Preserve the actual driver index and membership/order, rather than selecting a new physical driver by convenience.

### Why raw STEP alone is insufficient for connectivity

`releaseNetResources()` consumes weighted raw route steps, so those are the resource ledger. Separately, `get3DRoute()` inserts endpoint via stacks using tree alias access intervals and `getViaStackRange()`, then deduplicates output geometry. Its merged segment graph is useful for connectivity but cannot replace the multiset ledger. `setupHeap3D()` accesses terminal pin layers through `node_to_pin_idx` for two-terminal nets and tree access ranges for larger trees. The adapter needs both accounting and access/connectivity views, tied to the same checkpoint.

Coarse adjacent-layer via arcs have zero native planar-track demand; they do not model physical via cuts, enclosure, spacing or detailed accessibility. Net min/max layers constrain planar moves. Do not delete via-only access on a layer outside that planar interval. An optimistic adjacent-layer graph remains a declared relaxation of native search/access restrictions until the exported node/terminal state is joined and checked.

## Corridor and exterior contract

Choose one deterministic actual overloaded component and a bounded halo from the authenticated snapshot; log its vertices, released net set and rule. For each selected net, identify actual crossing edges and keep the exterior endpoint/component identity, layer and multiplicity. Keep interior real-pin terminals and prove that every released resource belongs to a selected net. Fixed demand on an interior edge is raw usage minus the exact selected multiset contribution; reject negative residuals and retain originally overfull fixed edges as explicit infeasibility, not extra capacity.

Remove only the selected interior route edges from the complete authenticated connectivity graph and compute each net's connected exterior components. Include the via/access graph needed to connect coarse pins, not merely raw planar STEP. Preserve all real boundary edges; do not cut off the final row/column or invent a free crossing. Crossing terminals coincident in geometry can be deduplicated for connectivity only after their net/component and release accounting remain explicit.

**First model within the current schema:** pin every boundary crossing and require all listed terminals of each net to connect inside the explicit corridor graph. Freeze the exterior and never introduce an implicit shortcut. A checked feasible witness is sufficient for this stronger connectivity condition plus frozen exterior. Proven infeasibility is only for that restricted local problem: the unchanged exterior may already connect multiple crossings, so insisting they reconnect inside can rule out valid repairs.

**Faithful frozen-exterior model requires a later schema change:** per-net exterior-component connectivity must be represented by net-private equivalence constraints or a separately validated expanded graph. The current solver accepts only physical orthogonal wires/adjacent-layer vias and has no net-private virtual-edge primitive. Do not disguise an exterior component as a zero-cost wire, fake via or shared supernode; that could let one net use another net's exterior or violate the geometry/demand contract. No such extension is implemented here.

Capacity-feasible output remains a constructive witness of the declared graph. It must be recombined with the fixed exterior, checked against all terminal memberships/resources, and later survive native guide handoff, complete routing and original physical/timing checks. Neither a restricted UNSAT result nor a timeout proves the chip impossible.

## Concrete size limits and selection implications

Current oracle limits are5000 nodes,12000 edges and128 nets. It constructs **two variables per edge per selected net**, even for a planar layer forbidden to that net: default100000 variables, absolute maximum500000. Crossing terminals count within the vertex bound. These are implementation limits, not feasibility measurements.

The known native grid179×98 with four layers expands to70168 layer vertices,139228 planar H/V edges and52626 adjacent-layer via arcs. Their total191854 edges exceeds the oracle limits before adding any exterior representation. The full439-owner cohort also exceeds128 nets. A full-chip exact solve is not what this implementation can presently attempt.

For a fully populated `w×h` window across four layers, including all H/V edges and all three adjacent-layer via arcs per grid position:

`vertices=4wh`, `edges=4[(w-1)h+w(h-1)]+3wh=11wh-4(w+h)`.

| Window | Vertices | Edges | Selected nets allowed by variable count |
|---|---:|---:|---:|
|33×33|4356|11715|4 at default100000;21 at hard500000|
|34×34|4624|12444|Rejected by edge limit before solving|
|10×10|400|1020|49 at default100000; capped at128 by net limit with500000|

At128 selected nets, dense construction admits at most390 edges under the default variable cap, or1953 under the hard cap. These arithmetic counts assume the full rectangular graph and do not predict solver runtime, useful detours or actual corridor feasibility. Removing impossible/irrelevant edges can reduce size only with a checked restriction/relaxation statement; pruning detours makes UNSAT narrower. Do not raise limits merely to hide a poorly bounded extraction.

## Smallest meaningful tests before any native adapter use

1. Hand-computed physical-pin memberships: two physical pins collapsing to one coarse tuple, same x/y on different layers, driver-collapse ordering, clamped connection layer and signed-division boundary. Reject missing memberships and unsupported negative grid coordinates.
2. Alias/via access: a terminal whose raw planar tree endpoint is on another layer, an endpoint stack generated by `get3DRoute`, and a pin accessing via a layer outside planar min/max. Check connectivity while preserving zero planar via demand and unknown physical via feasibility.
3. Exterior components: two crossings already connected outside, two disconnected outside components of one net, and coincident crossings on different nets. The strict first model must report its extra inside-connectivity restriction; any later component-aware model must prevent cross-net shortcuts.
4. Accounting: selected-net repeated edge occurrences, different layer costs, fixed background demand, an overfull fixed edge and a boundary release. Reconcile the old ledger before/after extraction; independently check the new witness's per-net union occupancy and all frozen resources.
5. Fail-closed extraction: omitted final-row/column edge, invalid layer join, incomplete tree/pin alias map, out-of-window terminal, changed initial checkpoint and exceeded node/edge/net/variable limits. No silent expansion, inferred terminal or resource relaxation.

Only after the actual ledger is known should a single bounded extraction be selected and qualified against those tests. The first useful result may be an explicit unsupported access state or a restricted infeasible window; report it precisely instead of calling it routing closure.
