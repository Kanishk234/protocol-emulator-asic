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
