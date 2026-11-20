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
tests across four modes and HALF values 4 and 25. 44797232291 passes all eight unbounded equivalence cases and 32 source tests,
with independently reviewed statuses, parameters and project Python runtime.
Fresh compilation 44798802734 reproduces the original control image exactly.
The candidate fits at 102/128 logic cells versus 103 for the control, with
identical pins/parameters/seed. Its compiler timing estimate is uncharacterized
and worse; no performance improvement is claimed. 44799827748 passes actual native/reset/reload and all three frame audits, but
STA reports four constant-rail feedback loops and exits nonzero. There is no
qualified timing result for this variant yet. D161 tests one proved unused
G.I0 selector at X4Y1, feeding an existing registered source, before repeating
native/reset/reload and connected timing. Production RTL is unchanged.

## Latest SPI source measurement and clock-bank follow-up

44802619585 passes the one-bit rail repair, actual native/reset/reload,
all three 8736-bit audits and zero-loop fully annotated timing. Its measured
setup is **−21.419043 ns**, hold **−2.660251 ns**, so it is worse and unadopted.
The better measured prior image remains the −9.795382/−1.867277 ns result above.
See [rail result](r1_spi_timer_rail_44802619585.json).

The fresh placement allocates GBUF X0Y4/A, and all 370 edge registers are
clocked. The earlier bank-D result has 134 inactive registers. The new worst
setup endpoint is a register at X1Y1/D with FF output select 0 and no placed
user cell. D162 tests clock-bank allocation as a confounder: reproduce the
same SPI source/control image, then constrain only the GBUF to X0Y4/D.
44827334401 reproduces the A-bank image exactly and routes the D-bank
candidate with identical packed logical graph and resource use. Raw D-bank
image: `4326eab8868442494239e0a413aa199158293b14cff856453ae8c37bd6d7403a`.
Actual configuration loading/reset/reload and full timing are next; no
unused-register path is waived.

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
