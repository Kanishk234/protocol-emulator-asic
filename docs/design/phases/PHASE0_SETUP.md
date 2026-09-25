# Phase 0: Setup

**Dates:** Sep 25 – Oct 4, 2026
**Goal:** a working repository where both flows run end to end on trivial designs: the Tiny Tapeout CMOS5L flow (RTL → GDS) and the FABulous flow (fabric → user Verilog → bitstream → simulation). Tool versions are pinned and the organizers have been asked the open questions.

## Tasks

### Repository and competition
- [x] Create the repo from the CMOS5L template; set `info.yaml` tiles to 6x4 and the top module to `tt_um_warp`. (template commit beb67c3; `info.yaml` 6x4 / `tt_um_warp`, local `tt_tool.py --check-docs` passes 2026-09-25; CI run ID pending push)
- [ ] Fill in the competition sign-up form.
- [ ] Email asic-competition@janestreet.com: (1) is an eFPGA-based emulator with no CPU eligible, (2) is a separately hardened fabric macro allowed inside the template flow. Log the question and answer in DECISIONS.
- [x] Create `docs/` skeleton files (WORKLOG, DECISIONS, BUGS, CLAIMS, VERSIONS, summaries/, reports/). (all present; `notes/` too)

### Environment
- [x] `scripts/setup_venv.sh` creates `.venv` from `requirements-dev.txt`. (run 2026-09-25, Python 3.12.3)
- [x] OSS CAD Suite installed; local Icarus version matches CI's; PATH order recorded in DECISIONS. (OSS CAD Suite 2026-09-25; Icarus 12.0 = CI; D-007)
- [x] `scripts/check_all.sh` runs lint and all simulation tests (trivially passing at this point). (PASS 2026-09-25, local)
- [x] `scripts/gl_local.sh` runs a gate-level simulation the way CI's `gl_test` does. (PASS 2026-09-25: Yosys netlist on cmos5l typ lib, TT Icarus 13, PDK 2bbec75)

### Template flow
- [ ] The template's trivial design passes `test`, `gds` (including precheck and `gl_test`) on CI.
- [ ] Record the hardening time and resource usage in `PHYSICAL_DESIGN_AND_CI.md`.
- [ ] Add `lint` and `unit` workflows as separate files; set the `gds` paths filter and concurrency.

### FABulous flow
- [ ] Pick one FABulous release (or known-working commit set) and record every tool version in `docs/VERSIONS.md`.
- [ ] Build a small reference fabric from the pinned release.
- [ ] Compile an unchanged reference user design to a bitstream and simulate the fabric loading and running it.
- [ ] Load a second, different design into the same fabric model and confirm different behavior.

### Prior art study
- [ ] Read Tiny FABulous: how the fabric is integrated into Tiny Tapeout (flat or macro), how configuration is loaded, how tests are organized. Notes in `docs/notes/tiny_fabulous.md`.
- [ ] Read PRISM's documentation: what it does, how its programming model differs from ours. Notes in `docs/notes/prior_art.md`.

## Phase exit checklist
- [ ] Template trivial design green on all template workflows (CI run IDs: …)
- [ ] FABulous reference: two different bitstreams loaded and run in the same fabric simulation (log summary in `docs/reports/`)
- [ ] `docs/VERSIONS.md` complete and matches what was run
- [ ] Hardening time recorded
- [ ] Organizer email sent (date noted); answer logged when it arrives
- [ ] Tiny FABulous integration method understood and written down
- [ ] Decision point: is there a known path to put a FABulous fabric through the TT CMOS5L flow? (answer in DECISIONS)
- [ ] All CI workflows green on `main`
- [ ] `docs/summaries/PHASE0.md` written
