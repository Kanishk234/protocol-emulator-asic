# Phase 2: close hold before antenna cleanup

## Evidence and decision

Full inline-guard screen [41759551888](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/41759551888) failed with6antenna nets/pins and40Metal3overflow, despite clean electrical checks, setup0allcorners and fast hold+0.138072ns. All64guard gates/12nodes survived. Reject this candidate; preserve reference41569397169(4antennas,0overflow). Detailed routing remains blocked. Full result receipt:spikes/phase2_stock_flow/inline_guard/result_41759551888.json.

The reference's saved post-antenna/pre-late-timing checkpoint was independently audited in [41582335231](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/41582335231): fresh antennas0/electrical0/setup0but fast hold−0.0163279ns. Disabling late repair alone does not qualify it.

Eight of1000reported fast min paths fall below the50psreserve. The original report gives these rounded slacks; these are reported paths, not an exhaustive endpoint census. Names are mapped FF identifiers from this reference only.

| Start FF | Capture FF | Slack ns | Gap to50ps ns |
|---|---|---:|---:|
| _51562_ | _51476_ | −0.016328 | 0.066328 |
| _51565_ | _51479_ | −0.012652 | 0.062652 |
| _51563_ | _51477_ | 0.007611 | 0.042389 |
| _51558_ | _51558_ | 0.014586 | 0.035414 |
| _51557_ | _51471_ | 0.027150 | 0.022850 |
| _51564_ | _51564_ | 0.027218 | 0.022782 |
| _51514_ | _51514_ | 0.044804 | 0.005196 |
| _51536_ | _51536_ | 0.048784 | 0.001216 |

## Short diagnostic prepared locally

Extend our separate gds-stock-checkpoint-audit workflow, selecting shared_minbuf2_postant. Retain hash-bound restore, unchanged source-view hashes, repeated3corner STA and fresh whole-design antenna checking. Add bounded FF min-path reports below0.05ns with100000paths per group/one path per endpoint, plus NL/PNL readbacks directly from loaded ODB. Record readback hashes independently from inherited source netlists. No resizer, placement, routing, source promotion or acceptance-gate change. Latch and other endpoints remain covered by existing whole-design STA; the new FF report is diagnostic only. Never claim complete endpoint coverage from the report cap.

Local validation:31focused tests pass; parser replay against the eight actual archived shortfalls gives2negative paths and largest gap66.328ps. Workflow YAML/embedded shell/Python syntax pass. Exact report flags checked in pinned OpenSTA43177bba8f5f88dfb7dc35795242080a4fe2e986(search/Search.tcl). Native execution of the new report hook remains pending publication and CI. No new full build or DRT launched.

## Congestion evidence must be solved separately

Do not qualify post-antenna congestion using the earlier stage41zero-overflow table or persisted DB map alone. Pinned OpenROAD26Q2GlobalRouter.cpp shows incremental antenna updates need not refresh that map. A read_guides shortcut is also untrusted:readGuides calls updateEdgesUsage, then computeGCellGridPatternFromGuides, whose FastRouteCore::init3DEdges reinitializes usage before updateDbCongestionFromGuides. This source inspection rules out assuming guide-import readback reproduces true demand; no runtime equivalence claim is made.

Primary sources inspected:OpenROAD26Q2src/grt/src/GlobalRouter.cpp,src/grt/src/fastroute/src/FastRoute.cpp andsrc/grt/include/grt/GlobalRouter.h. Tool code/command ordering remains unchanged. An authoritative final-stage native routing report on any future full screen remains required.

## Next decision

Use fresh hold-frontier/ODB readback evidence to confirm the paths and circuit. Then assess one controlled earlier-hold-target experiment on unchanged reference hardware. Raising early target from175to250ps is a candidate, not an established fix:75psdoes not translate directly to75psfinal slack. If late repair is disabled for an experiment, require valid final-source congestion and consistent views; current qualification must not fall back to an earlier clean report. All3corner timing,50psfast reserve,electrical0,antenna0and overflow0must pass together before detailed routing. Official GDS jobs,20nsclock,SDC and main hardware/config stay fixed.
