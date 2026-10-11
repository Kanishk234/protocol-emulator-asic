# Clock8 extracted timing repair preparation

Source: successful routing/extraction run37998284236, headaceb926a166c18b6d76ed79c83c5df800accf472, artifact11650178212. Extracted slow setup−1.467189078ns; fast hold+0.094165012ns. Slow/typ/fast slew125/29/1, fanout21each, cap8each. This candidate is not accepted for signoff; retain original strength37954320974 as the timing baseline.

## Path diagnosis and independent STA

Worst slow path starts configuration latch48179 and ends47345 through U0 pad selection and generic timed-unit logic. All configuration/latch checks remain timed. Weak place7221 BUF1 contributes0.865247ns delay and degrades the following gate. Subsequent worst paths shift between latch48179(word0) and48112(word4); a change that improves only one cone may leave WNS unchanged.

Local OpenSTA uses actual exported propagated-clock SDC and nominal extracted SPEF at all three Liberty corners. Baseline setup/hold reproduces six CI timing values within1e-6ns; baseline electrical counts agree exactly. Probe results reuse those physical wires and are not routed gains.

| Candidate | Slow setup WNS ns | Fast hold ns |
|---|---:|---:|
| Original clock8 route |−1.467189|+0.094165|
| Only place7221 BUF1→BUF4 |−0.868789|+0.094165|
| Previously measured six-cell sizing pattern |−0.251346|+0.094165|
| Six plus INV24876 sizing |−0.238119|+0.094165|
| Nine targeted changes |−0.106038|+0.094165|
| Ten including place7311 BUF1→BUF4 |−0.039028|+0.094165|
| Eleven including place6636 BUF1→BUF4 |0|+0.094165|

Eleven-cell prototype has setupWS0allcorners; typ/slow hold+0.196403116/+0.367677778ns, unchanged from local baseline. At 20 ns, global setupWS hides positive reserve. A tighter-period diagnostic establishes that eleven changes provide only about 3.27 ps slow setup reserve: 19.9 ns gives −0.096733294 ns and 19.8 ns gives −0.196733296 ns. Adding place6637 BUF1→BUF4 improves the 19.8 ns result to −0.071825214 ns, implying about 128.17 ps reserve at 20 ns. The limiting path returns to latch48179. Official constraints remain 20 ns. NOR37506 sizing gives little benefit alone and none on top of twelve; A21OI30048 sizing worsens the eleven-change diagnostic, so both are excluded. All prototypes retain baseline electrical counts; they do not remove125slow slew/21fanout/8cap violations. Zero reported setupWS does not establish positive setup reserve.

## Concrete prototype for physical qualification

Twelve changes: place7221/place7311/place8245/place6636/place6637 BUF1→BUF4;24812/24876 INV1→INV4;37732 NAND2_1→2;24896 NOR2_1→2;29918 NOR3_1→2;38013 NOR4_1→2;30044 A21OI_1→2. Actual logical audit requires identical cell names and all signal pin connections, with only these master substitutions. Pinned LEF footprint increase70.7616µm² for eleven (the twelfth buffer adds area that still needs a pinned-LEF accounting) before legalization/routing/antenna consequences; no measured final-area benefit or budget pass claimed.

Local native_clock8_size.py pins actual DRT NL SHA256 `15eba6e2995b1235d8372e81c9063e95ce9de3558cf283f320b879549767c019`, validates exact source pin/master identities, generates targets for the previously exercised preflight sizing Tcl, refuses overwrite, and labels physical qualification required/nonofficial. Actual-source twelve-cell topology audit passes. A standalone native_clock8_screen.py and manual gds-native-clock8-strength-screen workflow are now prepared locally. They pin route37998284236/headaceb926a, full trusted clock8 recipe/hardware, and exact final netlist; apply twelve strengths through the existing preflight/DPL wrapper; clear ordinary routed wires; require zero GRT overflow; permit one antenna-only cleanup with congestion disabled; and check fresh all-corner setup/hold with the50ps fast-hold gate. 102 focused helper/provenance/native-route/Tcl checks pass, and workflow YAML parses. Tcl checks require the local runtime on PATH. These checks use mocked physical APIs; ODB execution remains untested. This screen does not assert electrical closure, detailed-route extraction or GL. No workflow published or launched.

