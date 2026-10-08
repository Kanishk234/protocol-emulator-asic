# Dropped-event setup screen: measured hold leaves and bounded repair

Successful screen [37803300460](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37803300460) reports no setup/hold violations in three corners and0 antenna nets/pins. Setup WS0; hold fast+0.033514ns, slow+0.352956ns, typical+0.159913ns. This is estimated global routing, not extracted closure. Fast hold falls below our existing50ps continuation gate, so do not launch DRT from this source without margin repair.

Read artifact11563320092 using byte ranges to inspect actual current reports/netlists. Of1000 printed fast-hold paths,9 distinct endpoints are below50ps. Worst: slot latch50092→lane0.ex_imm[3] register46568. Prior lane0.state[2] leaf is no longer the minimum; its local prototype is deliberately unlaunched.

| Destination | Fast hold(ns) |
|---|---:|
| lane0.ex_imm[3] | +0.033514 |
| lane0.acc_addr[4] | +0.034862 |
| lane0.ex_imm[0] | +0.035133 |
| pin2.TX.er[1] | +0.036837 |
| pin2.RX.sst[2] | +0.038110 |
| lane0.acc_addr[3] | +0.040953 |
| pin2.TX.er[0] | +0.042327 |
| pin2.RX.rt[4] | +0.043165 |
| lane0.acc_addr[0] | +0.044174 |

All9 audited D nets have exactly one driver and one destination. Prepared drop_leaf_hold.tcl inserts9 noninverting BUF1 cells, initially2µm left of their sinks and requiring legalization. Added library area65.3184µm²; final total area/routing impact must be measured. All9 nets, driver/sink masters, buffer pin compatibility, supplies, and duplicate objects are checked before any mutation. Only D pins reconnect; clocks/resets remain untouched. The netlist guard requires exactly9 added BUF1 cells and9 destination-D net changes, with every other logical cell/connection preserved. Actual checkpoint netlist rehearsal passes.

Manual gds-drop-leaf-hold-screen freezes37803300460 and original full2/4 source37533969613/bs-event-late. It uses the same20ns fully timed constraints, reservation and pinned tools. Fresh source export must match inherited NL; repaired NL/PNL are mandatory; inherited SPEF/SDF/lib are cleared. Global routing must have zero overflow; antenna repair disallows congestion and is followed by independent checks, diode-only logical guards and fresh all-corner STA. Eligibility requires all timing/antenna gates and at least50ps fast hold, printed explicitly in gates.json. No timing resizer, repeated NOR2 sizing, inverter sizing, DRT or official hardening is added.

289 related helper tests pass, including failure on the last audited leaf before any insertion, exact9-buffer/9-net changes, clock/reset preservation and source/workflow wiring. OpenDB operations are mocked; no physical margin gain is claimed before CI measures it. Original event-late extracted-0.179789ns remains the stronger baseline; the prior NOR2-routed extraction-0.422085ns is rejected for promotion. No Phase2 ticks.
