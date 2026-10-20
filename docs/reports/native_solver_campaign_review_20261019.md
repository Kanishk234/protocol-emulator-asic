# Independent native solver campaign review — October 19

Read-only review of `tools/autonomy/native_solver_campaign.py` and its focused
fixtures. The reviewer authored the SCIP backend; root independently reviewed
that backend. This report reviews the separate root-authored campaign rather
than self-certifying the backend. No actual model solve, EDA, source/test edit
or dispatch was performed here.

## Input-binding finding

Initial review found one narrow provenance gap: the segment file was hashed with
`sp.read_bytes()` but then independently reopened with `sp.read_text()` for the
extractor. A change between reads could make the consumed text differ from the
verified checkpoint. Unlike raw/terminal buffers, the hash was not bound to the
exact segment bytes parsed. Requested fix: read segment bytes once, hash that
buffer, and decode the same buffer for extraction. Correction/retest status is
recorded below. No larger provenance framework or acceptance change is needed.

## Controls and bounds reviewed

Backend choice is restricted to cp_sat/scip before any audit or execution.
The campaign reruns the portable native evidence audit with **all three** flags
(candidate, native corridor, native terminals), explicit native run/attempt/full
source and caller-supplied API identity. It does not accept stored collector
booleans alone. Exact initial raw, terminal and segment checkpoint digests are
required before constructing either model. Full native controls/ledger/terminal
parsing and source-patch bindings remain delegated to the strict audited adapter.

Exactly two named models are constructed: fixed southern cohort32/120/123/124/387
in window[8,0,17,9], and the same cohort's global unit/all-layer coarse relaxation.
No input permits a seed, budget, backend or cohort sweep. Both backend calls use
30seconds,1024MB solver limit and100,000 variable cap. Existing backends enforce
one worker; CP-SAT additionally retains its default deterministic-time limit,
while SCIP has no equivalent deterministic-work-unit claim.

The output directory must be new and individual files use exclusive creation.
Input audit and model files are retained before solver calls. Backend exceptions
and invalid result identity/status/scope leave `diagnostic_completed=false`, a
recorded error and any prior artifacts; they are rethrown rather than normalized
to UNKNOWN. A genuine backend UNKNOWN is retained as inconclusive diagnostic
completion. Failures before authenticated model admission deliberately prevent
output/model/solver execution; job logs remain the evidence for those failures.

Each backend result must have the exact canonical graph hash, an allowed status
and false native-input/physical/timing authentication flags. Local results retain
an independent x16 capacity cut; a claimed FEASIBLE local result contradicting
that certificate aborts. A global FEASIBLE witness must additionally pass exact
original-layer reconstruction/allocation and coarse native-pin connectivity;
only then is proposed raw overflow summarized, with native_route_installed=false.
Other fixed background overflow remains part of the original-layer checker's
explicit metric, not hidden by the aggregate model.

Campaign source hash, native result hash and explicit native identity are
recorded. Solver/model identities and bounds are retained in individual outputs.
No code installs routes/guides, dispatches EDA or promotes a result. FEASIBLE,
INFEASIBLE and UNKNOWN scopes remain the two supplied declared graphs. The
selected-cohort relaxation is not zero-overflow chip signoff.

## Focused validation

In the project venv:

```sh
PYTHONPATH=tools:test_internal pytest -q tools/autonomy/tests/test_native_solver_campaign.py
```

Initial independent result: **11 passed in0.13s**, no skips. Fixtures enforce
all-audit-before-solve ordering, exact checkpoint hashes, new output protection,
error-versus-UNKNOWN preservation, backend enum, result graph/status/physical
scope checks and fixed call limits. They mock actual native audits/models/solver
calls and do not substitute for the first authenticated hosted campaign result.

## Corrected final disposition and workflow review

The single input-binding finding is fixed: raw, terminal and segment bytes are
read once; the segment buffer itself is hashed then decoded for extraction.
A new regression rejects any second text read of the segment path and checks
the extractor receives the hashed buffer. Independently reran the focused suite:
**12 passed in0.17s**, no skips. No source blocker remains for a bounded campaign.

