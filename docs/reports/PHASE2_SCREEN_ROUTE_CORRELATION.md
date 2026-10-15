# Screen-to-route correlation and bounded reserve screen

Evidence: green screen [38676308492](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38676308492), failed route [38679335674](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38679335674), route head b049a17343b3ff9912f596aa9953be1397c5baf7. Full routed artifact 11950305835; early gates 11948674778.

Final extracted setup WS is 0 at all corners, fast hold 90.416 ps, capacitance and antenna violations zero. Six fanout violations and three slow-slew rows reject the route. WS 0 is not a claim of positive global setup margin. Phase 2 and official GDS remain incomplete.

## Confirmed connectivity changes

Compared actual screened GRT DEF/eco netlist against final DRT DEF/netlist. Every original logical cell and connection is preserved; additions are audited antenna cells on existing nets. The six failing fanout nets all change from eight to nine loads:

| Driver | Added diode |
| --- | --- |
| `_29536_/Y` | `ANTENNA_635` |
| `_44515_/X` | `ANTENNA_637` |
| `_45868_/Q` | `ANTENNA_639` |
| `place7855/X` | `ANTENNA_645` |
| `place8798/X` | `ANTENNA_647` |
| `place8991/X` | `ANTENNA_646` |

The remaining slew failure is one net `_17463_`, driven by `_44692_/Y` (NAND4_1), with the same two sinks before and after routing: `_44693_/C` and `ANTENNA_191/A`. Worst transition is 2.596800 ns versus 2.507400 ns. No new diode appears on this net. The unchanged connectivity supports parasitic-estimation drift, rather than added connectivity, as the explanation; this comparison does not isolate individual resistance/capacitance contributions.

