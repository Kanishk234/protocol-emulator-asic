# TRIPWIRE closure branch, November 9

The user approved starting TRIPWIRE closure work, switching this workspace to
the new branch, and making grouped commits/pushes for this session with normal
messages and no attribution trailer. This session approval overrides the
standing Git restriction for this scope. Substantial verification belongs in
GitHub Actions, as the user requested.

Branch `tripwire/closure-8x4` starts at current main
`5407d4c278353ec125018f3a3d49de2fd620d9ce`. This workspace is checked out on
that branch. No rebase was necessary: the branch was created directly from the
fetched current main. The local `main` branch itself was not rewritten.
The initially used `/tmp/tripwire-closure` worktree is detached at the same
source; it does not own the working branch. Existing WARP review edits were
saved, including a worklog patch and report, under `/tmp/warp-review-preserved`.
Pre-existing untracked/previously ignored WARP artifacts are left alone.

## Concrete work

`scripts/ci/prepare_closure_candidate.py` exports committed source to a new
directory outside the source checkout and executes the existing hold125
workflow's exact preparation and 8x4 selection. It preserves all existing
hash/equivalence/physical-profile guards and refuses dirty candidate inputs,
an existing output directory, a different profile or ambiguous preparation.
There is no tool-runtime override, physical checkpoint import, acceptance
change, or physical launch. Candidate source, macro, firmware/model/test inputs
are recorded by hash and can be checked again after regression.

`.github/workflows/tripwire-closure-check.yaml` checks that source candidate
using the pinned OSS CAD Suite, real sigrok decoders and a project venv. It
runs compiler/model tests, four tests on the actual Tiny Tapeout top and the
22-case full-core protocol suite. Strict result inspection rejects missing,
failed, errored or skipped cases. Artifacts retain the actual source, candidate
receipt, environment versions and XML. This is RTL verification, not routed
netlist testing, physical timing or a phase-two exit claim. The protected
template jobs and production hardware/configuration remain unchanged.

## Local checks and environment findings

- 50 preparation/profile/screen-gate tests pass, including six new exporter
  selection/output-protection cases.
- Exact pre-expansion exporter smoke prepares the current full core, 8x4 and
  `portable_clock75_hold125`; all original source/profile guards pass and 36
  physical/metadata inputs are recorded and rechecked. The final exporter also
  binds firmware/model/test sources; cloud execution will establish its full
  count on committed branch source.
- Compiler/model suite on the prepared candidate: 335 passed, using real
  sigrok, with a project venv outside the sandbox. The initial sandbox run
  produced 30 decoder failures because libusb initialization was blocked and
  sigrok emitted empty output. The successful rerun resolves this environment
  issue without skipping decoders or changing a test.
- System Verilator 5.020 cannot run cocotb 2; explicitly selected the pinned
  OSS CAD Suite Verilator. Partial local full-core replay passes UART TX/RX
  after allowing sigrok. Both local full-protocol processes were stopped when
  moving substantial verification to cloud; no 22-case local pass is claimed.
- New workflow shell and embedded Python parse; actionlint/diff checks are
  recorded in the worklog. No physical run launched locally.

## Next gate