Raw temporary comparisons: /tmp/tripwire-clock8-strength-probes-37998284236/comparison.json, /tmp/tripwire-clock8-residual-probes-37998284236/comparison.json, /tmp/tripwire-clock8-targeted-probes-37998284236/comparison.json, /tmp/tripwire-clock8-final-strength-probes-37998284236/comparison.json, /tmp/tripwire-clock8-closure-probes-37998284236/comparison.json. Detailed paths/changed-master inventory remain in those temporary directories, not committed raw logs.

Next: prepare a standalone exact-source physical screen with old-wire reset, unchanged logical audit,0overflow, fresh antennas and allcorner/50pshold gates. Detailed extraction and exact-netlist protocol GL remain required before selecting it. The official20ns/50MHz/6x4/full2-4 contract and electrical/Phase2 gates stay unchanged.

Reserve evidence: /tmp/tripwire-clock8-margin-next/comparison.json. Twelve changes retain setupWS0 at 20 ns at all corners and fast hold +0.094165012 ns in the earlier closure comparison; fixed-wire diagnostics are not a new routed signoff result.

Startup failure38011244004 (BUG89): source guard used DRT hash against exported final NL. Corrected exported hash `f4098dfd7ac36eb044867ab6d8728c98a58f0ce1754b60d7ba0d0e47b9f0a43e`, retains DRT hash above and requires identical topology.103 focused tests and actual exported-source target generation pass locally. No sizing or routing occurred in failed screen; no new timing result. Publication/rerun pending.

## Qualified physical screen38017421599

Successful screen on bf217bfcc95a54a37f0b3e07ccdf8e2e52d832d3; artifact11656728386. Actual fresh post-antenna comparison: setupWS0 at allcorners; fast/typ/slow hold +0.100129/+0.203273/+0.378213ns. Slow/typ/fast slew4/1/1, fanout25each, cap0each. This is GRT-estimated timing, not a new extracted result. All twelve master substitutions executed and source/history/0overflow/antenna gates passed.

Prepared separate local native_clock8_strength_route.py and gds-native-clock8-strength-route workflow. Pins successful exact screen/run/SHA, its twelve-change receipt, original exported hash, before/after logical chain, wire-reset receipt and saved qualified checkpoint. Rechecks trusted hardware/full clock8 recipe, fresh antennas and allcorner/50ps gates; then stock detailed routing and new extraction without repeating sizing or GRT. Old extraction is preserved separately.109focused continuation/sizing/route tests pass. Publication/dispatch pending; no official or electrical-closure claim.

## Extracted continuation38019338907 — not accepted

Workflow succeeds in38m14s, artifact11658572276, but fresh slow setup is −0.088384413ns and fast hold is +0.042690352ns, below50ps gate. Typ/slow hold +0.136529902/+0.293931998ns; typ/fast setupWS0. The GRT timing pass did not survive detailed-route extraction. Original strength37954320974 remains the retained timing baseline. Next inspect exact setup/hold paths and electrical load changes; no official/Phase2 pass.

## Residual diagnosis after extracted route

All three checks.rpt files independently reproduce electrical_summary.json. All34 fanout drivers map to exact final-netlist connections: four internal clock branches each drive16BUF8 inputs with no diodes; all30 other branches have antenna cells. Worst data driver29457 has8functional+12antenna loads; place8587 has8+8;29451 has8+7. This points to reserving fanout capacity before antenna repair and physically splitting functional/antenna load groups while retaining required diodes. Removing diodes or relaxing max_fanout is not a repair. Clock splits require separate skew/hold qualification.

Fast hold limiting paths are47696→46984 (+42.690352ps) and47993→46597 (+45.020ps), on U3 configuration word6 bit2 and U1 configuration word4 bit8 respectively, confirmed from exact netlist latch Q connections. Both are shorter data cones than the long U0 setup path48179→47345. Targeted delay insertion at those endpoints is a candidate for physical testing; it has not been implemented or measured. Do not remove existing delay cells on long setup cones without measuring their own hold checks.

