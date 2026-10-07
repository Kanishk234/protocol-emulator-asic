# Event-late hold-headroom experiment (2026-10-06)

Leading measured candidate: event-late source37533969613,route37546499438,extraction37551577987 and routed GL37551578053. Extracted setup WS0at all corners; fast hold−0.014614976310ns,slow+0.104597222733ns,typical+0.030520697944ns. Final min report contains three violating entries: lane1ex_imm[6]−14.615ps,[7]−7.615ps,U0TXct[0]−6.856ps. GL log confirms22/22tests,0failure/skip. Its setup worst report includes a flop→latch zero-slack borrowing path; positive useful-path headroom remains to audit.

Original repaired screen config uses GRT_RESIZER_HOLD_SLACK_MARGIN0.05ns and SETUP0.0ns. Pre-route fast hold+0.0313302ns became−0.014615ns after route/extraction. The proposed isolated experiment uses a100ps hold-repair target on the same verified source checkpoint before antenna/DRT, aiming to retain headroom through physical changes. No guarantee that a larger target achieves it; actual extracted results decide.

Existing route workflow gains optional pre_route_hold_target choice source(default)/0.10. The new choice is restricted to bs-event-late and performs exactly one all-corner repair with setup target0.0 and hold target0.10. Require fresh setup/hold checks to pass at all corners and fast hold WS≥0.05ns before continuing. Existing post-antenna timing/antenna and route DRC gates remain. Saved headroom comparison is included in downstream extraction artifacts. Constraints,20ns clock,resources,RTL,source identity and official template jobs are unchanged.

Helper validates the selected hold target against resolved repair configuration and rejects unbounded/NaN/infinite values.131combined helper tests pass, including default preservation, explicit target propagation, all-corner/headroom gating and invalid-target rejection. Both edited workflows parse,choice/default checks and git diff check pass. Tcl tests use cached OpenSTA's Tcl runtime via temporary launcher, not physical OpenDB.

Proposed dispatch: source_run_id37533969613,source_variantbs-event-late,pre_route_hold_target0.10,repair_postantenna_holdfalse. CI/docs publication and launch pending scoped authorization. No physical hold improvement,combined RTL adoption or official timing pass claimed. Local resync combinations and SRAM-delay prototype remain separate unpublished work.

## Measured 100 ps trial and proposed 150 ps follow-up

Run37557256170 failed before antennas/DRT at the unchanged50ps headroom gate. Fresh fast hold improved31.3302→48.7026ps; slow229.262→376.427ps; typical102.516→178.650ps. Setup WS remained0allcorners. Extraction37558180965 andGL37558180997 skipped; there is no new extracted result.

The actual repair log reports241 endpoints below its100ps target and255 inserted buffers (+0.8% area). It reached100ps internally, then legalized (maximum displacement14.9um) and rerouted. Fresh STA's worst path is slot latch `_50151_` (`lane0.slots[461]`) through `_34673_`, `_34675_`, `_34676_`, `_34677_` to `_46523_` (`lane0.acc_addr[4]`), +48.703ps. Next reported endpoints are U2RXsst[2]+55.372ps, U2TXer[1]+55.628ps and lane0ex_imm[3]+59.044ps. This is not the original extracted event failing endpoint set. Saved artifact11454893508, local audit `/tmp/event-headroom-audit`.

Prepare an optional150ps repair target on the original trusted event source37533969613 (not an automatic retry of the mutated state). Keep zero setup target, one repair, fresh all-corner pass,50ps minimum fast hold, antenna/DRC guards and final extracted checks. Default remains source;100ps remains reproducible. Extra buffering may hurt setup or routing; no physical success asserted. Changes are local pending publication.

All1000 entries in this trial's slow max report end at latches and have zero reported slack. This report cannot establish execution-path setup margin; a separate flop-endpoint report is needed without changing constraints or hiding latch checks.

## Independent execution endpoint audit while 150 ps trial runs

Replayed source extraction37551577987 locally using its actual fill-inserted netlist,nominal extracted SPEF and emitted final SDC (20ns,propagated clocks,setup uncertainty0.25ns,hold0.10ns,IO4ns andearly/late0.95/1.05derates). Used cached PDK standard-cell and matching frozen SRAM libraries. No missing-cell/annotation errors reported; no IO pad instances in this design. Local OpenSTA2.6.0aa598a2f14 differs from the pinned CI tool,so this is independent endpoint analysis,not replacement signoff evidence.

