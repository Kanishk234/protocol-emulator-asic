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