Local OpenSTA reproduces all six extracted setup/hold numbers within1e-6ns. Fixed-wire probes place7312BUF4,24716INV4,place7221BUF8 and combined7312/24716 each improve slow setup to−0.069773525ns, with fast hold unchanged+0.042690352ns and all electrical counts unchanged. Critical path shifts to48112→47345 (U0 configuration word4); simply adding these changes does not close timing. Temporary evidence: /tmp/tripwire-clock8-residual-38019338907/comparison.json and /tmp/tripwire-clock8-residual-fanout-38019338907.json. No routed benefit or phase completion claimed.

Additional exact-source NOR43917_1→2 fixed-wire probe improves setup to−0.038946625ns, preserving hold and electrical counts; NOR37506_1→2 slightly worsens WNS to−0.088395074ns and is excluded. Evidence: /tmp/tripwire-clock8-targets-38019338907/comparison.json.

Combined NOR43917_2 and place7312BUF4 gives slow setup−0.028375525ns, typ/fast0, fast hold+0.042690352ns; electrical counts unchanged. It remains failing and is not selected for physical publication. Temporary comparison: /tmp/tripwire-clock8-combined-38019338907/comparison.json.

## Exact-source residual repair preparation (2026-10-10)

Prepared local clock8_residual_plan.py and clock8_residual.tcl against DRT NL SHA f9e558c27c0876d9a2f280130a618090732a36d2a272bc3b1989a7794b059b24 and DEF SHA a09a3856f46b2f7684b84e82fc0554174213d26318f70a75ea1b37e65973f218 from38019338907. Separate proposals, never a combined unmeasured change:

- Antenna:29457/Y has20loads (8functional/12diodes). Retain nearest6, spatially partition remaining14 into7/7; twoBUF4 inputs leave8upstream. All existing diodes/cells preserved. New locations are initial centroids, not verified legal sites.
- Hold: add oneBUF1 on46984/D and one on46597/D; exact drivers42227/NOR2B1 and40391/NOR2_1 each have one existing data sink. Placement starts at endpoint coordinates and requires legalization; no delay benefit inferred from placement.

Validator recomputes canonical proposal from pinned source/layout and permits exactly two added identity buffers plus enumerated sink rewires. Tcl preflights source connections, attached masters, new-name collisions, buffer pins, power and all sink nets before mutation; clock/reset pins are prohibited.16 focused topology/rejection/Tcl-completeness checks pass; both actual-source synthetic topology audits and target generation pass. Tcl physical OpenDB execution has not been tested; parsing is not physical qualification. Initial Tcl test invocation needed a script-file argument for this environment's OpenSTA-backed tclsh adapter, then passed.

Next prepare a standalone wrapper/workflow for each independent proposal: DPL, clear old signal wires, fresh0overflowGRT, topology audit, antennas and allcorner timing, with extracted follow-up required. Neither repair fixes every branch or guarantees setup/hold closure. No workflow published or dispatched.

## Independent physical screens prepared (2026-10-10)

Local clock8_residual_screen.py, pinned LibreLane Docker wrapper and manual gds-clock8-antenna-screen / gds-clock8-hold-screen workflows are reviewable. Both independently start38019338907/head77bc7608790352d118ad399b6f9c1704adab0cc1, frozen2/4bs-event-late50MHz6x4 hardware. Validate full trusted clock8 recipe/hardware and unique DRT checkpoint; canonical plan pins NL/DEF and compares original exported topology. Generate one selected-kind target file, then perform fresh GRT via preflight binding/DPL/ordinary-wire reset. Require exactly two repair receipts, positive unique wire-reset receipt,0overflow, promoted topology and at most one stock antenna cleanup with congestion disallowed. Fresh STA records complete corner/electrical comparison and acceptance requires nonnegative setup/hold,fast hold>=50ps and zero antenna violations. Source failing extracted timing is not treated as accepted; measured screens may fail and still upload evidence. No electrical gate is waived or closure claimed by timing qualification alone.

