# Autonomous development in an active Codex session

This is the operating procedure for a coordinator and specialist agents working
on WARP in one active session. GitHub executes substantial tests and heavy EDA;
the session chooses useful work, investigates failures, reviews evidence and
retains improvements. A workflow is an executor, not an autonomous engineering
judgment. Neither this document nor a workflow makes a closed chat run forever.
Resume with the handoff below when the session ends.

The executable supervisor is a separate bounded test campaign, not the agent
team or a general background AI. It dispatches only allowlisted phase-stress,
active-cancellation, C-host and compiler-seed checks against one pinned source
revision; persistent state and independent hash/evidence checks support restart
and review. The team uses the backlog to choose engineering work. Run the
supervisor from the project root:

```sh
source .venv/bin/activate
PYTHONPATH=tools python -m autonomy.supervisor --revision <40sha>
PYTHONPATH=tools python -m autonomy.supervisor --revision <40sha> --launch --watch-hours 4
```

The default state is `build/autonomy/state.json`, with `STATUS.md`, `evidence/`
and `events.jsonl` alongside it. Creating `build/autonomy/STOP` stops new
dispatches without cancelling existing jobs. Inspect status and current run
IDs before restarting or launching another campaign. No general AI background
thinking is configured by this command.

`.github/workflows/autonomy.yaml` tests the supervisor and performs one
read-only observation for its exact `efpga` revision. Its token can read
contents and Actions; it does not launch experiments. The retained XML,
state/dashboard and evidence artifacts support review for 30 days. The workflow
is an observer and validation check, not a model brain or continuous agent.

## October23 R1 handoff

Fresh reduced-radix profile preserves all six retained compiler cases and primary UART+SPI. Hosted loaded generated RTL and mixed mapped-LUT primary tests pass, with independent source/image/tool audits. Native preflight39996455894 at46682a2passes both fixed widths,210signal pins/438latches and exact native constant accounting. See reports/r1_physical_preflight_20261023.md and backlog R1-MODELS.

Representative first-column LUT run40009049924 now completes PDN/placement/GRT at both fixed widths with zero final overflow and zero final PG violations. BUG124 checker rejected auxiliary boundary patches despite full-height stripes; corrected retained-result/ODB replay and49local tests pass, hosted replay40009616432 at6b290889 attempt1SUCCESS both widths, with authenticated source/result/geometry and exact ODB-hash replay. Next qualify other tile types, column phases and shared interfaces before full-grid hardening; no new topology/seed/budget sweep. Native pin/core success is not routing/timing/whole-chip acceptance. Keep the narrowed core's limited reserve explicit; audit column power phase and other tile-type interfaces. Secondary UART+I2C remains a600-second compiler routing timeout, so its aggregate model workflow stays red. Freeze/replacement gates and G1 protection remain unchanged. All three initial graph profiles are already used.

## Current priority and protected results

Phase 5 is complete as of October 19: the fresh GDS/gate-test run39280550500,
applicable formal/fabric runs and current core checks passed independent source
applicability review. See `phases/PHASE5_EVIDENCE_DOCS.md` for exact evidence.
Phase 6 begins with a read-only rules check; final submission remains open.
A new compact diagnostic does not itself tick a submission box.

Keep two distinct tracks:

* **Frozen G1:** the submission fallback, with recorded GDS/precheck/gl_test
  evidence 36383587262 and 36451108163. Preserve committed architecture,
  bitstream ABI, working examples and D-023 simulation scope. Functional and
  compiler improvements can proceed without replacing the chip.
* **Compact successor:** experimental, not accepted. Best fanout-clean native
  route is still **133 overflow**, paired run 38168159774 using producer
  38167697696. This is the comparison control, not a passing routed chip.
  Preserve its authenticated inputs and exact routing/clock policy. Never
  combine another layout's geometry pass with its electrical or timing pass.

October15 follow-up: keep that original50-budget133 reference intact. Paired
38820879445 also establishes a **121-overflow** point at native15 iterations
on the same physical views/resources. It remains failed routing, with mixed
per-layer changes and no downstream signoff. Treat routing policy as part of
checkpoint identity; never compare a new physical change against133 while
silently applying the15 policy. Replay the explicit121 checkpoint with exact
segment hashes before using its grid or calling it a new comparison control.

The source of truth for outcomes remains reports, CLAIMS, BUGS and DECISIONS.
`../autonomy/backlog.json` is an actionable index, not stronger evidence.

## Team and shared workspace

The coordinator owns the work queue, acceptance decisions, integration, CI
dispatch and session handoff. With the currently available four agent slots,
use at most three specialists alongside the coordinator:

| Role | Concrete output | Ownership boundary |
|---|---|---|
| Evidence reviewer | Reconcile exact source SHA, run attempt, XML/results, artifact hashes and claim scope; challenge proposed acceptance | Read-only unless assigned specific evidence documents |
| Experiment engineer | One bounded implementation or diagnostic with a stated hypothesis and covering checks | Explicit files; no generated or upstream in-place edits |
| Research/verification specialist | Primary-source compatibility notes, independent oracle or adversarial validation | Read-only research or explicitly assigned tests; keep reference models independent from RTL |

Assign disjoint files before agents edit. Ask agents to report findings,
reproducible commands, failures and uncertainties, rather than merely saying
"done". Send discoveries across roles promptly. The coordinator alone stages
and integrates shared changes. Release/reuse finished slots for the next
bottleneck; do not spawn agents just to keep them busy. A specialist reviewing
reference-model semantics must not inspect the checked RTL if that would break
the project's independence rule.

If a specialist becomes unavailable or reaches its usage limit, preserve its
working-tree changes and let the coordinator take over review and verification.
Do not commit partially reviewed edits or repeatedly restart an unavailable
agent. Record which work was independently validated and which remains open.

## Work cycle

1. **Observe.** Read the latest WORKLOG, phase gate, architecture and active run
   state. Inspect dirty files and existing queued/running workflows before
   dispatching anything. Record which baseline and checks an idea affects.
2. **Form a hypothesis.** State the measured symptom, proposed cause,
   prediction, one changed variable, expected cost, rejection condition and
   smallest discriminating check. Consult previous rejected hypotheses first.
   A new seed is not new evidence for a previously rejected physical policy.
3. **Investigate independently.** Parallelize evidence review, source research
   and bounded implementation. Resolve missing artifacts and adapter mistakes
   before spending another long EDA run.
4. **Validate cheaply.** Use project-venv focused unit/parser/syntax checks and
   provenance preflights locally. Run meaningful tests for failure handling;
   do not write tests that only restate trivial implementation. Heavy EDA
   stays hosted. Use existing workflows before inventing another pipeline.
5. **Run the experiment.** Dispatch the exact committed `efpga` SHA, explicit
   inputs and one policy change. Keep immutable producer/control hashes, image
   digest, tool versions, constraints and expected result schema. Use a paired
   control where physical comparisons require it. Check for duplicate runs.
6. **Review the actual result.** A green collector means evidence collection
   succeeded. Inspect the native return codes, complete expected test cases,
   XML failures/errors/skips, compiled parameter reports and guard results.
   Missing evidence is unknown, never success. Independent review should try
   to disprove an apparent win before it is retained.
7. **Retain or reject.** Keep independently useful code only when its checks
   pass. Keep a physical candidate as a control improvement only if paired
   overflow improves 133 with all original guards retained. Nonzero overflow
   still blocks physical acceptance. Record rejects and their causal scope;
   archive reproducible provenance, not raw CI output in Git.
8. **Continue.** Update backlog and reports; choose the next actionable item.
   While hosted jobs run, make independent progress on phase-5 evidence or
   frozen-G1 tools. End with a WORKLOG entry and precise continuation state.

## Failure classes and stopping rules

| Classification | Meaning | Next action |
|---|---|---|
| Infrastructure | Runner, network, image pull, expired artifact | Diagnose once; regenerate from authenticated durable source or retry boundedly; no design rejection |
| Harness/provenance | Parser, wrong parameters, stale image, omitted source, unmatched policy | Fail closed, log BUG and covering regression; retry only after the specific fix |
| Design/physical rejection | Actual guard, protocol or native routing failure on valid inputs | Reject that hypothesis/configuration and preserve the control |
| Incomplete scope | Positive subset but missing modes, corners, endpoints or cases | Retain diagnosis; list missing obligations; no promotion |
| Accepted improvement | Predetermined checks passed with authenticated evidence | Retain within the measured scope and update claims only to that scope |

Do not repeat a rejected configuration without new measurements or a materially
different hypothesis. Update its rejection record with the distinguishing
evidence before dispatch. A setup fix does not count as a chip improvement.
Stop a line of work when its acceptance gate fails; switch to independent
phase-5 work rather than weaken constraints. If a required phase gate cannot
pass, report the blocker and a concrete fix/fallback; do not tick it.

