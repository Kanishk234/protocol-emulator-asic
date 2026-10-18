# Native clean route: physical checks pass, extracted timing does not

Route [39149073496](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39149073496), head `5867ea0688b4443a44f7e2d5851245cdfe0f33dc`, completes detailed routing and extraction but fails its strict extracted gate. Source screen [39141162581](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39141162581) passed every estimated gate. Keep the earlier passing extracted checkpoint 38784492656 as a separate baseline; it is not clean-build reproduction.

| Check | Screen | Extracted route |
| --- | --- | --- |
| Slow setup worst slack | 0 ns | −4.218641555 ns |
| Fast hold worst slack | +0.0819512 ns | +0.042531646 ns |
| Typical hold worst slack | +0.188140 ns | +0.131662907 ns |
| Slow hold worst slack | +0.364049 ns | +0.281998433 ns |
| Electrical violations, each corner | 0 slew / 0 fanout / 0 capacitance | 0 / 0 / 0 |
| Antenna violations | 0 nets / 0 pins | 0 / 0 |
| Detailed-route DRC | Not run | 0 after iteration 8 |

Setup is nonnegative at fast and typical corners. Fast hold is positive but misses the unchanged 50 ps acceptance gate by about 7.47 ps. Route instance area is 592372.68 µm² on a 902417 µm² core (65.64%, including SRAM). This is not Magic DRC, LVS, precheck or official GDS evidence.

The preserved effective signoff SDC hash is `63a9ac8dc9d00741c26ea37cf8ee01345c2ebf178e1c408dd213619e080d0ffa`, identical to the intended fully timed constraints. The failure is not a changed SDC.

## Critical paths and limits of the inference

Worst slow setup starts at configuration latch `_48225_`, unit 0 configuration word 0 bit 0, and ends at `_47215_`, mapped by the routed NL to `u_chip.dropped[14]`. The latch-to-counter path traverses pin-unit and fabric logic. Data arrival is 25.567234 ns against required 21.348593 ns. Its data section includes 49 buffer output arcs totaling about 10.790404 ns out of 19.025774 ns total cell delay. These are measured path delays, not a claim that deleting buffers preserves electrical constraints or recovers that entire delay.

Worst fast hold starts at configuration latch `_47933_` (unit 1 configuration word 5 bit 15), ending at `_46696_`, `u_chip.g_unit[1].u_unit.u_tx.er[7]`.

The estimated top-1000 slow setup paths are dominated by latch endpoints; the actual routed critical latch-to-flop pair is absent from that report. Zero global setup WS therefore does not show useful positive setup reserve or enumerate every potentially critical path. Add read-only FF-capture setup/hold reports alongside all original gates. OpenSTA supports selecting these pins with `all_registers -edge_triggered -data_pins`; use the pinned LibreLane corner-report fields and explicit current corner. [OpenSTA command source](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/sdc/Sdc.tcl).

## Bounded next test

Prepare `gds-native-wire150-hold125-screen`: change the native wire-length repair limit from 100 to 150 µm and hold repair target from 100 to 125 ps, retaining clean synthesis, CTS100/clock8, electrical55, antenna50 and the final native antenna pass. This tests whether reducing buffer-chain cost improves setup headroom while extra hold target compensates the measured erosion. It is a coupled policy trial, not attribution to one setting or guaranteed timing improvement.

All 20 ns signoff, 50 ps final fast-hold, zero electrical/antenna/overflow and 0.45 estimated electrical reserve gates remain fixed. No DRT until the new screen passes all gates. If electrical reserve fails, inspect offenders rather than waive the guard. If setup headroom remains inadequate, prioritize general carry/telemetry and configuration fanout paths using the measured capture reports; no RTL/ISA/latency change is authorized by this test.

Protocol replay for route39149073496 remains blocked because the route does not qualify. No Phase 2 boxes ticked.