Published tools2cb5c89, CI47e57e7 and docse248408 to
[`tripwire/closure-8x4`](https://github.com/Kanishk234/protocol-emulator-asic/tree/tripwire/closure-8x4).
[Candidate regression42690695832](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42690695832)
is confirmed in progress at exact sourcee248408. Standard unit42690695243,
test42690695257, lint42690695247 and docs42690694815 also queued/started.
No success is claimed before actual job/artifact inspection. Existing main
physical42681697462 is independently still in progress. This publication
receipt changes documentation only and does not supersede the candidate run's
source identity.

## Authenticated cloud result

Run42690695832 at e248408 is now SUCCESS. Downloaded artifact
`tripwire-closure-42690695832` contains strict XML with335model/compiler,
4actualTTtop and22protocol cases, all passing with0failures/errors/skips.
All170input hashes reconcile:141directly against e248408Git objects and29
against the independently prepared same candidate. Git comparison confirms no
changes to the underlying source/model/firmware/spec/tests/patches/physical
workflow from5407d4c to e248408. The34physical/metadata files actually present
in the artifact independently match their receipt; full170-file artifact
availability is not claimed. The hosted before/after check verifies candidate
inputs remain unchanged during execution.

| Evidence | SHA256 |
|---|---|
| tools.xml | `543c29844ba7856891f113008243aef6f98cc1c382f572d70ee1a6ba17f6a70b` |
| top.xml | `ce81f0a46635eeddac5f30191b635c8d21f86e76ccce12a59b8abf5031d7dd20` |
| protocols.xml | `a222767beee0df0b65b74f022600e424f292a26b646cbaed298b833493bdc1a2` |
| closure-candidate.json | `bb0c735f777147aeeeeda40ffee18427f5f3451d7c93ab3bf358d89136214cce` |

This refresh establishes the current candidate's RTL behavior, not extracted
timing or hardened operation. Source screen42681697462 remains separate.

## Qualified route continuation

`closure_route.py` and `tripwire-closure-route.yaml` prepare a continuation of
exact source screen42681697462,5407d4c,attempt1. A bounded cloud dependency
job waits for that source run to complete successfully. Any source failure,
foreign identity or180-minute dependency timeout stops the workflow before a
route job starts. This is an automatic dependency gate, not permission to
weaken screening.

The route job binds the complete archive to the API digest, refuses unsafe ZIP
entries and compares hardware/macros/config/metadata against fresh preparation.
It restores the original runner paths without rewriting saved state, recomputes
saved raw-screen qualification, checks signoff source hashes and metrics, and
verifies the exact dev4 engine/PDK/tools. Fresh original/signoff timing and
antenna checks precede DRT. Only thread count and per-iteration diagnostic
capture change in routing configuration; no physical repair, recipe search or
timing exception is introduced.

A completed zero-DRC route must pass topology/antenna/disconnect checks before
extraction. Extracted all-corner setup/electrical and>=50psfast-hold gates are
then mandatory. DRC reports/snapshots and outputs are retained on failure or
timeout, which are never treated as completion. Official GDS/precheck and
routed protocol replay remain later gates. Preparation/control tests are not
new physical evidence. Publication and actual execution status are recorded
in the worklog.

## Current release frontier

Published tools `fcd8dc5`, CI `059478e` and evidence `b13b439`.
[Qualified-route workflow 42692486237](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42692486237)
is confirmed at exact source `b13b439`: its 54 guard tests pass in the cloud
and its source dependency is waiting for run 42681697462. No route has started
while that source screen is pending. A failed source or wait timeout will stop
the continuation; a passing source allows fresh checks, routing and extraction
without another manual dispatch.

| Gate | Current evidence/status |
|---|---|
| Current full-core RTL regression | PASS, 42690695832; [exact case matrix](CLOSURE_PROTOCOL_MATRIX_20261109.md) |
| Current directed million-clock lockstep and two fault controls | PASS, authenticated 42697037494; [scope and evidence](CLOSURE_LOCKSTEP_20261109.md) |
| Current dev4 8x4 physical screen | PASS, authenticated 42681697462; [measurements](CLOSURE_SCREEN_20261109.md) |
| Exact route restoration/guards | Corrected cloud 42693952530 passes actual restoration, 55 guards and engine/Ciel initialization |
| Native pre-DRT protocol replay | PASS, authenticated 42694710310: all 22 cases, no skips, exact native NL |
| Detailed route and extracted timing | Route DRC/antenna/disconnect checks pass; extracted slow setup fails -1.982448040 ns in 42693952530 |
| Matching final-netlist protocol replay | 42700728949 refuses failed source; no final replay acceptance |
| Current qualified GDS/precheck and production integration | Pending |

Lint 42692486515, test 42692486236, docs 42692486054 and baseline
unit 42692486070 pass at `b13b439`. Cancelled two redundant
older branch unit runs (42690695243 and 42690788229) after Git comparison
confirmed identical consumed workflow/RTL/tool/model/spec/firmware/test inputs.
These baseline checks do not replace the candidate-specific or physical
gates. No release-wide all-CI-green or phase-completion claim is made.

Production core/config promotion remains conditional on reproducible physical
closure and review of settings outside the standing configuration whitelist.
No merge into main is implied by this branch.

## Current lockstep refresh

The historical million-clock lockstep result is not silently reused for the
composed closure candidate. `tripwire-closure-lockstep.yaml` prepares that exact
candidate and runs the existing directed RTL/model comparison for one million
clocks, followed by clean RX/cursor controls and both injected faults. The
priority injection now recognizes the original and shared-priority lane forms
unambiguously. Local exhaustive mask checks qualify the fault selector; only
actual simulation mismatches can earn detection credit.

The runner retains control and mutant XML/stdout when `L2_EVIDENCE_DIR` is set.
The cloud job requires one executed case per run, no skip/error, a passing
pristine control and a genuine failing mutation with a scoreboard divergence.
All evidence and mutant source copies are retained, while compiled simulator
binaries are excluded. The untouched candidate is hashed again after replay.
Hosted result 42697037494 is now SUCCESS; the downloaded million-clock case,
both clean controls and both intended assertion failures are authenticated in
[the lockstep report](CLOSURE_LOCKSTEP_20261109.md). This test covers the directed lane/
channel/pin stimulus in the existing bench, rather than arbitrary firmware,
exhaustive state exploration or physical timing.

## Exact final-netlist replay gate

`tripwire-closure-final-gl.yaml` waits for the exact reviewed route run
42693952530 at `ebf817e`, attempt 1, to finish successfully. It refuses a failed
source, foreign run or bounded dependency timeout. The replay then authenticates
the complete route archive, original frozen views, source/config/macros and
all completed route/extraction gates. It selects the exact NL named by the
extracted STA state, including a correctly inherited DRT NL, and checks its
logical cell connectivity against the detailed-route export.

Only that selected byte-identical netlist is replayed with Icarus 13, exact
new-PDK cell models, the pinned SRAM behavioral model, real sigrok and the
existing 22 protocol cases. The netlist, source bindings, runtime hashes and
strict XML are retained; no SDF or official GDS qualification is claimed.
Fourteen admission controls pass locally, but actual route artifacts and
replay remain pending. This keeps the earlier pre-DRT native replay separate
from the required final implementation test.

The source route subsequently fails extracted slow setup. Final replay
42700728949 correctly stops at its source gate. See
[the measured route failure and next diagnostic](CLOSURE_ROUTE_20261109.md).
No success-only gate has been weakened.
