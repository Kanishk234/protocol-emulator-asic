# Compact progress ledger and next decision

The compact successor is **not accepted**. Best fanout-clean routing remains133 overflow. Diagnostic setup fixes and green evidence-collection jobs are not improvements to the chip.

| Work | Actual evidence | Result and meaning |
|---|---|---|
| Frozen G1 fallback |36383587262 and36451108163 | Recorded Tiny Tapeout GDS/precheck/gl_test passes. D-023 fabric-model scope still applies; not a universal native-timing claim. |
| Stronger-driver compact layout |37708459393; official precheck37960021923 | Physical geometry/precheck progress, but33 fanout violations remain. Cannot combine this layout with another layout's electrical pass. |
| Fanout-clean fixed-original placement |38101405271 | Ten buffers remove the checked electrical violations; native global route remains146 overflow. |
| Combined reset placement |38168159774 |146→133 overflow at unchanged policy. This remains the best measured fanout-clean control, but is not routing closure. |
| Individual buffer moves, net ordering, mirroring |38178351037,38274085899,38279250531,38281724422 | Worse than133; rejected. Do not repeat those configurations. |
| CUGR engine |38292828402 | Complete guides but nonzero weighted grid overflow; rejected by observer. Its metric is not directly comparable to FastRoute counts. |
| Every delay cell queried |38315257114 |590 constrained min/max queries at each original PVT corner. Better diagnosis, not a physical improvement. |
| Smaller high-slack delays |38316322592 and38316844576 | Placement and estimated shell timing pass; footprint shrinks455.4144µm². Native routing worsens133→145; reject for routing. |
| Congestion-driven redistribution |38317781400 | Optimization completed, exporter setup failed before STA. No accepted placement/timing/routing result; Corrected38318370803 passes physical interface/power-phase checks but loses the0.1ns fast hold guard (actual0.05714ns); reject before routing. |
| Baseline UART fault/event functionality |38279446388 | Actual loaded full-duplex RX/TX/fault/recovery tests pass for both counter widths under D-023 RTL scope. |
| Portable C loader/channel |38293580979 | Compiled C loading/recovery and31-byte duplex pass through actual simulated SPI. No board/backend speed claim. |

## Why progress has been slow

Electrical repair changes routing demand and pin access, so a geometrically clean older build is not a substitute for the fanout-clean build. Standard-cell footprint and wirelength proxies have not predicted actual overflow reliably. Placement and shell timing pass before routing can still regress. Experiment adapter mistakes also consumed cloud cycles; BUG79–83 document those distinct setup failures. Full macro-native functionality and complete matched-chip RUN/LOAD/boundary timing remain separate from shell routing.

The recent small producers take minutes, including cloud provisioning. Historic detailed-routing/geometry jobs take tens of minutes to hours (recorded in PHYSICAL_DESIGN_AND_CI.md). Repeatedly entering those long jobs without a better routing control would compound the delay.

## Bounded next decision

1. The corrected producer failed its hold guard; stop post-CTS redistribution. Future placement producers must require actual immutable masters/connectivity/macro/boundary pins/die/rows, legal row power phase, and the original three-corner shell electrical/timing guards. An exporter failure is a setup problem; a real guard failure rejects the placement.
2. Only a passing producer gets a paired global-route comparison against133. Retain identical capacity policy, clock margins and native zero-overflow acceptance. If it does not improve133, reject that placement rather than proceed to hours of detailed routing.
3. Broad post-CTS redistribution failed the retained hold guard in38318370803. D092 now compares the original placement with congestion-driven placement **before CTS/hold repair**, then rebuilds both clock trees/repairs using the same cluster8 policy and original clock/constraints. Actual38319615838 restores reflow fast hold to0.100232ns with positive setup/hold and zero slew/cap at all3 corners. Both cases retain5 known fanout violations; no accepted producer or route. D093 now restores the established ten-buffer fanout fix with all existing positions locked, then rechecks original timing guards. Source snapshot export passed before the experiment; all corner violations remain explicit and block promotion.
4. Maintain the passing baseline and independently useful compiler/host/protocol work. Do not promote a compact successor or advertise native chip timing until all required checks pass on one matched build.

This ledger distinguishes actual chip progress, functional improvements, improved diagnosis and experiment setup. No phase exit box is ticked by this document.

Actual before-CTS comparison result SHA256: `f8db35215e1070f84fdda2450748e3d9b0e5b215bcba73e30c9b2eb461c942bd`. Control reproduces the previously measured pre-buffer ODB/netlist exactly. Reflow's additional49instances and restored timing margin are diagnosis/provenance results; routing benefit remains unmeasured.
