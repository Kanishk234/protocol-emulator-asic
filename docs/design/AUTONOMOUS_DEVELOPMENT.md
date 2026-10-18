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

## Current priority and protected results

The first unfinished phase is phase 5. Its report-content and summary gates have evidence; the remaining exit gate is
all required CI green on `efpga`, with source applicability audited. See `phases/PHASE5_EVIDENCE_DOCS.md`; do not start submission
tasks until every exit item passes. A new experiment does not itself tick a box.

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