OpenROAD [global routing](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html) can insert antenna diodes. [Estimated parasitics](https://openroad.readthedocs.io/en/latest/main/src/est/README.html) and [extracted routed parasitics](https://openroad.readthedocs.io/en/latest/main/src/rcx/README.html) use different wire information. Thus a strict green screen is necessary but does not guarantee extracted closure.

## Prepared local screen

`route_reserve_plan.py` binds exact NL/DEF/three-corner electrical/fast hold report hashes from route 38679335674. It partitions the six overloaded nets into BUF4 branches of at most four existing loads, and isolates the NAND4's two output loads behind one BUF4. Total: 19 BUF4 cells, 275.7888 um² added cell footprint, zero computed footprint overlaps, no resizing, hold delay cells or protected clock/reset-pin rewiring. All existing diodes remain connected through the reviewed identity-buffer partition. Physical legalization and timing are unmeasured.

The pinned LEF contains NAND4_1 but no NAND4_2; a simple NAND4 upsize is unavailable. Buffering every eight-load net is also unattractive: the final DEF contains 1,519 exactly-eight-load data nets with a unique X/Y/Q driver and no protected sink pin, including 30 with antenna diodes, plus 198 such eight-load nets with protected pins. This count is a diagnostic subset, not a complete STA fanout inventory.

`gds-route-reserve-screen.yaml` is manual and screen-only. It retains all existing strict timing/electrical/antenna/live-overflow gates and adds a **maximum six-load internal reserve** on the seven repaired source nets and 19 new branches after GRT antenna repair. Final acceptance remains max fanout eight and fast hold at least 50 ps. A green result still cannot guarantee no additional diodes or extracted slew regression. No DRT workflow is dispatched automatically.

Validation: 20 focused tests passed; actual-source proposal and geometry allocation passed; synthetic application of the exact proposed pin moves passed connectivity conservation; generated Tcl passed syntax-completeness check. These are preparation checks, not executed physical ECO evidence. User approved publication and launch on 2026-10-15. Tools commit cae00c9 and CI commit 7a80b08 prepare this screen; physical results remain pending.

## Next decision

Run the reserved screen before any DRT. If it passes, inspect the per-family reserve and slow-corner transitions before authorizing routing. Separately investigate a bounded post-DRT antenna/electrical repair loop with fresh extraction: the pinned router can reinitialize capacities on detailed-route input, so cold incremental routing requires explicit live-capacity, DRC and connectivity audits. Do not remove necessary diodes, loosen gates or claim official closure from experimental checkpoints.


## Reserve screen result and routing continuation

[Screen 38687129808](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38687129808) succeeded on exact main head 682ba0d0c8cabc032eaa927f031e18baf4b31d96. Bulk artifact 11951605789; gate artifact 11950034250.

- Setup WS 0 and no reported setup/hold violations at all three corners. Hold slack fast/typical/slow: 72.5907 / 168.950 / 340.245 ps.
- All-corner slew/fanout/capacitance counts zero, antenna nets/pins zero, live GRT overflow zero.
- Nineteen planned BUF4 plus three BUF4 from one bounded post-antenna batch. All 26 reviewed source/branch nets have at most four loads; internal six-load reserve passes.
- Independently recomputed exact proposal from pinned source reports and LEFs; checked baseline identity, logical conservation, post-antenna history, original placements, live routing capacity/overflow, strict gates and actual family loads using downloaded artifact views. All passed.

Prepared `gds-route-reserve-route.yaml` and `route_reserve_route.py`. They bind the complete successful receipt and screen SHA, recompute reserve from the saved DEF, repeat existing checkpoint/antenna/connectivity/placement checks, then perform fresh stock pre-DRT qualification, detailed routing and extraction without another full GRT/ECO pass. Final timing/electrical/antenna gates remain unchanged. Early summary upload precedes bulk evidence. Thirty-four focused tests pass. Routing/extracted signoff and official GDS are still unproven.

## Reserve route result: repair held, failures moved elsewhere

[Route 38689478738](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38689478738), main 54c32ceb682e3cbd7deb68e83c5d4b6400e0ad5f, fails final extracted electrical gates. Bulk artifact 11953303980; gate artifact 11953845578.

Actual final DRT state has `route__drc_errors = 0`. Setup WS is 0 at all three corners; fast/typical/slow hold slack is 89.0939/195.2136/382.3021 ps. Antenna and capacitance violations zero. Two fanout rows and twelve slow-slew rows remain. Thus routing DRC closure is achieved for this experiment; electrical closure and official GDS are not.

Independent before/after DEF/netlist comparison confirms:

| Driver | Screen loads | Final loads | Change / failure |
| --- | ---: | ---: | --- |
| `_28909_/X` (OR2_1) | 8 | 9 | New `ANTENNA_663`; fanout |
| `place8952/X` (BUF8) | 8 | 9 | New `ANTENNA_670`; fanout |
| `_29530_/Y` (NOR2_1) | 5 | 5 | Same connections; slow slew |
| `_33280_/Y` (NAND2_1) | 7 | 7 | Same connections, including existing ANTENNA_149; slow slew |

The twelve slew rows map to these **two** driver nets, not twelve nets. Worst transition 2.552041 ns versus 2.507400 ns (1.78% above limit). All 26 repaired source/branch nets retain at most four loads even in the final DRT DEF. The previous repair was effective on its reviewed families; a family-local gate cannot protect other marginal nets.

### Revised closure strategy

1. **Measure design-wide near-limit electrical margins before choosing more cells.** Existing `checks.rpt` uses `report_check_types ... -violators`; legal but fragile nets are invisible. Collect per-net worst slew and capacitance, fanout, driver master, diode counts, and protected-clock/reset status from the same green checkpoint and extracted final checkpoint. Bind the same libraries/corners/signoff SDC. Derive wire-estimate error and group risk by driver/load class; prioritize a bounded area budget rather than buffering all 1,500-plus eight-load data nets.
2. **Repair the risk class, not just the failed rows.** Study internal slew reserve (initial candidate 10%, calibrated from the paired data), and fanout spare capacity on diode-exposed nets and nets that acquired diodes across recent runs. Use native slew/cap repair with a verified area/cell budget and all-corner hold rechecks. High-capacity BUF8 nets can still fail a discrete fanout limit; upsizing alone cannot fix their load count. Protect functional clock/reset topology and existing hold repairs. Required final limits remain unchanged.
3. **Bring antenna consequences into the electrical fixed-point loop.** Evaluate a conservative GRT antenna margin, followed by electrical repair and fresh GRT/antenna/timing checks until the bounded screen converges. Current actual GRT margin is 10%; increasing it is an experiment, not a guarantee that post-DRT diodes disappear. It may increase load/area, so this must be judged jointly with electrical repair.
4. **Develop a route-preserving final correction path.** The strongest long-term flow closes electrical checks after the last antenna topology change, then re-extracts all corners and repeats DRC/antenna checks. Prototype one local edit on a saved zero-DRC checkpoint and prove unrelated-route preservation and live-capacity accounting before scaling. The pinned built-in post-GRT repair script always calls full GRT before resizer (comment references OpenROAD issue 5590), so inserting that stock step after DRT would destroy the intended preservation. It needs a reviewed custom continuation, not a blind stock-step insertion.
5. **Use logic/architecture changes only if measured cone structure demands them.** Present residual slew drivers are ordinary NOR2_1/NAND2_1 cells; there is no current evidence that protocol engines or the instruction architecture need redesign. A topology-preserving drive-strength repair may be efficient, but it must be selected from a complete margin inventory to avoid moving the failure again.

### Rejected shortcuts and pinned-tool findings

- Pinned `GlobalRouter::repairAntennas` performs jumper insertion only when `!haveDetailedRoutes(nets_to_repair)`. Setting jumper-only for a detailed-route source can suppress diode insertion without supplying the intended jumper fix; antenna signoff still has to pass. Do not treat this as a ready solution.
- The pinned LibreLane 3.1.0.dev3 `drt.tcl` passes `GRT_ANTENNA_REPAIR_MARGIN` into the post-DRT repair command, despite also exposing a separate DRT margin variable. Changing only `DRT_ANTENNA_REPAIR_MARGIN` would not change this script's actual repair argument. Current source config sets both to 10.
- Raising iterations, changing seeds, or reducing clock frequency does not directly repair the observed discrete fanout and maximum-transition failures. Lowering frequency is not the first response to passing setup/hold with electrical violations.
- A zero-violation screen and a positive hold number are necessary evidence, not a prediction of official GDS success.

Research references: [OpenROAD resizer](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html), [global routing and antenna repair](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html), [OpenSTA report commands](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/search/Search.tcl). Pinned implementation findings above were checked against the locally cached LibreLane 3.1.0.dev3 wheel and pinned OpenROAD source, rather than assuming current documentation matches the installed tool.

## Paired electrical-margin diagnostic prepared

Added `gds-electrical-margin-probe.yaml`, bound to failed route 38689478738 / head 54c32ceb682e3cbd7deb68e83c5d4b6400e0ad5f. It downloads that artifact (which includes the green screen and final extracted state) and uses the pinned flow's `STA_EXTRA_CORNER_TCL_FILE` hook. No custom tool image is needed.

The hook queries every hierarchical net with `report_check_types -net ... -format end`, including legal checks, on each of the three corners. Screen views use STAMidPNR/GRT parasitics; final views use STAPostPNR with saved extracted SPEFs. Both use exact `src/signoff.sdc` bytes, checked against the previous extraction constraint receipt. It runs no placement, resizer, antenna repair, routing or RCX steps. Source state/view hashes must be unchanged after measurement.

The parser requires explicit begin/end receipts, unique net markers and complete corner coverage. It records utilization of each reported net's worst slew/capacitance/fanout constraint, counts nets at 90% or more of their limits, and compares matched net/corner/check utilization to identify newly failing nets and the largest drift. Nets without a reported constraint remain visible as entries without a check, rather than being counted as measured passes. Diagnostic output is not a qualification gate. Comparing a worst check on a net can select different sinks between stages; it measures net-level risk, not a fixed-pin RC decomposition.

Validation: 25 focused tests pass, plus a real local OpenSTA API smoke test on a two-buffer toy design, checking valid per-net slew/cap measurements and successful parser ingestion. The smoke test caught and corrected verbose output's vertical format before publication. Pinned-flow execution is still required. Probe output upload contains only the new diagnostic directory, avoiding another inherited multi-gigabyte upload.
