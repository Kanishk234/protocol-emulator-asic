# Minimum native contract for a corridor feasibility oracle

The existing121 artifacts support topology and an optimistic residual graph,
but **do not yet specify an exact native capacity model**. An explicit CP-SAT
graph is useful only with declared resource/terminal/via assumptions. No solver
result should be called a WARP routing result until the missing live state is
exported and reconciled. This report selects the minimum observation contract;
it does not modify routing, build a tool or launch a workflow.

## Facts already available

The authenticated initial121 full segment map, canonical interior grid,
preferred boundary edges and physical census survive in the39143364213
artifact under `build/repair110_result/route_force_repair/`. Independent audit
identifies103 overflowing layer entries and439 exported owners. Those are
baseline facts, not evidence that every owner's native demand equals one.

OpenDB/Tcl can read actual layer directions, database units/grid coordinates,
net signal type and database NDR rule, physical instance/pin rectangles,
macro obstructions and boundary pins. The existing `cloud_boundary_audit`
export already exercises the relevant geometry APIs. However:

- OpenDB's reporting capacity/usage are encoded quantities. The pinned native
  exporter includes reductions in capacity and usage and combines horizontal
  and vertical usage. Repeated/display boundary cells are not physical edges.
  Subtracting reporting capacity from usage reproduces calibrated overflow;
  the positive capacity field is not a raw available-track count.
- Database NDR attributes do not encode live FastRoute soft-NDR state.
  Active per-layer demand must not be inferred solely from database wire width.
- Physical pin rectangles do not determine the live deduplicated/clamped
  FastRoute terminal grid/layer or all allowed access choices.
- Merged segment exports are geometry, not a proven per-net accounting ledger.
  Existing unit own-release analysis was explicitly optimistic; it is not the
  weight contract for the new oracle.

## Small read-only OpenDB observer

`patches/corridor_contract_observer.tcl` is a standalone supplemental observer.
It requires a preexisting `WARP_CORRIDOR_DIR`, a loaded block/reporting grid,
and the expected R0 `u_fabric`. Its exclusive output `odb-facts.tsv` contains
DBU/grid axes, actual routing-layer directions/levels, net types and database
NDR identity, instances, physical ITerm/BTerm shapes and macro/block obstructions.
It explicitly labels itself OpenDB-only and reports via feasibility unexported.
It neither invokes routing nor changes configuration or geometry.

SHA256: `775086e76741e32ad6feb3f2be861eb4a6ffd5d3cba7a154a6db36b8635cfb44`.
Tcl syntax completeness passes using the project venv's Tcl interpreter.
No native execution has validated this new observer. Its APIs follow pinned
OpenDB declarations and the existing geometry exporter. A partial file without
successful native completion/census checks is not evidence. This file is not
wired into a recipe or workflow by this task.

## Missing live-state export requires narrow C++ observation

Add a separately reviewed, read-only export at the **same authenticated
initial121 checkpoint**, after native routing/layer assignment completes.
Keep the same binary's observation-disabled control and require identical121
segments, interior grid and boundary data before interpreting exports.
Do not reconstruct this state by loading an ODB alone: internal soft-NDR flags
and current tree allocations do not survive as an equivalent OpenDB contract.

### Identity, edges and resource definitions

Record source commit, binary/patch hashes, workflow run/attempt, source/config/
ODB/SDC/PDK hashes, checkpoint route hashes, actual DBU and grid origin/tile
size, all grid axes and actual layer directions. Declare layer index bases;
FastRoute FrNet layer indices are zero-based, OpenDB routing levels one-based.

Export separate **raw horizontal and vertical native edge arrays** for every
layer, with capacity, usage, reduction and real-capacity fields where present.
Include all valid H edges `x<nx-1,y<ny` and V edges `x<nx,y<ny-1`, retaining
direction even on a nonpreferred layer. Exclude nonphysical endpoint cells
from the edge set; preserve their reporting values separately if desired.
Do not substitute `getCapacityReductionData`, which also aggregates encoded
reporting capacity, for the raw arrays.

Keep the calibrated reporting exports alongside raw arrays and demonstrate
that the pinned native encoding maps one to the other, including preferred
boundary edges and corner/sentinel treatment. Export arrays by reading them,
never by calling an adjustment or recalculating capacity. Any integer wrap,
negative residual accounting or unresolved encoded/raw mismatch blocks an
exact-native claim.

### Every live net's demand and terminal state

