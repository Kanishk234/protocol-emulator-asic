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


## First electrical repair fails strict electrical gate; follow-up prepared

Run38281277834 fails at final acceptance after actual27buffer insertion, GRT, antenna cleanup and allcorner STA. Artifact11761891578 (334164753bytes). Timing/antenna-qualified=true, electrical-qualified=false. SetupWS0all; fast hold53.5457ps, typical140.675ps, slow291.915ps. Final antennas0. Electrical slew slow/typical/fast1/0/0, fanout3each, cap0all. REN slew and allfour clock fanout failures resolved. Remaining slow slew SRAM A_ADDR[2]614.024ps versus595.200ps limit. Fanout _28813_/X12, _26701_/Y9, place8642/X9, versuslimit8. This is a real acceptance failure, not a tool crash or waived requirement. Fast hold reserve is only3.5457ps.

Final cleaned DEF SHA1f037dcdee9826d876c82ecd7ce71c699e342df4fea4bb83c373ed5cc13d38a9 independently maps all remaining failures. _28813_ has7functional+5newdiode loads; _26701_ retained branch gained3diodes and exceeded its2loadreserve; place8642 gained1diode above8loads. Address2 net7515 exclusively connects BUF1place7515/X to SRAM A_ADDR[2]; driver origin486.240,230.580um about356um from pin134.380,231.210.

Prepared residual mode and separate gds-electrical-residual-screen from exact failed source/headf85c6c674e34b183f0af92b61d75a9e607f738f5. Source failure allowed only with exact receipt proving timing/antenna pass and electrical fail; full frozen hardware/recipe and canonical original27buffer topology must reproduce. Follow-up adds7BUF4fanout branches with4loadbudget/headroom plus1BUF4near address2, retaining every earlier cell and diode. Addedfootprint116.1216um2; sequential full-footprint allocation0combinedoverlap. Addressbuffer136.800,245.700N,16.910um from pin. No DRT. Same strict electrical/timing/hold/antenna gates; reduced hold reserve remains a risk.

101focused checks pass; actual parent freshly exported NL passes exact27buffer conservation. Canonical parent plan audit encountered last-bit floating area representation464.4864 versus464.4863999999999; only summed area gets1e-9um2roundoff tolerance, all sites/cells/partitions remain exact and regression rejects actual area or wiring differences. Physical8buffer follow-up not run; publication/launch pending approval.


## Residual audit bug fixed before rerun

Run38282937757 reached eight-buffer insertion and zero-overflow GRT, then failed validate_change before antenna/timing qualification. Artifact11762706145 (351496425bytes). No final electrical or timing result exists. Reproduced exact failing sink: DEF A_ADDR[2] is represented inside nine-bit Verilog A_ADDR concatenation. BUG97 fixes explicit9bit mapping in validator, preserving exact comparison of every unplanned bit. Actual baseline/repaired netlists now pass exact eight-buffer conservation. 106focused tests pass including wrong-bit, wrong-width and unsupported representation refusal. Repair policy, sites, source and signoff constraints unchanged; rerun under existing approved residual experiment scope.


## Corrected residual run reaches physical acceptance and fails

Run38283838612 on64023d720a832189323a275d3fbdc1abcff4b1b9 fails final strict gate; bus validator now passes. Artifact11762243560,436539755bytes. SetupWS0all, holdfast49.6594ps (0.3406ps below50psgate), typical137.200ps, slow291.978ps. Electrical slew slow/typical/fast9/0/0, fanout2all, cap0all. The eight-buffer follow-up is not qualified and must not advance to DRT.

Final physical connectivity independently traces nine slow slew rows to one NOR4_1_25245_/Y net_19647_: driver plus eight receivingpins, output slew2.619903ns versus2.5074limit. Thus these are one electrical root cause, not nine independent repairs. Fanout_47490_/Q drives host_wdata[8] with7functional+7diode loads (14total); place8808/X has8functional+1diode load(9total). SRAM address2 and earlier REN/clock failures are fixed. Worst fast hold path49331latch→45710flop ends33530A21OI/Y net_00296_, exclusively connected to45710/D in finalDEF.

