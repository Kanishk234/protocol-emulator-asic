# Routed stronger driver passes physical and slew checks; native C2 mapping isolated

[Driver trial37708459393](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37708459393)
passes in30m05s (00:34:18–01:04:23UTC). Downloaded actual native,
geometry/LVS and fresh extracted electrical results were inspected.

The input is the legal placement-only ODB from37689324316, SHA256
7b2811c291443d4208bcb1154fbe37ab6eeb7be6702c52060f135d0318509adf.
Only u_cfg._54_ changes from a21oi_1 to a21oi_2; three cells shift left1.44um.
The earlier stale-pin-escape failure is repaired by ripping eight affected
signal nets before incremental routing. The remaining-geometry initial check
reports0 with those nets unrouted; this is not routing acceptance. Bootstrap
reports59 markers; the first late-cost pass reaches0, and a fresh full-chip
native check independently confirms0. Logical topology is unchanged.

Stock antenna nets/pins0 and critical disconnected pins0. Seven reported
noncritical disconnected pins remain; do not describe this as every pin connected.
Checked ODB SHA256:
b2378e005f42c3397940613919d2d564499127a878aa70015aaab0fe78b9f8b7.

Fresh fill/extraction uses the existing no-decap/D-052 pSD policy. Full Magic0,
KLayout0 and actual GDS-based shell LVS0. Final overlaid GDS SHA256:
bb415750feace175e140d2fbb3a9aca4b72731c248a884b46999eb933e3f3246.
Fresh extracted filled ODB SHA256:
b71f5f377faee63410781c4f108a7b9b06d26e2552ce9f3418b5f227fbf67285.

| Supplied shell corner | Setup worst slack(ns) | Hold worst slack(ns) | Slew | Capacitance | Fanout |
|---|---:|---:|---:|---:|---:|
|Fast1.32V/-40C|14.291997|0.124635|0|0|33|
|Slow1.08V/125C|12.250574|0.648150|0|0|33|
|Typical1.20V/25C|13.518095|0.312307|0|0|33|

At the unchanged20ns/50MHz target, all supplied setup/hold violation counts
are0. The previously measured nine slow-corner slew violations are now0 on
fresh routed parasitics, with geometry/LVS closure preserved. Fanout33 remains
an explicit open gate. Macro-black-box shell STA does not prove configured
fabric timing. The wider cell costs5.4432um2 nominal cell area; no equal-area
superiority, power improvement, precheck or successor promotion is claimed.

## Native synthesis-stage result

[Native diagnostic37709917442](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37709917442)
correctly fails overall while retaining all six actual cases. The two
regenerated original-control cases pass28 TX/28 RX edge patterns, STOP and
USER_RESET. Every actual configuration latch is known and matches the loaded
image:9164 latches,0 unknown,0 mismatches. BUG47's14 unloaded constant-X
aliases are classified using matched graph plus exact raw-source references.

Replacing only C2 with its original synthesis NL causes UART TX to become X
at4423540ns; the USER_RESET case fails at4425780ns. Replacing only C2 with
its original final physical NL causes the same failures. Those cases also
have9164 actual configuration latches known and matching. This isolates the
failure to behavior already present at original synthesis; physical processing
alone cannot explain it. The failing external pin is a real functional gate,
not another phantom configuration alias. The exact cause of the different
mapped combinational behavior remains under investigation.

Passing regenerated netlists still lack matching physical views. Continue
state-preserving combinational mapping isolation, a bounded matched-tile
floorplan/pin preflight and independent pre-CTS fanout work. Frozen G1 stays
the fallback until native function, configured timing, electrical limits,
official precheck and required CI are all supported by matching evidence.
