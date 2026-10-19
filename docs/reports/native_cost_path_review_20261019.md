# Native scalar and per-layer cost paths — 2026-10-19

Read-only source review, pinned OpenROAD
`dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`. This distinguishes a concrete
scalar/soft-NDR state transition from its unmeasured runtime consequences.
No source, policy, hardware or workflow was changed and no routing was launched.
At writing, observer build `39304728263` succeeded; native qualification
`39331153087` at `675b659` failed host-read/upload permissions (BUG102); corrected retry `39331845906` at `6b19d03` is active. No native export distribution or ledger
outcome is asserted here.

## Concrete state transition

`GlobalRouter.cpp:1388–1407`, in `makeFastrouteNet`, computes track consumption
from the database rule and passes a scalar cost and per-layer cost vector to
`FastRouteCore::addNet`. `FastRoute.cpp:249–278` reuses an existing FrNet, calls
`clearNetRoute` first, then calls `FrNet::reset` with the freshly computed costs.
`clearNetRoute:355–363` releases the old tree resources before clearing it.

`FastRoute.cpp:2201–2221`, `FrNet::reset`, overwrites `edge_cost_` and the layer
cost vector but does **not** reset `is_soft_ndr_`. Consequently an already-soft
FrNet can retain its soft flag while receiving a new nonunit scalar. This is
possible from the source; its occurrence and affected net counts still require
the actual observer export.

`FrNet::getLayerEdgeCost`, `FastRoute.cpp:2167–2174`, returns the supplied layer
vector only when it exists and `!is_soft_ndr_`; otherwise it returns one.
`getEdgeCost`, `DataType.h:76`, directly returns the scalar, without checking
soft-NDR. Thus `soft=true, scalar>1, all layer demands=1` is a valid source state.
The parser correctly permits it; it rejects soft=true with any nonunit layer
demand. A scalar-versus-layer difference alone is **not** an impossible export.

Within `run`, `FastRoute.cpp:1714–1740`, congestion may trigger
`computeCongestedNDRnets` followed by `applySoftNDR`. `computeCongestedNDRnets`
`:1897–1901` ignores already-soft nets. `applySoftNDR:1860–1880` subtracts old
scalar 2D route usage, calls `setSoftNDR`, then adds new scalar usage.
`setSoftNDR:1883–1887` sets the flag and scalar one. The helper
`updateSoftNDRNetUsage:1949–1981` changes **graph2d_ only**; it does not adjust
raw 3D edge usage. This transition occurs during negotiation before the
`layerAssignment` call at `FastRoute.cpp:1804`. No conclusion that it leaves
stale 3D usage follows merely from absence of a 3D update in this helper.

## Which cost charges which resources

| Path | Scalar use | Raw 3D usage use |
| --- | --- | --- |
| `FastRoute.cpp:808–836`, `updateEdge2DAnd3DUsage` | graph2d H/V usage | `getLayerEdgeCost(k)` |
| `utility.cpp:1159–1171`, `assignEdge` commit | scalar also influences fallback-layer threshold, not this 3D charge | per-layer cost |
| `maze3D.cpp:1557–1570`, committed 3D reroute | graph2d H/V usage | per-layer cost |
| `RipUp.cpp:371–402`, `releaseNetResources` | graph2d H/V usage | per-layer cost |
| `RipUp.cpp:349–362`, 3D ripup | graph2d H/V usage | per-layer cost |
| `utility.cpp:1695–1709`, restored route usage | graph2d H/V usage | per-layer cost |

The 3D search guards at `maze3D.cpp:841–1016` use the current per-layer cost
when comparing usage plus demand to edge capacity. Layer assignment dynamic
programming similarly compares available resources against per-layer demand
at `utility.cpp:947` and `:1070`, then charges that per-layer demand. Its
out-of-range-layer fallback helper `fixEdgeAssignment:469–497` uses the scalar
`net_cost`, passed by `assignEdge:755`, to decide whether enough spare capacity
has been found. Scalar divergence can therefore change 2D negotiation pressure
and fallback choices, without replacing raw 3D physical consumption by scalar
weights. This is a falsifiable behavior concern, not a routing-improvement claim.

The native debug verifier `utility.cpp:1868–1937`, `verify3DEdgesUsage`,
independently reconstructs raw 3D usage by iterating every net's complete tree
step multiset, skipping layer-changing steps and adding `getLayerEdgeCost`.
It separately reconstructs scalar 2D totals. This is direct source support for
the observer/parser ledger contract. It does not establish that the verifier
ran or passed on this chip.