Next evaluate targeted isolation/strength on NOR4 load, partition two remaining data fanouts with diode reserve, and an identity delay buffer on the single hold leaf. Preserve actual repaired source; do not waive50pshold or electrical counts. Repeated full GRT/antenna cleanup shifts failures to other long nets, so further repair must also assess route stability rather than merely add loads and reroute blindly. No new physical proposal has been qualified or launched.


## Targeted slew/fanout/hold follow-up prepared

Prepared --finish mode and separate gds-electrical-finish-screen from exact run38283838612/head64023d720a832189323a275d3fbdc1abcff4b1b9, finalDEF SHA5a436a81e547204e1ffbb73830664a8245b2844a5e3dad76ae85a2adf2188cfd. Incoming failed source is accepted only for repair with its exact unqualified receipt and measured0setup/49.6594psfast hold/9slow slew/2fanout/cap0/finalantenna0. Both preceding27buffer and8buffer canonical plans/netlist histories are audited before using this source. Output50pshold and zeroelectrical acceptance gates remain unchanged.

Proposed6BUF4fanout branches for host_wdata[8] and place8808, with4loadbudget/headroom;1BUF1identity delay only on33530/Y→45710/D net00296; and NOR4_1_25245_→NOR4_2 strength change with identical A/B/C/D/Y and supply connectivity. No other masters/clock/reset pins change. BUF1site672.480,37.800FS is1.920um from endpoint. NOR4 replacement legal footprint allocated444.960,366.660N,4.800um displacement. Newbufferfootprint94.3488um2 plus resize10.8864um2, total105.2352um2. Allplanned footprints reserved together, zerooverlap; physical legalization/power/pinaccess/timing still required.

Previous allocator excluded every row below SRAM top, even far-right rows; new mode admits lower-row segments only to right ofx260um while preserving lower-left macro exclusion. This avoids forcing lower-right repair buffers far above the SRAM and unnecessarily stretching their nets. Same strict zerooverflow/antenna/allcorner/electrical checks; no DRT. Bracket-escaped DEF source net normalization now aligns literal OpenDB/Verilog identities (BUG98).

116focused tests, compile/bash syntax/diff checks pass. Actual final netlist accepts a synthetic exact seven-buffer/one-resize conservation replay, including allold cells/diodes; actualsource Tcl parses7buffer/1resize operations. These checks verify proposal/audit representation, not physical behavior. Publishedpinnedimagewrapper adds existing master/pin/supply guarded sizing helper and placement binding. Custom-image diagnostic/officialportability limits remain. Physicalrun and publication pending approval.


## Targeted repair preflight naming failure fixed

Run38286752555 fails before physical mutations: NOR4 sizing expected port_state[45], but pinned OpenDB reports closing-bracket escape port_state[45\]. Artifact11764465151,437124753bytes. No new timing/electrical result. BUG99 replaces reused raw-name sizing check with dedicated electrical net resolver: normalize bracket escape spellings, require exactly one matching physical net, compare actual connected net objects, preserve those same objects after replacement. Missing nets and canonical-name alias collisions fail. Buffer source expectations use the same unique resolver. Existing native_hold100_size.tcl remains unchanged.

117focused checks pass, including Tcl runtime tests for actual escape representation, missing nets and ambiguous aliases; bash syntax/diff pass. Seven buffers, NOR4 master/site, sources and constraints unchanged. Publish/rerun covered by user's ongoing Phase2 authorization.


## Targeted repair executes; timing passes but electrical closure moves again

Run38287515824 fails final electrical gate, not preflight. Artifact11763968351,539241591bytes. Sevenbuffers/oneNOR4resize applied and allconnectivityguards passed. SetupWS0all; holdfast56.771ps, typical140.816ps, slow291.986ps. Timing/antenna-qualifiedtrue, electricalfalse. Cap0all, slewslow/typical/fast7/0/0, fanout3all. NOR4_25245_slew and priorfanout/holdleaf repairs worked. Newviolators fanout_28820_/Y14,_26845_/X9,place8806/X9. Seven slowslew rows belong to_28807_/Y and its attached sinks/diodes, maximum2.514342ns versus2.5074ns limit. Do not advance to DRT.