125 focused planner, promotion/provenance/workflow/native-route/continuation checks pass; shell syntax and Python compile pass. Actual source synthetic audits and target generation previously passed. Tcl completeness tests do not exercise physical OpenDB APIs; the new binding/image have not physically executed. Each120minute job uploads its independent result tree and inherited source evidence. No template/RTL/config edits; no combined repair or source timing mask. New DRT/extraction and final exact-netlist GL remain required for any promotion. Publication/dispatch pending.

## Hold screen and extracted continuation preparation (2026-10-10)

Hold screen38101472930 succeeds on6f89770559aa0531ba1167358ac21c107325f065; artifact11687693810. Estimated setupWS0all; fast/typ/slow hold+0.100798/+0.203280/+0.377012ns. Slow/typ/fast slew2/1/1,fanout36each,cap0each. Full source/baseline/two-buffer identity/antenna-only topology chain, routing0overflow and saved timing gates independently pass on actual downloaded artifact. Electrical violations remain open; estimates are not extracted signoff. Antenna38101471390 still runs at latest check, so no antenna result or combination is selected.

Prepared local clock8_hold_route.py plus separate manual gds-clock8-hold-route. Pins successful exact run/SHA and hold-only two-buffer qualification receipt; recomputes canonical source NL/DEF plan and compares saved proposal, original/post-ECO/antenna netlist chain, reset receipts and0overflow. Validates full trusted hardware/clock8 recipe, disables ECO image, rechecks fresh antennas and allcorner50ps gates, then stock DRT and fresh extraction. No repeated GRT/sizing; source extraction preserved separately.124focused hold-continuation/residual/native-route checks pass. Publication/dispatch pending. Final electrical, exactGL, area/DRC/LVS/antenna and officialGDS/precheck gates remain required for Phase2.

## General data-fanout reserve screen (2026-10-10)

Actual antenna screen topology clears29457 and retains its audited8/7/7 groups; none of these three drivers appear in the fresh max-fanout table. Aggregate36 masks new violations elsewhere after rerouting/antenna insertion, including28807,28820 and23899 relative to the original34-driver extracted set. Thus branch partition is effective locally but does not establish global closure.

Prepared one general data-fanout reserve policy on exact source38019338907: independently repartition all30 reviewed nonclock drivers whose attached loads exceed8, preserving every existing cell/diode. Minimize buffers while limiting initial source and new branch loads to6, reserving2loads for later antenna repair. Exact source generates39BUF4 additions; geometry/area/congestion after legalization/routing still require measurement. Four16-load clock branches remain untouched and unresolved. No diode deletion, constraint relaxation, protocol block or change to clock period/resource shape.

Reuses strict canonical topology validator and preflight physical binding; screen receipt count now matches selected proposal, preserving prior2-buffer variants. Tcl targets use the previously observed OpenDB bracket escaping for hierarchical data nets.127focused planner/physical-screen/continuation/native-route tests pass; actual source39-buffer topology audit and target generation pass. Separate manual gds-clock8-fanout-screen prepared, same0overflow/antenna/allcorner50ps gates. This is a reserve hypothesis, not a guarantee that later antenna insertion stays under8 or that setup/hold improves. New physical execution and extracted qualification remain required.

## Fanout screen qualified continuation (2026-10-10)

Screen38102524361 succeeds onacf2827167d1c34c87824f80304ee82aec345206; artifact11689015681. Estimated setupWS0all; fast/typ/slow hold+0.100739/+0.203280/+0.378222ns. Slow/typ/fast slew11/1/1,fanout8each,cap0each. Actual canonical saved proposal/39buffer topology/antenna-only cleanup/0overflow/fresh timing gates independently audited and pass. Remaining fanout: four internal clocks16loads/no diodes; place8354(16loads/8diodes),28820(13/6),place7616(13/6),26701(9/4). Two-load diode reserve is insufficient on some rerouted branches and new violations can appear on previously compliant nets. No aggregate zero-violation claim.

