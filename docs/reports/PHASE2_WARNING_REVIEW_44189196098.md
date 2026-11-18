# Warning and coverage review of the official green layout

Scope: official44189196098, physical revisione19556e. This review preserves the
verified design, constraints, configuration and official workflows. Compact
source-bound evidence is in warning_review_44189196098.json. Warnings remain
visible; the audit does not suppress them or claim that all warnings are harmless.

## Findings and disposition

| Warning / coverage question | Evidence | Disposition |
|---|---|---|
|15native lint warnings |7width-expansion comparisons and8unused-signal warnings, matching the narrowly reviewed cases in promoted_rtl.vlt. Tests and signoff pass. | Retain current RTL bytes. Cosmetic cleanup can be considered with a future functional change and renewed hardening. |
| Generic PnR/signoff SDC fallback | Stock base constraints loaded,20ns clock and0.25ns uncertainty independently checked. | Intentional stock configuration, not absent timing constraints. |
| SRAM internal netlist lacks SPEF | Actual corner STA logs confirm the matching SRAM Liberty is loaded at all3corners; SRAM timing endpoints appear in the STA log. | Characterized macro timing is used; do not replace it with an uncharacterized internal netlist. |
|77raw unannotated drivers per corner | All are unusedena plus76clkload outputs. Actual final Verilog omits those output connections; filtered unannotated net count0at every corner. | No uncovered functional driver identified in this inventory. Keep coverage review after future changes. |
| One input lacks antenna-gate data | The final LEF has19input pins; onlyena lacks ANTENNAGATEAREA. RTL explicitly leavesena unused. | Expected for this unused input; not evidence that functional gate areas are missing. |
|2002EST-0026repair messages | Intermediate repair warnings; final route/RCX/STA/checkers and macro connectivity pass. | Final outcome audited, not a blanket waiver of future missing-route warnings. |
|47DRT-0418macro pin-grid messages;7DRT-0349unsupported LEF58 rules | Final routeDRC0, whole-GDS CMOS5L KLayoutDRC0, LVS0and official precheck10/10. | Accepted on this artifact's final geometry evidence. Any changed warning/outcome requires review. |
| Clock fanout/single-sink CTS warnings | Clock tree is implemented and final extracted timing passes. | Known clock-topology diagnostics; positive timing reserve is still narrow. |
| RSZ max-wire-length tradeoff warning | Setting200um was part of the frozen tested recipe; actual extracted timing, capacitance and slew pass. | Do not retune the physical recipe merely to remove the message. |
|10Magic abstract overlaps / skipped MagicDRC | Exact reviewed SRAM-only marker inventory; whole-GDS KLayoutDRC0plus LVS pass. | Explicit D-185policy, not a claim of zero rawMagic markers. |
| Supply-source locations absent | Default source model and static typical-corner analysis, without explicit shuttle/package supply locations. | Real coverage limit: not package-aware or dynamic worst-case power validation. Follow-up below. |
| Long-wire threshold check skipped | A full wire-length report exists; an optional cutoff was not configured. | Quantify lengths and retain baseline; a fabricated cutoff would not add validation. |

## Power evidence and remaining work

The actual flow reports all VPWR and VGND shapes connected; the power-grid checker
reports0violations. Its typical static estimate gives worst drops0.356908mVVPWR
and0.284883mVVGND. These values use default supply-source assumptions and are
NOT measured silicon, package-aware bounds, or dynamic worst-case guarantees.
No guessed VSRC_LOC_FILES coordinates have been added to configuration.

Before making stronger power claims, obtain the actual shuttle/top-level tile
supply connection locations and an intended activity/power scenario. Then run a
read-only boundary-source sensitivity check and record the assumptions. This is
an integration/evidence follow-up, not an observed failing Phase2gate. The absence
of that data is not solved by choosing coordinates that make a warning disappear.

## Wire-length evidence

The existing routed-wire report covers42902nets. Cross-referencing DEF USE
attributes identifies1293clock nets. Longest reported routed net length is
1105.07um(clknet_0_clk,CLOCK); longest SIGNAL net is585.63um(net11723), followed
by515.8um(net2293).15nets exceed500um, and1exceeds1000um. These are reported
net lengths, not individual-segment maximums or failed timing paths.

Keep this distribution as a comparison baseline for future RTL/placement changes.
The existing extracted timing/electrical and whole-layout DRC checks provide the
current acceptance evidence. No arbitrary long-wire threshold has been declared
a new signoff requirement, and no skipped checker is represented as passed.

## Conclusion

No new functional timing-annotation or connectivity gap was found that warrants
reopening the verified physical design. Record the real power-analysis scope and
review new or changed warnings on the next hardware run. The design is qualified
under its stated model/flow/waiver assumptions, not proven free of every possible
silicon or integration risk.

Closure revision7f3ae9a has test44227558895,lint44227558861,unit44227558788and
 docs44227558977allSUCCESS. Together with the official workflow, independent
artifact audit and million-cycle/fault-injection results, Phase2exit criteria pass.