Repeated fullreroute/antenna cleanup changes other near-limit nets, reducing confidence in isolated reroute candidates. Inspected exact pinned common/grt.tcl: always invokes full global_route, not incremental mode. [Primary OpenROAD routing documentation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/master/src/grt/README.md) documents start/end_incremental and route-segment restoration in current upstream; availability and restoration semantics in our pinned image are not yet established. Next verify pinned capabilities and unchanged-net route preservation before adopting incremental repair. No routing exception or unsupported API assumed; no new run dispatched.


## Pinned routing capability probe

Prepared lightweight gds-routing-capability-probe on LibreLane3.1.0.dev3 image, without PDK or loaded design. Captures image digest, OpenROAD version and command/help availability for global_route incremental flags, read_guides and route-segment read/write. Local cached OpenROAD lacks Qt shared-library dependency; do not treat its execution as pinned CI verification. Parser rejects incomplete/duplicate evidence and explicitly does not claim checkpoint restoration or unchanged-route preservation. 122focused checks pass. Next inspect actual pinned capabilities and test saved-state restoration before changing repair routing.


## Pinned incremental capability confirmed; exact state export diagnostic

Probe38292662761 succeeds, artifact11766453346(1298bytes). Image reports OpenROADdcf36133a369abc8f3c5e5738cd4d82e4903c0e0; incremental start/end flags plus read_guides/read/write_global_route_segments available. Exact commit GlobalRouter.cpp confirms readGuides warns it cannot supply guide-based parasitics estimation; readSegments loads raw routes and verifies connectivity and pin coverage. Do not infer matched incremental state from guide rectangles.

Prepared gds-route-segment-export repeating the same reviewed finish baseline, with no new physical repair. Wrapper exports live full segment data after GRT and antenna cleanup. Dedicated --capture-segments requires finish mode and nonempty final ODB-matched segment file. Receipt retains actual qualified/timing/electrical fields and adds route_segment_capture_only=true, checkpoint_restoration_tested=false. Export diagnostic can succeed while qualified=false; this is not electrical/signoff acceptance and cannot advance to DRT. Regular screen gates unchanged. 127focused tests pass, including export-after-physical-step ordering, ambiguous input-read refusal and explicit diagnostic workflow/mode checks.

Next inspect live segments, test exact fresh-process roundtrip/STA and zero-edit incremental behavior, then apply remaining eight-buffer/NAND3 repair with measured unchanged-route preservation if supported. No false/multicycle paths, relaxed electrical/hold gates or official completion claims.


## No-edit saved-route restoration diagnostic prepared

Prepared route_restore_screen.py, exact geometry/timing auditors, pinned-image wrapper and separate gds-route-restore-screen. Bound to segment capture38293466146/head241f7dd11e4198b5be3a9a7a34f3c910baf3d414; do not dispatch before export completes and actual receipt/segments are inspected. Source may remain electrically unqualified; diagnostic cannot convert that into signoff. Full frozen hardware/native recipe, canonical7buffer/1resize policy and fresh source netlist/antenna-only history checked; segment path must belong to final ODB.

Wrapper replaces only pinned grt.tcl's unique full-routing source statement with routing-layer/capacity configuration, exact segment import/export and start/end_incremental with no design edits. No DPL, sizing, buffers, source-wire resets or detailed routing. Reject changed pinned script structure. Audit every imported/no-op segment exactly (direction/order immaterial; duplicate multiplicity retained), preserve allnetlist cells/connections and compare fresh allcorner source/restored setup/hold slack to1e-6ns and electricalcounts exactly. Current electrically failing source remains explicitly identified; output signifies only restoration behavior.

27focused preservation/runner/wrapper tests pass, compile/bashsyntax/diff checks pass. Missing/ambiguoussource, geometry/netlist/timing/electrical changes fail. Physical restoration has not executed. Export38293466146 has finished physical step and is uploading evidence; actual result pending finalstatus/artifact inspection.


## Segment export inspected and restoration source fixed

Export38293466146 succeeds, artifact11767790828(541577365bytes). Read final cleaned segment file and capture/timing receipts. FileSHA860b8c777de3b4d555ad9967ec4a1487dd540b71cb89e3401b8b36b73a794588,33909routednets/268616segments, grammar/orthogonalgeometry audit passes. It belongs to final antenna-cleanup ODB, not pre-cleanup routing. All measured setup/hold/electrical values exactly reproduce38287515824: setup0all, fast hold56.771ps, typical140.816ps, slow291.986ps; electricalslew7/0/0slow/typical/fast, fanout3all, cap0. qualified=false preserved. Restoration runner now pins exact segmentSHA/counts in addition to run/head/receipt/state/recipe. Next launch no-edit restoration; electrical/signoff gates remain outstanding.