Prepared clock8_fanout_route.py and manual gds-clock8-fanout-route: exact successfulsourceSHA/run,39bufferqualificationreceipt, canonical savedproposal and fullsourcechain; sourceviews include explicit actual tt_um_tripwire.def basename (BUG90 fix). Trusted fullclock8hardware/recipe, freshantenna/allcorner50psgate, stockDRT and newextraction; no repeated repair/GRT.151focused residual/hold/fanoutcontinuation/nativeroute checks pass plusactualartifactaudit. Initial Tcl-suite invocation lacked runtime PATH; corrected invocation passes without code workaround. Source extrapolation is not signoff; finalelectrical/area/DRC/LVS/GL/officialGDS still open.


## Independent internal clock branch screen prepared (2026-10-10)

Hold route [38102572131](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38102572131) and fanout route [38103189246](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38103189246) are in the fresh qualification/routing/extraction step at this check. Neither has final extracted evidence yet.

The new `clock` residual policy starts independently from the exact NL/DEF of source 38019338907. Each of four reviewed BUF8 clock drivers currently feeds sixteen BUF8 inputs. Eight added BUF8 cells split these into two spatial groups of eight per original driver; upstream fanout becomes two. Existing cells, leaf clock pins, reset pins, hardware and signoff constraints stay fixed. The OpenDB binding preserves each source net's signal type on its new downstream net. This changes internal clock distribution and can regress skew, setup or hold; fresh allcorner timing and the existing 50 ps fast-hold gate remain mandatory.

Verification: 155 focused planner/screen/hold-route/fanout-route/native-route checks pass. Exact actual-source hashes, canonical partition, generated Tcl and synthetic identity-topology audit pass. This proves preparation/connectivity only, not physical legality, timing, area closure or official signoff. The separate manual `gds-clock8-clock-screen` workflow is prepared locally and has not been published or dispatched. No Phase 2 checklist box is ticked.


### Publication commands for the prepared clock screen

Additional clock-specific rejection checks cover altered source drivers, altered sink masters, absent placements, missing loads and unplanned rewires. The focused suite now passes 165 checks. Both route runs remain in progress at this session's status check. The shared wire-reset helper clears ordinary clock wires as well as data wires (preserving power/ground), so this screen cannot retain the old routed clock branches after the topology change. Actual physical behavior still needs CI measurement.

Latest supplied AGENTS.md reserves history/remote commands for the user. Run these groups to publish only the prepared screen; unrelated local reports and FIPE are excluded. Before pushing while hardening runs, inspect the required hardware-history guard:

```bash
git log origin/main..main -- src info.yaml macro
git add scripts/ci/clock8_residual_plan.py scripts/ci/clock8_residual.tcl scripts/ci/clock8_residual_screen.py scripts/ci/test_clock8_residual_plan.py scripts/ci/test_clock8_residual_screen.py
git commit -m "ci: prepare audited internal clock branch repair"
git add .github/workflows/gds-clock8-clock-screen.yaml
git commit -m "ci: add independent clock branch screen"
git add docs/WORKLOG.md docs/reports/PHASE2_CLOCK8_TIMING_REPAIR.md
git commit -m "docs: record clock branch screen preparation"
git push origin main
gh workflow run gds-clock8-clock-screen.yaml --ref main
```


The user subsequently explicitly approved publication. The prepared helper and workflow groups are committed as eb21e49 and 931973c; publication/dispatch verification follows. This approval supersedes the earlier user-run publication handoff for these groups.


## Clock screen audit and independent extracted continuation

Screen 38103503234 artifact 11688563140 passes an independent exact-source canonical topology/antenna-retention/zero-overflow audit. All four original internal clock branches now have two loads; each of eight added BUF8 outputs has eight loads. None of these clock drivers remains in the fresh fanout violation table. The 31 remaining fanout violations are data branches. Fresh complete electrical tables confirm slew slow/typ/fast 12/2/1 and one capacitance failure in every corner: SRAM A_DOUT[0] (fast 0.068412 pF versus 0.064 pF limit). Slow slew failures include SRAM A_REN, A_MEN, A_ADDR[6] and the _28807_ data cone. These are independent of the repaired clock fanout. The saved comparison uses the same final state for before/after; its zero deltas do not measure benefit against the original source.

