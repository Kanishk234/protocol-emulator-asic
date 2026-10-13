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
