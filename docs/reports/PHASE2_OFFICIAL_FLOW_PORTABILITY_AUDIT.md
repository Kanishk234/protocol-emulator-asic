# Official-flow portability and SRAM locality preparation

## Finding

A clean build can receive a standard-cell locality policy through the existing LibreLane Classic `Odb.ManualGlobalPlacement` step and `MANUAL_GLOBAL_PLACEMENTS` key. This is a plausible integration route, not proof of official GDS closure. No main configuration or template job changed.

Inspected exact upstream sources:

- Tiny Tapeout action CMOS5L revision `3412659307918422f3f0727917cf9b499aaca588`: default LibreLane `3.1.0.dev3`, calls `tt_tool.py --create-user-config`, then `--harden`. [Action](https://github.com/TinyTapeout/tt-gds-action/blob/3412659307918422f3f0727917cf9b499aaca588/action.yml).
- Support tools CMOS5L revision `d66cf179e7bc4d296362ab7e2e3b344dc3c4f665`: generated user configuration overrides matching base keys; hardening invokes LibreLane on merged config and clears the old wokwi run. Archived ODBs and helper files are not automatically inputs. [Project entry](https://github.com/TinyTapeout/tt-support-tools/blob/d66cf179e7bc4d296362ab7e2e3b344dc3c4f665/project.py).
- Pinned LibreLane `3.1.0.dev3`: Classic runs RepairDesignPostGPL, ManualGlobalPlacement, DetailedPlacement, CTS and subsequent native timing/routing repair. [Classic](https://github.com/librelane/librelane/blob/3.1.0.dev3/librelane/flows/classic.py).
- Built-in placement key describes coarse, unfixed, non-legalized placement; operation uses instance names, converts micron coordinates to DB units, marks PLACED and fails on missing instances. [Step](https://github.com/librelane/librelane/blob/3.1.0.dev3/librelane/steps/odb.py), [operation](https://github.com/librelane/librelane/blob/3.1.0.dev3/librelane/scripts/odbpy/placers.py).

## Actual clean-build evidence

From artifact11715973741 (route38172640071), retrieved inherited native-stock-screen stage32 RepairDesignPostGPL,37 ResizerTimingPostCTS and43 ResizerTimingPostGRT netlists. Direct SRAM buffers wire9447/wire9439/wire9438/max_cap9445 already exist at stage32; all16 directly connected BUF4s are available for the normal manual-placement stage. This corrects the initial concern that these names might only exist too late. They remain implementation-generated names, so new synthesis/PDK/recipe changes can invalidate them.

Clean pre-placement NL SHA `2b3925b0d3fb308d16ea07b3b10e9f72598b74cec330c1b147072a8ac47ba9f0`; DEF SHA `337c6b32c5325e2da7a68d139f4f7ecc7b80d836e85e8e3456470302e5f8661d`. Original clean source37990280838 and retained routed source38172640071 have separate planner provenance and hashes. The new screen refuses a pre-manual clean topology that differs from the reviewed reference.

## Prepared experiment

`sram_bank_plan.py` validates exact NL/DEF and macro/standard LEF geometry, derives all16 SRAM pin centers from the fixed12,40 FS macro, reserves complete legal-row footprints sequentially and checks the combined final geometry. It proposes14 existing-buffer moves on retained DRT, or16 on the distinct original clean post-GPL stage. Added cells/master changes/logical changes0. Candidate fragment uses micron coordinates for built-in manual placement; raw hypothetical DEFs and proposals stay/tmp.

`sram_bank_clean_screen.py` prepares a fresh run from RTL through native Classic post-GRT timing repair, using the stock image and stock stage ordering. It adds the manual-placement dictionary to the trusted native AREA1/clock8/20ns/56%-density recipe and enforces congestion disallowed. Original signoff files, macro configuration and100psrepair/50psacceptance targets remain fixed. Audits pre-placement topology, actual manual coordinates and post-DPL coordinates, zero global overflow, fresh antennas and all-corner timing. It deliberately refuses qualification if antennas or50pshold/setup gates fail; always-upload workflow retains failure evidence. No archived physical state is passed as the new flow's initial state.

Separate `gds-sram-bank-clean-screen.yaml` uses frozen full2/4 candidate3393eea, event-late variant and retained artifact only as trusted/reference data. Upload includes the new clean run and reference recipe/post-GPL views, not every inherited physical tree.97focusedtests pass, plus actual source generation on routed and clean stage layouts. Physical experiment not executed. This screen tests SRAM placement policy alone; it does not automatically reproduce every earlier electrical/strength ECO, nor claim to supersede the selected lineage.

## Remaining official adoption work

1. Inspect running residual data extraction38179535945; preserve its evidence and avoid blindly stacking physical candidates.
2. Publish and run reviewed clean-bank screen; measure final buffer positions, timing, electrical, overflow, added repair cells and antenna burden. Unfixed placements can change during later resizer steps.
3. If beneficial, evaluate full clean flow through DRT/extraction and exact-netlist GL, with resource/area/routing checks. Demonstrate stable instance mapping or replace brittle names with a general reproducible identification policy where supported.
4. Main adoption needs a reviewed exception to AGENTS/physical-design config whitelist: at least MANUAL_GLOBAL_PLACEMENTS and the chosen native recipe keys beyond clock/density/SRAM. D-080 explicitly reserves a separate reviewed exception for native mapping adoption. Do not silently edit src/config.json, generated user_config, template jobs or installed tool code.
5. Integrate approved hardware/config/constraints on one main commit; official GDS/precheck/gl_test/viewer plus independent all-corner zero-electrical audit must pass on that commit. A current-branch GDS run without integration would rebuild the existing main design instead.

This experiment does not change architecture, firmware/protocol support or50MHz. Legal geometry does not establish pin access, power integrity, routability, timing or electrical closure.

## Initial launch failure and correction

Clean bank38180541456 failed before synthesis because the launcher did not create the nested flow directory required by the pinned --force-run-dir CLI. BUG92 records the cause. Corrected helper creates a fresh empty directory before CLI invocation and refuses reuse; regression checks the actual directory at launch, stock-image selection and no checkpoint initial state.99focusedtests pass. This failure provides no physical evidence for or against SRAM locality; corrected rerun remains under the previously approved experiment scope.

## Physical clean placement reproduced; post-timing antenna failure

Corrected run38181853373 (artifact11718259505) reaches the final qualification gate, after reference-topology/manual/DPLplacement checks and cleanGRT. Saved setupWS0all/fast hold83.3254ps, electrical slew slow/typ/fast10/1/1,fanout8each,capmetrics0. Antenna15nets/17pins causes proper refusal. These are estimates before post-timing cleanup, not extractedclosure.

BUG93: clean screen omitted the conditional stock post-timing antenna cleanup already used in native_stock_route. Added disallowed-congestion stockRepairAntennas/CheckAntennas, unique physical views/log/metrics checks, antenna-only topology validation and fresh allcornerSTA on repaired state. No fullGRT or timing-limit relaxation.106focusedtests pass; rerun remains within approved cleanbank scope. Official adoption still requires reviewed config exception and final clean DRT/GL/GDS evidence.

## Successful clean screen audited; exact stock DRT continuation prepared

Run38184574265 succeeds on96b19be921b9cafc83b3e8b51cd5eb5f139cabba, artifact11720082047. Retrieved177selected netlists/DEF/state/config/historyfiles; canonicalclean16bufferproposal, unchangedfullrecipe exceptapprovedmanual/strictcongestion policy, pre-GPL topology reproduction, manual+DPLcoordinates, zerooverflow, congestion-disallowed antenna cleanup and finalantenna0/timinggate audited. EstimatedsetupWS0all, holdfast83.3254ps,typ189.382ps,slow380.307ps; electrical slow/typ/fastslew10/1/1,fanout8each,capmetrics0. Not extractedclosure.

Actual cleaned state points ODB/DEF at antenna cleanup but NL/PNL at pre-cleanupflow43. BUG94 documents inherited-netlist audit limitation. Prepared sram_bank_clean_route.py and gds-sram-bank-clean-route: exactsuccessfulsource/gates, trustedfullhardware/constraints/native baseline, pinnedLEFs/canonicalproposal/manual+DPL/history check, freshantenna/STA50psgate, stockDRT and newextraction. FreshDRT-exported NL must preserve all original functional cells/pins and prior diodes with only antenna additions beforeextraction; this catches hidden changes absent from inheritedNL. No repeated placement/CTS/GRT or customimage.140focusedtests pass. Publication/launch pending scopedapproval; no mainconfig/templatejob edit orphasebox tick.

## Clean extracted regression and stock timing-reserve trial

Cleanroute38188484920 succeeds (artifact11721449509) but fails timing acceptance: slow setup-737.237847ps, fast hold40.558669ps; typicalsetupWS0,typicalhold131.974435ps,slowhold285.339538ps. Electrical slow/typ/fastslew134/19/2,fanout17each,cap1each(place8636). All SRAM output capfailures are gone. Preserve earlier timing-qualified checkpoints; this clean policy is not adopted.

Actualslow worstpath starts U0configword0bit4 latch_48179_ and ends dropped[67] flop_47345_. Weak NAND2_1 _37732_ onpath drives0.111237pF with0.962903ns delay. CleanNL retains weak versions of the six earlier strength targets, and place7307/7308 remainBUF1; prior ECOchain strength changes are absent. Thus this comparison does not isolate SRAM locality as thecause ofregression. Worstfast hold ends U3RXrt[6] flop_46988_ via_42267_ NOR2B, not the previously plannedholdleaf46597. Do not transplant that oldholdproposal blindly.

Prepared --reserve mode of clean screen and separate gds-sram-bank-reserve-screen. Samefrozen2/4RTL, same16bufferlocality policy, stockClassic/image, fullreference/topology/placement/antenna/zerooverflow guards. Only native timing optimization targets change: GRT setup reserve1.0ns and hold125ps, versus0/100ps baseline. Clock20ns, signoffSDC and50psholdacceptancegate unchanged; stockrepair may resize/rebuffer andincrease area. Targets exceed observed~0.737nssetup deficit and~43psestimated-to-extracted holdloss, but cannot guarantee finalreserve or convergence. Existingnativebuffer/utilizationlimits remain; no bufferquota or congestionrelaxation.

142focusedtests/compile/diffpass, includingunchangeddefaultmode, target-only configdifference, separateoutput/workflow sourceguards. Noreserve physicalrun yet. Nextpublish reviewedhelper/test/workflow/evidence andscreen under scopedapproval, thenstrictDRT/extraction ifqualified. This tries to reproduce timing improvement through native supported controls rather than archivedcell-specific sizing. Mainconfigadoptionstillrequires reviewedexception and officialflow/evidence.

## Reserve screen timeout

Run38206133048 failed after95minutes in physicalstep, confirmed by GitHubcheck-run114669919755 annotation. Uploadedartifact11730202099 containspartialflowlogs; finalstage43 nativeResizerTimingPostGRT continues setupoptimization beyond510iterations, WNS/TNS0 and2065endpoints belowrequestedmargin with no recordedclosure. No finalallcornerSTA/qualification/extracted result exists. The1nsreserve policy is unqualified; no positivefinalsetup orholdclaim. Next inspect whymarginoptimization doesnotconverge (including latch/borrowed-path behavior as a hypothesis) and boundrepair work/targets, instead of rerunning unbounded or simply increasing timeout. Alllatestfunctional/docs/lintchecks passed; selected timing-qualified ECOparents retained.


## Native electrical repair prepared after reserve timeout (2026-10-12)

Partial reserve logs repeatedly select `_47655_/D`, a U3 configuration latch (sg13cmos5l_dlhq_1), among 2065 zero-slack endpoints. Hundreds of attempted/undone resizes show no reported area increase. This supports a latch time-borrowing/margin nonconvergence diagnosis; it does not establish final timing closure. Another positive global setup-margin run is not justified by this evidence.

Prepared `--electrical` and separate `gds-sram-bank-electrical-screen`: same frozen RTL, 16-buffer bank placement, 20 ns constraints and 50 ps acceptance. Enable stock RepairDesignPostGRT with its native 10% slew/cap margins, automatic wire-length selection (0), and rerouting; setup margin explicitly 0, hold repair target 125 ps. The pinned Classic orders this repair before antenna insertion; existing conditional post-timing antenna cleanup still preserves its repaired guides. Require actual repair execution and zero routing overflow, then fresh antenna/all-corner timing checks. Native repair can add cells; the bank-placement policy itself adds none. No new SDC exemptions, clock changes, utilization relaxation or template edits.

This is a testable native repair policy, not a promise to recover the -737 ps extracted setup deficit. It may fail timing, electrical, congestion or area checks. Only qualified screen results justify a separately matched DRT/extraction, and all final signoff/GL/official gates remain outstanding. Publication/dispatch pending; 69 focused placement/screen/route tests passed.


## Electrical screen is not routing-ready (2026-10-12)

User-directed process correction: fix known screen violations before detailed routing. Screen38272508875 passes timing/antenna qualification but is not electrically qualified. Its shared gate omitted electrical counts (BUG95). Local correction requires explicit zero slew/fanout/cap counts at all three corners for electrical mode; 75 focused tests pass. No new routing launched.

Actual post-cleanup reports: A_REN slew slow0.962052ns versus0.595200ns limit, typical0.616676/0.476000, fast0.396926/0.380000. Pre-cleanup native repair netlist identifies SRAM REN net_00076_ driven by NOR2B_1 _29426_. Confirm final ODB connectivity before choosing its physical repair. Four clk_regs branches clkbuf_2_[0-3]_0_clk_regs/X have fanout16 versus8. Twelve data drivers violate fanout: _29457_, _28807_, _29451_, place7614, place8354, _29529_, place8636, _44389_, place8554, _26701_, _29453_, place9267; worst is20. Native post-GRT repair log reports zero inserted buffers and zero resized cells, so enabling this step alone did not repair these loads. Later timing/antenna processing can also change loads; final-checkpoint repair must include those sinks.

Next prepare SRAM REN slew repair and bounded data/clock fanout repair with preserved functional connectivity and clock intent. Re-screen after antenna cleanup; require zero electrical violations, timing/hold qualification and zero congestion before investing in detailed routing. Passing the screen still cannot guarantee extracted timing/DRC or official signoff.


## Final physical connectivity inventory (2026-10-12)

Retrieved nine matched final-cleanup DEF/state and pre-cleanup timing netlist views. New read-only electrical_load_inventory.py checks final DEF sink counts against the actual report, preserves all diode sinks and rejects clock/reset loads in data splits. All sixteen reported fanout counts match final physical connectivity exactly. Four clock branches need two BUF8 branches each (eight total). A bounded data split with load budget6 reserves two of the limit8 loads for later antenna changes and proposes18 buffers over12 drivers. Total proposed fanout buffers26; no placements verified or physical changes applied.

Worst _29457_ has20loads, including12 antenna diodes. _28807_, _29451_ and place7614 each have15loads including7diodes. This establishes why pre-antenna fanout repair alone cannot certify final zero violations. Final DEF independently confirms REN net_00076_ driver_29426_/Y NOR2B_1 at438.720,226.800um, while SRAM is fixed12,40FS. A_REN pin origin is about128.260,231.210um: driver origin is approximately315um away. Moving/isolating its output near the macro is a concrete locality opportunity; driver input timing, placement, power and routing must also be qualified.

80focused tests pass, including missing REN, mismatched report/DEF counts and incorrect clock sink refusal. Next implement and qualify legal sites plus exact identity-buffer conservation for fanout branches, and evaluate REN buffer/locality repair. This proposal has not been physically applied, published or launched.


## Reviewed final electrical repair screen prepared (2026-10-12)

Prepared electrical_repair_plan.py, electrical_repair.tcl and electrical_repair_screen.py with separate gds-electrical-repair-screen workflow. Source38272508875/head9a65064a2cf51d10577e416acabd74d1fad46758 and final DEF SHAe8512f53f6f4d4c16bab1724b48f91ed9fad34ee105a11d0579ac3a8bef0e11b are fixed. All16 fanout sink counts match final DEF. Canonical27buffer plan uses8BUF8clock branches,18BUF4data branches and1BUF4REN isolation. Total footprint464.4864um2. Full-footprint legal-row allocation reserves every proposed site sequentially; combined overlap count0. Sites are proposals, with detailed legalization/pin access/power/timing still to verify.

REN isolation moves only SRAM A_REN to the new identity-buffer output; preserves existing driver and other source sinks. Proposed BUF4 location132.960,245.700N is19.190um Manhattan origin distance from pin center128.260,231.210, versus original driver~315um. Fanout repair retains all diode and functional sinks; data branches budget6 loads, clock branches8. Clock rewires are exclusively BUF8 input pins, preserving leaf clock/reset connections.

Runner checks source provenance, frozen hardware/native recipe, canonical bank policy/history and exact cleaned DEF. Pinned-image wrapper freshly exports baseline NL directly from actual ODB, audits inherited functional cells with antenna-only additions, applies bounded buffers and legalizes, reruns GRT with congestion disallowed, exports actual repaired NL/PNL, checks exact identity-buffer conservation, then checks/conditionally repairs antennas with refreshed netlists. No full GRT after that new antenna cleanup. Final screen requires setup>=0 and fast hold>=50ps, zero electrical counts allcorners and zero antennas; failure writes separate qualification fields and fails workflow. No DRT step.

95focused tests pass, Python compile/bash syntax/diff checks pass, and actual-source Tcl plan round-trip validates17source preflight calls/27groups. Physical mutation has not run; Tcl syntax/topology tests cannot certify OpenDB behavior or timing. New experiment uses an explicitly disclosed wrapper on LibreLane3.1.0.dev3 (custom_image=true); official clean-flow reproduction of any adopted repair remains mandatory and unresolved. Publishing/launch pending scopedapproval.
