# TRIPWIRE work log

Newest entry at the top. One entry per work session.
- Keep entries short.
- Evidence means a CI run ID, a test command and its result, or a file path.
- Raw logs are not committed; link to them instead.

## 2026-10-09: Codex (diagnose clock8 screen startup failure)
- Workflow38011244004 failed at source hash validation before sizing/routing; routine main test/lint/unit/docs green, no running main jobs, two legacy queued. DRT/exported netlist hashes differ but all33779 logical cells/connections match. Corrected separate pinned hashes and added topology comparison; BUG89 logged.103 focused tests and actual exported-source target generation pass; diff check clean. Fix local, no new dispatch or phase checkbox. Next publish source-validation fix and rerun screen.

## 2026-10-09: Codex (publish approved clock8 strength screen)
- User approved publication/launch. Separate tools/CI/docs commits775381d/45c5cd3/53584bd pushed; remote main verified at53584bd7cb93484521466b5828168a194c929b20. Dispatched [gds-native-clock8-strength-screen38011244004](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38011244004) on that exact revision; queued at dispatch verification. Prior102focused checks passed; hardware history check showed no pending src/info/macro commits.
- FIPE and unrelated prototypes remain local; existing readiness/SRAM edits are not included. Next inspect actual physical sizing/legalization,0overflow, fresh antennas and allcorner/50pshold result before proposing extracted continuation. Electrical closure and official Phase2 gates remain open; no boxes ticked.

## 2026-10-09: Codex (prepare twelve-strength physical screen)
- Prepared local exact-source clock8 sizing screen and separate manual workflow. Pins route37998284236/headaceb926a/final NL SHA, validates trusted full hardware/clock8 recipe, preflights12target master/connectivity changes, legalizes, resets old signal wires, requires0overflow, fresh antenna checks/at most one cleanup, and allcorner/50pshold qualification. Existing electrical violations still need repair; screen is not official closure or final extraction.
- Validation:102focused tests pass with project Tcl runtime on PATH; initial Tcl invocation failed because tclsh was absent from default PATH, corrected without code changes. YAML parses and git diff check passes. No commit/push/dispatch or phase checkbox. Next publish the reviewed helper/workflow under the user Git rules, run the physical screen, then evaluate actual qualification before DRT/extraction.

## 2026-10-09: Codex (clock8 setup reserve diagnosis)
- Checked main: no in-progress workflows; legacy runs37655518919/37655518925 remain queued. Eleven-cell fixed-wire sizing passes20ns but has only3.27ps slow setup reserve. Adding place6637BUF4 raises inferred reserve to128.17ps; 19.8ns diagnostic WNS−0.071825214ns. Two other gate-sizing probes add no useful margin or worsen it. Updated exact-source sizing helper to twelve targets; electrical counts remain125/29/1slew,21fanout,8cap. No routed gain, publication or phase box claimed. Evidence: PHASE2_CLOCK8_TIMING_REPAIR.md and temporary margin comparison. Next prepare exact-source physical qualification before any publication request.

## 2026-10-09: Codex (publish approved relocation continuation)
- Clock8 continuation37998284236 completed successfully/artifact11650178212, but fresh extraction rejects timing promotion: slow setup−1.467189078ns, typ/fast setup0; fast hold+0.094165012ns,typ+0.196403122ns,slow+0.367677788ns. Slow/typ/fast slew125/29/1, fanout21each, cap8each. Fresh checks independently reproduce electrical_summary.json. Retain original strength37954320974 as actual timing baseline; clock8 substantially reduces fanout but is not a timing/electrical pass. No main workflows running; two legacy workflows still queued. Next map extracted slow paths and residual electrical loads before a separate repair. No phase box ticked.
- Additional parallel work during clock8 DRT: prepared local exact-NL/DEF balanced clock-branch planner and identity-topology validator. Each16sink branch partitions into twoBUF8/8sink groups,2upstream loads.9focused tests and four actual-source synthetic audits pass. Pinned master footprint is47.1744µm²/two-buffer branch before later repairs. No physical move, clock skew/timing pass or new dispatch; candidate plans remain local until extracted clock8 results guide selection. All electrical/Phase2 gates remain open as applicable; no checklist ticked.
- Parallel residual/phase audit while clock8 route37998284236 runs: downloaded exact screen checkpoint NL/DEF/config and mapped residuals. Four internal clocks each drive16BUF8inputs/no diodes; data29451 has7diodes/8other andplace8554 has2/8. REN shareshold11833 in this new checkpoint, so old hold11848 patches cannot be reused. One-buffer split of16leaves leaves9upstream loads; complete clock restructuring needs broader skew/hold measurement. Updated official-readiness report with current clean-build lead, retained extracted strength baseline and explicit remaining Phase2/official gates. No hardware edits, new dispatch, false phase ticks or physical closure claims.
- User approved clock8 continuation publication: tools/CI/docs commits pushed through `aceb926a166c18b6d76ed79c83c5df800accf472`, remote main verified. Launched [gds-native-clock8-route37998284236](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37998284236) on that exact head; in progress at verification.99 focused checks passed before publication; no pending hardware-history changes. Next inspect fresh antenna/timing gates, completed route DRC and extracted setup/hold/electrical counts before candidate selection. No phase checkbox ticked.
- Prepared clock8 DRT/extraction continuation locally using exact successful37990280838/head dfe1a9f. Adds a guarded profile and standalone workflow; fresh antenna/optional one cleanup/allcorner/50ps gates precede unchanged stock DRT/extraction.99 focused checks pass. Exact slow screen triage: four internal clock drivers have16loads, two data drivers15/10; remaining SRAM REN/ADDR0 slew and DOUT0 cap require new-checkpoint audits. No continuation published/dispatched yet, no extracted clock8 result, no phase box ticked.
- Results check: REN37989633910, branch37989637064 and clock8 37990280838 all completed successfully; latest main test/lint/docs/unit green. Exact target timing/comparison.json (excluding inherited source reports): setupWS0allcorners for all3; fast hold REN+101.780ps, branch+80.8179ps, clock8+100.377ps. Slow/typ/fast slew counts REN27/1/0, branch1/1/1, clock8 11/1/1; fanout198/197/6respectively, cap0/1/1respectively eachcorner. These remain estimated screens, not extracted signoff. Prioritize clock8 fresh antenna qualification and DRT/extraction; branch is a separate promising slew experiment. Original extracted timing baseline remains unchanged. No phase checkbox ticked.
- User approved clock trial publication: separate tools/CI/docs commits pushed through `dfe1a9f46d9b97d20550d1326fb7755cbe2829cf`, remote SHA verified. Dispatched [gds-native-clock8-screen37990280838](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37990280838) on that exact head; queued at verification. REN37989633910 and antenna-branch37989637064 remain in their physical qualification steps.76 focused clock/clean-flow/route checks passed before publication. Next compare allcorner timing, final clock fanout and area with native hold100 baseline; no closure claim or phase checkbox yet.
- Continued while REN/branch screens run: prepared local manual gds-native-clock8-screen and guarded opt-in clean stock runner integration. Starts frozen full2/4 RTL from clean synthesis, changes only clustering size8, preserves native hold100/20ns/allcorner constraints, and records explicit trial receipt.76 focused clean-screen/clock/route tests pass; diff check passes. Compare this independent trial with native hold100 clean baseline, not the six-strength ECO route. Both approved physical screens still in progress; no third workflow launched and no phase boxes ticked.
- While approved REN37989633910/branch37989637064 execute physical qualification, audited all164 original clock fanout failures: all clk_regs branches,10–17 attached sinks, zero antenna cells. Prepared local clock_cluster_trial.py and10 passing tests; applies one size8 CTS key to the fully timed native hold100 recipe, preserving existing timing/area controls and labeling it unmeasured. Actual downloaded config preparation passes; no clock tree or third workflow launched. Next inspect both active screens, then choose qualified DRT continuation or a separate clock clean-build trial. No phase boxes ticked.
- User approved follow-up publication: separate helper, GL-validator, CI and evidence commits pushed through `861c4bb630c37d6cc3d6682dcdf7fa38c344ac79`; remote SHA verified. Launched [REN screen37989633910](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37989633910) (in progress) and [antenna branch screen37989637064](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37989637064) (queued at verification), both on that exact head and independently using original strength route37954320974.142 focused checks passed before publication; FIPE/unrelated prototypes stay local. Next inspect fresh qualification/electrical counts before proposing any DRT continuation. No phase exit item ticked.
- Prepared a second independent local screen for one antenna-loaded branch on original strength route37954320974. One BUF4 splits eight selected distal functional/antenna pins; all existing diodes remain. Exact-source identity-topology audit rejects deletion/resizing/inversion/unrelated rewiring; Tcl preflights before mutation. Wrapper/image/manual workflow and shared fresh GRT/antenna/STA/50ps gates are prepared; no physical run dispatched.142 focused checks pass (mocked physical APIs), actual-source synthetic topology audit passes, and diff check is clean. Publication remains pending under supplied Git rules; no phase checklist ticked.
- Completed continuation37983933655/artifact11644161675:0DRT/antenna violations, setupWS0allcorners, fast hold+46.77775ps (fails50ps gate), typ+141.509ps, slow+306.416ps. DOUT0 cap clears, but slow/typ/fast slew166/36/4, fanout204each and cap6each worsen overall; retain strength37954320974. Fresh checks independently match summary. Exact netlist hash/logical audit passes:65 extra antenna cells, no existing logical changes. All8 added fanout violators have antenna loading; two sub50ps hold paths are config latches47709/47705→flops46991/46990. Evidence and next repair priorities recorded in SRAM report. No new GL run or phase box claimed.
- Continued independent preparation: REN-only move helper, wrapper/image and manual screen workflow now exist locally. Shared screen orchestration preserves default DOUT0 behavior and adds a separate REN target/output; mixed-move histories fail. Exact NOR2B_1 geometry/site/connectivity guards and fresh antenna/all-corner/50ps hold gates are covered by115 focused passing checks. No REN physical run launched and no timing benefit claimed. These follow-up changes remain uncommitted; no checklist boxes ticked.
- Parallel preparation: added a local, deliberately unregistered relocated-route GL validator. It requires successful exact run/SHA, reviewed final-netlist SHA256, unique clean DRT state, matching netlist path, qualified unrepeated relocation and unchanged full recipe/50ps gate. It cannot dispatch or claim relocation GL before the artifact is reviewed. 58 focused validator/continuation tests pass; `git diff --check` passes. These follow-up validator/test changes remain uncommitted.
- Published approved tools, CI, tests and evidence in separate commits through `0fa2b9f44a06b053142295e41b69d5640e547495`; verified remote `main` matches. FIPE and unrelated untracked prototypes remain local.
- Dispatched [gds-sram-relocate-route 37983933655](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37983933655) on that exact SHA; queued at dispatch verification. It continues the successful relocation screen through detailed routing and fresh extraction, then compares timing and electrical violations with the passing strength route.
- Validation before publication: 91 focused checks passed; `git diff --check` passed. No hardware-history changes pending. No phase checklist boxes ticked.
- Next: inspect actual detailed-route DRC, extracted all-corner setup/hold and electrical counts; retain the original strength route if relocation regresses. A relocated-netlist GL run and official clean-flow closure remain required.

## 2026-10-09: Codex (strength extraction passes timing, electrical remains open)
- Prepared exact SRAM relocation DRT/extraction continuation and manual workflow for37978260010/head815f78c. Original routed NL hash, move-only logic/antenna chain, post-cleanup retained site/history, trusted config/views and saved gates checked; fresh stock antenna/STA before DRT, no repeated physical repair. Old extraction preserved; new before/after summary separates target cap, timing and full electrical qualification.91 focused tests pass; actual downloaded baseline/logic/antenna/history/site audit passes. No dispatch yet; next scoped reviewed publication/launch, keep original passing checkpoint and FIPE local.
- Result check: strength GL37975960876 passes22/22,0fail/skip in57min; servo959.61s explains normal test7 pause. Exact strength route/NL hash validated; relocated candidate not covered by this GL. Latest test/lint/docs/unit green; no main runs active, only legacy37655518919/37655518925 queued.
- Local watchdog check62936 completed normal servo waveform assertions but full command failed independent decoder because sandbox libusb initialization returned empty output (BUG88), not timeout or VCD timestamp issue. Original and integer-formatted captured traces both decode7.5%/5.0% outside sandbox; fractional-clock writer rejection checked. Added integer VCD formatting alongside25ms edge bound, both local. Next exact relocation DRT/extraction, antenna-aware fanout/electrical repair and clean-build reproduction; no phase tick.
- Reviewed user-supplied organizer email and linked SRAM walkthrough (web tool inaccessible, read-only HTTPS fallback succeeded). Recorded COMPETITION_UPDATE_2026_10_09.md; corrected unsupported66MHz CMOS5L pad claim in overview/physical docs. Keep50MHz/6x4/2-lane4-unit targets, all timing gates and Phase2 order unchanged.8x4 awaits official template; no macro/grid/waiver changes copied. Local servo watchdog verification62936 remains running at receipt.
- Relocation37978260010 succeeds12min/artifact11641030625. Actual relocation/post-DPL exact-site/master/nets and33041-wire reset receipts pass; fresh GRT/antenna/STA qualify. Setup0all, holdfast+0.101780ns/typ+0.204571ns/slow+0.383295ns. Estimated slew24/1/1 slow/typ/fast, fanout198each, cap0each; not extracted macro improvement and fanout worsens. Preserve original timing-passing source; next exact-checkpoint DRT/extraction comparison. GL still active and local servo timeout check session62936 ongoing; no phase tick.
- Broader audit maps all32 non-clock fanout violators: each has antenna cells,29have8otherpins/3have7, total78antenna+253otherpins. Verified actual antenna masters. Pinned stock post-GRT design-repair Tcl inspected; prioritize bounded antenna-aware repair after insertion with fresh routing/antenna/hold checks. Generalized pinned placement planner to REN; three independent footprint-clear candidates ~19–20µm from pin vs315µm.33 screen/Tcl checks pass; no REN move.
- GL stall concern: current job~28min; earlier GL37895415098 test7 servo took961.99s (~16min), test8 I2S72.66s, total56min. Live logs unavailable; do not infer present test or confirmed hang from7/22. Found unbounded servo edge wait (BUG87), added25ms simulated bound for future runs; local targeted RTL servo test session62936 running. Remote37975960876 unchanged; relocation37978260010 still active.
- Independent current extracted REN probe:6 successful local STA processes, baseline all6timing values match CI1e-6ns.29426 NOR2B2 retains all setup/hold; REN slow1.740411→0.896252ns,typ1.127567→0.581867ns,fast violation clears. Slow/typ still fail; cap/fanout unchanged. Added library area3.6288µm², fixed-wire only. Missing NAND3_2 rejected before link; use buffering/placement for28807. Current extracted fanout164 clock-named/32other. Both relocation37978260010 and GL37975960876 still running; latest test/lint/docs green. Evidence local, next inspect relocation and prepare bounded REN placement/load repair.
- User approved relocation publication: committed24e4305/275b3a7/815f78c, verified remote main815f78cd3423ddffd69374ba4c0e9cc4e849a3ce, launched SRAM screen37978260010 on that exact SHA (queued at receipt). Outgoing hardware history empty, FIPE/unused prototypes excluded. GL37975960876 remains active. Next inspect pinned OpenDB relocation/legalization, fresh GRT/antenna and allcorner timing; no physical gain claimed.
- Standalone sram_relocate_screen.py/manual gds-sram-relocate-screen prepared: exact route37954320974, trusted source/config, unchanged exported baseline/logic, fresh views, unique relocation/DPL/reset receipt, GRT0overflow, antenna cleanup without repeated GRT, fresh allcorner nonnegative/50ps gate.53 focused tests pass across orchestration/Tcl/reset/GL guards; bash/diff checks pass. Physical operations mocked; no workflow publication/launch or timing benefit yet. Next scoped publication/physical screen, preserve passing source and exclude FIPE. GL remains running at last check.
- Implemented local SRAM one-buffer relocation Tcl, dedicated GRT/antenna wrapper and pinned-base Dockerfile. Complete source/master/pins/occupancy preflight, orientation-before-location, unchanged connections, exact post-DPL site, inherited wire reset and no antenna-stage repeat.21 Tcl/shell/reset checks pass (mocked OpenDB); physical binding/legalization/routing not exercised. Upstream API semantics checked, pinned runtime remains required. Next standalone screen orchestration/source guards; no relocation workflow dispatched or phase tick.
- SRAM planner now uses pinned LEF and actual placed footprints, including fillers/macro. Original nearest row63 site overlaps two components; three gap candidates pass independent complete footprint-overlap checks. Best row65(20.64,249.48)FS ~20.38µm from pin; no physical move, pin-access/PDN/routing-obstruction checks outstanding. GL still running expanded L3 at receipt. Diff check passes.
- Added local read-only sram_buffer_plan.py with exact NL/DEF hashes and buffer connectivity/placement guards. Actual route yields row63 candidate(22.56,241.92)µm,FS,10.90µm pin-to-origin estimate versus451.64µm current. Macro halo cuts rows through238.14µm, so lower tempting coordinates excluded. Occupancy/pin access/legalization not yet checked; no ECO or electrical gain claimed. GL still running.
- Parallel exact-route SRAM DEF/LEF/netlist audit: FS macro pin centers resolved; bits0/1/2 each drive one existing buffer roughly452/328/297µm away. Bit5 has two sinks; REN driver315µm away. Recorded one-buffer wire9447 relocation experiment with legal-row/pin-access/supply/antenna/reroute/allcorner hold requirements; no physical edit or added cells yet. GL37975960876 running expanded L3 after exact artifact validation passes.
- User explicitly approved GL publication commands: committed/pushed bf10b23 and verified remote main bf10b2352883975059d9091900776471d3a1d231. Dispatched l3-native-routed-gl37975960876 on this SHA for route37954320974, queued at receipt. Only GL helper/test/workflow files committed; current evidence docs and unused prototypes remain local, FIPE excluded. Next inspect exact artifact validation and full protocol results. Receipt recorded locally.
- Prepared native routed GL support for37954320974: exact successful main SHA/source gate/no-repeat history/DRT0/config checks plus final NL hash d5cc09ed3a7db5cbf941fbcacc30347ffac0f3a8488f56b964b9d46f36e327dc. Validated downloaded actual artifact. Workflow selects strength artifact and source, adds completion trigger, defaults to this run.41 focused tests pass including substituted-NL/repeated-repair rejection. Changes local; protocol GL not run yet. Next publish scoped GL helper/workflow changes and dispatch exact source, then electrical trials.
-37954320974 succeeds70min/artifact11632141562; latest test/lint/docs/unit green. Actual DRT zero violations; fresh extracted setupWS0allcorners, holdfast+0.056323503ns/typ+0.159938733ns/slow+0.331939818ns. Removed native−0.522ns setup failure;50ps hold gate passes with6.32ps headroom. No positive setup reserve measured for this route.
- Electrical slow/typ/fast slew130/11/4,fanout196each,cap5/5/6. Downloaded actual corner/electrical summaries to/tmp; report records exact evidence. GRT cap0 does not survive extraction. Next preserve checkpoint, prepare exact modified-netlist GL and bounded electrical repairs; official reproduction still required. No phase tick.

## 2026-10-09: Codex (parallel corrected-checkpoint electrical triage)
- Continued final DEF placement audit:28820/28807 sinks form distal groups near right edge; partial cell-origin maps span262–504µm/276–758µm Manhattan distance. Recorded bounded spatial partition experiment rationale and mapping limitations; no physical ECO applied. Main37954320974 and unit37954299925 running; latest test/lint/docs green. Live log API returns unavailable blob, so exact routing iteration not inferred. Next complete physical pin/load map and inspect extraction when available.
- Follow-up mapped exact final ECO netlist:28820 has12 antenna/7 other attached pins;28807 has7 antenna/8 other pins; REN includes ANTENNA_53 plus write-enable hold branch and SRAM input. Confirmed pinned CTS size option/default/forwarding. Prioritized antenna-aware partitioning and fresh clearance over indiscriminate logic buffering; no diode removal or physical modification. Exact pin counts distinguished from STA weighted fanout.
- Retrieved three actual STAMidPNR checks reports from37949660848. Fanout187 splits164 clock-buffer-named/23 other drivers each corner. SRAM REN slew violates all corners; remaining16 slow rows belong to28807 branch including antenna loads. Recorded exact values and prioritized bounded REN repair/data load partitioning, separate clock-tree repair and clean-build reproduction in PHASE2_SRAM_ELECTRICAL_NEXT_STEPS.md.
- Strict extracted-report parser rejects screen reports with omitted empty capacitance section; retained guard and used existing screen metrics, no missing-section pass inferred. Continuation37954320974 still active at routing/extraction step. No hardware/config change, new workflow or phase tick. Next use actual extraction to select physical target and preserve setup/hold.

## 2026-10-09: Codex (reset strength checkpoint qualifies)
- User explicitly approved publication and launch: committed c8f71f8/dffa228, verified remote main dffa228c710ff69749c70bb64ab38df056ed0f21, and launched native-strength-route37954320974 on that SHA (in progress).42 focused tests pass; outgoing hardware history empty. Next inspect detailed-route connectivity/DRC and actual extracted all-corner timing/electrical audit. Dispatch receipt recorded locally.
- Screen37949660848/headb6515e5 succeeds in11min, artifact11625986970. Receipt confirms33041 ordinary wires reset; qualification passes. Estimated setupWS0allcorners; holdfast+0.101697ns/typ+0.204571ns/slow+0.383296ns. Electrical slewfast1/typ1/slow17, fanout187each, cap0each; not electrical closure or extracted signoff.
- Updated continuation helper/workflow/test source registry to this exact successful checkpoint; old mixed-wire source is superseded. Next publish these scoped files and run native-strength-route, then inspect DRT/extracted timing/electrical results. Latest supplied AGENTS Git rule leaves commits/pushes to the user. FIPE remains local only; no phase tick.

## 2026-10-09: Codex (native DRT restart geometry fixed)
- Publication receipt: remote main verified b6515e5ca22111b5f54489aadf9034cda7d2d266; corrected strength screen37949660848 is running on that exact SHA. Source download/provenance checks pass; physical sizing/routing/qualification step is active. Latest test/lint/docs pass; unit remains running. Next inspect reset receipt and fresh timing before registering any detailed-routing continuation. No new extracted timing result.
- Continuation37945867391 fails DRT-0206 after fresh qualification, unvisited24874/Y (_19292_) and24895/Y (_19312_). No extraction/new WNS. Actual post-ECO GRT DEF retains original detailed ROUTED segments on both nets; BUG86 records mixed routing restart.
- Added ordinary signal/clock dbWire cleanup after legalization and before first GRT, preserving POWER/GROUND/special routing and logical connectivity. Pinned API/positive-reset receipt required; continuation rejects older screen lacking receipt. No full GRT after antenna cleanup.81 focused tests pass including real Tcl reset cases/power preservation, source/history guards and orchestrated timing gates; diff/shell checks pass.
- Next publish scoped correction and rerun strength screen from original hold100; require fresh success before registering new DRT source. Existing approval applies; FIPE excluded, no hardware/spec change or phase tick. Actual physical fix not yet proven.

## 2026-10-09: Codex (qualified strength DRT continuation prepared)
- Prepared native_strength_route.py and gds-native-strength-route for exact successful screen37943825506/headf2c2a82. Trusted hardware/full config, originalNLhash, complete six-change/antenna-only chain, saved checkpoint identity, zero-overflow and cleanup history are checked; fresh antennas and allcorner STA/50ps hold gate before stock DRT. No repair/GRT repeated.
- Preserves older extraction separately before fresh DRT0DRC-required extraction, including electrical audit/effective signoff constraints.76 focused tests pass (24 new provenance/chain/orchestration cases), diff check passes. No extracted gain or phase tick yet.
- Existing explicit commit/push/launch approval covers this continuation; next publish scoped helper/workflow/evidence groups and dispatch. FIPE/unused prototypes excluded. SRAM relocation remains separate electrical work.
- Published2e812b1/03181d9/f9845e3; verified remote mainf9845e3303c3fe11d3e762b4c5f960f589a7a6e0. Dispatched native strength route37945867391 on that exact SHA, queued at receipt. No hardware changes in outgoing history. Next fresh qualification, DRT0DRC and actual extraction audit.

## 2026-10-09: Codex (native strength screen qualifies)
- Corrected strength37943825506 succeeds in8min; artifact11622704162. All six sizing receipts, legalization, fresh routing0overflow, antenna cleanup and fresh STA gate pass. SetupWS0allcorners; holdfast+0.100882ns/typ+0.204349ns/slow+0.382839ns. Gates qualified=true, physical_screen_only=true, official=false.
- Fresh electrical counts slewslow18/typ0/fast0, cap1eachcorner; not electrically clean. This is estimated GRT timing, not new DRT/extracted timing. Original hold100 GL22/22 remains valid only for original routed netlist.
- Nightly/test/lint/docs green; two recent unit jobs still active at receipt. Next guarded DRT/extraction of exact qualified strength checkpoint, then electrical/GL review. No phase tick or official launch.

