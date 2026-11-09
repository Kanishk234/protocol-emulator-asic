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

Publish grouped tools/CI/docs commits and inspect the branch regression's
actual artifact. Do not count default branch unit/test badges as evidence for
the experimental core. Existing physical run42681697462 on main remains
untouched and was still in progress at the last check. Once its gates finish,
inspect native results before choosing detailed routing or another measured
one-variable correction. Production core/config promotion remains conditional
on reproducible physical closure and review of settings outside the standing
configuration whitelist; no main merge is implied by this branch.
