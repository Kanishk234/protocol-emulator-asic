# Recovered compact layout: physical checks pass, electrical/function gates remain

[Run37674839060](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37674839060)
completed successfully in22m14s (19:29:12–19:51:26UTC). Downloaded result,
Magic report, extraction/Netgen reports and fresh STA metrics were inspected.
This is a scratch checkpoint replay, not clean-source reproduction or promotion.

The source is the actual post-check native0 ODB from37669731197, SHA256
9cac79d86dd15707efdd385c32d3990347cb4695874bc802d0bfe20a5e90e9ba.
Fresh extraction/streamout uses no decaps; the D-052 measured filler pSD overlay
is applied with non-pSD equality and instance-count checks. Full Magic and
KLayout then report0, and actual GDS-based stock shell LVS reports0.
Final overlaid GDS SHA256:
7475586c234ce15f0d51b47a9882990b58a703e9c4f387083bd3f09aa4cf7a7a.
Stock macro abstraction remains; LVS does not qualify regenerated tile netlists.

| Shell STA corner | Setup worst slack (ns) | Hold worst slack (ns) | Slew violations | Fanout violations |
|---|---:|---:|---:|---:|
| Fast1.32V/-40C |14.292012|0.124635|0|33|
| Slow1.08V/125C |12.251012|0.648149|9|33|
| Typical1.20V/25C |13.518294|0.312306|0|33|

Clock target remains20ns/50MHz. Setup/hold violation counts and capacitance
violation counts are0 at all supplied corners. The nine slow-corner slew
violations and33 fanout violations remain real electrical limits, so this
is not a full timing pass. Macro-black-box shell STA does not prove configured
fabric timing or workload rates.

The older3-marker overlay follow-up37673567925 correctly failed: KLayout0,
LVS16, with top-level power-pin matching failure in the retained Netgen report.
Its exact LVS cause is not isolated here. The new recovered-route result passes
LVS without changing comparison rules; no older result is rewritten as green.
Global contained-via screen37673914480 was separately rejected for inaccessible
NAND4 inputs (D-054), and is not used by this passing route.

Next, refresh D-049's stronger frame-index driver diagnostic on these exact
fresh parasitics. An earlier old-wire diagnostic cleared nine slew errors,
but a resized driver still needs legal placement, routed physical checks and
new extraction. Separately, original compact tile mappings retain BUG33 native
simulation failures while regenerated mappings pass loaded UART; their physical
views must be hardened and matched before successor acceptance. Configured
timing, official precheck, clean reproduction and required CI remain gates.
Frozen G1 remains the fallback; its latest template gds37659595229 succeeds.