## 2026-10-09: Codex (native GL passes; physical name guard fixed)
- Corrected native GL37895415098 passes22/22,0fail,0skip on exact original hold100 routed NL. Latest routine CI green. Strength37895412132 fails at all-target connectivity preflight before mutations; no physical timing result.
- Exported failure baseline matches all six logical targets. Actual downloaded ODB/DEF proves hierarchical bracket escapes preserved in physical names; generated targets/mocks omitted them. Fixed BUG85 by generating exact names, retaining strict comparisons/preflight and improving mismatch diagnostics.85 focused tests pass including real Tcl runtime/observed name spelling, source hash generation and orchestration. No gate relaxation.
- Full-log approval review timed out; completed evidence retrieval via read-only job-log/artifact retries and terminated stalled request. Next scoped approved correction push and strength-only dispatch; do not repeat passing GL. FIPE excluded; no phase tick.
- Published0e2c19a/f2c2a82; remote main verified f2c2a82b81195ac380ebf7e6fbcbd48ee0315923. Relaunched strength37943825506 on that exact SHA, running at receipt; passing GL retained. No hardware history in outgoing commits. Next inspect all-target preflight, fresh routing/antenna/STA and electrical consequences before DRT.

## 2026-10-09: Codex (native source config failure fixed)
- GL37895041603 fails source validation; strength37895037616 also fails same validator before physical work. Actual source DRT config omits synthesis/hold settings; full src/config_native_stock.json contains AREA1/100ps/20ns. BUG84 records mistaken step/full config assumption.
- Fixed validator to check step clock/routing separately from full recipe; physical runner now uses fully audited native config.84 focused tests pass, including omitted step synthesis and wrong full hold target. Downloaded actual source metadata/NL/full config and reproduced passing validation; routed NL SHA256a75d8719dd48838ae6b1f051f1147b1835d7a050c55dbd7144d5ef14b438f8bb. No hardware/timing test ran in failed jobs; gates unchanged.
- Existing explicit publication approval covers correction/relaunch; next push scoped helper/test/bug evidence and launch fresh jobs. FIPE remains excluded; no phase tick.
- Published c3b0d52/7019b08 and verified remote main7019b08620933d7e5e2d01e0fb201302036f95db. Corrected strength37895412132 running and GL37895415098 queued on that exact SHA at receipt. No hardware history in outgoing commits.

## 2026-10-09: Codex (native six-strength physical screen prepared)
- User explicitly approved executing reviewed grouped publication/launch commands. Published08c482d/b9765e8/8553807; verified remote main8553807c762c140970c34801fdec383c8b833883 matches local. Strength screen37895037616 and native GL37895041603 both running on that exact SHA; routine CI active, unit queued at receipt. FIPE/unused prototypes excluded; no main hardware change. Next actual fresh physical timing/antenna results and protocol GL outcome.
- Added isolated pinned-base image/wrapper, physical runner and gds-native-hold100-strength-screen workflow for exact route37870374707. Trusted pre-download hardware/config checks, exact extracted NL hash, six sizing receipts, legalization/freshGRT0overflow, conditional congestion-disallowed antenna cleanup/fresh NL+PNL, cleared stale parasitics and fresh allcorner STA/50ps fast hold enforced. No repeated timing repair, full GRT after antennas, DRT or relaxed gates.
-83 focused tests pass, including full orchestration pass/fail hold and optional cleanup, real shell injection, Tcl all-target preflight, exact-change/physical-view audits and workflow source identity. Shell syntax/diff checks pass; physical APIs mocked locally, not a physical pass. One documentation patch missed its long-line context, corrected with exact text.
- Workflow/helper changes remain local and unlaunched under supplied git rule. SRAM relocation remains a separate next trial. Next publish reviewed groups via user-run git commands and launch physical strength screen plus exact-source native GL; review actual screen before DRT/extraction. No source hardware/spec change or phase tick. FIPE excluded.

## 2026-10-09: Codex (guarded native sizing contract)
- Prepared native_hold100_size.py/.tcl: exact extracted source hash, six targets from one Python contract, all-target preflight before mutations, power/signal pin compatibility and unchanged nets. Actual extracted prototype exact six-change rehearsal passes.
- Found/fixed BUG83: existing logical-cell audit silently skipped multiline SRAM buses. Added bus-rewire rejection and reaudited actual full netlist successfully.70 focused Python/Tcl/helper tests pass; Tcl physical APIs mocked, no physical pass. Initial malformed synthetic fixture corrected before validation.
- Changes remain local. Physical wrapper/workflow still required; do not claim launched/repaired layout. Next wire sizing into isolated legalization/GRT/antenna/STA, then actual extraction if qualified, preserving50ps hold gate. No hardware/spec edit, phase tick or publication.
- SRAM DOUT0 trace: single existing wire9447 BUF4 sink; SPEF interconnect0.126627pF dominates reported0.130419pF. Prioritize moving existing buffer near macro before adding cells. Placement/routing evidence still needed; no area/timing benefit claimed yet.

## 2026-10-09: Codex (hold100 targeted setup and reserve investigation)
- Downloaded actual hold100 max/min/checks, states and final NL/SPEF/SDCs. Electrical slow/typ/fast slew132/37/4, fanout186each, cap6each. SRAM DOUT0 cap0.130419vs0.064pF and REN slew1.265403vs0.595200ns remain. All independent baseline six setup/hold metrics match CI within1e-6ns.
- Four strength changes give setupWS0allcorners at20ns with holdfast+0.053669680 unchanged, added library area21.7728µm². Removing NAND change fails−0.185588434. Two electrical strength additions retain setup0, reduce slow slew132→112, but cap/fanout remain. Four-cell reserve fails19.9ns; extras on old cone do not help.
- Traced limiting reserve path cfgword15bit4→tokenproducer tok[14]. NOR4_2 at38013 plus A21OI_2 at30044, in addition to four-cell set, pass allcorner setup at19.8ns with unchanged hold:200ps fixed-parasitic reserve. Missing NAND4_2 probe safely rejected; initial strict clock-match refused20.0000, corrected before reserve evidence. Report PHASE2_HOLD100_EXTRACTED_REPAIR.md records successful/negative controls and limits.23 helper checks/diff check pass. No physical reroute, official claim, phase tick, publication or pending local terminal.
- Next prepare guarded physical trial of measured six-strength set, address macro/fanout capacitance with buffering, and run exact-netlist GL. User-supplied git rule still applies; changes local. FIPE local only.

## 2026-10-09: Codex (hold100 extracted result receipt)
- Hold100 route37870374707 completes successfully in65min; both latest unit runs green, no main runs in progress. Two legacy main runs37655518919 GL/37655518925 extraction remain queued, unrelated to current hold100 continuation.
- Actual artifact11591942595 corner_summary: slow setup−0.522092606ns, fast/typ setup0; holdfast+0.053669681ns/typ+0.135278459ns/slow+0.291619737ns. Slow setup improves about0.902ns vs native125−1.423654124, but still fails; fast hold exceeds50ps gate by only3.67ps. No official promotion or phase tick.
- Selective download saved eight reports under/tmp/tripwire-completed-hold100-route; electrical counts not yet retrieved. Full log request stalled and was terminated after successful artifact/status retry. Next retrieve exact critical/electrical reports and target remaining522ps setup deficit without losing hold. All changes local.

## 2026-10-08: Codex (combined electrical/timing prototype checks)
- Hold10037870374707 still active at check. Twelve actual fixed-wire all-corner STA processes combine REN/functional driver sizing on native125 and prior six-cell timing prototype. Baselines match established metrics within1e-6ns; global timing unchanged. Six-cell-plus-two setupWS0 all corners, holdfast+0.094072364ns. Slew133/34/3→113/13/2; cap/fanout unchanged. Combined added library area25.4016µm²; no physical closure claimed.
- Tightened local native GL workflow to require frozen candidate3393eea;23 helper/workflow/electrical/extraction tests and diff check pass. Changes remain local under supplied git rule. Next hold100 extraction review, remaining buffer/load repair and physical qualification. No phase tick.

## 2026-10-08: Codex (parallel functional fanout probe)
- Main hold10037870374707 and unit37870419756/37870374880 still active; latest test/lint/docs green. Native125 fanout triage:164 clock-buffer-named violations,24 other drivers, no clock exemption inferred.
- Six all-corner extracted processes test only driver28820 NOR2_1→2. Baseline timing matches CI within1e-6ns; setup/hold unchanged. Slow slew133→113 and typ34→14, fast unchanged3; cap6/fanout188 unchanged every corner. Added library area3.6288µm². Exact driver slow slew failure disappears; load still exceeds capacitance limit. Report updated, raw logs/tmp; no physical improvement or closure claim.
- Next actual hold100 result, then targeted buffer/strength physical experiment using measured baseline. Changes local, no phase tick or publication.

## 2026-10-08: Codex (native routed GL preparation)
- Hold10037870374707 remains active. Prepared separate l3-native-routed-gl workflow using existing L3 suite/pinned Icarus13 and matching native route artifacts. Exact reviewed route IDs/SHAs/profile/source gates, DRT0DRC, config and netlist identity validated; returned hash labels functional evidence only.
-22 focused native-GL/electrical/extraction tests pass; YAML/wiring audit and diff check pass. Workflow/helper remain local and have not run protocol GL. No hardware edit, publication or phase tick. Next inspect hold100 extraction, review/publish prepared follow-up within authorization, then test its exact netlist.

## 2026-10-08: Codex (measured SRAM REN sizing probe)
- Hold10037870374707 remains in progress. Ran six actual extracted native125 STA processes; baseline setup/hold matches CI within1e-6ns. One NOR2B_1→2 driver change improves slow SRAM REN slew1.411568→0.722519ns, still above0.595200ns; removes fast/typ REN violations. Global setup/hold unchanged, cap/fanout failures unchanged. Cost+3.6288µm² library area; no physical reroute claim.
- Report records baseline/probe electrical counts and exact pin limits. Raw evidence stays /tmp/tripwire-native-ren-probe-37859526262. No source hardware change, phase tick, commit or push. Next actual hold100 result; buffering/remapping required for remaining slow REN slew.

## 2026-10-08: Codex (fresh extraction electrical evidence)
- Hold10037870374707 still runs route/extraction. Connected electrical audit to extraction output with fresh per-corner reports and row/printed-total agreement checks.11 audit/extraction regressions pass; actual saved native125 slow report still audits correctly. Changes local; current workflow uses earlier code.
- Pinned library confirms NOR2B_2 available, same footprint, +3.6288µm² over REN driver NOR2B_1. Traced shared driver branch through hold11848 to write-enable inverter, so any sizing probe must check both setup and hold. Recorded concrete target; no physical improvement claimed.
- Next inspect actual hold100 reports and choose one qualified electrical probe. No phase tick, commit or push; FIPE remains local.

## 2026-10-08: Codex (electrical report audit helper)
- Hold100 route37870374707 remains in route/extraction stage; no new extracted result. Added electrical_report.py to distinguish slew/fanout/capacitance violations and refuse missing/duplicate report sections. Diagnostic output explicitly denies official signoff.
- Five focused tests pass. Actual native125 slow checks report reproduces133 slew/188 fanout/6 capacitance rows, matching its printed totals. Fanout was absent from the earlier electrical summary; recorded here rather than implying slew/cap alone exhaust the failures. Raw JSON stays in/tmp.
- Changes remain local under latest supplied git rule. No hardware edit or phase tick. Next audit hold100 final electrical report and timing, then choose one physical correction.

## 2026-10-08: Codex (parallel SRAM electrical audit)
- Native hold100 route37870374707 remains running, now in fresh antenna/timing qualification→route/extraction. Latest test/lint/docs jobs green; two unit runs still active. No new physical result claimed.
- Traced native125 SRAM REN to mapped NOR2B driver29426; separated input-slew repair from macro-output fanout/capacitance buffering. Reviewed pinned stock electrical-repair Tcl and upstream resizer documentation; recorded exact failures, experiment order and extracted/GL gates in PHASE2_SRAM_ELECTRICAL_NEXT_STEPS.md. Official-prep old PNR masking still needs correction before adoption.
- No hardware, constraint, git history or remote edits; FIPE stays local. Next inspect hold100 extraction, then select one measured electrical correction. No phase tick.

## 2026-10-08: Codex (hold100 guarded routing continuation)
- Prepared native hold100 continuation for successful screen37866086829/head7b87718f0b28be7c5815cded40db05eb52c27be8. Exact source/workflow/100ps target registry, trusted hardware/full-config equality, fresh antenna cleanup/STA/50ps fast hold, DRT0DRC requirement and automatic extraction remain enforced. Stock125 profile unchanged; no named-cell ECO.
-72 helper checks pass, including full orchestration for both source profiles and refusal of mismatched targets, bad cleanup/timing and insufficient hold. Workflow static audit and diff check pass. Published23a9c53/bfd4e52/73a35ce; verified remote main73a35ce3d22d0b63f213078cdeddc5565f0c1d97. Launched hold100 route37870374707 on that exact SHA, running at receipt. Next inspect fresh antenna/STA and actual extraction; no phase tick or electrical readiness claim. FIPE remains local.

## 2026-10-08: Codex (hold100 completed screen audited)
- Hold100 screen37866086829 succeeds in42min; no active main workflows. SetupWS0allcorners, holdfast+0.100882ns/typ+0.204349ns/slow+0.382839ns. Actual artifact11589244417.
- Final cell area514025.08µm² inclSRAM vs stock125ps524688.31 (−10663.23µm²/~2.03%);33245cells vs33898. GRT39.56%/0overflow. Electrical still fails: slewslow18/typ1/fast1, cap1eachcorner. No routed/extracted improvement or official closure claimed.
- Initial status tool stalled; terminated after read-only retry. Report updated locally. Next guarded hold100 route/extraction to measure actual setup benefit, while addressing electrical constraints separately. No phase tick; best earlier timing checkpoint preserved.

## 2026-10-08: Codex (native exact-baseline probes and bounded clean recipe)
- Actual native NL/SPEF baseline six metrics match CI within1e-6ns.54 all-corner probes: seven strength changes improve slow−1.423654→−0.262711ns; replacing two SD3 hold cells with SD2 gives setupWS0 all corners, holdfast+0.094072364ns unchanged. Added library area29.0304µm²; no physical or official pass claimed.
- Mapped dropped endpoint47345 and RX rt[23] endpoint46391; improving one branch moves the bottleneck. Prepared independent clean-build AREA1 hold100ps screen changing one repair option vs125ps, keeping clock/uncertainty/hardware/density fixed; acceptance gates remain unchanged.
-54 helper checks pass including actual hold-target propagation/default preservation and workflow audit.30 additional minimization processes reduce the fixed-wire set to six changes, setup0allcorners and holdfast+0.094072364ns, area+18.144µm². Total84 local STA processes. Earlier checkpoint electrical audit finds slewslow91/typ3/fast1 and capslow6/typ7/fast7: timing pass is not full electrical closure. User explicitly approves grouped commit/push/hold100 dispatch. Initial combined command stalled before any mutation; terminated and verified unchanged history before sequential retry. Published122e1b9/c819534/7b87718, verified remote main7b87718f0b28be7c5815cded40db05eb52c27be8. Hold100 screen37866086829 running on that exact SHA at receipt. No phase tick.

## 2026-10-08: Codex (native completed results audited)
- Verified native route37859526262 and electrical cleanup37858535440 complete successfully as workflows; no active main runs. Actual native extracted slow setup−1.423654124ns fails; holdfast+0.094072364ns/typ+0.196308975ns/slow+0.370721020ns. Slow electrical133slew/6cap. No promotion or official launch.
- Cleanup screen clears cap counts all corners but slewslow18/fast1/typ1 remain; setup0allcorners, holdfast+0.104755ns, finalGRT0overflow/39.76%, area524416.15µm² inclSRAM. Not yet routed/extracted.
- Retrieved actual slow critical path: live unit0configword0bit4→pin feedback→endpoint47345; loaded7221 BUF/24875 O21AI/24876 INV contribute0.899/1.159/0.721ns arcs. Best residual checkpoint remains extracted0/+0.062789ns and22/22 GL; do not replace with weaker native result. Report PHASE2_NATIVE_EXTRACTED_RESULTS.md records exact distinctions. No phase tick. Next independent extracted-baseline probes or qualified alternative clean-build recipe; raw reports outsidegit.

## 2026-10-08: Codex (native route antenna gate failure fixed)
- Run37858532319 fails safely before DRT: fresh setupWS0/holdfast+0.119326ns, but post-timing antenna15nets/17pins. Exact fresh artifact11584854275 confirms; source provenance/config/STA all pass. Electrical cleanup37858535440 remains active.
- Added conditional stock antenna cleanup with congestion disallowed and audited resolved config/repair command. Preserve repaired guides; proposed full reroute rejected locally after reviewing BUG79, before publication. Fresh CheckAntennas and STA use cleaned ODB; remaining antennas, timing or50ps hold failure still refuse DRT.
-51 helper regressions pass; diff check passes. BUG82 records cause and coverage. Published d9af592/c2d7c8b to remote main. Relaunched native route37859526262 on c2d7c8b1094edd4551cc6078ece502a2758c7255, running at receipt; cleanup37858535440 still active. Next inspect fresh cleanup/STA gates and actual DRT/extraction. No hardware/template edit, relaxed gate or phase tick.

## 2026-10-08: Codex (native physical audit and guarded continuation ready)
- Audited exact native37853023857 artifacts: both setupWS0; AREA1 holdfast+0.119326ns, area524688.31µm² inclSRAM, GRT39.76%/0overflow vs AREA0+0.074614ns/524994.94µm²/40.21%/0overflow.
- Found unresolved fresh electrical failures: AREA1 slow slew21 vs AREA0 3; both cap1 each corner. AREA1 SRAM A_REN0.996394ns vs0.595200ns, A_DOUT[0]0.070544pF vs0.064pF, loaded28820 cone about2.556ns vs2.5074ns. No official closure/adoption claim.
- Prepared exact-source AREA1 route→extraction continuation with trusted pre-download hardware/full-config equality, fresh antenna/STA/50ps hold gates and no repeated repair. Prepared independent AREA1 stock post-GRT design-repair screen targeting electrical failures.37 regressions and both workflow/static/diff checks pass. Phase summary updated, no phase ticks. User explicitly approves publication and both dispatches. Published757c521/d301904/9e2d550, verified remote main9e2d55059552b49a9c49d09732f777647cd8f5d6. Native route37858532319 running and electrical cleanup37858535440 queued at receipt, both pinned to that SHA. Next route/extract measured clean build and compare electrical cleanup; protocol GL follows actual final netlist. FIPE stays local.

## 2026-10-08: Codex (measured extracted timing reserve)
- Ran21 local all-corner fixed-parasitic STA processes on actual residual extraction37844735445; all six20ns baseline metrics match CI within1e-6ns. Fully timed constraints, no cell/port/uncertainty/derate changes; only clock period varied.
- All corners remain nonnegative setup at19.90/19.85ns, positive hold unchanged minimum+0.062788613ns. Slow fails19.75ns with−0.099644743ns. Former worst endpoint47775 is+0.150356174ns at20ns; globalWS0 reflects time-borrowing latch reports. Measured150ps period reserve, not official closure or per-path universal margin.
- Report PHASE2_EXTRACTED_TIMING_MARGIN.md records evidence/limits. Native stock37853023857 and unit37853058366 remain running; no new physical launch, phase tick or hardware/config edit. Next native clean-build result and matched DRT/extraction if qualified. Raw evidence in/tmp, FIPE local.

## 2026-10-08: Codex (extracted closure and stock reproduction preparation)
- Residual DRT37837038264 succeeds; extraction37844735445 setupWS0 all corners, hold fast+0.062788609ns/slow+0.315522950ns/typ+0.157048712ns. GL37844735520 passes22/22, no skips. No official closure or phase tick.
- Found pinned Classic post-GRT timing repair defaults disabled despite appearing in its step list. Prepared separate clean-build stock-sequence AREA0/AREA1 workflow and helper, explicitly enabling repair/all-corner resizer/125ps hold target with fully timed constraints. No checkpoint ECO, repeated repair or main hardware/template edits.
-16 native helper regressions pass (configuration guards, actual orchestration and no repeated repair), diff check passes. User explicitly approves grouped commit/push/dispatch commands. Published47dbb2d/55e62e9/a53dd57; verified remote main equals a53dd57b44438d2a10f3363e1418d489a175397e. Dispatched native stock37853023857 on that exact SHA, queued at receipt. Next inspect native stock gates before DRT/extraction. FIPE remains local.

## 2026-10-08: Codex (qualified residual DRT continuation)
- User requests continued work/manual launch. Published tools5ee1fcf, workflow8e5f6cd and earlier screen receipt30f9dd1. Added exact residual source37834700367: successful main provenance, full prior driver/hold/NOR chain plus exact3-cell audit, strict routing/antenna evidence and fresh all-corner STA/50ps hold gate. No repair repeated; existing DRT refused.
-84 routing tests pass including21 new residual checks. Static artifact-selection audit initially selected the wrong download step and failed; corrected explicit step-name selection passes. No implementation change needed. Shell publication proceeded after that audit failure; recorded and corrected before dispatch.
- Launched DRT37837038264 on verified published b877c2addf8c645c83dd3a047286b2b7fdf4175e, in_progress at receipt: original37533969613/bs-event-late, repaired37834700367, source hold target/no repeated repair. Routine CI active including older unit37834754490/37834675410. No hardware/config/template edit or phase tick. Next inspect final DRC, downstream extraction and routed GL; official clean-build reproduction remains required.

## 2026-10-08: Codex (residual screen qualifies)
- Screen37834700367 succeeds: fresh setupWS0 all corners; hold fast+0.113342ns/slow+0.418904ns/typ+0.226324ns; antenna nets/pins0/0, ready_for_route_review true and unchanged50ps hold gate passes. This is GRT evidence, not detailed-route/extracted/official closure.
- Two latest unit workflows37834754490/37834675410 remain running. Legacy37655518919 GL and37655518925 extraction remain queued. No residual DRT launched yet; next prepare guarded exact-source continuation preserving full three-cell/prior repair history, then extraction and protocol GL if DRT qualifies. No phase ticks.

## 2026-10-08: Codex (approved residual-screen publication)
- User explicitly approves the scoped commit/push/dispatch commands, overriding the latest git restriction for these groups. Reviewed diff checks and outgoing hardware history (none); no main source/config/macro edit. FIPE, comparison helper and unused hold prototypes excluded.
- Published tools e85bcb2, workflow9811a40 and evidence df46fa3 to remote main; verified remote SHA df46fa3a58547ed6ab849d0372d4bb1789d1e02c. Launched residual setup screen37834700367 on that exact SHA, in_progress at receipt, from qualified driver37818177484. Actual routed/extracted improvements remain unproven; no phase tick. Next: verify screen source/antenna/hold gates, then guarded DRT/extraction only if qualified.

## 2026-10-08: Codex (residual two-branch prototype ready)
-24 new all-corner fixed-wire probes: exact place6860 BUF2 +44061 A21OI2 +27962 NOR4_2 gives setupWS0 all corners;9 previous failing endpoints slow+0.098701492..+0.731180489ns. Worst hold unchanged fast+0.067579724ns. Cost18.144µm² library area; no state/connectivity changes; physical improvement unproven.
- Prepared guarded three-cell screen from successful37818177484, complete inherited history, powered/exact-change audit, strict routing/antenna evidence and unchanged50ps fast hold gate. Actual extracted NL rehearsal passes;120 targeted regressions pass with real cached Tcl runtime (physical APIs mocked), workflow/source audit and shell/diff checks pass.
- New files and recent audit/comparison docs remain local. Latest supplied AGENTS.md explicitly prohibits Codex git commits/pushes, so no publication/dispatch claimed; user scoped commands are needed. FIPE and unused prototypes excluded. Next: publish/run screen, then fresh physical/extracted/protocol qualification only if gates pass. No phase tick.

## 2026-10-08: Codex (27 fresh extracted-baseline sizing measurements)
- Retrieved exact driver NL/SPEF and ran27 fixed-wire all-corner STA probes; baseline all six metrics match CI within1e-6ns, missing masters/errors rejected. Best place6860 BUF1→2 reduces slowWS−0.147084132→−0.020914827ns; worst hold unchanged+0.067579724ns. NOR4-only gives−0.039319661ns.
- Larger BUF4 and NOR4+BUF2 pair add no global benefit; residual endpoint47981 now worst and47775 remains−0.009077184ns. Report updated; no timing closure/promotion or new physical launch. Next inspect residual branch before a guarded minimal physical repair. Diff check passes.

## 2026-10-08: Codex (driver routed protocols pass; active runs finish)
- At19:36UTC driver routedGL37825505461 succeeds:22 tests/22 pass/0 fail/0 skip. Main has no in-progress workflows; legacy37655518919 GL and37655518925 extraction remain queued. Latest driver routing/extraction/native screens and unit/lint/test/docs completed.
- Diagnostic workflow success is not timing closure: driver extracted slow setup−0.147084ns, fast hold+0.067580ns. No phase tick. Next: exact fresh critical-cone probes and native hold/full-flow reproduction; no official GDS currently active.

## 2026-10-08: Codex (19:07 UTC workflow check)
- Verified latest main runs: only driver routedGL37825505461 remains active, expanded L3 (~31min elapsed). Driver route/extraction, native mapping and latest unit/lint/test/docs completed successfully as workflows; extracted slow setup remains−0.147084ns and does not pass timing.
- Initial status request stalled; direct bounded retry and run-list check succeeded. No new result, launch, hardware change or phase tick. Next: driver GL result and fresh critical-cone probes.

## 2026-10-08: Codex (fresh critical cone and native physical evidence)
- Retrieved selected slow max report from exact extraction37825505569/artifact11570759230. Nine failures now begin48909/unit0 cfg word1 bit1; worst47775−0.147084ns. Dominant25443 O21AI1/25445 XOR2_1 loaded arcs have1.25/1.42ns delays; pinned library lacks stronger versions. Documented supported NOR4/upstream/load-splitting probes, pending exact-net/all-corner rehearsal.
- Native final repair GRT tables have zero overflow for both jobs. AREA0 final cell-type total510004.37µm²/33191 cells; AREA1 506758.41µm²/32768, about0.636% less reported area. Neither meets50ps fast hold continuation margin; no promotion or phase tick.
- Report updated with exact evidence and distinction between moved bottleneck and quantified positive margins. Static diff check passes. Next: exact current-baseline fixed-wire probes and matched native hold/full-flow recipe; driver GL remains dependency.

