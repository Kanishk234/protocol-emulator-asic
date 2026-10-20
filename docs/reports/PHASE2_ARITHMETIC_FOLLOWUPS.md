# Arithmetic follow-ups to combined screen39458833532

2026-10-20. Two independent deltas against bs-resync-event-cfg-staging;
neither changes main src, configuration, architecture, encodings or clock period.

## Evidence motivating the changes

The source-bound final netlist maps the worst slow launch to U0 PERIOD[0]
(configuration word4bit0), ending at chip dropped[22]. Its report passes through
the PERIOD/SAMPLEOFS arithmetic: the first mapped XOR takes SAMPLEOFS[0]
and a buffered PERIOD[0]. Data arrives at the launch latch at3.529114ns,
including2.131482ns borrowed; capture data arrival is18.424387ns. Sample-time
carry propagation is a concrete candidate, although the entire path contains
other logic, buffering and a hold-delay cell. Optimizing only the drop counter
would not address the whole path.

Two reserve misses are also concrete TX targets. Net16512 is driven by
cell43724/nor4_1 and structurally reaches all16 U3 TX eq bits; net14969 is
driven by41739/nor4_1 and reaches all16 U1 TX eq bits. The third net04145 is
driven by29480/nor4_1 and has a broad203-state-endpoint structural cone.
Structural reachability does not prove every path is sensitizable. These are
identities in this run only, not reused old instance mappings.

## Independent prototypes

**sample-csa** changes only normal sample-time arithmetic in trw_pin_bs.v:
compress sof, ~per and tb with bitwise XOR/majority; add the two resulting
vectors with the low carry bit set to1. This equals sof-per+tb modulo2^25,
including timer wrap. Keep the prior saturated resync cancellation, sp and
all event-selection logic. No new state or cycles. This differs from the old
D-071 CSA prototype, which compressed both normal and corrected sample
expressions before resync cancellation and had worse isolated ideal-wire
delay. That negative result remains relevant; lower area here is not timing
evidence, and only physical measurement can establish an improvement.

**tx-late-cursor** changes only trw_pin_tx.v: compute base/delayed cursor
increments before token selection, then select the result late. SYNC/late
cursor reset yields0 after the original ffff increment; other branches retain
prescaler wrap,7fff saturation and old selection precedence. rn/r_inc and all
other state logic remain unchanged. Replicated arithmetic could hurt area or
be synthesized back into equivalent structure; measured mapping is below.

| Metric | Combined base | Sample CSA | TX late cursor |
| --- | ---: | ---: | ---: |
| Local mapped cells | 26550 | 26415 | 26465 |
| Standard-cell area, µm² | 397041.4098 | 395532.9252 | 396655.4340 |
| Resettable flops | 2266 | 2266 | 2266 |
| Delta standard-cell area | — | −0.380% | −0.097% |
| Module equivalence points | — | 895 | 511 |
| Full pin suite | — | 60/60 | 60/60 |

Same whole-chip flattened Yosys/dfflibmap/ABC recipe, typical CMOS5L library
and unchanged blackboxed SRAM. These are local estimates, not native or
routed area, congestion or timing. Proof is module sequential equivalence
(equiv_simple plus induction, cap2), not whole-chip formal. Config staging
bytes remain identical to the previously phase-verified source.

## Reproduction and qualification

Use the project venv and append OSS CAD Suite bin to PATH:

```
python scripts/ci/verify_arithmetic_trial.py sample-csa /tmp/fresh-sample-trial
python scripts/ci/verify_arithmetic_trial.py tx-late-cursor /tmp/fresh-tx-trial
```

The helper prepares the frozen combined base, verifies its exact module hash,
applies one delta, checks every source file against the expected snapshot,
proves the changed module and writes an arithmetic_receipt.json. Delta patches
are sample_csa.patch/tx_late_cursor.patch; full frozen-source patches are
bs_resync_cfg_tx_cursor.patch for the physically eligible TX follow-up. Tests
verify that this full patch reverses cleanly from the independently prepared delta tree.
Negative controls reject unknown/wrong sources, extra edits and a missing
two's-complement carry bit.

Prepared a separate manual TX cursor native screen, with its own variant and
all three relevant module hashes bound. The source/config/SDC/resource policy,
wire150/hold125 repair, electrical utilization≤0.45, actual electrical/antenna
zero, fast hold≥50ps, measured slow capture≥3.5ns and watchdogs stay fixed.
No DRT until every gate passes. Full protocol replay must pass before launch;
its outcomes and launch receipts will be recorded when available.

Local evidence: /tmp/tripwire-sample-csa-20261020 and
/tmp/tripwire-tx-late-cursor-20261020. No extracted improvement claimed and no
Phase2 checklist boxes ticked. Lane-local slot staging remains deferred until
an updated path shows the residual slot broadcast limits closure.

## Local timing rejects CSA; prioritize TX

Matched isolated module mapping uses the same typical library/recipe; OpenSTA
then uses the slow library, ideal clocks/wires and zero external input delay.
The BS comparison constrains PERIOD inputs through RX-load output, with0.006pF
output load; the TX comparison covers all inputs through the16cursor D pins.
There are no extracted parasitics, physical clocks or realistic input arrival
times. This is prioritization evidence, not signoff timing.

| Local maximum data arrival | Base | Trial |
| --- | ---: | ---: |
| BS PERIOD→RX-load, CSA | 9.929828ns | 10.893814ns |
| BS PERIOD→RX-load, CSA plus parallel-prefix final adder | 9.929828ns | 10.713595ns |
| TX inputs→cursor D, late selection | 12.693307ns | 11.702561ns |

CSA and a further prefix-adder prototype both lose this comparison despite
passing895-point equivalence. **Do not launch a CSA physical screen**; its
prepared workflow was removed. The prefix prototype stays in/tmp, with raw
proof/map/STA evidence. CSA's complete expanded protocol replay nevertheless
passes22/22, no failures/skips, in360.88seconds; functional success does not
override worse timing evidence.

TX late selection improves this local metric by0.990746ns while reducing
mapped area. Its physical screen targets the two identified cursor reserve
cones; it does not directly rewrite the PERIOD-to-drop path or guarantee
the3.5ns setup reserve. Keep that gate fixed even if cursor reserve improves.
Raw timing evidence: /tmp/tripwire-sample-csa-local-timing-20261020,
/tmp/tripwire-sample-prefix-20261020/local-timing and
/tmp/tripwire-tx-cursor-local-timing-20261020.

TX replay now passes**22/22, no failures/skips**, in365.53seconds under
Verilator with independent decoders enabled. Five chip tests and2048L2model
comparison clocks also pass. The full pin suite passes60/60. Source-bound
verification_receipt.json and results_l3_tx_cursor.xml are retained in the
TX trial directory; XML SHA256:
72d85c8f1ee0ba51d6d1c8164c360a9f098ed86e0d3633036809941aea53f90f.
All local replay processes have completed. Focused helper/provenance/reserve
regression passes101tests; workflow YAML/bash/embedded-Python syntax checks
and git diff --check pass. Publication and native measurement are next under
the user's standing authorization; no positive routed timing claim follows.
