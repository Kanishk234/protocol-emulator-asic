# TRIPWIRE work log

Newest entry at the top. One entry per work session.
- Keep entries short.
- Evidence means a CI run ID, a test command and its result, or a file path.
- Raw logs are not committed; link to them instead.

## 2026-10-04: Codex (audited repaired-state routing continuation)
Done:
- Downloaded repair 37185455158 and audited fresh comparison/repair metrics: zero setup/hold violations in all corners; 8 inserted buffers, 14 upsized cells, 5 pin swaps; area +120 µm² (~0.023%), instances +8. Slew remains slow 3/typ 1; fanout 164; cap 0. Estimated timing passes, electrical and final routed closure remain open.
- Added separate `gds-repaired-drt-continuation.yaml` and helper: validate successful repaired artifact and pinned inputs, antenna check/repair/check, fresh matched signoff-view corners, then DRT only if setup/hold remain nonnegative. Four threads, five-iteration marker reports, combined 330-minute continuation budget. Candidate/template/config untouched.
- Seven helper regressions pass, including negative post-antenna timing blocking DRT and the final route consuming the correct saved state. YAML/embedded Python and diff checks pass. No new functional equivalence/netlist protocol evidence is claimed.

Checklist:
- No boxes ticked; physical signoff and functional final-netlist evidence remain required.

Next:
- Published CI/helper e2e98aa and audit e2334c8 separately. First dispatch encountered workflow-registration 404; registration check and retry succeeded. Controlled continuation 37187027878 launched against source 37037880327 / repair 37185455158 (queued at dispatch). Inspect antenna/timing gating and routing progress; do not repeat the old unchanged checkpoint replay.

## 2026-10-04: Codex (repair result and remaining priorities)
Done:
- Signoff-aware margin-zero repair 37185455158 completed successfully. Job 111386312253 reports 8 inserted buffers, 14 upsized instances, and zero GRT overflow. Fresh single-corner setup WS: fast 0→0, slow −2.32321→0, typical 0→0 ns. Hold WS after: fast +0.0672144, slow +0.328604, typical +0.161372 ns. These are estimated pre-antenna results, not final routed timing closure.
- Reviewed the Phase 2 exit checklist and prepared a prioritized chat to-do list: inspect repair electrical/area/path metrics, carry the repaired saved state through antenna/DRT with correct timing view, extract/sign off all corners, preserve functional behavior, finalize count/budget and main integration, then rerun complete physical/protocol/main gates. No checklist boxes ticked.
- Initial log/artifact retrieval escalation timed out in automatic review; one read-only job-log retry succeeded. No action remains blocked by approval review.

Next:
- Inspect the complete repaired artifact before selecting the next controlled continuation. No hardware/config adoption based solely on zero estimated WNS.

## 2026-10-04: Codex (post-antenna evidence and signoff-aware repair screen)
Done:
- Inspected both completed artifacts: PnR 37183579900 / signoff 37183581129. Post-antenna slow setup WS +0.853715 ns vs −2.249214 ns; signoff slow TNS −83.5406 ns / 111 violations. Fast/typ signoff setup WS 0, all hold slack positive. Fanout 180, slow slew 1, cap violations 0 after antenna repair.
- Matched worst flop-ending path _49012_→_47080_: signoff adds ~3.103 ns departure/borrowing time with identical downstream cell arcs. This disproves the earlier assumption that the setup-to-latch exception could not affect flop-ending paths; corrected report wording and logged #63. Older final endpoint _48142_ has new estimated signoff slack −1.243498 ns vs older extracted −10.698019 ns (different physical runs).
- Added isolated setup-margin option to the workflow/helper. Prepared signoff-aware slow repair with margin 0, preserving naturally zero-slack latch checks, hold margin, 20 ns and candidate inputs. Five regression tests pass; YAML and diff checks pass. This is a screen, not a candidate constraint change.

Checklist:
- No boxes ticked; physical timing/route/electrical closure remain open.

Next:
- Published CI/helper 0fd6ddb and evidence a990ece separately. Launched signoff-aware margin-zero repair 37185455158 against source 37037880327 (queued at dispatch). Inspect fresh corners, area/buffer cost and GRT overflow; do not promote without routed evidence.

## 2026-10-04: Codex (current workflow status)
Done:
- Current running workflows are main `unit` 37183579933 and 37183385156; none queued. Post-antenna PnR comparison 37183579900 and signoff-constraint comparison 37183581129 both completed successfully. Detailed routing replay is no longer running.

Checklist:
- No boxes ticked; successful diagnostic status alone does not establish timing closure.

Next:
- Inspect both completed post-antenna comparison artifacts and corner/path differences.

## 2026-10-04: Codex (matched post-antenna and constraint-view diagnostics)
Done:
- Added workflow `comparison=postantenna` to report stage 39 vs exact stage-43 DRT input with no repair/routing. Validates ODB/DEF/SDC/powered-netlist references against original stage 44. Added `constraints=pnr|signoff` and helper shared SDC override so both checkpoints use the same timing view.
- Compared saved SDC files: source runs 36799356107 and 37037880327 have identical PnR constraints. Signoff removes only the setup-to-latch-data exception; both retain setup uncertainty 0.25 ns / hold 0.10 ns. Earlier worst path ends at a flop, so this exception alone does not explain its failure. Live latch-starting paths stay timed.
- Validation: five helper regression tests pass; workflow YAML/embedded Python parse; diff checks pass; no outgoing src/info/macro commits. These are estimated GRT timing screens, not final signoff.

Checklist:
- No boxes ticked; hardware inputs unchanged.

Next:
- Published CI/helper b1787d3 and evidence 4667c00 separately. Launched stage-39/stage-43 PnR comparison 37183579900 and signoff-constraint comparison 37183581129 against source 37037880327; both queued at dispatch and serialized by source-run concurrency. Inspect fresh reports before choosing a physical change.

## 2026-10-04: Codex (successful matched corner timing screen)
Done:
- Downloaded successful timing run 37182963688 and inspected comparison JSON plus six fresh single-corner reports. Stage-39 slow setup WS +0.846560 → +1.201990 ns; fast +11.8676 → +12.0141; typ +7.80648 → +8.03823. Setup/hold WNS/TNS and violation counts are zero at all three corners; this is estimated pre-antenna GRT timing, not final signoff.
- Resizer reports no setup/hold violations and zero inserted buffers; it mirrors 14,866 instances and reroutes with zero overflow. Fresh repair area/instances 514,034 µm² / 33,602. Slow slew violations increase 13→15, typ 0→1, fast stays 0. All corners retain 164 fanout violations and zero cap violations. Do not attribute the slack gain to sizing or compare directly with older final-route WNS.
- Recorded measured results in the GDS report and updated bugs #60–62 with passing pinned-tool evidence. Routing geometry analysis remains independent: marker band/net spans support targeted hypotheses but do not establish causality.

Checklist:
- No boxes ticked; final routed timing, electrical limits and physical closure remain open.

Next:
- Prepare matched post-antenna all-corner STA and compare timing constraints/path endpoints/parasitic views with earlier final signoff. Continue locality/pin-access/obstruction analysis while workflows run; no hardware change until a controlled experiment has a measured hypothesis.

## 2026-10-04: Codex (legacy timing config fix and exact placement mapping)
Done:
- Timing retry 37182661906 completed with failure before STA: metadata version 2 rejected the legacy string DIE_AREA. Preserved source metadata version (default 1), recorded bug #62, and added the real legacy DIE_AREA shape to regression checks. Three tests and diff checks pass; no new WNS result.
- Mapped residual hotspot nets to exact post-antenna DEF from source run 37037880327. U0 producer token bit 16 driver at x=872.64 µm serves remote consumers x=518.88–666.24 µm, crossing the marker band; net1677's buffer is above that band; _17270_ has two nearby cells despite twelve marker records. Added coordinates and targeted load/locality hypotheses to the GDS report. Origin counts do not establish density or macro obstructions.

Checklist:
- No boxes ticked; no candidate hardware or timing-constraint changes.

Next:
- Published metadata fix f6111cb and hotspot evidence 7cf3c4c. Pinned-source review identified that STA-only resolved configs omit GRT_ADJUSTMENT; limited that validation to the repair step and published 46227fd (three regression cases pass). Cancelled superseded retry 37182914944 and launched replacement 37182963688 against source 37037880327. Replacement passed setup/checkpoint validation and is executing the comparison; fix commit 46227fd has green lint/test/docs (37182963082/032/086), unit 37182963039 is still running at the check. Obtain actual fresh slow-corner timing before changing critical nets or placement.

## 2026-10-04: Codex (timing-directory fix and routing hotspot analysis)
Done:
- Fetched main and checked Actions headBranch: 319d7d3/lint 37178674680 belongs to `anish_branch`, not main. Corrected the previous entry. Main is still 4652fc1 with green test/lint/docs/unit (37176353137/163/176/184). No integration conflict or newer main hardware change exists.
- Fixed required run-directory creation before LibreLane invocation and made regression CLI checks require it. Three cases pass; diff checks pass. Published CI fix 5109d19 and evidence f829ee5 separately; launched timing retry 37182661906 on f829ee5 (queued at dispatch). This fixes the pre-STA failure in 37176270000; no timing improvement is claimed.
- Parsed routing run 37165048635's snapshots 5–50. Last snapshot has 215 markers (157 shorts, 58 spacing); 203/215 lie in x=500–700 µm, y=300–350 µm, using 50 µm bins. U0 RX producer token bit 16 appears in 20 marker records. Counts are marker records, not independent defects or unique nets. Added snapshot progression/hotspot evidence to the GDS report.

Checklist:
- No boxes ticked; candidate hardware and constraints unchanged.

Next:
- Inspect timing retry 37182661906 fresh corner metrics against source 37037880327. Map the routing hotspot to macro/cell placement before proposing one physical experiment.

## 2026-10-04: Codex (completed diagnostic status)
Done:
- Timing run 37176270000 failed before STA: job log reports that `--force-run-dir runs/postgrt-timing/before-nom_fast_1p32V_m40C` must already exist. Fixed the local helper to create each run directory and tightened the mocked CLI check. Regression tests pass 3/3; `git diff --check` passes. No fresh timing measurements were produced.
- Routing replay 37165048635 failed after the routing timeout. Latest report `tt_um_tripwire.drc-50.rpt` has 215 markers: 157 shorts and 58 spacing; layers M2 184, M3 20, M4 11. This is 12 fewer than the earlier four-thread replay's endpoint of 227, still no completed route/signoff.
- No workflows are running or queued. Run 319d7d3 on `anish_branch` (corrected after checking headBranch) has green test/unit/docs but failed lint 37178674680: Verilator exits on 120 warnings, including UNOPTFLAT in `tt_um_warp` generated fabric files. Remote and local main remain 4652fc1; main test/lint/docs/unit are green; no remote/history changes made in this status check.

Checklist:
- No boxes ticked. Timing-directory correction is local and uncommitted.

Next:
- Publish the local helper correction; the apparent newer main changes belong to `anish_branch`. Analyze saved routing hotspots; repeated identical routing replay has not achieved completion.

## 2026-10-03: Codex (authorized publication of timing diagnostic)
Done:
- User explicitly authorized the commit/push/launch commands, overriding the default Codex git restriction for this action. Rechecked tests (3/3), YAML parsing and `git diff --check`.
- `git log origin/main..main -- src info.yaml macro` was empty before publication: no hardware changes queued that would cancel routing. Committed CI/helper changes separately as 13dce25 (`ci: compare fresh post-GRT timing by corner`). Documentation committed separately as 4a035d6 (`docs: reconcile protocol and timing evidence`). Both commits pushed successfully to main.

- Dispatched corrected timing diagnostic 37176270000 on 4a035d6 with source run 37037880327; confirmed in progress. Existing routing replay 37165048635 remains in progress. Working tree was clean after publication.

Checklist:
- No boxes ticked; actual diagnostic corner measurements remain pending.

Next:
- Inspect run 37176270000 fresh corner metrics when it finishes and routing replay 37165048635 snapshots. Preserve candidate inputs.

## 2026-10-03: Codex (route-free matched timing diagnostic and WNS hypotheses)
Done:
- Replaced the diagnostic workflow's ambiguous `--from`/`--to` range with `scripts/ci/postgrt_timing.py`: explicit resizer-only flow and six before/after single-corner STA flows, four threads, fresh WS/WNS/TNS checks, resolved-config validation and comparison JSON. Optional `--repaired` reuses an archived resizer checkpoint. No DRT step exists in these flows. Recorded bug #60.
- Added regression coverage for fresh repair, saved-repair reuse, and rejection of inherited metrics: `source .venv/bin/activate; pytest -q scripts/ci/test_postgrt_timing.py` passes 3/3. Workflow YAML parsing and `git diff --check` pass. Actual pinned LibreLane/OpenROAD/PDK execution is pending; no local container toolchain is available.
- Inspected fast electrical reports: all 164 fanout violators are clock-tree leaf outputs, not the presumed data cone. Added ranked WNS hypotheses and acceptance criteria to the GDS experiments report: locate stage/corner losses, audit repair's timing view, selective load splitting/sizing, equivalent selection-depth reduction, locality/mapping, and independent CTS analysis. These are unmeasured hypotheses.

Checklist:
- No boxes ticked. No candidate RTL/config/template-job changes, workflow dispatch, commits, or pushes.

Next:
- User commits/pushes the CI/helper and documentation groups, then runs the corrected diagnostic. Before a push while routing is active, check `git log origin/main..main -- src info.yaml macro`. Inspect fresh slow/typical metrics and completed DRT snapshots before choosing one controlled physical change.

## 2026-10-03: Codex (timing diagnostic follow-up)
Done:
- Inspected timing run 37166808611's STA command, environment, and reports. The command invokes pinned LibreLane `sta/corner.tcl` once with three corners loaded; its reports contain only fast. Upstream tag `3.1.0.dev3` explicitly documents this script as one-corner-per-process and selects the first corner before reporting. This explains the missing slow/typical measurements; loading libraries is insufficient.
- Identified useful independent work while routing runs: repair diagnostic endpoint/per-corner reporting, reuse the saved before/after resizer checkpoints for matched STA, and analyze electrical violators. No workflow or hardware changes made; no boxes ticked.

Next:
- Prepare a separate timing-only diagnostic that stops before DRT and explicitly reports each corner on matched checkpoints. Compare critical paths/electrical limits before selecting a physical change; wait for routing snapshots to select a congestion hypothesis.

## 2026-10-03: Codex (protocol evidence reconciliation and diagnostic comparison)
Done:
- Reconciled protocol coverage, claims, bug #59, and GDS experiment status with the passing expanded hardened-netlist run 37144286224. Downloaded its JUnit artifact and verified 22 testcases with no failures/errors/skips. Main unit 37145661022 and latest 37167980192 passed; functional simulation remains distinct from slow-corner timing closure.
- Inspected completed timing screen 37166808611 (failure, ended 2026-10-04 02:33:51 UTC). Its artifact preserves slow-library resizer execution with no setup/hold violations and zero GRT overflow, but fresh mid-PnR metrics only cover fast (setup WS +12.0141 ns, hold WS +0.0490773 ns). Slow/typical metrics are missing and the flow continued into unfinished DetailedRouting. Exact terminal cause is not established from the artifact; do not claim timing improvement.
- Added provenance, fresh timing/electrical, repair cost, five-iteration routing marker, completion, and promotion comparison criteria to `docs/reports/PHASE2_GDS_EXPERIMENTS.md`. Separate post-antenna replay 37165048635 remains running at the latest check; checkpoint validation passed.

Checklist:
- Validation: `git diff --check` passed; venv XML inspection confirmed 22 cases and no failures/errors/skips. No boxes ticked; documentation/evidence changes only. No candidate, RTL, config, workflow, or repository history changes.

Next:
- Inspect completed routing snapshots when available. Correct repeated-STA endpoint selection and explicit per-corner reporting in a separate diagnostic change before another timing screen. Keep the 20 ns target, live configuration timing, same-cycle feedback/DROPPED semantics, and protocols intact.

## 2026-10-03: Codex (current workflow status and immediate next steps)
Done:
- Refreshed GitHub Actions at 2026-10-04 02:15 UTC (2026-10-03 21:15 America/Chicago). Exactly two runs are in progress and none queued: post-antenna DRT 37165048635 (checkpoint validation passed, detailed routing active) and post-GRT timing screen 37166808611 (checkpoint/native corner configuration passed, slow-corner repair and mid-PnR STA step active). `gh run view --log` reports logs unavailable until completion; no live iteration count or fresh timing result can be inferred.
- Latest main `11243a7` test, lint, docs, and unit all passed: 37167980180, 37167980171, 37167980170, and 37167980192. Unit completed at 02:06 UTC.
- Confirmed the user removed the untracked handoff file. The only tracked local modification is this worklog.

Checklist:
- No boxes ticked; no implementation changes or workflow dispatches.

Next:
- While diagnostics run, reconcile stale protocol evidence and prepare comparison criteria for fresh corner STA and DRT markers. Inspect their completed artifacts before selecting another physical experiment; preserve candidate inputs and semantics.

## 2026-10-03: Codex (repository orientation and handoff review)
Done:
- Read `AGENTS.md` and the untracked `PHASE2_GDS_TIMING_HANDOFF.md`; reviewed the required project docs, recent worklog/decisions, Phase 2 evidence, core RTL/model/compiler/host code, verification harnesses, and physical/CI workflows, with a repository-wide file and test inventory.
- Confirmed `main` is at `11243a7`: its TT top remains the Phase 0 counter (D-047), while full-chip tests use `trw_chip` and physical experiments pin R4 candidate `3393eea`. Keep the candidate's 20 ns clock, D-066 timed live configuration, protocol behavior, and same-cycle feedback/drop accounting intact.
- Noted stale evidence wording: the handoff and protocol coverage audit leave expanded hardened-netlist L3 pending, while the worklog and Phase 2 summary record 22 passing cases in run 37144286224. D-056 concerns hold uncertainty; D-049 defines the resource floor, with final counts still undecided. No evidence documents were reconciled in this orientation session.
- No tests, remote status refresh, workflow dispatch, implementation changes, commits, or pushes performed. Run states in the handoff remain historical observations.

Checklist:
- No boxes ticked; Phase 2 remains open.

Next:
- When physical work resumes, refresh runs 37165048635 and 37166808611 and inspect completed artifacts for persistent DRT markers and fresh all-corner STA before selecting a follow-up experiment. Reconcile evidence wording against the corresponding artifacts.

## 2026-10-03: Codex (phase 2: repair timing-screen corner configuration)
Done:
- Pushed the post-antenna DRT and post-GRT timing workflows with their evidence updates as `90de9b7` and `22bb1aa`, authored by Krithik4. `test`, `docs`, `lint`, and `unit` all passed on the pushed commit (runs 37165038069, 37165038087, 37165038076, and 37165038086).
- Fixed the timing workflow's corner-list serialization and pushed `7ead414` and `f968a68`, authored by Krithik4. On `f968a68`, `test`, `docs`, and `lint` passed (37166801957, 37166801984, 37166801969); `unit` 37166801989 is still running.
- Started the four-thread post-antenna DRT replay [37165048635](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37165048635) from run 37037880327's stage 43 checkpoint. It remains in detailed routing; no final route result is available yet.
- Timing screen [37165052112](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37165052112) failed before producing STA. LibreLane parsed the CLI corner-list overrides as lists containing bracketed strings, so OpenROAD could not find `sg13cmos5l_buf_4`. The uploaded artifact confirms this in the resizer step config and `_env.tcl`; this is an experiment configuration failure, not a design timing result.
- The corrected timing screen [37166808611](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37166808611) passed checkpoint validation and native JSON corner configuration; `OpenROAD.ResizerTimingPostGRT` and mid-PnR STA are currently running. It uses the same saved checkpoint and no candidate source inputs changed.
- Traced the archived slow-corner path in `/tmp/r4-gds-36799356107/GDS_logs/runs/wokwi/55-openroad-stapostpnr/nom_slow_1p08V_125C/max.rpt`. U0's `idle` latch feeds TX/BITSYNC output logic, returns through driven-pad selection into `a_in`, then passes through RX/fabric logic to C2 `dropped[16]` D. Arrival is 31.722853 ns, required time 21.024834 ns, slack −10.698019 ns. One arc is 2.399 ns with 3.146 ns output slew; this supports focusing on the feedback/control and fanout path rather than only the DROPPED incrementer.
- Ran isolated D-066-timed Yosys/OpenSTA screens on exact RTL `3393eea9a58c5cad9077cc360a8515d0e5ec8284` under `/tmp/r4-abc-delay-screen-20261003/`. Baseline reproduced area 391,112.442 µm² and worst-flop slack +9.154 ns typical / +3.344 ns slow. Direct ABC `-D` targets of 15,000, 8,000 and 3,000 ps all produced the same mapped-netlist SHA (`93f4af5c…`) and unchanged area/slack. This local option did not change mapping; it does not test LibreLane's separate `SYNTH_STRATEGY=DELAY` setting.

Checklist:
- No boxes ticked. The corrected timing screen and DRT replay have not completed.

Next:
- Inspect the fresh STA/resizer output from 37166808611 and marker/final-route output from 37165048635 when they finish; use them to select one justified follow-up experiment.
- Continue timing screens only on isolated copies; keep the active candidate at 20 ns with all protocol behavior, D-066 paths, and same-cycle DROPPED accounting intact.

## 2026-10-03: Codex (phase 2: diagnose DRT timeout and prepare corner-aware timing screen)
Done:
- Inspected corrected post-GRT resizer run [37162483954](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37162483954) for candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` (2 lanes, 4 units; 20 ns; 56% density). It honored `GRT_ADJUSTMENT=0.16`; pre- and post-resizer GRT had zero overflow. Wirelength changed 2,465,539 → 2,474,553. The resizer used the typical default corner, reported no setup/hold violations, made no cell changes, and did not refresh the saved slow-corner WNS (−5.0436 ns).
- Confirmed the pinned LibreLane 3.1.0.dev3 release supports `RSZ_CORNERS` for resizer steps and per-corner mid-PnR STA with step-level aggregation. Updated the isolated timing-experiment workflow to target slow-corner repair, then run fresh post-repair mid-PnR STA across fast, slow, and typical corners using global-route estimated parasitics; the workflow asserts all resolved corner settings and requires fresh setup/hold slack metrics for all three corners. The candidate RTL and active GDS inputs remain unchanged. This experiment has not run yet.
- Downloaded the completed DRT replay [37144286178](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37144286178). It hit the workflow's 330-minute step timeout after 46 completed iterations numbered 0–45, with 227 markers remaining (61 spacing violations and 166 shorts). The prior unset-thread replay [37102837764](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37102837764) reached 277 markers after 35 rounds. This four-thread replay made more progress, but no detailed-route output state was saved. Artifact log and config are under `/tmp/gds-postantenna-37144286178/gds-postantenna-drt-37144286178/runs/postantenna-drt/`.
- Prepared the isolated post-antenna continuation workflow to set `DRT_SAVE_DRC_REPORT_ITERS=5`, so a same-checkpoint replay can reveal where the remaining route markers are concentrated. It changes diagnostic artifact generation only; candidate RTL and active hardening inputs remain untouched.
- Main `test`, `docs`, `lint`, and `unit` all passed on `467012a`: runs 37162474601, 37162474600, 37162474609, and [37162474623](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37162474623). The latest `unit` completed successfully, including the chip-level Icarus job.
- Updated `docs/reports/PHASE2_GDS_EXPERIMENTS.md` with the DRT timeout result, corrected screen, and next experiments. No checklist boxes changed.

Checklist:
- No boxes ticked. The current route replay is not full hardening signoff, and no slow-corner resizer result exists yet.

Next:
- Run the same-checkpoint DRT replay with reports every five iterations; use the remaining marker coordinates and nets to select one controlled route experiment.
- Run the updated isolated resizer workflow with its slow-corner override and fresh all-corner STA; compare setup/hold slack, cell area, and global-route overflow.
- Commit and push the prepared workflow and evidence updates, then dispatch the marker-report DRT replay and the slow-corner post-GRT timing screen. Continue preserving 20 ns, D-066 timed configuration paths, protocol support, and same-cycle DROPPED accounting.

## 2026-10-03: Codex (phase 2: timing-repair experiment prep while DRT runs)
Done:
- Rechecked the locally saved full-run artifact for candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` (2 lanes, 4 units; 20 ns; 56% density). Its stage 39 global-route report ends with zero overflow on every layer (`/tmp/gds-37037880327/runs/wokwi/39-openroad-globalrouting/openroad-globalrouting.log`).
- Confirmed the same run had `RUN_POST_GRT_DESIGN_REPAIR=false` and `RUN_POST_GRT_RESIZER_TIMING=false`; flow log records both steps skipped. The currently running replay [37144286178](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37144286178) starts at post-antenna stage 43 and runs detailed routing only, so it cannot measure a post-GRT timing-repair change.
- Added `.github/workflows/gds-postgrt-timing-experiment.yaml` and pushed it as `4e5f64d` (Krithik4). The first timing screen [37161186827](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37161186827) completed, but the replay fell back to `GRT_ADJUSTMENT=0.30` instead of the saved checkpoint's 0.16. Its resizer report moved setup WNS from −0.186 ns to +0.034 ns with one gate resize, one setup buffer, two pin swaps, and 21 hold buffers; area increased by 435.46 µm² (0.085%). Its second global route had 2,815 overflow. The slow-corner metric stayed at −5.044 ns without a fresh slow-corner report. This is a confounded screen, not a pass.
- Corrected the workflow to explicitly override and assert `GRT_ADJUSTMENT=0.16`, matching the saved checkpoint. The report and workflow change pass `git diff --check`; workflow YAML and embedded Python syntax were validated earlier. Push these corrections and rerun the bounded screen before using any timing or route result.
- Main CI on the latest work-log-only push: `test` 37161474600, `lint` 37161474579 and `docs` 37161474582 passed; `unit` 37161474583 has model job green and both RTL jobs still running. Detailed-route replay [37144286178](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37144286178) remains in DRT. No RTL, `src/config.json`, `info.yaml`, macro, or active hardening input changed.

Checklist:
- No boxes ticked; this is saved-artifact analysis and experiment preparation, not routed signoff evidence.

Next:
- Push the corrected workflow/report, rerun the stage 39 resizer screen with the 16% adjustment, and inspect the actual route/timing metrics. Preserve the 20 ns clock, D-066 timed configuration paths, and same-cycle DROPPED accounting.

## 2026-10-03: Codex (phase 2: whole-chip timing screen while DRT runs)
Done:
- The expanded 22-case hardened-netlist L3 workflow 37144286224 passed on the matching R4 netlist.
- Main `test`, `docs`, `lint`, and `unit` all passed on commit `62fa04d`: runs 37145661322, 37145660996, 37145661033, and 37145661022. Ticked Phase 2 box 9 with this evidence; rerun after the hardware switch.
- Post-antenna route replay 37144286178 validated the existing checkpoint and remains in detailed routing with `OPENROAD_THREADS=4`; it has run about 4 h 18 min so far. It is route-only, not full GDS signoff. No active GDS inputs or source files changed.
- Ran matched D-066-timed `bash synth/chip/run_chip.sh 20` screens against exact source `3393eea9a58c5cad9077cc360a8515d0e5ec8284` in isolated `/tmp` copies. Baseline area/slack: 391,112.442 µm², +9.154 ns typ / +3.344 ns slow. SHIFT_RX factoring: 392,762.563 µm², +7.866/+1.360 ns. Pad-output mux: 391,278.384 µm², +8.279/+2.001 ns. Pad-input selector: 389,852.757 µm², +8.599/+2.501 ns. RX + pad-output combined: 392,878.647 µm², +8.529/+2.376 ns.
- Although earlier checks improved selected latch-to-DROPPED paths, all four screens worsened the whole-chip worst slow slack. They use ideal clocks and no wire parasitics; none qualifies as a routed timing improvement. Did not run additional unit/L2 checks on the combined form after its whole-chip screen regressed. Details are in `docs/reports/PHASE2_GDS_EXPERIMENTS.md` and the isolated output directories listed there.

Checklist:
- Box 9 ticked: all four main workflows passed on `62fa04d` (run IDs above).
- No other boxes ticked. The route replay remains active and is not full GDS signoff.

Next:
- Review the completed route replay when it finishes; compare remaining markers and runtime with the prior timed-out attempt.
- For timing, use the route result and the archived high-fanout configuration cone to guide an isolated resizer/placement or narrower logic/load experiment. Preserve 20 ns, D-066 timed paths, protocol behavior, and same-cycle DROPPED accounting.

## 2026-10-03: Codex (phase 2: close L3 assertion gaps and diagnose DRT timeout)
Done:
- Reviewed completed post-antenna continuation [37102837764](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37102837764): checkpoint validation passed, but DRT hit its 330-minute limit. It started with 32,500 route markers, completed 35 optimization rounds and reached 277 markers; round 36 was partial. No final route state or signoff was produced. The flow used `OPENROAD_THREADS=null`.
- Reviewed expanded gate-level L3 run [37101678657](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37101678657) and unit runs [37102835070](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37102835070) and [37103768779](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37103768779): each exposed the same two sigrok assertion mismatches in 1-Wire and LIN. The newest run's Python/model job passed; both RTL simulator jobs failed only on these annotations after the protocol reference checks had passed. Corrected the assertions in `test_internal/chip/test_l3.py` to match sigrok's available annotations. Corrected-test CI reruns are now active as 37144273163 and 37144286224.
- Downloaded the latest unit artifacts to `/tmp/unit-37103768779-icarus/` and `/tmp/unit-37103768779-verilator/`; JUnit confirms the 1-Wire decoder emitted reset/presence and `Read ROM` but no slave ROM byte annotation, while LIN emitted frame ID `0x10`, valid parity, data and checksum (the test incorrectly expected protected ID `0x50`). The same run's `test`, `lint`, and `docs` workflows passed (37103768797, 37103768813, 37103768803). GitHub reports no queued or in-progress runs.
- Added an explicit 2/4-thread input to `.github/workflows/gds-postantenna-drt-continuation.yaml`, defaulting to 4, and pass it as `OPENROAD_THREADS` to LibreLane. The rerun will use the same source checkpoint and candidate, changing only the thread count.
- Removed the now-unused LIN `pid_of` import. Focused 1-Wire READ ROM and LIN commander tests passed on both Verilator and Icarus with `TRIPWIRE_SKIP_SIGROK=1` (4 simulator/test runs). `python -m py_compile test_internal/chip/test_l3.py`, workflow YAML parsing and the `OPENROAD_THREADS` wiring assertion passed; `git diff --check` passed.
- Committed and pushed as Krithik4: test `1a8d6f8`, CI workflow `9db6f37`, and docs/bug ledger `9be7d40`. Push checks: `test` 37144273130 and `lint` 37144273157 passed; `unit` 37144273163 and `docs` 37144273224 are running.
- Dispatched four-thread post-antenna replay [37144286178](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37144286178) and expanded hardened-netlist L3 [37144286224](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37144286224). Both validated their inputs; route replay is in detailed routing and L3 is running.

Checklist status:
- Box 9 remains unchecked: latest completed unit run 37103768779 passed the model job but failed both RTL simulator jobs on the 1-Wire/LIN sigrok assertions; corrected-test run 37144273163 is in progress. No boxes were ticked in this session; the million-clock L2 result remains valid.

Next:
- Review `unit` 37144273163, `docs` 37144273224, and hardened-netlist L3 37144286224 when they finish. Box 9 stays unchecked until the full main `unit` workflow is green.
- Review four-thread route replay 37144286178. A clean DRT result would still need full hardening for routed timing, DRC/LVS/antenna, precheck, gate-level tests and viewer output.
- Keep timing optimization focused on the slow-corner `idle` configuration latch to `dropped[16]` path from the last fully routed candidate; preserve 20 ns, D-066 timing, and same-cycle DROPPED accounting.

