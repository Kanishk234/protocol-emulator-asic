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