Iterate the complete live net map/`nets_`, not `net_ids_`: native `run` clears
the active routing-ID vector after collecting routes. Preserve the distinction
between3659 routed exports and other local/single-terminal database nets.
For each live net export:

- Stable database name/identity, route presence/local/merged status and native
  `FrNet::isClock()`; retain database signal type separately for reconciliation.
- `isSoftNDR`, actual scalar `getEdgeCost`, `getLayerEdgeCost(layer)` for every
  layer, current planar min/max layers, and database NDR identity. The scalar
  can differ from per-layer costs; neither may silently replace the other.
- Every actual FrNet pin `(pin_index,x,y,layer)`, driver index and all terminal
  memberships collapsed into a coarse pin. Join these to GlobalRouter's live
  pin positions and the physical shapes, with any clamping/deduplication and
  aliasing explicitly represented. Export tree-node aliases/layer access
  intervals when they determine access choices.

The authoritative3D wire weight is the live **per-net, per-layer** cost.
Require `demand_by_layer` explicitly in the oracle input; never default it to
unit demand. The scalar2D cost and history penalties are search machinery,
not additional physical3D tracks. An integer3D resource oracle should not
encode a100-times NDR search penalty as physical wire consumption.

### Per-net edge accounting and fixed demand

Export the actual tree/grid-walk contributions used by native debit/credit
code, including repeated edge multiplicity and per-layer weights. Derive this
from the live `TreeEdge.route.grids`/routing state and reconcile it with the
same semantics as `releaseNetResources`. Do not assume the final merged
segment set preserves accounting multiplicity or that each net contributes
one unit to each geometrically unique edge.

For **every** raw edge require an explicit conservation check:

`raw_usage = fixed_or_external_usage + sum(all exported net contributions)`.

When releasing selected nets, subtract only their reconciled contributions.
Require the remaining fixed usage nonnegative without clamping. A corridor
boundary cut must preserve all outside connections and fixed crossing demand;
its declared boundary terminals are part of the problem, not optional traffic.
If some native usage cannot be assigned, retain it as identified external
fixed occupancy with provenance, or reject exact accounting. Do not silently
treat unexplained demand as free capacity.

A Boolean per-net edge variable models union occupancy for a newly routed
net. That is a declared new-route accounting choice, not a claim that arbitrary
old tree multiplicities equal the union. The native route integration must
check/de-duplicate the proposed tree and remeasure actual usage afterward.

## Via and pin-access semantics: two distinct levels

Pinned `maze3D.cpp` permits adjacent-layer transitions within global layer
bounds and assigns via costs; it does not model a physical cut-capacity budget
or detailed enclosure/spacing legality for those transitions. Its planar moves
apply per-net min/max layer tests, while its via moves have different guards.
Do not remove all nodes outside planar min/max if they are needed by an actual
terminal access stack. Export allowed planar layers and via arcs separately.

An oracle matching this **coarse global abstraction** can declare explicit
adjacent-layer via arcs with zero planar-track demand and unbounded coarse
co-occupancy. It must state that detailed via access is optimistic, not invent
one-via-per-node capacity or silently allow unspecified transitions. Every
terminal must connect on its recorded live access layer/location, with any
permitted portal/stack exemption explicit. Macro-interior deletion based only
on a bounding box can remove native pin-credit access; use declared raw-edge
availability and explicit access exceptions instead of an unexplained mask.

A physically legal via graph would additionally need detailed-router pin
access points, allowed via templates and location-specific enclosure/spacing/
obstruction checks, including interactions among selected vias and wires.
Neither the current artifacts nor the supplemental Tcl file establish that
contract. A coarse solution must therefore be reintroduced into the native
complete chip and pass routing, connectivity, detailed DRC/antenna, extraction
and timing before any physical claim.

## Minimum useful oracle and honest outcomes

The smallest justified implementation accepts explicit net-layer demands,
raw-edge capacity/fixed occupancy, exact terminals, explicit via arcs and
boundary obligations, plus an assumption manifest identifying omitted physical
constraints. It can start with a declared small released set and expand the
region only as a separate measured modeling choice.

- **SAT/FEASIBLE:** a capacity-respecting route in the exported graph under its
  assumptions. Retain assignment and independently verify every edge balance,
  terminal connection and boundary obligation. It is a candidate, not proof
  that native detailed routing or configured timing passes.