| Corner | Worst flop-endpoint setup slack (ns) | Worst output setup slack (ns) | Global hold slack (ns) |
|---|---:|---:|---:|
| Fast |12.147419|13.448309|−0.014615|
| Slow |1.223082|10.259272|0.104597|
| Typical |8.164472|12.286599|0.030521|

Hold agrees with published extracted metrics to displayed precision at all3corners. Slow worst flop path is lane0a_lat[13] (`_46588_`)→lane0rpc[2] (`_46493_`). Local unrestricted setup report also returns this path,whereas pinned CI reports0at latch endpoints. Treat this difference as a tool/report-semantics limitation: retain full latch checks and do not relabel official/global WNS as positive. Flop-only reports from the exact pinned engine are still needed to confirm this margin. The evidence supports prioritizing measured hold repair;150ps repair has not yet completed. Scripts/logs under `/tmp/event-final-audit/execution-*`.

Prepared local reporting-only helper `scripts/ci/execution_margin.tcl` for an already-linked/constrained/extracted STA session. It retains global reports and independently selects4504flop,2065latch and24output endpoints on this candidate. Executed with the saved extracted design at all3corners; flop/output/hold values reproduce the independent audit above. Local2.6engine emits no paths for the2065latch endpoints,while pinnedCI previously reported zero-slack latch paths. This confirms the local analysis is incomplete for latch timing and cannot support any global-closure claim. The helper has not been integrated into remote workflows or published; pinned-engine execution remains required.

## 150 ps extracted result: hold closes, setup regresses

Route37559740009 completed successfully; extraction37566926240 completed diagnostically. Fresh pre-route fasthold+0.120978ns became extracted+0.067033713810ns (loss53.944ps). Slow hold+0.379780995180ns,typical+0.184989584442ns. Setupfast/typicalWS0; slowWS−0.389409404633ns. Therefore this candidate is not timing-closed despite successful diagnostic job status.443hold buffers were inserted versus255in the100ps trial. RoutedGL37566926287 is active.

Inspect actual slow max paths from artifact11459002750 before selecting a follow-up. A smaller bounded hold target or selective delay placement may reduce setup damage,but margins are not assumed linear and should not be chosen without the path audit. Official native proposal's150pshold setting is now unproven forsetup andmustnotbe promoted as a passing recipe.

## 150 ps setup-path audit

Actual extracted slow max report contains11violating entries:9dropped-counter endpoints and2U3RXtimer endpoints (`rt[23]`/`rt[22]`). Launches are U1/U0configword1bit1 (PIN_Aselection),not the earlier PERIOD/TXMODE cones. Worst U1PIN_A1→dropped[15]−0.389409ns includeshold12461 dlygate4sd3_1 adding0.662608ns; secondU0PIN_A1→dropped[31]−0.344089ns includeshold11765 adding0.617550ns. Remaining failures do not contain such finalholdbuffers in their reported data paths. Thus broad hold-repair delay androuting/slew effects both matter; removing two cells alone does not establish closure.

Preparing isolated event-late+drop-qual from frozenhardware. Parallel per-source drop qualification is alreadymodule-equivalent; combining it with event-late targets most failing counters while retainingliveconfig/same-cyclebehavior. It doesnotdirectlyaddress RXtimer failures andhasno measuredtiminggain. Combinedfunctionalverification mustfinish before anyphysicalscreen orpromotion.

Isolatedevent-late+drop-qual prototype completed:drop-qualification equivalence passes atN1/5/6/7/9/16 (event-late unchanged frompreviousprovenpatch),channeltests pass,5/5chiptests pass,and2048clockL2lockstep passes. Rawproof/tests under /tmp/event-drop-qual-20261006. Combinedpatch `spikes/r4_floorplan/bs_event_drop_qual.patch` preparedlocally; notpublishedorregisteredinremotechoices andnotphysicallymeasured. This prototypetargetsreportedcountercone,notall11violations.

## Bounded 125 ps follow-up prepared

