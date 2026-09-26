# Worklog

Newest entry at the top. One entry per session: what was done, boxes ticked (with evidence), next step.

---

## 2026-09-26 (`anish_branch`: user-authorized commits)
The user explicitly authorized committing the pending work. Reviewed the
experiment sources, runners and reports, retaining the documented failing
reload gate. Tooling and documentation are grouped separately using the
verified `anishvivek16` author/committer identity. Existing validation
remains 14 passing unit tests, shell syntax checks, and the recorded fabric
simulations; no expensive builds were repeated. No push was requested.
No phase boxes were ticked; the next step remains the reload repair plan.

## 2026-09-26 (`anish_branch`: frame-level reload diagnosis)
**Done:**
- Reused the two existing compiled images; no repeated synthesis/P&R or
  physical build. Cached run `warp-recheck.EAQHpix8`: cold LFSR 1,157 checks
  passes, wrong-image negative control exits 1, quick reload times out at
  byte 1996 (column 1/frame 12). Logs are now retained on the Windows volume.
- Added a strict reference-frame decoder and static SCC runner. Decoding
  matches all 140 macros of the tool-generated LFSR header. Complete
  counter/LFSR snapshots have 8 common DSP SCCs, while snapshots after
  32/33 new frames have 10/12 total SCCs, including new LUT feedback.
  Run IDs and limitations are in `docs/reports/ANISH_REFERENCE.md`.
- Added a separate read-only probe: `warp-recheck.GJ42Zo6F` observes
  64 transitions at one timestamp in X1Y8/LC's feedback mux, with A=1,
  B=0 and select fed by its output. This confirms RTL-model oscillation;
  it does not measure silicon behavior. Probe run remains a failure.
- Retained full-counter rerun `warp-recheck.bM6h67mg`: exit 0, 65,673 checks
  including wraparound. Corrected evidence references to supersede the
  initial temporary diagnostic log that did not survive WSL shutdown.
- Added `ANISH_RELOAD_PLAN.md`: test load ordering, define isolation graph
  coverage, include recovery and isolation cost in capacity comparisons.
  Consulted the upstream partial-reconfiguration discussion and Tiny
  FABulous integration/simulation documentation. Updated bug, research,
  version and phase-summary documents without changing chip RTL.
- Validation: 14 decoder/configuration-audit tests pass, all three shell
  runners pass `bash -n`, and `git diff --check` passes. No new chip/CI or
  physical signoff result is claimed.

**Boxes ticked:** none. The persistent reload acceptance test still fails.
No commit or push; branch and Git identity remain `anish_branch` /
`anishvivek16`. No changes to others' history.

**Next:** use the preserved frame/loop witness to test alternate loading
orders, then a minimal isolation candidate. Require a live A/B/A pass and
interrupted-load recovery before accepting a repair. Include any required
hardware overhead in the equal-area architecture comparison.

## 2026-09-25 (`anish_branch`: supported reference flow and upstream review)
**Done:**
- Fetched `origin/main` (`43282b4`) and `origin/efpga` (`b45a1d8`); reviewed
  their new pin-unit measurements and fabric capacity estimate. Added
  `docs/reports/ANISH_UPSTREAM_REVIEW.md` and linked it from the research
  plan. No branch merge or history change.
- Installed OSS CAD Suite 2026-06-29 under `/home/awsma/eda/2026-06-29`;
  removed exploratory replacement LUT/FF maps and pinned the compatible
  reference toolchain. Documented ANISH-D1 and the tool mismatch bug.
- Added independent pin-oracle tests and a reproducible runner for two
  real images, reset/enable behavior, counter wraparound, persistent A/B/A
  reload, a cold LFSR check and a wrong-image negative control. Added LF
  attributes for shell/FABulous scripts and evidence manifests.
- Local run `warp-reference.OBUfXfus`: counter compilation 26 logic cells;
  LFSR 19; both images 12,024 bytes. Counter passes 65,673 checked cycles
  before reload; cold LFSR passes 1,157; wrong-image test catches the
  functional mismatch. These are stock reference results, not chip capacity.
- Found ANISH-FAB-2: reload stalls during the second image upload. The
  bounded diagnostic reproduces it after the byte-1024 marker. Added
  progress logs and time limits; the runner fails rather than claiming PASS.
- Configuration audit: 616 mapped bits and 24 padding per reference tile;
  seven audit unit tests pass. `docs/reports/ANISH_REFERENCE.md` records
  scope, image hashes, run ID and unresolved checks.

**Boxes ticked:** none. Individual reference results do not close the
persistent reload or complete phase-0 gates. No chip RTL was changed.

**Next:** isolate the failing configuration transition and test a safe load
sequence/isolation repair; only then map complete protocol workloads and
measure actual primitive savings. The candidate remains specialized eFPGA
plus fixed shell; equal-area comparison, I2C-target storage and routing
margin remain open. All current edits are uncommitted for user review.

## 2026-09-25 (session 2)
**Done:**
- Fixed the `gds` docs check failure (empty title/author/description/pinout, missing `info.md` sections): filled `info.yaml` (WARP, 6x4, 50 MHz, `tt_um_warp`) and `docs/info.md`. Pinout is provisional (D-006).
- Renamed the placeholder top to `tt_um_warp` (`src/tt_um_warp.v`, `test/tb.v`, `test/Makefile`).
- Took the template `gl_test` UDP fix preemptively (BUGS #1).
- Added `scripts/setup_venv.sh`, `check_all.sh`, `gl_local.sh`, `requirements-dev.txt`, the `lint` workflow, and the `gds` paths filter + non-cancelling concurrency.
- Installed OSS CAD Suite 2026-09-25 to `~/oss-cad-suite`; FABulous-FPGA 2.2.0 into `.venv` (pinned). PATH order D-007; versions in `docs/VERSIONS.md`.
- Deleted the duplicate `docs/OVERVIEW.md` (the user did this).

**Boxes ticked (phase 0):** repo/info.yaml (local `--check-docs` pass), docs skeleton, setup_venv, OSS CAD Suite + PATH (D-007), check_all (PASS), gl_local (PASS). All local; CI run IDs to be added after the push.

**Blocked:** `FABulous` does not start: `ModuleNotFoundError: No module named 'tkinter'`. Needs `sudo apt install python3-tk` (the user; needs a password).

**Next step:** after `python3-tk`, build the FABulous demo fabric and run its reference user design through to a bitstream and simulation; then the LUT4AB area/config-bit measurement on cmos5l (early capacity estimate). Push and record CI run IDs for `test`, `gds`, `lint`.

## 2026-09-25
**Done:** Project plan, CLAUDE.md and phase docs created (drafted in a Claude chat, not yet checked against a working repo).
**Boxes ticked:** none.
**Next step:** Phase 0, first task: create the repo from the CMOS5L template.
