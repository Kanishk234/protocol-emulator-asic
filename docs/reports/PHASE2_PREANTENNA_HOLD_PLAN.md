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

## Native audit result and next controlled screen — November 4

[Checkpoint audit 41786909156](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/41786909156) passed in 7m26s on 94d1395. Independently checked all six raw corner reads, report summaries, readback hashes and fresh antenna metrics. It reports exactly the same eight fast-corner FF paths below 50 ps (two negative), with none reported in typical or slow. The report cap is 100000 per path group; this remains bounded reporting. Whole-design setup is 0 ns in all corners; hold fast/typical/slow is −0.0163279/+0.106528/+0.323963 ns; electrical and fresh antenna checks are zero.

The direct ODB netlist readback preserves all 44933 parsed existing non-fill/non-decap instances and their connections compared with the inherited stage41 netlist, adding exactly ten sg13cmos5l_antennanp instances. The same readback hashes repeat in all three corners. This resolves the circuit-view question for this checkpoint, not its final congestion or hold qualification. Raw verification receipt: minbuf2_hold_frontier_result.json under spikes/phase2_stock_flow.

Prepare rtl_shared_minbuf2_early250, compared directly with 41569397169. Change only PL_RESIZER_HOLD_SLACK_MARGIN from 0.175 to 0.250 ns. Keep late repair at 0.175 ns, late rerouting enabled, stage order, min-BUF2 policy, shared-priority hardware, 20 ns clock, SDC, density, SRAM and every final acceptance gate fixed. This tests whether earlier hold closure reduces later repair damage; it does not assume a one-for-one slack gain or guarantee clean antennas. Unlike the earlier provisional late-off idea, this experiment retains the authoritative final native rerouting report used by existing qualification.

Exact archived CI preparation, source/macro hardening-view comparison and pinned TT configuration generation pass. Both project and merged configuration differ from the reference only at that early hold target. 102 focused tests pass. Evidence: minbuf2_early250_preflight.json. Retire the failed inline-guard choice from the launch menu while retaining its profile and evidence. No main hardware/config or official GDS job changes. Detailed routing still requires all final gates to pass together.

## Early250 outcome: reject — November 4

[41788634487](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/41788634487) completed physical flow and fresh all-corner audit, then correctly failed final qualification after about 4h02m. Independently verified selected raw reports, final native routing table and violating antenna-pin sections. Setup WS is 0 ns in every corner; hold fast/typical/slow is +0.121930/+0.331854/+0.707296 ns; electrical checks are zero. Antennas are 11 nets/11 pins; final overflow is 179 (Metal2:1, Metal3:176, Metal4:2).

The requested early 0.250 ns control was exercised. Final cells are 47142 and area 717376 µm², versus 45099/688086 in reference41569397169: +2043 cells and +29290 µm². Native late repair reports 89 endpoints/14 inserted hold buffers, compared with reference170/7. Fewer reported endpoints did not mean less inserted buffering or a cleaner final layout. Reject this profile and retain the reference. Raw receipt: minbuf2_early250_result.json. No detailed routing.

The broad earlier-target hypothesis failed this controlled test. Next prepare a bounded native-tail diagnostic from the hash-bound reference post-antenna checkpoint, testing a smaller late hold target (candidate 0.075 ns versus 0.175 ns) while retaining native late rerouting and mirroring. This is not the previously tested two-variable early275/late075 recipe. It must run fresh repeated corner STA, fresh whole-design antenna checking and validate the routing report against the exact final physical database. Any changed qualification support must reject stale earlier routing evidence. Calibration and preparation are required before launch; no new full build or tail run was dispatched this session. The lower target does not weaken the fixed 0.050 ns acceptance reserve and is not a guaranteed fix.