Compact physical experiments retain unchanged layer capacities, margins,
20 ns target, physical interface, row power phase and all three original PVT
electrical/setup/hold guards, including the additional 0.1 ns hold guard.
Only zero native global overflow justifies advancing a candidate to detailed
routing, extraction and complete same-build timing/geometry qualification.
Conditional configured timing, estimated shell timing, real loaded RTL,
native mapped behavior and SDF-annotated behavior remain separate evidence.

## Research and provenance

Research when a measured uncertainty can change the next decision. Prefer
upstream source, official documentation, author papers and the actual prior-art
repositories. Record URL, retrieval date, immutable commit/release or paper
version, license and relevant exact source/API hash. Current documentation can
describe features missing from WARP's pinned image: inspect its installed API
and source before proposing an invocation. Separate direct observations from
inferences, and published results from predictions for WARP. Never silently
upgrade FABulous/OpenROAD/PDK or edit pinned upstream in place.

For each retained run record repository/source SHA, workflow and run attempt,
input producer, result SHA256, artifact identities, tool/container/PDK pins,
policy/SDC hashes, test names/counts/parameters and observed outcome. GitHub
artifacts expire: preserve small manifests and approved source archive hashes
with a documented regeneration path; do not invent missing historical views.
Record actual full hashes from artifacts, never expand abbreviated report
hashes by guessing. No raw logs, databases, waves or bitstreams go into Git.

## Recheck downloaded architecture evidence

The portable auditor reuses the hosted compiler evidence checks against the
explicit project revision and pinned tile-library Git objects. It does not
trust current working-tree pin specifications, launch workflows or run EDA.
Both repositories must contain the named objects; missing objects reject the
audit rather than substitute newer files.

```sh
source .venv/bin/activate
PYTHONPATH=tools python -m autonomy.architecture_evidence \
  build/arch109/current-architecture-comparison-38852379083 \
  --revision ba0cb76ac717b8656c7d081fc453ca9222b6e8d5 \
  --run-id 38852379083 --attempt 1
```

Supply the actual downloaded artifact directory and authenticated run identity
for another campaign. The read-only supervisor adapter accepts the same
explicit identity. Its four dispatch campaigns are unchanged: architecture
compilation is not added to automatic launches because that workflow lacks
the expected-SHA input guard. Tool hashes here are retained identities, not a
fresh binary execution or a physical timing qualification.

## Authorization and durable handoff

The user authorized agent delegation, commits and pushes **for the October 15,
2026 session, continued October 16**. This overrides the Git restriction for that session only;
it is not permission for future sessions or autonomous scheduled writes.
Normal repository rules, protected architecture/spec decisions and phase gates
still apply. Commit by file group. Before pushing while hardening is active,
inspect `git log origin/efpga..efpga -- src info.yaml arch macro` and the actual
workflow concurrency policy. Do not cancel useful hardening accidentally.

A session handoff records dirty files, retained/rejected changes, exact running
run IDs/SHAs, next evidence to inspect and next independent task. A successor
session starts with this prompt, adapting its authorization to that session:

> Read AGENTS.md, the newest WORKLOG entry, the current phase exit checklist,
> docs/design/AUTONOMOUS_DEVELOPMENT.md and docs/autonomy/backlog.json. Inspect
> working-tree and workflow state first. Use a coordinator and explicitly
> assigned specialist agents with disjoint file ownership. Preserve frozen G1
> and best133; first inspect already-running evidence, then advance the highest
> priority actionable phase-5 task. Distinguish setup fixes, rejected designs
> and scoped passes. Run substantial validation in existing GitHub workflows,
> keep heavy EDA hosted, and continue independent useful work while jobs run.
> Do not repeat rejected hypotheses or promote incomplete physical/timing
> evidence. Record exact provenance and end with a WORKLOG handoff. Apply only
> the Git authorization actually provided in this session.


## Recheck downloaded native repair evidence

`autonomy.repair_evidence` reuses the hosted grid/geometry/census/native-table/
guide validators, strict121/default and132/legacy observer controls, and exact
Git-object patch identities. It does not execute EDA, change hardware, dispatch,
or promote a route. Fetch the identity separately from the GitHub API; a local
JSON file is caller-supplied metadata, not independent proof of its own origin.

```sh
gh api repos/Kanishk234/protocol-emulator-asic/actions/runs/38950416231 \
  --jq '{id,head_sha,head_branch,name,status,conclusion,run_attempt}' \
  > build/observer109_result/run-identity.json
source .venv/bin/activate
PYTHONPATH=tools python -m autonomy.repair_evidence \
  build/observer109_result/controlled-native-pair-repair-38950416231/route_force_repair \
  --identity build/observer109_result/run-identity.json \
  --revision cb542492775ba0ee3b5a68e38e923956c09708dd \
  --run-id 38950416231 --attempt 1
```

