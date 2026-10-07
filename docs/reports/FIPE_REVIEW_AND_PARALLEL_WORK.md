# FIPE review and work alongside timing closure

Reviewed 2026-10-07. FIPE snapshot: `916ed28b013315ac02fe763752d65c45dce17979`.
Sources: [README](https://github.com/jlsviper/fipe/blob/916ed28b013315ac02fe763752d65c45dce17979/README.md), [event queue](https://github.com/jlsviper/fipe/blob/916ed28b013315ac02fe763752d65c45dce17979/hw/event_queue.ml), [protocol rules](https://github.com/jlsviper/fipe/blob/916ed28b013315ac02fe763752d65c45dce17979/spec/protocol_spec.ml), [sweep tests](https://github.com/jlsviper/fipe/blob/916ed28b013315ac02fe763752d65c45dce17979/tests/test_sweep.ml).

## What the public evidence says

FIPE uses a single sequencer and a four-entry queue of committed pin events. The queue compares signed 24-bit due times, can fire two events per clock, and detects late events, ordering errors and an invalid time window. Skew is applied before enqueueing. Its protocol rules describe edge-to-edge minimum/maximum intervals and qualifiers; the same rules support checking and monitor compilation.

The README reports simulated I2C device-margin recovery in 29 transactions and an area of 221,520 um² / 13,445 cells after synthesis. These are their published results, not independently reproduced measurements. Their four monitor slots are a concrete capability; UART/SPI firmware and hardware timing-contract formal proof remain listed as future work in this snapshot.

[First GDS workflow 37554106388](https://github.com/jlsviper/fipe/actions/runs/37554106388): GDS, precheck and viewer jobs succeeded; the gate-level test job failed at its GL test step. This verifies that a layout exists, not complete functional/timing signoff. We did not inspect its all-corner WNS and cannot infer that from job status.

## Comparison limits and transferable ideas

| Topic | FIPE | TRIPWIRE implication |
|---|---|---|
| Timing architecture | Committed due-time queue separates event preparation from firing | Supports the general principle of moving arithmetic/control preparation before a late pin decision. Our RX prototype applies that principle without changing the contract. A queue replacement would be an architecture change, not a small timing repair. |
| Area | README synthesis area is about 24% of die | Compare matching synthesis stages, die/core denominators, resource counts and capabilities. Our approximately 510k–516k figures are later placement/repair instance-area totals. They are not an equivalent benchmark. |
| Evidence | Rule-based checker, monitors, boundary sweeps | Future protocol demonstrations should report edge intervals and failure boundaries, not only decoded bytes. Start with host-side/offline checks; avoid adding monitors to the timing-critical chip now. |
| Shared definitions | OCaml ISA fields/spec drive several components | Retain our single encoding source, but keep independent model/RTL behavior per AGENTS.md. Shared encodings do not remove the need for independent checking. |
| Device-margin discovery | Simulated EEPROM with hidden parameters | A good later demonstration concept. Any result on our side must remain labelled simulation until hardware exists. |

## Parallel work that fits current phase 2

1. **Critical-path audit — completed.** Original 125 ps extraction has two slow setup failures, both U3 RX timer bits 23/22. The shared-RX continuation targets this measured cone. Do not add unrelated blocks while waiting.
2. **Endpoint reporting — completed locally.** `scripts/ci/execution_margin.tcl` separates execution, configuration-latch and residual timer/counter/SRAM paths. Preserve full checks; pinned-engine execution is still needed before treating local endpoint margins as adoption evidence.
3. **Fallback drive/fanout review — prepared.** The shared selection cone has slow O21AI/XOR arcs; the pinned library lacks stronger variants for those cells. Stronger NOR2/NOR4 cells exist further down the path, but their increased input capacitance can hurt upstream delay. A selective fanout repair is a hypothesis requiring all-corner physical measurement.
4. **Official-flow portability — open.** The normal GDS workflow does not automatically reproduce our custom routing-region wrapper or checkpoint repair. Review a clean-build recipe and full candidate source/config integration before an official run; retain all official checks.
5. **Protocol timing coverage inventory — reviewed.** Existing 22-case L3 evidence includes required UART/SPI/I2C scenarios and several additional protocols. It is not exhaustive timing-rule coverage, simultaneous operation, or silicon evidence. I2C reference tests cover stretching, ACK/NACK and START/STOP behavior; systematically sweeping hidden device timing thresholds remains future work.

Rule-checker features, on-chip monitors, device-margin demonstrations, a Hardcaml rewrite and a new event queue are not started here. Current phase work remains setup/hold closure, area/routeability, independent verification and official-flow readiness.

## Immediate decision

Keep the shared-RX + 125 ps continuation running. Its extracted setup/hold, route checks and expanded GL results decide the next hardware move. FIPE supplies useful verification and scheduling ideas, but no evidence that switching architecture or adding fault-monitor hardware would solve our two remaining setup paths economically.
