# Banked selector: extracted regression

Detailed-route continuation [37709856777](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37709856777) completed with zero route DRC errors. Extracted diagnostic [37714872507](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37714872507) is green but does not pass timing. Independently read artifact11522683978:

| Corner | Setup WS (ns) | Hold WS (ns) |
|---|---:|---:|
| Fast |0|+0.0949399475|
| Slow |-2.4757636642|+0.3294820066|
| Typical |0|+0.1851464590|

This is a setup regression relative to original event-late125ps (-0.1797886335 ns setup, +0.0372895059 ns fast hold). Banked selection is not eligible for official promotion. No official closure or phase tick follows from diagnostic success.

The slow max report contains41 violating entries. All start at `_48596_`, pin unit0 PERIOD configuration word4 bit1. Forty end at dropped-event counter bits and one at fabric channel1 `last_seq`. Worst endpoint `_47723_` is `u_chip.dropped[12]`. The worst reported data path contains no named hold-delay cell; buffer count alone does not explain the regression. These counts describe printed paths, not an exhaustive violation count.

Routed gate-level run [37714872772](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37714872772) independently passes22/22, zero failures/errors/skips (artifact11525366657). The isolated banked official-wrapper RTL replay also passes22/22 with sigrok,770.10s; its JUnit hash is recorded in PHASE2_OFFICIAL_GDS_READINESS.md. Functional correctness does not establish timing.

Retain original event-late125ps as the strongest extracted baseline. Its two remaining setup paths run from live PIN_A configuration through pad feedback/selection into unit3 RX timer bits23/22. Prefer a narrowly measured repair of that existing cone over another full-chip selector rewrite. Local static timing experiments must reproduce baseline timing before their deltas are trusted; any cell replacement still requires physical legalization, rerouting, all-corner extraction, antennas and protocol validation. Keep live configuration timed and all protocol support intact.
