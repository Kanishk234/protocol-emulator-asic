# Selected SRAM screen: residual repair priorities

Source: [screen 38111368461](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38111368461), artifact 11692116594. Preliminary global-route estimates; extracted continuation [38112320460](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38112320460) remains authoritative for the next physical repair.

Exact final screen netlist SHA-256: `2c00046d787af2d045bbb61a9fab4e15b0356c34ffb6d7397a950f6ecf104a80`.

Report rows independently match saved slow-corner slew 34 and fanout 18. Mapping to exact connected pins finds 14 data branches and four clock branches. Capacitance metrics are zero; the preliminary report omits that section, so this is not a complete electrical-report signoff audit.

| Target | Evidence | Small next repair | Cost and limitation |
|---|---|---|---|
| `_28807_/Y`, net `_03831_` | 17 slew rows; 16 loads, including 8 diodes; NAND3_1 | Partition nearby sinks into four BUF4 branches | Four cells; no stronger NAND3 variant available; fresh antenna insertion can consume load reserve |
| `_28820_/Y`, net `_03844_` | 14 slew rows; 13 loads, including 6 diodes; NOR2_1 | Partition into four BUF4 branches | Four cells; source drives four buffer inputs; timing must be remeasured |
| SRAM A_REN | 1.014359 ns slew against 0.595200 ns limit | Reposition existing REN driver toward macro before adding a stage | No added cell if existing driver can move; shared hold paths must remain above 50 ps |
| SRAM A_ADDR0/6 | 0.640266/0.628722 ns slew against 0.595200 ns | Inspect extracted wire load and existing driver strength/location | Small deficits; avoid unnecessary blanket upsizing or hold-buffer removal |
| Four clock branches | 16 BUF8 sinks each, no antenna diodes | Retune branch placement/depth with setup and hold budgets | Prior eight-buffer split worsened extracted setup; do not transplant it unchanged |
| Remaining 12 data branches | Mostly 9–16 loads with diode contributions | Repair only after these two dominant nets are measured | Lower immediate slew coverage; indiscriminate buffering adds routing pressure |

31/34 slow slew rows belong to the first two nets. This is concentration of reported violations, not proof that buffering removes every row or preserves timing. Their two fanout violations are included among the 18, so this repair alone cannot close electrical checks.

Read-only spatial partitions on the exact screen DEF conserve every original sink and diode exactly once: 16 loads become four groups of four; 13 loads become groups 4/4/4/1. Each source then drives four buffer inputs. Eight BUF4 cells have nominal master footprint 116.1216 square micrometres (3.84 by 3.78 each); this excludes legalization whitespace, new diodes and routing costs. Candidate groups are not legalized or physically qualified. Raw proposals remain in /tmp.

Next: inspect current extracted continuation; re-pin its exact netlist/DEF and recompute placements. Apply one dominant-net repair first, preserve all diode connectivity, reroute and check setup/hold/electrical/antenna/overflow. No changes to hardware, clock constraints, protocol support or phase checklists are justified by this analysis alone.

## Extracted follow-up and first physical screen

Run 38112320460 succeeds but does not close requirements: slow setup -2.614797 ps, fast hold 48.963834 ps. Complete electrical audits show slow/typ/fast slew 147/43/4, fanout 20 each and capacitance 4 each. The two dominant branches still retain their reviewed 16/13 loads and 8/6 diodes. Repinned planner to actual DRT netlist SHA `1da984a3d76325e06e39de478f8d8cf4c24d812970df97dff72f5ee9f1244cfe` and DEF SHA `7a6172759a31a18f20c1ae2b3fd17cce4bd699c3ae18d06ece0f0b887e8fab87`; both synthetic partition topology audits pass on these exact files.

Worst slow setup is _48179_ to _46883_; worst fast hold is _48776_ to _46037_. The first proposed screen changes only _28807_, four BUF4 branches, nominal added footprint 58.0608 um2 before diodes/whitespace/routing. It uses the existing guarded residual OpenDB binding and wrapper, with full source/recipe/hash checks, exact all-cell topology validation, DPL, old-wire reset, zero overflow, antenna-only cleanup and fresh all-corner 50 ps hold gates. No signoff limits are relaxed; success remains preliminary pending detailed routing/extraction.

Prepared dominant_slew_screen.py and separate gds-dominant-slew-screen workflow, pinned to the successful extracted run and exact main head a6e44b457e11e368ebcdd2f3fdafdfd68147cde0. 123 focused tests pass. New physical split has not yet run. The original SRAM screen evidence above is historical; do not use its old DEF for this new repair.

## Dominant-net screen measured and audited

Screen 38115998705 succeeded on ecc6bcf5cc4dadd2f246a4256ba11a019aca72cf (artifact 11693474079). Independent audit confirms exact source, canonical four-buffer partition, all-cell/sink/diode conservation, one route reset, zero overflow and congestion-disallowed antenna cleanup. _28807_ is absent from the final screen fanout failures. Preliminary setup WS 0 ns all corners and fast hold 98.2493 ps qualify for extraction; electrical slew slow/typ/fast 11/1/1, fanout 21 each and cap metrics 0 each still do not close requirements.