Use `--candidate` only for a three-case D102 artifact; the auditor rejects an
old two-case observer as candidate evidence. Candidate native activation must
be witnessed, both legacy controls must revalidate, and retained result fields
must agree with freshly parsed native files. Physical acceptance always stays
false. Fetch the actual selected run's artifacts and API identity before
substituting its explicit run/attempt/full revision. No newest-run guessing.


## Escaping a rejected hypothesis class

D102 restored initial-owner discovery without improving routing. Require a new
kind of discriminating evidence before repeating that class of repair. Track
geometric cuts, simultaneous topology choices, native cost/history accounting,
layer assignment and exporter correctness separately; keep rejected outcomes
in the backlog. More agent opinions or a new tool name do not qualify a route.

The exact explicit-graph oracle is `autonomy.corridor_solver`. Its optional
requirement lives in requirements-routing.txt and its separate bounded hosted
qualification is corridor_solver.yaml. Install only in the project venv:

```sh
source .venv/bin/activate
python -m pip install -r requirements-routing.txt
PYTHONPATH=tools python -m autonomy.corridor_solver graph.json --output build/corridor/result.json
```

Input contracts explicitly declare capacities, fixed demand, per-layer net
weights, pinned terminals, nonpreferred motion and via assumptions. A shared
multisink trunk consumes one net's edge demand, not a separate wire per sink.
An independent witness checker verifies union occupancy and connectivity.
FEASIBLE/INFEASIBLE describe this graph only; UNKNOWN includes inconclusive
limits. No output authenticates native WARP inputs or grants physical acceptance.
See routing_escape_options_20261019.md and native_corridor_contract_20261019.md
in docs/reports for extraction and native reconciliation prerequisites.

## Native corridor qualification (October 19)

The observer build39304728263 passes compiled API smoke. Native qualification
39331153087 at675b659 failed the Docker file-permission handoff and retained no
artifact; retry39331845906 subsequently passed the accounting controls. The parser preserves weighted route-step multiplicity
and rejects missing usage rather than inventing background occupancy.

Use `PYTHONPATH=tools python -m autonomy.native_checkpoint <bundle> --output <json>`
to require all three initial native exports and the default final to be byte
identical. This check is separate from raw usage accounting and physical pin
mapping. Source tests include27 checkpoint cases and69 parser cases.

Portable `autonomy.repair_evidence --candidate --native-corridor` additionally
requires an exact Git-authenticated observer patch field and rechecks all six
exports. Run39331153087 predates the required observer metadata and failed artifact
collection (BUG102); it supplies no usable native ledger. The successful retry
39331845906 reuses the same observer build and carries strict source metadata.
Do not modify retained results to force portable audit acceptance.

Even a reconciled raw ledger does not establish physical pin access or via
legality. Next extraction must join actual GlobalRouter pin identities and
clamped/deduplicated FrNet terminals, account for endpoint via stacks, and
preserve each selected net's exterior connected components at every corridor
crossing. An exact solver result stays scoped to that declared graph until
native replay and physical/timing checks pass.

Native follow-up: retry39331845906 at6b19d03 completes after BUG102's exact-file
permission handoff. Portable native audit and byte-identical checkpoint checks
pass; all6 weighted ledgers reconcile139228edges. Initial one repeated
cfg_word[23] traversal prevents whole-state union equivalence. Legacy reported
132 and both-direction raw134 differ by two nonpreferred overflows. Preserve
both metric scopes. See native_corridor_run_20261019.md and independent
native_corridor_result_review_20261019.md. Next terminal/access export and
net-private exterior connectivity are separate reviewed implementations, not
native model qualification yet.

Terminal follow-up build39333325323 succeeds, retaining raw schema1. Native
terminal qualification39367564921 at8782e28 SUCCESS; all six raw/terminal audits
were independently reproduced. The global terminal gate stays false for local
empty/absent trees and supplies; explicit selected supported cohorts can qualify. Portable auditing of a terminal-enabled
bundle requires all three flags `--candidate --native-corridor --native-terminals`
and the exact Git-authenticated fourth patch. It rechecks raw accounting,
checkpoint capacities/identity, native completion, terminal inventory, hashes
and unchanged terminal identity before comparing stored joins. Diagnostic
unsupported access stays false; malformed joins fail collection. Clock joins
compare raw native clock with database CLOCK, preserving the distinct cached
GlobalRouter nonleaf flag. No hardware/physical acceptance follows.


## Finite cut-guided joint routing campaigns (October20)