## 2026-10-08: Codex (driver extracted improvement; native results)
- Driver route37819598187 completes successfully; extraction37825505569 reports setup fast/typ0, slow−0.14708412681900332ns. Hold fast+0.06757972150942818ns/slow+0.34680981290632085ns/typ+0.1754376693575883ns. New best measured extracted setup, still failing; no official closure.
- Native37819169130 completes diagnostically: AREA0 setupWS0 all corners but fast hold−0.00416389ns; AREA1 setupWS0 all corners, fast hold+0.0404413ns (below50ps continuation margin), slow+0.220399ns/typ+0.118338ns. Neither qualifies automatic promotion; area/overflow audit pending.
- Prior hold routedGL37815131566 passes22/22, zero skips. Only active main workflow is new driver routedGL37825505461, expanded L3 started18:35:50UTC. Latest unit/lint/test/docs complete green. Initial GH request stalls; bounded API retry succeeds.
- Next: inspect fresh driver slow critical reports and native area/overflow evidence before selecting follow-up; await exact driver routedGL. No phase ticks.

## 2026-10-08: Codex (18:08 UTC workflow ETA snapshot)
- Verified six active main runs: driver37819598187 pre-DRT antenna/fresh timing (~18min elapsed); native37819169130 both GRT/timing (~21min); routedGL37815131566 expanded L3 (~53min); unit37818162329/37819155058/37819814438 chip-level RTL (~29/21/16min). Other unit jobs complete.
- Remaining estimates, not deadlines: driver45–75min, native20–60min per parallel job, routedGL10–25min, units respectively5–20/10–30/15–35min. Detailed-route downstream extraction remains a later dependency; no official GDS active. No new result or phase tick.

## 2026-10-08: Codex (parallel native-result comparison helper)
- Prepared compare_native_timing.py for downloaded AREA0/AREA1 artifacts: requires expected native manifest, all three corners, finite setup/hold slack and identical referenced constraint bytes. Prints per-corner differences while explicitly marking non-extracted/non-official evidence; does not select/promote a winner or claim area/overflow qualification.
- Five regressions pass, including missing corner, custom-image manifest, mismatched constraints and NaN rejection. Diff check passes. Helper/tests remain local; existing native/driver runs still active at check. No hardware/config change, workflow launch or phase tick.
- Next: use completed artifact evidence to compare timing, separately inspect full-chip area/overflow/antenna metrics and exact provenance before selecting a matched full-flow follow-up.

## 2026-10-08: Codex (native repair ordering resolved)
- Inspected pinned LibreLane3.1.0.dev3 Classic ordering and post-GRT repair implementation. Stock official flow already invokes native repair, but after design/antenna repair; current screen resumes directly from initial GRT. Documented why input checkpoints and globally changing RSZ_CORNERS are not equivalent.
- Main workflow check: driver37819598187 active in antenna/fresh timing preflight; native37819169130 both jobs active in GRT/timing; routedGL37815131566 active in expanded L3. Latest lint/test/docs pass, unit runs active. No finished new physical result, launch or phase tick.
- Static audit and git diff check pass. Next: inspect native matched results and exact post-antenna stock-flow repair before accepting official reproducibility; inspect driver extracted timing when downstream run completes.

## 2026-10-08: Codex (parallel official-recipe audit)
- Audited isolated full2/4 official preparation against running native screens. Found older PNR SDC retains latch setup exceptions; current screen uses fully timed signoff constraints throughout. Recorded exact config differences and the unresolved separate all-corner repair sequence in PHASE2_NATIVE_OFFICIAL_RECIPE_AUDIT.md.
- Checked main: native37819169130 AREA0/AREA1 both running GRT/fresh timing; driver DRT37819598187 checking antennas/fresh timing before DRT. Latest lint/test/docs green; unit runs active. No new physical launch, hardware/config change or phase tick.
- Validation: inspected config/SDC/helper/workflow inputs; git diff check. Next: compare finished native full-chip area/overflow/timing, inspect driver extraction and routed GL; require a reproducible matched official recipe before promotion.

## 2026-10-08: Codex (driver repair qualifies; detailed routing continues)
- Driver37818177484 succeeds: all-corner setup WS0/zero timing violations, fast hold+0.0717144ns/slow+0.336162ns/typ+0.168788ns, antennas0/0. Gate remains50ps; positive fixed-wire gains are not declared extracted closure.
- Launched guarded DRT37819598187 on97e6f84 from exact successful driver screen; original37533969613/bs-event-late, no repeated sizing or hold repair. In_progress at confirmation. Native mapping37819169130 AREA0/AREA1 jobs are independently running through stock GRT/STA; routedGL37815131566 still active.
- In-progress Phase2 summary refreshed with rejected banked/extracted regressions and current driver/native work. All394 selected helper checks execute/pass; diff checks pass. No phase ticks, no main hardware/config/template edits.
- Next: inspect DRT/extraction/GL and native full-chip area/overflow/all-corner measurements, then select clean official-flow reproduction based on actual results. Original−0.179789ns remains best extracted setup baseline.

## 2026-10-08: Codex (native full-design comparison running; all helper checks execute)
- Published3156476 conditional driver continuation,d78fc03 native helper,3440eb4 workflows and97e6f84 evidence to remote main. Launched stock-image native mapping37819169130: matched AREA0/AREA1 full2/4 event-late, no regional wrapper or checkpoint ECO. Main RTL/config and official jobs unchanged.
- AREA1 local module40393.6092→40144.3938µm² and13.142539→12.479320ns targeted ideal-wire delay supports this comparison; no full-chip gain claimed. D-080 records scope/cost/adoption limits.
-394 related tests pass with zero skips using an isolated argument-preserving cached-STA Tcl shim; no system packages installed. Driver37818177484 measurement step succeeds, upload active; routedGL37815131566 still running. No phase ticks.
- Next: verify completed driver gates/metrics, launch prepared DRT if qualified, inspect native all-corner/area/overflow comparison and protocol GL. Continue toward extracted and official closure without changing the timing contract.

## 2026-10-08: Codex (driver screen launched; clean-build mapping explored)
- Published99c69d7 driver guards,9ef5d1c effective-constraint evidence,663b341 workflow andccddb80 research to remote main. Launched37818177484 with antenna repair; provenance passes and pinned image builds at check. RoutedGL37815131566 remains active.
- Prepared local exact-driver-screen DRT continuation;83 continuation tests pass. It rejects unsuccessful/incomplete source and audits every prior repair plus fresh STA; no DRT launched from pending screen.
- Pinned-wheel ABC script mapping on event-late BITSYNC: DELAY0 area43678.6182µm²/slow PERIOD→rx_load12.122954ns, DELAY1 area44772.5502µm²/delay10.994252ns. About2.5% module area for1.129ns ideal-wire improvement. Native sizing adds no change at20ns. Source/state/clock unchanged; full-chip/container/physical effect unproven.
- No phase ticks or main hardware/config changes. Next: finish mapping controls and driver measurement, then DRT/extraction/GL only if qualified; select separate clean-build mapping trial from measured evidence.

## 2026-10-08: Codex (closure research and audited upstream-driver trial)
- Reviewed current extracted8-path cone, architecture/D-066, rejected RTL experiments, official portability and primary OpenROAD/LibreLane/Yosys/TinyTapeout sources. Report PHASE2_CLOSURE_RESEARCH.md records ranked actions and limits.
-24 current-checkpoint fixed-wire STA measurements reproduce six CI baseline values within1e-6ns.38386 A21OI1→2 removes printed slow setup failures; formerly failing endpoints+0.085912..+0.498670ns, unchanged fast hold+0.109290ns. Single-driver added library area5.4432µm². Inverter-only alternatives remain negative; larger inverter8 is worse than4. No physical improvement claimed.
- Prepared guarded driver screen from37806209914: exact single-master/pin audit, all prior repairs preserved, fresh zero-overflow GRT/strict antennas/all-corner STA and50ps hold gate. Actual source-NL rehearsal passes;336 related tests pass/8 wrapper skips, four extraction checks pass.
- BUG81: inherited artifact SDC masks latch setup paths; baseline assertion rejected invalid positive replay. Fully timed replay matches actual diagnostic. Future extraction exports and uses exact effective signoff SDC with SHA256 identity.
- No phase ticks or official source/config edits. Next: publish/run one-driver physical screen, inspect routedGL, then conditional DRT/extraction from qualifying evidence. Keep original−0.179789ns extracted baseline until beaten physically.

## 2026-10-08: Codex (extracted hold improves; setup remains failing)
- Extraction37815131590 succeeds as diagnostic, not timing closure. Slow setup−0.6039080517705893ns; fast/typ setup0. Hold fast+0.10929035763504281ns/slow+0.38645998606225973ns/typ+0.21145952254413386ns. Reject promotion; original−0.179789ns remains best extracted baseline.
- Downloaded selected slow reports by byte ranges from artifact11565909997.8 printed negative paths start at config latch48905 and end at48112–48119; worst48115 uses the separate38386/38387 branch. No unsupported claim attributing regression to one edit.
- RoutedGL37815131566 remains in expanded L3 simulation. No phase ticks. Next: current-checkpoint fixed-wire branch probes and routed protocol result, then separately controlled physical repair only if supported.

## 2026-10-08: Codex (hold-qualified routing completes cleanly)
- Routing37807978035 succeeded in55 minutes. Completed OpenROAD log confirms final detailed-route violations0 and antenna nets/pins0/0; this is not full signoff.
- Automatically launched extraction37815131590 and routedGL37815131566 at17:15 UTC; both in_progress at17:15:47, dependency installation/artifact download respectively. Current extracted setup/hold and routed protocol results remain pending.
- Latest test/lint/docs/unit all green. No phase checklist ticks. Next: inspect fresh extracted all-corner results and routed22-case protocol suite; preserve stronger prior baseline until actual evidence supports promotion.

## 2026-10-08: Codex (workflow ETA snapshot at16:22 UTC)
- Checked main: routing37807978035 building pinned image; five unit runs37808033530/37807950696/37806394870/37806176506/37803254216 active in chip-level RTL. Latest lint/test/docs green; bounded hold screen37806209914 succeeded.
- Older37655518919 routedGL and37655518925 extracted timing still queued; no reliable queue ETA. Current routing ETA roughly55–90 minutes remaining, based on prior58-minute route and runner variation; unit ETA roughly20–35 minutes for newest runs,10–25 for14–16-minute runs,5–20 for oldest38-minute run. Estimates, not measured deadlines.
- No phase ticks or new launch. Next: inspect routing qualification/final DRC and downstream extracted timing/GL; investigate oldest unit if it continues beyond comparable runtimes.

## 2026-10-08: Codex (approved hold-qualified detailed routing launched)
- User explicitly approved publishing and launch. Committed tools/tests450d29a, workflowfa6101a and evidence89d7537; pushed and verified remote main equals89d7537856b8e3b1de0742ea4884aa3fd9fcce1f. FIPE and unused local prototypes remain untracked.
- Launched [37807978035](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37807978035), queued at receipt: original source37533969613/bs-event-late, repaired source37806209914, pre-route hold target source, no repeated post-antenna hold repair. Source screen succeeded with fast hold+0.109256ns, all-corner setup WS0 and zero timing/antenna violations.
-62 continuation regressions pass after final edits; prior broader311 pass/8 skip and diff checks recorded. No hardware source, official config or phase checklist change.
- Next: monitor exact-source qualification and DRT final DRC; inspect downstream extracted timing and routed GL before promotion. Official clean-build portability remains unresolved.

## 2026-10-08: Codex (nine-leaf hold screen qualifies; DRT continuation prepared)
- Screen37806209914 succeeded in9.5 minutes. Matched artifact11563058526: all-corner setup WS0, zero setup/hold violations, hold fast+0.109256ns/slow+0.371234ns/typ+0.202929ns; antennas0/0. Fast hold exceeds unchanged50ps gate.
- Prepared local exact-source continuation with complete netlist-transition audit, trusted fingerprints, strict routing/antenna evidence and fresh STA before DRT. Workflow preserves inherited setup/hold evidence and uses ordinary routing image without repeated repairs.
-311 related helper tests pass;8 system-tclsh wrapper tests skip. Cached STA Tcl guards execute; physical operations in tests are mocked. Diff check passes. Evidence in PHASE2_DROP_LEAF_HOLD.md.
- No phase ticks or official closure claim. Changes remain local: latest supplied AGENTS.md reserves commits/pushes for user. Next: publish continuation, DRT, extracted all-corner timing and routed GL; then resolve clean official-flow reproduction.

## 2026-10-08: Codex (moved hold bottleneck audited; nine-leaf screen ready)
- Published78ca427 tools,b2652a1 workflow,61ac267 evidence to remote main. Launched [37806209914](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37806209914) on61ac267; in_progress at confirmation. Antenna repair enabled; no DRT or setup/inverter changes.
- Finished screen37803300460 passes setup/hold counts and antennas0/0; setupWS0, hold fast+0.033514ns/slow+0.352956ns/typ+0.159913ns. Fast hold is below50ps DRT gate; no threshold relaxed.
- Byte-range artifact11563320092 audit identifies9 distinct printed endpoints below50ps, headed by lane0.ex_imm[3], not prior state[2]. Old one-leaf prototype remains local/unlaunched. Actual fresh NL confirms9 separate single-driver/single-sink D nets.
- Prepared bounded9-BUF1 hold screen from exact37803300460. Preflight all branches before mutation; preserve all other logic and clock/reset; require zero-overflow routing, strict antenna repair and fresh all-corner timing with50ps margin. Added library area65.3184µm², not final routed area.
-289 related tests and actual checkpoint netlist rehearsal pass; shell syntax/diff checks pass. No phase ticks or official promotion. Next: publish/run bounded hold screen, then use qualified evidence for DRT/extraction/GL.

## 2026-10-08: Codex (parallel one-leaf hold prototype tested)
- Prepared local guarded BUF1 insertion at lane0 state[2] D and independent exact netlist-change validator. Pinned buffer is noninverting, area7.2576µm²; actual extracted-NL rehearsal passes. Clock/reset/other logic remain unchanged by the permitted edit.
-16 targeted guard tests and279 related helpers pass; diff check passes. No actual physical hold repair or numerical improvement claimed; existing+5.298629284ns destination slow setup headroom supports a future trial.
- Screen37803300460 measurement step now passes; artifact upload is active at check, final conclusion/metrics pending. Local prototype/report remain unpublished; no phase ticks.
- Next: inspect finished setup screen metrics, select a setup-qualified checkpoint for a separate one-cell hold trial, then require fresh physical extraction and all-corner evidence.

## 2026-10-08: Codex (parallel hold and portability audit)
- Running drop-event screen37803300460 passed setup/source validation and is building its image at check. Independent extraction hold audit finds1/1000 printed fast paths below50ps,37 below100ps; weakest is lane0 slot latch50100→state[2] register46479 at+0.035871ns.
- Reviewed cached pinned official action/support-tools/LibreLane code: ordinary merged-config clean build, no arbitrary post-placement sizing hook found; native resizer controls available, custom diagnostic images/checkpoints not automatically portable.
- Report PHASE2_PARALLEL_HOLD_AND_PORTABILITY.md records targeted leaf-delay option, distinction between50ps and100ps repair scope, native clean-flow reproduction and separate inverter follow-up. No hardware changes or phase ticks. Local exact extracted STA measures+5.298629284ns slow setup headroom at46479/D, supporting a small leaf-delay experiment without proving its physical result.
- Next: inspect destination setup headroom and current physical screen result; preserve original baseline until extracted evidence improves.

## 2026-10-08: Codex (extracted dropped-event bottleneck isolated)
- Published a12aeb5 tools,4bc3fd3 workflow,5b13ebe evidence to remote main.263 helper tests pass. Dispatched [37803300460](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37803300460), queued at confirmation; one31567 NOR2 change, antenna repair enabled, no DRT.
- Downloaded extracted artifact11535321738 from37743628998.9 printed negative slow paths terminate at dropped counters;31567 NOR2 delay2.300487ns dominates the worst branch. Prior RX timer is no longer worst.
- Local independent STA reproduces all-corner CI baseline within1e-6ns.31567 strength1→2 gives slow WNS-0.004851231ns; plus38387 inverter strength1→2 yields0 reported WNS/no printed setup failures and preserves fast hold+0.035871472ns. Combined cell-area increment5.4432µm²; fixed-wire evidence only.
- Discarded nonexistent upstream o21ai_2/xor2_2 black-box probes (BUG80). Prepared guarded single-cell physical screen from qualified37736921949; inverter remains a separate experiment. No RTL/config/official source changes or phase ticks.
- Next: measure the single NOR2 physical screen, then select separate inverter follow-up or DRT only from qualified measured evidence. Official portability remains unresolved.

## 2026-10-08: Codex (NOR2 extracted result regresses setup)
- DRT37737970080 succeeded in58 minutes, final DRT violations0 and final antenna nets/pins0. RoutedGL37743629089 passes22/22. Extraction diagnostic37743628998 succeeds as a reporting workflow but slow setup fails at-0.4220854896178046ns.
- Extracted hold: fast+0.03587147347360706ns, slow+0.3196811794654476ns, typical+0.13442103366429453ns; fast/typ setup WS0. Previous original event-late extracted slow setup-0.17978863351414795ns remains the stronger baseline.
- No active main workflows at check; older37655518919 routedGL and37655518925 extraction remain queued. Latest lint/test/unit/docs/nightly green.
- No checklist ticks or official promotion. Next: inspect extracted slow paths to distinguish remaining event feedback from route-induced/new critical paths before selecting another narrowly targeted repair; preserve the original baseline and all protocol behavior.

## 2026-10-08: Codex (NOR2 detailed-routing continuation launched)
- Published continuation448f423, workflow24343bf and readiness564f7c6 to remote main.240 related helper tests pass; diff checks pass. No source, macro, info or official configuration changed.
- Launched [37737970080](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37737970080) on564f7c6: source37533969613, bs-event-late, repaired checkpoint37736921949, no repeated hold repair or sizing. GitHub confirms in_progress. Fresh all-corner STA/50ps fast hold and saved antenna/provenance gates precede DRT.
- No phase checklist tick. Next: inspect DRT final DRC, then extracted timing and routed GL; official clean-build portability remains unresolved. FIPE and unused SRAM prototypes remain local-only.

## 2026-10-08: Codex (antenna-clean NOR2 screen succeeds)
- Screen37736921949 on d150bb7 succeeded. Final antennas0 nets/0 pins; all-corner setup WS0 and no setup/hold violations. Hold fast+0.0932422ns, slow+0.393571ns, typical+0.212009ns. Repair adds36 diodes;34189 cells, instance area524911.48µm².
- Successful source meets local continuation's50ps fast-hold gate. Updated prepared continuation to this exact run; prior failed runs remain rejected.240 helper tests pass. Continuation remains local/unpublished; no DRT launched.
- No phase tick: GRT estimates do not establish extracted timing or official signoff. Next: publish/launch guarded DRT continuation, then extracted timing and routed GL; resolve official clean-build portability.

## 2026-10-08: Codex (pinpoint and fix antenna audit regression)
- Failed screen37735461986 actually passes all-corner timing but fails47 antenna nets/52 pins. Repair itself reaches0 violations; the full audit reroute added afterward recreates them (BUG79).
- Removed full audit reroute; antenna configuration disallows congestion, wrapper asserts policy before/after repair and records completion, runner checks evidence and retains independent antennas/netlist/STA gates.
- Evidence:240 helper tests pass; shell syntax/diff checks pass. User explicitly authorized corrective commits and push. Only screen tools/tests and evidence groups selected; DRT preparation and FIPE remain local.
- No checklist ticks. Next: rerun corrected antenna screen and inspect actual final antenna/timing metrics before DRT qualification.

## 2026-10-08: Codex (parallel continuation provenance hardening)
- User-approved screen/tool and documentation commits c709085/44c2bc7 were pushed to remote main. Corrected antenna screen37735461986 launched and is building its pinned image after source/PDK setup passed.
- Updated local DRT preparation from failed37733684248 to corrected37735461986. Strengthened shared congestion validation: require one audit marker and a complete zero-overflow report after it; reject stale preceding reports and ambiguous/missing markers.
- Evidence:240 related helper tests pass; git diff --check passes. New hardening/continuation edits remain local; active screen uses44c2bc7. No DRT, official workflow or phase checklist tick.
- Next: inspect corrected physical antenna/timing result; publish continuation only with a qualifying successful source, then measure detailed routing, extracted timing and routed GL.

## 2026-10-08: Codex (NOR2 antenna overflow-report correction)
- Checked main: two unit runs active; older extracted-timing and routed-GL runs queued. Latest NOR2 screen37733684248 failed after diode repair because incremental routing omitted the full congestion table; fresh post-repair STA did not run.
- Fixed BUG78 locally: explicitly reroute after diode repair before parasitic estimation/export, then require the full zero-overflow report, independent antennas and all-corner STA. Wrapper rejects missing/duplicate insertion points. Physical rerouting may expose new antenna failures; no gate relaxed.
- Evidence:239 related helper tests passed; bash syntax and git diff checks passed. No checklist boxes ticked. No DRT or official workflow launched.
- Latest user-provided AGENTS.md reserves Git history/remote changes for the user. Next: user publishes the exact screen/tools/docs groups and dispatches repair_antennas=true; evaluate that physical result before any DRT promotion. Local DRT preparation, FIPE and old SRAM prototypes stay excluded.

## 2026-10-08: Codex (parallel NOR2 route orchestration reviewed)
- Antennafollow-up37733684248 is measuring; nofailstepatcheck. Main/originmatchcdeedba; localchanges are deliberatecontinuation/tools/workflowtests pluslaunchreceipt, notfailedpush. FIPE/oldSRAMprototypesremainexcluded.
-239relatedtests pass, including end-to-end repairedview/ordinaryimage/DRT-only selection andfreshSTAnegative refusal. Report PHASE2_NOR2_ROUTE_READINESS.md makeslocalcontinuation reviewable; nopublication/DRTlaunchyet.
- ActualGRTinstancearea baseline524712→NOR2524716µm², count34153unchanged; utilization0.581452→0.581456. Areaestimatehistorical remains distinct fromfinalcandidatequalification.
- No phase tick ormainhardware/configchange. Next: auditactualantenna-clean screenresult; thenpublishreviewedcontinuation ifqualified, measureDRT/extraction/GL, resolvecleanofficialportability andfullsignoff.

## 2026-10-08: Codex (NOR2 timing passes GRT; antenna cleanup prepared)
- Published3a9ea54 tools,c4e039e workflow,cdeedba evidence toremote main; antenna-enabledscreen [37733684248](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37733684248) is inprogress oncdeedbaf15e116d8538bc4b6b0a0e232aca8f009. NoDRT. Localcontinuationnowtargetsitsfreshantenna-repairedviews andchecks bothroutingpasses; publicationstillawaitsqualification.
- Correctedscreen37732392933 physicallyresizes/legalizes/reroutes andpassesstrictnetlistguard/zerooverflow. Independentartifact11530157875: setupWS0/allcornercounts0; holdfast/slow/typ +0.0932422/+0.393552/+0.211997ns. Finalgatefails42antennanets/45pins; noDRT/extractedclosureclaim.
- Prepared explicitrepair_antennas option(defaultfalse), oneboundedstandardrepair plusfreshchecks, no timingresizer/DRT. FreshrepairedNL/PNL promoted; onlyaddedantennanpdiodes onexistingnets allowed,originallogicunchanged.237helperspass; report PHASE2_NOR2_ANTENNA_FOLLOWUP.md.
- Paralleloriginaleventofficialprep in `/tmp/tripwire-event-nor2-official-prep-20261008`: generator/static19sources pass,125psnativeproposalunapplied. LocalNOR2routeworkflowintegrationtested butexcludedfromscreenpublication pendingqualification.
- Publishingnecessaryantennafollow-up withinapprovedrepair-onlyscope. No mainhardware/config/templatechange orphase tick. Next: cleanantenna/timingcheckpoint,thenDRT/extraction/GL andcleanofficialreproduction.

## 2026-10-08: Codex (NOR2 source antenna-view guard corrected)
- Published3aab4c3 tools and99fb65f docs toremote main; correctedscreen [37732392933](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37732392933) is inprogress on99fb65f778cd159fed38f7240c583dde4118eb93. NoDRT.
- Screen37730917594 fails guard after successfulNOR2swap/legalization/zerooverflowGRT, beforeSTA. Artifact11529811539 independently shows92existingantennanp cells materialized innewNL,0removedcells andexactly1intendedmasterchange. No timingverdict inferred; BUG77logged.
- Fix exports actualsourceODB baselineNL beforemutation; validates inheriteddifference exactly92antennacells/unchangedlogic, thenstrictone-master-onlyECO comparison.234helpers pass; realartifactregression and Bash/diffchecks pass. Localcontinuation updated butexcludedfrompublication.
- Proceeding with necessarycorrective tools/docs publication andscreenrelaunch withinapprovedrepair-only scope. NoDRT/mainhardware/configchange orphase tick. Next: actualcorrectedGRT/antenna/allcornerSTA results.

