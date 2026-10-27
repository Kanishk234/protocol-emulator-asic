# Unchanged official-flow preparation

This21-file design-only patch contains the verified full2-lane/4-unit/U0-full/SRAM prototype. It is unapplied, not a complete runnable integration, and not stock-flow timing evidence. It excludes config, workflow, runtime/container and physical ECO changes. File hashes bind the locally tested prototype. SRAM views and permitted project configuration require separate review. Do not apply the withdrawn phase2_main_promotion bundle.

Next steps:

1. Audit project inputs: canonical sources,6x4metadata, pinned SRAM views, power hookup and fully timed constraints. Keep the official action and stock flow unchanged.
2. Resolve SRAM Magic/overlap compatibility without suppressing checks or modifying PDK/macro views. Raw signoff39883160399 remains failed. Historical R3 green results used macro-specific checker exceptions, so they do not prove strict raw-Magic cleanliness.
3. Measure a stock-flow baseline on this exact RTL. Passing experiments used incremental-route instrumentation and81buffers/14strengthchanges/250sinkrewires; that timing is not transferable to stock synthesis/routing.
4. Choose general RTL improvements from actual failing stock paths, preserving firmware behavior/resources/20ns. Check functionality and area/routing.
5. Require the unchanged official gds/precheck/gl_test/viewer jobs green on main before closing Phase2.

## SRAM reference audit (2026-10-23)

The organizer-linked walkthrough https://kdp1965.github.io/ihp-um-janestreet-prism/ihp_sram_macro.html explicitly documents the LEF-obstruction/real-GDS mismatch. Its project configuration disables Magic DRC/illegal-overlap fatality and enables KLayout DRC with the CMOS5L deck. This is a project checker-policy exception, not an RTL fix or proof of zero raw Magic errors. It must not be silently adopted. No such settings have been applied here.

A stock-flow solution may use that documented SRAM integration if approved, while retaining zero real merged-GDS DRC, LVS, antenna and electrical violations. If every raw Magic marker must also be zero, that is an additional unresolved integration requirement. The previous plan incorrectly treated the known macro-view markers as ordinary RTL defects.

The walkthrough also contains custom-step and precheck-edit examples; those are explicitly excluded from our unchanged-flow plan. Reference advice is not authorization to modify Tiny Tapeout tools or PDK views.

## Prepared stock baseline

The isolated project is build/stock-official-20261023 (ignored build directory). The unchanged official tools at d66cf179e7bc4d296362ab7e2e3b344dc3c4f665 pass their actual --create-user-config/HDL-port checks. Canonical generation matches. All8macro hashes and21design-file hashes match; the official workflow hash is unchanged. input_validation.json records preparation evidence only.

The original baseline config changed only density56and documented SRAM integration fields. After timeout39996448720, the diagnostic follow-up additionally sets PL_RESIZER_SETUP_SLACK_MARGIN=0 (D-109); no other physical setting changes. It does not select a custom flow or disable checker error gates. Main adoption of the added optimizer field needs explicit owner review. It uses stock base.sdc, including default uncertainty rather than the experimental0.10ns hold override. The retained source signoff.sdc is not selected in this baseline. This is deliberately a stock baseline, not a claimed reproduction of the experimental recipe.

The separate gds-stock-official-baseline-screen workflow prepares this full design in an ephemeral checkout and runs the stock image/Classic order through the final pre-DRT STA. Real LibreLane3.1.0.dev3 confirms OpenROAD.STAMidPNR-3 immediately precedes DetailedRouting. No custom runtime/Tcl, checkpoint input, physical ECO, optimizer-policy override, template edit or automatic routing continuation is used. A green diagnostic job means measurement completed; timing/electrical/antenna reports must still be reviewed before qualification. No workflow is launched yet.

The normal official gds workflow will be used for final acceptance once actual stock-flow measurements justify promotion. The custom integration proposal remains withdrawn.

Follow-up diagnosis and exact fresh metrics: docs/reports/PHASE2_STOCK_BASELINE_TIMEOUT.md. Do not interpret diagnostic-job success as timing qualification.

After40026122208completed repair but timed out relaxing clock NDR, D-110adds only CTS_APPLY_NDR=none to this diagnostic configuration. This restores the normal-spacing project policy already documented in D-043, without stock-flow or checker changes. Fresh typical hold+0.273668ns is progress, not routed/all-corner qualification;169fanout violations remain.

Completed40042584523is measurement-only: typical setup0/hold+0.246254ns,5slew/1cap/180fanout errors and3738pre-antenna overflow. D-111next sets only CTS_SINK_CLUSTERING_SIZE=8and adds stock read-only repeated all-corner STA after the physical screen. Source-view hashes enforce no physical modifications by the audit. See docs/reports/PHASE2_STOCK_BASELINE_RESULTS.md. No routing qualification follows from job success.

