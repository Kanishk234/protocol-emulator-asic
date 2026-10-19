# Independent abstract corridor oracle review

Read-only review of `tools/autonomy/corridor_solver.py`, its qualification
tests, `requirements-routing.txt` and the separate hosted qualification workflow.
**No blocking formulation, witness-validation or scope issue found.** This is
an oracle for a declared abstract graph, not a WARP routing result.

## Model and witness checks

Each net/undirected edge has one occupancy Boolean and one signed integer flow.
For a net with k non-root terminals, the root supplies k units and every other
terminal consumes one. Flow conservation at all other nodes, combined with
`-k*x <= flow <= k*x`, requires connectivity through occupied edges. An
undirected edge has one signed flow, so direction does not create separate
physical capacity resources.

Resource use charges each net's declared edge demand once through its occupancy
Boolean. A shared trunk serving several terminals therefore consumes one
net's demand, not one demand per sink. Separate nets still compete for that
edge, together with the explicitly declared fixed background usage.

The separate witness validator uses graph reachability and direct capacity
summation rather than inspecting CP-SAT flow values. It checks every terminal,
forbidden planar layers and every occupied edge. Disconnected irrelevant
occupancy may be removed before validation; doing so only decreases demand
and preserves the root-connected terminal component. No minimum-wirelength
or optimal topology claim follows.

## Explicit assumptions and bounds

Layer-specific track demand, allowed planar layers, preferred/nonpreferred
motion, and via costs/capacities are explicit validated contracts. Via adjacency
uses the declared layer order. An unlimited coarse via is clearly distinguished
from a finite-capacity physical-via model. Boundary terminals are fixed required
nodes with no implicit outside connectivity.

Inputs, graph size, variable count and solver time are bounded. The dependency
is pinned to OR-Tools `9.14.6206`. UNKNOWN remains inconclusive and carries no
witness. Solver memory configuration is expressly not an OS-enforced memory
sandbox. INFEASIBLE is a solver conclusion about the declared model, without
an independently certified proof or an inference of WARP physical impossibility.

Every result explicitly retains `native_inputs_authenticated=false`,
`physical_acceptance=false`, `timing_acceptance=false`, and declared omissions
including DRC, track assignment, timing and antenna. A recorded source digest
does not authenticate a native extraction. No source-to-native adapter or
physical feasibility claim is introduced by this review.

## Qualification evidence and limits

Independent inspection of the test oracle confirms it exhaustively enumerates
edge subsets and connected terminal components, rather than duplicating the
signed-flow formulation. Its 27 two-net capacity combinations provide a small
independent cross-check. Further fixtures exercise multi-terminal shared trunks,
separate-net contention, fixed demand, explicit vias, planar restrictions,
disconnected terminals, malformed contracts and bounded UNKNOWN.

Independent strict inspection of `build/corridor111_local.xml` confirms **138
executed tests, no skips/errors/failures**, comprising **117 corridor tests**
and the separate repair-evidence tests. This is local Python qualification;
no local EDA is performed. The new hosted workflow is prepared separately;
this review does not claim a hosted result before execution.

The finite abstract graph and fixed-background contracts are essential limits.
A feasible witness cannot certify detailed routing, and an infeasible selected
corridor cannot prove the complete chip is unroutable. Native input extraction,
all-terminal selection, raw capacities/NDR accounting and frozen-background
authentication remain separate work before applying the oracle to WARP.

No solver edits, dispatch, commits, phase checkboxes or acceptance-rule changes
were made during this review.