The route workflow now accepts 0.125 ns only for the trusted event-late source. Regression checks: 135 passed across post-GRT timing, placement routing and route provenance; workflow choices/default parsed and diff check passed. All gates remain intact. This local change is not published or launched yet. Use source run 37533969613, variant bs-event-late, pre_route_hold_target=0.125, repair_postantenna_hold=false after publication.

Prioritize low-area alternatives if this misses either corner: target delay sizing on actual failing fast paths, strengthen only measured high-delay gates, or move dropped-counter control after state-derived carry. Each needs independent equivalence and matched physical evidence. Avoid broad buffering or new configuration storage. The RX arithmetic experiment is currently running but its isolated 29.4% area increase makes full-chip overflow an adoption gate.

## 125 ps routed result and pending extraction

Route37574267994completed successfully with final routeDRC0. The extra repair inserted180holdbuffers;resizer reports2.7% sizing/repair area growth within this pass. Buffer counts do not establish lower full-design area versus the other targets. Fresh repaired fast hold0.0974116ns;postantenna0.0991903ns. Postantenna slow/typical hold0.367636/0.203499ns;setupWS0allcorners. Detailed routing consumed roughly58minutes after repair/checks.

Extraction37581139249and expanded routedGL37581139271are active. These are diagnostic continuations; extracted setup/hold and protocol outcomes remain pending, and official GDS/precheck closure is unproven. The workflow's single long step includes repair,antenna andDRT,so its active name cannot identify the exact internal stage.

## Residual endpoint report helper

Published reporting-only `scripts/ci/execution_margin.tcl` retains unrestricted setup/hold and separate flop/latch/output reports. Optional `tripwire_report_residual_cones` selects96RXtimer D pins,72dropped-counter D pins and9SRAMaddress pins by preserved net names;reset/control pins are excluded from targeted flop groups. It fails if a required group is absent. It changes no constraints or hardware.

Executed against original event extraction37551577987 with saved emittedSDC/SPEF at allthreecorners using localOpenSTA2.6.0. Allgroups present and allsixgroup reports produced percorner. Slow targetedsetup margins:RX2.762297ns,dropped2.012822ns,SRAMaddress11.371373ns. These describe the original weaker-hold candidate,not125psrouting orRXprototype. Localengine's missing latch paths remain a limitation; pinnedCI replay required before using endpoint results to judge adoption or signoff. Rawlogs:/tmp/event-final-audit/residual-cones-*.log.

## 125 ps extracted timing (37581139249)

Completed diagnostic reports setupfast/typical0,slow-0.179788633514ns;holdfast+0.037289505872ns,slow+0.369336571780ns,typical+0.165097162836ns. Thus125psimproves slowsetup versus150ps(-0.389409ns)andpasseshold,but stillfailssetup. Fastholdloses61.9008ps frompostantenna+0.0991903ns. Do notpromoteasclosedorofficial-ready. RoutedGL37581139271stillactive. Inspectactualslowpaths beforeselecting another repair/RTL change.

## 125 ps setup-path audit and targeted follow-up

Artifact11464064023,extraction37581139249:the slowmax report contains exactlytwo failing entries among1000paths. Both launchU0PIN_Aselection(configword1bit1) and endU3RXtimer:rt23(_47775_) -0.179789ns,rt22(_47774_) -0.052855ns. No finalholdcell appears in either reported data path;the150psdropped-counter failures are absent here.

The common cone has slowarcs_o21ai_1(_25443_)1.166990ns andxor2_1(_25445_)1.305548ns feedingunit3sel,thenNOR2_1(_27853_)0.820204ns andNOR4_1(_27962_)0.785984ns. Pinnedlibrary hasNOR2_2/NOR4_2 alternatives but no strongerXOR2/O21AI variant. Selective fanout/drive changes are a small-area fallback;anupsizedNORincreasesupstreamcapacitance,soactualall-cornermeasurement isrequired.

SharedRXscreen37579966660alreadytargets these timerpaths. Preparedrouting allows that exactvariant onlywith125pstarget;existingevent-latechoices/defaultandallgates unchanged.171helpertests pass,including25source/targetauthorization cases. Routeonlyafter source screen passes,thenextractandrunfullprotocolGL;no continuation launched yet.