## 2026-10-08: Codex (NOR2 measurement active; continuation prepared locally)
- Screen37730917594 passes setup/artifactdownload/imagebuild/wrappersmoke and is measuring guardedresize/GRT/antennas/STA. No physicalpass inferred yet. Latestmainlintgreen; test/docs/unit stillrunning atcheck.
- Prepared local event_nor2_route.py and18gate/provenance tests. Full34NOR2helpertests pass. Continuation requires exactsuccessfulscreen, identity/one-cellnetlist/zerooverflow/antenna gates, freshallcornerSTA and50psfastbudget; ordinaryimage preventsrepeatresize. It preserves originalsourceevidence and refuses existingDRToutput.
- No routeworkflowintegration, publication, dispatch, mainhardware/configchanges orphase ticks. Newcontinuationfiles deliberatelyremainlocal pending measuredscreenresult. Next: inspectactualscreenartifact; ifqualified, integrate/publishreviewedcontinuation androute/extract/GL, thencleanofficialreproduction.

## 2026-10-08: Codex (approved one-cell repair publication)
- Published3591a5f tools,f8bfd01 workflow,631fab1 evidence to remote main. Repair-only [37730917594](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37730917594) is in progress on631fab1a6ba913d912590ebdb347ce8fe6548585; noDRT.
- User explicitly approves separate tools/workflow/report commits, remote main push and repair-only launch. Tools3591a5f and workflowf8bfd01 committed; FIPE and oldSRAMprototypes excluded.
- Rechecked diff and unpublished src/info/macro history: clean. No mainworkflowactive beforepublication; mainhardware/config/templatejobs unchanged.215helpertests pass.
- No phase boxes ticked. Next: push approvedgroups, launchgds-event-nor2-screen, inspect actualfreshGRT/STA/antenna gates before anyDRT/extractionfollow-up.

## 2026-10-08: Codex (Phase2 guarded one-cell physical screen prepared)
- Prepared event_nor2_size.tcl, wrapper/image, event_nor2_screen.py and separate manualgds-event-nor2-screen. Exactoriginalroute37574267994/source37533969613/event-late; oneNOR2resize, legalization, freshGRT/netlists, allcornerSTA/antenna gates. No broadresizer/DRT.
- Independently audited459MBoriginalartifact11464617506: exact pre-routecheckpointviews andtargetconnections present; intended one-cell netlistcomparison passes. PinnedLibreLane3.1.0.dev3 source reviewed from downloadedwheel withoutinstallation.
-215helpertests pass; Bashsyntax/diffchecks pass. Freshnetlistpromotion clears staleSPEF/SDF/lib; source/master/pins/connectivity/power, unintendedchanges andcompletezerolayeroverflow guarded. No phase tick, mainhardware/config/templatechanges, publication ordispatch.
- Next: publish reviewed tools/workflow/report groups under explicitgitexception oruser-runcommands; launchrepair-only screen. Then measuredDRT/extraction/GL ifqualified, andcleanofficialreproduction beforeclosingroutablebudgetgate.

## 2026-10-07: Codex (targeted sizing reproduces baseline and clears local residuals)
- Original125ps exact netlist/SPEF plus fully timedconstraints reproduces allcornerCIsetup/hold within1e-6ns. Twelve verified OpenSTAcorner invocations pass withoutSTAerrors; comparison in `/tmp/event-125ps-local-eco/comparison.json`.
- SingleNOR2 `_27853_` strength1→2 moves slowRXtimer23/22 -0.179789/-0.052855 to +0.103142/+0.230076ns; fast holdunchanged +0.0372895ns. Libraryarea +3.6288µm². NOR4alone +0.044478/+0.171411; both +0.327406/+0.454339. GlobalsetupWS0, notpositiveofficialWNS.
- Report PHASE2_TARGETED_CELL_SIZING.md records exact connections, guards and limitations. Fixedwireprobes do not prove legalization/newrouting/signoff. No mainhardware/config/remotechange, physicaldispatch or phase tick.
- Next: prepare boundedphysicalNOR2follow-up on exactoriginalcheckpoint; freshallcorners/antennas/extraction/protocolvalidation beforepromotion. No mainworkflowcurrentlyactive.

## 2026-10-07: Codex (banked extraction audited; original baseline retained)
- Route37709856777 succeeds, final routeDRC0. Artifact11522683978/extracted37714872507: slow setup -2.4757636642ns, fast hold +0.0949399475ns; fast/typ setup0, slow/typ holdpositive. Reject banked promotion versus original125ps -0.179789ns.
- Audited41 printed slow violations: all U0 PERIOD word4bit1;40droppedcounter,1fabricchannel1last_seq. Worst data path has no named hold-delaycell. Report PHASE2_BANKED_EXTRACTED_REGRESSION.md.
- Independently parsed routedGLartifact11525366657:22/22,0failure/error/skip. Local official-wrapper RTL also22/22 withsigrok,770.10s; manifest updated withJUnitSHA. Latest lint/test/docs/unit allgreen; no main workflowactive, only two obsolete superseded queued entries.
- Started isolated single-cell sizing probes on strongestoriginal125ps extractednetlist/SPEF. LocalfullytimedSTA reproduces its reported worststart/end and roundedslowWS-0.18ns; saved routingSDC exceptionremoved for signoff replay. No mainRTL/config/historychanges or phase ticks. Next: inspect exactdelta/allcornerhold and qualify physicalrepair beforelaunch.

## 2026-10-07: Codex (banked configuration review continued)
- Wrapper replay has passed6/22 cases, including UART TX/RX; servo PWM is active. Complete JUnit remains pending.
- Prepared banked-specific native config review/patch/audit in isolated candidate. Static fully timed constraints, three corners,125ps target and physical error gates pass; ten proposed keys differ, none applied.
- Route37709856777 and latest unit37709844787 remain active; lint/test/docs pass. GitHub live-job logs API returns404, so no internal DRT iteration inferred from its combined step name.
- No phase ticks or main hardware/config/remote changes. Next: complete wrapper replay, collect routed/extracted/GL evidence, then resolve clean-build SRAM repair and routing reservation portability.

## 2026-10-07: Codex (parallel banked official integration preparation)
- Prepared isolated original-RX/event-late/banked candidate in `/tmp/tripwire-banked-official-prep-20261008`. Generation and four top-level smoke tests pass; 19-source lists match, seven SRAM views resolve, clock remains20ns. Local hardware review patch/inventory covers17 changed integration files; no promotion.
- Corrected local L3 invocation from nonexistent tripsim/spec.py to generated tools/tripwire_spec.py. The first invocation stopped before simulation; corrected22-case full-wrapper RTL/sigrok replay is running, results pending.
- Route37709856777 remains active after successful identity/image checks. Latest main lint/test/docs pass; unit is in chip-level/L3 RTL checks. No phase boxes ticked or main hardware/config/template jobs changed.
- Next: collect wrapper JUnit; inspect completed route, actual extracted timing and routedGL; resolve checkpoint-specific repair/native-flow portability before official dispatch.

## 2026-10-07: Codex (approved repaired banked routing publication)
- Publication complete:7af0b1d tools,a2e7e4b workflow,dbdfb7f reports pushed; HEAD/origin/main matchdbdfb7f7a7530d5dd0e8e00996a30ce063591460. Routed continuation37709856777 is in progress on main.
- User approves separate tools/workflow/report commits, push and detailed-route launch. Rechecked245 helper tests and diff; no src/info/macro history changes or main hardening active.
- Tools committed7af0b1d; workflowa2e7e4b. Exact repaired source37690561695 has independently checked all-corner/50ps/antenna/identity gates; no repeat SRAM insertion or repair. FIPE and unrelated addr0 prototypes excluded.
- No phase boxes ticked. Next: push approved groups, launch exact continuation and inspect route/extraction/GL before any official promotion.

## 2026-10-07: Codex (repair passes; routed continuation prepared)
- Repair37690561695 passes: post-antenna setup0 all corners, holdfast/slow/typ +0.0700513/+0.376972/+0.198153ns; zero counts/antenna/GRToverflow. Artifact11513594590 independently validates36source hashes against frozen plus tested BS/IO and all checkpoint files. Seed buffer retained.
- Repair adds422 hold buffers; area526445/count34104, +3.03% from banked source. No extracted gain claim. Latest3c494c0 lint/test/docs/unit green.
- Prepared optional repaired-checkpoint continuation in existing route workflow; strict dual provenance, identity, saved/fresh50ps/all-corner/antenna checks, no repeated insertion/repair, original failing source refused.245 helper tests pass. Review PHASE2_BANKED_SRAM_HOLD_ROUTE.md; phase summary updated.
- No phase ticks, commit/push or DRT dispatch. Next: publish reviewed continuation and route exact repaired37690561695, then actual extraction/22caseGL before official-flow integration.

## 2026-10-07: Codex (repair wrapper PATH fix)
- Published e5d626f tools,da950eb workflow,3c494c0 docs to remote main. New repair-only37690561695 queued on3c494c023c65fea002665ebc04e0c31a809c4cf4; no DRT.
- Run37689746190 passes config guard but fails before STA because companion wrapper is not on LibreLane runtime PATH. Logged BUG76; delegate via installed wrapper directory, preserving actual script arguments.
-225 helper tests pass, including STA delegation and malformed/valid insertion with installation directory absent from PATH. Added container wrapper smoke before physical measurements. No physical mutation/timing result inferred from this failure.
- Next: publish corrective tool/workflow/docs groups and relaunch under existing repair-only authorization. No phase ticks or DRT.

## 2026-10-07: Codex (repair-only config guard scope fixed)
- Published c6e871c tools/tests and b5a19e4 docs; remote/local main match b5a19e4fc5a2918bdbad2f910d8b19846df2a327. Corrected repair-only run37689746190 is in progress.
- Run37689090398 fails before insertion: KeyError PL_TARGET_DENSITY_PCT. LibreLane resizer step config intentionally omits placement-only key. Logged BUG75; validate density in base plus unique actual placement config, keep repair clock/GRT/mirroring/SDC checks.
-224 helper tests pass; actual downloaded source configs pass corrected guard with runner SDC path rebased only in local audit. No timing result or hardware failure inferred from this tooling abort.
- Next: publish corrective tool/test/docs groups under approved repair-only scope and relaunch exact experiment. No phase boxes ticked or DRT dispatched.

## 2026-10-07: Codex (workflow and phase2 status snapshot)
- Repair-only37689090398 is building pinned region-reservation image. Current dbd3dd9 test passes; lint/docs/unit active (RTL Icarus/Verilator suites); older docs37668163469 remains displayed active. Two stale automatic extraction/GL entries still queued, superseded by completed manual runs.
- Phase2 checklist10/11 checked historically; routable-budget item remains open. Historical official typical-only gate does not meet current user requirement of positive full-design official WNS and nonnegative all-corner hold. Original125ps remains strongest extracted setup -0.179789ns/fast hold +0.037290ns; latest banked GRT setup0/fast hold -0.0223693ns, no banked extraction.
- No phase ticks. Next: inspect actual repair-only gates, then guarded routing/extraction/GL if justified; reproduce clean recipe in official GDS and revalidate complete candidate before phase exit.

## 2026-10-07: Codex (approved repair-only publication)
- Publication complete:41f23d9 tools,7499d4a workflow,dbd3dd9 reports pushed; HEAD/origin/main matchdbd3dd9a515f4d511ddf4b8de637a846b4bd1ff4. Repair-only run37689090398 is in progress on main. No DRT dispatched.
- User approved separate tools/workflow/reports commits, push and manual launch. Rechecked217 local helper tests and diff; no unpublished src/info/macro history or main hardening active.
- Tools committed41f23d9; new manual workflow7499d4a. Reports record exact negative banked hold and preserve original125ps baseline. FIPE and old addr0 prototypes excluded; direct routing support remains local until measured repair evidence.
- No phase boxes ticked. Next: push approved groups and launch repair-only screen, then inspect real legalization/routing/all-corner margin and antenna gates before any DRT.

## 2026-10-07: Codex (bounded SRAM repair-only workflow prepared)
- Prepared separate manual gds-banked-sram-hold-screen, exact source37669663762/variant identity, guarded address8 BUF1 insertion with legalization,125ps all-corner repair, antenna recheck and fresh50ps/all-corner timing gates. No DRT in this flow; gate failure is workflow failure with evidence upload.
- Independent image preserves existing Metal2 reservation; wrapper validates one checkpoint read and insertion order.217 local helper tests pass; Bash syntax/diff checks pass. Real physical behavior awaits pinned CI; local OpenROAD lacks QtCharts.
- Review in PHASE2_BANKED_SRAM_HOLD_SCREEN.md. No source/config/template job changes, phase ticks, commit/push or dispatch. Current AGENTS reserves history/remote changes to user; publication authorization for this new workflow remains needed.
- Next: publish reviewed tool/workflow groups then dispatch repair-only measurement; no routing until measured gates and source provenance pass.

## 2026-10-07: Codex (banked hold residual audited and guarded delay prepared)
- Screen37669663762 banked setup WS0 all corners; hold fast/slow/typ -0.0223693/+0.147057/+0.0526946 ns. Baseline hold +0.0313302/+0.229262/+0.102516 ns. Diagnostic green is not timing pass.
- Artifact11506981784 maps the single fast failure to lane1 acc_addr8→SRAM A_ADDR8. Repair area510973 µm²/33156 instances; zero GRT overflow. Do not launch direct routing: source gate correctly refuses hold failure.
- Prepared banked_sram_addr_hold.tcl with exact net9161/BUF2 wire9161/SRAM address8 guards and one BUF1 insertion. Five mock Tcl guard tests pass, zero skips. Actual OpenDB audit blocked by missing local libQt5Charts.so.5; no actual physical repair/timing claim.
- No phase ticks, history changes or workflow dispatch. Next: run a bounded repair-only measurement in pinned CI with source identity, legalization/routing, all corners and antennas; route only after measured pass/headroom. Original125ps remains strongest extracted baseline.

## 2026-10-07: Codex (matched banked screen completes)
- Both jobs in corrected screen37669663762 pass; latest cf78cde lint/test/unit/docs all pass. Older docs37668163469 still displays in progress.
- Independently read final GRT log tables: baseline and banked have zero overflow on every layer. Banked demand244196/usage40.81% versus baseline239415/40.01%; no extracted closure claim. Actual corner margins/instance-area artifact audit remains next.
- No phase ticks or routed dispatch. Retain original125ps as measured baseline until extracted comparison proves improvement.

## 2026-10-07: Codex (prepare guarded banked routed follow-up)
- Corrected matched screen37669663762 now has both event-late and banked jobs actively screening through GRT/fresh timing. Latest cf78cde test/lint/docs green; unit active.
- Prepared local downstream registration, exact banked IO fingerprint requirement and125ps-only headroom option. Successful main source provenance, complete original RX/BS/IO identities, fresh50ps fast-hold budget and all timing/antenna/DRC gates remain enforced.
- Added workflow-catalog test covering every actual screen input against patch mapping/runner, preventing BUG74 registration drift.196 helper tests pass; git diff --check passes. Changes remain local; no routed dispatch or phase ticks.
- Next: inspect screen results before publishing/launching routed continuation; require extracted improvement relative to original125ps -0.179789ns baseline.

## 2026-10-07: Codex (fix banked screen runner registration)
- Screen37668189723 banked job fails before synthesis with Unknown timing screen variant: workflow/patch mapping registered, runner timing-placement allowlist missed. Logged BUG74; corrected runner and added variant policy test.174 helper tests pass.
- Published only runner/tests fix cf78cde to remote main under screen authorization. Requested cancellation of incomplete failed comparison; dispatched corrected paired screen. No hardware changes or phase ticks.
- Next: inspect fresh matched physical results, retain original125ps baseline until extracted improvement is demonstrated. Shared-RX22/22 functional pass does not offset setup regression.

## 2026-10-07: Codex (approved banked-selector screen published and launched)
- User explicitly authorized commit/push/dispatch. Committed only four screen helper/workflow/patch files as e5a6e3c; push to remote main confirmed. Local HEAD and origin/main match e5a6e3cd129c9d59a6e6fa40bb90bbfab392bd2a.
- Launched matched bs-event-pin-banked versus bs-event-late screen37668189723; status in progress. Original RX retained. No main src/info/macro changes or phase ticks. FIPE report remains local/untracked.
- Initial compound command approval timed out before execution; simpler retry succeeded. Next: inspect matched all-corner setup/hold, overflow, area and endpoint evidence before any routed follow-up.

## 2026-10-07: Codex (smaller candidate screen prepared)
- Added bs-event-pin-banked to the manual RTL screen and source patch mapping; guard rejects missing IO or added RX mutation. Actual patch application reproduces verified BS/IO/original RX byte-for-byte.159 CI helper tests pass; git diff --check passes.
- Shared-RX routed GL37659138336 independently passes22/22 from artifact11501802812. Timing remains -1.427891 ns, so candidate is not promoted.
- No phase ticks, commit/push or workflow dispatch. Current AGENTS git rule reserves publication for user; exact screen dispatch recorded in regression report. Next: publish helpers/workflow/patch, then matched screen against event-late; route only with justified screen evidence.

## 2026-10-07: Codex (recover stronger baseline and verify smaller selector candidate)
- Independently mapped40 shared-RX slow setup report violations:39 dropped-counter entries and one channel2 last_seq, all from U0 PERIOD word4 bit11. Worst dropped[22] -1.427891 ns; worst data path has no named hold-delay cell. Original125ps remains stronger measured baseline.
- Prepared bs_event_pin_banked.patch against original RX/event-late; source audit confirms only BS/IO changes. Fresh cached-carrier pin harness passes60/60; chip5/5; model/RTL2048 clocks with zero divergence. Earlier pin fixture invocations reproduce known BUG73/stale build and are superseded, not hidden.
- Added regression report and updated readiness to disqualify shared-RX promotion. Routed GL37659138336 still running. No phase ticks, hardware promotion or physical dispatch.
- Next: screen the smaller candidate against the original event-late baseline with all setup/hold/overflow gates; require extracted evidence before official promotion.

## 2026-10-07: Codex (shared-RX extracted timing result)
- Manual extraction37659134964 completed successfully as a diagnostic, but extracted slow setup WS is -1.427891 ns; fast/typ setup WS0. Hold fast/slow/typ is +0.059525/+0.331955/+0.168051 ns. This candidate does not close timing and regresses setup versus original125ps -0.179789 ns.
- Manual routed GL37659138336 is actively running the expanded L3 suite. Stale automatic entries remain queued. No phase ticks or hardware changes.
- Next: inspect extracted failing paths and repair-induced area/buffers before choosing another physical experiment; retain original125ps as stronger measured setup baseline.

## 2026-10-07: Codex (manual downstream checks recover stalled queue)
- Automatic extraction37655518925 and GL37655518919 remained queued with no jobs; cancellation endpoint inconsistently reported completed. Successful source route37642988571 verified on main.
- Manually dispatched extraction37659134964 and routed GL37659138336 on main against the same route artifact/frozen candidate. Both now in progress. No hardware/config changes or phase ticks.
- Next: inspect actual extracted margins and expanded GL; stale automatic entries may persist in the UI and must not be mistaken for active checks.

## 2026-10-07: Codex (official native configuration review)
- Assembled isolated native configuration, ten-key review diff and portability audit in /tmp/tripwire-shared-rx-official-prep-20261007. Static assertions pass: 20 ns, fully timed PNR/signoff constraints, three corners, 125 ps hold target and physical error gates. Source configuration remains unchanged.
- Shared-RX route37642988571 passed with final DRT violations zero. Extraction37655518925 and routed GL37655518919 are queued; extracted closure is unconfirmed.
- No phase boxes ticked, new workflow launched or hardware change. Next: inspect downstream evidence and resolve native repair/Metal2-reservation portability before official promotion.

## 2026-10-07: Codex (parallel shared-RX official integration preparation)
- Kept structural changes on hold. Prepared isolated /tmp/tripwire-shared-rx-official-prep-20261007 withevent/sharedRXonly;bankedfallbackexcluded.19source lists/sevenSRAMviews/20nsmetadata andphysicalerrorgates checked. Generatorpasses;4top-levelsmokespass,0fail/error/skip;manifestincludesJUnitdigestandreviewpatch.
- Audit confirms inheritedPNRSDCcontainslatchsetupfalsepath;qualifiedofficialrecipe mustusefullytimedconstraintsconsistentwithD-066. Extra checkpointrepair/customMetal2wrapperalso neednativecleanbuildhandling. Separate125psnativeproposalremainsunapplied.
- No mainhardware/config changes,officialdispatch,newworkflows orphaseticks. Readinessreportupdatedlocally whilecurrentroute runs.
- Next:inspectactualsharedRXroute/extraction/GL;promoteonlywithallgates passingandreviewedofficialrecipe. Currentstatic/smokeevidenceisnotphysicalsignoff.

## 2026-10-07: Codex (local pin-selection study)
- SharedRXroute37642988571 remains active. Studied four equivalent selector forms on frozen trw_pin_io; factored validity worsens both area/timing, padded/polarity versions worsen the relevant pad path and are not queued.
- Banked comparison proves19points and maps1.5% smaller IO area. Ideal-wire slowpad→sel1.511804→1.442738ns;C_ACTIVE→sel worsens0.674786→0.796614ns. No full-design WNS gain claim.
- Isolated event/sharedRX/banked combo passes41pin tests,5chiptestsand2048-clockL2. Prepared pin_select_banked.patch, report andD-079. No mainRTL/config/spec change orphase tick;localFIPEfile remainsuntracked.
- Next:finishchip/L2, publish verifiedprototype/evidence separately, then choose physicalfollow-up fromactualsharedRXextraction. Preserveallsetup/hold/physicalgates.

## 2026-10-07: Codex (return focus to design timing)
- User requests the external-project comparison stay local. Removed its report from tracked files and retained the local copy; no ignore rules added. Removed the detailed comparison entry from the published worklog.
- No chip, configuration or workflow changes. No phase boxes ticked.
- Next: inspect shared-RX route37642988571 and continue setup/hold closure, extraction and protocol verification.

## 2026-10-07: Codex (completed shared screen and 22-case routed GL)
- Allmainworkflowsfinished;latestlint/test/docs/unitandnightlygreen. Original125psGL37581139271passes22/22,0fail/error/skip;independentlyparsedJUnitartifact11467535087. Originalslowsetupremains-0.179789ns.
- SharedRXscreen37579966660complete:setup0allcorners;holdfast/slow/typ+0.0166144/+0.150971/+0.069035ns. Finalinstancearea515652.60um² versusbaseline510232.98 (+1.06%);notextractedclosure.
- DispatchedpreviouslyverifiedguardedsharedRX125pscontinuationfromsuccessfulmainsource37579966660;preserveonepass/fresh50psfast/allcornertiming/physicalgates. No mainRTL/configchangesorphaseticks.
- Newcontinuation37642988571queuedon09db1db. Next:inspectfreshrepairheadroomandDRT;oncleancompletionextractandrunexpandedGL. Officialclosurestillunproven.

## 2026-10-07: Codex (125 ps residual setup localized to RX)
- Auditedartifact11464064023:exactlytwo slowsetupfailures,U0PIN_A1→U3RXrt23/22 (-0.179789/-0.052855ns). No finalholdcellinreportedpaths;dropped-counter failuresabsent. CommonSELarcsO21AI1.167ns/XOR1.306ns;NOR2/NOR4alsoweak. PinnedlibraryhasstrongerNOR2/4butnotXOR/O21AI;targetedfanoutrepair remainsfallback.
- PreparedexactsharedRX+125pscontinuationguard;refuseotherunreviewedsource/targetpairs.171helpertests pass. Existingall-corner/fast50ps/antenna/DRCgates preserved;no mainRTL/configchange/phase tick.
- SharedRXscreen37579966660and125psGL37581139271remainrunning;latestlint/test/docs green,unitactive. No routingdispatchuntilsharedRXsourceactuallypasses.
- Published CI2901811 anddocs09db1db;localHEAD/origin/main/GitHubref verified09db1db22ee2d5859adec551ac1bb71df27eafc5. SharedscreenandGLstillactive;continuationnotlaunched.
- Next:inspectsharedscreenandlaunchguardedcontinuationonlywithpassingprovenance;waitforactualGLbeforefunctionalclaim. Officialtimingunproven.

## 2026-10-07: Codex (125 ps route complete and parallel endpoint audit)
- Main125psroute37574267994passes withrouteDRC0;180extra holdbuffers,repairpassarea+2.7%,postantennafast hold+0.0991903ns/setup0allcorners. Extraction37581139249andGL37581139271active. SharedRXscreen37579966660measuringbothbranches;latestunitactive,lint/test/docs green.
- Extendedreporting-onlyexecution_margin.tcl withpreserved-net endpoint selection:96RXtimer,72dropped-counter,9SRAMaddress;D-onlyflopgroups excludereset. Replayedoriginal37551577987extraction allthreecorners;endpointcountsandsixreports/cornerpass. Olderlocalenginecannotreportfull latch timing;withheldsignoff/125psclaims.
- Publishinghelperandmeasuredreportseparately;no mainRTL/config change,phasetick orconstraintchange. OlderSRAMinsertionprototype remainsunlaunched/untracked becauseitscheckpointdoesnotmatchRX/newcandidate.
- Publishedhelpercdd7e2banddocs55c54db;HEAD/origin/main/GitHubrefmatch55c54db102dbcf5277b464c680f5db65bfb04faf. Extraction37581139249nowcomplete:slowsetup-0.179788633514ns,fasthold+0.037289505872ns;fast/typsetup0. Notclosed. GLandsharedRXscreenremainactive.
- Next:inspectactual125ps failing setuppathsand22-caseGL;assesssharedRXoverflow/area;runresidualreportwithpinnedenginebeforeofficialpromotion.

