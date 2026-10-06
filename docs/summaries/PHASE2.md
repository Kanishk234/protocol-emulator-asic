# Phase 2: building and fitting the chip

**Status:** in progress, updated 2026-10-06. The measured R4 candidate has 2 lanes, 4 pin units and U0 full; these are experimental counts, not an adopted change to the frozen specification. See [phase checklist](../design/phases/PHASE2_RTL_CORE.md).

## The goal

Build the lanes, token fabric, timed pin units, host interface and routine memory, verify them against an independent software model, and fit a 6x4 layout that operates at the 20 ns clock target.

## What we did

The RTL exists and the candidate passed one million comparison clocks with no divergences; injection tests caught both deliberate bugs. UART, SPI and I2C work through the pins with reference-model and sigrok checks. The expanded protocol suite now has 22 cases. The latest actual routed netlist passed 22/22 under Tiny Tapeout Icarus 13 in [37417248117](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37417248117), with no failures, errors or skipped tests. This checks function, without SDF timing simulation.

A historical standard GDS run 36799356107 passed DRC/LVS/antenna/precheck and typical timing, but slow setup was −10.698 ns. Later repairs produced −6.178 ns and −5.630ns extracted slow setup. Timing-driven placement with all-corner repair then completed [routing 37412965189](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37412965189). Its [extraction 37417248079](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37417248079) reports slow setup −1.731802 ns and fast hold −0.035371 ns. This is substantial progress, but both still fail. Improvements compare complete physical flows, not one isolated cell change.

We tested six independent RTL/placement ideas. Timing-driven placement provided the strongest no-storage follow-up. Estimated setup/hold passed before routing, yet extraction revealed 119 slow setup violatio ns and 4 fast hold violatio ns. Most reported slow failing paths start at U0 period configuration and end in the token fabric. Three hold paths run from lane slot latches into execution controls; one runs from pin configuration into RX state. Live configuration remains timed; we have not added false paths or changed cycles to hide failures.

New paired experiments separately test clock-sink clustering, one lane-control buffer, one SRAM-enable buffer and a saturating dropped-token counter rewrite. The SRAM-buffer screen reduced slow slew violations 3→1 against a matched unchanged repair baseline; the lane buffer did not improve that count. Both have zero global-route overflow and estimated setup/hold pass, but no extracted improvement is established. The counter rewrite changes no storage, encoding or latency; module equivalence, fabric/chip tests and short model comparisons pass, with a fresh million-clock run underway.

## What we found

Routing estimates are useful for screening, but do not predict extracted signoff reliably enough to declare closure. The electrical reports matter too: the current extracted route has 101 slow slew violatio ns and 187 fanout violatio ns, plus capacitance violatio ns. Clock leaves and long weakly driven data nets need separate treatment. The candidate's standard cells plus SRAM occupy about 56.43% of core; filler-inclusive area must not be mistaken for logic utilization or guaranteed repair capacity.

## What's left

- Close actual all-corner setup/hold and electrical violations at 20 ns, using one isolated physical change per route.
- Complete full selected-candidate DRC/LVS/antenna/precheck/viewer evidence; split route/extraction diagnostics do not replace the standard GDS flow.
- Verify protocol scope and separately agree final resource counts/spec changes. Area/budget is the first unchecked phase-exit item.
- Keep required CI green on final main and repeat matching functional checks before any hardware adoption.

## One-line takeaway

The routed chip passes its 22 functional tests and slow timing has improved to−1.732  ns, but phase 2 remains open until physical timing, signoff and resource decisions are complete.

Detailed evidence: [independent screens](../reports/PHASE2_INDEPENDENT_TIMING_SCREENS.md), [parallel electrical audit](../reports/PHASE2_PLACEMENT_PARALLEL_AUDIT.md), [exit evidence audit](../reports/PHASE2_EXIT_EVIDENCE_AUDIT.md).