Prepared independent `gds-clock8-clock-route` continuation pins screen 38103503234/head fd5c64173acacb3e8cbaf08fd4b4491b357d3f55, its eight-buffer canonical proposal and exact source NL/DEF. It rechecks topology, antenna-only changes, routing history and fresh allcorner/50 ps hold/antenna gates before stock detailed routing and fresh extraction; it does not repeat the clock ECO or combine unmeasured repairs. 189 focused checks pass. Existing user publication approval applies. No Phase 2 tick or promotion; final zero-electrical, DRC, GL and official requirements remain open.


## Post-antenna residual repair preparation

Added `residual_load_audit.py` to map complete electrical violation tables to exact netlist drivers, actual attached sink pins and diode loads. It fingerprints the netlist, preserves the distinction between STA fanout and pin count, rejects missing electrical sections/mismatched counts/absent drivers, and applies no ECO. Four focused checks pass. Actual clock screen fast report maps 31 data branches and zero clock branches; worst _29457_ has 20 sinks including12 diodes, place8587 has16/8, and _29451_ has15/7.

Next bounded physical policy: recompute violating data branches after antenna insertion, retain all diodes, partition using actual attached loads and spatial clusters, reroute and recheck antennas, electrical limits and allcorner timing. Consider a four-load initial target for residual branches rather than the prior six-load target, but large branches require a bounded multilevel tree to keep upstream fanout legal too. Limit iterations and reject repeated topology or timing/overflow regression; do not publish a success receipt from intermediate timing-only gates. This physical policy is not implemented or measured yet. Starting checkpoint remains undecided until independent extracted results arrive; three route runs remain active at this check.


## Hold repair extracted result: 38102572131

Run 38102572131 completes successfully on exact head8336e5ac1ef36971426e77291f34f442c3a4de35; artifact11689807226. Fresh extracted slow setup **-0.067696961ns**, typical/fast0. Hold fast **+0.091667843ns**, typical+0.187180499ns, slow+0.353127537ns. The targeted hold repair survives extraction and exceeds the50ps gate; slow setup still fails. Independent parsing of all three complete checks reports matches saved electrical summaries: slew slow/typ/fast187/22/6, fanout41 each, capacitance4 each. Do not promote this candidate or infer official closure from workflow success. Compared with source38019338907, hold improves42.690→91.668ps and slow setup improves-88.384→-67.697ps, but slow electrical counts worsen146→187 and fanout34→41. Fanout/clock extracted routes remain running at check; compare these before selecting follow-up.


## Fanout repair extracted result: 38103189246

Run38103189246 succeeds on ad189c03a2d9f46826365bb7e452721fc3be0f95; artifact11689887054. Fresh extracted slow setup **-0.065506713ns**, typ/fast0. Hold fast **+0.093253852ns**, typ+0.200783507ns, slow+0.376085729ns. Independent complete checks report parsing agrees with every saved electrical summary: slew slow/typ/fast120/22/6, fanout14each, capacitance2each. Four fanout failures are the unchanged clock branches; ten are data branches. Cap failures are place8636/X and SRAM A_DOUT[0] (fast0.094677pF against0.064pF). Estimated screen fanout8 becomes14 after detailed routing, and slow slew11 becomes120; no screen estimate may substitute for extracted closure.

Compared with hold-route38102572131, fanout route has similar slow setup/fast hold but fewer fanout41→14, slow slew187→120 and capacitance4→2. Prefer this as the provisional convergence checkpoint among these two measured routes; pending clock extracted result may change selection. It still fails setup and electrical closure and is not promoted to main RTL or official qualification. Next combine only validated useful clock policy with this checkpoint in one integrated candidate, then repair its actual residual data/SRAM/setup failures with fresh extraction.


## Fanout-route residual target mapping (parallel analysis)

