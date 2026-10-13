# Combined physical repair screen

Source: completed zero-DRC route38305592967, head2d73b6fe4b3ee22337fe7db2240cda7761dcda5e. Its extraction fails setup/hold/electrical limits. The successful fixed-SPEF study38321212600 identifies an eight-change AND4 setup candidate with all-corner setupWS0, but it is not physically qualified.

The proposal combines that candidate with19endpoint-local DLY4SD1 hold cells and57BUF4 electrical buffers, covering all29violating nets from the actual three-corner reports. Net footprint growth:1103.1552um2for76new cells plus23.5872um2for resizing; offline joint allocation has zero overlaps. Actual-source synthetic conservation covers all original functional cells, clocks/resets, diode protection and known SRAM address bus. No physical improvement is claimed until CI executes.

## Audits and execution

- Exact routed NL/DEF, fast min report and every electrical report are SHA256-bound. Frozen full2/4event-late hardware,20ns signoff constraints, native AREA1/clock8/SRAM placement recipe and pinned standard/macroLEFs are checked independently.
- Resize only the eight reviewed cells, preserve all pin/net objects, place complete footprints, lock original placements (including relocated resized cells), then add source-preflighted identity/delay cells. Never rewire clock/reset sinks. Each electrical branch receives at most4original loads, including diodes. Macro buffer coordinates use actual FS-transformed LEF pins.
- Buffer power anchors are standard cells only: macro VDD!/VSS! cannot supply the helper's VDD/VSS terminal lookup (BUG105 caught before launch).
- Legalize new cells, clear old ordinary detailed signal/clock wires while preserving POWER/GROUND and special geometry, perform one native full global route, and keep native antenna repair in that initialized process. Restore original placement statuses before saving fresh NL/PNL. This is a disclosed full reroute, not a promise to preserve old signal routes.
- Validate exact eight-resize/76-buffer conservation plus antenna-only additions, all original placements except reviewed resize coordinates, positive initial/final routing demand, zero overflow and a positive detailed-wire reset receipt. Then check antennas and fresh all-corner estimated timing/electrical counts.
- Require setup>=0allcorners, fast hold>=50ps, zero slew/fanout/cap allcorners and zero antenna violations. Failure writes gate evidence and fails the workflow. No detailed-route step or automated continuation exists.

53focused tests pass; actual-source joint allocation and eight-resize/76-buffer synthetic conservation pass; actual generated Tcl argument round-trip passes. Tcl/OpenDB behavior, new routing, power connectivity and timing still require the physical run. This uses a custom wrapper on pinned LibreLane3.1.0.dev3, not the official final GDS flow. Estimated-screen/extracted correlation remains a required follow-up before trusting a green screen as sufficient margin. Official clean-flow reproduction, GL and GDS/LVS/precheck remain outstanding.

## Screen outcome — 38334245126

Actualartifact11784965210 confirms strictqualification:allcorner setupWS0;fast/typ/slowhold54.2228/142.567/297.464ps;allcorner slew/fanout/cap0;antenna0;overflow0. Exact8resize/76buffer conservation, originalplacements except reviewedresizes, positiveinitial/finaldemand andsource detailed-wirecleanup allpassed. This is estimated globalrouting, not extracted closure. Fastholdheadroom is4.2228ps aboveacceptance, soextraction remains decisive.

Prepared exact-source continuation validates run/head/completegates andcanonicalproposal/actualfreshviews/history, uses stockimage, rechecks strictallcorner timing/electrical/antenna beforeDRT, and doesnotrepeatphysicalrepair/fullGRT. Detailedrouting mustfinish with0DRC andfreshnetlistconservation; extraction retains unchangedsignoffconstraints andmustpass allcorner setup/hold plus50psfasthold andzeroelectrical/antenna. Originalfailedextracted evidence ispreserved separately beforefreshoutput.45focusedtests pass. No officialsignoff/Phase2tick.

## Extracted outcome — 38336141213

Actualartifact11785924491 andfreshreports confirm completed0DRC/0antenna route withconservedNL, butstrict extractedgatefails legitimately. Slowsetup-0.399145617ns;fast/typ/slowhold38.505367/106.464285/235.561355ps. Slewslow/typ/fast13/0/0,fanout6each,cap0everycorner. Previousphysicalresult was-1.008813ns/0.0215psfasthold,93slowslew,9fanout,cap1fast/typ. Thecombinedrepair substantiallyimprovesactualresults butdoesnotclosePhase2. Nohelperexception/gatewaiverorblindrerun isappropriate.

