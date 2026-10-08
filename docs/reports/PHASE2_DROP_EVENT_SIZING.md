# Dropped-event residual: extracted analysis and bounded sizing

Route37737970080 passes final DRT/antenna checks; extracted diagnostic37743628998 reports slow setup-0.4220854896178046ns and fast hold+0.03587147347360706ns. RoutedGL37743629089 passes22/22. The9 printed negative slow paths end at dropped-event counters:8 share source configuration latch48909 and lane1 event path; the ninth ends at dropped[67] from latch48892. The former RX-timer bottleneck is no longer the worst printed violation.

The worst path contains NOR2_1 instance31567 driving8 loads/0.208821pF with2.300487ns cell delay and2.661975ns slew. Its exact pins are A=_05964_,B=_05968_,Y=_05970_. Strength2 exists in the pinned library. The separate67-counter path contains inverter38387 with1.230150ns delay; pins A=_12192_,Y=_12193_.

Local OpenSTA reproduces baseline setup/hold in all corners within1e-6ns using the exact final NL, extracted nominal SPEF and fully timed source SDC. Isolated evidence and SHA256 manifest: `/tmp/nor2-extracted-local-20261008/comparison.json`. No independent model implementation was read or changed.

| Fixed-wire probe | Slow setup WS(ns) | Fast hold WS(ns) | Added library cell area(µm²) |
|---|---:|---:|---:|
| Actual extracted baseline | -0.422085494 | +0.035871472 | 0 |
| NOR2_1→2 at31567 | -0.004851231 | +0.035871472 | 3.6288 |
| Above plus INV_1→2 at38387 | 0 | +0.035871472 | 5.4432 |

Both sizing probes retain nonnegative fast/typical setup and slow/typical hold at+0.319681168/+0.134421036ns. The two-cell probe has no printed slow setup failures; the9 former failing endpoint margins range from+0.289420038 to+0.629702508ns (dropped[67]:+0.489334822). Global setup WS remains0 because reported transparent-latch paths sit at0; this is not a claim of positive official WNS. These are fixed-wire estimates, not fresh physical closure. A valid alternative A21OI1→2 at44061 also reaches-0.004851231ns but has not been selected for physical screening.

Two exploratory upstream o21ai_2/xor2_2 probes were discarded: these strengths do not exist in the pinned library, and OpenSTA silently creates black boxes. Their apparent improvements are invalid. Accepted results check master existence and reject missing-cell/black-box/errors; physical helpers fail on absent replacement masters (BUG80).

Prepared manual workflow gds-drop-event-screen: freezes successful antenna-clean screen37736921949, original source37533969613/bs-event-late,20ns and full2/4 hardware fingerprints. Only31567 is resized;38387 remains unchanged. Fresh ODB baseline must match inherited logical netlist; exact one-master change and powered views are mandatory. Legalization, full GRT, strict incremental antenna repair, fresh diode-only views and fully timed all-corner STA precede eligibility. No DRT or official hardening is launched by this screen. The inverter is a separate next experiment after measuring this one hardware change.

Source alone still does not reproduce these physical ECOs in the official clean build. Preserve the stronger original extracted-0.179789ns baseline until a new candidate surpasses it physically. No Phase2 checklist tick.
