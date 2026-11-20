# R1 closure status — November 20, 2026

R1 is still experimental. G1 remains the selected production baseline.
No hardware, ABI, physical macro geometry or clock target changed in this work.

## What is actually established

| Gate | Latest relevant evidence | Result and scope |
|---|---|---|
| Declared macro-interface LVS | 44627346549 | All 449 root ports and devices match uniquely against independently source-proven SPICE. Enclosing chip/power integration is separate. |
| Connected extracted RC | 44621669039 | Original geometry matches on all 21 layers; all named terminals have correct resistor connectivity. |
| Moved image with three proved selector repairs | 44794158025 | Original/reroute controls, native UART/SPI/reset and full management error/CRC, USER_RESET, STOP/reload pass. All four actual 8736-bit audits pass; direct/reload states match. |
| Configured timing model for that image | 44794158025 | All 370 edge registers classified, 244 endpoints, 12675 active pins fully annotated, zero loops under both policies, identical slacks. |
| Timing closure | 44794158025 | **Fails:** setup −9.795382 ns, hold −1.867277 ns at the unchanged 20 ns period and 0.25 ns uncertainty. Nominal RC with slow/fast cells and the original conditional zero-I/O-delay macro boundary. |
| Additional upstream selector | 44794158025 | Passes native/reload and timing qualification; setup improves 0.397685 ns, hold unchanged. Still negative. |

A successful diagnostic workflow does not mean timing closed. Check
`model_qualified` and `necessary_macro_constraints_met` separately.
The qualified negative result is in
[r1_upstream_cleanup_44794158025.json](r1_upstream_cleanup_44794158025.json).

## What changed and why

The original fixed-placement reroute passes direct native traffic, but fails
shell traffic. A targeted combinational LC move also initially stalls native
simulation. The read-only VPI observer localizes the latter to an unused LUT
input feeding from its own output. Actual truth-table and routing proofs
justify two existing selector changes: X3Y3/D.I0 breaks the observed native
stall; X6Y3/E.I0 removes the remaining timing loop using an existing registered
source. Neither adds a register or changes the intended LUT function.

The first two repairs are two bit changes relative to the moved, rerouted compiler image;
they are not the total change relative to the original compiler placement.
After the additional D158 selector change, the current loaded image is
`33b768f80464046a1d718c0968a627537fd92d7815c45c9161064b69e26f64b6`.

The subsequent measured setup target was unused X2Y3/D.I1. Its loaded INIT is 0xaa00,
independent of I1, but its default input route traverses a long chain. D158
changes only upstream routing selector bit 183 (word 273 bit 23), redirecting
that input to an existing registered H output. Complete selected fanout has
three nodes and ends only at the unused input. Cofactor, carry, active-feature,
native selector/register identity and expected frame checks pass locally.
Run 44794158025 passes actual function/reload and timing qualification for this
change; setup improves modestly and hold remains negative.

The new worst path maps from SPI state[1] through hard-timer enable/terminal
count to nedge[1]. D159 tests a build-only free-running-timer user-program
variant with full binary output equivalence and existing independent SPI
tests across four modes and HALF values 4 and 25. No compile/native/timing
result is claimed for that experiment yet.

## Failures kept as controls

- 44678070512: moved image stalls during direct traffic; all 8736 observed bits match.
- 44784239092: routing-only image passes direct tests but stalls during shell traffic.
- 44785764117: instrumented original passes; observer stops the moved image at tick 116000000. Partial diagnostic output remains a failed job.
- 44787771176: candidate STA aborts on stale parent Q assertions (BUG165). Corrected complete gate/state checks reject stale, missing, duplicate and wrong-latch guards.
- 44790210039: corrected STA completes with active coverage, but rejects one remaining structural loop.

## What still blocks acceptance

First establish passing setup and hold with the same real image and constraints.
The current worst setup path launches and captures inside the macro; an external
boundary adjustment cannot dispose of it. The worst hold path starts at the
macro MISO input under the conditional zero-delay boundary. It needs a valid
physical enclosing-shell timing model or a demonstrated implementation repair;
no path is waived.

Enclosing physical power, complete shell/chip integration, loading-mode timing
and complete corner qualification remain open. The missing regular-grid VGND
stripe was only calibrated in a synthetic overlap probe, not repaired and
qualified in an actual full-chip PDN. Do not promote an image or tick a phase
exit box based on the functional/diagnostic passes above.