A separate unit-increment path exists:
`FastRoute.cpp:789–805`, `incrementEdge3DUsage`, adds one per grid edge. Its
observed caller is `GlobalRouter::updateEdgesUsage:2459–2482`, used by
`readGuides`/`loadGuidesFromDB` at `GlobalRouter.cpp:2345` and `:2383`.
A guide-restored database must not silently be equated to an authenticated live
initial global-route export; that route-loading path can have a different
accounting provenance. It is not evidence that ordinary 3D tree commitment
uses scalar costs.

## Discriminating actual-export checks

First authenticate exact initial121 and corresponding default/legacy/candidate
final identities. For **each** initial/final snapshot, report the full
distribution of `(soft_ndr, scalar_cost, demand_by_layer)` with stable native
slot, OpenDB ID and raw name joins. In particular:

| Requested measurement | Initial121 | Final legacy132 | Final membership139 |
| --- | --- | --- | --- |
| soft-NDR net count | pending export | pending export | pending export |
| soft-NDR with scalar greater than one, counts grouped by scalar | pending export | pending export | pending export |
| corresponding names, clock classification and STEP-edge support | pending export | pending export | pending export |
| all soft demands exactly one | pending export | pending export | pending export |
| exact raw-3D weighted multiset reconciliation | pending export | pending export | pending export |

Do not substitute clk-name heuristics for native `isClock`, or database NDR
presence for native `isSoftNDR`. Join the same nets across initial/final exports;
new nonunit scalars on retained soft nets would support the reset mechanism.
Their absence falsifies occurrence at the measured checkpoints, although it
cannot exclude a transient state between checkpoints.

Run the per-layer-weighted STEP multiset audit against **every** raw H/V edge
first. If it matches, scalar divergence has not broken that checkpoint's raw
3D ledger; the 2D negotiation question remains distinct. If it fails, retain
signed residuals `R(edge)=raw_usage−sum(layer-weighted STEP contributions)`.
As a diagnostic fingerprint only, compute
`D(edge)=sum_soft_nets(multiplicity*(scalar−layer_demand))` and compare exact
support, sign and magnitude with R. Residual edges outside the affected nets'
STEP support, or inconsistent magnitudes, reject the simple scalar-charge
account. Even exact agreement is correlation, not authorization to replace
layer weights or fabricate fixed occupancy; native accumulation history would
still need explanation. Check missing tree contribution/local/access or
guide-restoration provenance separately rather than coercing equality.

The current exporter emits raw 3D arrays, not graph2d scalar usage. It can prove
whether costs diverge and whether the raw 3D ledger reconciles, but cannot by
itself quantify a 2D usage mismatch. Any later 2D observation would need its own
source-bound contract; no extra instrumentation or policy change is proposed
as a fix by this review.

## Source identities

All line references above refer to the unmodified pinned source, before WARP
patches shift line numbers. Immutable upstream source location:
[FastRoute.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/FastRoute.cpp),
[utility.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/utility.cpp),
[maze3D.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/maze3D.cpp),
[RipUp.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/RipUp.cpp),
[GlobalRouter.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp).
Inspected local SHA256 values:

- FastRoute.cpp: `3fe281f6b7fbdd20ec46a7b81d38890f1358f09858cf17176739df2f208f7f0e`.
- utility.cpp: `b0dcd2c3c1e44af26d088e3fc9d79c6356675f900c357b07f82371c6a27d9305`.
- maze3D.cpp: `2fa8e3a4a3a9d777032ab54a360583ead5b47ab50995ba101c7fc2177538f79b`.
- RipUp.cpp: `01d611451a42477740b225450a4388af4b758dd3345b90ff2b949af71e65755f`.

## Actual six-export follow-up

Retry39331845906 succeeds at6b19d03. Independent `native_costs` analysis of all
six original exports finds zero raw-minus-live-layer-multiset residual on every
one of139228 edges. All initial/default-final distributions are3565 nonclock
nonsoft scalar1/demands1111,86 clock nonsoft scalar1/demands1111,4 clock nonsoft
scalar2/demands2222 and4 clock soft scalar1/demands1111. In both repair finals,
only the last group's scalar changes to2 while demands remain1111.

The four live soft nets are clk(slot0,db242), clknet_0_clk_regs(slot3,db3065),
delaynet_0_clk(slot29,db3090) and delaynet_3_clk(slot32,db3093). The hypothetical
scalar-minus-layer residual is positive on200 legacy/198 rebuilt edges; actual
residual support is empty. This falsifies that simple explanation for a raw3D
ledger error at these checkpoints. It does not measure graph2d usage or prove
what caused failed negotiation. Main actual report: native_corridor_run_20261019.md.
