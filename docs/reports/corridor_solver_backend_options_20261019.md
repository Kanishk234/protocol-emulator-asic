# Corridor solver backend option — October 19

The actual global selected-cohort model has3,210 nodes,5,526 edges and55,260
variables. Existing bounded CP-SAT returned UNKNOWN, not INFEASIBLE. This report
recommends one formulation/backend experiment, not more seeds/budgets or a claim
that another engine will necessarily solve it. No actual model was solved, no
package installed and no source changed during this investigation.

## Available in the already pinned environment

Project-venv introspection confirms `ortools.__version__ == 9.14.6206`.
`pywraplp.Solver.CreateSolver` plus `SolverVersion` reports:

| Requested backend | Available local implementation |
| --- | --- |
| SCIP | SCIP9.2.2, LP solver SoPlex7.1.3 |
| CBC | Cbc2.10.12 |
| SAT | CP-SAT9.14.6206 |
| GLOP | Glop9.14.6206, continuous LP rather than a binary routing backend |

GLPK/Gurobi were not available; they are unnecessary for this proposal. The local
`HIGHS` identifier returned a PDLP version label, so it is not treated as verified
HiGHS MIP availability. No external service/license or installation is proposed.
Constructing backend objects inspected availability only; no `Solve` call ran.

**Recommended first backend: SCIP through the existing pywraplp wrapper.** The
[official OR-Tools MIP guide](https://developers.google.com/optimization/mip/mip_example)
recommends SCIP for models combining integer and continuous variables. This is
source support for trying the mixed formulation, not evidence of WARP throughput
or superiority over CP-SAT. CBC is available as a separately scoped fallback,
not a request to launch an unbounded backend sweep.

## Equivalent mixed formulation

Keep the identical validated graph, allowed layers, capacity/fixed usage,
per-layer/via demands and net-private exterior component declarations. For each
net n and physical edge e, use binary occupancy `x[n,e]` and **continuous** signed
connectivity flow `f[n,e]` bounded by `−S[n] ≤ f ≤ S[n]`, where S is the number
of non-root required terminals. Retain `−S*x ≤ f ≤ S*x`, node conservation with
root supply S and unit demand at each other required terminal, and exactly the
existing capacity inequality `fixed[e] + sum(demand[n,e]*x[n,e]) ≤ cap[e]`.
Forbidden-planar-layer occupancy stays zero. v2 exterior star transfers are
continuous signed flows with the same ±S bounds and per-net ownership.

Why continuous connectivity flow is sufficient: for any fixed binary occupancy,
conservation implies every required terminal lies in the root's occupied/exterior
connected component—otherwise summing balances over a root-disconnected component
with terminal demand contradicts zero boundary flow. Conversely, any such
connected graph admits an integral root-to-terminal spanning-tree flow with each
edge's absolute flow at most S, so allowing continuous flow adds no feasible
binary occupancy patterns. The physical charge remains binary union occupancy,
never fractional flow or separate sink traffic. Flow splitting in an LP does not
permit fractional physical capacity use while occupancies remain binary.

For the present global graph, the same55,260 variables become27,630 binary
occupancies plus27,630 continuous flows. This changes solver relaxation/search
structure while keeping graph semantics and model-size bounds. It is not a
continuous relaxation of the occupancy decision, and an LP-only answer cannot
substitute for a binary witness. No new objective is needed for the feasibility
question. Optional future length objectives would be a separately described
question, not silently bundled into the first comparison.

## Concrete API and qualification safeguards

Installed wrapper source is
`.venv/lib/python3.12/site-packages/ortools/linear_solver/pywraplp.py`.
Its APIs provide `BoolVar(name)`, `NumVar(lb,ub,name)`, linear `Add` constraints,
`SetTimeLimit`, `SetNumThreads`, `SolverVersion`, model export and result statuses.
`SetSolverSpecificParametersAsString` returns success/failure; never silently
ignore an unsupported memory/limit parameter. Use an explicit allowlisted SCIP
backend, pinned package/version records, one thread, finite wall time and hard
input/model-size limits. Preserve the existing CP answer and exact graph hash.
CP deterministic-time units are not a portable SCIP work budget and must not be
reported as equivalent. Backend-specific memory settings are not an OS-enforced
memory sandbox; use existing bounded process/job controls and state their scope.
No backend-specific parameter string was tested as part of this report.

For native OPTIMAL or FEASIBLE, require every occupancy to be finite and within
a declared numerical tolerance of zero/one before extracting it; reject ambiguous
values. Apply the independent exact-integer union/capacity/BFS witness checker,
then the original-layer capacity allocator and coarse native-pin connectivity
checker. Their exact resource checks, rather than floating flow values, decide
whether a constructive witness is usable. Wrapper `VerifySolution(tolerance,...)`
is available after solving as an additional floating audit, not a replacement
for those independent checks.

Without a checked incumbent, time/limit stop or NOT_SOLVED is UNKNOWN. INFEASIBLE
is solver-reported infeasibility for the declared graph, without an independent
rational certificate; preserve that distinction. ABNORMAL/MODEL_INVALID or an
unexpected UNBOUNDED result for this bounded zero-objective formulation is an
error, not evidence of infeasibility. No status authenticates native inputs or
physical routing. The existing112 fixed-other overflow remains explicitly
separate from any successful selected-cohort witness.

Before applying SCIP to the actual graph, add independent tiny edge-subset
comparisons spanning v1/v2, shared multisink trunks, signed direction, fixed use,
NDR layer demand, forbidden layers/vias and exterior isolation; include feasible
and infeasible fixtures. Verify the known5>4 southern cut remains rejected and
that constructive incumbents pass the existing exact checker. Test unavailable
backend/version mismatch, failed parameter configuration, limit/no-incumbent
status, numerical ambiguity and modified model/witness rejection. Retain all
existing CP-SAT tests and defaults. Then one bounded same-graph SCIP attempt is
a discriminating experiment; UNKNOWN remains inconclusive and does not authorize
another budget/seed sweep.
