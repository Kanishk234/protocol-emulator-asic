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

## Fanout-clean earlier-stage candidate

[38320631258](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38320631258) passes native ten-buffer placement, exact immutability of all3645original instances, contracted signal connectivity and physical interface/power phase checks. All3 original-corner setup/hold/electrical checks pass; fast hold remains0.100232ns. Result SHA256: `df6f07c502518e2d9a1ec95facd43de5f5d060df11206dab6f59d484da33271b`. This is a newly qualified placement/electrical candidate, not routing closure or full native timing acceptance.

Candidate ODB: `90940c876925b362f0589d6e3052d37527d3fdae75b71388848b717d0d82bb17`; netlist: `d53fd05fb028b4589f7b855daaed84415cc4425fe2b88c840938e002a3d5d35f`. Prepared unchanged-policy GRT comparison with best133control. Adapter checks pass against actual downloaded artifacts.

## Actual earlier-stage routing outcome: reject reflow

[38321208948](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38321208948) completes the comparison: original133 versus reflow6544overflow, both native returncode1. Result SHA256: `e6eeb39ec5ee5a6f3fe7fcc517aa83f417c1de778b7b4c4dd8903aeb201ef65a`. Producer qualification was real, but did not improve routing. Retain133 control.

Native geometry moves cells toward the thin north corridor:76→443CORE cells; west3231→2892, east7→7. This is distribution evidence, not causal attribution. D094 changes only the placement estimator to native FastRoute feedback, retaining density55 and original clock/repair/layer/capacity policies. Runtime-copied GPL source is pinned/licensed and actual command execution is required. Final zero-overflow, electrical/timing and full physical gates remain unchanged.

### October13: native placement feedback result
Run38339209412 completes; resultSHA c22a7e67b1e41e900a388e37c18cfb4ab664f05bac5b860e8f56b7fea03d3b96. Candidate3670instances; fixed macro/interface and actual ROW phase checked. Three corners show zero setup/hold/slew/cap violations, five configuration fanout violations each. Fast estimated hold0.101014ns exceeds0.1guard; not extracted/full-chip timing signoff. Candidate ODB7ac798a5…/NLeb7d5e87… authenticated. Next: same ten identity buffers with every original instance fixed, then repeat all guards and only then routing against133 control. Collector green is not physical acceptance.

### October13: native feedback fanout repair qualifies
38452773248 producerSUCCESS in2m10s hosted job; resultSHA b804c57b3de1a1096535686d2adcdfcbb8904766218891fdfa32d826c278b946. Ten identity buffers,3670 originals unchanged,18369 original terminals checked with exact contracted connectivity. All three PVT electrical/setup/hold guards pass; fast hold0.101014ns retained. ODB71cb27c8…/NL68b84c66… authenticated. Prepared unchanged-policy paired GRT against133 control; actual routing still pending. No compact signoff claim.
