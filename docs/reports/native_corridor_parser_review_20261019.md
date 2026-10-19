# Independent native corridor parser review — 2026-10-19

Scope: source review of `tools/autonomy/native_corridor.py` and its independent
hand-computed fixtures against observer patch
`b7493c2fc4e4c7074363550fd0a059064ee739a4fc593f3eaf14081167a5ff65`.
No native routing, build, dispatch or parser/source modification was performed.
This is accounting-parser qualification, not WARP checkpoint authentication.

## Result

Raw edge and weighted accounting mechanisms pass independent source review.
One concrete source-consistency finding was sent to the author and root before
closing review: a native soft-NDR net must export per-layer demands of one, but
the initially reviewed parser accepted a contradictory soft flag with demand two
and a matching raw-usage ledger. Correction/retest status is recorded below.

## Checks that pass

The parser enumerates every declared layer, both H and V arrays, all valid edge
coordinates, and native emission order. H includes its real last row; V includes
its real last column. It does not substitute a preferred-layer subset or the
encoded OpenDB reporting grid. Missing, duplicate, out-of-order, out-of-bounds
and extra rows cannot silently disappear from the edge census. All four resource
fields are canonical integer values constrained to native uint16 ranges.

The schema/header/index/via declarations are exact. Slots are contiguous with
explicit empty slots, database IDs and raw names are unique, and native Booleans
are constrained to zero/one. Demands are complete and ordered per layer. Pin
indices and coordinates/layers are bounded; driver indices and planar layer
intervals are checked. Tree counts, node references, route/grid sizes, step
indices and footer totals are checked. STEP vectors must be continuous and
unit Manhattan moves; diagonal, stationary and nonadjacent via steps fail.
Via steps require zero planar demand. Planar STEP weight must equal the live
per-layer demand, rather than the scalar cost or an assumed unit weight.

The parser records planar step occurrences in a per-net Counter and multiplies
**every occurrence** by its layer demand. It does not merge repeated tree steps
or net-edge traversals into a Boolean union. It then compares exact integer
summed contributions with usage on **every** raw edge, including edges with no
exported contribution. Positive unexplained usage and excess contributions both
make the ledger gate fail. No residual is invented as background occupancy and
no uint16 modulo reconciliation is accepted. Capacity overflow remains observed
data and does not invalidate an otherwise complete accounting export.

The separate union comparison adds one layer demand per distinct net-edge and
reports disagreement with the multiset total. Duplicate traversal and zero-demand
observations prevent `solver_union_accounting_compatible`. Different nets sharing
an edge remain separate contributors. Native input authentication, physical
acceptance and timing acceptance explicitly remain false; successful accounting
cannot authenticate the original121 checkpoint, complete physical terminals,
layer-name joins, via legality or a solver graph.

Focused validation executed in the project venv:
`PYTHONPATH=tools pytest -q tools/autonomy/tests/test_native_corridor.py`:
**66 passed** at initial review. The tests include hand-computed demand-two
usage, repeated traversal within/between tree routes, separate-net sharing,
all-boundary mismatch, malformed fields/counts/steps, zero-demand incompatibility,
uint16 wrap mismatch and nonzero CLI status on failed reconciliation.

## Finding: soft-NDR consistency

Pinned `FastRoute.cpp:2167` implements `FrNet::getLayerEdgeCost(layer)` as the
NDR vector value only when the vector exists **and** `!is_soft_ndr_`; otherwise
it returns one. Therefore `NET.soft_ndr=1` with any nonunit DEMAND is impossible
for this exporter/source, even if the fabricated raw usage matches that weight.
An independent reproduction changed the existing demand-two fixture's soft flag
from zero to one; the initially reviewed parser returned `model_gate=PASS` and
`usage_ledger_reconciled=True`. The arithmetic itself remains correct, but this
contradictory native-state declaration should be rejected during strict parsing.
Requested fix: require all demands equal one when the native soft flag is true,
and add a negative fixture. No scalar==one requirement is justified: scalar
versus per-layer soft-NDR divergence is specifically an observation of interest.

Initial parser SHA256:
`b0c221384349ff9de2363c565337bc3eeddd61b51c18fb06831f66c2f0aff89a`;
initial test SHA256:
`bf2364a77a8b5c69c941e1fb075990fc1ba6332cf40d262eac8025404705c799`.

## Remaining scope gates

The parser alone cannot establish actual database/net identity or explain a
missing native census: the completion footer is an internal census, not an
independent OpenDB join. Authentication of the binary/source/input121 control,
full net-name/ID and layer joins, disabled/enabled observer equivalence, retained
raw artifact hashes and successful native usage reconciliation belong to the
qualification collector. Current-cost STEP reconstruction is allowed to fail
against historical usage; that failure must remain a false model gate. The
module does not establish terminal connectivity or physical via/cut feasibility,
and its union-compatibility flag only addresses accounting, not solver readiness.

## Final correction and independent retest

The author corrected the finding: after the complete DEMAND census, a native
soft-NDR flag now requires unit demand on **every** layer, including unused
layers. Scalar cost remains independent. Three regressions cover contradictory
matching-usage data, a contradictory unused layer, and valid soft-NDR with
scalar three and unit per-layer demand. Independently inspected this condition
and reran the focused suite in the project venv: **69 passed in 0.28 s**.
No concrete parser blocker remains for bounded native accounting qualification.
All native authentication, physical and timing scope gates above remain open.

Final parser SHA256:
`360056d71672329d6ac309c138bdfed5f338edc0d6255208e12efc94f19d4557`;
final test SHA256:
`d06c7c3b3b374d07614cf6567553e166a2c98144168ff98ec06d8fc8f3ee6331`.
