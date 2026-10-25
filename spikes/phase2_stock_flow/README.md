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
