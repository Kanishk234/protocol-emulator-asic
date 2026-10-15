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
