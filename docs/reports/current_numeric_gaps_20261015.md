# Current numerical evidence: bounded phase 5 audit

This audit covers the design-set comparison in `docs/EVIDENCE.md`,
`architecture_comparison.md`, `g0_results.md` and `g1_results.md`. It does not
inspect or refresh held-out inputs. The current eight-case compiler campaign
is `38852379083` at `ba0cb76`; its outcome was pending when this audit was
prepared. A workflow run starting is not measurement evidence.

Follow-up:38852379083 completed successfully and its native artifacts/images
were independently checked. The current design-set table and C6 now use that
run; dated report banners and scope corrections are applied, stale reproduction
and unit status updated, and unhosted showcase resource details removed from
the judge-facing summary. The physical timing/area limits below remain open.

## Actions after the paired campaign

| Exact remaining claim or presentation | Current evidence problem | Can the eight-case refresh close it? | Required action |
|---|---|---|---|
| EVIDENCE §3 presents G0 `124/86/115/184` and G1 `29/47/70/169` as “Logic cells”, under protocols that place and route. | The source tables are dated local measurements. Failed designs use synthesized demand estimates, not placed LC counts. The summary does not carry that distinction into its table. | Yes, for **current** default design-set compile results, if all eight cases are authenticated. It cannot reproduce those historical revisions automatically. | Replace the current summary with actual refreshed values/run ID. Show placed LCs only for successful cases and separately label synthesis demand for nonfits. Preserve dated historical tables. |
| EVIDENCE §3 and CLAIMS C6 state G0 fits one protocol and G1 fits three. | The G1 side has historical CI coverage; the G0 side is explicitly local in C6. EVIDENCE's nearby historical physical run IDs do not authenticate the paired current compiler matrix. | Yes, for current compiler placement/routing coverage. Every nonfit must have an accepted native diagnostic, not a setup error. | Cite the paired run and source revision; derive the fit count from its actual eight cases. If observed coverage differs, report it rather than treating the historical ratio as an expected result. |
| `architecture_comparison.md` calls the comparison “equal total area”, describes a primitive tile as `0.97×`, and says routing/configuration area are the same because macro and shell are identical. | Equal outer footprints are distinct from component area measurements. Changing macro contents does not establish identical routing or configuration-storage cost. The tile ratio is a historical local measurement. | No. Compiler runs do not measure physical area, total routing cost or shell area. | Keep the outline/placement evidence explicitly historical and linked to physical runs. Remove the unsupported component-equality inference and omit or label the local tile ratio. Do not use this refresh as a new equal-total-area proof. |
| `architecture_comparison.md` says “G1 dominates G0” and gives `53/68 MHz`, with D-030 `52.1` and UART `90.7→100.5`. | These are dated compiler/STA model results, not fresh configured physical rates. The worst-case numbers compare different fitting workload sets. “Dominates” overstates a result with lower worst-case Fmax and no new physical comparison. | It can refresh G0/G1 model Fmax for current successful cases, **not** the D-030 experiment or physical timing. | Present coverage and per-design model estimates separately. Explicitly say the 50 MHz value is an assessment target: the compiler runs with `--timing-allow-fail`, so successful compilation does not itself prove meeting that target. Preserve historical experimental rows as dated outcomes. |
| `g1_results.md` says “Not in the chip yet (the chip is G0)” and retains an “Open” item requesting G1 integration. | These are accurate statements about that September 27 report, but stale as present status; frozen G1 was subsequently integrated. | No new compiler measurement is needed. | Add a historical-status banner and point to the frozen-chip integration run. Avoid rewriting the dated original observations as current results. |
| EVIDENCE §8/§9 and the G1 timing section identify missing original primitive netlist/SPEF timing views. | This is already disclosed correctly. Current model files can be hashed, but provenance hashes cannot reconstruct or validate missing original physical views. | No. | Retain the limitation; recovering matching views or performing a separately qualified new timing experiment is needed for a fresh physical cross-check. Do not claim complete configured/native/SDF timing from the paired compiler run. |
| EVIDENCE §9 repeats local `38/88`, `83/88`, `85` and `91` showcase measurements. | Their wording discloses local/synthesized-shell scope, but those rows still lack a hosted run ID supporting each number. That remains relevant to phase 5's literal “every number linked to a run ID” gate. | No: those showcases are deliberately outside the eight default design-set cases. | Either remove the numeric detail from the judge-facing summary and keep the scoped historical reports, or obtain separately bounded hosted evidence. Do not expand this campaign into unrelated workloads. |

## Already scoped evidence and stale status

`g0_results.md` and `g1_results.md` explicitly say local run, date their results,
name their parameter forms, and describe model timing. Those are historical
records, not falsely claimed hosted measurements; the main repair is to stop
promoting their numbers into an unqualified current summary. The rejected
specializations in `architecture_comparison.md` should likewise stay dated
historical decisions unless rerun deliberately.

EVIDENCE §2's current plain-logic profile is already attached to hosted run
`38820879331` and distinguishes synthesis counts from placed cells. The paired
compiler refresh is a different measurement and should not replace that profile.

The top reproduction paragraph still describes `38777288608`'s omitted image
bytes, and the top status paragraph still says corrected unit discovery awaits
hosted evidence. Later retained evidence already supersedes those status notes
(`38780941472` for actual emitted images; the unit-discovery report for its exact
corrected run/census). These are presentation updates, not reasons to rerun the
paired architecture measurement or to weaken its acceptance checks.

## Acceptance boundary

After a successful, independently inspected eight-case run, the current
design-set LC/fit/model-timing table can have direct hosted evidence. That does
not close the missing physical timing views, qualify compact routing, prove new
equal-area superiority, refresh historical rejected variants, or authenticate
the separate local showcase numbers. Phase 5 also retains its independent
all-workflows-green and final-summary gates. Keep those gates open until their
own evidence exists.