Saved1000pathreportscontain10negativesetuppathsand4sub50psholdpaths. Worstsetup48179→47272hasNOR243582(1.713399ns,0.159253pF),NAND343583(1.493117ns),BUF1place7208(1.211073ns,0.255543pF),NOR425727(0.682320ns). Othernegativepaths include48112→47345/47343. Remainingholdepts46372/46325/46033/45735have38.505/42.679/43.538/44.180ps. Recomputeexactsource-boundlocaldelays ratherthanrepeatall19oldfixes.

The13slowslewrowsmaptoonlytwodrivers:NAND444589/net17361andNOR443311/net16410. TheNAND4hasnostrongervariant;boundedlocaloutputloadisolationisacandidate. NOR4_2isavailable. Fanoutdriversplace8647/place9151have10loads(2/4diodes);24514/28879/45622/place7856have9loads(1diodeeach). Theold76newcellsand8resizesmustberetained;onlyresidualsource-boundcorrectionsareproposed.

NewroutedNL SHA:c98fb068c21b40c07263a67f63e446e1099f8116b5a9fb0806841ea612e7d386;DEF:c28307f932c670729b1abb6fe5f987c49f659adb1897fc57dbf73b504b2524f7;extractedfillNL:08f99cf0d24fc7cc238ca80252d388500a0e845f4c6888dcbc71d4e7f5e00e1a. Nextpreparematchedresidualsetup/load/holdscreen;calibrateagainstnowmeasured16psfastholdscreen-to-extractedlossand0.399nssetupdeficitwithoutchangingofficialconstraints. NoDRTuntilcorrectedscreenpasses;officialGL/GDSremainopen.

## Residual diagnostic and next preparation

Completed fixed-SPEF study38342469816 improves slow setup from -0.399145617ns to -0.199742450ns with NOR2_2 at43582. BUF4/BUF8 and NOR4 alternatives tested in that study do not reduce the resulting global worst slack further. Fast hold stays38.505ps. This does not qualify physical timing.

The next six-case diagnostic compares the NOR2 change with individual and joint DLY4SD3-to-DLY4SD2 changes at hold12766 and hold12715. It keeps the measured source SPEF and checks all corners; shorter delays may expose hold paths, so inspect their results before choosing physical changes.

A source-bound residual physical screen is prepared but must remain undispatched until setup selection is resolved. Its provisional proposal retains previous repairs and adds32 endpoint-local DLY4SD1 cells for endpoints below75ps plus21 electrical BUF4 cells, with4 provisional resizes. Joint footprint growth is801.9648um2 with zero offline overlaps. The75ps repair selection does not change the50ps fast-hold acceptance gate. Recompute affected hold targets if the shared-delay study changes the selected source timing. All physical gates still require fresh evidence; detailed routing and official integration remain pending.

## Shared-delay result and selected residual physical screen

Successful diagnostic38345601171 (artifact11789351739, head72b7bfc7968a386f9c295d2e048c3f61adaa79f1) reproduces the baseline and reports all-corner setupWS0 for the NOR2_2 upgrade at43582 plus DLY4SD3-to-DLY4SD2 at hold12766. Changing hold12715 alone does not improve the remaining -0.199742450ns worst slack; adding that change or the previous BUF4/NOR4 setup changes provides no further reported setup benefit. Select the two-change medium12766 case. Reported setup0 means no reported negative slack, not proven positive margin. Fixed-SPEF results remain diagnostic only.

Fast hold stays38.505ps; slow slew13, fanout6 per corner and cap0 remain. The selected candidate's actual fast min report has exactly the same32 sub75ps endpoints and identical slacks as the original extracted baseline, so the source-bound local hold targets remain applicable.

The revised physical proposal combines those two setup changes with the electrical NOR4_2 upgrade at43311,32 local DLY4SD1 hold cells and21 BUF4 electrical cells. It retains all previous repairs, removes the unhelpful provisional BUF4/NOR4 setup upgrades, and leaves hold12715 unchanged. Joint allocation has zero offline overlaps; added cells769.3056um2 plus resizing12.7008um2 totals782.0064um2. Actual-source three-resize/53-buffer synthetic conservation and generated Tcl argument round-trip pass. Fresh physical routing, power connectivity and timing are still required.