## Restoration evidence inspected; cold capacity limitation found

Run38294805019 succeeds at ef6259831d3a5531931ff82ae65bda16698d54ae; artifact11768991337(621985214bytes). Independently re-parsed geometry/NL and timing: exact33909net/268616segment roundtrip/no-edit geometry, unchangedfunctional NL, allsetup/hold/electrical values match. This confirms geometry/STA behavior only. Actualno-op congestion table haszeroMetal2/3/4demand despiteexistingroutes. Exactpinned readSegments doesnotupdateedgeusage; startIncremental resetsFastRoute capacities. readGuides updates3Dusage only, leaving2Daccounting unresolved. BUG100 documents why no cold-restored physicalrepair is launched.

## Single-process electrical repair prepared

Prepared gds-electrical-incremental-screen from verified diagnostic38294805019, restoredDEF SHA7626616e05699cffde246ab26e501d212a2d889d6671ed7a8186796fb49137a1. Libraryoffers NAND3_1only, so replace speculative NAND3strength2 with two localBUF4s isolating its six existing loads into3/3groups. Combinedplan:8fanoutBUF4 +2slewisolationBUF4,145.152um2, combinedproposedfootprintoverlap0. Slewbuffers2.400/3.780um fromNAND3origin. Everyoriginalcell/diode retained, noclock/reset rewiring ormaster changes.

Correctcapacitystrategy: one explicitstockfullGRT initializes live2D/3Dusage, records rebasedODB/DEF/NL/fullsegments; then bufferedits+legalization, incrementalrouting, stockantenna repair and finalno-editincrementalreport occur in the sameprocess. Existingplacedcells frozen forlegalization and statusesrestored beforefinalsave. This initialfullroute maychange oldroutes andis separatelyreported; do not claim preservation acrossit. Exactafter-buffer routeaudit permitsonly plannedsource/newnets. Finalantennaroute allowance derivedonly fromactualnewdiodeNL additions after strictantenna-only topology check. Everypriorcellplacement mustremain unchanged. Positiveinitial/finaldemand andzerooverflow required. No separatecoldantenna process orDRT.

FreshallcornerSTA compares explicitrebasedbaseline tofinalphysicalcheckpoint; outgoing setup>=0, fasthold>=50ps, zeroelectrical/antenna gates unchanged. Source remainsunqualified; one-processwrapper isdiagnostic and officialcleanreproduction outstanding. 134focusedtests pass, actualrestoredsource synthetic10buffer conservation/Tclroundtrip pass, compile/bashsyntax/diffpass. Actualphysical outcomeunknown; publication/launch underongoingauthorization.

### Incremental screen startup failure — 38301813030

The live-process experiment failed before its first global route, because the placement-freeze helper passed DEF-style `FIXED` to OpenDB. The exact pinned OpenROAD `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0` [dbTypes.h](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/odb/include/odb/dbTypes.h) defines `LOCKED` as immovable and does not accept `FIXED`. The helper now uses `LOCKED` for existing PLACED/FIRM instances, restores their original statuses, and leaves existing LOCKED/COVER instances untouched. BUG101 records the failure. The strengthened Tcl regression rejects invalid enums; 31 focused helper/plan/audit tests pass locally. A physical rerun is still required; this startup failure provides no new timing or electrical result.

### Live repair route audit — 38302884774

The LOCKED correction worked. The actual routing process retained initialized capacity (final demand241307), zero overflow, all original placements and exact intended ten-buffer connectivity. The buffer phase changed only its14planned nets. Native antenna repair then inserted6jumpers and3diodes on9nets; the final audit stopped before STA because it allowed only new-diode nets. BUG102 records this incomplete evidence rule. The revised wrapper captures the pinned nonverbose checker report before antenna repair, and the audit allows only reported violating nets plus strictly verified added-diode nets. Unrelated routes remain rejected. Local32focused tests pass; a physical rerun and final strict timing/electrical checks remain required.
