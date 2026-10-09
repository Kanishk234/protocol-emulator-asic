# Independent compact preflight results, October 8

[Matched C2 preflight37811985092](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37811985092)
passes in1m55s including setup. Original synthesis and passing regenerated
C2 both reproduce all306 signal ports, directions, rectangles/layers and die
against the retained original pin ODB. No synthesis executed. Passing floorplan
ODB SHA2564f1972be5478f7c3c1c69253c32d8884cf5fa06a63e5ffd2086a320138cdfc70.
Original floorplan ODB SHA256b498380b42b37a2740d2718d0fa017e5fd1a30ec577eba968c3fb93699a873d6.
No PDN, detailed route, LVS or configured timing acceptance follows. This clears
a faithful physical continuation, using the exact original full-flow settings.

[Paired fanout preflight37811985079](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37811985079)
passes in2m45s including setup. Authenticated original pre-CTS source; only
CTS_SINK_CLUSTERING_SIZE changes from default to8. Macro views/location,
clock20ns, SDC, all six library file hashes and native placement checks pass.
Stock STAMidPNR emits estimated typical-corner metrics only.

| Typical estimated metric | Baseline | Cluster8 |
|---|---:|---:|
|Fanout violations|32|5|
|Slew/cap violations|0/0|0/0|
|Setup worst slack(ns)|13.9155|13.8665|
|Hold worst slack(ns)|0.296629|0.304198|
|Cell instances including macro|3557|3596|
|Total instance area(um2, rounded metric)|806793|807849|
|Standard-cell area(um2)|57231.6|58287.6|

All27 clock fanout violations disappear in this comparison. Five configuration
column outputs remain, each12 loads against effective limit8: columns1/2._23_/Y,
columns3/4/5._22_/Y. The old FSM fanout violation is absent after this flow's
resizing; this is not proof it stays absent after routing. Extra39 cells,
1056um2 cell area, more clock buffers and slightly less setup slack are costs.
No equal-total-area architectural superiority or routed/all-corner timing claim.
The [exact pinned CTS guide](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/cts/README.md)
confirms cluster size is a maximum register-sink cluster setting; actual connected
loads including dummy cells, not the knob value, establish this result.

[Native remap37811985147](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37811985147)
passes check and exact537-storage audit, then binary SAT reports a counterexample.
Do not advance this candidate. Programmable combinational feedback survives the
storage cuts; an identical-original self-miter through the same pipeline is the
next diagnostic to distinguish proof construction from genuine remap mismatch.
Actual counterexample/log retained; no proof waiver or state force.

[Official precheck37811985173](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37811985173)
fails six checks, passes layer/cell-name/analog checks. Five failures arise from
unused original filler masters becoming orphan top cells after overlay replacement.
Pin check reads native SIZE1289.28/710.64 as1289.028/710.064 because its pinned
parse_fp3 left-pads the fractional string; actual native die SIZE is correct.
Prepared single-chip hierarchy export with exact referenced shape/label/instance
comparison and exact-value three-decimal LEF formatting. Keep unmodified official
checks; rerun before claiming precheck acceptance. No routed geometry alteration.

Original driver37708459393 remains the physical/slew closure evidence. Regular
0309544 lint37811985150/docs37811985067/test37811985057/unit37811985064 all pass.
Frozen G1 remains fallback; no phase exit box ticked by these diagnostics.

Corrected official37813220689 passes eight of nine checks, including full
SG13CMOS5L DRC225.78s. Publication confirms the two extra tops were original
fill1/fill2 and preserves all724 reachable cells exactly (shape/label/instance
transforms/arrays and DBU). Remaining Pin check parser error is native RECT
double spacing. Formatting correction preserves exact values; all842 actual
RECTs now match pinned official syntax. Final pin acceptance still pending.

Identical-original proof control37813220521 fails with retained witness,
including four differing routing buses. Candidate proof/simulation does not
advance. This establishes current proof construction cannot judge the remap;
programmable feedback equations need a sound common-cut treatment first.

Matched C2 hardening37814078650 completes all physical stages in roughly7min
including setup. Fresh route/antenna/critical-disconnect0, Magic0/KLayout0 and
actual-GDS LVS0. Final router iterations1232→680→629→0. Job correctly fails
setup: worst slacks fast-3.395669619ns, slow-25.343514671ns,
typ-11.514293844ns; fanout62 at each supplied corner. Original CLOCK_PORT=null
uses a virtual clock, not a validated configured-fabric clock contract. Do not
call timing accepted. Retained actual final views need native loaded retest,
power/signal interface census and configuration-specific timing analysis.