Next launch only the residual combined physical screen: fresh all-corner setup/50ps fast hold/electrical/antenna/overflow gates. No detailed routing is authorized by diagnostic success; it remains conditional on every physical screen gate passing. Official GDS/GL and Phase2 remain outstanding.

## Residual physical outcome and fresh-screen correction

Run38347662810 (artifact11788839389, headcb16ebda06c8b915e2059a10ce606ea1a73c46ae) completes physical repairs and fresh timing, but fails the strict screen gate. SetupWS0 all corners; fast/typ/slow hold33.3996/138.314/325.319ps; slew and capacitance0 all corners, fanout2 each corner. Antenna check reports0 violating nets/pins; routing overflow and live-demand guards passed. No detailed routing started.

New sub50ps endpoints are45749,45784,46935 and45781; the full reroute changes the short-path set. Fresh min reports contain47 endpoints below75ps. Remaining fanout28764/Y has13 loads including6 antenna diodes; tripwire_combined_42/X has12 including8 antenna diodes. Preserve all diodes and split the loads into at-most4-load branches.

The next proposal uses the actual fresh global-screen NL/DEF and three-corner reports, not the older extracted source. SHA256 binds every view/report and exact GitHub run/head/workflow, retains all existing repairs, and adds47 DLY4SD1 local endpoint delays plus7 BUF4 fanout cells. Added footprint783.8208um2; no resizing; zero offline overlaps. Actual-source54-buffer synthetic conservation and generated Tcl round-trip pass.79 focused tests cover source selection, strict provenance, old DRT checks, fresh-screen wire checks, placement/conservation, timing helper and hold selection.

The global-screen source has no ordinary detailed wires: a dedicated Tcl check requires every signal/clock net to have no dbWire, preserves power/special geometry, and refuses an empty design. Existing detailed-route cleanup remains unchanged and still requires actual wires to remove. The fresh-screen receipt explicitly records zero detailed wires, rather than claiming a cleanup occurred. Rebuild routing with native inline antenna repair; recheck all original placements, connectivity, fresh timing/electrical/antenna/overflow. Acceptance remains setup>=0 all corners and fast hold>=50ps. No detailed routing unless every screen gate passes; no official-signoff or Phase2 completion claim.

## Follow-up timing clears; two new diode fanout violations remain

38349702735 (artifact11790677207, head2dcd16eb188774373a53400a0b1f892cc996e201) fails a genuine electrical gate after completed physical/timing checks. SetupWS0 all corners; fast/typ/slow hold75.1412/174.423/346.912ps. Slew/cap0 and antenna0; live routing/overflow/conservation checks pass. Fast hold now exceeds the50ps gate by25.1412ps at estimated routing. Extraction remains untested.

Both prior overloaded nets are repaired; the full reroute's antenna repair adds one diode each to two different eight-functional-load nets:29534/Y net04496 and place9211/X net9211. Each now has9 loads against8. Repair these actual fresh sources while retaining every diode and all previous timing repairs. A blanket reduction of every eight-load data net would affect1542 nets in this source, so it would carry substantial area/routing cost.

Prepared source-bound fanout-only screen38349702735:6 BUF4 partitions,87.0912um2 growth, zero offline overlap; no resizes or new hold delays. SHA-bound fresh fast min report has no endpoints below75ps; an empty repair set is allowed only after parsing a complete valid report and checking the expected count0. Default hold selection still rejects an empty set. Actual-source six-buffer synthetic conservation and generated Tcl round-trip pass;82 focused tests pass (61+21). Repeat strict screen gates before detailed routing. No official qualification or Phase2 tick.

## Fanout-only outcome — 38352108106

Artifact11791747745 on head3308827fa8cb9471cf7b04f9edb08cdf2fd8acf4 confirms another genuine gate failure:setupWS0 all corners;fast/typ/slow hold76.7236/174.305/345.928ps; slew/cap0,antenna0. Only one fanout net remains:place9271/X net9271 has14 loads, consisting of8 functional inputs and6 antenna diodes. The two previously targeted nets pass. No detailed routing started.