## 2026-10-03: Codex (phase 2: push expanded L3 checks and prepare post-antenna DRT)
Done:
- Committed and pushed the IR NEC state initialization, expanded 22-case L3 suite, and updated evidence as `68adf20`, `2c03bd3`, and `a9b9f26`, authored by Krithik4. No hardware input changed; the hardware-only ahead-of-main check was empty.
- Main `test`, `unit`, `lint`, and `docs` runs on `a9b9f26` are 37101626363, 37101626314, 37101626351, and 37101626299. Later runs on `9d42f3f` are 37102473180, 37102473194, 37102473168, and 37102473188; runs on `2a3845b` are 37102835114, 37102835070, 37102835113, and 37102835372.
- Dispatched expanded hardened-netlist L3 run [37101678657](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37101678657) against the earlier netlist from GDS run 36799356107, which matches candidate RTL `3393eea9a58c5cad9077cc360a8515d0e5ec8284`. This run can establish protocol function, not timing or route signoff.
- Added and pushed `.github/workflows/gds-postantenna-drt-continuation.yaml` (`d9bfcef`) to resume detailed routing from run 37037880327's post-antenna stage 43. Local artifact validation confirmed that stage 43's ODB/DEF/SDC/netlist references match the original DRT input, with 33,755 instances and `GRT_ADJUSTMENT=0.16`. The first attempt, [37102555758](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37102555758), stopped at artifact download because the manual run artifact is named `GDS_logs-37037880327`; fixed the workflow name in `8cb6016` and recorded the failure in `2a3845b`. Retry [37102837764](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37102837764) downloaded the artifact, passed checkpoint validation, and entered detailed routing.
- Screened a generic one-hot source-valid/sequence/load selector in `trw_chan_port` on isolated archives of exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`. With the current D-066-timed STA helper, baseline area/slack were 391,112.442 µm² and +9.154/+3.344 ns typ/slow; the variant was 391,175.984 µm² and +8.494/+2.251 ns. Rejected before simulation or routing. The test RTL is confined to `/tmp/r4-fabricmux-opt-20261003/`; active sources were unchanged.
- Reproduction command in each temporary tree: `source .venv/bin/activate && bash synth/chip/run_chip.sh 20`.

Checklist boxes ticked:
- None. These tests and route diagnostics do not complete the Phase 2 timing, signoff, or budget gates.

Next:
- Review the main CI runs on `a9b9f26`, `9d42f3f`, and `2a3845b`, plus expanded gate-level run 37101678657; resolve any failures before proceeding.
- Monitor continuation 37102837764 and expanded gate-level L3 run 37101678657. The route-only result does not replace a full GDS signoff run.
- Continue route-aware timing work with all configuration paths timed, the 20 ns target intact, and no added DROPPED latency. The one-hot source-select trial regressed and should not be promoted.

## 2026-10-02: Codex (phase 2: status review and next actions)
Done:
- Rechecked `main` at `3720983` against `origin/main`. The pending changes are the IR NEC firmware initialization, expanded L3 tests, and their evidence/docs; `git diff --check` is clean.
- Confirmed main test, unit, lint and docs runs 37066391043, 37066391060, 37066391039 and 37066391070 passed, with no GitHub workflows currently in progress.
- Confirmed full GDS run 37037880327 failed at its 330-minute detailed-route timeout. The earlier hardened netlist run 36799356107 used the same candidate RTL SHA, so the updated L3 suite can provide gate-level functional evidence against it; it does not establish timing or routing signoff.
- No Phase 2 checklist box changed. No commit or push was made; repository instructions reserve those actions to the user.

Next:
- Commit and push the pending firmware, test and documentation groups; inspect the resulting `test`, `unit`, `lint` and `docs` runs.
- Run the expanded L3 suite on matching candidate netlist 36799356107, then continue route experiments from the post-antenna checkpoint in 37037880327 and separately optimize routed all-corner timing without relaxing 20 ns or D-066 behavior.
- Only promote a candidate after L2, both RTL injections, the full protocol suite, and full GDS signoff pass; then repeat the official hardening and close the remaining area/count and Phase 2 evidence items.

## 2026-10-02: Codex (phase 2: analyze 16% hardening timeout and complete IR NEC RTL check)
Done:
- Retrieved and reviewed the artifact for full hardening [37037880327](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37037880327), exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` (2 lanes, 4 pin units, U0 full; 20 ns; 56% density; `GRT_ADJUSTMENT=0.16`). The LibreLane hardening job timed out at 330 minutes during DRT. GRT had zero overflow (capacity 601,423; demand 255,230; usage 42.44%). After 13 DRT rounds, 1,246 violations remained; the next round was cut off. Last counts: 345 M2 / 53 M3 / 2 M4 spacing, 697 M2 / 106 M3 / 43 M4 shorts. Antenna repair reduced 113 markers to zero, adding 141 diodes plus jumpers.
- Distinguished the run's intermediate STA from final timing: post-antenna, pre-DRT typical setup slack was +7.81655 ns and hold slack +0.171227 ns, with zero typical violations; no routed parasitics or slow/fast signoff exists. `precheck` and `gl_test` were skipped, and the run produced no GDS/viewer result.
- Compared the DRT input against continuation [36951141285](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36951141285): the failed full run entered DRT with 33,755 instances / 514,867 µm² after antenna repair, while the earlier continuation used the pre-antenna GRT checkpoint at 33,602 instances / 514,034 µm². This explains why the earlier zero-violation DRT result is not an apples-to-apples comparison; it does not prove antenna repair caused the timeout. The next route experiment should resume from the post-antenna state.
- Added PS/2, 1-Wire, SWD, JTAG, SMBus, HDLC, LIN, CAN and IR NEC repeat L3 tests to the existing twelve-case suite. Nine non-IR tests pass under both simulators; the IR test passes on the exact candidate under Verilator and Icarus. The IR test caught uninitialized decoder SRAM state in `programs/ir_nec.trw`; added a BOOT routine that initializes words 240–243 before input processing and logged BUGS #58. The existing tripsim IR frame/repeat test passes after the firmware change.
- Updated `docs/reports/PHASE2_GDS_EXPERIMENTS.md`, `docs/reports/PHASE2_PROTOCOL_COVERAGE.md`, `docs/summaries/PHASE2.md`, and BUGS #58 with the run result and evidence. No RTL, config, info, macro, or checklist count changed. No Phase 2 box was ticked.
- Current main `test`, `lint`, `docs`, and `unit` workflows are green (runs 37066391043, 37066391039, 37066391070, 37066391060); a live-run query returned no workflows in progress.

Commands and results:
- `source .venv/bin/activate && TRIPWIRE_SKIP_SIGROK=1 TRIPWIRE_SPEC_FILE=/tmp/r4-bitsync-work/tools/tripwire_spec.py make -C test_internal/chip SIM=verilator SRC_DIR=/tmp/r4-bitsync-work/src SIM_BUILD=sim_build/r4_l3_ir_verilator COCOTB_TEST_MODULES=test_l3 COCOTB_TEST_FILTER=test_l3_ir_nec_repeat_rx COCOTB_RESULTS_FILE=results_l3_ir_fixed_verilator.xml` — PASS, 1/1, 86.20 s.
- Same command with `SIM=icarus`, `SIM_BUILD=sim_build/r4_l3_ir_icarus`, and `COCOTB_RESULTS_FILE=results_l3_ir_fixed_icarus.xml` — PASS, 1/1, 465.34 s.
- `source .venv/bin/activate && PYTHONPATH=tools:tools/kernels pytest -q tools/kernels/tests/test_simple_protocols.py::test_ir_nec_rx_frames_and_repeat` — PASS, 1 test in 210.48 s.
- `source .venv/bin/activate && python -m py_compile test_internal/chip/test_l3.py`; `git diff --check` — clean.
- Artifact downloaded to `/tmp/gds-37037880327/`; detailed report is in `docs/reports/PHASE2_GDS_EXPERIMENTS.md`.

Checklist boxes ticked:
- None. The 16% hardening did not finish DRT or final signoff; the added protocol tests do not yet have hardened-netlist evidence.

Next:
- Compare/resume detailed routing from run 37037880327's post-antenna checkpoint before scheduling another full hardening. Then run sigrok-enabled CI and the expanded suite on a successfully hardened netlist. Preserve 20 ns, all protocol support and D-066 timed configuration paths.

## 2026-10-02: Codex (phase 2: keep D-066 paths timed in pre-layout STA)
Done:
- While hardening 37037880327 runs, audited the standalone STA scripts and found `set_false_path -from $latches` hiding legal live pin-configuration-to-unit-state paths under D-066. Removed the exception from the whole-chip, R4 spike, and pin-unit helpers; `synth/pin` now runs only with configuration latch outputs timed. Logged the issue as BUGS.md #57.
- Ran the corrected `synth/chip/run_chip.sh 20` in `/tmp/r4-sta-d066`, an isolated copy of exact candidate source `3393eea9a58c5cad9077cc360a8515d0e5ec8284`. Latch outputs stayed timed. Worst latch-startpoint flop slack was +9.154 ns typ / +3.344 ns slow; the slow path starts at U0 config word 0 bit 1 and ends at U0 TX `eq[14]`. This is pre-layout, without placement or routed parasitics.
- Compared the old STA Tcl on the same mapped netlist: its blanket false path hid the configuration path and reported the SRAM path at +10.442 ns typ / +4.828 ns slow. Historical `run_chip.sh` timing values using that helper do not include the D-066 path.
- Expanded hardened-netlist L3 run [37051434072](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37051434072) passed 12/12 under Icarus 13 on GDS netlist 36799356107 for the same candidate SHA. Main `test`, `docs`, `lint`, and `unit` passed on `56a71ea` (runs 37053242291, 37053242296, 37053242412, and 37053242391).
- Full 16% hardening [37037880327](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37037880327) remained in LibreLane step 11 at the latest query (20:01 UTC); its hardware inputs are unchanged. No RTL, `src/config.json`, `info.yaml`, or macro files changed. No Phase 2 box was newly ticked.

Commands and results:
- `bash synth/chip/run_chip.sh 20` in `/tmp/r4-sta-d066` with exact candidate `src/` and corrected `sta_chip.tcl` — PASS; typ +9.154 ns, slow +3.344 ns, latch outputs included as timing startpoints.
- Old Tcl comparison against the same `net_sta.v` and IHP libraries — reported SRAM path typ +10.442 ns / slow +4.828 ns; confirms the old exception concealed the D-066 path.
- `git diff --check` and `bash -n synth/chip/run_chip.sh synth/pin/run_pin.sh spikes/r4_floorplan/check_local.sh` — clean.

Checklist boxes ticked (evidence):
- None newly ticked. Existing box 11 evidence now includes BUGS.md #57; routed timing/signoff remain unproven by this pre-layout STA run.

Next:
- Finish and inspect hardening 37037880327. If it produces a viable route, rerun the expanded L3 suite against that exact hardened netlist. Use routed all-corner timing—not this pre-layout estimate—to select the next timing experiment.

## 2026-10-02: Codex (phase 2: correct reduced-candidate L3 map and add I2S)
Done:
- Confirmed the active R4 source checkout is exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`: 2 lanes, 4 pin units, U0 full, 20 ns, 56% placement target. Its temporary worktree's unrelated `test/` changes were left untouched.
- The first I2S RTL check showed no BCLK because `test_internal/chip/chiplib.py`'s ordinary loader encodes the frozen 3-lane/6-unit fabric selectors, while the R4 candidate uses its generated 2-lane/4-unit selectors. Added an optional `TRIPWIRE_SPEC_FILE` adapter in `test_internal/chip/test_l3.py` to encode candidate consumer/producer connections by the candidate's logical map, then start the loaded program. The standard main-shaped loader remains the default.
- Logged the reduced-candidate loader mismatch as BUGS.md #56; the optional generated-map adapter is the check/fix for it.
- Ran the complete 12-case L3 suite against the exact candidate with the adapter. Verilator: 12/12 passed in 185.24 s; Icarus 12: 12/12 passed in 1,171.39 s. Cases cover UART TX/RX, MIDI, SPI controller/target, I2C controller/target, DMX, WS2812, DShot, servo PWM, and I2S. I2S checks full-duplex 16-bit stereo at 48/96/192 kHz against `I2SADC` and `I2SReceiver`. Focused I2S also passed on main's 3-lane/6-unit RTL under Verilator (1/1, 10.32 s).
- Local tests set `TRIPWIRE_SKIP_SIGROK=1` because the WSL sigrok setup cannot decode locally; the expanded sigrok legs still need CI confirmation. No matching hardened-netlist L3 evidence exists for the new cases.
- Final focused candidate I2S rerun after the adapter's path validation change passed under Verilator: 1/1, 11.10 s, with the generated 2-lane/4-unit map.
- Updated `.github/workflows/l3-hardened-gl.yaml`: it accepts the exact candidate SHA and GDS artifact run ID, runs the current expanded L3 test module from `main` against that netlist, and supplies the candidate's generated compact fabric map. YAML parsing and `bash -n` on all five embedded shell blocks passed. The updated workflow was dispatched as run [37051434072](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37051434072), using candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` and GDS artifact `36799356107`; at the latest query (19:15 UTC) its expanded gate-level suite was running.
- Full 16% hardening run [37037880327](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37037880327) remains in LibreLane step 11. At the latest query (2026-10-02 19:15 UTC), setup and candidate validation had passed, but the hardening step was still active and GitHub withheld its logs. Its only flow override is `GRT_ADJUSTMENT=0.16`; the pinned candidate/config inputs are unchanged.
- Pushed test and evidence commits `97f11ad` and `39b8161` as Krithik4. Main-shape unit run [37048872125](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37048872125) passed all 12 L3 cases under Icarus and Verilator with sigrok enabled; each uploaded chip result has 18 tests and zero failures. The candidate-specific compact-map suite passed 12/12 under both simulators locally with sigrok skipped. On newer `main` SHA `89b4187`, test 37050001658, docs 37050001720, lint 37050001830, and unit 37050001629 all passed; the Icarus chip job completed at 19:14 UTC.
- Updated `docs/reports/PHASE2_PROTOCOL_COVERAGE.md` and `docs/summaries/PHASE2.md`. `git diff --check` passes, and `git log origin/main..main -- src info.yaml macro` is empty. No Phase 2 checklist box was ticked.

Commands and results:
- `source .venv/bin/activate && TRIPWIRE_SKIP_SIGROK=1 TRIPWIRE_SPEC_FILE=/tmp/r4-bitsync-work/tools/tripwire_spec.py make -C test_internal/chip SIM=verilator COCOTB_TEST_MODULES=test_l3 SRC_DIR=/tmp/r4-bitsync-work/src SIM_BUILD=sim_build/vl_l3_candidate_correctmap COCOTB_RESULTS_FILE=results_l3_candidate_correctmap.xml` — 12 passed.
- Same command with `SIM=icarus`, `SIM_BUILD=sim_build/icarus_i2s_r4`, and `COCOTB_RESULTS_FILE=results_l3_candidate_correctmap_icarus.xml` — 12 passed.
- `source .venv/bin/activate && TRIPWIRE_SKIP_SIGROK=1 COCOTB_TEST_FILTER=test_l3_i2s make -C test_internal/chip SIM=verilator COCOTB_TEST_MODULES=test_l3 SRC_DIR=/home/younix/protocol-emulator-asic/src SIM_BUILD=sim_build/vl_i2s_main COCOTB_RESULTS_FILE=results_i2s_main.xml` — main-shape I2S passed.
- Workflow validation: `.github/workflows/l3-hardened-gl.yaml` parsed with PyYAML and all five embedded shell blocks passed `bash -n`; `git diff --check` is clean.

Checklist boxes ticked (evidence):
- None. These are RTL protocol checks; the active full hardening, matching hardened-netlist checks, and team decisions remain open.

Next:
- Inspect the expanded hardened-netlist L3 result from run `37051434072`. Monitor hardening `37037880327`; when it completes, inspect routed WNS/TNS per corner, congestion, DRC/LVS/antenna, precheck, gate-level result, and viewer. Main CI is green on `89b4187`. Keep 20 ns and protocol behavior unchanged.

## 2026-10-02: Codex (phase 2: repair expanded L3 CI checks)
Done:
- Pushed four author-attributed commits to `main`: `7957114` (L3 tests), `d69f3cf` (WS2812 firmware), `ccd7994` (protocol and physical-design evidence), and `9941a81` (manual 16% GRT workflow). No RTL, config, info, macro, or hardening input changed.
- On CI run [37032034520](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37032034520), test, model/unit, lint, and docs jobs passed. The Verilator RTL artifact `/tmp/unit-37032034520-verilator/chip/results_vl.xml` identified two assertion issues: PWM sigrok only reported the first measured cycle because the VCD ended at the final rising edge; the I2C-target waveform correctly had five START/STOP transactions (four writes including the wrong-address NACK, plus one read), while the test expected three. The Icarus RTL job is still running on the earlier commit; the full unit workflow is not green.
- Updated `test_internal/chip/test_l3.py` to add a terminal falling edge to the sparse PWM VCD and expect five I2C-target START/STOP events. Focused Verilator tests for servo PWM and I2C target passed locally with `TRIPWIRE_SKIP_SIGROK=1`. Local sigrok decoding is unavailable in this environment; the CI sigrok-enabled run must confirm these fixes.
- `git diff --check` passed. No Phase 2 checklist box was ticked.

Checklist boxes ticked (evidence):
- None; the expanded RTL suite has a known failure and the full 16% hardening has not run.

Next:
- Let run 37032034520 finish and inspect the Icarus artifact. Commit and push the two test fixes, require a green unit workflow on that revision, then dispatch the full hardening workflow with GRT adjustment 16% and the pinned R4 candidate. Review final routed setup/hold and all signoff jobs.

## 2026-10-02: Codex (phase 2: 16% detailed route and servo PWM RTL)
Done:
- Reviewed DRT-only continuation [36951141285](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36951141285) for candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` (2 lanes, 4 units, U0 full; 20 ns; density 56%). It completed successfully in 3 h 48 min total; detailed routing took 3 h 45 min and ended with 0 router violations, 0 final route DRC markers, and 1,887,085 µm detailed wirelength. The workflow skipped post-route parasitic extraction/STA, GDS stream-out, full DRC/LVS/antenna, precheck, gate-level tests, and viewer; it is not full GDS signoff. Artifact: `/tmp/drt-continuation-36951141285/`.
- Added `test_l3_servo_pwm` in `test_internal/chip/test_l3.py`. On the exact candidate, it passed under Verilator (34.66 s) and Icarus 12 (292.51 s): UO0 emitted a 1.5 ms pulse, then a 1.0 ms pulse after an early host update; both periods were exactly 1,000,000 clocks (20 ms). Local command, after temporarily copying the current L3 test/helper into the candidate checkout and restoring them: `TRIPWIRE_SKIP_SIGROK=1 make -C /tmp/r4-bitsync-work/test_internal/chip SIM=verilator RTL_DIR=/tmp/r4-bitsync-work/src COCOTB_TEST_MODULES=test_l3 COCOTB_TEST_FILTER=test_l3_servo_pwm SIM_BUILD=sim_build/servo_l3_verilator COCOTB_RESULTS_FILE=results_servo_l3_verilator.xml`; repeat with `SIM=icarus`, `SIM_BUILD=sim_build/servo_l3_icarus`, and `COCOTB_RESULTS_FILE=results_servo_l3_icarus.xml`. Local sigrok was skipped; the test writes a sparse PWM VCD for CI decoding.
- Checked host-update timing against tripsim. With an 865-clock delay approximating the candidate SPI host write, a width update sent after a pulse falls misses the already staged frame; both model and RTL apply it on the following frame. No protocol bug was inferred. The test sends early enough in the frame to check the documented next-frame update.
- Updated `docs/reports/PHASE2_PROTOCOL_COVERAGE.md`, `docs/reports/PHASE2_GDS_EXPERIMENTS.md`, and `docs/summaries/PHASE2.md`. Changed `.github/workflows/gds-grt-adjustment-experiment.yaml` to accept a manual 12% or 16% flow-only setting, defaulting to 16%; YAML parsing and input/env consistency checks passed. The workflow was not dispatched.
- `git diff --check` passed. No Phase 2 checklist box was ticked. No RTL, `src/config.json`, `info.yaml`, macro, or hardening input changed. The candidate temp checkout was restored; its pre-existing top-level test changes were left untouched.

Checklist boxes ticked (evidence):
- None. The DRT-only result is not full signoff, and local protocol tests are not hardened-netlist evidence.

Next:
- After the workflow edit reaches `main`, run a full 16% hardening with the 20 ns clock and pinned R4 candidate. Review actual routed all-corner setup/hold, DRC/LVS/antenna, precheck, gate-level results, and viewer output before any checklist update.
- Run the expanded protocol suite with sigrok in CI and on the resulting hardened netlist; continue covering remaining model-verified programs.

## 2026-10-01: Codex (phase 2: extend RTL protocol coverage)
Done:
- Added complete-program MIDI TX, SPI-target, I2C-target, DMX, WS2812 and DShot checks in `test_internal/chip/test_l3.py`. The ten cases cover required UART/SPI/I2C controller tests plus MIDI, SPI/I2C targets, DMX, WS2812, and DShot at 150/300/600/1200 kbit/s.
- On exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`, all ten L3 cases passed across both simulators. Verilator: seven-test module passed 7/7, with focused DMX/WS2812/DShot tests passing. Icarus: six UART/SPI/I2C module tests passed 6/6, with focused MIDI/DMX/WS2812/DShot tests passing. Local command prefix: `TRIPWIRE_SKIP_SIGROK=1 make -C /tmp/r4-bitsync-work/test_internal/chip`; simulator-specific settings used `SIM_BUILD=sim_build/<case>_icarus COCOTB_RESULTS_FILE=results_<case>_icarus.xml COCOTB_TEST_FILTER=test_l3_<case>_tx` for focused cases. The model pulse suite also passed 6/6 with the command below. Local sigrok decoding was skipped; CI evidence covers only the original four L3 cases, and the expanded tests have not run on a hardened netlist.
- Model PULSE command: `TRIPWIRE_SKIP_SIGROK=1 PYTHONPATH=tools:tools/kernels pytest -q tools/kernels/tests/test_pulse_protocols.py::test_ws2812_two_frames tools/kernels/tests/test_pulse_protocols.py::test_dshot_frames_and_checksum tools/kernels/tests/test_pulse_protocols.py::test_dshot_checksum_is_computed_by_the_lane` — 6 passed.
- WS2812's first RTL test exposed a host-throughput gap hidden by the model test's instantaneous input preload. Updated `programs/ws2812.trw` to send two 12-bit length-in-token chunks per LED and use legal upper-tolerance pulse timings; the chip pad trace now passes the timing decoder with actual host SPI traffic. The model test was changed to the same format and BUGS.md #55 records the finding. I2C-target tests use bus-free intervals between 1 MHz writes because sustained writes exceed documented HOST_OUT polling throughput; no RTL defect was inferred.
- Updated `docs/reports/PHASE2_PROTOCOL_COVERAGE.md`, `docs/reports/PROTOCOL_SUPPORT.md`, and the in-progress Phase 2 summary with the evidence and remaining sigrok/netlist gaps. Active DRT continuation 36951141285 was still in detailed routing at the last check; GitHub reported it in progress, but live logs returned an API connection error.
- No RTL, config, info, or macro files changed; firmware, tests and docs changed. No Phase 2 checklist box was ticked. `git diff --check` passed.

Checklist boxes ticked (evidence):
- None.

Next:
- Run the expanded L3 tests with sigrok in CI, then on the matching hardened netlist when available. Continue with the remaining model-verified programs from `docs/reports/PROTOCOL_SUPPORT.md` while preserving active hardening inputs.

## 2026-10-01: Codex (phase 2: audit expanded protocol capability goal)
Done:
- Checked active GitHub workflows: DRT-only continuation [36951141285](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36951141285) is the only queued or running workflow; it continues detailed routing from the saved 16% GRT checkpoint.
- Compared `docs/reports/PROTOCOL_SUPPORT.md`, D-049's resource floor, the Phase 2/3 plans, and current chip tests. The current R4 RTL and hardened-netlist L3 evidence covers UART 8N1, SPI controller mode 0, and I2C controller only. D-049's one-program-at-a-time resource measurement does not establish RTL/GDS behavior for every program.
- Added `docs/reports/PHASE2_PROTOCOL_COVERAGE.md` to map roadmap status to current R4 RTL/netlist evidence and list the safe test-side work that can proceed during DRT. No RTL, config, info, macro, or active workflow input changed; no checklist box was ticked.
- `git diff --check` passed.

Checklist boxes ticked (evidence):
- None.

Next:
- Keep the DRT continuation running without modifying its checkpoint inputs. Start extending `test_internal/chip/test_l3.py` with complete-program RTL tests for the existing model-verified programs, then run the matching suite on the hardened netlist. Keep the 20 ns target and do not count model-only tests as RTL evidence.

## 2026-10-02: Codex (phase 2: RTL and gate-level L3 passed)
Done:
- Retrieved and reviewed candidate unit workflow [36799356039](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356039) for exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`. The chip RTL L3 suite passed 4/4 under both Icarus and Verilator, with `sigrok-cli` installed; tests cover UART TX, UART RX framing, SPI controller and I2C controller against reference models and sigrok. Artifacts `rtl-results` and `rtl-verilator-results` contain `chip/results.xml` and `chip/results_vl.xml`.
- Reviewed hardened-netlist L3 workflow [36952644578](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36952644578) and downloaded its `results_l3_gl.xml`: all 4/4 tests passed on the final netlist from GDS run 36799356107, for exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`. Tests cover UART TX, UART RX framing, SPI controller and I2C controller; the workflow used pinned Icarus 13, IHP models and installed `sigrok-cli`.
- Verified `docs/BUGS.md` contains a contiguous ledger from #1 through #54, including the latest open flow issue, and ticked checklist box 11.
- Ticked Phase 2 checklist boxes 5 and 6 with exact-candidate RTL and hardened-netlist evidence. Updated the checklist, `docs/reports/PHASE2_GDS_EXPERIMENTS.md`, and the plain-language Phase 2 summary. The area/budget decision, routed timing/congestion and full sign-off remain open.
- Audited D-056 against full GDS run 36799356107: 0.10 ns hold uncertainty had positive final hold slack at typ/slow/fast (+0.156 / +0.314 / +0.058 ns), and `gl_test` passed. The technical evidence condition is met; Kanishk's sign-off remains required before main adoption. Recorded the result in `docs/DECISIONS.md`; this does not resolve the run's −10.698 ns slow setup slack or 821 global-route overflow.
- Added the exact-candidate RTL and hardened-netlist L3 results to proposed D-048 for team review; approval remains pending. This keeps the Phase 2 tested scope tied to the shipped UART/SPI/I2C programs and leaves the wider protocol cases for phase 3 program work.
- Main CI is green at `3e82ae301c7afcb79d2f507e988754c4bfc85b99`: test 36952853704, lint 36952853714, docs 36952853881, unit 36952853654.
- DRT-only continuation [36951141285](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36951141285) remains in its detailed-routing step; no result is available yet. It continues from the 16% GRT checkpoint and is not a full sign-off workflow.

Checklist boxes ticked (evidence):
- [x] Box 5: RTL L3 suite, 4/4 tests under Icarus and Verilator in candidate unit workflow 36799356039; artifacts include `chip/results.xml` and `chip/results_vl.xml`.
- [x] Box 6: same L3 suite on the hardened netlist, 4/4 tests passed in workflow 36952644578; the exact test results are in its `l3-hardened-gl-36952644578` artifact.
- [x] Box 11: all currently logged bugs are represented in `docs/BUGS.md`, with consecutive entries #1–#54.

Next:
- Wait for DRT continuation 36951141285 to finish and inspect its detailed-route runtime and route DRC. If it completes, use the resulting checkpoint for routed timing and downstream physical sign-off; if it times out, stop repeating GRT-adjustment-only runs and choose the next isolated route-aware or timing experiment. Keep the 20 ns clock, protocol behavior, and D-066 live configuration contract.

## 2026-10-01: Codex (phase 2: analyze 12% GRT hardening)
Done:
- Downloaded artifact `GDS_logs-36913096552` for exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` (2 lanes, 4 pin units, U0 full; 20 ns; density 56%). Run 36913096552 failed after 5 h 31 min in the full hardening job; precheck and `gl_test` were skipped.
- The 12% global route had zero overflow, 631,958 total capacity, 254,567 demand, 40.28% usage and 2,458,468 µm wirelength. Compared with the 30% run's 821 overflow and 2,863,598 µm, this improves the global-route estimate but not the full route.
- Detailed routing was still in optimization when the LibreLane step hit its configured 330-minute limit. Its partial log reports 35,152 initial violations, 26,196 after optimization iteration 1, then 25,030 after iteration 2; no detailed route completion or final DRC was produced. Do not interpret those intermediate counts as a final DRC report.
- At the post-CTS checkpoint, preliminary metrics show slow setup WNS −5.044 ns / TNS −555.063 ns / 184 violating paths; fast and slow hold WNS −0.327 ns / −0.554 ns with 28 violating paths each. No final routed timing, LVS, precheck, gate-level, or viewer evidence exists for this run.
- Added 16% as an option to the existing GRT-only diagnostic workflow. It will compare capacity/overflow and route guides before another multi-hour full hardening; no RTL, config, macro, info, or active hardening input changed.
- Updated `docs/reports/PHASE2_GDS_EXPERIMENTS.md`; `git diff --check` passed. No Phase 2 checklist boxes were ticked.

Checklist boxes ticked (evidence):
- None. GRT improvement alone is not a completed route or signoff result.

Next:
- Run `gds-congestion-diagnostic` at 16%, then compare it against the saved 12% and 30% reports. Promote it to full hardening only if the routeability indicators support it. Keep timing optimization as a separate one-change hardening track and preserve 20 ns / D-066 behavior.

## 2026-10-01: Codex (phase 2: screen one-hot pin input selector)
Done:
- Screened an isolated one-file rewrite of `trw_pin_io.v` against the exact R4 candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` (2 lanes, 4 pin units, U0 full). It replaces the variable A/S pad select with equality decodes and a masked OR. The scratch tree is `/tmp/r4-pinin-opt/src`; the active GDS candidate and its inputs were not changed.
- Matched slow-corner mapped Yosys/OpenSTA: area changed 393,004.18 → 392,124.61 µm² (−0.224%). Worst path from U0 `idle` improved by 1.335 ns of slack; the same latch-to-`dropped[26]` endpoint improved by 0.902 ns. This is pre-placement, no-parasitic timing only.
- Yosys SAT proved combinational `a_in`, `b_in`, `c_in`, and `sel` equivalence for all two-state inputs. The R4 pin suites passed 60/60 for FULL=0/1 on Icarus on both baseline and scratch RTL; the scratch variant also passed 60/60 for each mode on Verilator. Whole-chip Verilator lint passed.
- Scratch L2 passed the 128-clock smoke and 1,000,000-clock comparison with zero divergences. Both L2 RTL injections were detected: priority flip at clock 99; cursor off-by-one at clock 326.
- Ran L3 using the matching R4 checkout/spec/tools. Baseline and scratch outputs match: UART RX passes; the TX, SPI-C and I2C-C reference-model checks pass, but local sigrok checks receive empty annotations, so those tests report failures. The VCD-to-UART toolchain smoke also returns no decoded bytes (`scripts/sigrok_smoke.py /tmp/tripwire-sigrok-smoke` expected `TRIPWIRE`, got empty output); `sigrok-cli -L` returns no supported-module listing, including with `SIGROKDECODE_DIR=/usr/share/libsigrokdecode/decoders`. This confirms a local sigrok installation/setup problem rather than a candidate RTL or L3 VCD-specific regression. A first cross-check using `main`'s newer generated host map was discarded as an invalid mixed-revision run.
- Refreshed hardening run 36913096552; at 2026-10-02 00:26 UTC it remained in full hardening step 11, about 5 h 10 min after start. GitHub still withholds logs until that step completes; its 6-hour job limit is approaching.
- Updated `docs/reports/PHASE2_GDS_EXPERIMENTS.md`. `git diff --check` passed. No phase checklist boxes were ticked; no candidate RTL or flow input was changed.

Checklist boxes ticked (evidence):
- None. The mapped screen and simulations do not establish routed timing or GDS signoff.

Next:
- Review run 36913096552 immediately when it completes or times out. If its slow-corner path remains relevant, decide whether to route this one-file selector as a separate hardening. Rerun the L3 sigrok checks with a working sigrok-cli/libsigrok installation; the local toolchain currently fails its standalone UART smoke test.

## 2026-10-01: Codex (phase 2: trace the slow timing cone)
Done:
- Audited the final slow-corner path list and mapped endpoint cells back to the archived synthesized netlist for run 36799356107. Of 1,000 reported worst paths, 991 launch from U0's stored `idle` configuration latch. The first 120 unique endpoints span 54 U0 BITSYNC state bits, 20 U0 RX producer state bits, 40 top-level state bits (including C2 DROPPED), five fabric `last_seq` bits and U0 `overrun`.
- This broad, shared cone indicates the counter endpoint is only one of many affected sinks. A counter-only rewrite is unlikely to close the path; focus screening on the latch-driven pad/RX/fabric cone and physical fanout/load repair.
- The saved GRT checkpoint is available, but the local replay remains unavailable: no LibreLane or Docker, and cached OpenROAD has missing shared libraries. The active GDS run 36913096552 was refreshed successfully at 18:06 Chicago and remained in hardening step 11.
- Updated `docs/reports/PHASE2_GDS_EXPERIMENTS.md`; `git diff --check` passed. No hardware or active flow inputs changed.

Checklist boxes ticked (evidence):
- None; this is report analysis, not a new routed result.

Next:
- Use a compatible flow environment to test timing repair at the saved GRT checkpoint. When the active run finishes, repeat endpoint/fanout analysis on its 12% GRT route before selecting the next RTL experiment.

## 2026-10-01: Codex (phase 2: prepare route-aware timing replay)
Done:
- Confirmed the prior baseline GRT checkpoint is present at `/tmp/r4-gds-36799356107/GDS_logs/runs/wokwi/39-openroad-globalrouting/`: it includes the ODB, DEF, guides, config, and LibreLane state. The checkpoint is candidate `3393eea` with 30% GRT adjustment; use it only as a flow-repair screen, not as a substitute for the active 12% run.
- Checked the local replay environment. The project venv has no LibreLane module and Docker is unavailable. The cached OpenROAD binary cannot start because its cached package dependencies (`libtcl8.6`, `libortools`, and Qt libraries) are missing. No local route-aware repair run could be launched.
- GitHub CLI recovered on retry. At 18:06 Chicago, run 36913096552 remained in full hardening step 11; later steps are pending.
- No candidate RTL/config/flow inputs were changed. Existing documentation changes remain uncommitted.

Checklist boxes ticked (evidence):
- None. The saved checkpoint has not been replayed and the active workflow result is unavailable.

Next:
- Run the saved-state ECO replay in a compatible LibreLane 3.1.0.dev3/IHP/OpenROAD environment, or wait for the active run's artifacts and use its 12% GRT checkpoint. Report fresh slow-corner setup and fast-corner hold at the checkpoint before routing any RTL variant.

