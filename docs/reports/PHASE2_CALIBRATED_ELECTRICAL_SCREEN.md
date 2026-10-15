# Calibrated electrical screening from paired route evidence

## Evidence

[Diagnostic 38762064184](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38762064184) succeeded on 697497e5491aa6eaa62fad8fe41b6eeb5faac3f9. Artifact11987565310 contains all six per-net reports and summary. It reuses green screen38687129808 and failed extracted route38689478738, with the same signoff SDC/corners and unchanged saved physical files.

Independent local reparse reproduces all stage measurements and paired results. There are34,432 screen nets and34,430 extracted nets; the two screen-only names are VPWR/VGND. All34,430 common nets match. Row ordering in the first paired summary varied with Python hash seed; measurement values/counts do not. BUG113 fixes presentation determinism.

| Slow-corner net | Estimated transition | Extracted transition | Limit |
| --- | ---: | ---: | ---: |
| `_07894_` | 1.414666 ns | 2.552041 ns | 2.507400 ns |
| `_04493_` | 1.376814 ns | 2.508724 ns | 2.507400 ns |

The critical nets appeared at only55–56% of their transition limit in screening. A10% reserve would not catch these failures. On `_07894_`, capacitance also changes from0.152115 to0.273483 pF. This establishes large measured screen/extracted disagreement; it does not isolate coupling, detours, RC-model parameters or each individual contribution.

No screen net reaches90% of its slew/capacitance limit. Extracted slow corner has five nets at>=90% slew, and two at>=90% capacitance; fast corner has four at>=90% capacitance. Fanout has1,718 screen nets and1,719 extracted nets at>=90% of their limit. Buffering all such fanout nets would be an unnecessarily broad first experiment.

## Prepared bounded risk-class repair

Select data nets with either screen slew/capacitance utilization>=0.45 in any corner, or at least eight physical loads including an existing antenna diode in the final source DEF. This selects64 data nets. One additional protected clock net is explicitly recorded and excluded from rewiring; its current signoff fanout is legal, but it retains diode-load risk. No universal fanout headroom claim is made.

`margin_risk_plan.py` binds the actual route NL/DEF/hold/electrical report hashes and full paired-summary hash, recomputes the selection, and requires the exact64-source inventory. Four nets have measured extracted violations;60 additional nets receive preventive isolation. It partitions these sources behind123 BUF4 cells, at most four original loads per branch. Added cell footprint1785.3696 um²; no computed footprint overlaps. No resizing, hold-delay insertion, clock/reset-pin rewiring, RTL change or signoff constraint change. Physical legalization, congestion and timing remain unmeasured.

The shared plan builder accepts preventive sources only from a review-bound profile; existing profiles retain their old behavior. The shared timing helper optionally adds the read-only per-net hook only for this profile.

## Required screen gates

`gds-margin-risk-screen` is manual and stops before detailed routing. It requires:

- Existing all-corner setup/hold and zero electrical/antenna/live-overflow gates, including fast hold>=50 ps.
- At most six loads on all reviewed source and new branch nets after antenna repair.
- Fresh per-net after-repair reports at all three corners, with **both estimated slew and capacitance utilization<=0.45 globally**. A missing or failing margin report revokes the qualified receipt.

The0.45 threshold is a conservative empirical internal screen target, not a changed library limit or proven worst-case estimate bound. The previous green screen is correctly rejected by it: slow29slew/6cap nets exceed it; typical/fast each have7cap nets above it. A new green result still requires actual detailed routing/extraction and ultimately official GDS/precheck.

Validation:103 focused checks pass across new inventory/gates, paired measurement, shared plan/timing helper and existing screen profiles. Actual-source proposal/geometry allocation, synthetic connectivity conservation of all123 identity buffers, and generated Tcl completeness pass. Six actual diagnostic reports were independently reparsed; their values agree with the saved summary. No physical result is claimed from these preparation checks.

Next run this screen. If the global calibrated gate fails, inspect the reported new risk class before any routing. If it passes, continue the exact qualified checkpoint and compare actual extracted margins; retain fresh final gates and route DRC checks. The separate route-preserving final ECO investigation remains open.

## First calibrated screen result and live repair follow-up

[Run38767625186](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38767625186), bb1eeb5c39b1295fdab45208108576d08a4ac08f, reaches the new internal margin gate and is rejected there. Small artifact11991610753; bulk11991294060. Ordinary all-corner electrical violation counts and antenna counts are zero; setup WS0; fast/typical/slow hold70.8775/166.924/338.733ps. Repaired-family fanout reserve passes (maximum5loads).

The internal0.45guard rejects15slow-slew nets, one typical-slew net and three capacitance nets in each corner. Worst slow estimated slew utilization0.725765. Independent actual-report classification finds16distinct margin-risk nets, corresponding to24max-four-load BUF4 branches in a first batch. None of the123new branch nets exceeds the margin target. Most offenders are outside the original64source families; net8647 remains a capacitance-margin offender on an original repaired source. Thus a new full reroute exposes different margins even after the selected sources are repaired.

Prepared `gds-inline-margin-screen`: keep the exact same original route source and123-cell proposal, changing only the live post-antenna repair policy. After each antenna cleanup, in the already-initialized GRT process, estimate parasitics and capture every net's worst slew/capacitance check for all three pinned corners. Select sources above0.45 alongside ordinary fanout failures, partition only unprotected standard-cell data loads behind BUF4, legalize and incrementally reroute, repair antennas and repeat. Retain existing two-batch/32-buffers-per-batch/64-total dynamic budget, protected clocks/resets/exposed-net rules, final live-overflow, all timing/electrical/antenna gates, six-load family reserve and global0.45margin gate. Final signoff limits remain unchanged. No DRT occurs in this workflow.