The repair cycle is sensitive to new diodes introduced by a full reroute. The revised source-bound fanout-only screen retains all existing cells/diodes and partitions this actual14-load net into4 BUF4 branches. Added footprint58.0608um2, zero offline overlaps, no timing resizes/delays. Exact newest NL/DEF/three-corner reports and complete fast min report bind the source; there are no sub75ps endpoints. Actual-source four-buffer conservation, Tcl round-trip and82 focused tests pass. Recheck every acceptance gate; a different net may need repair after rerouting. No timing-gate relaxation, extraction claim or Phase2 completion.

## Recurring antenna-induced fanout and bounded same-process correction

38353731199 (artifact11792092356, head1b58a13fd9bfa650dccbdea9b6b0add161b9ea29) again fails the electrical gate legitimately:setupWS0 all corners;fast/typ/slow hold74.5192/170.826/342.264ps; slew/cap0 and antenna0. Previous target passes, but new fanout place7616/X has14 loads (7 diodes) and place8061/X13 (5 diodes). No detailed routing.

The repeated source-net repairs have not converged reliably because each full reroute can create fresh antenna diode loads elsewhere. BUG106 records this sequence issue. Pinned OpenROAD GlobalRouter::repairAntennas first attempts jumpers, then may insert diodes and update dirty routes in the initialized process; making repairs in a later cold process would lose the relevant capacity state.

New experiment keeps the exact newest SHA-bound source and initial8BUF4/116.1216um2 residual partition, then performs bounded data-net fanout repair after native antenna cleanup in that same process. Partition only overloaded standard-cell data nets into at-most4-load BUF4 branches; retain all original cells and every diode. Skip exposed/clock/reset nets, reject ambiguous drivers, preflight identity/power/connectivity, freeze existing placements, begin incremental routing before edits, legalize new cells, end incremental routing, and run native antenna repair again. At most2 batches of32 buffers; fail if the final check still finds overloaded eligible nets. No unconstrained repair or gate relaxation.

Each batch exports before/after NL and a JSON branch receipt. Audit antenna-only intervals, exact BUF4 connectivity changes, complete load partitions, protected-pin refusal, original placements and live zero-overflow routing; record dynamic additions separately. Existing final all-corner setup/50ps fast hold/zero electrical/antenna gates remain mandatory before DRT.100 focused tests (39 Tcl/batch/source checks +61 existing regressions), actual-source8buffer synthetic conservation/bounded audit and generated Tcl round-trip pass. Dynamic placement/routing and convergence require pinned CI; no physical/official qualification claim.

## Strict post-antenna screen qualifies — 38356513586

Actualartifact11793266699 on5671a0d06461aad776cbdfd55c262644d3b26370 confirms strictqualification:setupWS0 all corners;fast/typ/slow hold73.4991/172.911/347.727ps; slew/fanout/cap0 in every corner;antenna0;zero overflow. Native post-antenna correction converges in1batch of3BUF4 cells, in addition to8 offline-planned BUF4 cells. Independent canonical proposal, original placements, initial8-buffer connectivity, every dynamic batch/antenna interval, positive route demand and strict gates pass on actual saved reports. BUG106 now has physical-screen evidence.

Prepared exact-successful-source continuation through stock DRT and extraction. Revalidate source run/head/workflow, entire strict gate receipt, canonical initial plan, actual bounded batch history, complete fresh NL/PNL/ODB/DEF/SDC linkage, old placements, native full recipe and frozen2/4 hardware. Recheck fresh stock all-corner timing/electrical/antenna before DRT; do not replay physical repair or full GRT. Require0DRC and conserved fresh route NL, then unchanged20ns/all-corner extracted setup/hold/50ps fast hold/zero electrical/antenna gates. Preserve prior failed extraction evidence separately.

Prelaunch replay caught summed-area float roundoff (BUG107):only totals tolerate<=1e-9um2, all physical fields exact. Extracted electrical gate now requires exactly all three measured corners and explicit clean receipts; missing/empty summaries fail closed (BUG108).97 focused tests pass (58 continuation/planning checks +39 Tcl/batch/source checks). Screen success permits detailed routing but does not qualify extraction, routed protocol behavior, clean official-flow reproduction or GDS/LVS/precheck. Phase2 remains open.

## Post-antenna detailed route/extraction — 38358706808