## 2026-10-07: Codex (shared RX physical screen preparation)
- Main125psroute37574267994 remains active;latestlint/test/docs passed,unitactive. Correction:its single named step includes repair/antenna andDRT,so active step alonecannotidentifyexactsubstage.
- Preparedbs-event-rx-shared pair against event-late withtwo-module mutation/provenanceguards.181helpertests pass;workflowchoices parse. Freshreusableverification provesBSandRXFRAC4/8;41pintests,5chiptestsand2048L2clocks allpass. No mainRTL/config/templatejobchange orphasetick.
- Publishedprototypee7a3447,CIf3371dd,docsfbf7835;HEAD/origin/main/GitHubref allmatchfbf78351e1990851897086c055b1254598a7ddfb. DispatchedsharedRXscreen37579966660,queued;newtest/docs/lint/unitactive.125psroute37574267994continues. Threeolderexperimentalhelpersremainuntracked andwerenotincluded. Next:inspectnewscreenand125psextractedresultwhenavailable. Retainallphysical/timinggates.

## 2026-10-07: Codex (main workflow progress and RX screen result)
- All latest main lint/test/docs/unit runs on24bb0fd passed.125psroute37574267994 remains active atantenna/fresh-timing checks beforeDRT; no new extracted result.
- RXpairedscreen37572964628completed:setupWS0allcornersboth;fast holdRX+0.0229828ns versusbaseline+0.0313302ns. BothfinalGRTzerooverflow. Postrepairinstancearea510232.98→517408.93um² (+about1.41%);routingdemand239415→245441. RecordedactualresultinRXreport;no promotion/phase tick.
- RXendpointaudit:worstfastpathlane1rpc0→SRAMA_ADDR0,+22.983ps;second+37.224ps. Slowmax1000pathsalllatchendpoints,nontimer,soaggregate0cannotproveRXsetupbenefit.
- BuiltsmallerRXshared-delta patch:area11701.7082um² (6.83%belowpreviousprototype),ideal-wiretimertiming1.812930ns,otherinputendpoint6.063411ns. FRAC4/8equivalence,41pintests,5chiptestsand2048L2clocks pass. Initialcurrent-encoding/frozenRTL invocation was discarded;matchingfrozenenvironment rerunpasses. No physicalgainclaim/mainRTLchange.
- Next:finishsharedvariantchip/L2,inspect125psresult,andpreparepinnedendpointmeasurementbeforepromotingRX. Retainallgates;officialpositiveWNS remainsunproven.

## 2026-10-06: Codex (area-conscious timing follow-up)
- Prepared bounded 125 ps event hold target between the tested 100/150 ps settings. Five CI/workflow files updated; 135 helper tests and workflow default/choice validation pass. Retained every setup/hold/physical gate; no main hardware/config edits or phase ticks.
- Main paired RX screen37572964628 still measuring GRT/fresh timing on both branches. Unit37572948480: Python and Verilator jobs pass, Icarus chip/L3 step remains active; lint/test/docs pass.
- Prioritized selective delay-cell sizing, measured weak-gate drive fixes and state-derived counter carry over replicated arithmetic/storage. RX prototype costs29.4% module area; full-chip overflow must justify adoption.
- User subsequently explicitly authorized commits/pushes. Committed the verified CI group as57039a5; publishing docs separately and dispatching125ps from the original trusted event source. No main hardware inputs change.
- Published CI57039a5 anddocs24bb0fd toremote main; localHEAD/origin/main/GitHubref independently match24bb0fda821bc829c5c0c4992405f7169e7b7844. Dispatched125psroute37574267994,inprogress. RXscreen37572964628continues;newlintpassed,test/docs/unitactive. Three experimentalhelpers remainuntracked andwere notincluded.
- Next: inspect125ps fresh/extractedsetup/hold andRXscreenarea/overflow/all-corner timing;promoteonlywithphysical/GL evidence. Officialtiming remainsunproven.

## 2026-10-06: Codex (RX timer late-selection prototype)
- Routed150ps eventGL37566926287 completed22/22PASS,0FAIL/SKIP. Extracted slow setup still−0.389409ns despitepositivefast hold+0.067034ns; no timingclosure.
- Pairedscreen37569441149completed:dropqualification setup0allcorners butfast hold−0.0184668ns versusbaseline+0.0313302ns. Refuse directrouting/promotion ofthatfailingcandidate.
- NewRXtimer arithmetic moveslateSTARTselectionafterprecomputedvalues; preservesall sample clocks/livewrites. ModuleequivalenceFRAC4/8passes (FRAC8:226points,inductionstep1underseq2cap);20RX/fulltests,5chiptests and2048L2clocks pass locally. Mappedslowain→rt6.620677→1.943963ns,area9704.3184→12559.7682um² (+29.4%);onlymoduleprobe,fullroutingcostunknown.
- FoundBUG73:frozen standalonepin carrier_active unconnected. Opt-inharnessconnectioncommit64fa661;mainolderinterfaceandfrozentrial20/20eachpass. Reusableverifier archivesHEADtests,sofirstreuse stillhadoldfixture;freshcommittedfixtureverification passedbothmoduleproofs,41pintests,5chiptestsand2048-clockL2.
- Prepared pairedRX/eventscreen+routeprovenance,requiredRXhash,157helperchecks passingandworkflowparsepassed. NewreportPHASE2_RX_TIMER_LATE.md,D-075/BUG73/CLAIMS evidence recorded. No mainRTL/config/spec/templatejobs edited; no phase ticks.
- Fresh reusable verification completed both named module proofs,41pin tests,5chip tests and2048L2 clocks. Published test64fa661,prototype84501b4,CI42fddb2,docs15e1d13 toremote main;HEAD/origin/main/GitHubref allmatch15e1d1344dee7da5d52671ab15288c2df9098468. Launched matchedRXscreen37572964628,event-latebaseline,queued atcheck. Newlint/test/docs/unitrunning. No mainhardwarechanges.
- Next: inspectnewscreenallcornertimingandglobaloverflow;routeonlypassingcandidate. Keeppriorfailedcountercombinationand150pssetupregressiondistinctfromfunctional22/22GLpass.

## 2026-10-06: Codex (standing publication authorization)
- User grants standing approval for commands, commits, pushes and workflow launches in this timing task; no repeat scoped approval needed for routine authorized work. Repository rules and evidence requirements remain otherwise intact.
- Committed verified prototype patches9f5037b separately from CI187d4fd. Both named-module proofs, channel/pin/chip simulations and2048-clock L2 pass for the new combination;143helper tests andworkflow parses pass. MainRTL/spec/config/template jobs unchanged.
- Publishing reviewed reports with exact extracted setup/hold tradeoff and complete22/22localwrapperprotocol evidence. Pending push/pairedscreen dispatch; no physical gain orphase tick claimed.
- Published prototype9f5037b,CI187d4fd anddocsacd7d5f toorigin/main. LocalHEAD,origin/main andGitHubref independently matchacd7d5fdc79bf8999607cddc5901528842ed3f46. Launched pairedscreen37569441149(bs-event-drop-qual versusbs-event-late),inprogress. Newlint/test/docs/unit active; priorroutedGL37566926287stillrunning. Remaininguntrackedfiles areexecutionreport/SRAMprototypehelpers; publicationstatus notes remain local.
- Next: inspectmatchedscreen'sfreshallcornertimingandrouteonlywithpasses;monitorpriorGL andcontinue setup/hold closure withoutrepeatpermissionquestions.

## 2026-10-06: Codex (paired combination screen prepared)
- Prepared bs-event-drop-qual screen and route continuation with exact two-module mutation guards, independent source fingerprints and successful-main provenance. Optional comparison_baseline=bs-event-late isolates the new channel qualification change; existing defaults remain unchanged. No template GDS jobs or main RTL/config edited.
- 143 CI/helper tests pass, workflow choices/defaults parse, and diff check passes. Reusable verifier proves both modules (channel N=1/5/6/7/9/16 and bitsync), channel/pin/chip suites and fresh 2048-clock L2 all pass (session74453 exit0). Report PHASE2_EVENT_DROP_QUAL.md contains review scope and proposed dispatch.
- Routed GL37566926287 still running. No new physical margin or phase tick; publication/dispatch pending a scoped git exception under AGENTS.md.
- Next: finish reusable L2, publish reviewed CI/prototype/docs groups and launch matched event-late comparison after authorization; inspect current routed GL.

## 2026-10-06: Codex (actual setup cone and verified combination)
- GL37566926287activeatmaincheck;route/extractionsuccessstatusesunchangedandtimingnotclosed.
- Auditedcompletedartifact11459002750:11slowsetupentries,9droppedcounter/2U3RXrt22/23. SourcesU1/U0PIN_Aselectionword1bit1. Worst−0.389409ns/second−0.344089ns include0.662608/0.617550nshold-delaycells;otherfailureshavenofinalholdbuffer,soeffectsincludecriticalrouting/slew.
- Builtisolatedevent-late+drop-qual,frozen2/4. ChannelmoduleequivalenceN1/5/6/7/9/16passes;channeltests,5chiptestsand2048L2zero-divergencepass. Localpatchbs_event_drop_qual.patch;rawresults/tmp/event-drop-qual-20261006. No mainRTLchange,push,dispatchorphysicalgainclaim.
- Next: preparesource-provenancedtwo-modulephysicalscreenandreviewcounter/RXcones;inspectcurrentGL. No phase ticks.

## 2026-10-06: Codex (150 ps extracted tradeoff and static audit)
- Newroute37559740009SUCCESS,extraction37566926240SUCCESSdiagnostic: setupfast/typ0,slow−0.389409404633ns;holdfast+0.067033713810,slow+0.379780995180,typ+0.184989584442ns. Notclosed.443holdbuffers,pre-routefasthold+0.120978ns,extractioncost53.944ps. GL37566926287running; allCIgreen.
- Startedartifact11459002750downloadtosavedzipforslowsetupcone audit. Priorityshiftedtoactualsetupregression; donotpromote150psaspassingrecipe.
- Staticcandidateauditpassed19sourcepaths,7SRAMviews,clockmetadataandphysicalerrorgates. Recordedstatic_integration_audit.jsonandupdatedreadiness/headroomreports. No physicalgeometry/LVSclaimorphaseticks.
- Next: identifyextractedslowcriticalpaths,chooseboundedselectivehold/setupfollow-upandinspectGLresult.

## 2026-10-06: Codex (official native recipe audit)
- Main150psroute37559740009stillactive; allCIgreen. Verified officialaction LibreLane3.1.0.dev3andIHPnativeconfigmerge fromremoteaction/project/techsource.
- Prepared standalone native-timing-settings-proposal.json inisolatedcandidate:timing-driven/no-mirror placement,zero setup targets,0.16routing,signoffPNRconstraints,allcornersandpending150pshold. Notappliedtosrc/config orpublished; requiresreviewedconfigexception beforeadoption.
- Documented customMetal2wrapperandextra checkpointpass are notreproduced bynormalofficialflow. Firstofficialbuildmusttestportability ratherthanassumeequivalence. No officialdispatch,phaseticksornewmarginclaims.
- Next: inspect150psroute/extraction,thenreviewnativeconfigandfullcandidatepromotionforofficialGDS.

## 2026-10-06: Codex (parallel candidate protocol gate passes)
- Full-wrapper2/4event-late RTL replay finished22/22PASS,0FAIL/ERROR/SKIP withsigrok enabled,1545.11s. Independently verifiedJUnit andrecordedhash in /tmp/tripwire-official-2x4-prep-20261006/candidate_manifest.json. Localterminal28639 complete.
- Generator --check passes. Prepared /tmp/tripwire-official-2x4-prep-20261006/official-hardware-review.patch againstcurrentHEADsource/spec/info/testMakefile forreview; no mainRTL/spec/config changes,promotionorpublication. Updatedreadinessreport tosupersede100psactive status withactualfailure/150psfollow-upandlocalprotocolevidence.
- No phase ticks: officialflowportability,latchmarginpinnedengine,andcompletephysical/precheck/GLremainrequired.
- Next: inspect150psroute/extraction; reviewofficialrecipe andcandidatepromotionwithactualphysicalresults.

## 2026-10-06: Codex (execution report helper and green CI)
- Mainlint/docs/test/unit on87fbb59 allpassed;150psroute37559740009 stillactive. Local full-wrapper replay has18passes,0failures andis running19HDLC.
- Prepared reporting-onlyexecution_margin.tcl,ran against actualprior extracted design at all3corners. Finds4504flop/2065latch/24output endpoints; flop/output/hold values match preceding independent audit. LocalolderOpenSTA emitsno latch paths unlike pinnedCI; explicitlydocumented incomplete latch coverage andwithheld globalpositive-WNSclaims. No constraints modified,remote helper integration/publication orphaseticks.
- Next: finish replay,check150psrouting/extraction andrun endpointhelperwithpinnedengine beforefinalmarginclaims.

## 2026-10-06: Codex (independent extracted endpoint margin audit)
- Route37559740009 andunit37559733397 remain active;lint/docs/test green. Local decoder replay28639 passed UARTTX/RX andis onMIDI.
- Audited previous event extracted netlist/SPEF/emittedSDC with local OpenSTA2.6.0: fast/slow/typ hold−0.014615/+0.104597/+0.030521ns reproduce published metrics. Worst flop endpoint setup12.147419/1.223082/8.164472ns; slow pathlane0a_lat13→rpc2. Output marginspositive. Local global setup report differs from pinned latch0report,so results are independent execution-path diagnostics,not official closure or replacement WNS.
- Added evidence/limitations to event hold-headroom report. No phase ticks,publication or additional remote launches.
- Next: confirm flop endpoint margin with pinned engine,inspect150ps actualfresh/extractedholdandcontinue protocol replay.

## 2026-10-06: Codex (local decoder replay started)
- Main37559740009 route and37559733397unit still in progress;lint/docs/test passed. No new extracted timing.
- Local first L3 suite finished22cases:5pass17fail,2073s. Inspected all17traces: each fails at empty sigrok annotation output. Previous out-of-sandbox UART/WS decoding confirms environment cause; not a full functional pass.
- Started full unchanged RTL L3 replay outside sandbox with working decoder,session28639,log /tmp/tripwire-official-2x4-prep-20261006/l3-decoder-replay.log andseparate results_l3_decoder_replay.xml. Old simulator completed; no duplicate live suite. No phase ticks.
- Next: inspect replay andremote fresh timing/extraction results.

## 2026-10-06: Codex (progress check)
- Main150ps route37559740009 remains in combined repair/antenna/fresh-STA/DRT step; public step label does not identify its inner stage. Unit37559733397 running;lint37559733405,docs37559733390,test37559733356 passed. No new extracted measurement.
- Local full-wrapper L3 advanced to19/22HDLC; multiple tests fail at sigrok annotation checks with empty stdout. Previously demonstrated sandbox libusb cause on UART/WS; suite not counted as passing and decoder-dependent cases need replay with working sigrok. No phase ticks.
- Next: finish local suite,inspect every failure and replay; audit remote repair's fresh metrics when available.

## 2026-10-06: Codex (approved 150 ps publication and launch)
Done:
- User explicitly authorized all listed commit/push/dispatch commands. Re-ran68helper tests anddiff check successfully; committed CIf99c148 anddocs87fbb59 separately,then pushed remote main. HEAD andorigin/main match87fbb59077f6af13739a59886d30ccc52738aa6e. No src/info/macro changes in pushed commits.
- Dispatched150ps event hold target run37559740009 from trusted source37533969613; in progress. New unit37559733397,lint37559733405,docs37559733390,test37559733356 in progress at check. Original routing failure/downstream skips unchanged; no physical pass claimed.
- Background terminal7673 is actual Icarus RTL L3 simulation,currently case7/22servoPWM. PID1663469 consumes101%CPU after11min,so actively computing. Decoder-restricted cases need replay outside sandbox; UART/WS saved waveforms already decode correctly there. No simulator stopped or duplicate suite launched.
Checklist boxes ticked: none.
Next: inspect150ps fresh/route/extraction gates; finish and replay decoder-dependent local L3 cases. Remaining local speculative combination/SRAM files and official-readiness edits intentionally unpublished.

## 2026-10-06: Codex (bounded follow-up ready for review)
Done:
- Audited artifact11454893508:241 endpoints below100ps target,255buffers (+0.8%area),internal100ps before legalization/rerouting became fresh48.7026ps. Worst slot461→lane0acc_addr[4]; next U2RXsst2+55.372ps,U2TXer1+55.628ps. Slow setup report1000entries all latch endpoints; execution margin not yet established.
- Prepared optional150ps event repair from original source37533969613. Source default and100ps option preserved;50ps fast budget/all-corner/setup/antenna/DRC guards unchanged.68helper tests passed,workflow choices/default parse anddiff check passed. D-074 and event-headroom report updated. No commit/push/dispatch in this session.
- Confirmed local sigrok failures are sandbox libusb initialization: same UART VCD decodes correct11bytes outside sandbox. Local L3 continues; its failures must be replayed with working decoder before a full-pass claim.
Checklist boxes ticked: none.
Next: publish scoped CI/docs groups using user-run commands perAGENTS.md,then dispatch150ps diagnostic; inspect local protocol suite and replay decoder-affected cases.

## 2026-10-06: Codex (hold-headroom failure diagnosis)
Done:
- Main route37557256170 failed the explicit50ps pre-route fast-hold headroom gate: repair improved fast WS+0.0313302 to+0.0487026ns; setup WS0allcorners,slow hold+0.376427ns,typical+0.17865ns. This is a margin-gate failure before DRT, not an extracted timing result. Dependent extraction37558180965 andGL37558180997 skipped. Unit37557237430 still running; lint/docs/test green.
- Started download of saved artifact11454893508 to /tmp/event-headroom-37557256170.zip for limiting-path audit. No gate relaxed or new workflow launched.
Checklist boxes ticked: none.
Next: inspect actual min paths and repair decisions before choosing a targeted hold change or another bounded margin trial; retain all-corner/setup/antenna guards.

## 2026-10-06: Codex (parallel full-wrapper protocol validation)
Done:
- Started the expanded 22-case L3 protocol suite against the isolated 2/4 event-late candidate using the real tt_um_tripwire RTL wrapper, behavioral SRAM and candidate-generated resource map. Local terminal session 7673; log /tmp/tripwire-official-2x4-prep-20261006/l3-official-prep.log. Elaboration passed and UART TX is running; no completed-suite claim yet.
- Early local L3 result: UART TX passed the Python waveform/reference and status checks but failed the additional sigrok annotation check (empty decoder stdout); UART RX framing passed. The suite is continuing. Investigate local decoder output before attributing the failure to RTL; do not claim a full pass.
- Checked main workflows: hold-headroom routing 37557256170 and unit 37557237430 remain in progress; test/lint/docs passed. This local simulation is independent of the physical repair result.
Checklist boxes ticked: none.
Next: inspect the protocol JUnit result, then compare the hold-headroom extraction with the previous fast hold deficit and complete official-flow adoption review.

## 2026-10-06: Codex (parallel official candidate preparation and local file audit)
Done:
- Explained remaining local files: combination patches/verifier registrations,guarded SRAM prototype/tests,report and recent status notes. They are separate unpublished work; no unpushed commits or hidden main RTL changes.
- Prepared isolated `/tmp/tripwire-official-2x4-prep-20261006` with full frozen2/4wrapper/source/SRAM plus event-late,regenerated resource tables/docs,and synchronized19source files. Generated RTL matches frozen exactly; gen --check passed. Manifest records35hardware/macro fingerprints. All4top-port smoke tests pass.
- Found old spike disables MagicDRC/illegal-overlap error gates; enabled them only in prepared candidate and recorded remaining PDN/SDC/NDR/flow adoption gaps. Updated PHASE2_OFFICIAL_GDS_READINESS.md. No main candidate adoption or physical pass claimed.
- Repair37557256170 active at pinned-image build inspection. No new dispatch/publication or phase tick.
- Latest progress check: repair37557256170 now active in combined repair/antenna/timing/DRT step; unit37557237430 active,lint37557237415/docs37557237426/test37557237427 passed. No new extracted results. Closest measured event setup0allcorners/fast hold−14.615ps; positive setup headroom and official complete-design validation remain unproven.
Next:
- Audit hold-headroom result and complete official-compatible physical recipe/full protocol validation before proposed promotion. Keep local speculative prototypes separate from published repair.

## 2026-10-06: Codex (prepare isolated event hold-headroom repair)
Done:
- Verified source event repair inherited50ps hold target and0setup target. Prepared optional/defaultsource100ps hold target for event-late only,one all-corner repair with resolved-target validation,fresh full pass and≥50ps fast headroom before existing antenna/DRT gates. This addresses known post-route margin loss without positive setup-margin latch stalls.
- Added D-073 and PHASE2_EVENT_HOLD_HEADROOM.md.131helper tests,workflow parsing/default-choice validation,diff check passed. No physical execution/publication yet; local combination and SRAM prototype files remain separate.
- User approved. Committed CIbfe2bc4/docs1f73633 and pushed origin main; local HEAD,origin/main and remote main independently match1f7363358daa3dda54e8d00da7864a8170e374f6. Launched37557256170(source37533969613,bs-event-late,hold target0.10,postantenna recoveryfalse),queued at verification. No unpushed commits; local combination/SRAM prototypes and subsequent status notes remain unpublished.
Next:
- Scoped CI/docs push and launch source37533969613/bs-event-late/pre_route_hold_target0.10 after publication authorization,then measure actual extracted setup/hold and GL. Continue full2/4 official candidate readiness; no phase tick or timing-pass claim.

## 2026-10-06: Codex (select event-late and audit final hold endpoints)
Done:
- Downloaded extracted event37551577987 artifact11452594564. Final fast min report contains3violating entries: lane1ex_imm[6]−14.615ps,[7]−7.615ps,and U0TXct[0]−6.856ps. These differ from load-flat SRAM targets. Slow max report starts flop→configuration latch,slack0,no violating entries; zero global setup WS does not establish positive headroom on useful flop paths.
- Verified routed GL37551578053 job112568071978 log:22tests/22pass/0fail/0skip. Event-late is leading measured candidate for next repair; prioritize its own residual hold paths. All remote workflows completed at prior inventory.
Next:
- Quantify real setup headroom and final electrical/physical counts,prepare bounded hold repair for event-late's exact endpoints,then re-extract/retest. Reproduce full2/4 wrapper/source/SRAM/constraints and winning recipe in clean official GDS before any closure claim. No new dispatch,publication or phase tick.

## 2026-10-06: Codex (prepare guarded SRAM bit0 delay while event route runs)
Done:
- Event-late37546499438 remains active, so combined setup candidate selection awaits extracted results. Independently prepared local sram_addr_hold.tcl for exact recovery37547755184 branch net7589/place7589→SRAM A_ADDR[0]. Guards reject changed connectivity/masters, duplicate mutation and disconnected power; only SRAM sink is rewired behind one BUF1.
- Latest explicit main inventory: only event-late37546499438 running; queued list empty. Latest lint/test/docs/unit all passed. No new extraction/GL results; load-flat recovery remains failed and its downstream checks skipped. No dispatch or new physical timing claim.
- Subsequent main check: no running/queued workflows. Event-late route37546499438,extraction37551577987 and GL37551578053 completed successfully. Extracted setup WS0allcorners (no positive margin established); fast hold−0.014614976310ns,slow+0.104597222733,typical+0.030520697944. Timing still fails hold; full artifact/path and GL testcase audit pending. No official pass or phase tick.
- Five mock OpenDB/Tcl checks and115combined helper tests pass using cached OpenSTA Tcl interpreter via temporary launcher (standalone tclsh unavailable). Confirmed named driver/net in exact repaired netlist. No actual ODB mutation, measured delay gain, physical workflow integration or dispatch yet; no phase tick.
Next:
- Continue event-late monitoring; implement checkpoint-validated local physical insertion/STA integration before proposing publication or launch. Any BUF delay hypothesis must pass fresh all-corner timing, antennas, legal placement and routing. Current extra code/docs remain local.

## 2026-10-06: Codex (audit SRAM hold failure and prepare one-pass recovery)
Done:
- Audited failed artifact11450688351 from37546502664. Exactly1fast hold violation: lane0acc_addr[1]→SRAM A_ADDR[1],arrival0.946049ns/required0.979280ns,WS−0.0332313ns. Setup counts0allcorners; slow/typical hold positive.
- Prepared opt-in/defaultfalse post-antenna hold recovery: reject setup failures,one all-corner timing repair,independent antenna check,fresh three-corner timing,then existing DRT gate. No retries or relaxed constraints; downstream upload preserves follow-up evidence.108helper tests/workflow validation/diffcheck pass. Report PHASE2_LOAD_FLAT_HOLD_RECOVERY.md.
- Event-late37546499438 still active; its named step encompasses checks and DRT, so internal stage is not independently confirmed. Unit remaining RTL job in chip/L3/rotation tests; other two unit jobs passed. No new dispatch/publication or phase tick.
- User approved publication/launch. Committed CIcd9d22f/docs eb90c4d and pushed origin main; HEAD,origin/main and remote main independently match eb90c4d8ff7ee48b7714271a4dbe6cb19c1174c8. Launched load-flat bounded recovery37547755184 from source37533972946 with repair_postantenna_hold=true; queued. Existing event-late remains active. No unpushed commits; subsequent status note remains local.
- Latest main check: both event-late37546499438 and load-flat recovery37547755184 in progress in combined antenna/timing/DRT step; no independently confirmed internal stage. Unit37547743325 and prior37546482082 active. Latest docs37547743332,lint37547743341,test37547743337 passed. No new physical results or dispatch.
- Subsequent workflow check: load-flat recovery37547755184 failed its bounded repair gate. Fast hold improved−0.0332313→−0.0216314ns but remains negative; setup0allcorners,hold slow+0.188543/typical+0.0731607ns. Extraction37549226850/GL37549226991 skipped. Latest unit37547743325 passed; prior unit37546482082 and event-late37546499438 still active. No repeat dispatched; exact residual endpoints require artifact audit.
Next:
- Publish scoped CI/docs and launch source37533972946/bs-load-flat with repair_postantenna_hold=true after explicit publication authorization. Continue event-late/extraction/GL monitoring and evaluate actual routed timing.