- **UNSAT:** no assignment for that exact released set, corridor, fixed demand,
  allowed arcs and terminal choices. If those are restrictive, this says
  nothing about the whole chip. A proved-infeasible optimistic supergraph can
  rule out the corresponding less permissive graph only if its supergraph
  relationship and resource semantics are established.
- **UNKNOWN/TIMEOUT:** no feasibility conclusion. Do not report this as UNSAT.

Until the live export and conservation checks pass, the explicit graph remains
an abstract feasibility experiment. That still tests the solver and can expose
cuts in its declared model, but it is not a hidden claim that WARP has escaped
the measured routing basin.

## Pinned source references

All native source discussion refers to
`dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`:
[GlobalRouter.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp)
for pin-grid conversion and reporting wrapper;
[FastRoute.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/FastRoute.cpp)
for reporting encoding, live net lifecycle, scalar/layer costs;
[DataType.h](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/include/DataType.h)
for FrNet state/accessors;
[RipUp.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/RipUp.cpp)
for actual usage debit;
[maze3D.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/maze3D.cpp)
for planar/via guards. New observation must retain upstream attribution and
licenses; no upstream source was modified here.

## First native export tranche prepared, not executed

`patches/openroad_corridor_observer.patch` is a separate additive patch applied
**after** the existing D101 `openroad_force_reroute.patch` and D102
`openroad_force_used_grid.patch`. It does not replace either routing experiment.
Its explicit Tcl/SWIG entry point is:

```tcl
# Caller must create a fresh, writable directory before loading this observer.
# Invoke after the authenticated initial121 route, before forced rerouting.
set ::env(WARP_CORRIDOR_DIR) /absolute/fresh/observer-directory
grt::export_native_corridor_state
```

The entry point rejects an absent/empty directory variable, an existing
`native-corridor.tsv` (including unreadable files and dangling symlinks),
uninitialized or empty routes, pending dirty nets, explicit incremental mode,
incremental callbacks, active forced rerouting, CUGR, and detailed routing. It
opens no routing transaction and calls no placement, route, history, resource,
cost, classification or configuration setter. Serialization completes in memory
before atomic Linux `open(O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0600)` creates the
final file. The write loop retries EINTR and handles short writes, rejects zero
or failed writes, and checks close before logging success. A failed write throws;
partial files without a successful close and completion witness are invalid.
Directory creation and artifact/provenance handling belong to the caller, who
must use a fresh privately owned directory. Parent-directory symlink resolution
is not restricted; atomic exclusivity/no-follow protection applies to the final
file. No fsync or crash-durability claim is made.

The file schema is `warp-native-corridor-v1`, with tab-separated rows:

| Row | Fields after the row tag |
| --- | --- |
| `INDEXING` | `zero_based_fast_route_layers_and_grid` |
| `MODEL_GATE` | `usage_ledger_verified`, `false` |
| `VIA_MODEL` | `global_route_steps_only_no_physical_cut_capacity` |
| `GRID` | x count, y count, layer count, x corner, y corner, tile size |
| `EDGE` | H/V, layer, x, y, raw cap, usage, reduction, real_cap |
| `EMPTY_SLOT` | deleted native net slot index |
| `NET` | native slot, OpenDB net ID, raw name, native isClock, isSoftNDR, scalar edge cost, min planar layer, max planar layer, driver index, pin count |
| `DEMAND` | native net slot, layer, current getLayerEdgeCost(layer) |
| `PIN` | native net slot, pin index, grid x, grid y, layer |
| `TREE` | native net slot, terminal count, node count, edge count |
| `TREE_EDGE` | native net slot, edge index, len, n1, n2, n1a, n2a, routelen, grids size |
| `STEP` | native net slot, tree edge index, step index, from x/y/layer, to x/y/layer, current release weight |
| `COMPLETE` | native slot count, nonnull exported net count, exported step count |

Layer and grid indexing are explicitly zero based. Routing layer names, DBU,
physical pins and macro/obstruction geometry still come from the separate ODB
observer; the caller must bind both exports to the same source/database/control.
The native GRID corner/tile information is exported directly, without assuming
it is interchangeable with the OpenDB reporting axes.