Run40110884653eliminated clock fanout but exposes slow setup−1.31005ns/fast hold43.0439ps and remaining actual electrical errors. D-112next tests the coherent3-setting native electrical-repair recipe (enabled post-GRT repair,600um buffering length,0.16routing adjustment), preserving all stock scripts/ordering/checkers and full hardware. All-corner audit remains read-only; no DRT from measurement-job success. See the results report for exact settings and cost/risk.

Run40120999838clears electrical counts at all3corners,saved routing overflow and final antenna. Slow setup−0.447463ns/fast hold15.865psstill block DRT. D-113next enables the existing native post-GRT timing repair with0extra setup margin/125pshold target. Final audit now includes fresh read-only antenna measurement on the timing-repaired state, with immutable source hashes. No stock physical ordering or script changes.

Run40127505533meets fast hold50.6384ps/electrical0but regresses slow setup−0.750799ns/final antenna55nets. Current D-114candidate applies hash-bound late_drop_select.patch after the verified base source bundle. AllN1..16channel equivalence,7channel/4topRTLtests and representative mapping checks pass. Use DELAY0/150psearly hold/optional late timing off, retaining stock ordering/checkers and final fresh audits. This is not the old unchanged-RTL baseline; the variant hash and scope are in late_drop_select_evidence.json. No main source/template changes or DRT qualification.

Current D-115test applies forwarded_drop.patch after the prior late-select source. The2pending event bits preserve exact cycle-visible count by forwarding F(base,pending); allN1..16equivalence and7channel/4topRTLcases pass. Physical config is identical to40162935683to isolate the RTL effect. Source hashes/proof and local ideal-wire diagnostics are in forwarded_drop_evidence.json; those are not whole-chip timing. Exact CI prepare/real TT config checks pass; physical results pending.


Run40179640229 completed with slow setup -0.780544ns, fast hold -0.0124152ns, three fanout failures, and post-repair overflow36. It does not qualify for DRT. D-116 adds mode_predicate.patch after the existing counter patches, caching the existing joint mode condition with unchanged word0 visibility. Physical config is unchanged. Source hashes, proof scope and test counts are in mode_predicate_evidence.json; the separate mode_predicate_harness.patch connects the cache in pin-unit tests. No main source/config or official-template edit.

Replay the source-bound property proofs, negative control and exhaustive configuration tests with the project venv:

```sh
source .venv/bin/activate
python spikes/phase2_stock_flow/mode_predicate_checks/check.py BASELINE NEW_WORK_DIRECTORY
```

BASELINE contains the prepared full-design src directory before mode_predicate.patch (for example build/stock-official-20261023). The helper copies sources and applies only the guarded patch into a new directory. It never edits BASELINE. Physical benefits remain unmeasured; no DRT follows from functional proof or green measurement-job status.


D-116 run40214888335 reaches reported setupWS0 at all three corners, with fast hold -33.3446ps and three actual fanout failures. D-117 now keeps hardware fixed and tests exactly two physical settings: early hold target250ps and native jumper-only antenna repair. Final DEF confirms antenna-cell loads cause all three current fanout failures. native_antenna_hold_evidence.json binds the prior/candidate config hashes and unchanged hardware. Stock timing/fanout/antenna acceptance remains fixed; jumper-only can still fail final antenna and extra hold repair can harm setup/area. No DRT from measurement-job success. Main source/config and official template remain untouched.


D-117run40353011505fails slow setup(-0.412522ns),fast hold(-0.00505285ns),12slow slew checks and45antenna nets,despite fanout0. Jumper repair adds0jumpers on its last two passes, so do not just increase iterations. D-118restores the exact40214888335physical settings and applies one additional source-only config_banks.patch. Two independently enabled parity banks reduce per-bit distribution while retaining ordinary antenna diodes/checks. This may still leave producer-token fanout/hold failures; physical benefit unmeasured. Main source/config and official workflow unchanged.

Replay written-word/derived-output contract proofs and both-phase configuration simulations:

```sh
source .venv/bin/activate
python spikes/phase2_stock_flow/config_banks_checks/check.py PREPARED_MODE_CACHE_BASELINE NEW_WORK_DIRECTORY
```

The baseline must have the verified D-116 sources before config_banks.patch. The helper uses a new scratch directory, guards source hashes, checks full/lean latch/flop cases and rejects a wrong-bank mutant. It does not modify the baseline. Source hashes, regression counts and local mapping cost are recorded in config_banks_evidence.json; no whole-chip formal or physical qualification is implied.