## 2026-10-06: Codex (audit residual paths and verify local combinations)
Done:
- Downloaded/audited resync extracted37529099235:11reported violating slow setup entries all start U0TXMODEbit2, worst enddropped[14],WS−0.325228ns. Fast min report5violating entries end lane state/immediate and BSqueue; distinct from SRAM hold.
- Audited load-flat recovery37547755184: exactly1residual fast hold violation by metrics, now lane1acc_addr[0]→SRAM A_ADDR[0],−0.0216314ns. Originalbit1 target is not the remaining worst failure. A targetedbit0 delay experiment requires exact connectivity and fresh all-corner/antenna validation; no insertion performed.
- Created two local combined patches against frozenR4. Resync+event and resync+load each prove892points,pass21bit-clock tests,5chip tests and2048L2 clocks. Ideal-wire PERIOD probes10.119960/10.311445ns versus resync10.669182; areas41659.7958/41552.4060µm² versus41905.9494. Active→load query eventcombo6.795213vsresync7.115667ns,not whole-chip mode timing.
- Named verifier support prepared;110helper tests and diff check pass. Report PHASE2_RESIDUAL_TIMING_AND_COMBINATIONS.md. Main RTL/spec/physical choices unchanged; no publication or new dispatch. Older unit37546482082 now passed; event-late37546499438 remains active.
Next:
- Await isolated event extraction before selecting combined physical screen. Prepare guarded targetbit0 hold experiment against exact repaired checkpoint if pursuing load-flat. Keep live modes timed and require official full2/4 signoff; no phase ticks.

## 2026-10-06: Codex (load-flat route stopped at timing guard)
Done:
- Event-late37546499438 remains active in antenna/fresh timing checks; main unit37546482082 active. Latest lint37546482114,test37546482166,docs37546482128 passed.
- Load-flat37546502664 failed before detailed routing: after antenna repair fast hold WS fell+0.0236243→−0.0332313ns; slow hold+0.154009,typical+0.052975,setup0allcorners. Existing guard correctly refused DRT. Extraction37547207387 and GL37547207361 were skipped because their source route failed. This is a physical timing regression, not a source-provenance failure.
Next:
- Audit exact violating hold endpoints and saved antenna checkpoint before preparing any bounded hold-repair follow-up; do not bypass the guard or rerun unchanged. Await event-late result. No new dispatch or phase tick; best extracted setup remains−0.325228ns with negative fast hold.

## 2026-10-06: Codex (audit completed event screens and prepare guarded routes)
Done:
- Downloaded both candidates and their exact paired baselines using direct artifact API after standard download stalled. Both candidates match27expected source/config/info files. All-corner estimated setup/hold counts0; zero repaired GRT overflow. Event-late holdfast+0.0313302ns,slow slew8,fanout166,cap0all; load-flat holdfast+0.0236243,slow slew6/typical1,fanout160,capfast/typical1.
- Repaired baseline/event/load area508444/510233/509017µm² and demand233872/239415/239238. Physical tradeoffs do not establish an extracted timing win. Both qualify for isolated bounded routing. Full comparison in PHASE2_EVENT_SCREEN_AUDIT.md.
- Prepared routing options and exact patch/source guards for both, with named-patch regression.98helper tests,workflow-choice and diff checks pass. No publication/route dispatch or main hardware change.
- User approved publication. Committed CI666b5e9 and docs1411f26, then explicitly pushed origin main. Local HEAD,origin/main and git ls-remote main all equal1411f26d20a4b47d089b9f8492ff0b5532aad848. Launched event-late route37546499438(active) and load-flat37546502664(queued), both on that exact remote revision. Subsequent status note remains uncommitted; no commits await pushing.
Next:
- Obtain scoped approval to publish CI/docs and launch two isolated routes, then audit automatic extraction/GL. Resync remains best reviewed setup−0.325228ns but fast hold−0.008053ns; official timing still fails. No phase ticks.

## 2026-10-06: Codex (all main workflows completed)
Done:
- Explicit main queries for in_progress and queued both return empty. Event-late37533969613 and load-flat37533972946 completed successfully, including both paired baseline/candidate jobs. Resync routed GL37529099455 completed successfully. Latest main lint37533961193,test37533961246,docs37533961215,unit37533961312 all green.
- Diagnostic workflow success does not imply timing closure. Best currently reviewed extracted setup remains resync−0.325227853853ns with fast hold−0.008052669870ns. New screen artifacts await metric/path audit; no new extracted claim or phase tick.
Next:
- Audit the completed event/load artifacts and resync GL evidence, rank physical candidates, then prepare separately guarded routing for a qualifying candidate. No dispatch/publication in this check.

## 2026-10-06: Codex (publish approved event screens and read resync extraction)
Done:
- User approved separate prototype/tools,CI,docs commits, push and both event screens. Prototype/tools committed3bf11bb; publication in progress. Approval-review timeout on first compound command was resolved by a scoped retry; no rejection of task authorization.
- Main resync route37521491667 and extraction37529099235 completed. Extracted slow setup WS−0.325227853853ns; fast hold−0.008052669870ns, slow hold+0.145561455898ns,typical+0.043376747866ns. Setup fast/typical0. This is a closer diagnostic setup result than prior−1.385050ns, but both setup and fast hold still fail; no official pass.
- Matching routed GL37529099455 is active. Previous main lint/test/docs/unit all passed. Local resync million-clock comparison completed successfully.
- Published prototype/tools3bf11bb,CI3233de5,docs2b93d42 to main. Launched event-late37533969613 and load-flat37533972946 on exact2b93d42; both queued at verification, event-late matrix names confirmed. New main docs37533961215,lint37533961193,test37533961246,unit37533961312 active. No main hardware-input commits were pending before push. Subsequent status note remains local.
Next:
- Finish approved publication,launch bs-event-late and bs-load-flat independently and record run IDs. Download/audit resync extracted path families and hold endpoints before selecting a combination or repair. No phase ticks.

## 2026-10-06: Codex (prepare isolated event timing screens)
Done:
- Resync background terminal completed: results_million.xml contains1passing testcase, log reports1000000clocks/zero divergences,1103.64s. Session88060 no longer needs to run. Resync route37521491667 remains active in antenna/fresh timing checks; main lint/test/docs passed, unit active.
- Prepared existing RTL screen choices bs-event-late and bs-load-flat with independent concurrency, paired unchanged baseline, exact frozen2/4 source guards, timing-driven placement/all-corner repair and0ns margin. Direct-predicate regression stays local; no dispatch yet.
- All83helper checks pass, workflow inputs parse/validate, diff check passes. Added D-072 with general need and measured costs. Publication/launch needs scoped approval under AGENTS git rule; reviewed changes are in PHASE2_EVENT_TIMING_PROTOTYPES.md.
Next:
- Publish separate prototype/tools/CI/docs groups and launch the two approved isolated screens after scoped authorization. Audit completed physical evidence; no combined candidate or phase tick.

## 2026-10-06: Codex (prove and measure three event-path prototypes)
Done:
- Answered background-terminal question: session88060 is local Verilator resync RTL/model million-clock lockstep, latest900000clocks without reported divergence; final result pending.
- Implemented three isolated frozen2/4 patches outside main RTL. Module proofs pass892points for load-flat/event-late and818for sample-predicate. Each passes21bit-clock tests,5chip tests and2048L2 clocks.
- Identical-library slow PERIOD→RX-load probes: baseline13.808641ns/40667.3184µm²; load-flat12.391160/40740.4998; event-late11.697581/40591.0764; predicate13.980507/41529.5370. Prioritize first two; reject predicate physical spending on this evidence. These are local ideal-wire queries, not extracted WNS.
- Fixed verification fixture resource mismatch (BUGS72): regenerate Python tables from frozen specification without rewriting RTL. Regression plus existing helper suite81passed. Added named local verification support and detailed PHASE2_EVENT_TIMING_PROTOTYPES.md. No publication/new physical dispatch or checklist tick.
- Approved resync route37521491667 remains active in antenna/fresh-timing pre-route checks at latest inspection.
Next:
- Audit resync route/extraction/GL and finish local million-clock run. Prepare measured isolated physical candidates for event-late/load-flat; seek scoped publication approval only after concrete review. Preserve complete2/4 protocol floor,20ns and live configuration.

## 2026-10-06: Codex (rank further timing ideas during resync routing)
Done:
- Audited worst extracted slow path37499559422:41cell arcs total17.333846ns versus0.104522ns reported interconnect, excluding clocks/preceding3.502306ns launch time. Logic depth and loaded slow cells are concrete targets; this is one path only.
- Recorded six ranked hypotheses and proof/physical-validation requirements in PHASE2_TIMING_NEXT_IDEAS.md: direct sample predicates, late sample gating, flattened producer-load arbitration, prepared drop-counter prefixes, targeted cell/fanout repair and critical configuration-launch decode. No implementation, architecture adoption or new dispatch in this brainstorming pass.
- Fresh local million-clock resync comparison reached400000clocks without a reported mismatch; not a completed pass. Current isolated routing remains37521491667. No phase checklist boxes ticked.
Next:
- Prepare narrow equivalence/mapping experiments for top candidates while current route runs; evaluate combinations only after isolated physical evidence. Keep20ns,2/4,all protocol behavior and live writes intact. New report/status notes remain local.

## 2026-10-06: Codex (audit resync and prepare modified-RTL routing)
Done:
- Downloaded exact candidate/baseline37504886226. Fresh setup/hold counts0 all corners; fast hold+0.0379569ns; slow slew8→1; fanout162→160; cap0→2/1/2fast/slow/typical. Repaired area508444→509241µm²; demand233872→243504(+4.12%),overflow0. Exact27RTL/config/info fingerprints match frozen3393eea plus bs_resync.patch. Full audit in PHASE2_RESYNC_ROUTE_AUDIT.md.
- Prepared existing route workflow for bs-resync with expected fingerprints computed from trusted checkout+patch before artifact download, main-only exact run provenance, existing all-corner/antenna guards and saved source identity rechecked during extraction/GL. Added macro artifact payload to support downstream checks; pre-launch bug71 covered.77helper checks, workflow parsing and diff checks pass.
- Resync qualifies for diagnostic routing, not electrical signoff; no combined SRAM-buffer/CTS change, no extracted resync WNS and no new dispatch yet. Main hardware/config/spec remain unchanged.
Next:
- Publish validated route support under scoped git authorization, then route source37504886226/variantbs-resync and audit automatic extraction/GL. Fresh million-clock comparison is required before any eventual RTL adoption. Best prior extracted setup remains−1.385050ns; no phase boxes ticked.
- Continuation: repeated all77helper tests successfully and confirmed no main workflows running/queued. Started fresh resync million-clock RTL/model comparison locally (Verilator, session88060); result pending. Requested scoped approval for CI/docs commits, push and resync route because AGENTS.md reserves publication for the user. No publication or launch performed.
- User explicitly approved publication and launch. CI support committed as f0ab242; fresh local comparison reached200000/1000000 clocks without a reported mismatch so far (not a final pass). Preparing separate docs commit and approved push/dispatch; main hardware inputs remain unchanged.
- Published CI f0ab242 and docs8496fb8 to approved main remote. Dispatched resync route [37521491667](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37521491667), source37504886226/bs-resync; queued at first verification. Main unit37521483283,test37521483360,lint37521483275,docs37521483295 are active. Local resync lockstep reached300000/1000000 clocks, result pending. Hardware pending-commit log was empty before push; no official GDS launched or phase boxes ticked.
- Rechecked user's remote-push concern: git ls-remote and GitHub commits/main API both confirm remote main8496fb8314bf3030222915fd416d7d310c0c1d0d, matching local HEAD. Resync route37521491667 is now in progress on that exact revision. Only subsequent WORKLOG status notes remain uncommitted locally.

## 2026-10-06: Codex (restrict workflow monitoring to main)
Done:
- User directed main-only workflow monitoring. Branch-filtered inventory shows all recent main runs completed; none running/queued in the checked set. Resync37504886226 passed; margin37504890339 timed out; both routed GL runs and latest unit/lint/test/docs passed.
- Correction to prior unfiltered inventory: newly reported official GDS/compact runs were outside main and must not be treated as main advances or main evidence. Main's latest checked revision remains44700f3.
Next:
- Monitor/analyze main runs only until user changes scope. All originally awaited main workflows are finished, so their artifacts can now inform the2/4 official candidate decision. No new dispatch or phase tick.

## 2026-10-06: Codex (workflow check after remote advances)
Done:
- Earlier runs finished: CTS routed GL37502135732 success; margin37504890339 failure after80min step timeout. Completed margin log shows repair iterations813–821 with reported WNS0,2065targets and+0.0% area change; no useful final fresh timing result. Do not repeat global2ns margin blindly.
- GitHub now has newer revisions than local44700f3: official gds37515299060(a284f4c) in Build GDS; compact experiments37516794406(1784a49) route active, demos success, native_fabric failure; unit37516794383 active. Latest lint/test/docs passed. Prior compact37516278474(c26f520) failed native and route jobs. No checkout/history changes or new dispatches made.
- Current compact completed failure log is unavailable until its workflow finishes. Prior native failure log reports a Yosys tile-cone conversion subprocess failure; do not assume latest root cause matches without logs.
Next:
- Await current official/compact results and inspect exact new remote candidate before making hardware claims. Local checkout remains44700f3 with local documentation changes preserved. No phase boxes ticked; best earlier extracted setup remains−1.385050ns.

## 2026-10-06: Codex (investigate long margin screen)
Done:
- At18:40UTC, margin37504890339 has run~63min; baseline completed in22min33sec. Candidate's screen step started17:39:11UTC, with80min timeout (deadline~18:59:11UTC), job cap100min. GitHub refuses unfinished-job log retrieval; exact internal stage not independently confirmed.
- Identified likely explanation: global2ns repair margin can repeatedly target intrinsically zero-slack borrowing latch endpoints, the known D-032 limitation. This is a hypothesis pending completed logs, not evidence of useful continuing optimization. Selecting global margin should have accounted for that history.
Next:
- Respect user's wait instruction: allow bounded current run to finish, do not extend or relaunch. Inspect failure/success artifact and iteration progress to confirm whether margin is viable. Prefer genuine critical-cone shortening over trying to force positive margin on borrowing endpoints. No phase boxes ticked.

## 2026-10-06: Codex (resync screen completed; two workflows remain)
Done:
- Resync37504886226 completed successfully. Log reports fresh estimated setup WS0 all corners and hold fast+0.0379569ns, slow+0.227755ns, typical+0.100974ns after repair. Baseline setup0/hold+0.0360107,+0.238266,+0.103103ns. Estimated passes do not establish extracted improvement; full artifact audit pending.
- Both main unit runs passed; lint/test/docs green. Only margin37504890339(candidate active/baseline success) and CTS routed GL37502135732(simulation) remain running.
Next:
- Follow user's instruction to await all existing runs before selecting official candidate; launch no additional experiments. Audit full artifacts after completion. Best extracted setup remains−1.385050ns; no phase boxes ticked.

## 2026-10-06: Codex (official GDS readiness assessment)
Done:
- Verified main TT entry point is still phase0counter and info.yaml lists only it; real protocol experiments harden frozen R4. Dispatching unchanged main cannot measure current protocol timing improvements.
- Recorded official candidate requirements and diagnostic-to-official portability gaps in PHASE2_OFFICIAL_GDS_READINESS.md. SRAM ODB repair and placement/all-corner/reservation recipe do not automatically transfer to clean official synthesis. Current resync/margin screens still active.
Next:
- Prepare complete reproducible2/4 candidate, choose measured winning change after screen results, document any config-policy exception, then run official gds on exact candidate. No official dispatch, hardware adoption or checklist tick in this audit.

## 2026-10-06: Codex (active workflow inventory)
Done:
- Verified five workflows active: resync37504886226(both paired jobs), margin37504890339(candidate active/baseline passed), CTS routed GL37502135732, unit37504873739 on6847566 and unit37505008445 on44700f3. Unit model/Verilator jobs passed; each remaining Icarus job is in chip/L3/rotation tests. No queued workflows in this checked set.
Next:
- Audit completed timing candidates; unit duplication comes from successive code/docs pushes, not extra hardware variants. Official gds is not running. No phase boxes ticked.

## 2026-10-06: Codex (synthesize timing and protocol lessons)
Done:
- Audited claims, protocol scenarios, resource-floor decision and physical comparisons. Recorded latest22-case routed-GL evidence, exact failing extracted timing and bounded resync prototype evidence in CLAIMS with explicit limits.
- Main lessons: retain general protocol primitives and2/4 resource floor; optimize the common PERIOD→bit-clock→fabric-accounting cone; prefer extracted timing over estimated passes, electrical counts or cell count. Counter/prototype functional checks preserve behavior but do not establish physical speed.
Next:
- Audit resync/margin physical screens, reproduce winning changes on a complete2/4 candidate, and require official GDS all-corner timing plus physical and protocol checks. No phase boxes ticked; no new routed WNS claimed.

## 2026-10-06: Codex (SRAM routed GL completed)
Done:
- SRAM routed GL37499559483 completed successfully; downloaded JUnit verifies22cases,zero failures/errors/skips. Functional gate-level evidence without SDF; setup closure remains unproven.
- CTS GL37502135732 has started expanded simulation. Resync37504886226 and margin37504890339 each have baseline/candidate active in GRT/fresh timing stage. Latest main lint/test/docs passed; unit still active. No checked failures.
Next:
- Audit completed resync/margin screens when fresh reports appear. Best extracted slow setup remains−1.385050ns. No phase boxes ticked.

## 2026-10-06: Codex (estimate routed L3 runtime)
Done:
- At17:51UTC, SRAM GL37499559483 has run about56minutes and is still in expanded L3 simulation. Previous matching22-case GL37417248117 took56min41sec total. CTS GL37502135732 is pending behind it.
Next:
- Expect roughly an hour per run, with variation by netlist and runner; pending CTS starts after SRAM finishes. Simulation step timeout300minutes is a ceiling, not expected runtime. No new timing evidence or phase boxes ticked.

## 2026-10-06: Codex (publish and launch approved timing prototypes)
Done:
- User explicitly approved separate prototype/CI/docs commits, push to the exact Kanishk234 repository and both screen launches. Published66bc13d(prototypes),fa16d52(CI) and6847566(evidence/docs). No hardware inputs pending in origin/main..main; no main RTL/config/spec changed.
- Launched resync screen37504886226 and independent2ns margin screen37504890339, both gds-rtl-timing-screen on main. Each has its own unchanged baseline and isolated candidate. Main test/lint/unit/docs checks queued on6847566.
- SRAM routed GL37499559483 remains active; CTS routed GL37502135732 pending. Best actual extracted setup remains SRAM−1.385050ns; CTS−1.996169ns is worse. No phase boxes ticked.
Next:
- Audit fresh resync/margin timing, electrical counts, area and routing overflow. Advance only measured qualifying candidates with matching modified-RTL provenance; then demonstrate complete2/4 official-GDS timing before the3/6 attempt.

## 2026-10-06: Codex (implement structural timing prototypes at 2/4)
Done:
- Recorded user-directed2/4 official closure first, then3/6 if area permits (D-070). Prepared isolated drop_qual.patch, bs_resync.patch and bs_csa.patch against3393eea; no main RTL/spec/config changed. D-071 records general need, behavior preservation and costs.
- Module equivalence passes: fabric97points atN1/5/6/7/9/16, resync893points andCSA868points; equiv_simple plus induction closes at step1 withseq2 cap. Affected unit tests7/7fabric and21/21bit-clock each; all three pass5/5chip tests and2048-clock L2 withzero divergences. Corrected local fixture/include bugs68/69; reruns pass. Reusable verifier proof passes including a path with spaces.
- Local mapped slow PERIOD→RX-load delay: baseline13.808641ns, resync10.669182ns, CSA14.636085ns. Resync module area+1238.6304µm² (~3.05%); parallel fabric delay1.324727ns versus1.254606baseline and more area. Prioritize resync and independent2ns repair-margin screen; other variants remain lower priority. Ideal-wire module probes are not routed WNS.
- Parameterized existing RTL-screen workflow with named isolated trials and exact source/patch guards;58helper tests, patch/proof/JUnit/workflow checks and git diff --check pass. Publication and dispatch have not occurred. CI code/patches and documentation are reviewable locally.
- CTS extraction37502135749 completed but regresses: slow setup−1.996169ns/fast hold−0.004410ns. SRAM remains best measured at−1.385050ns with positive hold all corners. No phase boxes ticked.
Next:
- Publish validated prototype/CI changes with scoped git authorization, then dispatch bs-resync and setup-margin separately. Measure overflow and fresh timing; route only qualifying candidates with explicit modified-RTL provenance, then build a clean reproducible2/4 official-GDS candidate. Other prototype sessions completed; no local proof/test process remains active.

## 2026-10-06: Codex (high-impact timing closure plan)
Done:
- Recorded prioritized cone-level changes and exact official-flow acceptance in docs/reports/PHASE2_TIMING_CLOSURE_PLAN.md. Main candidates: parallel source/drop qualification, timer arithmetic shortening, counter late-enable rewrite, critical-cone locality and positive pre-route optimization margin.
- Verified frozen spec remains3lanes/6units, while current−1.385050ns extracted result is2lanes/4units. D-049 is experiment approval, not final adoption; closure must be demonstrated on the adopted full design via official gds, not custom diagnostics.
- Read RTL and prior extracted-path evidence without touching model code or hardware. Newest SRAM artifact download63574 and counter matched-baseline download80502 remain active; no new prototype or timing gain claimed.
Next:
- Complete routed path/baseline audit, prepare isolated source-selection and arithmetic changes preserving cycle behavior, then measure before combining. Require clean reproducibility and official full-flow evidence. No phase boxes ticked.

## 2026-10-06: Codex (parallel analysis and new SRAM extracted result)
Done:
- Retrieved completed extracted diagnostic37499559422: SRAM trial slow setup WNS−1.385050335848ns (previous−1.731802306133ns, improvement0.346751970285ns). Fast/typical setup0; hold positive all corners: fast+0.050187910803ns, slow+0.247750382777ns, typical+0.123471236730ns. Setup still fails; no signoff claim or checklist tick.
- Began counter matched-baseline path comparison while CTS routing and SRAM GL run. Candidate artifact available; matched-baseline download in progress. Raw reports remain in/tmp.
Next:
- Inspect remaining SRAM setup paths and complete counter comparison; prioritize the next isolated trial based on extracted critical cones. Audit CTS and SRAM routed GL completion.

## 2026-10-06: Codex (workflow status check after SRAM routing)
Done:
- SRAM route37490897034 completed successfully. Its automatic extracted-timing37499559422 is extracting/reporting all-corner timing; routed GL37499559483 is running expanded L3 simulation.
- CTS follow-up37496347122 remains in antenna/fresh-timing/DRT step. Main54388c8 lint/test/docs passed; unit37496335870 RTL chip tests remain active, other two jobs passed. No failures observed in checked runs.
Next:
- Analyze SRAM extracted timing when available and verify routed GL. Inspect CTS fresh repair/route outcome. No new WNS yet (latest−1.731802ns); no phase boxes ticked.

## 2026-10-06: Codex (publish approved CTS follow-up)
Done:
- User explicitly approved the push. Published CI commit54388c8 to main at the authorized repository; no hardware files were pending in origin/main..main.
- Dispatched [37496347122](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37496347122), gds-placement-route with source_run_id37486833508/source_variantcts. Queued at dispatch; performs one bounded all-corner hold repair and gates before routing. SRAM route37490897034 remains in progress.
- Main lint/test/unit/docs checks started for54388c8. No new extracted timing result; WNS remains−1.731802ns. No checklist boxes ticked.
Next:
- Audit the CTS fresh repair gates and SRAM route completion, then extracted timing and routed GL results. Keep the 20ns constraints unchanged.

## 2026-10-06: Codex (bounded CTS follow-up and completed counter audit)
Done:
- Counter screen [37489333139](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37489333139) completed. Downloaded candidate artifact: fresh estimated setup WS0/count0 all corners; hold fast+0.0234049ns, slow+0.203146ns, typical+0.0996158ns/count0. Slow slew9, fanout158 each, cap0; repaired area508,489µm²,33,077instances. Baseline slow slew8/fanout162; electrical results are mixed, and no routed improvement is established.
- Extended existing placement-route workflow with CTS source provenance and actual cluster-size8 validation. Exactly one additional all-corner repair precedes fresh setup/hold gates, antenna checks, and DRT. Source-variant concurrency permits an independent CTS experiment while SRAM routing continues. No RTL or timing constraints changed.
- 39 timing/route/GL/extraction helper tests pass; workflow YAML parses and git diff --check passes. Local CI commit54388c8 created. Automatic approval review rejected its push to main because exact push authorization was not recognized and AGENTS reserves pushes for the user. Requested explicit approval; no push or CTS dispatch occurred.
- SRAM route37490897034 remains in its antenna/fresh-timing/DRT step. Actual extracted WNS remains−1.731802ns; no checklist boxes ticked.
Next:
- After exact push authorization, publish54388c8 and dispatch placement-route with source_run_id37486833508/source_variantcts. If the single follow-up repair still fails, refuse routing and inspect its fresh evidence. Analyze SRAM extraction when available. Counter needs route evidence before any timing claim.