Reviewed `.github/workflows/native_solver_campaign.yaml`: its solve job runs only
on explicit efpga workflow_dispatch; the push path is registration-only. Inputs
are restricted to explicit run/full revision/attempt and two backend enum values,
then shell-regex checked before interpolation into quoted gh/Git commands.
Permissions are read-only actions/contents. The workflow fetches API identity,
exact source Git object and the specifically named native artifact. Project venv
installation pins the solver requirement; fixture XML, package list and current
tool revision are retained. The job is bounded12minutes; source campaign bounds
each of exactly two solves30seconds/1024MB/100,000variables. Concurrency does not
cancel an in-progress campaign. Artifact upload runs even on failure. No job
installs native routes, dispatches EDA or promotes a chip.

Recommended addition before hosted execution: include the quick backend-specific
`test_corridor_mip.py` fixtures in the hosted check step, so the actual installed
SCIP library is exercised on tiny independently checked models before the real
graph. The backend's version/availability/configuration guards already fail
closed; this recommendation is qualification coverage, not an observed source
correctness blocker. Hosted result inspection remains separate from this review.

Reviewed final SHA256 at this disposition:

- Campaign: `fa8f7d90188e3f993906ee9620a87de55bde898fcde353cca6363ae12785e647`.
- Tests: `68cf668da8e7bf0f4eab6be0a31e9ed0e670760ccd20eb9c003fc3948774d354`.
- Workflow: `f19137a13726c308601f99ab7acbc7990e32082ebdaf92f774bab3fe28c7d73e`.

This final disposition covers the same-buffer campaign plus workflow above.
Later partition discovery/certificate additions and actual result claims require
their own follow-up review; no such additions are implicitly qualified here.

## Follow-up partition checker, discovery and actual result audit

Reviewed the added explicit-partition certificate and bounded mincut-discovery
helper. Found a concrete generic-checker bug: a partition crossing a finite via
could use planar minimum demand2 even when declared via demand was1, falsely
certifying a feasible one-via graph. Independently reproduced a valid exact
witness and the incorrect certificate before correction. Root fixed the checker
conservatively by refusing **all via-crossing partitions**; a new negative fixture
first validates the feasible witness then requires refusal. Independently
confirmed the fix and reran **21 tests PASS in0.18s**, no skips. No remaining
concrete false-certificate blocker found in the reviewed restricted checker.

`discover_partition_certificate` is limited to finite, nonnegative-residual,
single-layer, unit-demand v1 graphs and at most128 root/sink terminal pairs.
Maxflow proposes a partition only; `certify_partition` independently recomputes
its complete cut capacity and required-net lower bound. A bad maxflow status
raises, and no discovered deficit returns None as inconclusive. Pair-cut discovery
is not complete. Actual global models are single-layer, so the via bug never
invalidated their existing arithmetic certificates.

Independently recomputed the stored actual explicit partitions:

- Five-net global: demand5>capacity3; sole positive crossing `H_17_1`.
- Six-net (+70): demand5>capacity2; positive crossings `H_18_1`,`V_15_68`.
- Seven-net (+1162): demand6>capacity2; positive crossings `H_18_1`,`V_16_70`.

Each recomputed certificate equals its stored artifact. For the seven-net case,
the file is `build/corridor112_expanded1162/discovered-cut-certificate.json`;
no MIP solve is asserted. Actual five-net global SCIP reports INFEASIBLE on exact
canonical graph`9fc8041f91eef1fab1b20f83c3ddda43177d246167e97c008b3b0bf48cdf98cc`,
identical to the earlier CP-SAT UNKNOWN graph. Actual local SCIP is INFEASIBLE.
The graph-only cuts, rather than solver confidence, supply independent restricted
infeasibility evidence. No new model solve was run by this review. Existing
physical/native flags remain false and the graph/frozen-cohort scope remains.

Final reviewed partition-checker SHA256:
`4eadc55fab24d23a2d63ae21fbd870f10092b913412b449f54c7030820edb281`;
its tests:
`cc0738e269ea87d5669fcea16f138bb7a2b97bdd76f8c0258e9ea77584d6da1a`.

