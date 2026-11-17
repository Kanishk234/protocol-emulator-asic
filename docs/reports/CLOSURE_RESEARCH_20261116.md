# Closure methods review — 2026-11-16

Current result: no demonstrated stock20ns extracted closure for the selector
candidate. Density60 run43961635994 failed solely five antenna nets/pins,
overflow0; reject it. The better density56 source43951998125 still fails one
antenna, despite estimated timing/electrical/overflow passes. Historical routed
reference42693952530 has slow setup−1.982448ns and legacy hold uncertainty;
it does not establish current-source stock closure.

## Research findings and scope

The exact pinned PDK89d42ee6 config sets an empty LAYERS_RC dictionary and
selects IHP_rcx_patterns.rules. This establishes an estimation-model concern
in our actual pinned source, independently of reports about newer dev:
[pinned config, lines85–119](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/89d42ee6d2fd9b50b86a1aada6fee6673c3e6008/ihp-sg13cmos5l/libs.tech/librelane/config.tcl#L85).
We have not yet compared the resolved runtime layer values or extraction-rule
contents. Empty source configuration alone does not quantify our timing error.

[IHP issue1282](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1282) reports
underestimated wire capacitance relative to extraction in a different design
and warns that its fitted values use an extraction deck under question. Its
numbers are unsuitable as replacement signoff values. This is corroborating
context, not a measured explanation of our current critical path.

[IHP issue1151](https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1151) records
maintainer concern about the reused SG13G2 extraction deck for CMOS5L.
[PR1237](https://github.com/IHP-GmbH/IHP-Open-PDK/pull/1237) proposes CMOS5L
extraction models and configuration changes; the reviewed page still marks it
draft. No unreviewed model or PDK upgrade is applied. Keep extracted results
labelled with their exact PDK/deck, and investigate the official accepted
submission toolchain before calling numerical closure foundry signoff.

[OpenROAD's repair documentation](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html#repair-antennas)
describes diode/jumper repair and warns that diode insertion cannot improve
certain constant diffusion-side-area rules. Thus more diodes are not a
universal fix. Check the actual violating rule and available diffusion credit
in the pinned technology before selecting another repair method. Latest docs
are a research guide; they do not establish our pinned binary's behavior.

For our exact LibreLane3.1.0.dev4 wheel, drt.tcl contains a post-route antenna
repair/reroute loop. The local script SHA256 is
e7e4e4984dff976e96fdf42561b185000bc2a9a3a21553b9bc781cfaef94447f.
The proposed workflow checks that hash inside the pinned image and checks the
resolved native default of three iterations. Runtime verification is pending.
Local installed LibreLane3.0.14 is not evidence for dev4 behavior.

## Ranked next experiments

| Priority | Action | Evidence required / limit |
| --- | --- | --- |
| 1 | Route the exact better selector artifact using stock DRT repair, then extract | D-176 diagnostic; fresh source checks, zero DRC, connected route, all-corner native0.25ns reports; failed antenna remains failure |
| 2 | Compare estimated and extracted delay/capacitance on actual failing paths | Same source/corner/constraints; separate cell delay, wire delay and clock skew; inspect resolved LAYERS_RC and actual extraction deck hashes |
| 3 | Inspect residual antenna geometry and repair iterations | Before/after detailed route, diode/jumper changes, per-layer ratios and diffusion credit; global-guide rectangle counts are insufficient |
| 4 | Evaluate an officially accepted CMOS5L RC model when available | Separate pinned toolchain comparison and decision; rerun physical/electrical/timing checks; never transplant issue1282's fitted numbers |
| 5 | Make one general RTL or placement change driven by measured critical path | Preserve live configuration timing, independent primitive checks and full protocol regression before hardening |

Density60 is rejected, not a reason for a broad density/seed sweep. A slower
clock is a contract decision rather than closure at20ns. Keep Metal4 limits,
hold/electrical/antenna/DRC gates and live configuration timing intact. Existing
simulation passes remain useful functional evidence, not extracted timing.

## Prepared diagnostic and publication

Local implementation: scripts/ci/selector_drt_diagnostic.py, its16controls,
and .github/workflows/tripwire-selector-drt-diagnostic.yaml. Combined related
suite150passed; actionlint passed. No diagnostic cloud run exists yet.
The workflow push trigger covers only its own file on tripwire/closure-8x4.
It emits its own diagnostic result and never a qualified-route completion.

Automatic approval review could not complete the attempted commit because its
service usage quota was exhausted; no commit/push was executed. Existing session
authorization has been explicitly renewed. Publish after review service recovery
or by the user. Do not bypass review. Before pushing, inspect active hardening and
`git log origin/main..main -- src info.yaml macro` as required by AGENTS.md;
these prepared changes contain no hardware inputs.

Scoped commands for the user if publishing directly:

```sh
git add scripts/ci/selector_drt_diagnostic.py scripts/ci/test_selector_drt_diagnostic.py
git commit -m 'tools: add bounded selector routing diagnostic'
git add docs/DECISIONS.md docs/WORKLOG.md docs/reports/CLOSURE_RESEARCH_20261116.md
git commit -m 'docs: record closure research and diagnostic scope'
git add .github/workflows/tripwire-selector-drt-diagnostic.yaml
git commit -m 'ci: run bounded selector routing diagnostic'
git push origin tripwire/closure-8x4
```

Exclude unrelated untracked files and sealed fixtures. Confirm the push-created
run before dispatching manually, so only one diagnostic is launched.
