# Placement candidate: electrical, path and resource audit

Evidence: artifact `gds-placement-multicorner-timing-placement-37408506116`, frozen 3393eea, local download `/tmp/placement-multicorner-37408506116`. Sources are repair netlist/DEF/metrics and fresh slow `checks.rpt`/`max.rpt`. Results precede antenna repair and detailed routing. No hardware or constraints changed by this audit.

## Electrical violations

All 162 fanout violations are clock-tree leaf BUF8 outputs for `clk_regs`. Report limit 8; actual loads 10–17. No data-net fanout violation appears in this report. This is a clock-tree sizing/clustering question, not evidence that the fabric needs architectural fanout reduction. CTS sink clustering is enabled but its size and diameter are null in saved CTS config. A separate experiment could bound sink clusters to 8; verify actual resulting leaf fanout, clock skew/latency, area, all-corner hold/setup and route overflow. Clustering size alone does not guarantee every post-resizer leaf meets the limit. Do not relax max-fanout constraints to erase the report.

Eight slow slew violations resolve to two nets, with zero capacitance violations:

| Driver | Net | Reported slew / limit (ns) | Loads | Logical role | Driver-to-load Manhattan distances |
|---|---|---|---:|---|---|
| `_33713_/Y`, NOR4_1 | `_07896_` | 2.730727 / 2.507400 | 5 | Lane 0 slot write/control decode; upstream inputs include slot waddr[4:3] and lane run | 443.46–460.62 µm |
| `_30323_/Y`, NOR4_1 | `_04725_` | 2.726310 / 2.507400 | 1 | SRAM enable arbitration, feeding `_30324_/A2`; its output is u_sram.men | 515.82 µm |

The remaining six reported violations are the receivers on these same nets, not six further root drivers. Slow receiver slew reaches 2.731817 ns. These distances are cell-origin Manhattan estimates from DEF, not measured routed wire lengths. `_33713_` sits at (293.76,287.28), its loads around (576.96–603.84,124.74–139.86); `_30323_` at (856.80,192.78), `_30324_` at (352.32,204.12).

Evidence supports testing one driver-side buffer/load split on one net per physical experiment, or improving local placement of the weak NOR4 driver. Preserve the same combinational function and sampling cycle. Do not assume a stronger NOR4 variant exists without checking the pinned library, or assume buffering improves setup without routed evidence. Wait for current antenna/extracted reports before choosing a net: its slew/load may change during routing.

## Critical paths

Old extracted failing logical path U0 mode configuration word0 bit0 → dropped[26] still maps to `_49139_` → `_48163_` in this candidate. Their current cell-origin distance is 597.84 µm. The older route reported a 724.8 µm critical intermediate branch; these measure different objects and must not be called a direct wire-length improvement.

Current worst listed slow path `_48984_` → `_49160_` is U0 configuration word13 bit11 → carrier_active latch. Origins (816.00,627.48) → (794.88,623.70), Manhattan 24.90 µm. The following listed paths start at flop `_46758_` and end at configuration latches, also reported at zero slack. All three corner setup/hold violation counts are zero, but zero setup slack supplies no positive margin. A changed top report is not proof the old routed failure disappeared; the report has a bounded path list, and extracted STA is pending. D-066 live configuration stays timed, with no new false paths or added cycles.

## Area and resource budget

Core area 902,417 µm²; total instance area 508,444 µm² (56.3425%). Standard-cell area 463,135 µm² (51.3216% of core), SRAM macro 45,309.3 µm². There are 33,169 instances, including 154 clock gates, 4,273 sequential cells, 1,001 clock buffers and 3,186 timing-repair buffers. The last repair adds 39 hold buffers. The gross difference to 60% core utilization is 33,006.2 µm²; this is not guaranteed routing/ECO capacity. Distinguish total-cell utilization from standard-cell-only utilization when comparing reports.

This measured candidate lies within the original rough 50–60% routability range, with zero logged global-route overflow and real DRT still pending. The fully frozen architecture estimate remains 109–120% of core; reduced 2-lane/4-unit/U0-full counts are still an experimental protocol-floor candidate, not final adopted resource counts. No area phase gate is ticked. Cached-input's 192 extra latch bits remain deferred, especially given its measured nonzero overflow (37); stateless input-decode also had overflow 5.

## Next controlled experiments

1. Complete the active placement route and automatic extraction/L3. Use actual routed critical paths and electrical reports to prioritize the following experiments.
2. If the same data slew violations survive, compare one driver-side buffer/load split for one of the two nets, with unchanged hardware semantics and constraints.
3. Separately compare CTS sink clustering size 8 against the present default. Record clock-leaf load distribution, skew, hold-repair growth and overflow, not cell count alone.
4. Keep final resource adoption and full DRC/LVS/precheck/signoff open. These experiments provide evidence; they do not authorize spec changes.