For every layer, H covers `0 <= x < nx-1, 0 <= y < ny`; V covers
`0 <= x < nx, 0 <= y < ny-1`. These are raw FastRoute arrays, including the real
last-row H and last-column V edges; they are neither the encoded preferred-edge
reporting grid nor its 550-row boundary sidecar. Both directions are exported,
even when one direction is not preferred on that layer. No encoded capacity or
combined H/V usage is substituted. Every nonnull `nets_` entry is exported,
including native local nets, and its pointer-to-slot mapping is checked against
`db_net_id_map_`; this does not depend on the cleared active `net_ids_` vector.
Raw net names containing tab/newline fail rather than producing ambiguous rows.

The raw `TreeEdge::route.grids` multiset is accessible within FastRouteCore and
is now exported **without** calling `get3DRoute`, its synthetic via filling or
its unordered segment deduplication. The loop follows all tree edges and exactly
`route.routelen` consecutive grid pairs, as `releaseNetResources` does, retaining
multiplicity and native edge identity. Same-layer steps carry the current
`getLayerEdgeCost(from.layer)` value; layer-changing steps carry zero planar
release weight. Tree route completeness and layer bounds are checked before
indexing. This is a measured release-weight proposal, not proof of a historical
usage ledger: current soft-NDR/layer costs could differ from weights used when
old usage was accumulated, and nonunit, diagonal, stationary or malformed steps
must be rejected by the downstream auditor rather than silently normalized.
Raw step endpoint coordinates are preserved for that audit.

A downstream audit must enumerate every valid raw physical edge, validate all
step geometry and pin bounds, canonicalize each planar step to exactly one edge,
sum multiplicities with their exported current weights, and compare the sum with
raw `EDGE.usage`. The first tranche deliberately writes
`MODEL_GATE usage_ledger_verified false`. It neither labels unexplained residuals
as removable demand nor adds a fabricated fixed-occupancy term to force equality.
If any edge differs, the per-net release model remains unavailable until a
separately justified external-occupancy source or native accumulation mechanism
explains it. Do not accept a nonnegative residual alone as proof. No solver
acceptance gate should consume these contributions until reconciliation succeeds.
The complete current-cost export can independently assess the suspected scalar
versus soft-NDR asymmetry without changing policy.

Preparation verification: reconstructed the exact pinned source in
`/tmp/warp_corridor_base`, applied D101 then D102 sequentially with `patch
--batch --fuzz=0 -p1`, generated the new patch against that resulting tree, and
successfully ran `patch --batch --fuzz=0 --dry-run -p1` for all five new-patch
files. Original pinned source copies were preserved. Source anchors are
`FastRouteCore::get3DRoute`, `FrNet::getLayerEdgeCost`, `FrNet` in DataType.h,
and `FastRouteCore::releaseNetResources`; the latter establishes multiplicity
and weighting, not automatic successful reconciliation. The inherited upstream
BSD-3-Clause headers remain intact. No binary was compiled or executed and no
workflow/recipe/runner was changed. Compilation/SWIG qualification, exact121
control hashes with the observer disabled and enabled, unchanged geometry and
capacities, full census and raw-usage reconciliation remain required.

Patch SHA-256 at preparation:
`b7493c2fc4e4c7074363550fd0a059064ee739a4fc593f3eaf14081167a5ff65`.
Exact pinned `FastRoute.h` SHA-256:
`087b2384f112ab1d86c6d7fa535cb4210e167212af48fdb79944fced86910c80`;
`FastRoute.cpp`:
`3fe281f6b7fbdd20ec46a7b81d38890f1358f09858cf17176739df2f208f7f0e`;
`RipUp.cpp`:
`01d611451a42477740b225450a4388af4b758dd3345b90ff2b949af71e65755f`.

Independent source review identified missing `is_incremental_` guard and a
nonexclusive output-open race in the initial draft. Both were corrected before
build qualification: idle now explicitly excludes incremental mode, and final
output creation uses atomic exclusive/no-follow flags with checked writes/close.
The exact-source D101 then D102 application and observer `--fuzz=0 --dry-run`
were repeated successfully after these corrections. Neither draft has been
compiled or executed as part of this task.

Pinned `Edge3D` fields `cap`, `usage`, `red`, and `real_cap` are all
`uint16_t` (DataType.h lines 150–156), so the original direct stream insertion
was numeric. The exporter nevertheless now casts all four explicitly to
`int64_t`, preventing accidental character formatting if the underlying fields
change. Exact-source sequential no-fuzz dry-apply passed again after this edit.
The two `continue` statements are separate, intentional branches: retry an
interrupted write and skip a null native net slot. There is no duplicate
consecutive `continue` in the patch or generated source.