Actualartifact11795955910 on8e77722239af612fad2f590c322cab84600f76d0 confirms successful fresh stock screen recheck, completed0DRC route, conserved fresh NL and0antenna, but legitimate extracted gate failure. Slow setup-0.230240722ns; fast/typ/slow hold61.102791/166.093255/339.983051ps. Cap0 all corners; slow slew27 (typ/fast0); fanout5 each corner. No launcher exception or unchanged rerun is appropriate; Phase2 remains open.

Seven printed negative setup paths share latch48107 (pin configuration word15) through the decode/decision chain to47345/47343/47347/47344/47342. High-delay gates include30044/A21OI1 (0.904995ns),37714/NAND3_1 (0.923974ns; no stronger pinned variant),43884/O21AI1 (0.790600ns; no stronger variant),43915/AND3_1 and43917/NOR2_1. Prepare five fixed-SPEF cases: baseline, A21OI2 at30044, NOR2_2 at43917, both, plus AND3_2 at43915. Exact newest run/head/extracted-NL binds and baseline reproduction required.29 focused tests plus five actual-source conservation checks pass. Diagnostic only; no physical closure claim.

Detailed routing adds27 native antenna diodes despite a clean global screen. New fanout targets26667,place6434,place7566,place8659,place8876. The27 slow-slew rows collapse to7 data-driver nets, including SRAM address8 via hold11754. This shows post-GRT fanout convergence does not guarantee post-DRT electrical closure. The next physical repair must account for the detailed-route antenna stage and extracted loads. Four extracted hold endpoints below75ps are candidates for margin; fast hold already passes50ps. Resolve setup selection before the next combined physical screen, retain all strict gates and every diode, and require clean extracted evidence before official integration.

## Decode diagnostic result and combined physical proposal

38418432056 succeeds on9d91d414b2ab64f7e7d7e3f0647964793157b5e5; artifact11825992255 reproduces the actual extracted baseline. Slow setup:baseline-0.230240722ns; A21OI2 at30044 alone-0.113562496ns; NOR2_2 at43917 alone-0.009507062ns; both0; adding AND3_2 at43915 also0. Select the two-gate case; all-corner reported setupWS0, fast hold61.102791ps unchanged. This is fixed-SPEF diagnosis, not a physical pass or positive global margin claim.

The selected candidate's complete fast min report has exactly the same four sub75ps endpoints and slacks as the original extracted source:46740(61.103ps),46656(66.402ps),46801(68.094ps),45597(73.910ps). The new combined physical proposal retains all prior cells/diodes and adds4 local DLY4SD1 hold cells plus24 electrical BUF4 cells for12 measured source nets (7 slew-driver nets and5 fanout nets), together with the selected2resizes. Initial footprint growth406.4256um2 plus9.072um2 resizing=415.4976um2; zero offline overlaps. SRAM address8 receives local buffer isolation without altering the other address bits.

Controller binds newest run/head/fresh routed NL/DEF/hold/all3electrical reports and pinned geometry; sourceDRC0 is required. Clear actual old detailed signal/clock wires, preserve power/special routes, reroute once, and retain bounded same-process post-antenna fanout cleanup. Require all unchanged screen gates before any DRT.69 focused tests(30 planning/source/wrapper/hold/diagnostic +39 Tcl/bounded-history checks), actual two-resize/28-buffer synthetic conservation including SRAMADDR8, and generated Tcl round-trip pass. Native physical timing, legalization and post-DRT antenna/load behavior remain unproven. New detailed routing can still add diodes; final extracted gates remain mandatory before official integration.

## Combined decode screen qualifies; exact continuation prepared

38421594711 succeeds on0225eecc6798b1bea2e7ff37cc9e56eda89ebb23 (artifact11828740117). Saved strict results:setupWS0 all corners;fast/typ/slow hold77.8488/174.230/345.514ps;slew/fanout/cap0 all corners;antenna0;zero overflow/live-demand audit passes. Two resizes/28 cells match the canonical proposal; post-antenna cleanup needs0additional batches/buffers. Independently revalidated actual sourceNL/DEF, every initial rewire including SRAMADDR8, all original placements except reviewed resizes, antenna-only final interval and complete strict gates.

