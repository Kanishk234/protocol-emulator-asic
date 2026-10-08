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

Published61ac267 and launched [37806209914](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37806209914) with antenna repair enabled. It succeeded in about9.5 minutes. Artifact11563058526 contains matched gates and fresh timing: setup WS0 in all corners, zero setup/hold violation counts, hold fast+0.109256ns/slow+0.371234ns/typical+0.202929ns, antennas0 nets/0 pins. Fast hold improves from+0.033514ns and passes the50ps continuation gate. These remain estimated global-route results; extracted timing and official signoff are outstanding.

Prepared local DRT continuation for this exact successful source. It validates every inherited netlist transition: original diode materialization, first NOR2 sizing, dropped-event NOR2 sizing, nine leaf buffers, and subsequent diode-only changes. It also requires source fingerprints, zero-overflow/strict antenna evidence, fresh views without stale extracted parasitics and fresh all-corner STA with at least50ps fast hold. The ordinary routing image resumes the checkpoint without repeating repairs. Workflow downloads the exact hold artifact and preserves the full evidence chain for downstream extraction and routed GL.311 related tests pass;8 Tcl wrapper tests skip because system tclsh is unavailable. Guard tests use the cached STA Tcl runtime and mocked OpenDB operations; tests do not establish physical closure.

Next: publish the prepared continuation, run DRT from37806209914, then inspect final DRC, extracted all-corner timing and routed protocol GL. User explicitly approved publishing and launching the prepared continuation after reviewing the successful screen; record its run receipt separately. No Phase2 boxes ticked.

Approved continuation published on89d7537 and launched [37807978035](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37807978035); queued at receipt. Exact original source37533969613/bs-event-late and repaired source37806209914; no repeated repair. Await actual DRT, extracted timing and routed GL results.
