# Resumable cut-guided routing development — October20

The autonomous diagnostic now retains and reuses proven bottlenecks. It selects
additional nets jointly, validates every proposal, records each counterexample,
and stops at declared limits. No native route improvement or physical/timing
acceptance has resulted yet; compact native121 remains failed routing.

## Retained implementation

- 07573aa: exact cut-cohort selector and native adapter. Original STEP multiset
release, unit/all-layer eligibility, candidate pin crossing demand and fixed
background overflow remain explicit. Nonnegative resource offsets need no
activation binary. Nets releasing no useful cut resource are safely pruned.
- ed3d11c: exact chain/dead-end reduction. Optional synthetic coordinates describe
computational topology, not native geometry. Parallel chains aggregate unit
capacity, then each selected net is assigned an original path with spare capacity.
Every witness expands and passes original resource/connectivity validation before
original-layer/native-pin checks.
- 98433f0/a468bd7: bounded refinement, exclusive stage outputs, authenticated
entry, compressed resume constraints and source hashes. Decode is capped at2MB,
encoded input50k, imported constraints32, known cuts64/10k resources, rounds8 in
the library and4 in the hosted entry. Every seed model and cut is rebuilt;
prior status booleans supply no authority. Existing outputs are never overwritten.

The fixed graph experiment keeps its100k-variable cap. Broader joint experiments
explicitly permit150k inside the existing500k hard limit because coordinated
cohorts exceed100k (observed nine-net originals100782/101052variables;
ten-net originals approximately112k). Per-solve30s/1024MB/one worker limits stay
unchanged. Raising the model census does not increase native routing capacity,
search time, clock target or physical acceptance.

## Validation and review scope

Local full autonomy:915executedPASS/0skip at the algorithm source through49da841;
strict XMLbuild/autonomy112_resumable_final.xml. Planner/native adapter53tests,
including27 independent exhaustive original-usage subset comparisons. Reducer126
cases include original/reduced exhaustive feasibility, parallel path assignment,
via/cost restrictions and tamper rejection. Refinement17tests and joint entry16
tests cover round/time/model bounds, authority/graph checks, partial-stage
preservation, resume identity/schema/decompression and seed recertification.

Dedicated hosted qualification39456418346 at49da841 SUCCESS; downloaded strict
XML518executedPASS/0skip and exact source SHA/package pins checked. It does not
include the joint-entry fixtures requiring the separate manual campaign's
PyYAML installation. Existing fixed hosted39371954205 atbe895de has326executed
PASS and both actual SCIP graphs INFEASIBLE, exact graph/LP hashes checked.

After all specialist agents hit usage limits, the coordinator implemented and
reviewed the new selector/reducer/refinement. The new mathematical tests use
independent subset enumeration; this is not a second-agent source review of
those modules. Earlier backend/campaign/cut source and actual outcomes retain
independent reviews in native_solver_campaign_review_20261019.md.

The lightweight autonomy job exposed BUG106: fixture mincut discovery required
optional OR-Tools.794dafd replaces that discovery with an arithmetic cut fixture.
With OR-Tools unavailable, full local base checks676PASS/239expected optional
skips. Real solver tests execute in dedicated qualification. Corrected hosted
base checks remain pending at this report entry.

## Actual accumulated outcomes

The first qualified selector reduced4384draft variables/1109constraints to806/
350, retained578of3650candidates and selected three extra routes satisfying all
seven known cuts. The admitted eight-net routing graph89248variables still had
a fresh5>2 cut, so no routing MIP ran.

With that counterexample included, at most three additions is SCIP INFEASIBLE
for the known cut problem. Four-extra proposals also expose fresh6>3 and2>1
cuts; the ten-cut selection problem with at most four additions reports
INFEASIBLE. Five-extra proposals produce further6>3 and5>2 deficits. These are
conditional known-cut selection results, not whole-chip impossibility proofs.

The retained two-round refiner starts with13cuts and preserves new7>3 and9>4
counterexamples (build/corridor112_refinement_qualified). The fully authenticated
joint entry then imports15cuts, rechecks all native controls, and terminates
selection_INFEASIBLE for at most five extra nets after one round. Artifacts:
build/native_joint112_local_resumed. No route solver or guide installation is
invoked for these cut-rejected proposals. A six-extra two-round follow-up preserves a fresh7>2 cut, then reports
selection_INFEASIBLE with16knowncuts (build/native_joint112_six_extra). A seven-extra
two-round follow-up completes selection_INFEASIBLE with16knowncuts. Direct cardinality minimization permitting up to32extras finds an optimal eight-extra selection [1074,1362,1418,2802,2850,3209,3227,3228]; original146120/reduced137124variables, then a fresh8>4cut rejects it before routingMIP. These results concern the stronger zero-selected-overflow target. A separate incremental objective produces an independently checked uninstalled121→118proposal; see congestion_proposal_20261020.md.

## Hosted resume approval

Prepared data-only manifest:15constraints,19016encoded bytes,
SHA2562a0de2bbeb63b9b18edf0ed38f4046ffab59a0c3681ae92498459c9055462aee.
It contains checkpoint hashes, cohort IDs and partition node IDs, not raw native
logs/bitstreams. Automatic approval review rejected dispatching it to the existing
Kanishk234/protocol-emulator-asic GitHub workflow because specific derived-data/
destination approval was required. No manifest was transmitted. Explicit approval
is pending; local resumed work and read-only CI checks continue. Do not bypass
this rejection by uploading the same data through another route.