## 2026-10-01: Codex (phase 2: timing experiment research)
Done:
- Traced the archived slow latch-to-DROPPED path and consulted primary OpenROAD, Yosys and LibreLane documentation. The path has slow heavily loaded cell arcs as well as logic depth; a 2.399 ns cell arc and >3 ns transition motivate targeted sizing/load repair.
- Checked the baseline resolved configuration: AREA 0 synthesis, timing-driven placement disabled, and both post-GRT design repair and timing repair disabled. Post-CTS repair loaded all corners but reported no setup violations; intermediate STA/GRT loaded typical only. The repair/signoff discrepancy needs fresh checkpoint reports, not conclusions from metrics inherited in state JSON.
- Added a ranked screening plan and source links to `docs/reports/PHASE2_GDS_EXPERIMENTS.md`: route-aware repair, timing-driven placement, delay synthesis/slow mapping, existing RTL trials, configuration predecode, narrow load/drop decode and targeted locality/cloning. No hardware or running-flow inputs changed; no new experiments were launched.

Checklist boxes ticked (evidence):
- None; the new ideas are proposals without timing results.

Next:
- Diagnose the repair/signoff discrepancy and screen route-aware repair using saved checkpoints before selecting the next complete hardening. Preserve 20 ns, D-066 and same-cycle DROPPED accounting.

## 2026-10-01: Codex (phase 2: timing and signoff action plan)
Done:
- Checked `gds-grt-adjustment-experiment` run 36913096552 at 22:54 UTC (17:54 Chicago): still in progress, about 3 h 38 min after the hardening job started. Setup and candidate validation passed; full LibreLane hardening step 11 remains active. GitHub does not expose this job's logs until completion; precheck and gate-level jobs have not started.
- Reviewed the timing experiment report. The current flow trial uses exact candidate `3393eea`, 2 lanes / 4 units / U0 full, 20 ns, density 56%, with only the 12% GRT adjustment override. The earlier GRT-only zero-overflow result does not establish detailed-route or timing success.
- Set the follow-up order: inspect this run's routed all-corner paths and physical checks; if timing still fails, prioritize a separate single-change pad-mux hardening if the path diagnosis still supports it, then evaluate the RX compare-factor trial separately. Both prototypes already passed million-clock L2 and RTL injection checks, but neither has routed timing evidence.

Checklist boxes ticked (evidence):
- None; the active experiment has not completed.

Next:
- Download the completed run's artifacts and compare congestion, routed timing, slew/cap, DRC/LVS/antenna, runtime, precheck, and gate-level results. Complete the matching-candidate L3 reference/sigrok suite and run it against the hardened netlist. Keep the 20 ns clock, protocol support, timed D-066 live configuration, and same-cycle DROPPED accounting throughout.

## 2026-10-01: Codex (phase 2: screen pad mux timing)
Done:
- Refreshed hardening run [36913096552](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36913096552): it remains in full LibreLane hardening step 11, pinned to candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`, 2 lanes / 4 units / U0 full, 20 ns, 56% density, `GRT_ADJUSTMENT=0.12`. At 21:56 UTC it had been in that step about 2 h 40 min; precheck and gate-level jobs are waiting on hardening. GitHub says logs will be available when the step completes.
- Screened a separate `trw_pins.v` rewrite in `/tmp/r4-padmux-opt` against the exact R4 source at `3393eea`. Parallel owner/A/N match vectors and masked ORs preserve one-owner pad selection and A-before-N priority; no active candidate RTL, config, info, macro, clock target, false path, or `DROPPED` behavior changed.
- Matched local full-chip Yosys-mapped / OpenSTA slow-corner STA on the same logical idle-latch → C2 DROPPED[0] path: arrival 13.5434 → 12.2152 ns (1.3282 ns faster), slack +5.8762 → +7.1606 ns, mapped area 392,541.24 → 391,881.75 µm² (−0.168%). This excludes placement and routed parasitics; no routed improvement is established.
- The Verilator pad-owner scoreboard passed 1,500 randomized cycles. Candidate L2 passed a 128-clock smoke and 1,000,000 clocks with zero divergences (1,019.81 s). Separate clean L2 baselines passed; the priority-flip and cursor off-by-one RTL mutations were detected at clocks 99 and 326.
- The R4 chip-level suite passed 5/5, including UART TX on full and lean units at the 20 ns target and the UART program loopback. Local artifacts, RTL trial and reports are in `/tmp/r4-padmux-opt/`.
- Updated `docs/reports/PHASE2_GDS_EXPERIMENTS.md` with this timing experiment and current hardening status. `git diff --check` passed.

Checklist boxes ticked (evidence):
- None. The pad-mux STA is pre-route; run 36913096552 has not completed, so no Phase 2 exit box is newly satisfied.

Problems / decisions:
- The pad-mux prototype is a promising isolated timing/area experiment, not proof that the 6x4 layout meets slow-corner timing. Keep it out of the active run and do not call the GDS workflow green yet.
- The active run was still in hardening; no logs or downstream precheck / gate-level results were available at the latest query. No L3 scope decision or final hardware-count decision was made.

Next:
- Review run 36913096552 when it completes. Compare all-corner timing, congestion, DRC/LVS/antenna, detailed-route duration, precheck, gate-level tests and rendered design. If timing remains failing, decide which single isolated RTL timing change warrants a separate hardening at the same 20 ns target.

## 2026-10-01: Codex (phase 2: isolate RX timing optimization)
Done:
- Added timing optimization as a separate workstream beside the active hardening and L3 validation in `docs/reports/PHASE2_GDS_EXPERIMENTS.md`.
- Rechecked the archived physical slow-corner worst path for R4 candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` (2 lanes, 4 pin units, U0 full; 20 ns): U0's live `idle` config latch bit 7 to `dropped[16]`, 31.723 ns arrival, 21.025 ns required, −10.698 ns slack.
- In an isolated copy under `/tmp/r4-timing-opt`, split the SHIFT_RX sample-zero check into START/`sofs` and `S_SAMP`/`rt` terms. It remains combinational, samples on the same clock, keeps configuration latch-to-state paths timed, and does not alter `DROPPED` accounting. The active hardening tree and its inputs were not changed.
- Matched local full-chip mapped-gate slow-corner STA on baseline and prototype: same idle-latch → DROPPED endpoint, arrival 13.5434 → 11.9531 ns (1.5903 ns faster), slack +5.8762 → +7.4761 ns. Mapped area increased 392,541.24 → 394,026.03 µm² (+0.378%). This is pre-layout evidence only; the routed baseline remains −10.698 ns and the prototype has no routed result.
- Added an RX unit regression that writes the real configuration latches after activation and checks that the next frame uses the new pin and sample offset on the specified clock. Candidate full-unit Verilator RX tests passed 16/16 on baseline and optimized RTL; lean-unit Icarus RX tests passed 16/16 on both. Top-level UART RX framing passed.
- L2 passed a 128-clock smoke, a 1,024-clock isolated rerun, and 1,000,000 clocks with zero divergences. The priority-flip RTL mutation was detected at clock 99; the cursor off-by-one RTL mutation was detected at clock 326; both corresponding clean baselines passed.
- The latest successful query reported active full hardening [36913096552](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36913096552) as `in_progress` (last updated 2026-10-01 19:16:50 UTC); a later refresh could not connect to GitHub. It remains on the pinned candidate and flow override. No GDS inputs, Phase 2 boxes, or RTL candidate were changed.

Evidence:
- Physical worst path: `/tmp/r4-gds-36799356107/GDS_logs/runs/wokwi/55-openroad-stapostpnr/nom_slow_1p08V_125C/max.rpt`.
- Prototype diff and matched STA: `/tmp/r4-timing-opt/rx-sample-factor.patch`, `/tmp/r4-timing-opt/sta_chip_baseline.log`, `/tmp/r4-timing-opt/sta_chip_opt.log`; full-unit candidate RX suite XML: `/tmp/r4-timing-opt/pin_candidate_live.xml`, `/tmp/r4-timing-opt/pin_opt_live.xml`; lean-unit candidate RX suite XML: `/tmp/r4-timing-opt/pin_lean_base_icarus.xml`, `/tmp/r4-timing-opt/pin_lean_opt_icarus.xml`; UART RX XML: `/tmp/r4-timing-opt/l3_rx.xml`.
- L2 smoke XML: `/tmp/r4-timing-opt/l2_short128.xml`, `/tmp/r4-timing-opt/l2_short1024.xml`; the exact one-million-clock command was `L2_CYCLES=1000000 make -C test_internal/l2 SIM=verilator RTL_DIR=/tmp/r4-timing-opt/src RTL_REV=timing-opt` (1,000,000 compared clocks, zero divergences, 961.90 s).
- L2-INJECT: `RTL_DIR=/tmp/r4-timing-opt/src RTL_REV=timing-opt SIM_BUILD=/tmp/r4-timing-opt/l2_injection_build python -u test_internal/l2/run_injections.py`; isolated cursor mutant check used `run_mutation` with a separate `SIM_BUILD`. One initial attempt on the shared simulator build reported a lane-debug mismatch at clock 99; fresh isolated baseline and optimized builds passed at 128/1,024 clocks, and the isolated clean baselines plus both mutations then passed/detected. The shared-build discrepancy did not recur; its cause is undetermined.
- `git diff --check` passed. The main checkout has documentation updates and the new `test_internal/pin/test_pin_rx.py` regression; `/tmp/r4-timing-opt/src` is an isolated RTL copy.

Checklist boxes ticked (evidence):
- None. Local mapped STA is not routed timing, and no Phase 2 exit box is newly satisfied by this isolated experiment.

Problems / decisions:
- No false path was added. D-066 live configuration behavior and same-cycle `DROPPED` accounting remain in the timed design. The 20 ns target and supported protocol/resources are unchanged.
- The mapped area rises 0.378%, and local STA does not include placement, routing, or parasitics. Do not promote this prototype into the active hardening run. Wait for run 36913096552 and resolve the separate L3 sigrok/VCD annotation issue; only then consider a one-change hardening with this RTL.

Next:
- Review run 36913096552's routed timing, congestion, DRC/LVS/antenna, precheck, gate-level, and viewer outputs. Keep L3 decoder diagnosis and timing RTL promotion as separate workstreams.

