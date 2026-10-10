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