Python independently parses each pre-batch three-corner report and authorizes a small-fanout partition only when that source has measured margin risk. All original cells/pins and diode-only intervals remain audited. The final no-change iteration must show no margin offenders, including protected nets; skipped protected sources cannot silently qualify. Saved batch reports and connectivity receipts remain artifacts. The gate receipt now includes every offending net/pin/limit/actual/utilization and prints that evidence on failure, before bulk upload (BUG114).

Validation:103focused tests pass (dynamic margin proof, Tcl data/protected selection, existing antenna/fanout/history, conservative gates and shared screen/timing). Real local OpenSTA three-corner toy tests check classifier thresholds and report/parser agreement. The actual failed screen's original history still passes the unchanged default audit; its16offenders are independently recovered. Shell syntax and diff checks pass. Physical convergence is unproven; the bounded loop may still reject the design, in which case routing remains blocked.

## SRAM data-bit audit correction and saved-checkpoint qualification

Run38773856018 reaches completion of the physical GRT step, then stops in `validate_batch` with `Wrong or repeated post-antenna sink`. This is a validation rejection before fresh timing qualification, not evidence of final timing or DRT failure. Its full artifact is still uploading at preparation time, so exact failed-batch replay remains pending.

The audit had a demonstrated coverage gap: it expanded the known SRAM's nine address bits but left its16data-input bits as one concatenated A_DIN port. The live margin-risk inventory includes net11741, connected to SRAM A_DIN[8]. OpenDB receipts identify that individual pin; the old audit cannot find it. Corrected the two connectivity checks to share strict expansion of A_ADDR[8:0] and A_DIN[15:0], validating exact width and bit order. Other SRAM ports remain unchanged. This is a representation fix, not permission to skip SRAM wiring checks.

Regression covers data bits0/8/15, wrong-bit receipts, unrelated net changes and truncated data buses. A synthetic identity buffer on A_DIN[8] using the actual mapped project macro instance passes complete cell/pin conservation. Exact failed-job receipt replay is still required to confirm this accounts for its exception.

Prepared `gds-inline-margin-qualify` to reuse run38773856018's completed physical checkpoint after the artifact becomes available. It binds that failed run's exact SHA, revalidates the original hardware/recipe/source proposal, refuses stale qualification outputs, verifies saved GRT view identity, replays all corrected connectivity/margin/placement/overflow audits, then runs fresh stock antenna and all-corner STA plus unchanged family/global margin gates. It performs no new physical ECO or GRT. A failed audit still refuses qualification. This avoids spending another routing run solely to correct Python bus representation.

Both the original screen and qualification workflow now upload repair receipts, before/after logical netlists and inline margin reports before bulk evidence, even when no gate receipt exists.97focused tests pass, including stale/missing replay-view refusal and workflow-source binding. Physical results and exact failed-batch replay remain pending uploaded evidence; no phase completion claim.

The completed failed-run artifact11994451665 now confirms the exact expected A_DIN[8] sink on net11741 (and A_ADDR[4] on net11770). Corrected audit passes the complete actual24-buffer batch, all preserved cells/pins and diode-only intervals. The physical loop reports16margin-risk nets before the batch and zero afterward. Independently parsed final inline maxima: slow slew0.449244/cap0.444233; fast cap0.448547; all corners/checks below0.45. Actual proposal, source baseline, initial123-cell ECO, original placements, live zero-overflow and route-reset audits pass too. These are inline electrical/GRT proofs, not fresh timing qualification.

Published audit fix/replay workflow on main86fa8453317230c26df767e76f67c6dd8092f86b and launched [qualification38777752196](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38777752196), confirmed in progress. It reuses the saved physical checkpoint and performs no routing/ECO again. Fresh antenna/STA and final qualification remain pending. This launch receipt is local pending subsequent documentation publication.

## Saved checkpoint qualifies; stock routing prepared

[Qualification38777752196](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38777752196) succeeds on86fa8453317230c26df767e76f67c6dd8092f86b. Bulk artifact11996651166, audit11995720114, gates11994154162.

Fresh stock all-corner STA: setup WS0 and zero reported electrical violations; hold fast/typical/slow70.8775/166.924/338.733ps. Fresh antenna nets/pins0/0. Global estimated slew/capacitance utilization remains below0.45 (slow worst slew0.449244, worst all-corner cap0.448547). Repaired source/branch families pass the six-load reserve. These are strict screening results, not extracted signoff or positive global setup margin.

Independent downloaded-artifact audit passes: full gate receipt, original hash-bound123-buffer/64-net proposal and source baseline, all connectivity including SRAM data/address bits,24dynamic buffers and antenna-only intervals, original placements, live zero-overflow/reset receipt, fresh timing/electrical/antenna and recomputed global/family margin guards.

Prepared `gds-inline-margin-route`, bound to this exact successful qualification and complete receipt. It revalidates margin evidence, then uses the shared stock continuation: fresh pre-DRT timing/antenna/electrical gate, DetailedRouting, actual final logical-netlist audit, zero-DRC extraction and all-corner final timing/electrical/antenna gates. No extra ECO or full GRT is repeated. Early extracted summary upload remains before bulk.89focused tests pass. Detailed-route/extracted and official GDS closure remain pending.
