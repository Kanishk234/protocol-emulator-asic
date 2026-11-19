# D-192 physical screen: prepared, not executed

The verified status-merge candidate is ready for a separate manual `status-merge-screen` workflow. Local staging changes exactly `src/trw_pin_bs.v` in an ignored copy. Main hardware, info.yaml, SRAM, qualified configuration and official workflow files remain unchanged. The [preparation receipt](phase3_status_screen_preparation_result.json) binds staged inputs, source/helper/workflow hashes and49passing CI-helper tests. It is not a physical result: screen_passed, physical_qualified and official_gds_passed remain false.

## Inputs and tool compatibility

The screen requires the existing source-bound candidate proof and55-case whole-chip regression receipts. `prepare` audits the qualified repository first, copies src/macro/info.yaml, applies the exact reviewed patch and rejects any additional physical-input change. It also binds its read-only reporting helpers. It refuses to overwrite an existing trial directory or stage recursively inside qualified source/macro/Git directories.

Current upstream was checked through the GitHub API on2026-11-19. The [official action](https://github.com/TinyTapeout/tt-gds-action/blob/ttihp27a/action.yml) still selects LibreLane3.1.0.dev4 for CMOS5L and defaults support-tools to main. Support-tools advanced15commits from qualified9d13ff3 to reviewed0922544e6c7f6126047c3fba720b0437fa32a1b8. The [comparison](https://github.com/TinyTapeout/tt-support-tools/compare/9d13ff3e3e6202090740110438c6a10c1d62ca0f...0922544e6c7f6126047c3fba720b0437fa32a1b8) changes product docs, Sky130-only prechecks and extraction of an unchanged analog-pin limit into a named constant. Hardening generation, CMOS5L physical tech files and requirements are unchanged. The [review receipt](phase3_status_screen_upstream_review.json) lists changed files/blob identities.

The new workflow pins that reviewed current support-tools revision; the validator enforces the qualified LibreLane version, PDK89d42ee, container digest and OpenROAD build. A moving tag or unknown runtime override cannot silently change the test. Recheck upstream before the eventual official GDS run; this screen is not a guarantee of future official results.

## What runs

The current native Classic sequence, including the already-qualified post-timing antenna insertion, runs through `OpenROAD.STAMidPNR-3` and stops before detailed routing. It does not restore historical profile patches, change density/clock/repair settings, suppress native stages or modify the official template jobs.

Read-only audits then repeat STA for all three corners under both PnR and stock signoff constraints. The pinned native fallback is explicitly sourced through a read-only wrapper; the official config generator does not create a local src/signoff.sdc. All diagnostic configs remain beside src/config_merged.json so dir:: references resolve identically. Fresh ODB netlist exports must match across repetitions/corners, and source physical views must retain their hashes. Antenna checks are fresh on the same final ODB.

| Screen gate | Requirement |
|---|---|
| Actual functional flop/output setup reserve | Strictly positive at all three corners |
| Ordinary all-path setup/hold | Nonnegative slack and zero violation counts |
| Fast hold | At least50ps |
| Slew/capacitance/fanout | Zero violations at every corner |
| Fresh antenna check | Zero violating nets and pins |
| Routing | Zero preceding full-route overflow; final native incremental antenna repair forbids congestion |
| Clock uncertainty | Reports confirm unchanged0.25ns |
| Source/configuration/physical views | Hash identity preserved |

The overflow evidence has the same qualified baseline scope: it is a preceding full global-route measurement plus congestion-prohibited final native incremental antenna repair, not a newly invented final full-route result. Detailed-route DRC, extracted timing, LVS, full-GDS KLayout and TT precheck remain later gates under unchanged D-185policy. No raw-Magic-zero claim is made.

## Local checks completed

49CI-helper tests pass, including rejection of49.999ps fast hold, zero functional reserve despite aggregate setup0, missing/nonfinite metrics, positive slack with nonzero violation counts, modified trial configuration, unsafe staging paths, workflow/tool pin consistency and incorrect signoff/path assumptions. A fresh real staging pass confirms one RTL-file delta and identical project configuration. Physical tools/Docker are unavailable locally, so the physical engine itself has not been executed. Artifacts from a remote run must be reviewed before any pass or adoption claim.

Main has no active workflow at the last check. Two unrelated October7experiments remain queued in GitHub (37655518919and37655518925); they were not canceled or treated as new candidate runs.

## Publication and launch

The supplied AGENTS.md reserves commits/pushes for the user. The commands below are provided for the user to run, not executed by Codex. They publish proof/regression/CI/evidence groups; they do **not** apply the hardware patch to main src/. Review each staged group before committing. Before pushing, check `git log origin/main..main -- src info.yaml macro` and current hardening status: a hardware-input push can cancel a running hardening. This prepared publication does not change those inputs.

```sh
git status --short
git log origin/main..main -- src info.yaml macro

git add \
  spikes/phase3_status_merge/status_merge.patch
git diff --cached --stat
git commit -m 'rtl: add status merge repair prototype'

git add \
  .gitignore \
  formal/channel.sby \
  formal/fixtures/pin_unit_status_collision.json \
  formal/fixtures/pin_unit_status_collision_minimized.json \
  formal/pin_rx.sby \
  formal/pin_unit.sby \
  formal/props/channel_composition.sv \
  formal/props/pin_bs_overrun.vh \
  formal/props/pin_rx_overrun.sv \
  formal/props/pin_unit_flags.vh \
  formal/props/status_queue_harness.sv \
  formal/props/status_queue_reference.vh \
  formal/status_queue.sby \
  scripts/formal_channels.py \
  scripts/formal_pin_rx.py \
  scripts/formal_pin_unit.py \
  scripts/formal_status_candidate_integration.py \
  scripts/formal_status_queue.py
git diff --cached --stat
git commit -m 'formal: prove channel and pin status contracts'

git add \
  scripts/check_status_candidate_chip.sh \
  scripts/check_status_merge_candidate.py \
  scripts/replay_pin_unit_status.py
git diff --cached --stat
git commit -m 'test: add status merge replay and regressions'

git add \
  .github/workflows/formal.yaml \
  .github/workflows/status-merge-screen.yaml \
  scripts/ci/functional_setup_frontier.py \
  scripts/ci/functional_setup_frontier.tcl \
  scripts/ci/status_merge_screen.py \
  scripts/ci/status_merge_screen_audit.tcl \
  scripts/ci/test_status_merge_screen.py
git diff --cached --stat
git commit -m 'ci: add isolated status merge physical screen'

git add \
  docs/BUGS.md \
  docs/CLAIMS.md \
  docs/DECISIONS.md \
  docs/WORKLOG.md \
  docs/design/VERIFICATION.md \
  docs/design/phases/PHASE3_SHOWCASE_PROTOCOLS.md \
  docs/reports/PHASE3_FORMAL_CHANNELS.md \
  docs/reports/PHASE3_FORMAL_PIN_RX.md \
  docs/reports/PHASE3_FORMAL_PIN_UNIT.md \
  docs/reports/PHASE3_STATUS_MERGE_CANDIDATE.md \
  docs/reports/PHASE3_STATUS_MERGE_FORMAL.md \
  docs/reports/PHASE3_STATUS_MERGE_SCREEN_READY.md \
  docs/reports/phase3_formal_channels_result.json \
  docs/reports/phase3_formal_pin_rx_result.json \
  docs/reports/phase3_formal_pin_unit_result.json \
  docs/reports/phase3_pin_unit_status_replay_result.json \
  docs/reports/phase3_status_integration_formal_result.json \
  docs/reports/phase3_status_merge_candidate_result.json \
  docs/reports/phase3_status_queue_formal_result.json \
  docs/reports/phase3_status_screen_preparation_result.json \
  docs/reports/phase3_status_screen_upstream_review.json \
  docs/summaries/PHASE3.md
git diff --cached --stat
git commit -m 'docs: record phase 3 verification and screen readiness'

git push origin main
gh workflow run status-merge-screen.yaml --ref main
```

After the screen finishes, inspect its screen_result.json and raw reports. Proceed to detailed routing/official qualification only if all required screen gates pass. Main hardware remains the qualified baseline until the repair is deliberately adopted and requalified.