Exact final NL and allcorner setup/hold paths from artifact11689887054 retrieved; `residual_load_audit.py` maps all14fanout failures to actual sinks. Four unchanged clock branches have16BUF8loads/no diodes. Ten data drivers: place8354(16/8diodes),place8379(15/7),28820(13/6),place7616(13/6),26701(9/4),26706(9/1),26845(9/1),27698(9/4),45871(9/1),place8807(9/1). This is the integrated candidate's concrete data repair list, not the earlier screen's four-data residual list.

The two failing slow setup paths share start48179 (U0configuration word0bit4 latch) and end46883/46884 (U2TX eq13/eq14): -65.507ps/-38.693ps. Both include NAND3_1 instance24811, whose output has0.119093pF load,1.615409ns slew and1.349124ns cell delay, feeding24812 INV4 and28083 A21O1. This is a concrete candidate for an equivalent driver-strength probe on the new measured source; benefit and upstream/fast-hold effects are unmeasured. Both paths also traverse hold12461 with0.611712ns slow delay; do not remove it without reproducing allcorner timing and inspecting every affected fast hold path.

Other bounded targets: place8636 BUF1 drives eight actual pins (seven logic and one diode); it violates capacitance despite meeting fanout, requiring drive/placement/load repair rather than a fanout-only rule. SRAM output0 feeds wire9447 BUF4, so moving its existing input buffer nearer the macro may reduce output-wire capacitance without another buffer. REN driver29426 NOR2B1 also feeds hold11833 and a diode; MEN driver29663 A21OI1; ADDR6/ADDR0 buffer outputs place7514/place7516 each also connect a diode. Geometry and full extracted timing must be audited before any physical target is applied. Clock route38104539932 still runs; no further candidate launched or design integrated in this analysis.


## Clock route extracted result and convergence selection

Run38104539932 succeeds on cbf2735d66bf293243e3b00e0c2ef7ce36bf1de3; artifact11689569002. Fresh slow setup **-0.186608068ns**,typ/fast0; hold fast **+0.076138709ns**,typ+0.172239339ns,slow+0.335699700ns. Independent complete allcorner electrical parsing matches saved summaries: slew slow/typ/fast177/5/5,fanout36each,cap4each. No clock fanout rows remain, so targeted clock repair survives extraction. However total electrical violations and slow setup remain unacceptable. SRAM DOUT0fast cap0.130811pF exceeds0.064pF; DOUT2 and29451/29457also fail cap.

All three independent routes are now measured. Select fanout-route38103189246 as the convergence checkpoint: slowsetup-65.507ps,fast hold93.254ps,slow slew120,fanout14,cap2. Hold-route is worse electrically; clock-route is worse in setup and total electrical closure despite removing clock fanout. Retain original strength37954320974 as the timing-passing reference, not as an electrical closure claim. No candidate passes allrequirements and no Phase2 box is ticked.

Next work is one integrated follow-up on the selected fanout checkpoint: address its exact residual drivers/load/placement and shared critical setup cone, measure the remaining clock repair within this layout, protect fast hold and preserve constraints. Do not transplant the eight-buffer clock policy unchanged on the assumption of additive improvements. Every changed checkpoint needs topology/antenna/overflow and fresh extracted allcorner electrical/timing evidence before final GL/integration/official GDS. No new candidate launched in this result review.


## Selected fanout source: local setup probes (not qualified)

Retrieved exact fanout38103189246 final NL/SPEF/exported SDC. Pinned library only provides NAND3_1, so direct24811upsizing is unavailable. Tested independent fixed-wire equivalent changes: INV24812_4→2 worsens slow setup-65.507→-142.167ps; BUFplace7307_1→4 and BUFplace7308_1→4 each produce reported slow setupWS0, typ/fast0 and unchanged local fast hold93.253851ps. Electrical counts remain120/22/6slew,14fanout,2cap. WS0 does not prove positive setup reserve.

Strict baseline validation rejects this batch: source slow hold376.085728760ps versus local375.826925ps (difference0.258804ps, above1e-6ns tolerance). Baseline slowsetup-65.506712ps,typ setup0/hold200.783506ps and fast setup0/hold93.253851ps reproduce source within tolerance. No tolerance relaxation, physical change or timing pass claimed. Raw probe logs remain /tmp/tripwire-fanout-setup-38103189246; investigate slow hold path/library/STA reproduction before promoting a strength target. Buffer probes are promising hypotheses only; fresh physical routing/extraction and electrical repair remain mandatory.