## 2026-10-01: Codex (phase 2: exit plan)
Done:
- Reviewed the current Phase 2 exit checklist and latest worklog. Open checklist boxes are area/budget, L3 RTL, L3 on the hardened netlist, and bug-log audit.
- Refreshed full hardening run 36913096552: still in progress at `Run full LibreLane hardening with GRT adjustment override`; the GitHub CLI reports logs will be available when the job completes.
- Ran `source /home/younix/protocol-emulator-asic/.venv/bin/activate && make -C /tmp/r4-bitsync-work/test_internal/chip SIM=verilator SIM_BUILD=/home/younix/protocol-emulator-asic/test_internal/chip/sim_build/vl_l3_spi COCOTB_TEST_MODULES=test_l3 COCOTB_RESULTS_FILE=results_l3_r4.xml` against matching R4 candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`: UART RX passed; UART TX, SPI-C and I2C-C passed their reference-model checks but failed when sigrok produced no annotations. XML: `/tmp/r4-bitsync-work/test_internal/chip/results_l3_r4.xml`. `sigrok-cli -L` likewise listed no decoders beyond a libusb warning; the same empty UART decode reproduces on a tripsim-generated waveform, pointing to a shared sigrok/VCD setup issue rather than isolating an RTL failure.
- `test/` remains the counter placeholder, so these `trw_chip` tests alone do not provide the required top-level pin-test evidence.
- An initial cross-branch run paired R4 RTL with `main`'s 3-lane/6-unit tools and was discarded as invalid. No checklist boxes were ticked; no project decisions or hardware inputs changed.

Next:
- Resolve the sigrok decoder/VCD setup and rerun L3 against the matching candidate; review run 36913096552's full hardening, precheck, gate-level, and GDS preview when it finishes.

Template:

```
## YYYY-MM-DD: <who> (phase N)
Done:
- ...
Checklist boxes ticked (evidence):
- [x] <item>: <CI run #/command/file>
Problems / decisions:
- ... (DECISIONS D-xxx, BUGS #x)
Next:
- ...
```

## 2026-10-01: Codex (phase 2: GRT congestion map and controlled follow-up)
Done:
- Added `.github/workflows/gds-congestion-diagnostic.yaml`, pinned to candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` (2 lanes, 4 pin units, U0 full, 20 ns, 56% density). It stops at `OpenROAD.GlobalRouting` and uploads the stage report and artifacts.
- Added `scripts/ci/openroad_congestion_wrapper.sh` and `scripts/ci/Dockerfile.openroad-congestion`. The wrapper preserves router arguments and injects only the congestion-report output; the custom image makes LibreLane's OpenROAD override available inside the Dockerized flow.
- Runs 36893706804 and 36896957051 reproduced baseline overflow 821 (M2 10, M3 779, M4 32; M3 usage 78.19%) but did not produce bin reports. The hook worked in run 36899340155: 769 overfull bins, 820 horizontal and 1 vertical overflow, summing to the same 821. The bins span x=244.8–792.0 µm and y=0–698.4 µm; the largest 100 µm x band is 600–700 µm with 444 overflow. Overflow spans the design height rather than being confined to one small blockage. This is GRT-only evidence, not proof of detailed-route capacity.
- Added a diagnostic input for `GRT_ADJUSTMENT=0.30` (baseline) or `0.12`, passed through LibreLane's `--override-config`; it does not edit either candidate config file. The first 12% dispatch, run 36904343041, stopped before LibreLane because the generated merge omits the default-valued key. Run 36906496173 then completed GRT at 12% with zero overflow but the workflow failed its nonempty-report assertion: OpenROAD emitted no bin report when no bins overflowed. The validator now accepts a missing report only when the GRT log's final aggregate overflow is zero, and writes a short zero-overflow summary into the artifact.
- At 12%, run 36906496173 reports 0 overflow on M2/M3/M4, 40.28% overall usage, and 2,458,468 µm global-route wirelength. Baseline 30% run 36899340155 reports 821 overflow, 58.24% usage, and 2,863,598 µm. This is a favorable GRT estimate, not a detailed-route result: the lower adjustment gives the router more assumed capacity, not more physical tracks.
- Added `.github/workflows/gds-grt-adjustment-experiment.yaml` for full LibreLane hardening on the same pinned R4 candidate with only the `GRT_ADJUSTMENT=0.12` CLI override. On successful hardening it packages the Tiny Tapeout submission, runs precheck and gate-level test jobs, and uploads a GDS preview artifact; it does not publish a viewer or change any candidate hardware input.
- Dispatched full experiment [36913096552](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36913096552). Candidate validation and all setup steps passed; the full LibreLane hardening step is running. The run pins `3393eea9a58c5cad9077cc360a8515d0e5ec8284` and keeps the 20 ns clock, 2-lane/4-unit shape, U0 full and 56% density.

Checklist boxes ticked (evidence):
- None. Runs 36899340155 and 36906496173 are GRT-only evidence, not full hardening/signoff runs. A lower congestion estimate alone will not establish that detailed routing fits.

Problems / decisions:
- No RTL, candidate config file, `info.yaml`, macro, clock, density, or resource count was changed. The adjustment is passed as a flow-only CLI override; the diagnostic stops before detailed routing.
- First dispatch, run 36892786936, stopped before synthesis/GRT because LibreLane requires the `--force-run-dir` path to exist first. No congestion data was generated; the workflow now creates that directory before launch.

Evidence:
- `.github/workflows/gds-congestion-diagnostic.yaml` and `scripts/ci/openroad_congestion_wrapper.sh`.
- `.github/workflows/gds-grt-adjustment-experiment.yaml` for full hardening plus dependent precheck and gate-level test jobs.
- Full hardening progress: [run 36913096552](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36913096552); setup passed and LibreLane hardening is active.
- `bash -n scripts/ci/openroad_congestion_wrapper.sh`; wrapper smoke check with a stub OpenROAD executable; PyYAML and embedded-Python workflow checks; zero-overflow report postcondition smoke-tested against run 36906496173; `git diff --check`.
- Failed setup attempt: [workflow run 36892786936](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36892786936), error: `Directory 'runs/congestion-diag' does not exist`.
- Missing report evidence: the `COMMANDS` and `openroad-globalrouting.log` files in the downloaded artifacts for [run 36893706804](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36893706804) and [run 36896957051](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36896957051) show the stock executable and no `-congestion_report_file` option.
- Successful report evidence: [run 36899340155](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36899340155); `/tmp/gds-congestion-36899340155/gds-congestion-36899340155/runs/congestion-diag/39-openroad-globalrouting/congestion.rpt` (769 bins) and adjacent `openroad-globalrouting.log` (per-layer overflow summary).
- First 12% setup failure: [run 36904343041](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36904343041), `KeyError: 'GRT_ADJUSTMENT'` before the flow began; the workflow now uses LibreLane's `--override-config` CLI instead of editing the generated config.
- 12% GRT evidence: [run 36906496173](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36906496173), adjacent `openroad-globalrouting.log` shows `Global adjustment: 12%`, zero total overflow, and 2,458,468 µm wirelength. Its overall job failed only because zero overflowing bins produce no congestion report file; the postcondition now handles that case.

Next:
- Review run 36913096552 after full hardening completes: GRT, detailed-route runtime/DRC, all-corner timing/hold, LVS, antenna, precheck, gate-level tests and the GDS preview. Until those results pass, treat 12% as a promising estimate only.

## 2026-10-01: Codex (phase 2: trace R4 timing and congestion)
Done:
- Traced the run 36799356107 slow-corner path from U0's `idle` configuration latch bit 7 to `dropped[16]`, bit 0 of C2 / L1.I0. Candidate fabric source 0 for C2 is U0.rx.
- The mapped path crosses U0 pin/drive and BITSYNC logic, RX token loading, and the C2 drop condition; it contains 32 combinational cells and 12 fanout buffers. Arrival is 31.723 ns, required time 21.025 ns, slack −10.698 ns. The counter is the endpoint; the long delay is primarily upstream logic depth and buffering.
- Checked the retained GRT ODB, DEF, guides, log and metrics. The artifact has no per-bin congestion report or heatmap, so the 779 M3 overflow cannot be localized from its saved summary. The route-guide boxes do not encode overflow. Local OpenROAD is unavailable to inspect the ODB directly.
- Updated `docs/reports/PHASE2_GDS_EXPERIMENTS.md` with the path trace and a diagnostic-only next step: rerun GRT on the same candidate/settings and save its congestion report before changing routing settings.

Checklist boxes ticked (evidence):
- None. This session did not run a new verification or signoff check.

Problems / decisions:
- D-066 requires the live configuration-to-state path to remain timed. Do not false-path or add a cycle to DROPPED accounting; that changes frozen behavior. The current GRT archive does not support a claim about spatial M3 hotspots.
- No RTL, `src/config.json`, `info.yaml`, macro, or hardening input was changed.

Evidence:
- Timing path: `/tmp/r4-gds-36799356107/GDS_logs/runs/wokwi/55-openroad-stapostpnr/nom_slow_1p08V_125C/max.rpt`.
- GRT summary and retained files: `/tmp/r4-gds-36799356107/GDS_logs/runs/wokwi/39-openroad-globalrouting/`.
- Exact candidate fabric mapping: `/tmp/r4-bitsync-work/src/trw_fabric.v` at `3393eea9a58c5cad9077cc360a8515d0e5ec8284`.

Next:
- Produce bin-level congestion data on the exact candidate without changing its hardware or flow settings; then propose one isolated routing-setting experiment if the map supports it. Continue timing work as a separate experiment, with D-066 paths timed and all required protocol behavior intact.

## 2026-10-01: Codex (phase 2: review full 6x4 hardening)
Done:
- Reviewed standard GDS workflow run [36799356107](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356107) for exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` (`spike/r4-floorplan`; 2 lanes, 4 pin units, U0 full; 20 ns; density 56%; hold uncertainty 0.10 ns, setup 0.25 ns). The counts remain the candidate under test, not approval of final hardware counts.
- All four workflow jobs passed: GDS (4 h 23 min), precheck (9/9 checks, 2 h 22 min), gate-level test (4 existing tests), and viewer. The rendered image shows the actual routed design.
- Candidate `test`, `lint`, `docs`, and `unit` runs all passed on the exact R4 commit (36799356152, 36799356097, 36799356063, 36799356039). Main's corresponding workflows also passed on `ad401efdd0421c11931e9c6f533ed43cc5fcd788` (36799339276, 36799339202, 36799339220, 36799339309).
- Detailed routing finished in 3 h 15 min 40 s with final route DRC 0. LVS and antenna checks are clean; KLayout SG13CMOS5L DRC and all other precheck checks passed. The 57,924 Magic DRC markers are the documented SRAM exception baseline; its 10 overlap markers are the expected POWER-stripe/SRAM-OBS crossings noted in the run's config and checked by Loom.
- Typical setup has 0 violating paths; all-corner hold has 0 violating paths. Slow setup remains poor: WNS −10.698 ns, TNS −4,463.296 ns, 1,132 violations. Max-slew violations are 44 typical / 211 slow, and max-cap violations are 18 in each corner.
- Global routing still reports 821 overflow (779 M3, 10 M2, 32 M4) at 78.19% M3 usage. Thus detailed routing converged within the Phase 2 <4 h routing target, but the high global congestion remains a design risk. The worst slow setup path is U0's `idle` configuration latch bit 7 to `dropped[16]`; keep it timed under D-066.
- Added the run to `docs/reports/AREA.md` and updated the experiment record and Phase 2 checklist with the passed evidence. The 2-lane/4-unit measurement is not a final-count decision.

Evidence:
- GDS, timing, route and checker reports: downloaded run artifact at `/tmp/r4-gds-36799356107/GDS_logs/runs/wokwi/`; primary files are `final/metrics.json`, `39-openroad-globalrouting/openroad-globalrouting.log`, `44-openroad-detailedrouting/openroad-detailedrouting.log`, `55-openroad-stapostpnr/summary.rpt`, and `55-openroad-stapostpnr/nom_slow_1p08V_125C/max.rpt`.
- Precheck: `/tmp/r4-gds-36799356107/precheck_reports/results.md` (all 9 checks pass).
- Gate-level suite: `/tmp/r4-gds-36799356107/gatelevel_test_results/results.xml` (4/4 tests pass; this is not the full L3 UART/SPI/I2C suite).
- Viewer: `/tmp/r4-gds-36799356107/gds_render/gds_render.png` and viewer job in run 36799356107.

Checklist boxes ticked (evidence):
- [x] All RTL modules exist and lint clean with latches only where allowed: candidate lint run 36799356097; full synthesis checks in GDS run 36799356107.
- [x] Full 6x4 GDS criteria as written (precheck, DRC/LVS/antenna, typical timing, detailed routing <4 h): run 36799356107. Slow-corner setup and global-route congestion are recorded above and in `docs/reports/AREA.md`.
- [x] Viewer output shows the full routed design: viewer job and rendered image from run 36799356107.
- [x] First full-design AREA row: `docs/reports/AREA.md`, run 36799356107.

Problems / decisions:
- Phase 2 is not complete. The area/count decision remains open; box 6's required L3 protocol tests on the hardened netlist are not covered by the four existing gate-level tests; slow-corner timing and global-route overflow need engineering review. The candidate counts are not approved for final hardware.
- The candidate's all-corner STA report is retained as required evidence. Do not false-path or otherwise waive U0 `idle` → `dropped[16]`; D-066 requires live reconfiguration paths to remain timed.
- The main-side test/docs/lint/unit runs were green before these uncommitted documentation updates. The docs workflow runs after push; no hardware inputs were changed by this session.

Next:
- Trace the `idle` → `dropped` logic and inspect the M3 congestion map; propose one behavior-preserving RTL or placement-flow experiment without lowering the 20 ns clock or removing protocol support. Keep D-066 paths timed and ask for any decision that changes the frozen contract. Then add the full L3 suite to the gate-level path and obtain the remaining budget/count sign-off.

## 2026-09-30: Codex (phase 2: register carrier enable on the pin clock)
Done:
- Added one flop in `trw_pin_tx.v` to capture the cached carrier-enabled predicate at each pin-unit clock and use that sampled value for the pad output. The carrier configuration latch-to-flop path remains timed under D-066; the registered carrier state no longer feeds the output-to-RX loop combinationally.
- Kept this as one RTL change on top of R4 `cfc41e1d67a1f9c8cbca4168f6979f4c17a999cc`; lane/unit counts, 20 ns clock, and 56% density are unchanged.
- The full and lean pin suites each pass 60/60. L2 smoke passes 128 clocks; the full lockstep passes 1,000,000 clocks with zero divergences against main's `b6f8fa9` model. Both required RTL injections are detected.
- Matched 20 ns pre-layout STA with every latch-to-state path timed improves worst slack from +8.858 to +9.154 ns typical and +2.717 to +3.344 ns slow. Yosys mapped area rises from 390,666.74 to 391,112.44 µm² (+445.70 µm²).
- Copied only `src/trw_pin_tx.v` into `/tmp/r4-bitsync-work` for review before pushing. Routed timing, congestion and signoff remain unproven until GDS run 36799356107 finishes.
- Updated the main-side `gds-thread-experiment.yaml` guard to permit either the exact baseline or a candidate differing from `cfc41e1` only in `src/trw_pin_tx.v`, so this one-file candidate can be tested with an explicit OpenROAD thread count.
- R4 commit `3393eea9a58c5cad9077cc360a8515d0e5ec8284` passed `test`, `lint`, `docs`, and `unit`. Its standard GDS workflow is still running in `Build GDS`; precheck, gate-level test, and viewer are downstream.
- Main commit `ad401efdd0421c11931e9c6f533ed43cc5fcd788` passed `test`, `lint`, `docs`, and `unit`.
- Re-ran L2 on the exact pushed RTL revision `3393eea9a58c5cad9077cc360a8515d0e5ec8284`: smoke passed 128 clocks; full comparison passed 1,000,000 clocks with zero divergences in 555.36 s. Both clean injection baselines passed; priority-flip was detected at clock 99 and cursor off-by-one at clock 326.
- Added `docs/reports/PHASE2_GDS_EXPERIMENTS.md` to summarize the measured fit/timing experiments, constraints, current status, and follow-up candidates.

Evidence:
- Pin suites: `/tmp/r4-carrierout-ff/test_internal/pin/results_full1_frac8.xml` and `results_full0_frac8.xml` (60/60 each).
- L2: `L2_CYCLES=128` smoke and `L2_CYCLES=1000000` full run from `test_internal/l2` with `RTL_DIR=/tmp/r4-carrierout-ff/src`; full run reported zero divergences in 523.39 s.
- L2-INJECT: `RTL_DIR=/tmp/r4-carrierout-ff/src RTL_REV=cfc41e1d67a1f9c8cbca4168f6979f4c17a999cc-carrierout-ff python test_internal/l2/run_injections.py`; priority-flip detected at clock 99, cursor off-by-one at clock 326, and both clean baselines passed.
- Exact-revision L2 rerun: `L2_CYCLES=128 make -C test_internal/l2 SIM=verilator RTL_DIR=/tmp/r4-bitsync-work/src RTL_REV=3393eea9a58c5cad9077cc360a8515d0e5ec8284`; `L2_CYCLES=1000000 make -C test_internal/l2 SIM=verilator RTL_DIR=/tmp/r4-bitsync-work/src RTL_REV=3393eea9a58c5cad9077cc360a8515d0e5ec8284` (PASS, 1,000,000 clocks, zero divergences, 555.36 s); `RTL_DIR=/tmp/r4-bitsync-work/src RTL_REV=3393eea9a58c5cad9077cc360a8515d0e5ec8284 python test_internal/l2/run_injections.py` (clean baselines passed; both RTL mutations detected).
- STA and area: `/tmp/r4-carrierout-ff/synth/chip/build/sta_typ_d066.txt`, `sta_slow_d066.txt`, and `stat_flat.txt`; baseline: `/tmp/r4-candidate-cache/synth/chip/build/sta_typ_1p20V_25C_d066.txt`, `sta_slow_1p08V_125C_d066.txt`, and `stat_flat.txt`.
- GitHub Actions: R4 test [36799356152](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356152), lint [36799356097](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356097), docs [36799356063](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356063), and unit [36799356039](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356039) passed; GDS [36799356107](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799356107) remains in progress at `Build GDS`. Main test [36799339276](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799339276), lint [36799339202](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799339202), docs [36799339220](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799339220), and unit [36799339309](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36799339309) passed.

Checklist boxes ticked (evidence):
- [x] Phase 2 L2 lockstep and L2-INJECT: exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`, 1,000,000 clocks with zero divergences; both clean baselines passed and both RTL mutations detected. Detailed evidence is in `docs/design/phases/PHASE2_RTL_CORE.md` and the commands above.
- Other Phase 2 boxes remain open. Full routed timing and GDS signoff are still required.

Problems / decisions:
- This is pre-layout evidence only. The new register changes sub-cycle response to a pin-configuration latch update; the architecture and model observe the new setting on the next pin-unit clock, and clock-level pin/L2 checks pass. Review the diff before hardening.
- The first GitHub Actions query could not connect to `api.github.com`; a subsequent query succeeded and confirmed the runs above.
- The main checkout has uncommitted `docs/WORKLOG.md`, `docs/design/phases/PHASE2_RTL_CORE.md`, and new `docs/reports/PHASE2_GDS_EXPERIMENTS.md` updates. Both pushed branches were clean and in sync at the time of the check.

Next:
- Wait for R4 unit and GDS runs to finish. If GDS passes, verify the downstream precheck, gate-level test, and viewer jobs. If GDS fails, inspect its artifact and address the measured failure; do not tick any other Phase 2 boxes before their evidence passes.

## 2026-09-30: Codex (phase 2: screen critical-path RTL ideas)
Done:
- Kept the source baseline at R4 candidate `cfc41e1d67a1f9c8cbca4168f6979f4c17a999cc` (2 lanes, 4 pin units, U0 full, 20 ns, 56% density) and made one-at-a-time prototypes in `/tmp` only.
- Screened five behavior-preserving RTL forms with the chip Yosys/cmos5l and OpenSTA flow, keeping D-066 latch-to-state paths timed. Baseline was 390,666.74 µm² and +2.717 ns slow-corner pre-layout slack. Every trial increased mapped area and reduced slow slack:
  - fabric one-hot source selection: 391,177.19 µm², +1.004 ns;
  - fabric indexed selection: 392,077.93 µm², +2.176 ns;
  - factored RX event-edge decode: 391,948.73 µm², +1.660 ns;
  - parallel saturating-counter toggles: 392,327.94 µm², +2.690 ns;
  - factored carrier output level: 391,046.18 µm², +1.759 ns.
- Rejected all five. None was copied into the R4 worktree or main, and no hardening candidate or protocol resource changed.

Evidence:
- Four-thread post-route critical path: `build/ci/r4/thread4/runs/wokwi/55-openroad-stapostpnr/nom_slow_1p08V_125C/max.rpt` (U0 carrier-active latch to `dropped[6]`).
- Matched baseline and prototype chip reports: `/tmp/r4-candidate-cache/synth/chip/build/sta_slow_1p08V_125C_d066.txt`; `/tmp/r4-fabriccase-opt/synth/chip/build/sta_slow_d066.txt`; `/tmp/r4-fabricidx-opt/synth/chip/build/sta_slow_d066.txt`; `/tmp/r4-event-factor/synth/chip/build/sta_slow_d066.txt`; `/tmp/r4-satcounter-opt/synth/chip/build/sta_slow_d066.txt`; `/tmp/r4-carrierlvl-opt/synth/chip/build/sta_slow_d066.txt`. Mapped areas are in each directory's `stat_flat.txt`.

Checklist boxes ticked (evidence):
- None. The estimates are pre-layout and do not establish routed timing or behavior; physical Phase 2 signoff remains open.

Problems / decisions:
- All five local RTL hypotheses lost on the measured pre-layout timing/area tradeoff. The post-route path still includes the legal output-to-input pin feedback and live reconfiguration required by D-066.
- A one-clock delayed `DROPPED` update could remove counter accounting from this same-cycle path without changing protocol data traffic, but it changes the frozen F4/D-044 visibility timing. Do not implement it before a DECISIONS proposal and requester/Kanishk approval.

Next:
- Keep R4 at `cfc41e1` and 20 ns. Propose the `DROPPED` visibility timing change for team review, or obtain a route-aware optimization that preserves F4 exactly; do not harden any of these prototypes.

## 2026-09-30: Codex (phase 2: review four-thread hardening artifact)
Done:
- Reviewed the 2 GB artifact for run 36759109179. The candidate check passed for 2 lanes, 4 pin units, U0 full, 20 ns, and 56% density; the generated OpenROAD environment confirms `OPENROAD_THREADS=4`.
- The run generated final GDS and completed in about 3 h 48 min. Detailed routing took 2 h 44 min; final detailed-route DRC was 0, and antenna and LVS checks passed.
- Global routing still reported 143 overflow (142 on Metal3, 1 on Metal4). Signoff failed: slow-corner setup WNS -15.684 ns with 1,271 setup violations; typical WNS -2.213 ns with 81; max-slew/max-cap checks reported violations. Magic reported 57,924 markers in SRAM-exception rule classes, KLayout DRC was skipped, and 10 illegal overlaps were reported.
- The worst setup path is from U0's `carrier_active` latch to top-level `dropped[6]`, confirming this live reconfiguration path remains critical under D-066. Post-route summary also records two fast-corner hold paths at -4.6 ps, although the configured hold checker did not report a failure.
- No RTL, config, info, macro, or hardware candidate changed; no Phase 2 checklist box was ticked.

Evidence:
- Run 36759109179: https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36759109179.
- Artifact: `build/ci/r4/thread4/runs/wokwi/`; key reports are `39-openroad-globalrouting/openroad-globalrouting.log`, `44-openroad-detailedrouting/openroad-detailedrouting.log`, `55-openroad-stapostpnr/summary.rpt`, `62-magic-drc/reports/drc.magic.rpt`, and `warning.log`.

Checklist boxes ticked (evidence):
- None. Timing, congestion and complete DRC signoff remain unresolved.

Problems / decisions:
- The custom experiment stops after hardening and does not run the standard workflow's precheck, gate-level test or viewer jobs.
- The Magic DRC report names only SRAM-exception rules, but KLayout DRC was skipped and illegal-overlap checks reported 10; do not claim clean merged-GDS DRC.
- The 56%-density artifact's source baseline (`cfc41e1`) differs from the 59%-density run 7 source (`9138ee6`) in `trw_chip.v`, `trw_pin_cfg.v`, `trw_pin_tx.v`, and `trw_pin_unit.v`. Treat the density comparison as confounded; do not attribute the overflow change to density alone.

Next:
- Keep 20 ns and protocol behavior fixed. Use the critical `carrier_active`-to-`dropped` path and the slew/cap reports to guide one RTL optimization, then validate it with simulation, L2 lockstep and pre-route STA before another hardening.

## 2026-09-30: Codex (phase 2: check OpenROAD thread experiment result)
Done:
- Checked workflow run 36759109179. Candidate validation passed, but the full LibreLane hardening step failed after about 3 h 47 min; the always-run log/artifact upload step succeeded.
- Tried retrieving the job log and artifact for diagnosis. GitHub's API/log endpoints began returning connection errors from this environment before the detailed failure could be inspected.
- No hardware inputs changed. No Phase 2 checklist box was ticked.

Evidence:
- Run 36759109179: https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36759109179 (hardening step failed; artifact upload succeeded).

Checklist boxes ticked (evidence):
- None. GDS signoff has not passed.

Problems / decisions:
- The failure cause is not yet established from the detailed hardening log. Do not infer a routing or timing cause from the job-level failure alone.

Next:
- Retrieve and inspect the uploaded artifact and hardening log when GitHub's API is reachable; identify the failing physical-design stage before choosing another experiment.

## 2026-09-30: Codex (phase 2: dispatch explicit OpenROAD thread experiment)
Done:
- Set the GitHub CLI default repository to `Kanishk234/protocol-emulator-asic` after the initial dispatch failed because no default repo was selected.
- Dispatched `gds-thread-experiment.yaml` from `main` for `spike/r4-floorplan` with 4 OpenROAD threads. Candidate checkout and validation completed; full LibreLane hardening is running.
- No RTL, config, info, macro or candidate hardware inputs changed. No Phase 2 checklist box was ticked.

Evidence:
- GitHub Actions run 36759109179: https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36759109179 (hardening step in progress at last check).

Checklist boxes ticked (evidence):
- None. The experiment has not completed; GDS signoff remains unproven.

Problems / decisions:
- The experiment evaluates explicit thread count and runtime/physical results only. It does not run the standard workflow's precheck, gate-level test or viewer jobs.

Next:
- Monitor run 36759109179; inspect uploaded routing and signoff artifacts after completion before deciding on another flow experiment.

## 2026-09-30: Codex (phase 2: prepare explicit OpenROAD thread experiment)
Done:
- Confirmed R4 run 36656975727 is completed/cancelled after the 6 h limit; no GDS workflow is currently running on `spike/r4-floorplan`.
- Added `.github/workflows/gds-thread-experiment.yaml` on the default branch so GitHub can manually dispatch it. It checks out `spike/r4-floorplan`, rejects hardware changes from candidate `cfc41e1d67a1f9c8cbca4168f6979f4c17a999cc`, and verifies 2 lanes, 4 pin units, U0 full, 20 ns and 56% density.
- The workflow tests 4 threads by default (2 is available for a later separate run) using LibreLane 3.1.0.dev3's per-run `--override-config`. It leaves `src/config.json` and the standard `gds.yaml` workflow untouched; its hardening step is capped at 330 minutes and an always-run upload preserves available logs before the 6 h job limit.
- This targets the invalid `openroad -threads None` invocation seen in run 36656975727. The thread-count speedup and routing effect remain unmeasured.

Evidence:
- Current R4 workflow run 36656975727: `https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36656975727` (cancelled).
- Prior route database and logs: `/tmp/gds-36605194167-artifacts/GDS_logs/runs/wokwi/44-openroad-detailedrouting/`.
- LibreLane CLI override source: `https://raw.githubusercontent.com/librelane/librelane/3.1.0.dev3/librelane/flows/cli.py`.
- YAML syntax parsed successfully with the project virtualenv; `git diff --check` is clean.

Checklist boxes ticked (evidence):
- None. The manual experiment has not run and does not itself run the standard workflow's precheck, gate-level test or viewer jobs.

Problems / decisions:
- Local route replay is unavailable: no OpenROAD binary is on `PATH`; the cached binary lacks Tcl, OR-Tools and Qt libraries, and the pinned PDK is not installed.
- This full hardening experiment still has placement/routing variation. Compare overflow, detailed-route time, antenna repair, all-corner timing, and GDS signoff; a faster route by itself is not a pass.

Next:
- Commit and push this docs/workflow change on `main`, then dispatch `gds-thread-experiment` from `main` with candidate ref `spike/r4-floorplan` and 4 threads. Review its artifact before deciding whether to try 2 threads or request a supported persistent flow-setting exception.

## 2026-09-30: Codex (phase 2: research next 20 ns / 6x4 experiments)
Done:
- Reviewed R4 route-pass costs, physical inputs, RTL critical cones, and upstream Tiny Tapeout / LibreLane / OpenROAD documentation and source. Candidate remains `cfc41e1d67a1f9c8cbca4168f6979f4c17a999cc`, 2 lanes / 4 pin units / U0 full, 20 ns, 56% placement target; this is the measured candidate, not approval of final hardware counts.
- Found a concrete upstream thread-selection bug (#54): LibreLane 3.1.0.dev3 generates `openroad -threads None` because its fallback tests `str(None)` rather than the optional value. The archived route command confirms the argument; process statistics for the preceding run average about 100% CPU. OpenROAD source keeps its existing thread count for invalid input and initializes it to one. An explicit valid thread count is the first proposed experiment; its speedup and effect on physical results are unmeasured.
- Audited the SRAM signal LEF rectangles against the archived DEF's Metal2 X tracks: all 47 logged off-grid warnings are reproduced among 108 signal pins. Sweeping X phase over one 0.48 um pitch on a 0.005 um grid only reduces misses to 45. The best geometric shift is +0.45 um, which has not been checked against the tightly constrained PDN. A simple X nudge is not a strong fix; consider a Y-position change only if physical hotspots implicate the macro.
- Ranked follow-on experiments: increase early antenna-repair margin to reduce post-route repair passes; local cell-spacing or macro-Y changes guided by hotspots; cached configuration predicates using the existing word gate; balanced TX/RX arithmetic preserving every clock; synthesis strategy A/B; and a separate 30% to 18% global-routing capacity-adjustment diagnostic. Each is a hypothesis to test separately, not a demonstrated fix.

Evidence:
- R4 run 36656975727 raw log `/tmp/gh-cli-cache/run-log-36656975727-1790732994.zip`; archived prior run `/tmp/gds-36605194167-artifacts/GDS_logs/runs/wokwi/44-openroad-detailedrouting/COMMANDS`, process statistics, DEF and routing log.
- LibreLane pinned source: <https://raw.githubusercontent.com/librelane/librelane/3.1.0.dev3/librelane/steps/openroad.py> (`OPENROAD_THREADS`, `get_command`, antenna margins and route snapshots).
- OpenROAD thread fallback/default: <https://github.com/The-OpenROAD-Project/OpenROAD/blob/master/src/OpenRoad.cc> and <https://github.com/The-OpenROAD-Project/OpenROAD/blob/master/include/ord/OpenRoad.hh>.
- Placement and routing references: <https://openroad.readthedocs.io/en/latest/main/src/gpl/README.html>, <https://openroad.readthedocs.io/en/latest/main/src/grt/README.html>, <https://openroad.readthedocs.io/en/latest/main/src/drt/README.html>.

Checklist boxes ticked (evidence):
- None. No RTL, config, macro, info or workflow input changed; no hardening was started.

Problems / decisions:
- Threading addresses tool runtime and does not establish clean DRC, post-route timing, or cause of the stubborn-tile search. Keep all signoff checks and the 20 ns constraints active.
- `AGENTS.md` and `PHYSICAL_DESIGN_AND_CI.md` restrict project config edits to the clock, placement density and macro block. Persisting thread, antenna, padding or mapping settings requires an explicit exception to that rule; a local supported override / separate diagnostic workflow can evaluate them without editing template jobs.

Next:
- First reproduce valid thread selection and benchmark a route-stage replay with the pinned toolchain and preserved database, retaining DRC, antenna and timing reports. If runtime remains excessive, test early antenna repair next, then pick geometry or RTL work from retained hotspot/critical-path evidence. Any RTL candidate needs pin suites, million-clock L2 and both RTL injections before a single-change hardening.

## 2026-09-30: Codex (phase 2: test one-hot C-pin select prototype)
Done:
- In disposable `/tmp/r4-padsel-opt`, changed only the C-pin pad lookup from a dynamic vector index to a 24-bit one-hot decode and masked reduction. The active R4 worktree stayed clean at `cfc41e1d67a1f9c8cbca4168f6979f4c17a999cc`.
- Rebuilt the full-chip mapped netlist and ran matched pre-layout STA with configuration-latch paths timed under D-066. Against the carrier-cache candidate, worst typical slack regressed from +8.858 ns to +8.316 ns and worst slow-corner slack regressed from +2.717 ns to +2.045 ns. Mapped area fell only 45.25 µm² (390,666.74 to 390,621.50 µm²).
- Rejected the prototype: the small area reduction does not compensate for the timing regression, and it was not promoted to protocol simulation or the hardening candidate. No RTL, config, info, macro, workflow input, or Phase 2 checklist box changed.

Evidence:
- Prototype STA: `/tmp/r4-padsel-opt/synth/chip/build/sta_typ_1p20V_25C_d066.txt`, `/tmp/r4-padsel-opt/synth/chip/build/sta_slow_1p08V_125C_d066.txt`.
- Baseline matched STA: `/tmp/r4-candidate-cache/synth/chip/build/sta_typ_1p20V_25C_d066.txt`, `/tmp/r4-candidate-cache/synth/chip/build/sta_slow_1p08V_125C_d066.txt`.
- Mapped area: `/tmp/r4-padsel-opt/synth/chip/build/stat_flat.txt` and `/tmp/r4-candidate-cache/synth/chip/build/stat_flat.txt`.

Checklist boxes ticked (evidence):
- None. Physical Phase 2 signoff remains open.

Problems / decisions:
- The one-hot C-pin lookup is not a useful timing or area improvement. As a synthesis-only prototype, it has no behavioral test evidence.

Next:
- Keep the active R4 candidate unchanged. Before spending another multi-hour hardening, find a change with measurable benefit to detailed-route runtime/congestion or obtain route-stage diagnostics from a run that preserves the relevant database and hotspot reports. Any RTL candidate must preserve protocol behavior and D-066 timing, then pass pin tests, million-clock L2, and both RTL injections before hardening.

## 2026-09-30: Codex (phase 2: assess global-route adjustment experiment)
Done:
- Checked the run-366051 artifact and R4 config: the hardening used `GRT_ADJUSTMENT=0.30`; run 36656975727's router suggested 18% after 143 global-route overflows.
- OpenROAD defines this adjustment as a reduction in the routing capacity assumed by global routing. Lowering 0.30 to 0.18 gives GRT a less conservative capacity estimate; it can reduce reported overflow while producing less-spread route guides, so it does not establish better detailed routability or physical capacity.
- LibreLane exposes `GRT_ADJUSTMENT`, but the repository policy restricts `src/config.json` edits to the clock period, placement density, and SRAM macro block. The checked-in GDS workflow calls the Tiny Tapeout action without a route-setting override. No LibreLane, Nix, Docker, or Podman runner is installed here, and the available OpenROAD binary lacks runtime libraries needed to run a representative route.
- No RTL, config, flow, info, macro, or workflow input changed. No GDS run was launched and no checklist box was ticked.

Evidence:
- Run artifact: `/tmp/gds-36605194167-artifacts/GDS_logs/runs/wokwi/39-openroad-globalrouting/_env.tcl` (`GRT_ADJUSTMENT=0.3`) and `openroad-globalrouting.log`.
- Current route suggestion: GitHub Actions run 36656975727, raw job log `/tmp/gh-cli-cache/run-log-36656975727-1790732994.zip`.
- OpenROAD global-routing adjustment semantics: <https://openroad.readthedocs.io/en/latest/main/src/grt/README.html>.
- LibreLane configuration variable reference: <https://librelane.readthedocs.io/en/latest/reference/step_config_vars.html>.
- Workflow inputs: `.github/workflows/gds.yaml`; project config and workflow restrictions: `AGENTS.md` instructions supplied for this repository.

Checklist boxes ticked (evidence):
- None. Physical Phase 2 signoff remains open.

Problems / decisions:
- The 18% suggestion is a capacity-model diagnostic, not an established GDS fix. Testing it requires a supported local/temporary flow override or a separately approved project configuration change; neither is available in the current environment.
- The current failed run did not retain an OpenROAD database, so its stubborn detailed-route tiles still cannot be localized.

Next:
- Keep R4 RTL, 56% density, 20 ns clock, and counts fixed. Do not spend another hardening on the 18% setting without a valid local experiment and team approval. Continue with an STA-grounded RTL experiment that preserves all protocols, or obtain a complete flow environment and test the route knob only as a separate measurement. Any successful hardening must finish detailed routing in under 4 h and complete the DRC/LVS/antenna, typical timing, precheck, and gate-level checks.

## 2026-09-30: Codex (phase 2: trace R4 full-chip timing path)
Done:
- Rebuilt pre-layout chip netlists from exact pre-cache `0f506785e97d6c225b138181431e56fde7854aa2` and carrier-cache `cfc41e1d67a1f9c8cbca4168f6979f4c17a999cc` source snapshots. Ran the same STA with every configuration-latch path timed under D-066.
- The cache candidate improves matched pre-layout worst slow-corner arrival/slack from 17.648 ns / +1.719 ns to 16.792 ns / +2.717 ns. Typical arrival/slack improves from 11.385 ns / +8.164 ns to 10.756 ns / +8.858 ns. Mapped area changes from 391,017.2 to 390,666.7 µm². These ideal-clock estimates exclude routed wire parasitics and are not signoff timing.
- Traced the candidate's worst path: U0 cached carrier-active latch → U0 output logic → `uo_out[7]` → U2 pin selection (`u_io.sel`) → U2 RX state `rt[23]`. This follows the intentional feedback in `trw_chip.v`: driven `uo_out` pads are included in `pads`, which every pin unit samples.
- In a disposable `/tmp/r4-rt-opt` source copy, rewrote the RX timer update as one add of a selected precomputed step. The targeted U2 `rt[23]` path improved from 16.792 ns to 14.692 ns, but the overall worst slow path moved to U0 TX `eq[12]` and slack fell to +1.779 ns; mapped area rose by about 914 µm² from the cache candidate. Do not carry this variant into the hardening candidate based on this result.
- The prototype passed the R4 candidate pin suite under Verilator (60/60, FULL=1) and a 128-clock L2 smoke comparison (zero divergences). This is exploratory evidence only, not million-clock or injection signoff.
- Kept density at 56%, clock at 20 ns, and the R4 RTL/config inputs unchanged. No Phase 2 checklist box was ticked.

Evidence:
- Full-chip STA: `/tmp/r4-cache-baseline/synth/chip/build/sta_slow_1p08V_125C.txt`, `/tmp/r4-cache-baseline/synth/chip/build/sta_typ_1p20V_25C.txt`, `/tmp/r4-candidate-cache/synth/chip/build/sta_slow_1p08V_125C_d066.txt`, `/tmp/r4-candidate-cache/synth/chip/build/sta_typ_1p20V_25C_d066.txt`.
- Disposable RX-timer prototype reports: `/tmp/r4-rt-opt/synth/chip/build/sta_slow_d066.txt`, `/tmp/r4-rt-opt/synth/chip/build/sta_slow_rt_target.txt`, and `/tmp/r4-rt-opt/synth/chip/build/stat_flat.txt`.
- Source trace: `src/trw_chip.v`, `src/trw_pins.v`, `src/trw_pin_io.v`, `src/trw_pin_tx.v`; R4 candidate sources at `/tmp/r4-bitsync-work/src`. The rejected arithmetic variant is isolated at `/tmp/r4-rt-opt/src/trw_pin_rx.v`.

Checklist boxes ticked (evidence):
- None. Physical Phase 2 signoff remains open.

Problems / decisions:
- The cache improves the matched pre-layout timing estimate, but there is no post-route timing report or current OpenROAD database for run 36656975727. The report proves the logical feedback route, not the cause of the detailed-route runtime increase.
- Breaking or registering the pad feedback path could change pin timing semantics. Any next RTL trial should preserve combinational pad behavior and use a disposable source copy first.
- The first equivalent RX timer rewrite improves its target path but shifts the chip bottleneck and loses overall slack; it is not a viable next hardening change.

Next:
- Keep the active candidate and density 56% unchanged. Reject the RX timer rewrite for now. Inspect the newly exposed U0 TXMODE → `eq[12]` cone and look for a local simplification that does not increase area or worsen other critical paths. Any candidate must pass the full pin suite, million-clock L2, RTL injection checks, and matched chip synthesis/STA before proposing one new hardening change. Preserve the next run's OpenROAD database and detailed-route hotspot reports.

## 2026-09-30: Codex (phase 2: diagnose R4 detailed-route runtime)
Done:
- Compared detailed-routing logs for carrier-cache run 36656975727 (`cfc41e1`, density 56) and the prior pre-cache run 36605194167 (`0f50678`, density 56).
- Current run: first route pass took 3 h 11 min over 33 iterations; after 41 net / 44 pin antenna violations and 56 diode insertions, a second pass took 1 h 40 min over 28 iterations. A final pass took 3 min 46 sec. The log includes stubborn-tile iterations taking 22 min 29 sec, 32 min 3 sec, and 16 min 44 sec. Detailed routing ended with zero violations.
- Prior run: first route pass took 1 h 47 min over 8 iterations; antenna repair (48 violations, 64 diodes) took 11 min 30 sec over 6 iterations; the last pass took 4 min 36 sec. It had higher global-route overflow (1,090 versus 143).
- Route totals also ran against the intuitive congestion explanation: the cache run used about 292,056 guides and ended at 1,934,977 µm of detailed wire; the prior run used about 305,652 guides and ended at 2,021,692 µm. The cache run therefore had roughly 4.4% fewer guides and 4.3% less wire, but many more slow tile iterations.
- The mapped synthesis netlist grew modestly: the final ABC standard-cell list is 22,180 cells versus 22,033 in the prior run (+147, about 0.7%); Yosys's reported chip area is 408,331 versus 407,717 µm² (+614 µm², about 0.15%). A small area delta does not rule out a difficult local routing topology.
- The saved R4 pin-unit A/B reports isolate the cache's local effect with configuration paths timed (D-066): standalone full-unit worst arrival improved 16.273 → 14.937 ns (−1.336 ns), with the worst path moving from TXMODE word 0 bit 1 → `u_tx.eq[12]` to PERIOD word 4 bit 1 → `g_bs.u_bs.st_d[0]`. The wrapper area rose 90,985 → 91,244 µm² (+259 µm², about 0.28%) and gained one latch and one integrated clock gate. These are pre-layout pin-unit estimates, not full-chip routed timing.
- The mapped cache predicate is local in the pin-unit netlist: its state output drives three logic loads and its update uses one added integrated clock gate. That gives no obvious high-fanout explanation for the whole-chip runtime increase; a small topology/placement shift or run-to-run routing variation remains possible.
- The R4 RTL diff between the two candidates is the carrier-active cache in `trw_chip.v`, `trw_pin_cfg.v`, `trw_pin_tx.v`, and `trw_pin_unit.v`; both used density 56% and a 20 ns clock. This correlation identifies what changed, but without the current ODB/artifact it does not prove the cache caused the longer route search.
- Revised D-068: hold density at 56%; the evidence does not support raising it to 58% to fix the iteration pattern. No RTL, config, macro, info, workflow, or protocol semantics changed.

Evidence:
- GitHub Actions run 36656975727, raw log `/tmp/gh-cli-cache/run-log-36656975727-1790732994.zip`, `3_gds.txt`.
- Prior artifact `/tmp/gds-36605194167-artifacts/GDS_logs/runs/wokwi/44-openroad-detailedrouting/openroad-detailedrouting.log` and `runtime.txt`.
- Prior synthesis log `/tmp/gds-36605194167-artifacts/GDS_logs/runs/wokwi/06-yosys-synthesis/yosys-synthesis.log`; current synthesized-cell and area counts are in the raw run log.
- Pin-unit A/B summaries: `/tmp/r4-cache-baseline/synth/pin/build/summary.txt` and `/tmp/r4-bitsync-work/synth/pin/build/summary.txt`; the respective detailed slow-corner timed paths are in `sta_meas1_slow_1p08V_125C_cfg0.txt`.
- `git diff 0f506785e97d6c225b138181431e56fde7854aa2..cfc41e1d67a1f9c8cbca4168f6979f4c17a999cc -- src` identifies the only RTL changes between the two physical candidates.
- `git diff --check` clean.

Checklist boxes ticked (evidence):
- None. Phase 2 physical signoff remains open.

Problems / decisions:
- The current hardening did finish detailed routing, but needed about 5 h 9 min for repeated stubborn-tile iterations and antenna repair; the 6 h job limit then stopped Magic DRC during setup. Higher density could worsen local congestion and is not supported as the next lever by this evidence.
- Detailed-route iteration behavior is strongly associated with the cache candidate, but run-to-run causality is unproven because the current ODB and physical artifact were not retained.
- The cache has measured local timing benefit, so reverting it solely to recover route runtime would trade away a quantified 1.336 ns pin-block gain without proving the full-chip routing regression is caused by the cache.

Next:
- Keep the cache, density 56%, clock 20 ns, and protocol-floor resources fixed while selecting the next experiment. The next hardening decision needs current full-chip timing evidence and a way to inspect the detailed-route hotspot; the pin-unit A/B does not establish chip-level setup margin. Do not treat the density-58 proposal as approved.

## 2026-09-29: Codex (phase 2: prototype carrier predicate cache)
Done:
- Prototyped a cached one-bit carrier-active predicate in the isolated R4 worktree at baseline `0f506785e97d6c225b138181431e56fde7854aa2`. The derived latch updates in the same gated high phase as the carrier config words; TX uses it instead of recomputing `carrier[23:9] != 0`.
- Added a focused pin test for independent writes to both carrier words, including writes after activation. Updated the pin measurement harness and corrected the configuration timing comments to match D-066.
- Kept this as an experiment only. No main RTL, config, counts, info.yaml, macro, GDS workflow input, or model file changed; no hardening run was started.

Evidence:
- Verilator `-Wall` lint passed for the pin unit and `trw_pin_cfg` in FULL=0/1 and latch/flop configurations.
- Full candidate top-level Verilator `-Wall` lint passed across all 22 RTL modules.
- `source /home/younix/protocol-emulator-asic/.venv/bin/activate && make -C /tmp/r4-bitsync-work/test_internal/pin SRC_DIR=/tmp/r4-bitsync-work/src SIM=icarus FULL=1`: **60 passed**. FULL=0: **60 passed**. The added `test_carrier_active_tracks_both_config_words` passed.
- L2 smoke: 128 compared clocks, zero divergences. L2 full run: **1,000,000 compared clocks, zero divergences** (`RTL_REV=0f506785e97d6c225b138181431e56fde7854aa2-carrier-cache`).
- L2-INJECT against the modified candidate: clean RX and cursor baselines passed; priority-flip detected at clock 99; cursor off-by-one detected at clock 326.
- `synth/pin/run_pin.sh 20` mapped comparison against an archived baseline: full-unit measurement area rose 90,985 → 91,244 µm² (+259 µm²); local worst slow-corner path improved 16.273 → 14.937 ns (−1.336 ns). This is a pin-block estimate, not a full-chip routed result.

Checklist boxes ticked (evidence):
- None. The physical Phase 2 gate still needs a full hardening with timing, congestion, DRC/precheck, gate-level tests, and viewer evidence.

Problems / decisions:
- The cache appears worth a physical measurement: local timing improves with a small area increase and protocol tests remain green. The full-chip slow path may still be limited by the downstream pad/RX/fabric chain; only routing can confirm the gain.
- Candidate modifications are in `/tmp/r4-bitsync-work` and are not committed or pushed. The main checkout remains unchanged except this work-log entry.
- User selected this as the next hardening candidate. A live GitHub workflow check was attempted, but `gh` could not connect to `api.github.com`; verify no GDS hardening is active before pushing, since a push that changes RTL cancels it.

Next:
- After confirming no hardening is active, commit the R4 RTL, test, and measurement-harness groups and push `spike/r4-floorplan` for one hardening run. Keep the clock at 20 ns, density at 56%, and all protocol resources unchanged; judge the result by global-route overflow and timing as well as the remaining signoff gates.

## 2026-09-30: Codex (phase 2: inspect carrier-cache hardening timeout)
Done:
- Retrieved the raw GitHub Actions job log for candidate `cfc41e1d67a1f9c8cbca4168f6979f4c17a999cc` (2 lanes, 4 pin units, U0 full). The GDS job was cancelled at 6 h 1 min; `precheck`, `gl_test`, and `viewer` were skipped.
- The flow completed global routing with 143 overflow total (142 on Metal3, 1 on Metal4), compared with 1,090 on the previous density-56 run. It still reported congestion and suggested changing layer adjustment from 30% to 18%.
- Detailed-route DRC checker reported clear and the flow reached post-PnR STA, which finished all three corners, then Magic DRC setup. Its last output shows GDS hierarchy import reaching 340,000 `uses`, followed by loading the full DRC style. The job was cancelled before the log shows `drc check` running or any Magic DRC count; no run artifacts were uploaded.
- The detailed-routing step ran from 02:00:34 to 07:09:04 UTC (about 5 h 9 min), across three route passes. The first found 41 net / 44 pin antenna violations and inserted 56 diodes; the second found 2 / 2 and inserted 2 more; the last pass ended with zero detailed-route violations and zero antenna violations.

Evidence:
- GitHub Actions run 36656975727, raw job log for job 109703304444. The GDS job started at 2026-09-30 01:49:57 UTC and was cancelled at 07:51:01 UTC; the `Build GDS` action reports the operation was cancelled at 07:50:56 UTC.
- The archived prior candidate artifact for run 36605194167 (`/tmp/gds-36605194167-artifacts/GDS_logs`) reports detailed routing in 2 h 21 min and Magic DRC in 47 min, with about 345,000 GDS hierarchy `uses`. Its RTL was the pre-cache SHA `0f50678` at density 56; this run used the same density with the carrier-cache RTL. The current run's STA corners completed, but numeric timing metrics were not retained in its raw log or an artifact.
- The run cannot establish final setup/hold, Magic/KLayout DRC, LVS, antenna sign-off, precheck, gate-level, or viewer status.

Checklist boxes ticked (evidence):
- None. The physical Phase 2 gate remains open.

Problems / decisions:
- Routing congestion improved substantially, but global routing still had overflow. The carrier-cache candidate's detailed routing took about 2 h 48 min longer than the pre-cache run at the same density, despite a lower global-route overflow. The run had two antenna-triggered detailed-route reruns. The Magic import count is similar to the prior completed run, so it is not currently the leading runtime hypothesis; the six-hour limit stopped the job during Magic DRC setup.
- No RTL, configuration, flow setting, or protocol support was changed while diagnosing the log.

Next:
- D-068 proposes a single-variable density 56% → 58% measurement on the same carrier-cache candidate to test whether tighter placement reduces the detailed-route runtime. It is not approved yet; do not edit `src/config.json` or start another hardening until the requester and Kanishk approve. Preserve the 20 ns target and all protocol resources.

## 2026-09-29: Codex (phase 2: assess additional physical levers)
Done:
- Re-read the failed R4 slow-corner path and global-route report before the next hardening. The carrier reduction is only the first part of the path; the path then crosses multiple logic stages and a high-fanout repair-buffer tree before L1.I1's tap-drop counter.
- Identified two behavior-preserving RTL candidates for later measurement: replace the procedural selected-source loop in `trw_chan_port` with a balanced, explicit source mux, and optimize the saturating drop-counter next-state logic while preserving its same-cycle count and host-visible value.
- Identified two separate physical-flow experiments: test the router's suggested 16% layer adjustment as a diagnostic, and test a macro placement change only if a congestion map shows the SRAM blockage overlaps the hot region. Neither is approved by D-067, so each needs its own decision and single-variable run.

Evidence:
- Run 36605194167 slow `max.rpt`: carrier config bit 10 reaches the L1.I1 drop-counter D pin at 34.181 ns (slow WNS −13.037 ns). The path crosses an OpenROAD fanout buffer tree and additional fabric logic after the carrier decode.
- Run 36605194167 global-route log: total overflow 1,090, including 1,050 on Metal3; router suggests layer adjustment 30% → 16%. The floorplan uses one 236.8 × 191.34 µm SRAM macro at (12, 40) with 882 reported blockages.
- No additional RTL, config, flow, or count changes made in this brainstorm; no Phase 2 box ticked.

Problems / decisions:
- The carrier cache is worth a full-chip measurement. The prior slow-corner WNS was −13.037 ns; the 1.336 ns pin-block estimate uses a different, local timing model, so it cannot establish how much full-chip margin the cache recovers.
- Layer adjustment changes routing capacity estimates and guides; it does not itself prove clean physical routing. Macro movement and all non-approved config changes need separate review.
- No model-side work is needed; the proposed ideas preserve cycle semantics and need RTL/L2 checks if tested.

Next:
- Keep the carrier cache as the first single-change hardening candidate. If timing still fails, inspect the new full-chip critical path before selecting the fabric mux or counter as a follow-up change. Consider the routing-setting or macro-placement experiments separately if Metal3 overflow remains.

## 2026-09-29: Codex (phase 2: brainstorm protocol-preserving R4 options)
Done:
- Kept the 20 ns / 50 MHz target fixed. Reviewed the density-56 R4 result and the timed U0 `carrier[10]` → pad/RX/fabric → `dropped[26]` path; no RTL or flow settings were changed.
- Identified an untested RTL experiment: maintain a redundant one-bit `carrier_active` configuration latch in `trw_pin_cfg.v`, updated atomically when either word holding `carrier[23:9]` is written, then consume it in TX instead of recomputing the 15-bit reduction. This should preserve carrier behavior and protocol capability if the write/update timing is equivalent, but adds latch/decode cost and may leave most of the path delay untouched.
- Listed follow-on physical experiments: partition the general pad feedback/fanout path only where reports identify the delay, and separately measure an allowed CTS/route-setting change. The router's suggested layer adjustment is diagnostic and must not be treated as proof of a physical fix.

Evidence:
- `docs/reports/R4_FLOORPLAN.md` and GDS artifact for run 36605194167: 1,090 global-route overflow (1,050 on M3), typical WNS −0.683 ns, slow WNS −13.037 ns; clock target remains 20 ns.
- `docs/DECISIONS.md` D-066 requires live reconfiguration paths to remain timed; D-067 authorizes the density-56 branch-only result, not further settings or a main switch.
- `git diff --check`: clean before this entry; no hardware or config changes made.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- `carrier_active` was only a hypothesis at that point. It required cycle-accurate tests for writes to both carrier word halves before and after activation, full pin tests, L2, and routed timing/overflow measurement.
- No model-session work was needed. Existing model semantics already cover the legal live-reconfiguration behavior; revisit only if the RTL experiment exposes a semantic ambiguity.

Next:
- Prototype the derived carrier predicate in the isolated R4 worktree and measure it as one hardware change. Keep main, the 20 ns target, protocol resources, and GDS inputs unchanged until that evidence is reviewed.

## 2026-09-29: Codex (phase 2: evaluate R4 timing-cone rewrites)
Done:
- Followed the R4 slow-corner path from U0 `carrier[10]` through the pin output/readback and RX event path to `dropped[26]` (L1.I1). The path is consistent with the legal TX-to-pad-to-RX event and tap-drop behavior; it cannot be cut by a false path under D-066.
- Tested two single-file Boolean rewrites in the isolated R4 worktree: direct EV_EDGE-bit decoding in `trw_pin_rx.v`, and a mux form for the carrier-qualified output in `trw_pin_tx.v`. Neither was retained: generic Yosys cell counts rose from 682 to 695 for RX and 1,960 to 1,983 for FULL TX.
- Restored both RTL files to candidate `0f506785e97d6c225b138181431e56fde7854aa2`; no candidate RTL change remains.

Evidence:
- With the temporary EV_EDGE rewrite, `source .venv/bin/activate && make -C /tmp/r4-bitsync-work/test_internal/pin SRC_DIR=/tmp/r4-bitsync-work/src SIM=icarus FULL=1`: **59 passed**, including event timestamps, qualified START/STOP, carrier, UART/SPI/I2C-related pin modes, and BITSYNC.
- Generic Yosys `synth -top trw_pin_rx -flatten; stat`: baseline 682 cells, EV_EDGE rewrite 695. `synth -top trw_pin_tx -flatten` with FULL=1: baseline 1,960 cells, carrier mux rewrite 1,983. These are logic-count checks, not routed timing results.
- The R4 worktree was confirmed at candidate SHA `0f506785e97d6c225b138181431e56fde7854aa2` with the source files restored.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- These source rewrites did not establish a physical improvement and were discarded. No RTL, model, or config change remains.
- Raising `CLOCK_PERIOD` enough to cover the slow-corner deficit would require roughly 34 ns before margin (first-order estimate from the −13.037 ns WNS at 20 ns). That would lower the 50 MHz core target and reduce documented maximum SPI rates; it is not applied and would need a team performance decision.
- The model session has no prerequisite work for these physical experiments. Keep it on standby unless an RTL change raises a semantic question.

Next:
- Continue with a structural optimization of the general pad/readback path, using the timed carrier-to-RX-to-fabric cone as the target. Measure placed/routed timing and overflow before retaining a change; avoid changing clock target or protocol performance without a separate decision.

## 2026-09-29: Codex (phase 2: trace R4 post-route critical path)
Done:
- Traced the density-56 timing report and RTL on candidate `0f506785e97d6c225b138181431e56fde7854aa2`: startpoint is U0 carrier config bit 10 (packed word 13, bit 10); endpoint is `dropped[26]`, bit 2 of the L1.I1 consumer's saturating drop counter.
- The path is a timed configuration-to-pad/RX/fabric path under D-066. The report includes a high-load buffered net; a false path or change to live-reconfiguration semantics is not justified.
- Tried an isolated parallel decode for the pad-owner output mux in the R4 worktree. Its 1,500-cycle randomized mux test passed, but generic Yosys synthesis grew from 1,621 to 1,643 cells. Reverted the experiment because it did not demonstrate a physical timing gain and increased logic.

Evidence:
- Run artifact: `/tmp/gds-36605194167-artifacts/GDS_logs/runs/wokwi/55-openroad-stapostpnr/nom_slow_1p08V_125C/max.rpt` and `runs/wokwi/06-yosys-synthesis/tt_um_tripwire.nl.v`.
- `source .venv/bin/activate && make -C /tmp/r4-bitsync-work/test_internal/pins SRC_DIR=/tmp/r4-bitsync-work/src SIM=icarus`: randomized pad-owner/mux test passed (1,500 cycles) on the temporary rewrite.
- Generic Yosys `synth -top trw_pins -flatten; stat`: baseline 1,621 cells, parallel-decode experiment 1,643 cells. This is a logic-count comparison, not a routed timing measurement.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- The tested mux rewrite is discarded; the R4 RTL worktree is restored to its original candidate revision. No RTL or configuration change remains.
- No model-side work is needed for the current physical timing issue. L2 already covers this candidate; rerun it after any retained RTL change.

Next:
- Continue path-level RTL/netlist analysis to find a transformation that reduces the observed high-fanout/delay without changing pin timing or protocol behavior. Evaluate one retained hardware change at a time, then rerun functional checks before another hardening.

## 2026-09-29: Codex (phase 2: review R4 density-56 hardening)
Done:
- Re-read the Phase 2 exit checklist after L2 was completed and checked the result of R4 GDS run 36605194167 at candidate `0f506785e97d6c225b138181431e56fde7854aa2` (density target 56%).
- Confirmed the candidate branch's `test`, `unit`, `lint`, and `docs` workflows completed green: runs 36605194188, 36605194238, 36605194253, and 36605194365. These are on `spike/r4-floorplan`; the Phase 2 gate still requires green workflows on `main`.

Evidence:
- [GDS workflow 36605194167](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36605194167): `Build GDS` failed; dependent `precheck`, `gl_test`, and `viewer` jobs were skipped.
- Retrieved the exact run artifact at `/tmp/gds-36605194167-artifacts/GDS_logs/`; this is distinct from the older local `build/ci/r4/run7/GDS_logs.zip` (run 36526332067, commit `9138ee6`, density 59%).
- Global routing completed, but reports total overflow **1,090** (Metal2 11, Metal3 1,050, Metal4 29); Metal3 use is 82.59%. OpenROAD warns to reduce layer adjustment from 30% to 16% and says routing finished with congestion. Detailed-route DRC metric is 0, but that does not erase the global-route congestion result.
- Post-route setup WNS is **−0.683 ns typical** and **−13.037 ns slow** (1,277 slow-corner violations); fast corner has no setup violations. Hold passes all corners. Max-slew and max-cap checker warnings are also reported. The worst path starts at U0 pin configuration word 13 bit 10 (`carrier[10]`) and ends at `u_chip.dropped[26]`; keep it timed under D-066's approved live-reconfiguration contract.
- Magic reports **57,924** markers, matching the SRAM macro baseline recorded in `docs/reports/R4_FLOORPLAN.md`; KLayout DRC is disabled/skipped, so this run provides no merged-GDS KLayout DRC or precheck evidence. The illegal-overlap checker reports 10. LVS passes and antenna repair/check passes. The flow took about 3 h 26 min, within the 4 h target.
- Candidate `test`, `unit`, `lint`, and `docs` workflows were green (runs 36605194188, 36605194238, 36605194253, 36605194365), but on `spike/r4-floorplan`, not `main`.

Checklist boxes ticked (evidence):
- None in this session. L2 remains the only newly completed Phase 2 checklist item.

Problems / decisions:
- Density 56 improved over the preceding density-59 run documented in `docs/reports/R4_FLOORPLAN.md`, but still misses congestion and setup requirements. The Magic count appears to be the SRAM macro baseline, but independent KLayout DRC and precheck remain unproven; do not mark physical signoff clean.
- The protocol-floor counts remain a budget constraint, not final approved hardware counts; D-056 remains branch-only pending its evidence plan.

Next:
- Before another full hardening, diagnose the U0 `carrier[10]` to dropped-counter timing cone while preserving D-066 semantics, then choose one measured change. Separately evaluate the router's 16% layer-adjustment suggestion as a flow-only experiment; it is not evidence that the design itself has met congestion or signoff requirements. Require merged-GDS KLayout DRC/precheck evidence on the next run.

## 2026-09-29: Codex (phase 2: start R4 L2 RTL lockstep)
Done:
- Added a test-side Verilator/cocotb adapter for R4 that maps candidate debug taps by logical producer/consumer names and derives candidate host offsets from the R4 headers/generated fabric.
- Built a legal deterministic RX workload and a directed TX cursor workload. Both initialize lane slots, routine constants, pin configurations, and fabric ports before RUN.
- Verified the candidate revision `0f506785e97d6c225b138181431e56fde7854aa2`: 2 lanes, 4 pin units, U0 full. This is the candidate test shape, not a final count approval.

Evidence:
- Candidate revision verified from the worktree: `0f506785e97d6c225b138181431e56fde7854aa2`; shape is 2 lanes, 4 pin units, U0 full. This is only the candidate under test, not a final-count decision.
- `source .venv/bin/activate && L2_CYCLES=128 make -C test_internal/l2 SIM=verilator RTL_DIR=/tmp/r4-bitsync-work/src RTL_REV=0f506785e97d6c225b138181431e56fde7854aa2`: 128 compared clocks, zero divergences; the test also checks that the first two candidate reflex slots match the intended program before RUN.
- `source .venv/bin/activate && L2_CYCLES=1000000 make -C test_internal/l2 SIM=verilator RTL_DIR=/tmp/r4-bitsync-work/src RTL_REV=0f506785e97d6c225b138181431e56fde7854aa2`: **1,000,000 compared clocks, zero divergences** (628.57 s).
- `source .venv/bin/activate && python test_internal/l2/run_injections.py`: clean RX baseline passed (1,024 clocks); isolated priority-flip RTL mutation detected at compared clock 99; clean cursor baseline passed (1,037 comparisons); isolated cursor off-by-one RTL mutation detected at directed clock 326 (`unit_flags[0]`, expected 2 / mutated RTL 0). Each mutation ran from a temporary candidate copy; baseline R4 RTL was unchanged.
- GDS run [36605194167](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36605194167) on `spike/r4-floorplan`, candidate `0f506785e97d6c225b138181431e56fde7854aa2`, has completed with failure: `Build GDS` failed; `precheck`, `gl_test`, and `viewer` were skipped. This is separate from the L2 evidence.

Checklist boxes ticked (evidence):
- **L2**: the million-clock RX comparison and both required RTL injections passed, with clean unmodified RX/cursor baselines; evidence is listed above.

Problems / decisions:
- An initial smoke failure came from incorrect input-head/availability bit offsets in the new test adapter; the corrected map passed smoke and the full run.
- During bring-up, an RX rerun once reported an `r0`/`r1` difference at clock 99 even though its producer/port snapshots matched. The final testbench now verifies the exact loaded reflex words before RUN; subsequent 128-clock, 1,024-clock, mutation-baseline, and million-clock clean runs passed. The transient was not attributed to a candidate RTL change.
- An earlier three-command cursor experiment diverged at directed clock 1227 (`pads[0]`, model 0 / RTL 1); it was not used as evidence. The final cursor baseline uses one delayed LEVEL command, and the mutation runner requires a clean unmodified baseline before crediting a mutation.
- No RTL, `config.json`, `info.yaml`, macro, frozen semantics, or spec counts were changed. Candidate floor counts remain pending final budget and hardware decisions.

Next:
- Continue Phase 2 with the remaining unchecked hardware and L3 gates; keep the candidate-count decision separate from this L2 evidence.

## 2026-09-29: Codex (phase 2: record D-049/D-066 team approvals)
Done:
- Recorded the requester's and Kanishk's approval of D-049's protocol floor as a minimum budget constraint, not a frozen-spec count change.
- Recorded both approvals for D-066: preserve pin reconfiguration while lanes are halted and keep latch-to-state paths timed.
- Clarified D-067: the branch-only density/hold experiment does not authorize final counts or a main-branch switch. Existing spec counts remain 3 lanes / 6 units pending GDS review and a separate count decision.

Checklist boxes ticked (evidence):
- None. These approvals do not satisfy a Phase 2 verification or physical signoff item.

Problems / decisions:
- D-056's 0.10 ns hold uncertainty remains branch-only until all-corner hold signoff and `gl_test` pass.
- The final budget/count selection remains open until the active GDS evidence is reviewed; the approved D-049 floor constrains that decision but does not make it.

Next:
- Continue L2 against the explicit current RTL candidate counts once the RTL session provides its test-side signal adapter and common stimulus interface.

## 2026-09-29: Codex (phase 2: model-side L2 oracle preparation)
Done:
- Inspected the model and verification tree for L2-RAND/L2-INJECT. No lockstep runner, per-cycle scoreboard, or RTL fault-injection harness exists in the checkout.
- Added `tools/tripsim/lockstep.py`: a model-only snapshot from generated D-046 debug-map addresses and generated producer/consumer lists, plus a recursive first-difference reporter for a future scoreboard adapter.
- Added focused tests for snapshot coverage and field-level mismatch reporting. No model behavior, frozen semantics, spec counts, or RTL files changed.

Evidence:
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_lockstep.py tools/tripsim/tests/test_semantics.py tools/tripsim/tests/test_pinregs.py`: **94 passed**.
- Snapshot coverage derives actual lane/unit and fabric counts from the model/spec-generated definitions; the test does not assume the proposed budget floor is the final chip shape.

Checklist boxes ticked:
- None. This is model-side scoreboard preparation only; no RTL lockstep clocks or L2-INJECT run were performed.

Problems / decisions:
- The 1,000,000-clock Phase 2 gate requires a test-side RTL adapter/Verilator runner and a common stimulus stream; the model-side tree has none. L2-INJECT additionally needs executable RTL mutations for priority and cursor timing. These cannot be established by model-only tests.
- D-049's requester-approved 2-lane/4-unit protocol floor is not a frozen spec-count change; Kanishk's agreement for final budget lock/main switch remains unrecorded. Keep model defaults tied to the generated frozen 3-lane/6-unit spec until the team changes it.
- D-066's active-reconfiguration behavior is in the approved architecture contract; no semantic changes were needed here.

Next:
- Once the RTL test session provides a test-side adapter contract and the team settles counts, connect this snapshot to the cycle scoreboard, run ≥1,000,000 compared clocks, then run both L2-INJECT mutations.

## 2026-09-29: Codex (phase 2: R4 timing report cross-check)
Done:
- Cross-checked the model session's active-configuration audit against the run 7 post-route STA report and the routed netlist. The slow-corner worst path starts at U0 configuration `idle` (a latch output) and ends at `u_chip.dropped[26]`; it passes through the effective A input and RX/fabric logic. This confirms the path is functional under the current contract and must not be excepted.
- Confirmed that the report belongs to run 7's design commit `9138ee6`, which is an ancestor of `spike/r4-floorplan` HEAD `a594862`. No RTL or config change was made. The R4 source still carries proposed D-056 hold uncertainty 0.10 ns and target placement density 59%.

Evidence:
- `build/ci/r4/run7/GDS_logs.zip`, especially `runs/wokwi/55-openroad-stapostpnr/nom_slow_1p08V_125C/max.rpt`, `runs/wokwi/final/metrics.json` and `runs/wokwi/final/nl/tt_um_tripwire.nl.v`.
- Slow-corner post-route result: WNS -13.336 ns, 1,296 setup violations; typical WNS -0.934 ns, 27 violations; fast corner has none. Antenna/LVS passed, but detailed routing overflow and failed timing remain; precheck did not run.
- R4 worktree status: clean at `a594862`; shared main still contains the model session's three uncommitted files and was left untouched.

Checklist boxes ticked:
- None. No Phase 2 exit condition was newly satisfied.

Problems / decisions:
- D-066's audit rules out a false-path exception for the U0 `idle`-to-state path under the current H1/H1a/H2 contract. The active-config path is the dominant setup failure and has a deep RX-to-fabric cone; next physical experiment must preserve this timing check and protocol behavior.
- The R4 artifact has 1,503 global-routing overflow (1,438 Metal3), so timing and congestion both need attention. One hardware change per hardening still applies.

Next:
- Use the team-approved R4 budget/hold decisions to select one hardware or permitted floorplan knob for the next hardening. First candidate needs local RTL regression and synthesis evidence; then launch a new hardening and compare overflow and post-route timing.

---

## 2026-09-29: Codex (phase 2: verify R4 density experiment launch)
Done:
- Verified the user's pushes: `main` is at `ca61a1d` (`docs: approve R4 floor experiment`) and `spike/r4-floorplan` is at `0f50678` (`physical: test R4 placement density at 56`). Both local worktrees matched their origin branches before this worklog entry.
- Confirmed the main commit contains only `docs/DECISIONS.md`, `docs/WORKLOG.md`, and `docs/reports/R4_FLOORPLAN.md`; the R4 commit contains only `src/config.json`.
- Confirmed the intended R4 `gds` run started and its `Build GDS` step is running. R4 `docs` and `lint` have passed; R4 `unit` and `test` are still running. Main `docs`, `lint`, and `test` passed; main `unit` is still running.

Evidence:
- R4: GDS 36605194167, unit 36605194238, test 36605194188, lint 36605194253, docs 36605194365.
- Main: unit 36605092488; test 36605092410; lint 36605092385; docs 36605092402.
- `git status` confirmed both branches are clean after the pushes; `git diff --check` passed before this log update.

Checklist boxes ticked:
- None. The hardening is still running; no signoff or phase exit evidence yet.

Problems / decisions:
- R4 GDS has only just entered `Build GDS`; no placement, routing, timing, or signoff result is available yet.

Next:
- Monitor R4 GDS 36605194167 through global routing, detailed routing and signoff; report the measured overflow and timing before considering another change.

---

## 2026-09-29: Codex (phase 2: approve and prepare R4 density experiment)
Done:
- Recorded the requester's approval of the D-049 per-protocol resource floor, D-056's 0.10 ns hold setting for the branch experiment only, D-066's decision to retain live pin reconfiguration and time the latch paths, and D-067's 56% density experiment.
- Updated `R4_FLOORPLAN.md` to distinguish the earlier D-056 timeout (36455532221) from the newer area-pass hardening artifact (36526332067), and added its timing/routing/signoff results.
- Prepared the R4 config at density 56; no RTL or SDC changes. The upcoming branch push will start the GDS run.

Evidence:
- `build/ci/r4/run7/GDS_logs.zip`; updated D-049/D-056/D-066/D-067 and `docs/reports/R4_FLOORPLAN.md`.
- R4 `src/config.json` is valid JSON using the project venv; `git diff --check` passes in both worktrees.
- No Phase 2 checklist boxes ticked. Latest main unit workflow 36602221087 was still in progress at last check; latest GDS result 36526332067 failed setup.

Checklist boxes ticked:
- None. No Phase 2 exit condition was newly satisfied.

Problems / decisions:
- 0.10 ns remains branch-only until all-corner hold signoff and `gl_test` pass. Kanishk's agreement on the final budget lock and main-branch switch is still to be recorded.
- The density experiment tests routing and timing only; it does not prove the floor routeable and does not authorize a main-branch switch.

Next:
- User can now commit/push the main decision/report updates, then push the R4 config commit to start the branch-only GDS run. Review the workflow result before considering any main switch.

---

## 2026-09-29: Codex (phase 2: prepare R4 density candidate)
Done:
- Prepared the proposed R4 run 8 setting on the clean `/tmp/r4-bitsync-work` spike worktree: `PL_TARGET_DENSITY_PCT` 59 → 56, with RTL, counts, SDC and other flow settings unchanged.
- Added proposed D-067 on `main`, including the evidence, expected timing/routing tradeoff, and the requirement for team approval of D-049/D-056 before hardening.
- Confirmed the pushed main commit's docs workflow is green, unit is still running, and no R4 GDS workflow is active.

Evidence:
- `python -m json.tool /tmp/r4-bitsync-work/src/config.json`: valid JSON (project venv).
- `git diff --check` on both worktrees: clean.
- Branch-only config diff is two lines; main D-067 is in `docs/DECISIONS.md`.
- Workflow runs: main docs 36602220855 green; main unit 36602221087 in progress; latest R4 GDS 36526332067 completed with failure.

Checklist boxes ticked:
- None. No Phase 2 exit condition was newly satisfied.

Problems / decisions:
- D-067, D-049 and D-056 remain proposed. Do not push the R4 config or start hardening until the team approves the density test and budget/hold assumptions.
- The active pin-configuration path remains timed per D-066.

Next:
- Get the team's go/no-go on the prepared single-variable density experiment. If approved, the user can commit/push the main decision record and the R4 config change separately; then inspect the new GDS run.

---

## 2026-09-29: Codex (phase 2: next R4 floorplan experiment)
Done:
- Compared the archived run 6 job log, the earlier D-056 run 7 summary, and the newer `build/ci/r4/run7/GDS_logs.zip` artifact. The newer artifact is from commit `9138ee6`, with area/BITSYNC RTL changes in addition to the 0.10 ns hold setting; it is distinct from the earlier run 7 timeout summarized under D-056.
- Confirmed the newer artifact used `PL_TARGET_DENSITY_PCT=59`, produced about 54.5% standard-cell / 56.8% total instance utilization after placement, and still reported 1,503 global-route overflow (1,438 on Metal3). Its slow setup WNS is -13.336 ns and typical is -0.934 ns.
- Identified a bounded, protocol-preserving next experiment: keep the same R4 RTL/counts and hold SDC, and lower only `PL_TARGET_DENSITY_PCT` from 59 to 56. This stays above the measured standard-cell utilization while testing whether less local placement pressure reduces Metal3 overflow. The expected tradeoff is that wire lengths and setup timing may move either way; both must be measured.

Evidence:
- `build/ci/r4/run6/gds_job.log` and `build/ci/r4/run7/GDS_logs.zip`.
- Run 7 artifact: `runs/wokwi/final/metrics.json`, `runs/wokwi/39-openroad-globalrouting/or_metrics_out.json`, `runs/wokwi/55-openroad-stapostpnr/nom_slow_1p08V_125C/max.rpt`, and `runs/wokwi/55-openroad-stapostpnr/nom_typ_1p20V_25C/max.rpt`.
- `docs/design/PHYSICAL_DESIGN_AND_CI.md` §5 permits `PL_TARGET_DENSITY_PCT` as a floorplan knob and requires judging changes by global-routing overflow.

Checklist boxes ticked:
- None. No Phase 2 exit condition was newly satisfied.

Problems / decisions:
- The D-056 0.10 ns hold setting is still proposed, and the D-049 budget remains a team decision. A run at 56% would be a branch-only measurement, not evidence to switch the setting or floorplan to `main`.
- No config or RTL was changed and no hardening was launched. The live pin-configuration path remains timed per D-066.

Next:
- Ask the team to approve the budget/hold assumptions and the single-variable 59% → 56% R4 density experiment. If approved, make that config change with its decision record, run local source checks, and let the user push to start hardening.

---

## 2026-09-29: Codex (phase 2: active pin-config timing audit)
Done:
- Audited D-038/D-041 and ARCHITECTURE §7.2 / §14 H1, H1a and H2 against the host-map model. A host may write pin configuration after activation once all lanes are halted; `live` remains set and pin units keep clocking. Recorded the timing-contract conflict and choices for team decision as proposed D-066.
- Added `test_pin_config_can_change_after_activation_when_lanes_are_halted`: it rewrites the full configuration through generated `HOST_MAP` and proves the new pin selection is sampled on the next live unit clock.
- Left frozen spec counts and all RTL/SDC untouched. `test_pinregs.py` already derives feature checks from generated `PIN_UNIT_FEATURES`; no budget/count change was made.

Evidence:
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py tools/tripsim/tests/test_pinregs.py`: **92 passed**.
- Mutation that rejected pin-config writes whenever `live` was set failed the new test at the first config write. Mutation that stopped pin-unit compute/commit when all lanes were halted failed it at the next pin-unit sample. Both mutations were reverted.
- `git diff --check`: clean.

Checklist boxes ticked:
- None. L2 remains unstarted.

Problems / decisions:
- D-038's false-path rationale assumes configuration latches stay static while active. The current H1/H2 + D-041 contract permits active pin units to see new config after lane HALT, so latch-to-state setup paths cannot be excluded under that contract. D-066 asks the team whether to time these paths or change the reconfiguration contract.
- `PHASE2_RTL_CORE.md` in this checkout has sections 1–5 and no §7.4; `docs/HANDOFF.md` is absent. Continued from the newest WORKLOG and the governing architecture/decision text.
- D-049/D-056 lane/unit budget decision remains with the RTL session. Counts remain frozen at the spec's 3 lanes / 6 units; L2 and any count-bound change wait for that decision and green model/CI evidence.

Next:
- Get the D-066 contract/timing decision and the RTL session's D-049/D-056 counts. Then rerun generated-count model checks and complete remaining pre-L2 evidence before starting lockstep.

---

## 2026-09-28: Codex (phase 2: R4 run 7 review)
Done:
- Read the completed R4 run 7 logs and recorded its physical result in `R4_FLOORPLAN.md`, `AREA.md` and D-056.
- Run 7 reduced hold-violation endpoints (1,891 → 540) and global-routing overflow (5,350 → 4,198), but timed out in detailed routing at 143 violations. No signoff, precheck, viewer or `gl_test` evidence was produced; D-056's evidence plan remains unmet.
- Identified the R4 branch unit failure: seven `test_pinregs.py` failures on the old count-bound assumptions; the branch RTL and Verilator jobs passed. Main workflows for `59dec5f` (unit/test/lint/docs) are green.

Checklist boxes ticked:
- None. No Phase 2 exit condition was newly satisfied.

Problems / decisions:
- Do not treat 0.10 ns hold uncertainty or the D-049 protocol floor as validated by this run. The floor still needs a new, team-selected physical experiment.
- The other session's tripsim edits remain shared and untouched by this RTL review.

Next:
- Compare run 7's route diagnostics with run 6 and make the D-049/D-056 budget and physical-design decision with Krithik and Kanishk before preparing another hardening.

---

## 2026-09-28: Codex (phase 2: implement approved D-057–D-065 model readings)
Done:
- Krithik and Kanishk approved the recommendations. Updated P8/P17/P20/P23/P25/P26/P28/P30 in `docs/design/ARCHITECTURE.md` and recorded approvals/evidence under D-057–D-065.
- Updated `tripsim` for the approved PULSE minimum, carrier threshold/phase, BITSYNC idle sample, P8 event priority, response-JAM acceptance, bare JAM [0], foreign-frame stuff errors and one-entry output wait. P-G33 already matched the approved rule; its spec clarification and focused test were retained.
- Fixed BUGS #53: a P8 event plus a queued BITSYNC output could request two same-clock producer loads.

Evidence:
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py tools/tripsim/tests/test_pinregs.py`: **91 passed**.
- Tripsim suite with sigrok hidden from PATH: **133 passed, 2 skipped**; the two skipped UART sigrok cases and the four deselected kernel SPI/I2C sigrok cases were then run unsandboxed with the project venv: **6 passed**.
- Under the sandbox, `sigrok-cli` returned no UART/SPI/I2C annotations and reported `libusb_init() returned LIBUSB_ERROR_OTHER`; outside the sandbox, all six annotation checks passed. This isolates the discrepancy to sandboxed sigrok/libusb initialization, not the model waveforms.
- Required UART/SPI/I2C and I2C/SPI target suites: **34 passed** (the four sigrok checks were separately run unsandboxed and passed).
- PULSE/IR carrier/HDLC/selected CAN regressions: **15 passed**; CAN error-handling suite: **5 passed**; USB-LS feasibility suite: **2 passed**.
- Revert mutations for P-G24, P-G25, P-G26, P-G28, P-G29, P-G33, P-G36, P-G38, P-G40 and P-G41 all failed their focused tests.
- `git diff --check`: clean.

Checklist boxes ticked:
- None. L2 remains unstarted; count/budget selection still waits for GDS.

Problems / decisions:
- D-049/D-056 count/budget decisions remain with the RTL session pending its run 7 review; this model session left the generated 3/6 counts unchanged. USB-LS remains a feasibility study, not a support claim.
- The test-backed resource floor in D-049 retains the 20 compiled programs at 2 lanes, 4 units with U0 full, 12 slots and 512 SRAM words. Physical routability is not established by this model session.

Next:
- After the team freezes counts, rerun model count checks and obtain green CI for these changes; only then hand off to the separate L2 test-side session.

---

## 2026-09-28: Codex (phase 2: protocol compatibility check before approved model updates)
Done:
- Checked the approved D-057–D-065 recommendations against the stated protocol scope and D-049's measured program resource floor; no feature or resource is removed by the recommendations.
- Confirmed the required UART, SPI controller and I2C controller, plus the I2C/SPI target showcases, against their tripsim reference tests before changing the disputed readings.

Evidence:
- `PATH=/home/younix/protocol-emulator-asic/.venv/bin python -m pytest -q tools/kernels/tests/test_uart.py tools/kernels/tests/test_spi_controller.py tools/kernels/tests/test_spi_target.py tools/kernels/tests/test_i2c_controller.py tools/kernels/tests/test_i2c_target.py -k 'not sigrok'`: **34 passed, 4 deselected**. Used the project venv and deselected external sigrok annotation checks because the local decoder returned no annotations.
- `docs/design/OVERVIEW_TRIPWIRE.md` lists UART/SPI/I2C as required; I2C/SPI targets as core showcases; CAN as stretch; USB-LS as not planned. `programs/README.md` explicitly labels `usb_ls.trw` a feasibility study, not a support claim.
- D-049 records the 20-program floor: 2 lanes, 4 units with U0 full, 12 slots and 512 SRAM words. The all-kernel test run was interrupted before a summary; no result is claimed for it.

Checklist boxes ticked:
- None. No model semantics changed and L2 remains unstarted.

Problems / decisions:
- Krithik and Kanishk approved the recommendations; implementation and post-change regression remain next. GDS/budget outcome still decides whether the floor or larger frozen counts are used.
- USB low-speed remains an unclaimed feasibility study, consistent with the overview's “not planned” scope.

Next:
- Apply the approved D-057–D-065 clarifications/model updates with focused tests and revert mutations; rerun protocol model regressions before beginning L2.

---

## 2026-09-28: Codex (phase 2: complete pin-reading review through P-G47)
Done:
- Added focused P-G33–P-G47 tests to `tools/tripsim/tests/test_semantics.py` and revert-mutation checks for each behavior.
- Confirmed P-G34/P-G35, P-G37/P-G39, and P-G42–P-G47. Recorded model/spec-reading differences for P-G33, P-G36, P-G38, P-G40 and P-G41 as D-061–D-065; no behavior changed.
- Added a `test_pinregs.py` check proving default lane and unit counts follow generated definitions; reverting either default to a fixed 3 or 6 fails.

Evidence:
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py tools/tripsim/tests/test_pinregs.py`: **91 passed**.
- Full tripsim suite: **133 passed, 2 failed**. The only failures are `test_uart_tx_shift_decoded_by_sigrok` at both baud rates; `sigrok-cli` returned no UART annotations for the generated VCD. Its startup also reports `libusb_init() returned LIBUSB_ERROR_OTHER`; root cause is not established, so this is recorded as an unresolved environment/check issue rather than a model bug.
- Each focused test's revert mutation failed, including TX queue terminal stuffing, JAM acceptance, foreign-frame stuff errors, event queue depth, readback mode, JAM disarm, TX run count, listen-only clearing, abort-event fields, and the SE0 condition.
- `git diff --check`: clean.
- Pushed workflows for `0b3b8e9`: [unit](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36486427059), [lint](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36486427054), [test](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36486427153), and [docs](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36486427097) all succeeded.

Checklist boxes ticked:
- None. L2 remains unstarted.

Problems / decisions:
- D-057–D-065 contain proposed clarifications/contests; team decisions are needed before changing those behaviors. No new BUGS entry was warranted because these are unresolved reading differences, not established implementation bugs.
- The seven `test_pinregs.py` cases now select feature-capable and lean units from generated `PIN_UNIT_FEATURES`; the added default-count test and fixed-count revert mutations confirm model construction follows generated lane/unit counts. The team budget/count decision remains pending, so the frozen spec counts remain in effect.
- No checklist boxes were ticked; the full tripsim suite is not green with the two sigrok annotation failures.

Next:
- Apply the team’s decisions to D-057–D-065, then complete count/budget review and its remaining tests. Start L2 only after the model prerequisites and evidence are ready.

---

## 2026-09-28: Codex (phase 2: D-044/D-045 model confirmation)
Done:
- Added focused D-044 coverage for a port reconfiguration cancelling a same-clock take, and D-045 coverage for no fetch during EXEC/waiting plus RPC advance at fetch.
- Recorded the model confirmation of the D-044 and D-045 readings in `docs/DECISIONS.md`.
- Added a fractional CARRIER check for D-051 P-G26. It exposes a model/spec-reading disagreement for 5.5-clock periods; recorded as proposed D-058 without changing behavior.
- Added checks for D-051 P-G24/P-G25 and D-052 P-G29, documenting differences from the milestone readings in D-057/D-059 without changing behavior.
- Added a D-052 P-G28 event-generator check and confirmed D-053 P-G27/P-G30 (stuff-error bit count and FRAME verdict). P-G28 is proposed in D-060; P-G27/P-G30 have focused mutation evidence.
- Added D-054 P-G31 focused coverage: WAIT [1] clears at the sample point and permits TX DATA acceptance that clock; a revert mutation fails.
- Added D-054 P-G32 coverage for opening our frame on the next bit boundary and loading EVENT `0x9001` on that clock; a boundary mutation fails.
- Added D-054 P-G33–P-G35 checks. Empty-queue terminal stuffing disagrees with P-G33 and is proposed as D-061; frame-start stuffing reset and released-line own-edge/idle behavior match P-G34/P-G35.

Evidence:
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py tools/tripsim/tests/test_pinregs.py`: **75 passed**.
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py -k fractional_carrier`: **1 passed**; rounding the period to whole clocks killed the test.
- Revert mutations for zero-tick pulse timing, sub-two-clock carrier suppression, and inclusion of the BITSYNC idle-making sample each failed the focused check.
- Revert mutations for BITSYNC event bypass, stuff-error bit count, and FRAME verdict threshold each failed the focused check.
- Reverting P-G31's wait clear also fails its focused check.
- Delaying the P-G32 frame-open condition by one clock fails its focused check.
- Mutations changing the frame-start stuffing reset or treating a released line as driven for own-edge or idle checks fail their focused tests.
- Revert mutation removing D-044's take cancellation failed (`port.takes` became 1); removing the D-045 fetch guard failed during EXEC; removing the RPC increment failed the RPC assertion.
- `git diff --check`: clean.
- Pushed workflow run [36484905620](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36484905620): unit, lint, test, docs and all RTL/Verilator jobs completed successfully.

Checklist boxes ticked:
- None. L2 remains unstarted; D-051–D-055 and the count/budget decision are still pending.

Problems / decisions:
- No disagreement with D-044/D-045 readings found. D-057's P-G24/P-G25/P-G28, D-058's P-G26, D-059's P-G29, D-060's P-G28, and D-061's P-G33 proposals remain unresolved; none of their semantics changed. D-053 P-G27/P-G30 and D-054 P-G31/P-G32/P-G34/P-G35 are confirmed.
- The Phase 2 RTL checklist L1 edit is an existing, separate workspace change and is not part of this model session's code changes.

Next:
- Continue focused tests and revert mutations for P-G24–P-G47, recording any contested reading through DECISIONS before changing semantics.
- Obtain the count/budget decision, then audit remaining count-bound tests. Start L2 only after all prerequisites are ready.

---

## 2026-09-28: Codex (phase 2: implement approved D-041 A/B)
Done:
- Recorded Krithik's approval on behalf of both teammates for D-041 A (every pin-config word write restarts that unit and clears sticky flags) and B (pin units stay inactive until the first valid RUN or STEP) in `docs/DECISIONS.md`.
- Implemented restart state and `t_cfg` event epoch in `tools/tripsim/pinunit.py`; pin-config writes through the host map now apply the same rule. The RUN readback reports `live` at generated `HOST_RUN_LIVE_BIT`.
- Gated pin-unit RX/TX compute and commit until `Chip.run()` or an eligible STEP. Updated direct pin-only model fixtures to RUN an empty lane first. Updated P8/H1 in `ARCHITECTURE.md` to record the approved semantics.
- Added D-041 A/B tests; mutation checks that zeroed `t_cfg` and bypassed live gating both failed their focused tests.

Evidence:
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py`: **45 passed**.
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py tools/tripsim/tests/test_pinregs.py`: **64 passed**.
- `source .venv/bin/activate && pytest -q tools/tripsim/tests -k 'not uart_tx_shift_decoded_by_sigrok'`: **106 passed, 2 deselected**.
- With sigrok present, high-rate UART decode and CAN sigrok assertions produce empty decoder output despite passing model-side protocol/reference assertions. A protocol-kernel run without the sigrok assertions was started but interrupted before a final result; kernel-suite status remains unverified.

Checklist boxes ticked:
- None. L2 remains unstarted and no CI run was performed.

Problems / decisions:
- D-041 A/B are approved and implemented. D-046 host pin-config writes now work while all lanes are halted and trigger A; valid RUN/STEP activates units and the RUN status exposes B.
- The initial D-044 F5/invalid-select checks and D-045 fetch timing/ignored-write tests remain, but D-044 same-edge config-vs-take and D-045 no-fetch-while-waiting/RPC mutation coverage are still open.
- D-051–D-055 still need per-reading `test_semantics.py` tests and revert mutations. D-057 records P-G24/P-G25/P-G28 discrepancies as a proposal; no behavior change made for them.
- Lane/unit counts remain the frozen 3/6. The count-bound test assumptions found in `test_pinregs.py` now use the generated feature list; the team budget decision is still needed before any spec count change.
- No BUGS entry was added for empty sigrok output because its root cause was not established in this model session.

Next:
- Complete D-044/D-045 focused tests and mutations; review every P-G24–P-G47 reading in D-051–D-055 and add focused tests/mutations, resolving disagreements through DECISIONS before behavior changes.
- Obtain the area/count decision, audit count-bound tests, and begin L2 only when all model prerequisites pass.

---

## 2026-09-28: Codex + Krithik (phase 2: L1 checklist)
Done:
- Marked Phase 2 exit box 3 (L1 unit tests) complete using the green `unit` workflow on `main` at c2a1c04.

Checklist boxes ticked (evidence):
- [x] L1 unit tests all green: GitHub Actions `unit` run 36456739733.

Problems / decisions:
- None.

Next:
- Run the model-side L2 prerequisites in a session that does not read `src/`; wait for R4 run 7 before deciding the area budget and D-056.

## 2026-09-28: Codex (phase 2: model-side L2 prerequisites)
Done:
- Added address-based `Chip.host_read()` / `host_write()` for the approved D-042 flags, D-044 port/DROPPED registers, and D-046 control/status, lane debug, HOST_IN/HOST_OUT, and SRAM map. Address ranges and names come from generated `HOST_MAP`; port source ordering comes from generated `LEGAL_SOURCES`.
- Made default lane/unit counts derive from the frozen generated fabric and pin feature definitions. Changed `test_pinregs.py` count assumptions to use `PIN_UNIT_FEATURES`.
- Added focused semantics checks for flag W1C, D-044 F5/same-edge load and clear, out-of-range `sel`, D-046 tagged HOST_IN and lane debug, plus D-045 fetch/EXEC timing and ignored running-lane writes.

Evidence:
- `source .venv/bin/activate && pytest -q tools/tripsim/tests/test_semantics.py tools/tripsim/tests/test_pinregs.py`: **61 passed**.
- Full `tools/tripsim/tests`: **103 passed, 2 failed** (the same high-rate UART sigrok cases; 1,000,000 and 921,600 baud).
- Mutation checks: forcing D-042 reads to zero failed `test_d042_unit_flags_are_readable_and_write_one_to_clear`; inverting the D-044 F5 sequence snapshot failed `test_d044_host_port_map_f5_and_dropped_clear`.
- Full `tools/tripsim/tests`: **102 passed, 2 failed** in high-rate UART TX sigrok cases (1,000,000 and 921,600 baud, sigrok decoded no bytes); failure reproduced in isolation. Root cause not established, so no BUGS entry or claim that this was pre-existing.

Checklist boxes ticked:
- None. L2 has not started; this session did not establish the required million-clock lockstep or injection evidence.

Problems / decisions:
- D-044 readings are consistent with model behavior: source `seq` is snapshotted when the host writes the port, an out-of-list `sel` resolves to no source, and config takes precedence because the host configuration is applied before the model's next fabric edge. F5 and invalid `sel` have focused tests; the config/take case still needs a precise same-edge model test and mutation.
- D-045 readings are consistent with the model's registered SRAM rotation and pipeline; focused tests cover fetch-to-EVAL/EXEC and ignored STEP/host writes while running. Mutation coverage is still needed.
- D-051–D-055 readings have not yet each been reviewed and pinned by new `test_semantics.py` tests/mutations. Do not count this prerequisite complete. P-G24, P-G25 and P-G28 were checked in source and recorded in D-057, but still lack focused test/mutation evidence.
- D-057 now records three concrete proposed clarifications from the review: P-G24 zero-tick duration, P-G25 sub-2-clock carrier, and P-G28 BITSYNC event generation/priority. No model behavior was changed for these unresolved comparisons.
- D-041 A/B remain pending. The exact missing decision is Krithik and Kanishk's approval or rejection of: **A**, any write to a pin-unit config word restarts TX/RX/cursor/tick/prescaler and clears sticky flags; **B**, pin units and their producers remain inactive until the first RUN or STEP, including STEP setting `live`.
- Lane/unit spec counts remain 3/6. The team area/budget result (including the pending R4 run 7 / D-056 decision) is still needed before changing those frozen counts. Dynamic count handling is in place; the requested seven count-bound `test_pinregs` cases were not identified in this checkout and remain to audit against the settled budget.
- `host_read`/`host_write` model the register map, not SPI bit timing. Slot/K and owner writes plus packed channel debug readback are now covered. Pin-config writes still await D-041 A/B so their restart/live semantics are not guessed; full D-046 map support is therefore incomplete.

Next:
- Finish the D-046 host address paths and add focused D-044 configuration-vs-take coverage.
- Review every P-G24–P-G47 model reading in D-051–D-055, add one semantics test and a revert mutation per rule, and record disagreements as proposed DECISIONS/spec changes before changing model semantics.
- Obtain D-041 A/B and area/count decisions, finish count-bound tests, then begin L2 lockstep only after all prerequisites pass.

---

## 2026-09-28 (later): Krithik + Claude (phase 2: R4 run 6 result; count-generic tests; milestone B3)
Done:
- **R4 run 6** (gds 36384571157, the real `trw_chip` at the protocol floor): GPL 56.1 %, **global-routing overflow 5,350** (Metal3 87.3 %), detailed routing 16 violations after 64 iterations in 4 h 53 min, then cancelled by GitHub's 6 h limit in the antenna re-route; no artifacts. Read from the job log. `R4_FLOORPLAN.md` §12, AREA, D-043. The floor as built does not harden inside the TT `gds` job (a local hardening would not count: every entry uses the same workflow).
- **Count-generic tests** (BUGS #52): `tb_chan.v`, `tb_host.v`/`test_host.py`, `test_gen`, `tools/host` and `tripc` tests take the lane/unit counts from the spec. Pass at 3/6 (main: pytest 292, chan 7/7, host 7/7 under Icarus and Verilator) and at 2/4 (branch copy: pytest 285 + the 7 `test_pinregs` cases, all `rtl` suites, pin 52/52 ×2, chip 10/10).
- Area by block at the floor (Yosys, `synth/chip/run_chip.sh`): pin units ~201K, lanes 150K, fabric + producers 35K, host 22K.
- **Milestone B3** (Krithik: B3 first, then the area pass): readback and arbitration, bit errors, JAM responses and armed flags, listen-only, DELIM = flag with the hold-back and aborts, NRZI, SE0 with J, pin N low in SE0, DELIM = se0, OE auto, data[14] "own frame", a one-entry status EVENT register. Tests `test_pin_bs_b3.py` (7) against the reference CANNode (arbitration, ACK, error flags), `protomodels.hdlc` (±1 % drift, bad FCS, abort) and `protomodels.usb` line states (TX bit for bit, RX of four packets). Pin suites 59/59 on both builds under Icarus and Verilator; chip tests 10/10; mutants B3 34/34 and B2 31/31 killed; `scripts/check_all.sh` PASS. Engine 43.2K, full unit ~81.9K; chip 632.2K at spec counts (+7.09 typ / +0.02 slow), **407.6K at the protocol floor**. D-055 (readings P-G36–P-G47). Milestone B is complete.

- **RTL area pass** (behaviour-preserving, Krithik's order after B3): lanes −6.5K each (merged register read/write ports), TX −0.3K each, engine −1.1K; the floor chip 407.6K → **391.7K**. Lane 6/6 + 15/15 mutants; pin 59/59 both builds; milestone-B mutants 70/70 (the lean/full mutant filter fixed: B2/B3 mutants no longer run on the lean build). `R4_FLOORPLAN.md` §14.
- **Flow growth found:** run 6 grew 466.2K → 567.7K before routing (fanout repair +25.3K, clock tree +24K); hold repair was +52.3K at 1,891 endpoints, caused by the 0.25 ns clock uncertainty applying to hold. Locally at the fast corner (run 5's post-CTS netlist): 1,546 violations at 0.25 ns, 29 at 0.10 ns. **D-056 (proposed): hold uncertainty 0.10 ns.** R4 run 7 prepared (run 6's design + that change) in `~/tw-r4`. §13.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- Run 6: the chip must come down ~40–60K µm² (to run 5's ~340K) or change the floor. Needs the team (D-049/D-043); no D-055 written yet.
- 7 `test_pinregs` cases still hard-code U1 full (in `tools/tripsim/`, not read in this RTL session).

Next:
- Push R4 run 7 (hold uncertainty 0.10 ns); read hold endpoints, utilisation after GRT, overflow, DRT time, sign-off hold at every corner. Then D-056 for the team.

## 2026-09-28: Krithik + Claude (phase 2: milestone B2c; engine retimed; R4 run 6 prepared)
Done:
- **Milestone B2c** in `trw_pin_bs.v`: the TX queue (DATA, SYNC, LINE [2]/[6]/[3], WAIT [1]), TX stuffing, the TX CRC with CRC_XOR, our frame start and the join, the own-edge rules; pin A from the engine. Tests `test_pin_bs_tx.py` (5), including three CAN frames decoded and ACKed by the reference `CANNode` on a wired-AND bus. Pin 52/52 on both builds and under Verilator; B2 mutants 30/30 killed; chip tests 10/10. Engine 34.8K, full unit logic 73.8K. D-054 (readings P-G31 to P-G35).
- **Timing:** chip STA showed slow −9.80 ns through the engine (pin → bit-clock sums). Retimed with no behaviour change: +7.65 typ / +0.87 slow at spec counts (BUGS #51).
- **Host** at unit counts other than 6: width fixes (BUGS #50).
- **R4 run 6 prepared** on `spike/r4-floorplan` (worktree `~/tw-r4`, not committed): the real `trw_chip` at the protocol floor, 398.7K µm², ~56.4 % expected, density 59. Lint clean, `test/` 4/4, chip tests 10/10 at the floor's counts. `R4_FLOORPLAN.md` §11, D-043.
- R4 run 5's precheck **passed** (1 h 56 min, the KLayout DRC of the full GDS): run 5 is green end to end, 4 h 54 min in all.

Checklist boxes ticked (evidence):
- None.

Next:
- Push R4 run 6 (branch) when the user decides; read GRT overflow and DRC.
- B3: readback and arbitration, errors, flags, JAM, listen-only, NRZI, SE0, OE auto (P26–P29).

## 2026-09-28: Krithik + Claude (phase 2: milestone B2b; R4 run 5 routes clean)
Done:
- **R4 run 5 routes clean** (36363295528): 0 DRC, LVS match, 0 antenna, typ timing met, slow −6.0 ns (slot latch → flop), `gl_test` pass, `gds` job 2 h 58 min (detailed routing 1 h 58 min). The routable ceiling is between 47.6 % and 58.9 %. `R4_FLOORPLAN.md` §10, AREA row, D-043 result and the next proposal (a run at the protocol floor's size).
- **Milestone B2b** in `trw_pin_bs.v`: RX stuffing and stuff errors, the RX CRC, `FRAME n` and its verdict, `SETN` rx; the engine takes RX commands. Tests `test_pin_bs_frame.py` (6) against the CAN and HDLC reference models. Pin 47/47 both builds; mutants 17/17 lean, 36/36 full (one first-round gap fixed: a stuff error after bit n was detected but not reported). Engine 25.1K, full unit logic 62.3K. D-053.

Checklist boxes ticked (evidence):
- None (run 5 is the stand-in, not the real chip; precheck was still running).

Next:
- B2c: the TX queue, `LINE`/`SYNC`, the TX CRC.
- Team: the budget, with run 5 and the floor (D-049); a run at the floor's size is proposed (D-043).

## 2026-09-28: Krithik + Claude (phase 2: milestone B2a, the BITSYNC receive core)
RTL session, from `ARCHITECTURE.md` §14 P20–P22 and D-023–D-027; `tools/tripsim` not read.

Done:
- `src/trw_pin_bs.v` (new): bit clock, bus idle, frame start with hard sync, resync limited to SJW, RX words. `trw_pin_unit.v` instantiates it in full units and muxes loads (event generator first) and, until B2c, holds pin A recessive and takes nothing in BITSYNC. Added to every source list (pin/chip Makefiles, synthesis scripts, CI lint).
- `test_internal/pin/test_pin_bs.py` (3 tests, both builds): phases, idle drop, ±2 % drift with and without SJW, a 1-clock-late edge. Pin 41/41 both builds; 7 B2 mutants killed; chip lint and tests unchanged.
- Area: a first version was 20.2K; one timer and one signed correction brought it to 16.1K. Full unit logic 54.0K. BITSYNC is heading for ~30K vs ~16.7K estimated (D-052); this raises the D-049 floor by ~2 % of the core.

Checklist boxes ticked (evidence):
- None.

Next:
- B2b: stuffing, the RX CRC, `FRAME` and the verdict (P23, P24).

## 2026-09-28: Krithik + Claude (phase 2: pin-unit milestone B1, PULSE and carrier)
RTL session, from `ARCHITECTURE.md` §7 and §14 P17, P30; `tools/tripsim` not read.

Done:
- Milestone B planned in three stages (`PIN_UNIT_RTL.md` §9): B1 PULSE + carrier, B2 BITSYNC core (P20–P25), B3 BITSYNC readback/JAM/flags/NRZI/SE0 (P26–P29). Krithik agreed that verification-infrastructure items (pyuvm, L9) can wait while the RTL phase needs RTL.
- **B1 done:** `trw_pin_tx.v` (`FULL`): PULSE bursts in whole ticks with back-to-back joining; the carrier with a fractional half-period timer. `trw_pin_unit.v` passes the fields. Lint clean both builds; chip lint and chip tests unchanged.
- `test_internal/pin/test_pin_full.py` (4 tests, both builds); pin suite 38/38 lean and full; `mutate.sh` handles `FULL` and the B1 mutants: 17/17 lean, 21/21 full.
- Area: full unit logic 37.9K µm² (+7.7K).
- D-051: three readings (P-G24–P-G26) for the model side.

Checklist boxes ticked (evidence):
- None.

Next:
- B2: the BITSYNC core (P20–P25).

## 2026-09-28: Krithik + Claude (phase 2: protocol floor, L1-ROT, L0-ASRT, L-XSIM, L8-EQY)
Done:
- **D-049 (proposed), the protocol floor**, from Krithik's constraint that every protocol must stay supported (not at the same time). From the 20 compiled programs: ≥ 2 lanes, ≥ 4 units with U0 full (U1 may be lean), 12 slots, the 512-word SRAM. That is ≈ 395K µm² ≈ 56 % at placement, inside the window R4 has not measured (run 4 47.6 % routed globally, run 3 58.9 % did not).
- **L1-ROT** (`test_internal/chip/test_rot.py`): all three lanes store/load through the SRAM while the host reads; every clock only the slot's owner drives the SRAM; every store lands. `test_internal/chip/mutate.sh`: 2/2 mutants killed. Added to the CI `rtl` job. L1-OVR already existed (`test_pin_rx.py::test_overrun_keeps_the_old_token`).
- **L0-ASRT**: `src/trw_assert.vh` (`TRW_ASSERT`, `TRW_ASSERT_ON`); invariants in `trw_pin_unit` (open drain never drives high; RX never loads a full producer), `trw_pins` (a driven pad has an owner), `trw_lane` (never takes an unavailable input; never loads a full output), `trw_chan_port` (a disabled port shows no token), `trw_chan_prod` (no load while full). `SIM_ASSERT` is on in every `test_internal` Makefile; all suites pass with it; two planted bugs trip their assertions. Under `FORMAL`: `formal/l0_asrt.sby` proves the pads and producer invariants unbounded (k-induction); a planted bug fails the proof. Plain and `SIM_ASSERT` builds lint clean.
- **L-XSIM**: every suite passes under Verilator 5.053 (venv cocotb 2.0.1) as under Icarus: 101 L1 + 10 chip/L3/ROT. The pin Makefile passes parameters per simulator; the chip Makefile uses `--timing -Wno-fatal` for the macro model under Verilator. New CI job `rtl-verilator` (OSS CAD Suite pinned and cached like the `efpga` branch).
- **L8-EQY feasibility (D-050)**: the PDK's Verilog cell models are not readable by Yosys; liberty-derived models + a SAT miter prove the ALU's netlist equivalent (and reject a wrong RTL). `formal/equiv.sh`.

Checklist boxes ticked (evidence):
- None (L1 still needs BITSYNC cases, which wait for milestone B / the budget).

Problems / decisions:
- **Not added: a `formal` workflow.** The `efpga` branch (a separate eFPGA design) already has `.github/workflows/formal.yaml` and `formal/*.sby`; a second one on `main` would collide if it is ever merged. Krithik and the teammate decide the naming.

Next:
- R4 run 5; the budget with D-049 as its floor; the pyuvm skeleton; the L9 Hardcaml spike.

## 2026-09-27: Krithik + Claude (phase 2: CI for the RTL suites, first claim, BUGS #49)
Done:
- R4 run 5 launched on the branch (`gds` 36363295528, `DRT_OPT_ITERS` 64, e20d390).
- Gate-level run of the chip after the BUGS #48 fix: `test_chip` 5 + `test_l3` 4, **9/9 pass** (TT Icarus 13).
- `docs/CLAIMS.md`: claim 1 (the three L3 programs on the chip RTL, simulated only) and a "Known limits" section (host link throughput: continuous UART RX above ~460 kbaud overruns at SCK = clk/8).
- `unit` workflow: new job `rtl` (VERIFICATION.md §10 puts L1 there): whole-chip Verilator lint, every L1 suite, the pin unit lean and full, the macro model fetch, and `test_chip` + `test_l3` on the chip RTL; results uploaded. First run will show whether Ubuntu 24.04's Verilator 5.020 agrees with the local 5.053.
- BUGS #49: STEP now also makes the pin units live (D-041 B). L1-HOST 7/7, mutant killed.
- `docs/HANDOFF.md` (local, not committed) for the next agent.
- **L3 extended** to every rate the shipped programs support (`test_internal/chip/test_l3.py`): UART TX 9600/115200/1M, UART RX 115200/460800 with a framing error, SPI mode 0 at 1/5/8.3 MHz, I2C 100k/400k/1M with no, short and longer-than-a-period stretching. **4/4 tests (12 configurations) pass on RTL**, reference models + sigrok. `chiplib.start(clock=...)` so a test can reset between configurations without stacking clocks.
- **D-048 (proposed):** judge the phase 2 L3 box on what the shipped programs implement; parity, SPI modes 1–3 / 16-bit and I2C arbitration loss move to phase 3 with the program work they need.

Checklist boxes ticked (evidence):
- None.

Next:
- R4 run 5 result; the area budget; D-048 (L3 scope) with Kanishk.

## 2026-09-27: Krithik + Claude (phase 2: L3 on the chip RTL, R4 run 4 result)
Done:
- **R4 run 4** (36349736069, 2 lanes, density 51) read from `GDS_logs` (`build/ci/r4/run4/`): GPL 47.6 %, **0 global-routing overflow** (Metal3 74.2 %); detailed routing 874 violations after the 4 iterations `DRT_OPT_ITERS` 3 allows (still falling), 1,428 after the antenna re-routes; typ met, slow −5.98 ns; job 2 h 55 min. `R4_FLOORPLAN.md` §9, AREA.md row, D-043 result and run 5 proposal.
- **L3 on the chip RTL** (`test_internal/chip/test_l3.py`, pins only, programs compiled by tripc and loaded with `tools/host`): UART TX at 1 Mbaud and 115200 (reference line model + sigrok `uart`), UART RX at 460800 with a framing error, SPI controller mode 0 at 5 MHz against the reference target (+ sigrok `spi`, both directions), I2C controller at ~400 kHz with 40-clock stretching: writes, a NACKed address, repeated START, reads (+ sigrok `i2c`). **4/4 pass.** Shared helpers in `test_internal/chip/chiplib.py` (host polling that drains HOST_OUT, a pad environment stepping the reference models, a VCD writer, sigrok).
- **BUGS #48** found by L3 and fixed in `trw_host.v`: a status+data burst could take a token the status had not shown. New L1-HOST test and mutant; L1-HOST 6/6.

Checklist boxes ticked (evidence):
- None. L3 passes on the RTL for the cases above, but VERIFICATION.md §6 asks for more (UART 9600 and 8E1/parity, SPI modes 1–3 and 16-bit, I2C 100k/1M and arbitration loss), and the tests belong in `test/` once the top is switched.

Problems / decisions:
- UART RX faster than ~460 kbaud overruns: the host at SCK = clk/8 needs ~560 clocks per HOST_OUT read. A protocol limit of the host link, not of the chip; worth a CLAIMS note.
- Run 5 (proposed): `DRT_OPT_ITERS` back to 64.

Next:
- Team: run 5; then the area budget (the RTL chip at 2 lanes / 6 units is ~62 % at placement; run 4 routed globally at 47.6 %).
- L3: the remaining §6 cases.

## 2026-09-27: Krithik + Claude (phase 2: the whole chip, trw_chip)
RTL session; `tools/tripsim` not read. R4 run 4 still running.

Done:
- **`src/trw_chip.v`**: every block wired (D-047), lane/unit counts generated from the spec (`TRW_LANES` etc.). `src/trw_sram.v` from R3. `trw_pin_cfg.v`: `FULL` test made width-clean for Verilator. Whole chip Verilator `-Wall` clean.
- **Chip tests** (`test_internal/chip/`, pins only, `tools/host` frames at SCK = clk/8): identity/time/SRAM/E2, lane forwarding, UART TX on U0 (full) and U3 (lean), a routine with LD/ST, and `uart.trw` loaded with `tools/host.load_sequence` and looped back. **5/5 RTL, 5/5 gate level** (Yosys netlist, TT Icarus 13).
- `synth/chip/run_chip.sh`: **517.4K µm² + macro (~62 % of the core, ~72 % at placement)**; +10.36 typ / +4.94 slow pre-layout, worst slow path from the SRAM output into EVAL.
- All L1 suites and `pytest` re-run: pass.

Checklist boxes ticked (evidence):
- None. "All modules exist and lint clean" waits for `tt_um_tripwire.v` to become the wrapper (the switch, D-047).

Problems / decisions:
- The chip at spec counts does not fit (~72 % at placement vs. a routable ceiling below ~59 %). `info.yaml` stays on the placeholder until the budget is set.

Next:
- Run 4 result → the area budget (lanes, full units, slots) → the switch: wrapper, `info.yaml`/`test/`, `config.json` (SRAM block, latch SDC, density) with their entries → the first real hardening on `main`.

## 2026-09-27: Krithik + Claude (phase 2: tools/host)
Done:
- **`tools/host`** (phase 2 task 2.3 item 7): §9 frames (`frame_write`, `frame_read`), the D-046 map from `tripwire_spec.py`, `load_sequence(image)` (every §14 H1 write: halt, all 6 unit blocks, all owners, all 13 ports, each used lane's 12 slots + K + r0–r3/STATE, SRAM, RUN), a `Host(xfer)` client (run/halt/step, lane debug block, unit flags, HOST_IN push with the busy check, HOST_OUT pop) and a `RegisterModel` to check sequences offline.
- `tripc` now emits `pin_regs` for every unit (defaults for unused ones), so a load writes every block (task 2.3 item 8 with the ports and owners in `load_sequence`).
- Tests (`tools/host/tests`): frames, encodings, the load sequence of all 20 programs checked register by register, the client against a fake chip. `pytest -m "not slow"`: 292 passed.

Checklist boxes ticked (evidence):
- None.

Next:
- Run 4 result, then the real top: the pin-level tests in `test/` will drive it through `tools/host` frames.

## 2026-09-27: Krithik + Claude (phase 2: host map in the spec, host RTL)
RTL session; `tools/tripsim` not read. R4 run 4 still running.

Done:
- Krithik approved D-042, D-044, D-046. `spec/tripwire.yaml` v1.2 gets `host_map`; `gen.py` generates the Verilog constants (`TRW_HA_*`, `TRW_HL_*`, `TRW_IRQ_*`, ID, version), the Python tables (`HOST_MAP`, …) and the §9 table, with validation (no overlapping blocks, consistent with `pin_config` and the fabric). 1 new generator test; `pytest -m "not slow"`: 269 passed.
- `src/trw_spi.v` (SPI engine from the R4 stub) and `src/trw_host.v` (the map: control, IRQ, write strobes, read multiplexer, SRAM host slot). Verilator `-Wall` clean. 24.8K µm².
- BUGS #47: a prefetch of the next read word took the HOST_OUT token; now taken only when the word is shifted out.
- L1-HOST (`test_internal/host/`): 5 tests through the pads (2-FF, SCK = clk/8), 12/12 mutants killed. All L1 suites re-run after the defs change: chan 7, alu 4, lane 6, slots 2, pins 1, host 5, pin 34 + 34, all pass.

Checklist boxes ticked (evidence):
- None yet: every module of the §2.1 table now exists except the real top; the box needs them wired and linted as one design.

Problems / decisions:
- The R4 branch's host stub still has BUGS #47 (it does not affect run 4, which measures routing).

Next:
- Run 4 result; then the real top (`tt_um_tripwire.v`) with the lane count it gives, `info.yaml`/`test/Makefile`, the SRAM macro and latch SDC in `config.json` (DECISIONS entries), and `tools/host`.

## 2026-09-27: Krithik + Claude (phase 2: slots, pads, host map proposal)
RTL session; `tools/tripsim` not read. R4 run 4 still running.

Done:
- `src/trw_slots.v` from the spike: write-only (the debug read port is gone, D-039), slot word 3 stores its 5 bits. 24.5K µm² (700 latch bits, 52 clock gates), as before. L1 (`test_internal/slots/`): 2 tests on the latch array and the flop build (`FLOPS=1`), both pass.
- `src/trw_sync.v` (2-FF, P1) and `src/trw_pins.v` (owner registers and the pad multiplexer, §7.1; host pads ignore owner writes). L1 (`test_internal/pins/`): 1,500 random clocks against the ownership rule, pass. Verilator `-Wall` clean on all three.
- D-046 (proposed): the full host register map (control/status, lane debug block, HOST_IN/HOST_OUT status, IRQ), so `trw_host.v` can be written.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- The host RTL waits for D-046, D-044 and D-042 (all proposed).

Next:
- Krithik/Kanishk: D-042, D-044, D-046. Then `trw_host.v` and `tools/host`.
- Run 4 result; then the top that wires everything (lane count from run 4).

## 2026-09-27: Krithik + Claude (phase 2: lane and ALU RTL)
RTL session, from `ISA.md` §2–§5 and `ARCHITECTURE.md` §5, §6, §14; `tools/tripsim` not read. R4 run 4 still running.

Done:
- `src/trw_alu.v` (from the R1 spike, unchanged) and **`src/trw_lane.v`**: the R1 lane checked against D-035 and §14 L12, plus the routine controller (RPC, RIR, CALL entry read, BR, DJNZ, LD/ST, OUT, SYS), STEP (H2), host writes to r0–r3/STATE (E2), `out_load` for the fabric (F4). Verilator `-Wall` and Icarus clean.
- Two latent spike bugs fixed on the way: BUGS #45 (BSEL 3), #46 (GETT time).
- L1-ALU (`test_internal/alu/`): 4 tests, 8/8 mutants killed. L1 lane (`test_internal/lane/`): 6 tests covering L1-EVAL (400 random cases against ISA §4.2–4.3) and L1-PIPE, the routine controller, urgent vs routine, halt/STEP/host writes; 15/15 mutants killed.
- Yosys: 51.5K µm² per lane with the ALU (+9.6K vs the spike). AREA.md.

Checklist boxes ticked (evidence):
- None (L1 still lacks OVR, ROT and HOST; the lane is not in the top yet).

Problems / decisions:
- D-045: three readings for the model side (fetched word competes in clock k+1; no fetch while a step is in EXEC or waiting; STEP/host writes ignored while running).
- The fetched-word path (macro clock-to-output into EVAL) is not timed yet.

Next:
- Run 4 result.
- `trw_slots.v` to `src/`, then a top that wires lanes, fabric, pin units and SRAM (and the host), so pre-layout STA and a real `gds` run can start.

## 2026-09-27: Krithik + Claude (phase 2: channel fabric RTL)
RTL session, from `ARCHITECTURE.md` §4 and §14 F1–F7; `tools/tripsim` not read. R4 run 4 (2 lanes) running on the branch meanwhile (`gds` 36349736069).

Done:
- `src/trw_chan_port.v` (consumer port: legal-source mux, en/tap/sel/accept registers, last_seq, DROPPED; F1, F2, F4, F5, F7) and `src/trw_chan_prod.v` (producer register; F3, F6).
- `src/trw_fabric.v` **generated** by `tools/gen/gen.py` from the spec's legal sources (13 ports, 13 release terms); `gen.py` also exports `FABRIC_PRODUCERS` / `FABRIC_CONSUMERS` in `tools/tripwire_spec.py`. 2 new generator tests (38 in `tools/gen/tests`).
- L1-CHAN in `test_internal/chan/`: fabric plus a producer register on all 13 producers, checked against a model of F1–F7 every clock. 7 tests: 0–4 blocking × 0–2 tap subscribers (delivery exactly once and in order, DROPPED exact), registered release, DROPPED saturation and clear, accept filter, re-pointing, sel past the list, 6,000 random clocks. **7/7 pass; `mutate.sh` 10/10 killed.**
- Yosys: fabric 44.4K µm² (AREA.md).
- Not in `info.yaml` / `test/Makefile` yet: the modules join when the top wires them.

Checklist boxes ticked (evidence):
- None (L1 is not complete until ALU, EVAL, PIPE, OVR, ROT and HOST exist).

Problems / decisions:
- D-044 (proposed): port registers at `0x2000 + c`, DROPPED at `0x2040 + c` (write clears), and three readings of F5 / sel / write-vs-take for the model side.
- `pytest -m "not slow"`: 268 passed; `lint`: Verilator `-Wall` and Icarus clean on the three files.

Next:
- Krithik/Kanishk: D-044 (and still D-041 A/B, D-042).
- Run 4 result when it finishes.
- RTL: the host (`trw_host.v`, §9) or moving the R1 lane into `src/` (with an `out_load` output for F4 tap drops on lane producers).

## 2026-09-27: Krithik + Claude (phase 2: R4 run 3 result)
Done:
- R4 run 3 (36327551624, 462bf06, `CTS_APPLY_NDR` = `none`) ran the full flow in 5 h 25 min; `GDS_logs` read locally (`build/ci/r4/run3/`, not committed).
- **Global routing ended (4 min): overflow 4,883, 4,651 on Metal3 (92.8 % usage). Detailed routing: 6,004 violations after the first pass, 12,872 at the end. The full chip does not route at 58.9 % / 65.9 %.** ~74 % of the violations are in the lanes' area (approximate, by net names).
- `R4_FLOORPLAN.md` §7, AREA.md row, D-043 result and run 4 proposal.
- Run 4 approved and set up: `localparam NL = 2` in the R4 top, `gen_fabric.py` reads it; density 51. Yosys 337.4K µm² (−80.3K); `check_local.sh` PASS (lint, 5/5 RTL, 5/5 gate level). `R4_FLOORPLAN.md` §8.
- Checked: all 20 programs use at most 2 lanes (CAN, LIN, IR NEC use 2), so every protocol still runs with 2 lanes, only fewer at once.
- Fixed: the run 3 docs cited D-041 for the area budget; it is `AREA_ESTIMATE.md` / D-038–D-040.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- GitHub's live log stops at ~38.6K lines (in CTS), so a running R4 job cannot be followed; wait for the end.
- LibreLane failed parsing netgen's JSON after the LVS mismatch, so precheck did not run (tool issue, only when LVS already fails).
- Proposed run 4: 2 lanes instead of 3 (D-043). The routable ceiling bears on the area budget (`AREA_ESTIMATE.md`, D-038–D-040).

Next:
- Krithik: commit, then push `spike/r4-floorplan` for run 4; collect `GDS_logs` into `build/ci/r4/run4/`.
- Team: revisit the area budget (`AREA_ESTIMATE.md`) with run 3 and run 4.

## 2026-09-27: Krithik + Claude (phase 2: R4 run 2 result)
Done:
- R4 run 2 (36279959944, ed3b949) read from the job log with `gh api` (cancelled at the 6 h limit, so no `GDS_logs`).
- **Placed at 58.9 %; CTS, hold repair (3,067 buffers) and detailed placement passed; global routing never ended.** It had overflow after 50 iterations and then relaxed the clock NDR one net at a time (GRT-0273) for 5 h 51 min. No overflow figures were printed.
- `R4_FLOORPLAN.md` §6, AREA.md hardening row, D-043 run 2 result and run 3 proposal.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- Any run with global-routing overflow will time out the same way while clock NDRs are on (LibreLane `CTS_APPLY_NDR` = `half` by default).
- Proposed run 3: `CTS_APPLY_NDR` = `none`, same design, to get the overflow numbers (D-043).

Next:
- Krithik: approve or change run 3; then Claude edits the branch `config.json` and gives the commands.

## 2026-09-26: Krithik + Claude (phase 2: R4 run 2 setup)
Done:
- Run 1 ID found with `gh`: 36269756517; added to AREA.md and R4_FLOORPLAN.md.
- **R4 run 2 (approved): 4 pin units.** `localparam NU` in the R4 top; `gen_fabric.py` reads it and leaves out the absent units' TX ports; density 73 → 62.
- `check_local.sh`: PASS (lint clean, 5/5 RTL, 5/5 gate level). Yosys 417.7K µm² (−81K); expected GPL ~60 %; slack +10.28 typ / +5.08 slow.
- D-043 run 2 entry, `R4_FLOORPLAN.md` §5, AREA.md synthesis row.

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- The `gds` run 36278610622 on `main` came from the P34/P38/P43 RTL push; the pin-unit files are not in `info.yaml`, so it rebuilds the same chip.

Next:
- Krithik: push run 2 on `spike/r4-floorplan`; collect `GDS_logs` into `build/ci/r4/`.

## 2026-09-26: Krithik + Claude (phase 2: R4 run 1 result)
Done:
- Read `GDS_logs` of R4 run 1 (`spike/r4-floorplan`, 1ca1bdc; unpacked in `build/ci/r4/`, not committed).
- **Result: failed at placement, before routing** (DPL-0036 in `ResizerTimingPostCTS`).
  - Global placement utilisation 70.0 % (predicted ~71 %); 70.5 % after the fanout repair and CTS.
  - The hold repair added 3,921 buffers (+10.1 %, 2,315 endpoints), taking it to ~77 %; 43 instances could not be legalized.
  - Setup clean (typ +8.94 ns mid-PnR). Hold at typ is mostly on the SRAM inputs (−0.65 ns, 0.46 ns clock skew).
  - ~5 min of flow time.
- `R4_FLOORPLAN.md` §3–4, AREA.md hardening row, D-043 outcome and the run 2 proposal.
- Also fixed `sources.sh` (it failed when writing into `src/` itself on the branch).

Checklist boxes ticked (evidence):
- None.

Problems / decisions:
- The run ID is not in the logs; to add to AREA.md and R4_FLOORPLAN.md.

Next:
- Krithik: approve run 2. Proposed: 4 pin units (a unit-count parameter in the R4 top), density = the new GPL utilisation + 2.

## 2026-09-26: Krithik + Claude (phase 2: pin unit follows D-041)
RTL session, from `ARCHITECTURE.md` §14 P31–P45 (D-041); `tools/tripsim` not read. R4 launched first (branch `spike/r4-floorplan`, 1ca1bdc).

Done:
- **P-G7 → P34 (changed):** a CLK taken in a burst's final-release clock (with STRETCH: the clock the line reads IDLE) extends the burst instead of starting a new one.
- **P-G12 → P38 / P8 (changed):** EV_RESET restarts framing before the event clock's sample, which becomes bit 0 of the new word.
- **P-G20 → P43 (changed):** TX_EDGE code 3 acts as none (timed shift); it made the unit linked on the fall.
- **P-G9 → P36, P-G22 → P44:** the RTL already complied; both are now pinned by tests.
- 7 new L1 tests (34 in all), passing on the lean and full builds. `mutate.sh`: 4 new mutants (old P34/P38/P43/P44), 3 stale ones updated to the FRAC/P38 source, and an `ONLY=` filter; **16 of 16 caught**.
- `PIN_UNIT_RTL.md` §6: the resolution of each gap.

Checklist boxes ticked (evidence):
- None.

Next:
- R4 run 1: collect `GDS_logs`, fill `R4_FLOORPLAN.md` §3–4 and the AREA.md row.
- Proposals A/B (D-041) and D-042 wait for Krithik and Kanishk; the RTL already does A, B and write-1-to-clear.

## 2026-09-26: Krithik + Claude (phase 2: R4 full-size floorplan spike, prepared)
RTL session; did not read `tools/tripsim` or `spikes/area/ae_prims.v`.

Done:
- **D-043:** R4 on branch `spike/r4-floorplan` (never merged), sources in `spikes/r4_floorplan/`. Contents: 3 R1 lanes without slot read-back, with routine sequencer stubs; 6 lean pin units with config latches; the fabric (13 producers, 13 ports, legal-source muxes generated from the spec by `gen_fabric.py`); the SRAM macro with the rotation; a host SPI stub that writes and reads back every block.
- Branch `config.json`: R3's macro block, density 73 (lowest legal, from the R2 synthesis-to-placement ratio), R2's latch SDC, `DRT_OPT_ITERS` 3. Every exception is listed in D-043.
- Size (Yosys, flat): **498.8K µm² + the 45.3K macro, ~71 % of the core at placement**; 2,592 flops, 2,814 latches, 210 clock gates; the per-module numbers match the earlier blocks. Pre-layout slack at 20 ns: +10.63 typ / +5.50 slow.
- `spikes/r4_floorplan/check_local.sh`: lint; 5 pin-level tests through the host stub, on RTL and on the Yosys gate-level netlist; Yosys area; pre-layout STA.
- `trw_lane` (spikes/r1_lane) gains a register debug output, connected in the R1 harness, its tb and the R2 overlay; `run_r1.sh` re-run: PASS, lint clean.
- BUGS #44 (host stub address assembly, caught by the local suite before any push). BUGS: moved the "Note on #1" below rows 41–43, which had landed outside the table.
- `docs/reports/R4_FLOORPLAN.md` (setup; results pending); AREA.md synthesis row.

Results:
- Local: lint clean; RTL 5/5; gate level 5/5 (evidence run of `check_local.sh` at the end of the session, below); `scripts/check_all.sh` on `main`.

Checklist boxes ticked (evidence):
- None (R4 answers a planning question; phase 2 task 2.0 stays open until the budget is decided).

Next:
- Krithik: run the branch commands (`spikes/r4_floorplan/README.md`). The push starts a `gds` run on the branch.
- Then: collect `GDS_logs`, fill `R4_FLOORPLAN.md` §3–4 and the AREA.md hardening row, and choose one change for run 2.
- RTL follow-ups from D-041: P-G7 (CLK in the final-release clock extends the burst), P-G9 (an edge in the clock after a preload is also ignored), and checks of P-G12, P-G20 (unnamed enum codes act as code 0) and P-G22.

## 2026-09-26: Krithik + Claude (phase 2: pin-unit RTL gaps answered, 4-bit fraction check)
Done:
- **The 23 pin-unit RTL gaps (P-G1 to P-G23) are answered in §14** as new rules P31 to P45 (plus edits to P8 and P13), recorded in **D-041**. Where the RTL's reading was better, the model now follows it.
- The model changed in 14 places, each pinned by a test (18 new tests in `test_semantics.py`), and each change was reverted once on purpose to confirm a test fails.
- The review found three real model bugs:
  - BUGS #41: SHIFT_RX stalled when a sample fell in an event clock;
  - BUGS #42: a preloaded bit hidden by a same-edge shift;
  - BUGS #43: CLKGEN drift with an odd PERIOD.
- Evidence: the full suite passed (271); the fast suite passes after the last test change (266); injected reverts of the 18 model changes are all caught (18 of 18); `gen --check` is clean.
- **The RTL must change in two places** (P-G7: a CLK in the final-release clock extends the burst; P-G9: an edge in the clock after a preload is also ignored), and should check three others (P-G12, P-G20, P-G22). Listed in D-041.
- **Proposed, awaiting approval:**
  - D-041 A: a config write restarts the unit;
  - D-041 B: pin units are live only after the first RUN/STEP;
  - D-042: write-1-to-clear status word per unit.
- **4-bit timer fraction, model side:** a new exploration knob, `TRIPSIM_FRAC=4`, rounds every time setting to 1/16 clock. With it, the full suite passes except the one test that checks the encoding is exact at 1/256 (253 of 254). So all 20 protocols work with 4-bit fractions. The RTL session is measuring the area side.

Checklist boxes ticked (evidence):
- None.

Next:
- Krithik/Kanishk: approve or change D-041 A/B and D-042.
- RTL session: the fraction measurement, then R4. Pass it the D-041 changes for the pin unit.
- 4-bit fraction: the RTL measured -1.9K µm² per lean unit (about 1.5 % of the core for six units). Not adopted; kept as a late option, since the model shows every protocol still works.

## 2026-09-26: Krithik + Claude (phase 2: 4-bit timer fraction, measurement)
Done:
- `FRAC` parameter (default 8) on `trw_pin_unit/tx/rx`: the cursor fraction, the burst timer, the SHIFT_RX timer, and the PERIOD/SAMPLEOFS inputs (top FRAC bits). No spec change.
- Threaded through the L1 harness (`make FRAC=4`) and `synth/pin/run_pin.sh` (`FRAC=4`, outputs in `build/frac4/`).
- `PIN_UNIT_RTL.md` §7: lean unit 29,790 → 27,903 µm² (−1.9K, −6 %), 216 → 204 flops, slow-corner slack +6.42 → +6.94 ns. Worth ~1.5 % of the core for six units, so not a big lever; recommendation: don't adopt it on its own.
- Tests: FRAC = 8, 27/27 (same function); FRAC = 4, 24/27 (the three 5.4-clock-period tests fail, as expected on a 1/16 grid). `scripts/check_all.sh` PASS.

Checklist boxes ticked (evidence):
- None.

Next:
- Task 2: the R4 full-size routability spike at 6x4 (branch `spike/r4-floorplan`).

## 2026-09-25: Krithik + Claude (phase 2: pin unit RTL, milestone A)
RTL session: worked from the documents and `spec/tripwire.yaml` only; did not read `tools/tripsim` or `spikes/area/ae_prims.v`.

Done:
- `tools/gen/gen.py`: Verilog output for `pin_config` (field positions, `TRW_PCE_*` enum codes, stored-bit masks per feature, units per feature) and a check that no two defines collide; 3 new generator tests. `src/trw_defs.vh` regenerated.
- RTL, not yet in `info.yaml`/`test/Makefile`: `trw_pin_cfg.v` (latch array, a clock gate per stored word, write-only, `FULL`), `trw_pin_io.v`, `trw_pin_tx.v`, `trw_pin_rx.v`, `trw_pin_unit.v`. Lean feature set for both builds; PULSE, carrier and BITSYNC are milestone B.
- The cursor needs no multiplier: it is kept relative to now in ticks (`PIN_UNIT_RTL.md` §1).
- `test_internal/pin/`: cocotb harness plus 27 L1 tests (L1-PIN-TX 13, L1-PIN-RX 12, L1-OVR 2), expected values from the §14 rules; `mutate.sh` (12 injected bugs, all caught).
- `synth/pin/`: `run_pin.sh` (lint, Yosys area, OpenSTA typ/slow), `ablate.sh` (price per feature), measurement wrapper with a stand-in producer.
- `docs/reports/PIN_UNIT_RTL.md`: numbers, the budget, gaps P-G1–P-G23. AREA.md synthesis row; BUGS #40 (generator define collision, caught by the new test before any RTL used it).

Results:
- Lean unit 29.4K µm² (216 flops), config 5.1K lean / 11.4K full, producer 1.5K. With the estimated port: **38.7K vs the estimate's 41.2K (−6 %)**. The chip at scenario E is ~85 % of the core, so the cuts are still needed.
- The wide timers dominate: the burst timer alone is 8.5K, the SHIFT_RX timer 3.9K.
- Slack at 20 ns +10.8 typ / +5.8 slow with config static. Critical path: burst timer → cursor subtract → `eq`.
- Tests: `make FULL=0` and `FULL=1` both 27/27; `scripts/check_all.sh` PASS; 34 generator tests pass; `gen --check` clean; lint clean.

Checklist boxes ticked (evidence):
- None. "All modules exist and lint clean" needs the whole table; "L1 all green" needs the other blocks and BITSYNC.

Problems / decisions:
- P-G15 (restart on a config write) and P-G16 (`live`) change §14 H1; P-G19 adds a clear mechanism to §9. They need a DECISIONS entry (not written: the user decides; D-041 is still free).

Next:
- Team: choose the next area cuts with `PIN_UNIT_RTL.md` §5 (fraction width, 4 units, 2 lanes).
- Model session: answer P-G1–P-G23 in §14.
- RTL: milestone B (PULSE, carrier, BITSYNC) after the cut decision, since a timer-width change touches BITSYNC too.

## 2026-09-25: Krithik, Kanishk + Claude (phase 2: tier 1 area decisions)
Done:
- **D-038:** pin configuration in a latch array (`trw_pin_cfg.v`); §14 H1: the host writes every unit's block before RUN; CLAUDE.md latch rule updated.
- **D-039:** slots, K and pin configuration are write-only from the host.
- **D-040:** U0–U1 full, U2–U5 lean (no PULSE, carrier, BITSYNC):
  - `pin_config.features` / `units` in the spec, validated by the generator; the §7.2 table shows each field's units;
  - the model and tripc reject a missing feature;
  - lean units don't store the optional fields;
  - `tripc.load` writes all six blocks.
- Area with tier 1: ~781K µm² placed, 87 % of the core (AREA_ESTIMATE scenario E).
- Tests: full suite 251 passed (slow included); `scripts/check_all.sh` PASS; `gen --check` clean. Spec bumped to v1.1 (still frozen).

Checklist boxes ticked (evidence):
- None. The task 2.0 box stays open until the design fits a routable budget.

Next:
- RTL session: `trw_pin_unit` (full and lean) first, synthesized, to replace the estimate's glue guess.
- Then choose the next cuts (a leaner core, 4 units, or 2 lanes) with real numbers.
- Ask Jane Street / Tiny Tapeout about 8x4.

## 2026-09-25: Krithik + Claude (phase 2 start: plan update, area estimate)
Done:
- `docs/HOW_IT_WORKS.md`: plain-language introduction (kitchen analogy); linked from OVERVIEW and CLAUDE.md.
- `PHASE2_RTL_CORE.md` updated with phase 1's findings:
  - helpers out (D-029);
  - pin-unit scope per §7 and the P-rules;
  - R2/R3 physical inputs (latch SDC exception, density ~42 % for the slot arrays, SRAM macro);
  - new task 2.0: area estimate first.
- **Area estimate (task 2.0), `docs/reports/AREA_ESTIMATE.md`:**
  - building blocks synthesized alone (`spikes/area/`), multiplied by counts from the spec;
  - **the frozen spec does not fit: ~109-120 % of the 6x4 core placed.** Pin units are ~84K µm² each, about half of the chip;
  - options priced (latch config, heterogeneous units, a leaner core, 4 units, 2 lanes, no read-back); only nearly all of them together reach a routable ~56-61 %.
- The project `.venv` was missing; recreated with `scripts/setup_venv.sh`.

Checklist boxes ticked (evidence):
- Phase 2 entry criteria (phase 1 complete, CI green on `367aacc`).

Next:
- Team decision on the area options (AREA_ESTIMATE §8): latch config, no slot/config read-back, heterogeneous units now; the rest after measuring.
- RTL session: write `trw_pin_unit` first and synthesize it, to replace the glue guess.
- Ask Jane Street / Tiny Tapeout whether 8x4 will be offered.

## 2026-09-25: Krithik + Claude (phase 1 closed)
Done:
- Pushed the D-035/D-036/D-037 commits (`ffb7d7d`..`367aacc`). The two tripc files missed in the tools commit went in separately as `367aacc`.
- Collected CI on `367aacc`: every workflow passed.

Checklist boxes ticked (evidence):
- "All CI workflows still green on `main`": `test` 36079759567, `unit` 36079759530, `lint` 36079759569, `docs` 36079759587, `gds` 36079759590 (all four jobs), `nightly` 36079785059 (manual) and 36136704498 (scheduled).
- That was the last box: **Phase 1 is complete.** Summary: `docs/summaries/PHASE1.md`.

Next:
- Phase 2, first task: area estimate for pin units, fabric and host, pricing heterogeneous pin units first (D-036).
- Kanishk: read D-036 and the §7.2 table.

## 2026-09-24: Krithik + Claude (phase 1: pin-unit registers, spec freeze)
Done:
- **D-036: pin-unit configuration register layout** in `spec/tripwire.yaml` (`pin_config`):
  - 22 words per unit at `0x3000 + u·0x20`, owners at `0x30C0`;
  - all times are 16.8 clocks, and the sample point is an offset in 1/256 clocks;
  - the generator validates it and emits the ARCHITECTURE §7.2 table;
  - the model runs every configuration through `tripsim/pinregs.py`, and tripc emits `pin_regs` and rejects values that do not fit;
  - `test_pinregs.py`, plus 5 generator validation cases.
- **Area input:** 307 config bits per unit (~1,840 for six units), comparable to all the slot latches. Noted in D-036 for the phase 2 area estimate.
- **D-037: spec frozen, v1.0.**
- Tests: 220 fast tests pass (`-m "not slow"`); `gen --check` clean; full suite result below.

Checklist boxes ticked (evidence):
- None new. "All CI green on `main`" waits for these commits' CI runs.

Next:
- User: commit and push. Then send the run IDs of `test`, `unit`, `lint`, `docs` on the new HEAD, plus one manual `nightly`. `gds` does not run: `src/` is unchanged since run 35942676979.
- Claude: tick the CI box with the run IDs and close Phase 1.
- Kanishk: read D-036 and the §7.2 table.

## 2026-09-24: Kanishk, Krithik + Claude (phase 1: §14 second-person review, D-035)
Done:
- **Kanishk reviewed §14** (with Claude reading `tools/`). He found gaps G9–G24 and model bugs #35–#37, and proposed D-035 items A–P.
- **Krithik accepted D-035.** The two choices went to Claude: E2 = host-writable r0–r3 and STATE while halted; F = one RX load per clock, the loser sets OVERRUN.
- **Applied (model side):**
  - ARCHITECTURE §4.5, §5.1, §6.2, §9 (K at slot index 12; lane register block), §11, §12, §14 (new L12, H2, and text for B, C, E, F–M); ISA §4.4, §5.3; YAML JAM/FRAME text.
  - Model: BUGS #35–#37 fixed; `Chip.step_lane` (H2), and a halted lane makes no SRAM accesses; `Lane.write_reg/write_state/write_k`, which `tripc.load` uses.
- **Second pass over P20–P29, line by line:** G25–G31, answered in the §14 text; BUGS #38 (BITSYNC SETN rx n > 16) and #39 (own-frame bit missing on flag/SE0 frame ends), both fixed.
- **Tests:** new `tools/tripsim/tests/test_semantics.py` (18 tests). A 12-mutation check (each fix reverted in turn) fails a test every time. Full suite: 220 passed, slow tests included; `gen --check` clean.

Checklist boxes ticked (evidence):
- [x] Zero OPEN items + §14 reviewed by two people: D-033, D-035 (accepted), `test_semantics.py`.

Problems / decisions:
- D-035. BUGS #35–#39.
- Kanishk's review found that `spec/tripwire.yaml` has no pin-unit configuration register layout (PERIOD 16.8, SAMPLEOFS, SJW, CRC fields and so on). That is an encoding the RTL, host tools and area estimate all need, so it is done before the spec freeze (next).

Next:
- Pin-unit configuration register layout in `spec/tripwire.yaml` (+ generator, host map), reviewed by both.
- Then the Phase 1 wrap-up: spec `status: frozen`, the CI box with run IDs, the final PHASE1 summary.

## 2026-09-24: Krithik + Claude (phase 1: spike lane vs. D-033)
Worked from `ARCHITECTURE.md` §14 as pulled (26bdc86: L8–L11, R5–R6, H1); did not read `tools/`.

Done:
- Checked `spikes/r1_lane/trw_lane.v` against the new rules. It agrees with L8 (BSEL, MKCTL), L9, L11, R5, R6 and H1 (RUN = 0 and all flops reset; the harness, the R2 top and the tb write all 48 slot words before RUN).
- **L8 KT: fixed on `main`** (BUGS #34). KT now keeps the head tag only when ASRC is I0/I1; otherwise OT gives the tag.
  - `tb_r1_lane.v` covers both halves: slot 0 has KT with A = I0 and OT = ERR, and must keep DATA; slot 2 has KT with A = zero, and must emit EVENT.
  - The old behaviour fails the tb ("O1 token tag 0"); the fixed lane passes.
- Not re-applied to `spike/r2-latch`: R2's result does not depend on it, and a push would restart the running hardening.
- `run_r1.sh` re-run: sims PASS, lint clean. ABC mapping noise moved the worst EVAL row to 11.68 ns (flop, unbuffered, slow), slack +7.87. That is below the +8.2 ns the docs claimed, so `R1_LANE_TIMING.md` §3, D-030, the phase checklist evidence, `AREA.md` and `PHASE1.md` now carry the corrected figures (margin 1.67×). The conclusion is unchanged.

- **L10 CALL: fixed on `main`** after Krithik's OK. CALL now ignores DST (no wait, no reservation, no output load) and DFE (no PEND, no flag write). Both fixes are one BUGS entry, #34 (references D-033 and the model's twin #32).
- **Sim checks** (`tb_r1_lane.v`, both slot stores PASS):
  - KT with A = zero gives OT (EVENT); KT with A = I0 keeps the head's DATA over OT = ERR.
  - A CALL with DST = O0 while O0 holds the last, untaken byte, and DFE on f0 = 1: it must fire; O0 stays unchanged; `resv` and `PEND` are 0 in the CALL's own EXEC clock (the old behaviour set and cleared both, invisible at the end); f0 stays 1 (a flag write would store R = 0).
  - H1: nothing fires, is taken or loaded while halted and the slots are being written.
- **Mutation checks:** removing each of the five L10 guards alone fails the tb, and so does the old KT rule. A lane that ignores RUN fails the H1 check (the X from unwritten latches shows as `take xx`).
- **H1 confirmed:** RUN resets to 0 in the harness, the R2 top and the tb; every lane flop has a synchronous reset; the tb writes all 48 slot words plus K0–K3 before RUN, and the R2 test writes all 52 words before RUN.
- `run_r1.sh` re-run: sims PASS, lint clean; worst EVAL this run 10.76 ns (slow). The report's table is this run; the headline keeps the worst across runs (11.68 ns, +7.87).
- Not re-applied to `spike/r2-latch`.

Next:
- R2 run 2 (`gds` 36017019520): cancelled after ~3 h, no artifacts.
  - The resizer fix worked: routing started within minutes.
  - Routing stalled at 8 Metal2 violations in the 27th stubborn-tile pass (live log, D-032).
- Run 3 prepared (D-034): `PL_TARGET_DENSITY_PCT` 52 (not 45: the placer's utilisation is 48.9 %) and `DRT_OPT_ITERS` 20. A non-converging run now fails with `GDS_logs` instead of timing out without them.
- D-034 also states the branch-only config-rule exceptions (DRT_OPT_ITERS, and the SDC keys from run 2) that I had not flagged.
- R2 run 3 (`gds` 36039323359):
  - routing started 4 min in (SDC fix confirmed);
  - pin access clean;
  - density 52 cut the first-pass violations from 8,297 to 33, but the tail held at 26–27 (Metal2/Metal3);
  - pass 5 was a ~1 h stubborn pass, so a cap of 20 would still time out (kill at 00:09 UTC; I first misstated it as 22:09).
- Run 4 first planned as a diagnostic-only run (cap 3). Revised at Krithik's question ("why run a workflow we know will fail?") into an attempt to pass: tile 4x2, density 42, cap 8 (D-034). No RTL or test change.
- **R2 PASSED (run 4, `gds` 36060938609, c4ef059):** gds 73 min, precheck 16.7 min, gl_test 0.8 min, viewer green.
  - Routing reached 0 violations at iteration 5; DRC, LVS and antenna 0; post-CTS resizer 9.5 s.
  - `AREA.md` row 3; latch slots kept.
  - [x] R2 box ticked (run 36060938609).
- **D-030 post-layout recheck:** OpenSTA on the routed netlist + SPEF (hold slacks match the flow's) gives EVAL +11.75 / +6.94 / +13.65 ns (typ/slow/fast), above the 2 ns threshold. Confirmed.
- Phase 2 inputs recorded (D-034, AREA row 3): the latch SDC exception; ~42 % local density for the slot arrays (Metal3 still 66 % used); the read-back mux as the first wiring cut.

## 2026-09-24: Krithik + Claude (phase 1: R1 spec gaps G1–G8, model side)
Done:
- Answered the eight spec gaps from the R1 report (§6) from what `tools/tripsim` does, and wrote them into `ARCHITECTURE.md` §14 (new L8–L11, R5–R6, H1), §5.1/§5.2, and the `spec/tripwire.yaml` field descriptions (regenerated ISA tables). D-033.
- The spike agrees with every answer except G6 `KT` with a non-input A (the spec says ignore it; the spike used the latched head tag).
- Two latent tool bugs found by the review and fixed: BUGS #32 (model reserved an output for CALL), #33 (`tripc.load` left unused slots unwritten). tripc now rejects `keep` without an input operand.
- Tests: 197 fast tests pass (`pytest -n auto -m "not slow"`), `gen --check` clean.

Checklist boxes ticked (evidence):
- None. "Zero OPEN items" still needs the second person's §14 review.

Problems / decisions:
- D-033. DECISIONS numbering: D-031/D-032 came from the R2/R3 session; this is D-033, so that session should use D-034 next.

Next:
- Kanishk: review §14, including the new rules, then the "zero OPEN items" box can be ticked.
- R2/R3 session: change the spike's `KT` handling to §14 L8 before the lane becomes phase 2 RTL.

## 2026-09-24: Krithik + Claude (phase 1: R1 risk spike)
Fresh session, RTL context only: read `ARCHITECTURE.md`, `ISA.md`, `spec/tripwire.yaml` and `PHYSICAL_DESIGN_AND_CI.md`; did not read `tools/tripsim` or `tools/kernels`.

Done:
- **`spikes/r1_lane/`** (throwaway RTL, outside `src/`, no CI reads it). It contains:
  - `trw_lane` (12 ready terms, the §4.3 rule, one priority encoder, static updates, EXEC, routine steps);
  - `trw_alu` (16 ops);
  - `trw_slots` (Ibex-style latch array, with a flop variant);
  - `trw_cport` (source mux, F7);
  - `trw_r1_top` (harness: all lane neighbours are registers);
  - `tb_r1_lane` and `run_r1.sh`, `sta.tcl`, README.
- **Tools:** OpenSTA 2.6.0, the standalone `sta` extracted from the OpenROAD 2024-12-14 Ubuntu 22.04 package plus `libtcl8.6` / `tcl-tclreadline` via `apt-get download`, into `~/.cache/tripwire/openroad`. No root needed; `run_r1.sh` does it.
- **Sanity sim** (Icarus, latch and flop slots): ISA §7.1 at 3 clocks per byte, then EVENT: PASS. Verilator `-Wall` clean.
- **Timing at 20 ns** (Yosys onto cmos5l, OpenSTA, before layout):
  - EVAL 3.7–7.3 ns typ, 5.8–11.4 ns slow;
  - worst slack +8.2 ns (flop slots, unbuffered, slow);
  - EXEC at most 10.6 ns.
  - Report: `docs/reports/R1_LANE_TIMING.md`.
- **Area:** ~67K µm² per lane with latch slots (slots 25.5K vs 51.7K as flops). Recorded in `AREA.md` (synthesis-only section).
- **DECISIONS D-030 (accepted):** fire every clock; no fallback in the phase 2 RTL. Recheck against R2's post-route slack.
- **Spec gaps G1–G8** (report §6): places where the text leaves an RTL choice open or disagrees with itself (BSEL reg/k index, routine step pipeline position, blocked routine OUT, PEND set/clear on the same edge, DJNZ and RZ, KT/CALL/f3 corner cases, slot latches without reset, PEND/slot-width/RRET inconsistencies). None affects timing.
- `docs/summaries/PHASE1.md` item 16.

Checklist boxes ticked (evidence):
- [x] R1 decided: `docs/reports/R1_LANE_TIMING.md` (run_r1.sh), D-030 accepted by Krithik ("accept D-030").

Problems / decisions:
- Before layout only: no wires, no CTS. R2's hardening gives post-route numbers for the same logic.
- The clock gate in `trw_slots` is a behavioural latch + AND. For R2 and phase 2, instantiate `sg13cmos5l_lgcp_1`.

Later (R3 set-up):
- D-031: R2/R3 hardenings on throwaway branches (per-ref `gds` concurrency keeps `main` safe); R3 first.
- `spikes/r3_sram/`:
  - branch overlay: 2x2 `info.yaml`, test top with direct word access and an 18-pass walking-ones BIST, `trw_sram` wrapper, macro blackbox, `config.json` with the macro block, Loom's `pdn_cfg.tcl` verbatim (commit c7000671), `test/Makefile` + `test.py`;
  - `fetch_macro.sh` (IHP-Open-PDK 2bbec75, byte counts checked);
  - `check_local.sh`;
  - `apply_to_branch.sh` (refuses to run off `spike/r3-sram`).
- `check_local.sh`: PASS. Lint; 3/3 tests on the RTL and on a Yosys gate-level netlist (TT Icarus 13); flattened instance `u_sram.sram`.
- Mutations: a wrong BIST write is caught (1 test fails); address aliasing is caught (2 tests fail).

- User pushed `spike/r3-sram`. **R3 PASS:** `gds` run 35961480554 (09e8697): gds 7.9 min, precheck 1.7 min, gl_test 0.8 min, viewer green; lint/test/unit/docs green. The macro is kept (D-031).
  - [x] R3 box ticked (run 35961480554).
  - Pages now shows the R3 chip until the next `main` hardening.
  - Numbers from `GDS_logs` (copied to the git-ignored `build/ci/r3/`) are now `AREA.md` row 2:
    - setup +10.95 / +9.23 / +11.23 ns, hold +0.33 / +0.67 / +0.14 ns;
    - 47 % utilisation, 0 overflow, LVS / routing DRC / antenna all 0.
  - The macro's clock-to-output is **6.59 ns slow** (4.29 typ): a phase 2 constraint on the routine decode.
- `docs` on `main` (db974df): one of two identical push-triggered runs failed inside the TT docs action (35962848241), the other passed (35962849222), so the failure is flaky, not ours. Re-run requested.

Later (R2 set-up, D-032):
- `spikes/r2_latch/`: branch overlay for the whole R1 lane on 3x2, with pin-driven I0 producer, O0/O1 subscribers and RIR. Also `test.py` (latch array: two patterns over all 52 words; a program with §7.1, a routine step pair and a K constant), `check_local.sh` and `apply_to_branch.sh`.
- Shared `trw_slots.v`:
  - library ICG `sg13cmos5l_lgcp_1` under `ifdef SYNTHESIS`;
  - a debug read port (~9.4K µm² per lane: a phase 2 question);
  - the upper 11 bits of each slot's 4th word are no longer stored (132 latches that R2's readback had kept).
- `check_local.sh`: PASS. Lint; 2/2 on RTL and gate level (700 latches, 52 `lgcp`); STA pre-layout +10.8 ns (slow, flop endpoints).
- R1 re-run: same conclusion. The ABC mapping moves rows by up to ±1.2 ns between such edits, so the report now uses the final run and carries a ±1.5 ns note. D-030, AREA and the summary are updated to match.

- **R2 run 1 timed out:** `gds` 35962617201 (06d0f3d) was cancelled at the 6 h job limit inside Build GDS, with no artifacts.
  - Job log (`build/ci/r2/`): the post-CTS resizer spent 3 h 21 min on 700 "violating" latch data pins (time borrowing → slack 0.000 < the 0.05 margin).
  - Detailed routing went 8,297 → 21 violations in ~1 h, then 1.5 h of stubborn-tile passes left 14 Metal2 spacing violations.
  - M2/M3 usage 58 % / 55 %, wire length 367 mm.
  - D-032 has the full diagnosis.
  - Run 2 fix, one change: `pnr.sdc` (default + no setup repair on latch data pins) and `signoff.sdc` (default). Checked with OpenSTA locally.

Next:
- User: push the R2 run 2 change (`spikes/r2_latch/overlay/src/{pnr.sdc, signoff.sdc, config.json}`) to `spike/r2-latch`.
- Then: from run 2's artifacts, locate the Metal2 violations and the congestion hot spots, and size the routing cost of the slot array (and of the 52-word read port) for the 6x4 plan.
- (done) User: commit, then create `spike/r2-latch` and push it (spikes/r2_latch/README.md). Record both gds runs when they finish.
- Team: answer G1–G8 in §14 / ISA (the model owner can say what tripsim does).
- R2: a 2x2 TT project around `trw_slots` + `trw_lane` (library ICG, host-write path from pins). Plan: spike branches in this repo (`spike/r2-latch`, `spike/r3-sram`) with `tiles: "2x2"`, never merged; `gds` concurrency is per ref, so they don't cancel `main`.
- R3: the SRAM macro smoke project (PHYSICAL §3 recipe).

## 2026-09-23: Krithik + Claude (phase 1: CI speed, ISA §9 answers, freeze proposals)
Done:
- **CI speed.** The `unit` workflow took about 20 min. Five tests (servo, IR NEC TX/RX, two LIN tests) took 785 of the 906 s, because they simulate 3–10 M clocks each.
  - Marked those five `@pytest.mark.slow` (the marker is registered in `pyproject.toml`).
  - `unit` now runs `pytest -n auto -m "not slow"` with pytest-xdist 3.8.0 (pinned in `requirements-dev.txt`): 183 passed in 37 s locally with 4 workers.
  - New `nightly` workflow (daily plus manual), with two jobs: `full` (everything) and `r1-fallback` (kernels at `TRIPSIM_FIRE_PERIOD=2`).
- **R1 fallback measured.** `Chip` reads `TRIPSIM_FIRE_PERIOD`. All 103 kernel tests pass at fire period 2, in 656 s, including every speed-limit test.
- **`tools/explore/metrics.py`** (`cd tools && python -m explore.metrics`) reports per-lane slots, registers, K, head tests, ALU-flag uses, readiness and ablation bounds for every program. Its table is now `ARCH_EXPLORATION.md` §1a.
- **`ARCH_EXPLORATION.md`** answers every `ISA.md` §9 row: slots, registers + K, ablation, R1, TX/RX NBITS, routine rate, and Q7 throughput.
- **DECISIONS D-029 (proposed):**
  - keep 12 slots, 4 + 4, and every D-007 feature;
  - the R1 fallback is acceptable;
  - close Q1–Q7;
  - a new connectivity table (Lk.I1 needs 9 sources);
  - no helper units in phase 2;
  - host MISO moves to `uo_out[3]` (RP2350 SPI0 RX); pin map follows.

- **D-029 accepted and applied** (Krithik: "go with your recommendations for both").
  - `spec/tripwire.yaml`: host pads `ui4 ui5 ui6 uo3 uo6` (MISO moved from `uo7`, checked against RP2350 datasheet Table 645), and a new `fabric` legal-source table (4-bit `sel`; Lk.I1 has 9 sources).
  - The generator expands the table into `LEGAL_SOURCES` (Python) and a generated table in ARCHITECTURE §4.6. There is no Verilog output yet, so `src/` is unchanged; it is added when the phase 2 RTL needs it.
  - tripc rejects a `connect` outside the table; every program passes (`test_every_program_uses_only_legal_sources`). New gen and tripc tests: 189 fast tests pass in 18 s.
  - ARCHITECTURE §4.3–4.6, §8 (helpers deferred), §9 host pins, §10 pin map, block diagram; ISA §8–9. Zero OPEN items remain.

Checklist boxes ticked (evidence):
- [x] ARCH_EXPLORATION answers every ISA §9 row, with decisions logged (D-029 accepted). Evidence is next to the box.
- "Zero OPEN items" is done, but the box also needs the second person's §14 semantics review, so it stays open.

Next:
- Kanishk: review ARCHITECTURE §14 (cycle-exact semantics), and read D-029.
- R1–R3 spikes (fresh session, RTL-only context); area estimate and cut list for the pin-unit options.
- Check the first `nightly` run (start it by hand with workflow_dispatch).

## 2026-09-23: Krithik + Claude (phase 1: every remaining protocol)
Done:
- New programs, each against a reference model written from its spec (+ sigrok where it has a decoder): MIDI (UART at 31 250 baud), DMX512 TX/RX, servo PWM, IR NEC TX/RX, SMBus with PEC, LIN 2.x commander + monitor, I2S out/in, HDLC, CAN part B + error handling, USB low-speed device (feasibility only).
- General features (DECISIONS D-024..D-028; §14 P8, P21-P30): event timestamps in PRESC ticks, carrier; BITSYNC flag framing, TX CRC register + CRC_XOR, own-edge rule; JAM, readback modes 0-3, listen-only, own-frame bit; NRZI, pin N, OE auto, SE0, DELIM = se0, CRC_SKIP; tripc `table`.
- Reference models: dmx, nec, smbus, lin, i2s, hdlc, can (rewritten: part B, error frames), usb (low-speed host).
- Fixes: BUGS #16-#31 (servo race, IR padding, CAN register race and level-bit test, USB branch polarity, LIN slot pacing, tripc bound and ld/st offsets, BITSYNC own-edge resync and EOP gap, I2S ADC model, HDLC abort, sigrok DMX and CAN decoder limits).
- Mutation checks: 13 of 13 new features caught (carrier, tick timestamps, flag hold-back and abort, CRC_XOR, armed JAM, strict readback, listen-only, NRZI, CRC_SKIP, OE auto, own-edge resync, half-duplex echo). Two first survived (armed JAM, listen-only): the CAN tests now watch our TXD for the error flag and for silence (no ACK) in bus-off. New fast unit tests for carrier and tick timestamps.
- Full suite: 186 passed (before the last two test edits, which pass on their own); `check_all.sh` and `gen.py --check` below.

Checklist boxes ticked (evidence):
- none new (these are stretch protocols beyond the phase 1 checklist).

Problems / decisions:
- The spec YAML and `src/trw_defs.vh` changed (new commands): pushing starts a gds run.
- SRAM use: CAN 353, USB 335, LIN 208 of 512 words; lane slots at most 12 of 12 (CAN, SMBus).

Next:
- Close phase 1: ablations (now with a much longer feature list, and area estimates to decide cuts), zero OPEN items (incl. the §4.6 connectivity table), semantics review, R1-R3 (fresh session), green CI.

## 2026-09-23: Krithik + Claude (phase 1: CAN via BITSYNC)
Done:
- D-023: BITSYNC pin-unit mode (recovered bit clock with hard sync + SJW resync, bit stuffing, CRC ≤ 16 bits with append/check, readback abort/report, `FRAME n`, one-bit override, TX status events) and `pin_s` (sense pad). Spec YAML: `FRAME` (op 9), `LINE` (op 10), `WAIT` [1], `SYNC` text. §14 P20–P26. `tools/tripsim/bitsync.py`.
- `programs/can.trw`: CAN 2.0A controller on 2 lanes (11 + 10 slots, 3 routines), 1 pin unit.
- `tools/protomodels/can.py`: reference CAN 2.0A node (bit timing, stuffing, CRC-15, arbitration, ACK).
- Tests: `test_can.py` (16) and `tripsim/tests/test_bitsync.py` (6, an HDLC-style configuration). sigrok `can` agrees on every frame and ACK. 155 pytest pass; `check_all.sh` PASS; `gen.py --check` clean.
- Engine mutations: 8 of 9 caught; "resync on own dominant edges" is not (a gap, noted in D-023).
- BUGS #10–#15: test-harness host FIFO, two CAN firmware design problems, a pending-flag slot mistake, reference model stuff-after-CRC, override armed by a stuff bit.
- Confirmed last session's open item: the 1-Wire sigrok leg runs and agrees (READ ROM, ROM code).
- Noted: the ARCHITECTURE §4.6 connectivity table does not match the programs (HOST_OUT from O1); marked for the freeze.

Checklist boxes ticked (evidence):
- none new (CAN is a stretch goal beyond the phase 1 checklist).

Next:
- CAN follow-ups if wanted: error frames and error counters, extended IDs, remote frames; a multi-transmitter propagation-delay test for the resync rule.
- Remaining phase 1: ablations, zero OPEN items (incl. the §4.6 table) + semantics review, R1–R3 (fresh session), green CI.

## 2026-09-23: Kanishk + Claude (planning: protocol coverage, FPGA target)
Done:
- Reviewed the model's protocol coverage against the competition brief:
  - required UART/SPI/I2C and the suggested JTAG/SWD/PS/2 are verified on the model;
  - CAN, USB low-speed and 10BASE-T are not.
- D-012 check on the CAN/USB primitives: resync, bit stuffing (N as a setting), NRZI, readback compare and CRC are general. SE0 detection and the complementary pair must be generalized first (multi-pin pattern match, pin-pair mode). Firmware-only CAN to be tried first.
- D-022: the FPGA target is a Basys 3 running the full design; the reduced iCE40 build is dropped (it could not run I2C). Updated PHYSICAL_DESIGN_AND_CI §6/§8, phase 3 items 8–9 and exit box, the phase 4 freeze box, phase 7, and the OVERVIEW/VERIFICATION CI tables. The template's `fpga` workflow is untouched and informational.
- Docs only; no code or CI changes.

Checklist boxes ticked (evidence):
- none

Next:
- CAN on current primitives (firmware-first), then only the primitives it proves necessary.
- Remaining phase 1: ablations, zero OPEN items + semantics review, R1–R3 (fresh session), green CI.
- Phase 3: choose the Basys 3 build path (openXC7 workflow vs local Vivado) and record it in D-022.

## 2026-09-23: Kanishk + Claude (phase 1: verification plan additions)
Done:
- D-021: verification cross-checks added to `docs/design/VERIFICATION.md`:
  - L0-ASRT (in-RTL `TRW_ASSERT` for formal and simulation);
  - L-XSIM (Icarus and Verilator);
  - L8-EQY (eqy, RTL vs netlist);
  - L8-XPROP;
  - L9 Hardcaml (H0 spike, H1 expect tests, H2 independent OCaml model).
- Tasks added:
  - Phase 2 §2.5, items 12–15;
  - Phase 3 §2.8, items 11–13.
- Other doc updates:
  - OVERVIEW §13 item 6 resolved (RTL stays Verilog);
  - `hardcaml` workflow added to the CLAUDE.md list.
- Docs only; no code or CI changes.

Checklist boxes ticked (evidence):
- none

Next:
- Unchanged: remaining phase 1 work (ablations, zero OPEN items + semantics review, R1–R3 in a fresh session, green CI).

## 2026-09-23: Krithik + Claude (phase 1: PS/2, 1-Wire, SWD, JTAG)
Done:
- Four more protocols verified on the model, each against a reference model written from its spec plus sigrok:
  - `programs/ps2_host.trw` (12 slots + 1 routine);
  - `programs/onewire.trw` (9 + 1);
  - `programs/swd.trw` (12 + 3; SWCLK up to 8.3 MHz);
  - `programs/jtag.trw` (8; TCK up to 12.5 MHz).
- D-020: `SETN rx` (timed RX framing restart + run-time RX length) and `SAMPLE` (sample pin A at a chosen time). Spec YAML + generated files, §14 P18/P19, tripsim, unit tests.
- Reference models: `tools/protomodels/ps2.py`, `onewire.py`, `swd.py`, `jtag.py`.
- Mutation checks: SAMPLE delay ignored, SETN rx length ignored, SETN rx without restart, SWD echo kept / no ACK restart / no WAIT before release, JTAG no TDO restart are all caught. "JTAG samples TDO on the fall" is not caught and is benign on this model (zero-delay target + input synchroniser); rise sampling stays.
- BUGS #6–#9 (sigrok ps2 decoder off by one, PS/2 device model, SWD firmware stale words, a test waveform).
- Docs: PROTOCOL_SUPPORT, ARCH_EXPLORATION, programs/README, PHASE1 summary.
- 133 pytest tests pass; `scripts/check_all.sh` PASS; `gen.py --check` clean.

Checklist boxes ticked (evidence):
- none new (these protocols are beyond the phase 1 checklist).

Problems / decisions:
- D-020. The regenerated `src/trw_defs.vh` means the push touches `src/` and starts a gds hardening run.

Next:
- CAN primitive set (edge-resync RX, bit-stuffing codec, readback compare, CRC helper) and a CAN program.
- Remaining phase 1: ablations, zero OPEN items + semantics review, R1–R3 (fresh session), green CI.

## 2026-09-23: Krithik + Claude (phase 1: PULSE mode, WS2812, DShot)
Done:
- D-019: PULSE mode as two-phase symbols per bit value (pulse-width, pulse-distance, Manchester); §14 P17.
- `programs/ws2812.trw` (2 slots) and `programs/dshot.trw` (2 slots + checksum routine).
- `tools/protomodels/pulse.py`: WS2812B datasheet-tolerance decoder and DShot decoder (checksum, timing).
- Tests:
  - WS2812: two frames, zero tolerance violations, sigrok `rgb_led_ws281x` agrees;
  - DShot 150/300/600/1200;
  - a corrupted checksum routine is caught;
  - new unit tests for OE, SYNC, LATE, SETN and the fabric port filter.
- Two injected PULSE bugs are caught. 117 pytest tests pass.
- Honesty notes:
  - my first guard test assumed a checksum bit that wasn't set; it now asserts its premise;
  - sigrok shows WS281x colours reordered to RGB, which the test now accounts for.

Checklist boxes ticked (evidence):
- [x] tripsim passes its own unit tests (every op, channel rules, pending rule, rotation, pin-unit modes): `tools/tripsim/tests/` + `tools/kernels/tests/`, local pytest 117 passed.

Next:
- CAN feature set (edge-resync RX, bit stuffing, readback compare, CRC helper) + a CAN kernel; or quick "expected" programs (SWD, JTAG, PS/2, 1-Wire).
- Remaining phase 1: ablations, zero OPEN items + semantics review, R1–R3 (fresh session), green CI.

## 2026-09-23: Krithik + Claude (phase 1: tripc v0, programs, protocol roadmap)
Done:
- `tools/tripc` v0 (D-018): the `.trw` language, compiler with static checks and report, JSON image, loader, CLI (`python -m tripc`).
- `programs/`: uart, spi_controller, spi_target, i2c_controller, i2c_target. Compiled images are bit-identical to the reference kernels (slots, K, registers, routines at 3 periods). `tools/kernels/*.load()` now compile the programs, so every protocol test runs on compiled firmware.
- `tools/protomodels/uart.py` (8N1 line model). `test_uart.py`: TX vs the model + sigrok at 4 baud rates; RX with a framing error; 256-byte loopback.
- Pad numbering moved into `spec/tripwire.yaml`.
- BUGS #5: the VCD writer dropped a final steady level, so sigrok missed the last byte; fixed.
- `docs/reports/PROTOCOL_SUPPORT.md`: honest roadmap (verified / expected / needs primitive / not feasible).
- 106 pytest tests pass.

Checklist boxes ticked (evidence):
- [x] Spec only place of encodings; lint CI no diff: lint 35921199653, unit 35921199432.
- [x] UART/SPI-controller/I2C-controller programs pass vs reference models and sigrok (and the two sub-boxes): `tools/kernels/tests/test_uart.py`, `test_spi_controller.py`, `test_i2c_controller.py` (local pytest, 106 passed).
- [x] tripc reports for all programs, slots ≤ 12: `test_tripc.py::test_reports_and_slot_budget`.
- [x] Jane Street assumptions stated: D-003.

Next:
- PULSE mode (unlocks WS2812/DShot/servo/IR, and the `tripsim` unit-test box).
- The primitives for CAN (edge-resync RX, bit stuffing, readback compare, CRC helper), then a CAN kernel.
- Remaining phase 1 boxes: ablation rows in ARCH_EXPLORATION, zero OPEN items + a two-person semantics review, R1–R3 (fresh session for RTL), green CI.

## 2026-09-23: Krithik + Claude (phase 1: spec YAML, generator, phase summaries)
Done:
- `docs/summaries/` with plain-language PHASE0.md (complete) and PHASE1.md (in progress). CLAUDE.md: every phase ends with a summary there.
- `spec/tripwire.yaml` (draft 0.1): all encodings in one place.
- `tools/gen/gen.py`: validates the spec and generates `tools/tripwire_spec.py`, `src/trw_defs.vh` and the ISA/ARCHITECTURE tables; `--check` for CI.
- tripsim now imports the generated tables (`isa.py`, `asm.py`, `pinunit.py`); its hand-written copies are gone.
- New CI workflows `lint` (gen check, defs compile, Verilator lint) and `unit` (pytest with sigrok).
- 15 generator tests; the total is 73 pytest tests, and `check_all: PASS`.
- A hand-edited generated table is caught by `--check` (demonstrated).
- Found on the way: YAML 1.1 reads a bare `off` key as `false`. The keys are now quoted, and the generator rejects non-string field names.

Checklist boxes ticked (evidence):
- none yet. "spec/tripwire.yaml is the only place encodings live; the lint CI regenerates and shows no diff" can be ticked once the `lint` workflow runs green on `main`.

Next:
- Push (note: `src/trw_defs.vh` is under `src/`, so this push starts one ~45-minute `gds` run; harmless).
- Tick the spec box from the `lint` run ID.
- Then either `tripc` v0 or the R1–R3 spikes (fresh session for RTL).

## 2026-09-23: Krithik + Claude (phase 1 start: tripsim v0)
Done:
- `tools/tripsim` v0 (model-first, D-008), written from `ARCHITECTURE.md` + `ISA.md` only:
  - encodings and the shared op table, a minimal assembler, the channel fabric, lanes (EVAL/EXEC, pending, implicit checks, urgent pre-emption, routines with the SRAM rotation, LD/ST, CALL/RET);
  - pin units: TX LEVEL/OE/GAP/SYNC/SETN + SHIFT with a drift-free fractional cursor; RX SHIFT_RX + EDGE_TS;
  - host FIFOs, pads with 2-FF synchronisers, VCD output.
- 28 pytest tests (`python -m pytest -q`, now in `check_all.sh`). Headline measurements:
  - pin-to-pin reaction exactly **7 clocks**;
  - count loop 3 clocks/byte;
  - routines 1 step per 4 clocks;
  - sigrok decodes the model's UART TX at 1 M and 921.6 kbaud;
  - UART RX framing check via CMPM.
- Test quality: three injected bugs (no pending rule, TX one clock early, BUGS #2 fix reverted) each caught.
- `ARCHITECTURE.md` §14: draft cycle-exact semantics (rules F1–F6, L1–L7, R1–R4, P1–P5) fixed while writing the model.

Findings:
- BUGS #2 (spec): 1-bit `seq` makes a tap alias after two missed tokens; fix: a counted drop is a take.
- D-009: OP 15 = `MOVB` (d = B), needed to react to an input with a constant in one action; keeps the 7-clock reaction.
- Q7 (open): registered release limits a lane output to 1 token / 3 clocks and HOST_IN→lane to 1 / 2; §4.4's "1 per clock" is not met.

Later the same day (I2C):
- Pin units: LINKED_RX (with RX_TAIL), COND_EDGE, linked TX shift; separate RX/TX link edges (D-010, §14 P6–P8).
- `tools/protomodels/i2c.py`: reference I2C controller written from UM10204.
- `tools/kernels/i2c_target.py`: write-direction I2C target, 9 of 12 slots:
  - passes at 100 kHz, 400 kHz and 1 MHz against the reference controller, and under sigrok `i2c`;
  - ACK queued 7 clocks after the 8th SCL rise; works down to 12 clocks/bit, so about 2x margin on the Fm+ SCL-high minimum;
  - two injected kernel bugs (ACK on the wrong edge, wrong address bits) are caught.
- `docs/reports/ARCH_EXPLORATION.md` started. 33 pytest tests pass.

Later still (SPI):
- Pin units: CLKGEN, TX_ACCEPT tag filter, TX_PRELOAD (D-011, §14 P9–P12).
- `tools/protomodels/spi.py`: reference SPI target, mode 0.
- `tools/kernels/spi_controller.py`: 4 slots, 1 lane, 4 pin units; one lane output multicast to SCK/MOSI/CS by tag:
  - mode 0 correct both ways against the reference target and sigrok `spi`;
  - fastest SCK 16.7 MHz (the MISO synchroniser limits it); 38 clocks/byte at 12.5 MHz.
- BUGS #3: preload race in the model, found by the SPI kernel at 2 of 3 speeds; fixed (P9).
- Test hardening: every unit must end with zero bad tokens. Injected removal of each tag filter or of the preload fix is caught (one earlier "survivor" was a broken injection script).
- R1 fallback priced on the kernels: no loss in the I2C/SPI speed limits; SPI byte rate -9%.
- 38 pytest tests pass.

Later still (generalization, D-012/D-013):
- Team principle recorded: every addition general *and* optimized; no dedicated protocol blocks (D-012, CLAUDE.md, memory).
- Pin units generalized: event generator (replaces EDGE_TS + COND_EDGE), two-phase framing (replaces RX_TAIL), echo suppression, TX length-in-token. ISA: HS head-bit select (slot now 53 bits).
- `tools/kernels/i2c_target.py` is now a full read + write I2C target in **12 slots** (14–18 before):
  - passes at 100 kHz / 400 kHz / 1 MHz and under sigrok;
  - fastest 12 clocks/bit;
  - disabling any of the 4 new primitives fails 5 tests.
- Docs updated in one pass of exact replacements (ARCHITECTURE §7/§14 P8, P13–P14; ISA §2/§4; VERIFICATION; OVERVIEW; PHASE2); generality table added to ARCH_EXPLORATION.

Later still (SPI target):
- D-014: pin C (select/frame) per pin unit: framing reset, abort on deselect, OE gating, events on C (§14 P15). `Chip.settle_inputs()` models pads held stable through reset.
- `tools/protomodels/spi.py`: reference SPI controller (mode 0, edge-exact MISO sampling, configurable CS setup, partial transfers).
- `tools/kernels/spi_target.py`: 3 slots, 2 pin units. Correct both ways vs the reference controller and sigrok. Measured:
  - SCK ≤ 12.5 MHz (MISO on the rise) or 8.33 MHz (on the fall);
  - CS setup ≥ 3 clocks; MISO released ≤ 3 clocks after deselect.
- Honesty catches along the way:
  - the first reference controller sampled MISO one clock late, which flattered us (12.5 MHz with MISO on the fall); fixed to edge-exact;
  - a "lucky" first byte (0xA5 starting with 1) hid the CS-setup limit; test data changed so an undriven line shows;
  - my own test helper overrode CS setup; fixed.
- Removing framing reset, abort or OE gating each fails a test. 48 pytest tests pass.

Later still (I2C controller):
- D-015: tag filters moved to every fabric consumer port (supersedes D-011's pin-unit filter).
- D-016: CLKGEN periods are IDLE half then ACTIVE half; STRETCH; new WAIT command (op 7); echo taint = own shifted bits on the pin.
- `tools/protomodels/i2c.py`: reference I2C target (address, writes, reads, clock stretching).
- `tools/kernels/i2c_controller.py`: 11 slots + 2 routines (repeated START, STOP). Passes 100 kHz / 400 kHz / 1 MHz × {no stretch, 40-clock stretch, longer-than-a-period stretch}, with sigrok and a bus-timing oracle (tLOW, tHIGH ≥ PERIOD/2).
- BUGS #4: kernel START race (a WAIT armed after its edge); fixed by ordering + tBUF.
- Honesty catches along the way:
  - STRETCH-off survived until the timing oracle and a long stretch were added;
  - the reversed START order is equivalent under current timing (recorded, not claimed);
  - the SPI controller limit is 12.5 MHz (the old 16.7 relied on a lopsided duty cycle).
- R1 fallback re-measured on all kernels: no speed limit changes; SPI controller throughput -8%.
- 58 pytest tests pass.

**Every required protocol role (UART TX/RX, SPI controller, SPI target, I2C controller, I2C target) now runs on the model, each checked by sigrok.**

Checklist boxes ticked (evidence):
- none yet. The tripsim box still needs PULSE; the program boxes need `tripc` and the UART/SPI/I2C-controller programs.

Next:
- I2C target read direction (does a full I2C target fit in 12 slots?); SPI target (flash); I2C controller (needs STRETCH).
- Ablations of the D-007 features.
- R1 risk spike (lane RTL at 50 MHz): best done in a fresh session that has not read `tools/tripsim` (independence rule).

## 2026-09-23: Krithik + Claude (phase 0)
Done:
- Top module renamed to `tt_um_tripwire` (`src/tt_um_tripwire.v`); trivial design = 8-bit counter on `uo_out`, enabled by `ui_in[0]`.
- `info.yaml` filled (title, authors Kanishk and Krithik, 50 MHz, 6x4, placeholder pinout); `test/Makefile` and `test/tb.v` updated.
- `test/test.py`: 4 pin-level tests (reset, count, hold, wrap), gate-level safe (relative counts only).
- `gds.yaml` trigger: `paths` filter (`src/**`, `info.yaml`, `macro/**`, the workflow) + `concurrency` cancel-in-progress. Template jobs untouched.
- Folder skeleton created, then removed at the team's request: folders now appear with their first real file (D-005).
- `docs/DECISIONS.md` (D-001..D-005 + open spec questions Q1–Q6 for the P1 freeze), `BUGS.md`, `CLAIMS.md`, `docs/reports/AREA.md`.
- Local loop: `.venv` via `scripts/setup_venv.sh` (versions pinned in `requirements-dev.txt`); OSS CAD Suite 20260914 appended to PATH in `~/.bashrc`; `scripts/check_all.sh` (L0-TT source sync, Verilator lint, Yosys synth/no-latch, cocotb suite).
- CLAUDE.md: venv rule added.

Checklist boxes ticked (evidence):
- [x] Ledgers exist and `.gitignore` excludes build/sim/formal output: files in `docs/`.
- [x] `docs` workflow green: run 35822749773 (bff60b5).
- [x] gds paths filter works: docs/scripts-only push (bff60b5) started no `gds` run; `gds` 35821375890 kept running.
- [x] `check_all.sh` passes and sigrok decodes a UART VCD: `check_all: PASS` (4/4 tests; an injected "ignore enable" bug made 1 test fail), `sigrok_smoke.py` ok.

- After the first push (commit 0786358): `test` green (run 35821375912); `docs` red on every push so far (run 35821375894). Cause: TT `--check-docs` rejects the template placeholder text in `docs/info.md`. Filled in `docs/info.md` for the placeholder counter; `tt_tool.py --check-docs` now passes locally.
- `scripts/sigrok_smoke.py`: writes a UART 8N1 VCD and checks that `sigrok-cli`'s `uart` decoder returns "TRIPWIRE"; added to `check_all.sh`. `check_all.sh` → PASS.

- `docs/design/ISA.md` written early (D-006 exception): research on PIO, PRU, Loom, FlexIO, P2 smart pins, XMOS, PSoC UDB and Triggered Instructions; one shared op table, implicit readiness checks, flag result from every op, K constants, head-bit test (D-007); Q1–Q6 given proposed resolutions. `ARCHITECTURE.md` §5.2/5.3/6.1 now point to it.
- Phase 1 reordered to model-first (D-008); phase 1 doc updated.
- Honesty fixes: V1 relabelled `[OURS]` (a Hardcaml entry already bounds pin timing statically); survey count marked stale; Loom's utilisation corrected to 78.8% (was ~51%).

- Jane Street sign-up form submitted (team). `fpga` dispatched manually: run 35823310537 on 9fdcf93.
- `scripts/gl_local.sh`: local gate-level run with the pinned PDK and TT Icarus 13 (cached in `~/.cache/tripwire`); `gl_local: PASS` 4/4, and it fails with the CI error when the UDP line is removed.
- [x] Jane Street box reworded to "emailed or deferred with a DECISIONS entry" (team decision) and ticked: form submitted, D-003 deferral.
- Roles: team chose to list Kanishk and Krithik as contributors in the README, no per-role split; box ticked.
- `gl_test` failed in gds run 35821375890 (BUGS #1): the template's `test/Makefile` omits the PDK's `sg13cmos5l_udp.v`. Added it. Verified locally with TT Icarus 13 and a Yosys cmos5l netlist: template fails identically, fix passes 4/4. In the same run, `gds` (30.3 min), `precheck` (13.5 min) and `viewer` passed. Only `gl_test` failed.
- [x] `gds` all green: run 35824649426 (9bd6f7d, manual): gds, precheck, gl_test, viewer. BUGS #1 fix confirmed on the hardened netlist. **All phase 0 exit boxes ticked.**
- `docs/reports/AREA.md` row 1 from the `GDS_logs` artifact of run 35824649426: 79 logic cells (8 flops), 0.13% utilisation, setup slack +13.6 ns at the slow corner, zero overflow, DRC/LVS/antenna clean. Magic DRC takes ~25 of the 27 flow-step minutes even on an empty tile.
- Clarified in PHYSICAL_DESIGN_AND_CI §5 and CLAUDE.md: the 6 h limit is per job (the `gds` job), not per workflow.
- Team: design for 6x4; tile-size and SRAM questions not being emailed for now (D-003); R3 settles the SRAM macro.
- [x] `fpga` run once: 35823310537 green.
- [x] Pages viewer live: https://kanishk234.github.io/protocol-emulator-asic/ (gds run 35821375890: `gds` and `viewer` green; `precheck` and `gl_test` still running at time of writing).

Problems / decisions:
- D-002 keeps `tt_um_tripwire` despite TT's uniqueness advice; rename path noted.
- `sigrok-cli` not installed yet (needs sudo).

Next:
- User: `sudo apt install sigrok-cli`; commit and push (triggers first `test`, `docs`, `gds`); enable Pages (Source = GitHub Actions); run `fpga` once by hand; confirm the repo is public.
- User: Jane Street sign-up form + email (D-003); assign roles (then Claude writes them into the README).
- Claude: sigrok UART VCD decode check in `check_all.sh`; record CI results and AREA row 1.

## 2026-09-22: team (phase 0, not started)
Done:
- Research and idea selection (TRIPWIRE).
- Design docs written: `docs/design/` (overview, architecture, verification, physical design & CI, phase 0–7 docs).
- `CLAUDE.md` created.
- Template (cmos5l branch) cloned locally in WSL.

Checklist boxes ticked (evidence):
- none yet

Next:
- Phase 0, task 1: create the GitHub repo from the local template clone, rename the top module to `tt_um_tripwire`, commit the docs.

## 2026-10-01: Codex (phase 2: evaluate 16% GRT diagnostic)
Done:
- Reviewed GRT diagnostic run [36949467252](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36949467252) for exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284` (2 lanes, 4 pin units, U0 full; 20 ns; 56% density). It passed candidate validation and global routing in about 8 minutes, with zero overflow on every layer; the diagnostic stops before detailed routing.
- Compared its saved GRT data with 12% run 36906496173 / hardening 36913096552 and 30% run 36899340155. At 16%: capacity 601,423, demand 255,230, usage 42.44%, wirelength 2,465,539 um, and 262,708 guide rectangles. Relative to 12%, capacity is 4.8% lower, while demand, wirelength, and guide rectangles each increase about 0.3%. Both 12% and 16% have zero GRT overflow. The 12% detailed-route attempt timed out after 330 minutes with 25,030 intermediate violations remaining after two optimization iterations; no final DRC was produced.
- Conclusion: 16% has no demonstrated aggregate routeability advantage over 12%, and GRT-only success does not establish DRT completion, timing, or signoff. Do not claim a passing hardening or blindly repeat a full run. Assess whether the saved 16% GRT checkpoint can be continued through DRT in the pinned LibreLane/PDK environment; compare routed evidence before choosing another full run.
- Added `.github/workflows/gds-drt-continuation.yaml` to resume from the saved GRT `state_out.json` and run only the detailed-routing step. Commits `f308fa2` (workflow) and `05568a6` (report/worklog) were pushed to `main` by `Krithik4`.
- Dispatched DRT continuation [36951141285](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36951141285). Artifact download, candidate/checkpoint validation, and pinned image build passed; its DRT step is active. The run changes no candidate hardware inputs and is not a full signoff workflow.
- `test`, `lint`, and `docs` are green on commit `05568a6`; the `unit` workflow remains in progress in its chip-level/L3 RTL step. No RTL, `src/config.json`, `info.yaml`, macro, or active hardening input changed. `git diff --check` passed.

Checklist boxes ticked (evidence):
- None. Run 36949467252 is a GRT-only diagnostic, not a completed hardening.

Next:
- Monitor run 36951141285 for detailed-route completion, runtime, and route DRC; if it completes, continue downstream checks before claiming GDS signoff. If it times out, pivot from GRT-adjustment-only experiments to a separately controlled timing RTL or route-aware repair experiment. Keep 20 ns, all protocol behavior, and D-066 timed live reconfiguration intact.

## 2026-10-01: Codex (phase 2: run L3 on hardened netlist)
Done:
- Added `test_internal/chip/tb_chip_gl.v`, a pin-only harness that instantiates `tt_um_tripwire` from the hardened netlist while keeping the cocotb-visible pins expected by the existing `test_l3.py`.
- Added manual workflow `.github/workflows/l3-hardened-gl.yaml`. It downloads the final netlist from successful GDS run 36799356107 for exact candidate `3393eea9a58c5cad9077cc360a8515d0e5ec8284`, installs the pinned IHP SRAM/standard-cell models and Tiny Tapeout Icarus 13, and runs the unchanged UART/SPI/I2C L3 test module.
- Local Icarus 12 elaborated the hardened netlist and test harness successfully (34,161,403-byte simulation image); this is compile evidence only, not a valid simulation because Icarus 12 triggers BUGS #1. The GitHub workflow uses Icarus 13.
- Dispatched gate-level L3 run [36952644578](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36952644578). Its artifact download completed and the pinned PDK/SRAM setup is active; L3 simulation has not started yet. The separate DRT continuation [36951141285](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36951141285) remains in its detailed-routing step.
- On commit `f47a5c8`, `test` 36951822413, `lint` 36951822419, `docs` 36951822379, and `unit` 36951822390 all passed. On the newer test/workflow commit `32bf4f0`, test/lint/docs passed; unit is still running. No hardware input changed. `git diff --check` passed.

Checklist boxes ticked (evidence):
- None from these runs yet. Box 6 remains open until the exact hardened-netlist L3 run passes; the DRT continuation is not full GDS signoff.

Next:
- Monitor runs 36952644578 and 36951141285. If the gate-level L3 suite passes, record the evidence and tick only box 6. For the DRT continuation, inspect final route DRC/runtime and continue downstream signoff before treating it as a passing hardening. Preserve the 20 ns target, all protocols, and D-066 behavior.