The workflow now includes both original CP-SAT and new SCIP focused fixtures
before hosted actual models, resolving the earlier qualification recommendation.
Updated workflow SHA256:
`9e8bc1a8a191e3ceb6ce5d725d40597649be8ca645e97d45ee2dcfaa0131445f`.
Campaign source/tests remain unchanged at the hashes above; independently reran
**12 campaign tests PASS in0.21s**. No blocker remains for committing/reproducing
this reviewed bounded campaign. Any subsequent integration of automatic global
cut retention should bind its certificate graph hash and preserve inconclusive
None/status semantics; it is not implicitly covered before that code exists.

## Automatic global-cut retention delta reviewed — October 20

Reviewed the subsequent small integration: after the graph-bound global backend
result, bounded partition discovery independently certifies the same model and
always retains `global-cut.json`, including explicit JSON null when inconclusive.
The separate summary flag reflects certificate presence; it does not overwrite
a backend UNKNOWN with INFEASIBLE or claim physical/native acceptance. A FEASIBLE
backend contradiction aborts before original-layer allocation, while preserving
prior artifacts and a failed summary. The reviewed discovery helper returns a
non-null object only for a checked strict deficit. No concrete blocker found.

Independently reran campaign and cut suites: **35 passed in0.17s**, no skips
(14campaign +21cut). Added fixtures verify retention with UNKNOWN and rejection
of a contradictory FEASIBLE result. This review did not rerun the real graph or
inspect newly completed hosted artifacts; those actual results require their own
artifact/source-bound audit.

Reviewed delta hashes: campaign
`16153342149da203d1cdf293d966087d671161abf72829fad8c82d1c689cc6fb`;
tests `1877ef17b5fedc53842f209216023c9da623215e122bd9e9ef71b7b28c3b4b62`.

## Downloaded hosted qualification independently checked — October 20

Reviewed downloaded campaign39371954205 under
`build/solver112_hosted_campaign` and backend qualification39371931884 under
`build/solver112_hosted_backends`. Both retained revision files name exact
`be895deef40218b49b3d3e69e2627beb7792695e`. Independently matched the campaign
source SHA to bytes from that Git object; both package inventories include
ortools9.14.6206. Strict testcase enumeration finds326 executed campaign-fixture
passes and301 backend-fixture passes, with zero failure/error/skipped cases in
either XML. No new solve or native EDA was executed for this audit.

The hosted completed diagnostic retains native39367564921/attempt1/source8782e28
and original resultSHA8ac9ecbb…f73674, exact cohort/window and false native-input,
physical and timing acceptance flags. Its local/global SCIP results are both
INFEASIBLE. Recomputed canonical model graph hashes agree with their solution
records, and both graph **and LP-model** hashes equal the corresponding earlier
local campaign:

- Local graph `7f49b0ddb0ea3976cdf4c7f4191f4099f1fd8a60da1a1037de251c4dfb73b8d0`;
  LP model `8b7693aa371738f7e3660474dde5350e5a804b81c6426ff2a98fd2ecb8d8c08a`.
- Global graph `9fc8041f91eef1fab1b20f83c3ddda43177d246167e97c008b3b0bf48cdf98cc`;
  LP model `1e19d5d81375e269f1a0d7e3940bee9dfd65befff1c5e1ee433e0914e4e0f27f`.

The separate certificate in `build/solver112_hosted_global_cut.json` was
independently recomputed against the downloaded global graph: exact equality,
four required unit-net crossings versus residual capacity1, with sole positive
crossing H_18_1. This4>1 partition is another valid obstruction of the same graph,
not a contradictory change to the earlier5>3 partition. Both are independently
checked restricted-cohort proofs; neither proves whole-chip impossibility.

This hosted source predates automatic global-cut retention: its summary has only
the local certificate flag. Do not attribute a hosted global-cut.json or newer
integration tests to that run. The downloaded-graph global certificate is a
separate subsequent read-only audit, and later source additions retain their own
qualification obligations. No native route was installed or accepted.