## 2026-10-06: Codex (analyze completed clock-clustering artifact)
Done:
- Downloaded CTS37486833508 artifact: fresh all-corner setup counts0; fanout4 each (baseline162), slew0 each (baseline slow8), cap0, final GRT overflow0. Area514,551µm²,33,464instances;31hold buffers in last repair. Estimated fanout improvement is substantial despite failed hold gate.
- Only estimated hold failure is fast−0.00424344ns, `_46919_`→SRAM macro. Cluster8 is promising for a bounded hold-repair follow-up, but cannot route as-is. Revised assessment from hold-only headline; no extracted gain claimed.
- SRAM route37490897034 still active. Counter screen37489333139 baseline completed, variant active; timing benefit not yet known. Million-clock functional verification already passed.
Next:
- Prepare one bounded all-corner hold follow-up for CTS with unchanged constraints; repeat fresh per-corner gates before any route. Audit SRAM extraction/counter variant once complete. No phase boxes ticked; actual WNS remains−1.731802ns.

## 2026-10-06: Codex (parallel experiment progress)
Done:
- CTS37486833508 completed diagnostic execution. Cluster8 estimated setup0, fast hold−0.00424344ns; matched baseline fast hold+0.0360107ns. This variant regresses hold and does not qualify for routing without repair; workflow success is not timing gate success.
- Counter prototype fresh million-clock L2 completed:1,000,000clocks,zero divergences,JUnit1case0failures/errors,956.26s underVerilator. No full-chip formal claim.
- SRAM-buffer route37490897034 active in antenna/timing/DRT step. Counter screen37489333139 both jobs active in GRT/fresh timing step. No new extracted WNS result.
Next:
- Inspect CTS electrical/fanout artifact before deciding whether any hold-repaired follow-up is worthwhile; do not promote failing hold variant. Audit counter results and SRAM extracted timing on completion. Actual WNS remains−1.731802ns; no phase boxes ticked.

## 2026-10-06: Codex (continue actual-path-directed timing repairs)
Done:
- Audited downloaded37417248079 extracted artifact:119slow setup violations,4fast hold;115reported failing path pairs start atU0PERIOD word4bit10, worst endsdropped[31]. Fast hold paths are three lane-slot→execution-control and oneU0mode→RXsst[0]. Counts/electrical/path details recorded in PHASE2_INDEPENDENT_TIMING_SCREENS.md.
- Confirmed two prepared slew targets survive as worst slow slew violations; dispatched CTS37486833508, lane37487199839, SRAM37487199871 as independent paired screens. No main RTL/config/spec changed.
- Prepared drop_counter.patch targeting late control in saturating8-bit DROPPED update. Proved98module equivalence points each atN1/5/6/7/9/16 with induction;7fabric tests and5chip tests pass. Fresh2048-clock L2 passes underVerilator and Icarus. Shared helper14tests and workflow parse/diff checks pass. Prototype only, no measured timing gain yet.
Next:
- Published CI b58fca0 and docs765b443; dispatched drop-counter37489333139, currently running. Million-clock L2 is running locally (session63351), reached700,000clocks without divergence. Earlier diagnostic parser session95080 was interrupted after a slow report regex; completed audit used bounded per-path parsing instead.
- Buffer screens37487199839/37487199871 completed successfully; fresh estimated setup0 and fast hold+0.0442855/+0.051976ns versus baseline+0.0364431ns. Downloaded variants and matched baseline: slow slew3baseline/3lane/1SRAM, alloverflow0, fanout162/cap0. Lane has no additional slew-count improvement; SRAM is stronger. Extra unchanged repair alone reduces8→3. Downloads completed; CTS37486833508 still running.
- Selected SRAM-buffer for separate guarded routing from37487199871; extended existing placement-route dispatch to bounded placement/lane/SRAM artifacts, preserving default original source. Twenty-eight gate/GL/extraction checks and workflow parsing pass. Updated in-progress PHASE2 summary with actual−1.732ns result and remaining gates.
- Published guarded routing CI fea46ed and milestone docs30d1aa9. SRAM-buffer route37490897034 dispatched and running with source37487199871/source_variant=sram; automatic extraction/L3 enabled after success.
- Collect CTS/counter metrics and complete million-clock comparison; no new extracted WNS yet. Actual setup remains−1.731802ns and hold−0.035371ns; no phase boxes ticked. Fullsignoff and resource adoption still open.

## 2026-10-06: Codex (new-day completed workflow check)
Done:
- No workflows running or queued. Latest nightly37476592630, main test/lint/unit/docs, placement route37412965189 and extraction37417248079 all successful.
- Routed GL37417248117 completed successfully; downloaded JUnit records 22 cases, 0 failures, 0 errors and 0 skipped. Functional netlist evidence only, not timing signoff.
Next:
- Actual setup remains−1.731802ns and fast hold−0.035371ns. Audit extracted critical/electrical paths and choose prepared isolated repair comparisons. No phase boxes ticked.

## 2026-10-06: Codex (workflow inventory explanation)
Done:
- Verified sole active run is l3-placement-routed-gl37417248117, expanded netlist simulation; none queued. Enumerated registered GDS workflows and distinguished completed screens, prepared manual experiments, route/extraction pipeline and historical diagnostics. GitHub workflow-list active means enabled, not running.
Next:
- Audit L3 result and extracted critical paths, then choose prepared experiments. Latest actual slow setup−1.731802ns and fast hold−0.035371ns remain failing. No phase boxes ticked.

## 2026-10-06: Codex (placement route extracted timing result)
Done:
- Placement route37412965189 succeeded. Automatic extraction37417248079 succeeded and printed fresh all-corner timing: slow setup−1.731802306ns, fast/typ setup0; fast hold−0.035371207ns, slow+0.115164992ns, typ+0.012006063ns. Timing still fails; diagnostic workflow success is not signoff.
- Slow setup improves3.898297ns versus previous actual−5.630099ns, about69.2% less deficit. This compares complete flows, not an isolated cell change.
- Automatic gate-level L3 run37417248117 is active in expanded simulation; latest main unit/test/lint/docs all successful. Timing/path/electrical artifact details still need audit.
Next:
- Audit extracted critical paths/counts/electrical reports to select prepared experiments; fast hold repair must also survive extraction. Inspect L3 JUnit on completion. No phase boxes ticked.

## 2026-10-06: Codex (workflow progress at 05:07 UTC)
Done:
- Two active workflows, none queued: route37412965189 (~50min since job start) in combined antenna/timing/DRT step; unit37413767879 (~40min) in Icarus chip/L3 tests, with Verilator and module-unit jobs successful.
- Other three previously active unit workflows completed successfully; latest test/lint/docs successful. No new extracted timing run/result available.
Next:
- Monitor route and automatic downstream extraction/L3; actual WNS remains −5.630099ns until new extraction. No phase boxes ticked.

## 2026-10-05: Codex (workflow progress at 04:33 UTC)
Done:
- Active placement route37412965189 started04:17UTC (~16min elapsed); setup/source download/provenance/image stages complete. Combined antenna/fresh-STA/DRT step active. Live job-log API returns404 while job is active, so exact router iteration is unavailable; do not claim DRT has started.
- Four active unit workflows:37413767879 and37413470130 in Icarus chip/L3 and Verilator suites;37413151906 and37412962050 have Verilator/unit successful, Icarus chip/L3 still active. All four unit jobs passed. No queued workflows.
Next:
- Monitor route completion/gate, then automatic extraction and routed L3. No new WNS evidence or phase boxes ticked.

## 2026-10-05: Codex (three independent follow-ups and phase exit audit)
Done:
- Prepared manual gds-cts-cluster-screen (timing-placement baseline vs sink-cluster8), gds-lane-slew-screen (oneBUF4 on slot-write decode), and gds-sram-slew-screen (oneBUF4 on SRAM-enable branch). Buffer trials reuse exact37408506116 checkpoint and move only audited loads; no combined changes or main hardware edits.
- Added fail-closed source/connectivity/supply/duplicate guards and reused established after-read→split→DPL→repair hook. Baselines follow identical DPL/repair sequence without connectivity mutation. Twenty-three helper/Tcl checks passed; three workflows/embedded Python parsed; diff checks passed. No physical success claimed from mocked tests.
- PHASE2_EXIT_EVIDENCE_AUDIT.md records all exit items, historical evidence and required final-candidate evidence. Area/budget is first unchecked item; reduced counts adoption, actual all-corner timing and full selected-candidate signoff remain unresolved. No boxes ticked.
Next:
- Publish prepared manual workflows, but select dispatches after current routed/extracted evidence identifies surviving issues. Route37412965189 remains active in antenna/timing/DRT step. Automatic extraction/L3 already published; preserve20ns, constraints and D-066.

## 2026-10-05: Codex (parallel electrical/path/budget audit)
Done:
- Completed requested parallel audit; PHASE2_PLACEMENT_PARALLEL_AUDIT.md records reproducible artifact/netlist/DEF/STA evidence and next controlled experiments.
- All 162 fanout violations are clk_regs clock leaves (limit8, loads10–17). Eight slew pins belong to two NOR4_1 nets: lane0 slot-write decode driving five remote loads (443–461 µm), and SRAM-enable arbitration feeding one load (516 µm). Capacitance violations zero.
- Mapped old logical failing U0modecfg→dropped26 and new top carrier-config latch path; retained D-066 timing and did not infer closure from bounded pre-route reports.
- Budget audit: total instance utilization56.3425%, standard-cell51.3216%; gross gap to60% is33,006.2 µm², not guaranteed usable capacity. Reduced resource counts remain unadopted; no phase boxes ticked.
Next:
- Current placement route 37412965189 was active in its antenna/timing/DRT step at query. Let automatic extracted timing and L3 measure the exact route. If electrical issues survive, test one data-net buffer split or separate CTS-clustering experiment; no constraint relaxation or premature hardware change.

## 2026-10-05: Codex (current WNS/progress snapshot)
Done:
- Latest run query: placement route 37412965189 is active; no newer extracted timing run/result exists. Main test/lint/docs are green; unit runs remain active. Latest actual extracted slow setup is −5.630099 ns (37398296289); placement all-corner global-route estimated setup is 0, hold positive (37408506116). Keep these evidence levels separate.
- Correction to earlier commentary claiming all six screens had zero overflow: report correctly records input-decode final logged overflow 5 and cached-input 37; placement, RX, pad and load-select have zero. This reinforces deferring cached/stateless input changes.
Next:
- Diagnose eight slow slew and 162 fanout violations from existing reports, compare critical latch paths against old routed failure, and audit resource budgets while routing runs. Automatic extraction and L3 are published for successful route completion. No phase boxes ticked.

## 2026-10-05: Codex (automatic placement-route downstream evidence)
Done:
- Routing continuation 37412965189 is active; first check showed setup complete and source-artifact download in progress.
- Prepared gds-placement-extracted-timing and l3-placement-routed-gl with automatic workflow_run triggers after successful main-branch gds-placement-route completion, plus manual dispatch fallback. Both select the triggering route ID and download that exact artifact.
- Extraction requires a completed zero-router-DRC checkpoint and records fresh three-corner extracted reports; negative timing remains diagnostic evidence. Functional GL validates saved route/netlist/constraints/source policy and uses pinned Tiny Tapeout Icarus 13, SRAM models and existing expanded L3 tests; no SDF timing claim.
- Twenty-eight saved-route/extraction/gate checks pass; both workflows and embedded Python parse; diff check passes. No hardware/spec/config input changes or phase boxes ticked.
Next:
- Publish these downstream workflows before route completion; monitor antenna/timing guard and DRT. If routing succeeds, automatic extraction and L3 start; audit artifact reports/JUnit before claims. If routing fails, fix the actual cause without launching downstream jobs on an incomplete checkpoint.

## 2026-10-05: Codex (all-corner placement audit and guarded routing)
Done:
- All-corner repair 37408506116 completed successfully; no active workflows at progress query. Placement setup/hold violation counts zero in all corners, hold +36.01/+238.27/+103.10 ps fast/slow/typ. Baseline slow setup remains −0.274897 ns.
- Audited downloaded area/electrical/path evidence and updated PHASE2_INDEPENDENT_TIMING_SCREENS.md: 508,444 um² instance area, 8 slow slew and 162 fanout violations remain. Zero setup slack is not positive margin or extracted timing closure.
- Prepared guarded artifact continuation through antenna checks/repair, fresh per-corner STA and DRT only on passing timing/antenna. Thirty-two helper tests and workflow/embedded-Python/diff checks pass. Actual saved placement config verified, not inferred from repair config where placement keys are omitted.
- No main hardware, constraints or spec change; no phase boxes ticked.
Next:
- Publish and dispatch gds-placement-route, audit post-antenna gate and detailed-route result; then run extraction and gate-level verification on that exact route. Existing extracted setup remains −5.630099 ns until a new routed measurement exists.

## 2026-10-05: Codex (timing screens compared; all-corner repair follow-up)
Done:
- Audited logs for all six paired screens; report PHASE2_INDEPENDENT_TIMING_SCREENS.md records fresh before/after slow setup, fast hold and final logged GRT overflow. Baselines reproduce exactly. Timing placement is strongest no-storage follow-up, with setup WS 0 and fast hold −0.0045709 ns.
- Prepared independent placement-multicorner screen to address fast hold; all three repair corners load together, while every before/after STA invocation remains single-corner. Existing helper defaults remain slow-only. Fourteen helper tests, workflow YAML and diff checks pass.
- Only modified file at user query was WORKLOG.md from completion audit. Previously tracked pad/RX background simulation terminals returned exit 0; no cancellation needed. No main hardware/config/spec edits or phase boxes ticked.
Next:
- Publish and dispatch the matched all-corner repair screen, then audit hold/setup, area and electrical checks before detailed routing. Extracted timing remains failing at −5.630099 ns.

## 2026-10-05: Codex (workflow completion audit)
Done:
- Queried 45 recent runs and separately all in-progress/queued/waiting runs. No workflows remain active, queued or waiting.
- All six independent screens completed successfully: RX 37399927459, pad-mux 37400509726, load-select 37403723129, input-decode 37403722954, cached-input 37403723111 and timing-placement 37403722938.
- Latest main test/unit/lint/docs and routed L3 37398304113 are successful. Older branch repair failure 37380322860 is the already-recorded BUGS #66, followed by a successful corrected run.
- No phase boxes ticked; diagnostic success is not timing closure.
Next:
- Extract and compare all six paired timing/area/overflow results, then choose the next routed experiment from evidence.