Banked run40378317785 reports setup0 at all corners and holdfast+35.18ps,with slew/cap/antenna0and last pre-antenna overflow0. Fast reserve is14.82psshort of50ps; four fanout branches still fail after antenna insertion. Actual pre-antenna area+9482um²vs40214888335. D-119now keeps hardware/mixed antenna fixed and tests wire-buffer length300um plus early hold target175ps. Exactly two diagnostic physical settings are hash-bound in wire300_hold175_evidence.json; baseline bank config remains recorded in config_banks_evidence.json. Constraints/checkers/template/main source stay unchanged. This is a measurement candidate, not DRT qualification.


Wire300/hold175 run40399598426reports setup0allcorners,electrical/antenna0and last pre-antenna overflow0. Only reported timing/electrical/antenna screen failure is fast hold-3.75733ps(53.75733psshort of50psgate); physical signoff/DRT remain unperformed. D-120changes only early hold target175→250ps. wire300_hold250_evidence.json binds the matched control to the prior config hash. Hardware/other policies/template/acceptance unchanged. More buffers can regress any physical gate; final fresh audits remain required.


Hold250 run40410841468reports setup0allcorners,fast hold+43.7279ps,electrical/antenna0. It misses50psreserve by6.2721ps; last pre-antenna overflow44also prevents a clean-routing claim. Area+26653um²vs175psearly hold. D-121tests smaller250→275pshold increment and native overflow iterations50→100,with wire300/hardware/otherpolicies fixed. Evidence is wire300_hold275_iter100_evidence.json. More iterations may not resolve local pressure and timing may regress; no DRT/official-green claim.


Run40427663913times out at our145min diagnostic limit just after saving final antenna-insertion ODB/DEF/state; it does not provide fresh final timing. Last pre-antenna overflow61is not clean-routing evidence. recovery_40427663913.json binds48frozen inputs and exact source/tool provenance. Separate gds-stock-checkpoint-audit restores the same checkpoint and performs only repeated stock STA/fresh antenna checks; no repair/state rewrite/DRT/qualification. Twelve validator checks and actual artifact validation pass. The original failed job remains failed. Diagnostic budgets become190minphysical/30minaudit/240mintotal; official workflow/hardware/settings/gates unchanged. Recovery measurements pending.


Recovered audit40445418882 measures frozen40427663913without physical changes: setup0allcorners,fast hold48.4025ps(1.5975psshort of50ps),electrical/antenna0; last known pre-antenna overflow61stillunresolved. No DRT qualification. D-123adds independent hold300 and density54 choices to the existing screen. Each changes one setting only against the exact baseline; stock_control_profiles.json binds all hashes and selected_profile.json identifies each run. Base strict_project_config.json remains unchanged. Both actual TT configs/exact preparations/schema checks pass; unknown profiles reject. Physical outcomes unmeasured; do not combine settings or infer closure from job success.


On2026-10-27 hold300run40447369799 worsens fast hold to31.7554ps/overflow106. Density54run40447377789is a no-op: GPLclamps54and56to61minimum; ODB/DEF/NL/PNL/SDCbyte-identical to recovered baseline48.4025ps/61overflow. D-124retires those choices. New wire400 tests one buffer-length change; late75 enables native late timing repair with75pshold target on the same early275baseline. Native rerouting/order/gates stay fixed; late rerouting can regress antenna and all fresh checks remain required. Effective-control validation checks real commands/late step and rejects density clamps. Eight guards,actual-log checks,exact preparations/schema and TT configs pass; physical outcomes unknown. Latephysical240min/sharedjob300min are diagnostic-only budgets; official workflow unchanged.


Late7540459607737clears timing/electrical(fast84.0735ps)butfails31antenna nets/finalreportedoverflow68. Wire40040459596311failsfast36.7189ps/onefanout,lastpreantennaoverflow48. Source-bound late75_antenna_evidence.json shows all31failingpairs/sinktypesexisted beforelate; earlier27jumpers/17diodes and later18holdbuffers motivate persistent-protection testing. D-125adds late_diodes(native diode-only) andlate_grt15(reservation16→15%)asindependent one-additional-setting controls versusmeasuredlate75. Per-case config/reference hashes and native command/resource verification apply. No combinedcase/baselinererun,tool/SDC/ordering/official-template change. Diode loads and more optimistic capacity can each regress physical gates; actual DRC remains mandatory. Same-checkpoint STA-only override preserves source routing metadata; legacy helper0.16behavior unchanged. Twenty-twoguards/exactprep/schema/TTchecks pass; physical results pending.


2026-10-27 follow-up: late_diodes 40538578732 passes timing/electrical but retains 23 antenna / 71 overflow; late_grt15 40538583444 has two slow slew, 28 antenna / 83 overflow. See late_diodes_residual_evidence.json for unchanged 45 diode connections and residual classification. Active independent controls late_ant50 and late_early175 each change one setting from measured late_diodes. Native commands and exact config hashes are checked. Main hardware and official workflow remain unchanged; no candidate qualifies for detailed routing yet.
