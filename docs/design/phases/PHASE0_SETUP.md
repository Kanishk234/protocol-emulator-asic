# Phase 0: Setup

**Dates:** Sep 25 – Oct 4, 2026
**Goal:** a working repository where both flows run end to end on trivial designs: the Tiny Tapeout CMOS5L flow (RTL → GDS) and the FABulous flow (fabric → user Verilog → bitstream → simulation). Tool versions are pinned and the organizers have been asked the open questions.

## Tasks

### Repository and competition
- [x] Create the repo from the CMOS5L template; set `info.yaml` tiles to 6x4 and the top module to `tt_um_warp`. (template commit beb67c3; `info.yaml` 6x4 / `tt_um_warp`, local `tt_tool.py --check-docs` passes 2026-09-25; CI on a63877d: `docs` 36170807355 success, `gds` 36170807513 pending)
- [x] Fill in the competition sign-up form. (done by Kanishk, confirmed 2026-09-25)
- [ ] Email asic-competition@janestreet.com: (1) is an eFPGA-based emulator with no CPU eligible, (2) is a separately hardened fabric macro allowed inside the template flow. Log the question and answer in DECISIONS.
- [x] Create `docs/` skeleton files (WORKLOG, DECISIONS, BUGS, CLAIMS, VERSIONS, summaries/, reports/). (all present; `notes/` too)

### Environment
- [x] `scripts/setup_venv.sh` creates `.venv` from `requirements-dev.txt`. (run 2026-09-25, Python 3.12.3)
- [x] OSS CAD Suite installed; local Icarus version matches CI's; PATH order recorded in DECISIONS. (OSS CAD Suite 2026-06-29, the release FABulous 2.2 pins; Icarus 12.0 = CI; D-007)
- [x] `scripts/check_all.sh` runs lint and all simulation tests (trivially passing at this point). (PASS 2026-09-25, local)
- [x] `scripts/gl_local.sh` runs a gate-level simulation the way CI's `gl_test` does. (PASS 2026-09-25: Yosys netlist on cmos5l typ lib, TT Icarus 13, PDK 2bbec75)

### Template flow
- [x] The template's trivial design passes `test`, `gds` (including precheck and `gl_test`) on CI. (a63877d: `test` 36170807382, `gds` 36170807513 with precheck + `gl_test` green, `docs` 36170807355)
- [ ] Record the hardening time and resource usage in `PHYSICAL_DESIGN_AND_CI.md`.
- [ ] Add `lint` and `unit` workflows as separate files; set the `gds` paths filter and concurrency.

### FABulous flow
- [x] Pick one FABulous release (or known-working commit set) and record every tool version in `docs/VERSIONS.md`. (FABulous 2.2.0 + OSS CAD Suite 2026-06-29; CI LibreLane version still to fill in from the `gds` log)
- [x] Build a small reference fabric from the pinned release. (stock FABulous 2.2 project, 672 LCs; `docs/reports/fab_demo.md`)
- [x] Compile an unchanged reference user design to a bitstream and simulate the fabric loading and running it. (`sequential_16bit_en`, 100/100 cycles match; `docs/reports/fab_demo.md` step 1)
- [x] Load a second, different design into the same fabric model and confirm different behavior. (`lfsr_down` matches its source, mismatches the counter's; `docs/reports/fab_demo.md` steps 2-3)

### Prior art study
- [x] Read Tiny FABulous: how the fabric is integrated into Tiny Tapeout (flat or macro), how configuration is loaded, how tests are organized. Notes in `docs/notes/tiny_fabulous.md`. (done 2026-09-25)
- [x] Read PRISM's documentation: what it does, how its programming model differs from ours. Notes in `docs/notes/prior_art.md`. (done 2026-09-25, from its TT page)

## Phase exit checklist
- [ ] Template trivial design green on all template workflows (CI run IDs: …)
- [x] FABulous reference: two different bitstreams loaded and run in the same fabric simulation (log summary in `docs/reports/`) (`docs/reports/fab_demo.md`, local run 2026-09-25)
- [ ] `docs/VERSIONS.md` complete and matches what was run
- [x] Hardening time recorded (`PHYSICAL_DESIGN_AND_CI.md`, run 36170807513: `gds` job 35 min, precheck 12 min)
- [ ] Organizer email sent (date noted); answer logged when it arrives
- [x] Tiny FABulous integration method understood and written down (`docs/notes/tiny_fabulous.md`)
- [x] Decision point: is there a known path to put a FABulous fabric through the TT CMOS5L flow? (answer in DECISIONS) (D-009: yes; tile hardening on cmos5l still to be shown)
- [ ] All CI workflows green on `main`
- [ ] `docs/summaries/PHASE0.md` written
