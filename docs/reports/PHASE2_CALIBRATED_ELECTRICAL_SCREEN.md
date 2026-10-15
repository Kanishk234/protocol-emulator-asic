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