## Local hold mismatch isolated; explicit setup reserve probe

Expanded local slow hold report has the same _46328_→_46328_ self-feedback path as CI. Data arrival2.046538830ns, early clock arrival1.612994075ns, late1.824418187ns and library hold-0.042541128ns match CI to printed precision. CI clock reconvergence correction is approximately0.211424ns (full clock arrival difference); local OpenSTA2.6.0 uses0.211165309ns. The discrepancy equals the final clock wire's late1.516232ps minus early1.257439ps, or0.258793ps. This isolates the reproduction mismatch to treatment of the final clock segment in reconvergence correction; an STA implementation/settings difference is inferred, not an unexplained data-path change. No manual slack offset or tolerance waiver applied. Exact pinned-engine validation remains required before accepted qualification.

A local explicit endpoint check for place7307BUF1→4 gives setup slack **+19.589664ps** at46883 and **+46.403769ps** at46884. This is real reported local endpoint headroom, rather than an inference from aggregateWS0, but fixed-wire and not physically qualified. Headroom remains small, electrical counts unchanged, and other endpoints must also pass. The one-buffer strength change is a candidate for the selected fanout checkpoint's integrated physical qualification, with exact-source/master/topology checks and full fresh extraction; no physical change or new dispatch yet.


## Selected-checkpoint one-buffer physical screen prepared

Prepared `fanout_setup_plan.py`, `fanout_setup_screen.py` and manual `gds-fanout-setup-screen`: exact source run38103189246/headad189c03a2d9f46826365bb7e452721fc3be0f95, DRT NL388d1b91816f8ce1ad3cdbae071998617637979425e46d3a4b13af618ec4cb67 and DEF344286c41b56c9d279b4556b5e8ff24be5a8c4f2c68163e19016d9f56dd84ccd. Changes only place7307BUF1→BUF4, preserving exact A=net7308/X=net7307 connectivity and every other cell. No added buffer, hardware or signoff constraint change.

Uses already physically exercised guarded sizing/DPL/wire-reset/antenna bindings, canonical master-only topology audit, full trusted clock8 recipe/hardware and exact DRT/exported topology. Fresh GRT must have0overflow and exactly one sizing/reset receipt; antenna repair preserves diodes, followed by fresh pinned allcorner timing and50psfast-hold gate. This directly measures the hypothesis with pinned CI tools without accepting the local CRPR discrepancy as signoff. Estimated screen results still require new DRT/extraction; electrical counts are recorded and cannot imply Phase2 qualification from timing-only screen success. 161 focused checks and actual-source canonical/target generation audit pass. Publication/launch under ongoing user workflow approval; no phase box.


## Parallel SRAM placement preparation on selected checkpoint

While setup38108151690 runs its physical step, added read-only `fanout_sram_plan.py` pinned to the selected38103189246 DRT NL/DEF. Reuses reviewed LEFgeometry fingerprint c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219, exactexistingcell/pin/placement guards and complete footprint occupancy checks. Actual selected source generates SRAM DOUT0buffer wire9447BUF4 candidate ROW64(25.92,245.70)N, no footprint overlaps and origin-to-macro-pin distance17.66µm, versus current451.64µm. REN driver29426 candidate ROW64(132.96,245.70)N gives19.19µm versus314.87µm. Alternatives documented only in local proposal outputs. Neither distance is routed wirelength or proof of pin access.

Three source/connectivity rejection checks pass; combined planner/setup suite16checks pass. No buffer moved, physical legality/timing/electrical improvement measured or further workflow launched. Output0 relocation adds no cell by itself; later automatic repair costs remain unknown. If setup screen changes placements, regenerate against its exact new checkpoint rather than reuse these sites blindly. Next qualify output0 relocation in the evolving integrated design, protecting upstream/downstream setup/hold and fresh antenna/electrical/overflow gates; REN is a subsequent measured physical step, not a simultaneous unmeasured combination.