## 2026-10-05: Codex (four additional independent timing screens)
Done:
- Prepared isolated load-select, stateless input-decode, cached-input and timing-driven-placement comparisons against frozen 3393eea. Each workflow has its own unchanged baseline; main hardware, 20 ns clock and density 56 remain unchanged.
- Load-select: Yosys proved 98 equivalence points at each N=1/5/6/7/9/16. Input-decode: 13 equivalence points proved. Each RTL variant, including cached-input, passed five chip tests and a fresh 2,048-clock L2 comparison with zero divergences.
- Cached-input exhaustive bench passed all 1,024 A/S index pairs in full/lean and latch/flop configurations. Whole-chip Yosys hierarchy/proc/check passed after fixing prototype clock visibility (BUGS #67). Added storage costs 192 latch bits on R4; measurement only, adoption pending evidence (D-069).
- Shared helper/Tcl suite passed 40 checks; all four workflows parsed. RX million-clock L2 completed with zero divergences. Pad million-clock comparison remains separate.
- No phase boxes ticked. Latest extracted slow setup remains −5.630099 ns; new screens have no measured timing result yet.
Next:
- Published scoped CI 67e3f8c and docs b7dd8f7 with explicit user approval for this remote. Dispatched load-select 37403723129 (in progress), input-decode 37403722954 (queued), cached-input 37403723111 (queued), timing-placement 37403722938 (queued). Each has an independent baseline. RX 37399927459 and pad 37400509726 are now completed successfully; their timing metrics still need audit. Routed GL 37398304113 also completed successfully; inspect its artifact before recording case counts.
- Audit area, global-route overflow and fresh all-corner timing before selecting changes for detailed routing. No timing closure claim follows from workflow success.

## 2026-10-05: Codex (independent parallel pad-selection trial)
Done:
- Prepared a second isolated exact-3393eea tree; only trw_pins.v changes, verified by byte comparison. Persisted parallel_pad_mux.patch preserves owner read/write/reset, invalid-owner behavior and A-before-N selection. RX change is absent from this variant.
- Yosys equiv_make/equiv_simple/equiv_status -assert proved all 83 pad-module equivalence points for both NU4 (candidate) and NU6 (default). Randomized 1,500-clock owner/output scoreboard passed; archived candidate chip suite passed 5/5, including UART loopback. Fresh million-clock pad L2 started, not yet complete.
- Prepared independent gds-pad-mux-screen baseline/pad-mux matrix using the same shared helper and flow settings as RX; no main hardware/spec/config edits. All 39 helper/Tcl checks pass; YAML/embedded Python/diff checks pass.
- Existing RX screen and routed protocol verification still active at check; fresh RX L2 reached 700,000 clocks with zero reported divergence. No phase boxes ticked or new timing gain claimed.

Next:
- Published CI 9e38669 and separate docs b355b48; independent pad screen 37400509726 is running alongside RX screen 37399927459. Compare both RTL ideas separately before combining or routing. Fresh RX L2 reached 800,000 clocks without divergence; pad million-clock L2 is active. Inspect fresh slow setup/fast hold, area, overflow and electrical evidence.

## 2026-10-05: Codex (isolated RX comparison trial and matched physical screen)
Done:
- Rebuilt exact candidate 3393eea in isolated baseline/variant trees; applied persisted rx_sample_factor.patch with zero fuzz. Byte comparison confirms trw_pin_rx.v is the only changed hardware file. Main src/config/spec remain unchanged. Separate START/S_SAMP zero comparisons preserve the existing sample event and timer arithmetic.
- Fresh RX suite with current live-reconfiguration case passed 16/16 for FULL0 and FULL1 under Icarus. Yosys equiv_make/equiv_simple/equiv_status -assert proved all 275 default-FRAC8 equivalence points between the exact baseline and RX variant (matched-state module equivalence; not physical timing). Fresh million-clock L2 on exact variant passed 400,000 clocks so far and remains active; new million-clock result is not yet claimed. Archived candidate chip suite passed 5/5 including UART loopback. An initial current-main chip harness attempt used the main selector map and was unsuitable for this reduced candidate; only the matching candidate suite is acceptance evidence.
- Prepared gds-rx-compare-screen matrix for baseline/rx-factor with identical 20 ns, density56, GRT.16/region reservation/no-mirroring, slow repair and signoff constraints. It stops at unique GlobalRouting, rejects unexpected DRT/missing checkpoint views, then runs fresh independent before/repair/after corner reports. No full hardening/physical signoff claimed by this screen.
- All 39 helper/Tcl checks passed; workflow YAML/embedded Python and diff checks passed. No phase boxes ticked.

Next:
- Published CI ec076b7 and separate docs 652167d; matched screen 37399927459 running. Inspect timing/area/overflow/electrical evidence, finish L2, then route only a justified surviving trial. Actual extracted branch WNS remains −5.630099 ns; routed protocol 37398304113 still active.

## 2026-10-05: Codex (high-leverage WNS brainstorming)
Done:
- Reviewed archived mapped/routed cone, exact R4 RTL, prior isolated RX compare/pad mux prototypes, and fabric drop contract without reading model implementation. Ranked logic-depth reductions before further generic buffering: RX compare factoring, parallel pad owner mux, narrow late-control/counter optimization, critical-cone locality, and optional stored predecodes requiring contract/cost review.
- Recorded evidence, limits and acceptance criteria in PHASE2_GDS_EXPERIMENTS.md. Earlier local gains 1.5903/1.3282 ns are not additive or routed predictions. No candidate changes or phase boxes ticked.

Next:
- Audit new extracted paths and pick one isolated RTL trial; preserve 20 ns, live config, feedback, same-cycle DROPPED and fast hold checks. Await independent routed L3 result.

## 2026-10-05: Codex (new extracted timing measured)
Done:
- Extraction 37398296289 completed successfully as a diagnostic. Completed job 112059433306 prints actual slow setup WS −5.630099213 ns, fast/typ setup WS0; fast hold −0.024958369 ns, slow/typ hold +0.153200346/+0.030348946 ns. Timing still fails. Previous routed slow WNS was −6.178462361 ns; new route improves worst setup by ~0.548363 ns across the full branch/follow-up physical experiment, not an isolated single-change attribution.
- Final routed protocol 37398304113 remains active in its expanded simulation step after artifact/netlist validation and simulator setup passed. No new protocol pass or phase boxes claimed.

Next:
- Audit detailed extracted critical paths/electrical reports and hold failures, retain the 20 ns/spec contract, choose a different controlled optimization if needed; inspect final protocol result.

## 2026-10-05: Codex (branch routing completed; extraction and protocols dispatched)
Done:
- Routing 37390375337 completed successfully (job 112033753464), 23:46:20–00:50:35 UTC (~64 minutes). Downloaded completed log: final router violations 0 at 00:49:41; antenna net/pin violations 0 at 00:49:47. Terminal wirelength 1,918,723 µm. These are router results, not full physical signoff.
- Dispatched guarded hotspot extraction and final routed L3 workflows for new route 37390375337 on published helpers; each validates the saved final checkpoint/artifact. No new WNS or functional pass claimed yet. Latest main test/lint/unit/docs remain green. No phase boxes ticked.

Next:
- Inspect extracted multicorner setup/hold/electrical results and final routed protocol JUnit independently. Actual prior extracted WNS remains −6.178462 ns until the new measurement completes.

## 2026-10-05: Codex (branch DRT status check)
Done:
- Checked DRT 37390375337: job 112033753464 acquired runner at 23:46:20 UTC; setup, artifact downloads, provenance validation and image build passed. Detailed-routing step active; final artifact upload pending. No terminal DRC/antenna or extracted timing result available.
- Latest main test 37390367648, lint 37390366937, unit 37390366738 and docs 37390366560 all passed. No phase boxes ticked.

Next:
- Audit final routing state after completion, then run fresh extracted timing and routed protocol verification. Actual extracted WNS remains −6.178462 ns until a new completed result is measured.

## 2026-10-05: Codex (branch follow-up gates passed; routing continuation)
Done:
- Downloaded and audited successful follow-up 37386510229: final fresh setup WS/WNS 0 ns and setup/hold count 0 at all corners; hold WS fast/slow/typ +0.0649927/+0.333241/+0.158755 ns; antenna nets/pins 0. Electrical still open: slew 0/4/1, fanout203, cap0. These are estimated gates, not extracted timing.
- Added explicit branch-followup artifact/root selection to owned DRT workflow/helper with successful provenance and branch flags required. Kept all existing DRT timing/antenna/config gates. Updated routed L3 validator to read the correct follow-up repair config when present. No hardware source changes.
- Helper suite 35 passed including both checkpoint roots; workflow YAML/embedded Python/diff checks pass. No phase boxes ticked.

Next:
- Published CI 2c420f7 and separate docs 28fb3ea; controlled DRT 37390375337 dispatched with repair 37386510229 and explicit follow-up selection, queued at check. Inspect terminal router DRC/antenna, then fresh extraction and protocol verification. Actual extracted WNS remains −6.178462 ns until measured on this new physical result.

## 2026-10-05: Codex (bounded branch follow-up prepared)
Done:
- Traced matched _49012_→_47080_ reports: fresh post-resizer setup slack −0.309102 ns precedes antenna repair; post-antenna −0.280528 ns. This supersedes attributing the deficit solely to antenna repair. Both paths traverse the inserted BUF4; no extracted benefit established.
- Added separate critical-branch-followup workflow to repair the measured post-antenna branch checkpoint once with no reinsertion, mirroring disabled, identical 20 ns/signoff/zero-margin constraints and fresh corner/antenna gates. Output stays in runs/branch-followup, retaining original input state. Workflow validates completed branch provenance. No DRT launch included.
- All 34 helper/Tcl checks pass; YAML/embedded Python/diff checks pass. Follow-up guards reject mismatched source, missing branch/no-mirror provenance, dirty antenna and reinsertion. No phase boxes ticked.

Next:
- Published CI 6cd9287 and separate docs 8afdbd0 using ongoing user permission; follow-up 37386510229 is in progress. Judge fresh final gates; if setup remains negative, reject checkpoint and investigate a separate RTL logic optimization instead of repeating the same repair.

## 2026-10-05: Codex (corrected repair completed and routed protocols passed)
Done:
- Corrected branch repair 37381107529 completed successfully (job 112003036121). Log confirms real branch insertion, no estimated repair setup/hold violations and terminal antenna repair 0 violations. Downloaded gate artifact: post-antenna estimated slow WNS −0.280528 ns / 6 setup violations; fast/typ setup pass, all hold pass (+0.0503921/+0.281459/+0.132105 ns). Gate false, so no DRT dispatched. No extracted improvement claimed.
- Final routed protocol run 37376481257 passed; downloaded JUnit results_l3_gl.xml has 22 cases, 0 failures/errors/skips. This verifies the previous routed netlist, not the new branch trial, and includes no SDF timing claim.
- Latest main lint 37381099916, test 37381100012, docs 37381100021 and unit 37381099885 all passed. No phase boxes ticked; actual extracted setup WNS remains −6.178462 ns.

Next:
- Reject this branch checkpoint for DRT at current gates. Diagnose post-antenna regression (_49012_→_47080_/79/78, _49036_→_48163_/66/64), then choose a separate controlled repair; preserve required constraints.

## 2026-10-05: Codex (critical branch container dependency fix)
Done:
- Diagnosed failed repair 37380322860 from job 112000338612: pinned container has no awk; wrapper aborted before OpenROAD repair. No new timing result. Logged bug #66.
- Replaced awk with Bash built-in loops and explicit one-read guard. Restricted-PATH wrapper regression excludes awk and confirms insertion ordering and malformed-script rejection; complete helper suite 27 passed, shell/diff checks passed.
- Latest lint 37380313880, docs 37380313792 and test 37380313782 passed. Unit 37380313735 and final routed L3 37376481257 still active at initial check. No phase boxes ticked.

Next:
- Published CI 3fd67f0 and docs 90e20a2 using explicit user authorization; fresh corrected repair 37381107529 is in progress. Inspect real OpenDB execution and per-corner gates before DRT/extraction. WNS remains −6.178462 ns.

## 2026-10-05: Codex (authorized branch trial published and dispatched)
Done:
- User explicitly authorized running the prepared publication script, overriding AGENTS.md Git restriction for this action. Initial opaque-script approval review timed out without execution; explicit commands succeeded. Published CI 092cd76 and separate docs 0988430. Hardware-change log for origin/main..main over src/info.yaml/macro was empty before push.
- Reconfirmed all 27 local helper/Tcl checks passed. Dispatched critical-branch repair 37380322860 on 0988430 with exact source/screen IDs and disabled mirroring; runner acquired and dependency setup active (job 112000338612). Final routed L3 37376481257 still active; unit 37376426740 passed.
- No new timing result or phase boxes ticked. Actual extracted setup WNS remains −6.178462 ns and fast hold −0.020809 ns.

Next:
- Inspect actual branch insertion, legalization, estimated multicorner/electrical and antenna results. If guarded gates pass, continue DRT and extraction before claiming improvement; audit final L3 result independently.

## 2026-10-05: Codex (repair-hook validation and complete hold audit)
Done:
- Added real wrapper execution tests for insertion ordering and rejection of missing/duplicate ODB reads. All 27 helper/Tcl tests passed; diff checks passed.
- Audited all four fast extracted hold failures and mapped actual routed netlist signals: U0 word13 bits12/14/3 to TX ct[12/14/3] (−20.809/−9.121/−8.073 ps), U3 word4 bit1 to RX rt[1] (−0.356 ps). Recorded arrivals, required times and identities in the route audit. No hold or clock change made.
- Unit 37376426740 passed; final routed L3 37376481257 remained active. Prepared branch CI remains local/unpublished. No phase boxes ticked.

Next:
- Publish the prepared groups using the user-run script as required by AGENTS.md, then measure the controlled setup branch experiment before choosing a separate hold repair. Actual extracted setup WNS remains −6.178462 ns.

## 2026-10-05: Codex (measured critical-branch repair prepared)
Done:
- Prepared separate critical-branch repair workflow and guarded pre-route BUF4 split of _19783_; pinned library has no stronger O21AI variant. Confirmed source checkpoint netlist has exactly driver _25365_/Y and loads _25366_/B1, rebuffer5871/A. Preserve 20 ns clock, no-mirroring baseline, region reservation and configuration contract.
- Guarded changed connectivity/master/power/duplicate insertion; legalize before GRT. Extended DRT provenance acceptance only for explicitly flagged branch artifacts. Local helper/Tcl suite 24 passed; shell/YAML/embedded Python/diff checks passed. Real OpenDB/placement/timing remain untested. No phase boxes ticked.
- Latest lint 37376426718, test 37376426587 and docs 37376426735 passed. Final routed L3 37376481257 and unit jobs remain active.

Next:
- User publishes the prepared CI and docs groups under the newly supplied AGENTS.md prohibition on agent commit/push, then dispatch critical-branch repair. Audit actual execution, estimated multicorner/antenna/electrical changes; proceed through DRT, extraction and functional checks only with evidence. Actual baseline remains setup −6.178462 ns and fast hold −0.020809 ns; no timing improvement claimed.

## 2026-10-05: Codex (extracted timing diagnosis and routed L3 validator fix)
Done:
- Monitored extraction 37375411729 through completion: actual routed slow setup WS/WNS −6.178462 ns / 902 violations; fast hold −0.020809 ns / 4 violations. Fast/typ setup pass; slow/typ hold +0.198143/+0.057654 ns. Slew fast/slow/typ 1/179/28. No timing closure claimed.
- Worst slow path U0 mode config latch _49139_→dropped[26] flop _48163_, arrival 27.414698 vs required 21.236235 ns. Large arcs: _25365_ O21AI 1.905905 ns, _25366_ O21AI 1.379506, _25128_ NOR4 1.372737. Worst fast hold U0 word13 bit12 latch _48986_→TX ct[12] flop _46495_, arrival 0.894947 vs required 0.915756 ns. Preserve configuration timing/feedback contract.
- Final L3 run 37375683211 failed validation, not simulation: DRT config omits PL_OPTIMIZE_MIRRORING. Corrected validator reads saved repair config; executed successfully on actual artifact (SHA256 matches). Logged bug #65. No phase boxes ticked.

Next:
- Published validator fix e7d4f61 and extracted audit dbad41b; corrected final-netlist L3 37376481257 launched and running. Critical _25365_→_25366_/buffer branch spans 724.80 µm in x; nominal SPEF _19783_ cap 0.156899 pF and 29 resistance segments sum 1122.8124 Ω (not point-to-point resistance). Following _19784_ cap 0.0560947 pF. These measured loads support a controlled branch distribution/sizing investigation, not changing live-config timing or relaxing clock. Close fast hold too; do not equate zero estimated WNS with extracted closure.

## 2026-10-05: Codex (continuous verification and final routed netlist)
Done:
- Extraction 37375411729 has started; no timing result inferred from active status. Continued independent work while source timing is being extracted.
- Prepared separate l3-hotspot-routed-gl workflow for the final routed netlist from 37363064899, with successful source workflow, zero route DRC, state netlist path, config/gate and SHA256 validation; pinned simulator/models and full expanded suite. This covers routing-stage changes beyond the earlier repaired-netlist suite. YAML/embedded Python/diff checks pass.
- No phase boxes ticked or hardware inputs changed.

Next:
- Published CI 77a14d3 and docs b74cc66; launched final-netlist verification 37375683211, now running alongside extraction 37375411729. Final route audit additionally records 33,902 instances, 515,776 µm² instance area and empty terminal router DRC report. Final routed netlist SHA256 efeb0feaeff6451961c295d5aafc0c5ace4803a62cb96eaac207a65e0414b50a. Keep auditing new results; no extracted WNS claim yet.

## 2026-10-05: Codex (final route audit and extracted timing preparation)
Done:
- Downloaded final 37363064899 artifact: one completed DRT state, route__drc_errors=0, route antenna count=0, saved ODB/DEF/nl/pnl all present. Terminal wirelength 1,912,141 µm. This is route evidence, not full DRC/LVS or extracted STA.
- Added separate hotspot-extracted-timing workflow and explicit route-root selection in existing guarded helper. Restore original source plus hotspot route artifact; check success/provenance, final DRC/files, then cleanup, antenna, connectivity, wirelength, fill, extraction and multicorner signoff-view STA. Twenty-two helper/Tcl checks pass; YAML/embedded Python/diff checks pass.
- Requested failed-job retries of latest unit 37370695839, docs 37370695882 and independent L3 37370664368. No candidate changes or phase boxes ticked.

Next:
- Published CI 0c9726b and docs 30ff3f5 separately; extraction [37375411729](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37375411729) dispatched (queued). Inspect actual routed WNS/hold/electrical results and prerequisite check outcomes. Continue full physical signoff only after the measured result supports it.

## 2026-10-05: Codex (routing log zero violations confirmed)
Done:
- Downloaded completed DRT log 37363064899. First routing pass reached zero violations at 20:40:04; subsequent antenna repair/reroute reached zero again at 20:57:47, then flow completed. This confirms terminal router-reported zero violations, not full signoff DRC/LVS or extracted timing.
- Latest unit RTL job passed including chip/L3 tests; other jobs were cancelled with no steps. Latest lint/test passed; protocol retry did not execute tests. No main workflows in progress at check time.

Next:
- Audit final saved route state/antenna metrics and run extraction if checkpoint validation passes. Final routed WNS remains unmeasured for this trial.

## 2026-10-05: Codex (routing workflow completed)
Done:
- Routing 37363064899 completed successfully, 19:29:14–20:58:46 UTC (~1 h 30 min including setup). Route step and artifact upload passed. Final DRC/state and extracted timing are not yet audited; no clean-route or timing-closure claim from job conclusion alone.
- L3 retry 37370664368 cancelled with no executed steps; protocol checks have not run. Latest lint/test passed; latest unit remains active, latest docs job was cancelled earlier.
- Started retrieving final routing log to verify route output; no boxes ticked.

Next:
- Audit final route DRC/state, then prepare extraction if clean. Resolve independent protocol runner allocation; electrical and final signoff remain open.

## 2026-10-05: Codex (independent verification runner allocation)
Done:
- L3-hotspot-gl 37370664368 failed before executing steps: annotation confirms no hosted runner acquired. Requested one failed-job retry; no protocol failure or pass is established.
- Routing 37363064899 remains active. Latest lint/test passed; two recent unit workflows are running. Latest docs job ended cancelled with no steps, while preceding docs run passed.
- No hardware changes, phase boxes or new timing evidence.

Next:
- Inspect routing and independent L3 retry results when available; distinguish provisioning failures from executed check failures.

## 2026-10-05: Codex (independent electrical and repaired-netlist work)
Done:
- Mapped no-mirroring slew-driver placement spans: _39031_ NOR3 608.64×147.42 µm, _30323_ NOR4 448.32×18.90, _30187_ NAND4 669.12×124.74, _34785_ O21AI 258.72×0. Connection counts 9/3/4/2 include drivers; origin bounds are not routed lengths. Added quantified targets to electrical audit.
- Prepared separate l3-hotspot-gl workflow for exact new 37360552753 repaired netlist: expanded 22 cases, pinned Icarus/PDK, source/gate/config validation and SHA256. Independent of routing; functional evidence only. YAML/embedded Python/diff checks pass.
- No active routing inputs or candidate RTL/config changed; no phase boxes ticked. Earlier annotation-read approval review timed out; unaffected local work proceeded without another retry or new permission request.

Next:
- Published CI 731c1c9 and docs 1f5228a separately; independent netlist suite [37370664368](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37370664368) dispatched (queued). Inspect results alongside routing. Use electrical targets for a later single-change repair trial without altering the active checkpoint.

## 2026-10-05: Codex (workflow email update check)
Done:
- Routing 37363064899 remains active in DRT; no final result. Unit retry 37363104833 is queued. Lint retry 37363104841 again ended cancelled with no executed steps, indicating runner provisioning rather than a lint result. Latest test/docs remain passed.
- Did not launch another immediate lint retry after repeated provisioning failure. No candidate changes or boxes ticked.

Next:
- Inspect routing and queued unit retry outcomes; retry lint when runner allocation recovers.

## 2026-10-05: Codex (unit completion and runner retry)
Done:
- Unit 37363104833 finished: Python/model and RTL/Icarus jobs passed, including chip/L3 tests. Verilator job executed no steps; annotation confirms hosted runner was not acquired. Requested failed-job-only retry.
- Routing 37363064899 remains in detailed routing. Retried lint 37363104841 is queued; latest test/docs remain green. No final routing or WNS evidence available, no boxes ticked.

Next:
- Inspect routing completion and runner retries; keep extracted timing/electrical closure open.

## 2026-10-05: Codex (routing and CI status check)
Done:
- Routing diagnostic 37363064899 remains in its detailed-route step; setup, checkpoint downloads, provenance validation and pinned image build passed. No final route result available.
- Latest test 37363105105 and docs 37363180371 passed; unit 37363104833 remains active. Earlier failed CI jobs show cancelled status with no executed steps. Lint 37363104841 annotation: hosted runner was not acquired after multiple attempts, not a code-check failure.
- Requested retry of runner-allocation-failed lint 37363104841. No candidate or routing inputs changed; no phase boxes ticked.

Next:
- Inspect routing result when it finishes and the retried lint outcome; preserve electrical and extracted-timing checks as open.

## 2026-10-05: Codex (guarded no-mirroring routing continuation)
Done:
- Mapped 19 slow slew records into shared driver groups: _39031_ NOR3 plus eight loads (9), _30323_ NOR4 plus load/diode (3), _30187_ NAND4 plus buffers/diode (4), _34785_ O21AI plus load (2), SRAM A_MEN (1). Electrical closure remains open; no library limits relaxed.
- Added owned hotspot-drt workflow/helper to restore exact passing 37360552753 checkpoint and dependencies. Independently validate no-mirroring, signoff constraints, margin 0, three-corner setup/hold counts, antenna 0 and state files before one-step DRT. Four threads, five-iteration marker reports, 330-minute route limit; preserve region hook during DRT antenna reroutes.
- Twenty-one helper/Tcl checks pass, including negative timing, dirty antenna and missing state refusal. Workflow YAML/embedded Python and diff checks pass. No phase boxes ticked or candidate changes.

Next:
- Published CI f4e54b9 and docs 40a9961 separately; route diagnostic [37363064899](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37363064899) dispatched (queued). Judge convergence/marker geometry against earlier 108-marker timeout. Preserve separate electrical follow-up and require extraction/full signoff after a completed clean route.

## 2026-10-05: Codex (no-mirroring repair result)
Done:
- Audited successful run 37360552753 artifacts: no-mirroring repair has setup WS/WNS 0 and zero setup/hold violations in all corners after antenna repair. Hold WS fast/slow/typ +0.0499802/+0.302909/+0.141023 ns. Antenna nets/pins 0/0; gates.json confirms estimated timing/antenna pass and no DRT launched.
- Compared with mirroring baseline 37221292614 slow WS −0.124212 ns / 15 setup violations. Trial preserves timing through downstream geometry, but has slow/typ slew 19/1 (fast 0), fanout 189, cap 0. These electrical issues and extracted routed timing remain open.
- Repair inserted 8 buffers and upsized 4 cells; antenna repair added 76 diodes and 63 jumpers. No candidate hardware changes or phase boxes ticked.

Next:
- Map the 19 remaining slow slew violators and prepare a guarded DRT trial from the exact no-mirroring post-antenna state. A successful estimated timing screen is not final signoff; extracted all-corner timing and electrical closure remain necessary.

## 2026-10-05: Codex (baseline timing-cone audit during mirroring trial)
Done:
- No-mirroring run 37360552753 passed setup, artifact validation and image build; active in timing/antenna/corner-check step. No result inferred from active status.
- Mapped corrected baseline worst path: U0 config word 4 bit 0 (_49036_) to dropped[21] (_48147_); remaining separate failing cone is U0 config word 0 bit 0 (_49139_) to BITSYNC tb[24] (_47080_). Preserved timed live configuration and same-cycle feedback.
- Quantified worst estimated path: 50 output arcs sum 16.019526 ns, input/net increments 0.084843 ns. Largest arcs and interpretation limits recorded in PHASE2_REPAIRED_ROUTE_AUDIT.md. These are estimated parasitics; no routed improvement or root cause claimed. No phase boxes ticked or hardware changes.

Next:
- Inspect the no-mirroring result when available. If slow timing remains negative, use the common-cone delay/load evidence to choose a single controlled repair; do not dispatch DRT from a failing state.

## 2026-10-05: Codex (controlled repair mirroring screen)
Done:
- Audited corrected 37221292614: clean antenna checks, slow setup WS −0.124212 ns / TNS −1.33337 ns / 15 violations; fourteen from _49036_, one _49139_→_47080_. Fast/typ setup and all hold pass estimated checks. Slew fast/slow/typ 0/1/1, fanout 193, cap 0. Bug #64 CI fix confirmed.
- Prepared one-variable repair comparison: PL_OPTIMIZE_MIRRORING=false in a disposable config; same source region state, constraints, repair margin 0, legalization, routing and antenna hooks. Validate resolved flag. This tests whether mirroring contributes to the downstream regression, not an established root cause.
- Sixteen helper/Tcl checks pass; YAML/embedded Python/diff checks pass. No phase boxes ticked, no DRT or candidate hardware changes.

Next:
- Published CI 7ffeb94 and docs 44caf4f separately; dispatched no-mirroring bounded repair [37360552753](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37360552753) (queued). Compare with corrected baseline 37221292614 before any DRT.

## 2026-10-05: Codex (latest WNS status)
Done:
- Corrected bounded repair 37221292614 completed successfully as a diagnostic. Fresh post-antenna estimated setup WS/WNS: slow −0.124212 ns, fast/typ 0 ns; hold WS fast +0.0853453, slow +0.349589, typ +0.181270 ns. This does not pass slow setup or establish final routed closure.
- Last completed extracted routed slow WNS remains −10.698019 ns from GDS 36799356107. Different routing stages/runs prevent claiming a measured −10.698→−0.124 ns routed improvement. No phase boxes ticked.

Next:
- Inspect corrected repair artifacts, electrical/antenna gates and residual slow paths before selecting another experiment. No DRT dispatched from this negative-timing state.

## 2026-10-04: Codex (antenna reservation hook correction)
Done:
- Downloaded failed repair 37220414494. Antenna checks actually reached zero nets/pins after 88 new diodes and 65 jumpers; no post-antenna corner reports were produced because the guard stopped first.
- Pinned antenna_repair.tcl calls repair_antennas directly, whose internal reroutes bypass Tcl global_route. Corrected wrapper to reserve the region before repair_antennas too; added actual-entry Tcl regression (bug #64). Fifteen helper/wrapper checks pass with local Tcl; shell and diff checks pass.
- Timing resizer inserted 8 buffers, upsized 4 cells and swapped 9 pins, reaching zero internal violations. After legalization (14,932 mirrored instances) and fresh rerouting, slow WS −0.114909 ns / TNS −1.61488 ns / 22 violations. This establishes that internal resizer success does not survive downstream geometry; mirroring alone is not proven causal. No DRT/phase box/physical closure claimed.

Next:
- Published hook fix e0c4e00 and docs 4d3ed63 separately; corrected bounded repair [37221292614](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37221292614) dispatched (queued). Obtain valid post-antenna corner results; do not add a second flow change or route a state with negative timing.

## 2026-10-04: Codex (live workflow status and region repair failure)
Done:
- Region repair 37220414494 failed its antenna rerouting reservation guard after setup/download/build and timing repair completed. Fresh post-timing-repair slow setup WS −0.114909 ns (source −0.0447979); hold remains positive. This is not a passing repaired state; no DRT was launched.
- Status check found three main unit workflows still running: 37220444968, 37220404486, 37219349491. Recent lint/test/docs passed.

Next:
- Inspect antenna-step logs/artifact to determine whether the reservation guard caught an actual missing override or a no-reroute case; address that orchestration issue before another repair screen. Independently review the worsened slow timing result.

## 2026-10-04: Codex (region trial timing and antenna repair preparation)
Done:
- Inspected seven slow violations: six paths originate at latch _49036_ to _48142_–_48147_; one _49012_→_47080_. Worst −0.044798 ns. No architectural latency or constraint change proposed.
- Added separate hotspot-repair workflow/helper: restore region checkpoint, slow signoff-aware margin-zero timing repair, antenna repair, then matched fresh three-corner checks. Stop before DRT and report actual timing/antenna gates.
- Extended region wrapper to rsz_timing_postgrt.tcl and antenna_repair.tcl; validate repair reroutes retain the trial reservation. Fifteen helper/wrapper checks passed with a Tcl interpreter unpacked under /tmp (no system installation); shell/YAML/embedded-Python/diff checks passed. No phase boxes ticked.

Next:
- Published CI 2158652 and docs aab3aad separately; repair screen [37220414494](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37220414494) dispatched (queued). Inspect cell/electrical changes and post-antenna timing/antenna gates before considering DRT.

## 2026-10-04: Codex (local resource screen completed)
Done:
- Screen 37219355996 succeeded as a diagnostic. Both fresh GRT variants have zero overflow and 33,775 instances. Baseline/region wirelength 2,530,396/2,518,898 µm. Region slow setup WS −0.0447979 ns, TNS −0.180505 ns, 7 violations; baseline setup passes. Hold remains positive in all corners.
- Fresh rerouting reintroduces antenna violations in both variants: baseline 86 nets/95 pins, region 84 nets/97 pins. Slow slew 13/14; fanout 181, cap 0. Neither rerouted checkpoint is ready for a clean DRT/signoff continuation. No phase boxes ticked.

Next:
- Examine the seven new slow paths and ensure any local-resource trial survives signoff-aware timing repair plus fresh antenna repair. Preserve the region override during rerouting; do not directly route either antenna-dirty screen output or mistake diagnostic success for closure.

## 2026-10-04: Codex (bounded local Metal2 resource screen)
Done:
- Inspected pinned PDK cell LEF: implicated buf/a21oi/a221oi pins/obstructions use Metal1. SRAM footprint is outside the persistent x=500–700 hotspot. Power-grid via entries also occupy Metal2; exact interference remains unproven without routed geometry.
- Added owned hotspot-screen workflow, helper and pinned OpenROAD wrapper. Compare identical post-antenna source with global adjustment 0.16 against a local Metal2 0.30 reservation in {500 280 700 380}; run only GRT, antenna checks and six matched corner reports. No cell/placement/RTL changes, antenna repair or DRT.
- Eleven helper regressions pass; workflow YAML/embedded Python, shell syntax and diff checks pass. No phase boxes ticked.

Next:
- Published CI/helpers 74a199a and docs 561fa13 separately; dispatched bounded screen [37219355996](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37219355996), now in progress. Compare fresh overflow, antenna, all-corner timing and guide allocation before selecting any detailed-route continuation.

## 2026-10-04: Codex (repaired post-antenna and routing hotspot audit)
Done:
- Downloaded completed continuation 37187027878: post-antenna signoff-view estimated setup WS 0 in all corners, hold +0.0897432/+0.366301/+0.190121 ns (fast/slow/typ), zero setup/hold violations. Remaining SRAM A_MEN slow slew excess 0.100671 ns; fanout 181, cap 0.
- Confirmed timeout during iteration 51; completed iteration 50 has 108 intermediate markers (80 shorts/28 spacing; M2 103/M3 3/M4 2). No final route state exists. 95/108 records occupy the earlier x=500–700/y=300–350 µm band; current leaders are lane-0 output-token bit 3, net1580, net1468 and _18767_. Mapped drivers/loads to saved placement.
- Added reusable `scripts/ci/routing_audit.py` and `docs/reports/PHASE2_REPAIRED_ROUTE_AUDIT.md`. Analyzer matches both actual 108/215 snapshots and log breakdowns; diff check passes. Repaired L3 artifact confirms 22 cases, zero failures/errors/skips. No phase boxes ticked or candidate hardware changed.

Next:
- Inspect pin shapes, routing obstructions and guides in the persistent Metal2 band before selecting a local spacing/resource experiment. Extraction remains gated on a completed clean route; avoid another identical replay.

## 2026-10-04: Codex (completed repaired-netlist and routing results)
Done:
- Repaired-netlist L3 run 37187473289 completed successfully; its protocol-suite step passed. This is functional evidence, not extracted timing signoff.
- Repaired routing continuation 37187027878 timed out at the combined step's 330-minute limit. Job 111391024983 reached 50 completed optimization iterations with 108 violations remaining, and timed out during iteration 51. Compared with the older replay's 215-marker snapshot, the remaining count is lower, but routing still has no demonstrated clean completion.
- Recent main test/lint/unit/docs runs and nightly 37204675992 passed. No phase boxes ticked or candidate hardware changed.

Next:
- Inspect saved post-antenna timing and remaining routing-marker geometry before choosing another controlled experiment. Keep extracted-timing continuation pending until a completed clean route exists.

## 2026-10-04: Codex (independent repaired-netlist, electrical and extraction work)
Done:
- Added separate `l3-repaired-gl` workflow: exact R4 candidate, audited repaired netlist, SHA256, config validation, pinned Icarus 13/IHP models and full 22-case L3. Does not depend on active routing output.
- Traced electrical violators from already completed repair 37185455158: SRAM A_MEN fails slow/typ slew; _30323_ NOR4 output → _30324_ A21OI input fails slow slew, with 446.88 µm x separation. All 164 fanout failures are clock-tree leaves. Added quantified targets/placement and controlled hypotheses in `docs/reports/PHASE2_ELECTRICAL_AUDIT.md`.
- Prepared separate extracted-timing workflow/helper, requiring a completed clean route and following pinned cleanup/connectivity/fill/RCX/multicorner STA ordering. It refuses timeout/missing/dirty checkpoints. Not dispatched because it requires the future route artifact.
- Nine helper regression cases pass; both new workflows' YAML/embedded Python parse; diff checks pass. No candidate RTL/config changes and no changes to active route inputs.

Checklist:
- No boxes ticked; prepared workflows/tests are not completed physical/functional evidence.

Next:
- Published CI/helpers c2c7fae and electrical audit 793aa8f separately. Dispatched independent repaired-netlist L3 37187473289 against repair 37185455158 (queued at dispatch). Inspect its own results when available. Extraction is published but deliberately not dispatched until a completed clean route exists; electrical fixes remain hypotheses.

## 2026-10-04: Codex (active workflows and independent work)
Done:
- Four main workflows running: repaired continuation 37187027878 and unit 37187043719, 37187014115, 37185475488; none queued. Continuation passed setup, both artifact downloads and provenance validation; combined antenna/corner-check/route step is active. No finer-grained completion is established from step status.
- Identified useful independent work: expanded L3 simulation of repaired netlist, mapping remaining electrical violators, and preparing extracted-timing/physical-signoff continuation. No changes dispatched in this status check; no boxes ticked.

Next:
- Prioritize repaired-netlist functional verification while routing continues; it has physical cell/pin changes but no fresh protocol evidence yet.

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
