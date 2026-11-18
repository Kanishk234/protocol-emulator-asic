# Repository organization before Phase 3

This cleanup preserves the qualified full-design RTL, configuration, constraints, macro views, encodings, tile allocation and all four official workflow files. It does not start Phase 3 or substitute a new physical recipe.

## What changed

| Area | Result |
|---|---|
| Experiment history | Complete original tree preserved at 9b440582c489b228f8306a137f3a722bdfa8ed2a on `archive/phase2-experiments-20261118` |
| Main working tree | 1,306 retired tracked files inventoried in `docs/archive/phase2-files.json`; old screens, replay helpers, synthesis benches, patches and superseded reports removed |
| Workflows | 249 → 9 active definitions: four unchanged official files, lint/unit/nightly, repository audit, reusable manual protocol replay |
| Current documentation | New index, baseline and protocol scenario matrix; current 8×4/2-lane/4-unit facts; historical worklog and estimates clearly separated |
| Development checks | Mandatory internal-suite aggregator; CURDIR paths; current-checkout L2 defaults; committed SRAM models; no experiment-directory fetch in unit CI |
| Local tools | Qualified PDK revision used for local GL/synthesis helpers; explicit matching netlist/PDK for internal GL |
| Dev container | Project venv setup; removes mutable support-tool checkout and conflicting combined dependency installs; physical signoff stays in official CI |
| Evidence preservation | Official submission, precheck and GL artifacts copied and hash-verified outside repo; full detailed GDS logs archived with a checksum |
| Build cleanup | Obsolete build/, old spike/synthesis builds removed; venv, PDK caches and Git history preserved |

The external evidence directory is `/home/younix/protocol-emulator-asic-local-archive/phase2-green-44189196098`. It is local storage, not part of the submission; CI artifacts and committed compact receipts remain the portable evidence sources.

## Validation

- Qualified-input guard passes; generated files and source lists match.
- GDS, test, docs and FPGA workflow bytes match their pre-cleanup snapshots.
- All eight vendored macro-view hashes match PROVENANCE.json; licenses retained.
- Markdown file links resolve; archived links target immutable history.
- All nine workflow YAML files parse; shell entry points pass `bash -n`.
- Verilator full-design lint passes with the existing narrow annotations. The qualified PDK Liberty was fetched successfully and the existing Yosys synthesis/allowed-latch sanity check passes.
- Maintained CI helper tests: 27 passed, including missing/skipped/failed replay cases, mismatched input identities and Make/shell filter expansion.
- Model/tool tests: 335 passed (non-slow suite, four workers).
- L1 aggregator: 147 executions passed, including lean/full pin modes.
- Top-level RTL: 3/3 passed with no skips.
- Full chip/protocol/rotation regression: 28/28 passed under Verilator, including all 22 protocol cases, with zero failures/skips (386.15 s simulation runner wall time). Compact hashes and counts: `repository_cleanup_20261118.json`.

The restricted sandbox cannot initialize sigrok's libusb backend; its first model run had empty decoder output. The same required decoder checks passed outside the sandbox. Decoder checks were not bypassed. The long chip suite was switched from Icarus to the established Verilator runner; an interrupted run is not counted as passing evidence.

No tracked raw log, waveform, ZIP, SPEF, ODB or SDF was found. A targeted private-key/token-pattern scan found no matches; this is not a comprehensive security audit. The new replay workflow and revised devcontainer still need their first execution in their intended environments; static checks and helper tests do not establish that they ran successfully.

## Publication and Phase 3 entry

Main's latest published 9b44058 test 44255442381, lint 44255442549, unit 44255442544 and docs 44255442455 runs are all green. No main workflow is in progress. Creating the archive branch triggered its normal unit check 44257560136; that branch check is separate from current main and is not hardening. Two historical October 7 runs remain queued with no jobs: l3-placement-routed-gl 37655518919 and gds-placement-extracted-timing 37655518925; neither is current qualification work. The user explicitly authorized committing and pushing the complete cleanup after local validation. Publish the complete file groups together, then require the routine CI and new repo-audit checks to pass. No hardening is needed for this cleanup because hardware and official jobs are unchanged.

After publication CI passes, review the Phase 3 schedule and pick a firmware/verification showcase using existing primitives. MEM/CAPTURE hardware remains deferred and the stock FPGA workflow is not a Basys 3 build.

Suggested publication commands (run all groups before pushing):

```sh
git add -A -- scripts spikes synth formal test test_internal .devcontainer
git commit -m "tools: retire phase 2 experiments and repair local checks"
git add -A -- .github/workflows
git commit -m "ci: retain core workflows and reusable protocol replay"
git add -A -- docs programs/README.md README.md AGENTS.md CLAUDE.md
git commit -m "docs: organize qualified baseline and archived experiments"
git diff --check
git log origin/main..main -- src info.yaml macro
git push origin main
```

The hardware-path log should be empty for these cleanup commits. Preserve the archive branch; do not rewrite history or force-push. The new replay workflow is manual and does not trigger a physical build.
