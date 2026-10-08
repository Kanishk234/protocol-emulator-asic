# Native stock clean-build qualification and next experiments

2026-10-08. Run37853023857, helper revision a53dd57b44438d2a10f3363e1418d489a175397e; frozen full2/4 event-late hardware. Both jobs completed successfully. This is GRT/STA screen evidence, not extraction or official signoff.

| Measurement | AREA0 | AREA1 |
|---|---:|---:|
|Setup WS, every corner ns|0|0|
|Fast hold ns|+0.074614|+0.119326|
|Typical hold ns|+0.217490|+0.226062|
|Slow hold ns|+0.421121|+0.401382|
|Post-repair cell area including SRAM µm²|524994.94|524688.31|
|Cell count|34149|33898|
|Final GRT usage|40.21%|39.76%|
|Final GRT overflow|0|0|
|Slow slew violation count|3|21|
|Fast slew violation count|0|1|
|Typical slew violation count|1|1|
|Capacitance violations per corner|1|1|

Evidence: downloaded exact artifacts11584441701 AREA0 and11584249022 AREA1; fresh timing/comparison.json and flow/43-openroad-resizertimingpostgrt/openroad-resizertimingpostgrt.log. The last congestion report has zero overflow on all required routing layers. AREA1 area is only0.0584% lower after all repair; previous first-GRT area savings are not the final result. AREA1 has stronger fast-hold margin but worse electrical slew counts, so it is an exploratory routing choice rather than an adopted official recipe.

## Exact AREA1 electrical failures

Fresh slow checks.rpt: SRAM A_REN slew0.996394ns vs0.595200ns limit;20 other violating pins share approximately2.556ns slew vs2.507400ns limit, including driver28820/Y, its consumers and antenna diodes. SRAM A_DOUT[0] has0.070544pF capacitance vs0.064000pF limit. No limits are relaxed or waived. These require investigation before claiming official electrical closure. Native resolved.json shows RUN_POST_GRT_DESIGN_REPAIR=false.

## Prepared independent follow-ups

1. native_stock_route.py plus gds-native-stock-route.yaml binds to exact successful main run37853023857/head a53dd57/AREA1. Trusted pre-download source/macro/SDC fingerprints and full generated config equality protect provenance. Fresh CheckAntennas and all-corner STA must pass, including50ps fast hold, before stock DetailedRouting. No cell ECO or repeated timing repair. Completed zero-DRC route is then passed to existing RCX/all-corner extraction helper. This diagnoses whether clean-build timing survives actual routing. It does not waive the electrical violations or claim official closure. Routed protocol tests follow once exact final netlist exists.
2. gds-native-design-repair-screen.yaml builds AREA1 from scratch with stock RUN_POST_GRT_DESIGN_REPAIR=true before antenna and timing repair. This is the only additional physical option; hardware/shape/20ns/56%/all-corner repair/125ps hold stay fixed. It tests native repair_design for the observed SRAM/load electrical failures. Stock step is experimental and may take longer. No named-cell overrides or custom image. Compare fresh electrical counts, timing, area and final overflow before any promotion.

37 relevant helper checks pass, including complete orchestration, provenance/config/hardware rejection, nonfinite and insufficient margins, missing antenna evidence, no repeated repair, and explicit one-option design-repair selection. Both workflow static audits and diff checks pass. No newly prepared workflow has been published or launched yet. Raw logs and downloaded reports stay in/tmp.

## Native route antenna failure and correction

Run37858532319 passes hardware/config provenance and reproduces native timing, but fresh antenna check has15nets/17pins; DRT is correctly refused. Initial stock antenna repair ended at0 violations, then post-GRT timing repair changed routing. Prepared continuation now conditionally runs stock RepairAntennas with GRT_ALLOW_CONGESTION=false and verifies resolved policy plus absence of -allow_congestion in the actual repair command. No subsequent full GRT discards repaired guides (BUG79). Fresh antenna/STA use the cleaned state before DRT.51 related checks pass, including remaining-antennas, bad-policy and bad-timing rejection. Correction is not a physical pass until rerun.
