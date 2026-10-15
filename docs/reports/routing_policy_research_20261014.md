# Pinned-router obstruction research, 2026-10-14

Best fanout-clean compact control remains 133 overflow. This addendum proposes diagnostics, not a routing fix or a hardware/specification change. Original 50/150-iteration runs, CUGR, mirroring, smaller delays and broad redistribution already failed to improve the control; do not rerun those policies without new evidence.

## Verified version and relevant upstream evidence

The first line of retained `build/cloud_boundary_38456351705/export.log` and `build/cloud_cfg_fanout_local_38101405271/buffer.log` identifies OpenROAD `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`.

1. [Issue 3020](https://github.com/The-OpenROAD-Project/OpenROAD/issues/3020) reports guides crossing a completely obstructed intermediate layer. The issue page is closed as **not planned**, with a stale label; closure is not evidence of a validated fix. A later discussion suggests blockage improvements, but that does not demonstrate applicability to WARP.
2. The cited [instance-blockage modeling commit 5374a1b](https://github.com/The-OpenROAD-Project/OpenROAD/commit/5374a1bd89c4a34109d2340c32c8cb9f7e6f2e72) replaces a merged per-layer rectangle with multiple rectangles and models overlaps on adjacent layers. The GitHub [ancestry comparison](https://github.com/The-OpenROAD-Project/OpenROAD/compare/5374a1bd89c4a34109d2340c32c8cb9f7e6f2e72...dcf36133a369abc8f3c5e5738cd4d82e4903c0e0) reports the installed revision ahead, with zero commits behind. This old change is already in our history: **do not propose upgrading to get it**. No specific newer fix was established in this research pass.
3. In the [pinned maze.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/maze.cpp), `getCost` uses a finite logistic/history penalty, and the inspected neighbor relaxation derives its cost from usage/reduction/history. That relaxation does not explicitly prohibit zero-capacity edges. Inference: an intermediate overflow-producing route through an obstruction can be an unsuccessful negotiation result, not proof that the physical obstruction was omitted. This source inspection does not prove the exact cause of WARP's 133 overflow or cover every router stage.
4. Official [ORFS troubleshooting guidance](https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts/blob/master/docs/user/FlowVariables.md) recommends reducing a failing route case because one impossible connection can disturb otherwise routable nets. Its example includes a clock connection over a macro. We can apply the diagnostic principle using a command verified in our pinned documentation, without changing capacities or taking its separate capacity-tuning suggestion.

Downloaded pinned source SHA256: README `024a28ab6f14b0ad80d0cd6c09e9a3a44aa4a0bc060f4f9fa8fd420456c25431`; maze.cpp `2e246dad9c6c07839b6ebceb35e765b2c4c43fdefa49c9041a453c4822bb11b3`. No upstream source was edited.

## Ranked next diagnostics

**First: finish actual segment attribution on the exact 133 control.** Retain the native routing error, original congestion report and capacity data, then inspect actual segments for `cell_val[30]`, `cell_pad[27]`, `cell_pad[31]` and `cell_val[27]`. Guide rectangles overlapping a macro are insufficient: they can include broad coverage or pin-access regions. Distinguish preferred-direction edge traversal, layer changes, terminal access and full-interior traversal. The separately prepared trace collector must reproduce the control before its exported evidence is interpreted.

**Second: isolate only confirmed suspect connections.** The [pinned GRT README](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/README.md#Set-Specific-Nets-to-Route) explicitly documents `set_nets_to_route`. Example Tcl literal:

```tcl
set_nets_to_route {cell_val[30]}
```

Use the actual full database net name and confirm it resolves exactly once before routing. Route a singleton, then only the smallest relevant pair if needed. Keep every original instance, macro obstruction, boundary pin, routing layer and capacity policy; start each case from the authenticated unrouted checkpoint. Do not delete unrelated cells or physical blockages to reduce the case. Compare the complete native capacity arrays with the control because selecting nets can affect pin-dependent adjustments. If arrays differ, report that confound instead of claiming a controlled congestion comparison.

Interpretation:

- Isolated connection still crosses a fully blocked interior: prioritize terminal-access/grid-representation analysis and a minimal router reproducer. Extra iterations or broad placement lack a demonstrated reason to help.
- Singleton routes cleanly on identical capacities but the pair/full set fails: competition or negotiation becomes more plausible. It is not proof a particular net-order policy will solve the full design.
- Guide overlap disappears when actual segments are inspected: stop treating guide rectangles as direct evidence of an illegal route.
- Any selected-net success is diagnostic only. Unselected nets are deliberately unrouted; it cannot pass whole-chip routing or timing.

The pinned README also documents `global_route_debug -saveSttInput ... -net ...`; use this only if terminal/grid mapping remains unclear. The current exporter work may already provide sufficient detail, so avoid another collector unless something specific is missing.

**Third: choose a fix only from the reduced failure.** If correct terminal access and a legal alternative are demonstrated yet the pinned search repeatedly crosses zero-capacity interior edges, investigate a separately pinned search-cost/obstacle-handling patch with an upstream regression. A hard prohibition can strand legitimate pin-access stubs, so blindly replacing finite penalties with infinity is unsafe. No supported Tcl option for that change was established. Any patch needs exact source provenance, license retention, existing pin-access regressions, and an unchanged-capacity full-control comparison before considering detailed routing.

No ambiguous whole-tool upgrade or new seed sweep is recommended. No capacity increase, congestion acceptance, macro obstruction removal, hold-margin relaxation or hardware change is proposed by this document.