Prepared stock continuation bound to this successful exact run/head/workflow and complete gate receipt. Regenerate source-bound canonical plan and reaudit current fresh views/history/native full configuration/frozen2/4 hardware before fresh allgate recheck. No physical repair or full GRT replay; zeroDRC and fresh conserved NL required after DRT, followed by unchanged allcorner extracted setup/hold/fast50ps/zero electrical/antenna gates with allthree electrical corners required. Preserve prior failed extraction separately.58 focused continuation/provenance/stock-gate tests pass;diffcheck passes. This does not guarantee post-DRT timing or fanout, since native DRT antenna repair can introduce new diode loads; official GDS and Phase2 remain pending.

## Decode detailed route: extracted timing clears, fanout remains

38433037592 (artifact11833878873, head18dd627c8671e82d650b6978236857724cb258fa) completes0DRC route/extraction and passes every timing gate:setupWS0 all corners;fast/typ/slow hold68.172303/167.606822/347.524241ps. Antenna0;slew/cap0 everycorner. It fails solely on9fanout nets ineachcorner, so it is not qualified for official adoption.

Clock-buffer clkbuf_1_0__f_u_chip.g_unit[0].u_cfg.g_word[3].g_stored.gclk/X has12loads;place9170 has11,place8842 has10;29538,45886,47069,place7854,place8807,place8992 eachhave9. Next inspect exact native post-DRT diode/load changes and prepare controlled fanout closure. Preserve generic data-helper clock/reset exclusions; the clock branch needs its own reviewed physical timing/conservation checks. No threshold relaxation, falsepaths, official timing/Phase2 completion or new hardware adoption.

## Nine-net fanout and clock-diode isolation proposal

Exact38433037592 clock net contains6 DLHQ GATE loads and6antenna diodes; its reported12loads exceed8. Two BUF4 branches move only the6diode A terminals, leaving every latch GATE on its original clock net. Reviewed source/root/master/count checks refuse any other protected partition. Clock driver then sees6functional loads+2buffer inputs=8; branchloads4/2. Every diode remains in the chip. Buffer isolation changes which net a diode protects, so fresh antenna qualification and later DRT checks are required; no guaranteed closure claim.

Source-bound combined fanout screen retains passing gate strengths and every prior cell, adds24BUF4 for8data nets plus2clock-diodeBUF4 and2localDLY4SD1 for the new68.172/74.395ps sub75ps hold endpoints. Total28cells,406.4256um2, zero offline overlaps; no resizes. Exact newestNL/DEF/threecornerreports/holdreport and pinned LEFs bind the proposal. BUG109 fixes hierarchical instance spelling only in the reviewed mode; runtime instance resolution rejects ambiguous bracket aliases. Generic clock/reset sink-rewire exclusions remain intact.

94 focused tests (46 plan/continuation/partition +48 Tcl/identity/bounded-source checks), actual28buffer synthetic conservation, unchanged functional clock/reset-pin proof and generated Tcl round-trip pass. Use detailed-source wire cleanup and bounded same-process post-ant data fanout repair, then require fresh allcorner setup/50ps hold/zeroelectrical/antenna/overflow before DRT. Post-detailed-route diode changes still require final extracted qualification. Phase2/official GDS remain open.

## Fanout-load screen qualifies; exact continuation prepared

38453218365 succeeds on57028198781956737a0709e16b88d18c7cd40d67 (artifact11842440456). Savedstrictresults:setupWS0 allcorners;fast/typ/slow hold77.3791/174.240/345.834ps; slew/fanout/cap0 allcorners;antenna0;zerooverflow/live-demand audit passes.28plannedcells, noresizes,0postantbatches. Independent actual-source re-audit confirms canonical plan, all old placements, complete buffer connectivity and antenna-only final interval. Every functional CLK/GCLK/GATE/RESET_B pin still connects to its original net, including the clock branch whose diode loads moved.

Prepared exactsuccessfulsource stock DRT/extraction continuation. Revalidate entire source receipt/run/head/workflow, canonical source/repair/history, frozen2/4 fullnative recipe andfresh views; recheck allgates beforeDRT. No repair/fullGRT replay; require0DRC/fresh conserved NL and unchanged allcorner extracted setup/hold/50ps fast hold/zero electrical/antenna with allthree corners. Preserve priorfailedextraction separately.74focused continuation/source/protection tests andactualartifact audits pass. Detailedrouting may stilladddiodes; allfinalgates mustpass beforeofficialadoption. NoPhase2 completion orpositive globalsetup-margin claim.
