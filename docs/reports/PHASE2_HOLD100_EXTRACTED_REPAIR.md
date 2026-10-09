# Hold100 extraction and independent repair probes

2026-10-09. Native route37870374707/artifact11591942595 finishes in65min. Workflow success is diagnostic completion, not timing/electrical closure.

| Extracted metric | Result ns |
|---|---:|
| Slow setup | −0.522092606 |
| Fast/typical setup | 0 |
| Fast hold | +0.053669681 |
| Typical hold | +0.135278459 |
| Slow hold | +0.291619737 |

Slow setup improves about0.902ns versus native125, but fails. Fast hold has only3.67ps above the50ps gate. Electrical counts slow/typ/fast: slew132/37/4, fanout186 each, cap6 each. Slow SRAM REN slew1.265403ns exceeds0.595200ns; SRAM DOUT0 cap0.130419pF exceeds0.064000pF. Other slow cap failures: place8636,28807,28820 and SRAM DOUT1/2.

The slow critical path remains live configuration latch48179→pin selection/feedback→dropped[67] endpoint47345. Bufferplace7221 drives0.153229pF with0.839553ns cell delay; following O21AI24875 contributes1.161771ns. Actual max/min/checks reports and extracted NL/SPEF were downloaded selectively, not recreated.

## Fixed-wire probes

All baseline six setup/hold metrics match actual CI within1e-6ns; pinned library masters and command diagnostics are checked. Connectivity, state and constraints unchanged except explicitly labeled reserve tests.

| Strength changes | Slow setup ns |
|---|---:|
| Only place7221 BUF1→4 | −0.209308133 |
| Buffer plus37732 NAND2_1→2 | −0.209308133 |
| Buffer plus24896 NOR2_1→2 and29918 NOR3_1→2 | −0.185588434 |
| All four | 0 |
| Four plus30202 NOR3_1→2 | 0 |

All hold metrics stay unchanged. Four changes add21.7728µm² library area; no delay cells are weakened. Adding REN29426 NOR2B_2 and functional28820 NOR2_2 keeps setup0all and hold unchanged, adds7.2576µm², and changes slew counts132/37/4→112/36/3. Cap/fanout remain6/186 each. These results are not physically rerouted or officially validated.

Four-cell reserve test at19.9ns fails slow−0.098358661ns;19.8ns fails−0.198358670ns. Thus the20ns nonnegative result has very little setup reserve on the limiting branch. Hold is unchanged. Do not infer robustness from globalWS0, which includes time-borrowing latch behavior. Initial reserve harness refused to run because its strict clock-match regex did not accept20.0000; corrected before producing these results.

Raw evidence: /tmp/tripwire-hold100-{driver-probe,cone-probes,minimize,fourcell-reserve}-37870374707. Next improve reserve while preserving fast hold, measure physical buffering for remaining capacitance/slew, then matched GL and official clean-build integration. No phase gate passes from this report.

## Reserve bottleneck investigation

Adding30202 NOR3_2, strengthening place7311 toBUF4, or strengthening place7221 further toBUF8 does not improve the measured19.8ns global result. The reserve-critical path is configuration latch48107 (unit0word15bit4)→token producer tok[14] endpoint46108, a separate configuration/logic cone. Its NOR4_1 cell38013 contributes0.947729ns and NAND4_1 cell38107 contributes1.125409ns in the19.9ns report. Adding38013 NOR4_2 improves19.8ns slowWS−0.198358670→−0.105846003ns, still failing. NAND4_2 is absent in the pinned library; the guard rejects that probe before linking, so no result is claimed for it.

Combined electrical sizing on hold100 improves SRAM REN slew1.265403→0.652105ns but still exceeds0.595200ns. Buffering remains necessary to address attached capacitance, including SRAM DOUT0 more than twice its limit. These are actual report limits, not reasons to weaken constraints.

The available-cell reserve probe adds38013 NOR4_2 and30044 A21OI_2 to the four changes. At19.8ns, setupWS0allcorners and holdfast+0.053669680ns/typ+0.135278463ns/slow+0.291619748ns. This demonstrates200ps period reserve with fixed parasitics; it is not a rerouted result or a guarantee of official closure. Raw comparison: /tmp/tripwire-hold100-config-reserve-37870374707/comparison.json.

## Physical sizing preparation

native_hold100_size.py pins the actual extracted source SHA256 c4461934d2faf14ea22593a1ff3201473cbbd064252e5252b094ea7c2305760b and six exact masters/connections. It emits a Tcl call from the Python target contract; native_hold100_size.tcl checks every instance/master/signal/power pin before any mutation and checks unchanged connectivity afterward. Missing/incompatible targets, repeated repair and unexpected netlist changes are rejected. The actual extracted prototype passes exact six-change validation.70 focused tests include real Tcl execution with physical APIs mocked; these do not constitute physical routing tests.

Preparation found/fixed BUG83: multiline SRAM buses were omitted by the existing inner pin parser. The full actual six-cell change audit was repeated with bus ports included and passes. Initial synthetic fixture failed because it omitted the whitespace present in mapped instances; fixed before validation. The physical-flow wrapper and separate screen workflow are now prepared locally. Legalization, fresh GRT/antenna/STA and actual DRT/extraction remain mandatory before promotion.

gds-native-hold100-strength-screen downloads only reviewed route37870374707, verifies provenance/trusted hardware/full native config and source NL hash, then uses a pinned-base image with a wrapper restricted to sizing/legalization at the single GRT checkpoint read. All six target receipts and zero overflow are required. Optional antenna cleanup disallows congestion, exports fresh NL/PNL, rejects any logic changes beyond new antenna cells, and never invokes another full GRT afterward. Stale SPEF/SDF/lib views are cleared. Fresh all-corner STA gates nonnegative setup/hold plus50ps fast hold. This workflow ends at a physical screen; it does not run DRT or establish electrical/official closure.

83 focused tests pass, including full orchestration with/without antenna cleanup and pass/fail hold gates, exact-change audits, real shell wrapper injection, Tcl preflight checks, connectivity regression and workflow source selection. Physical OpenROAD operations are mocked in local orchestration tests; no screen has been launched yet. SRAM-buffer relocation remains a separate next trial.

## SRAM output placement target

Actual DOUT0 net maps to lane0 mem_rdata[0] and has only one standard-cell sink: wire9447, a BUF4 input. It already isolates downstream fanout. Nominal SPEF uses1pF units and gives this net interconnect capacitance0.126627pF; reported macro output load is0.130419pF. Thus the measured load is dominated by routing, not multiple logic sinks. First test relocating the existing output buffer near the macro boundary with legalization/rerouting, rather than assuming another buffer is needed. This is a potential zero-added-cell-area repair, not a measured improvement. Preserve downstream connectivity and check SRAM read setup/hold at every corner.
