# Native clean-build extraction and electrical cleanup results

2026-10-08 local date; both jobs completed2026-10-09 UTC. No official closure or candidate promotion.

## Exact outcomes

Native AREA1 continuation37859526262 completed in40min, including conditional congestion-disallowed antenna cleanup, fresh timing, detailed routing and extraction. Extraction ran to completion; workflow success is not timing closure.

| Corner | Extracted setup WS ns | Extracted hold WS ns |
|---|---:|---:|
|Slow|-1.423654123774|+0.370721019931|
|Typical|0|+0.196308974632|
|Fast|0|+0.094072363673|

Actual artifact11587186953, runs/extracted-timing/corner_summary.json. Slow extracted electrical report has133 slew violations and6 capacitance violations. SRAM A_DOUT[0]0.128690pF vs0.064000pF limit; other output bits and driver28820 also violate capacitance. Therefore this clean-build route is not eligible for official promotion despite successful routing and positive hold.

Worst setup path begins48179, unit0 live configuration word0 bit4 latch, and ends47345. It passes through hold12888 (0.611ns slow delay), pin pad selection/feedback, and downstream logic. Loaded place7221 has0.169663pF,0.899162ns arc and1.072083ns slew; following24875 O21AI has1.159493ns arc, then24876 INV0.720835ns. Other logic stages contribute materially. These are actual extracted path observations, not proof that one resize alone will recover1.424ns. D-066 live configuration remains fully timed.

## Stock electrical design repair

Fresh AREA1 screen37858535440 completed in57min with RUN_POST_GRT_DESIGN_REPAIR=true. SetupWS0 every corner; hold fast+0.104755ns/typ+0.233848ns/slow+0.431466ns. GRT remains zero overflow with39.76% usage. Cell area524416.15µm² inclSRAM,33886cells.

Capacitance violations become0 at all three screen corners. Slew remains fast1/typ1/slow18 (prior AREA1 fast1/typ1/slow21). Slow SRAM A_REN0.984095ns vs0.595200ns; A_ADDR[6]0.667443ns vs0.595200ns. Other loaded-cone slew now approximately2.631ns vs2.5074ns. This is partial electrical improvement; detailed-route/extracted results for this new recipe do not exist and must not be inferred from the older native route.

Evidence artifact11587476694, fresh timing/comparison.json, slow checks.rpt and final post-GRT repair log. Raw evidence remains/tmp/tripwire-completed-route and/tmp/tripwire-completed-cleanup.

## Decision

Keep the earlier residual checkpoint37844735445 as the best measured candidate: extracted setup0 all corners, minimum hold+0.062788609ns, GL22/22, and tested19.85ns period reserve. The native recipe is a reproducibility experiment, not a replacement for it. Clean native routing exposes configuration/pin-feedback loading and late electrical failures; further clean-build corrections must be measured with actual extracted constraints/parasitics. Avoid launching official GDS from this failing native recipe. No current main workflow is running at result receipt.