The five-net full-grid coarse problem is independently cut-infeasible, not just
window-limited. Known cuts also reject successive small expansions. Keep the
native121 result protected; these are frozen-other-route constraints, not proof
that the complete chip is unroutable. See
[global cohort evidence](../reports/global_cohort_obstructions_20261019.md).

`cut_cohort` chooses additional unit/all-layer nets against known necessary cut
inequalities. It checks selected margins using original integer resources;
selection is never a routing witness. `cut_cohort_native` reconstructs every
supplied graph/certificate against native inputs before making the cut problem.
`corridor_reduce` prunes terminal-free leaves and contracts chains. Its optional
topological coordinates are computational indices; every feasible witness must
expand through original paths, original resources and native pin connectivity.
Parallel chains retain separate original paths for unit-capacity allocation.

`cut_refinement.run` performs at most eight requested rounds (four in the hosted
joint entry). Each newly discovered deficit becomes a checked counterexample;
a routing solver runs only after necessary-cut discovery returns none. UNKNOWN
stays inconclusive. Stage JSON files are exclusive and retained before later
steps, so a failure does not erase an earlier proposal or certificate. Seed cuts
and bounded history support resume. A missing cut is not a feasibility proof.

The manual `native_solver_campaign.yaml` supports `mode=fixed` or `mode=joint`.
Both import the explicit successful native run/source/attempt/API identity and
rerun all three portable audit modes first. Joint mode uses SCIP, at most five
extra nets, four rounds,30s/1024MB/one worker per solve, and an explicit150k route
variable cap (inside the existing500k hard bound). Its larger model census
accommodates broader cohorts required by the cuts; time and memory budgets do
not increase. Fixed mode retains its100k cap. The job has a12minute outer bound,
read-only GitHub permissions, artifact upload and no route installation/promotion.

For resume, `native_joint_campaign.encode_seeds(snapshot,state,records)` creates
an archive of checkpoint hashes, cohort IDs and partition node sets only. The
optional `seed_manifest` workflow input accepts at most50k encoded bytes; decoded
content is bounded to2MB/32cuts. Every imported model and deficit is reconstructed
from the newly authenticated snapshot. Stored status booleans are not imported.
Known-cut storage allows64cuts with a10k resource bound; each invocation still
has a finite round limit. Preserve generated models/logs in artifacts, not Git.

A local equivalent, after fetching native artifacts and their API identity:

```sh
source .venv/bin/activate
PYTHONPATH=tools python -m autonomy.native_joint_campaign <bundle> --identity <api-json> --revision 8782e284e94706486f20f25248c7067eecdf0d70 --run-id 39367564921 --attempt 1 --seed-manifest "$WARP_SEED_MANIFEST" --output build/joint-<unique>
```

The session reviews outcomes and chooses the next hypothesis. The workflow
executes a finite diagnostic and does not create continuous background AI.

## Fresh successor exploration (October20)

User approved FRESH_CANDIDATE_PLAN.md; begin paired G1 capability census before choosing hardware. New framed UART+SPI workload passes16mode/primitive simulations and22evidence-checker tests. Fully hard-backed combination requires three timers/three shifts, correcting the initial two/two assumption. Hosted39470166731 atfc7a3ac is pending; do not infer fit from standalone cell sums. Preserve all six personalities and seal a fresh evaluation set before hardware tuning.

Incremental congestion sourceaa33398 retains an uninstalled121→118coarse proposal with whole-grid independent checks. Native best remains121. Pinned readSegments review finds append/accounting hazards; require a pristine full-inventory/native-ledger round-trip before handoff. Strict capacity-feasibility cuts and partial-overflow objectives answer different questions. No automatic promotion.

## R1 evaluation seal — do not open selected identities

Four roles are sealed in `HELDOUT_R1_SEALED.json`, SHA256 a36c0e2ebc4b04555d744c1433e6ebbbff96fad36dfcdc77084aa979b71e026d. Read only `HELDOUT_R1_MANIFEST.json` before R1 hardware freeze. The entire six-role public pool in that manifest is excluded from training, profiling and new RTL/models until freeze. `.rgignore` excludes the selected file from ordinary searches; do not bypass it. The coordinator used SystemRandom without printing or reading selected identities; this is a procedural seal, not independent-agent selection or encryption. Never replace/reseed the seal after candidate tuning.

Automatic approval review rejected committing the selected JSON to repository history. Keep that file local while explicit payload approval is pending; commit only the public manifest/hash and exclusion rules. No selected identities were uploaded. This leaves recovery dependent on the local file; do not regenerate it if lost.