Nine of the eleven slow slew rows are on the branch driven by _25245_/Y, plus SRAM A_REN and A_ADDR0. No blind second _28820_ repair is warranted from old screen failures; inspect extracted continuation first. Remaining fanout includes four clock branches and 17 data branches. Prepared dominant_slew_route.py and separate workflow pinned to the exact successful screen; no repeated split, fresh antenna/STA checks precede stock DRT and extraction. 116 focused tests pass, including complete checkpoint refusal cases and saved-proposal JSON round-trip. Publication and launch are pending scoped user approval.

## Timing-qualified extraction and next one-cell screen

Extracted run 38116800326 succeeds on bb7125ea2f963c78dcdc95961019a783bddfd5ee; setup WS 0 ns all corners, hold fast/typical/slow 65.626395/165.272023/337.585081 ps. Complete electrical audits match slew slow/typical/fast 134/21/4, fanout 24 each, capacitance 3 each. Cap targets now SRAM DOUT2, DOUT4 and place8636. This checkpoint passes timing gates, not electrical closure or official GDS.

Exact DRT NL SHA 402b87e6f798a8c760b277bf148a048527a74e92a87069db2801d148a0301e90, DEF SHA 73abf7de3ab00c578ca5d6718d6670f930d189c26ecb30ae8bd5d4c3d083d3eb. Worst slow slew _25245_ NOR4_1 output is 4.498456 ns against 2.5074 ns and drives eight logic pins/no diodes. Prepared exactly one NOR4_1 to NOR4_2 physical screen using existing guarded sizing binding, preserving all five signal pins and every other cell/net. Reviewed LEF footprint increases from 2.88x3.78 to 5.76x3.78 um: +10.8864 um2, no added cell. DPL and fresh timing/antenna/electrical/overflow are mandatory; strength alone may be insufficient for this severe wire load.

95 focused tests pass plus real source/hash/topology and Tcl escaped-bracket argument checks. No physical sizing has run. Separate gds-residual-nor4-screen workflow uses exact successful source 38116800326 and original full hardware/recipe, unchanged 50 ps gate. Next publish reviewed helper/tests/workflow/evidence then measure. _28820_ remains a separate 14-row slew/13-load branch target; do not combine changes before measuring this screen.

## Parallel capacitance repair preparation during NOR4 screen

NOR4 screen38162764354 is in progress (last observed preparing generated config). Read-only checks use timing-qualified DRT38116800326 only; all geometry must be revalidated after the running screen's resulting layout.

| Repair candidate | Current evidence | Proposed cost | Qualification still needed |
|---|---|---|---|
| Move DOUT2 buffer wire9439 closer to macro | Cap 0.101150–0.101696 pF versus0.064; BUF4 at341.28,230.58N; candidate45.12,245.70N | No added cell/master/net change; origin distance296.68→14.60 um | Physical pin access, power, legality, antenna and extracted timing/cap |
| Move DOUT4 buffer wire9437 closer to macro | Cap0.064554–0.065100 pF versus0.064; BUF4 at291.84,238.14N; candidate67.68,245.70N | No added cell/master/net change; origin distance231.06→14.52 um | Same; current overage is small, no guaranteed result |
| Isolate distal place8636 branch | BUF1 drives8 pins,7 logic/1diode; cap0.323056–0.327563 pF versus0.300 | One BUF4 candidate14.5152 um2; move only _36028_/A1 and ANTENNA_38/A to its downstream net; original upstream7 loads, new branch2 loads | Exact topology, legal placement near distal pair, physical RC, antenna rerun and hold/setup |

DOUT proposals were computed from pinned macro LEF pin centers, fixed SRAM placement12,40 FS, exact current DEF and reviewed standard-cell LEF. Both complete footprints have zero overlap on row64, independent candidates. These are origin distances, not routed wire lengths or guaranteed delay reductions. Raw proposals stay in /tmp.

place8636 is at249.12,264.60. Its distal logic _36028_ is at1154.40,98.28 and associated ANTENNA_38 at1155.36,94.50, over1mm Manhattan distance from current driver. The other six sinks span255.36–659.04 in x. One distal identity branch could shield the original BUF1 from the long wire, preserving both original logic and diode; blanket upsizing cannot reliably fix the physical capacitance limit. This is a topology/placement hypothesis, not a measured repair.

None of wire9439, wire9437, place8636 or _28820_ appears in the saved reported fast-hold or slow-setup path sets. Reports are truncated path samples, so this does not prove these changes cannot affect hold/setup; the15.626ps fast-hold reserve must be rechecked physically.

Priority after current screen/extraction: DOUT2 proximity first for a large zero-added-cell cap deficit; DOUT4 proximity if actual resulting layout still has a cap failure; isolate place8636 distal branch if its cap failure persists; continue selected data/clock fanout policy. Keep one physical change per measured hardening and preserve original signoff limits.

## NOR4 screen audited; extraction prepared

Screen38162764354 qualifies: setup WS0 all corners, hold fast100.728ps/typ203.267ps/slow378.209ps; slew slow/typ/fast15/1/0, fanout24each, cap metrics0. Exact one-master/topology/antenna-only/receipt/reset/zero-overflow history independently audited against66 downloaded files. These estimated figures do not establish electrical closure or improvement against extracted counts. Prepared exact screen continuation residual_nor4_route.py and gds-residual-nor4-route;112 focused tests pass. Fresh antenna and all-corner50ps timing qualification precede stockDRT/extraction; no repeated sizing. Publication/launch pending scoped approval.
