# R1 all-tile native interfaces

D108 extends the frozen third profile to all ten tile types at the two already-declared widths. Local isolated preparation succeeds; LUT exported SHA exactly reproduces the passing representative netlist b743335546eb7cbecd98d9fd129a26855e900ca4f868caea2f5a43167faf6b1a. All original generated-model hashes remain unchanged. Actual assembled connectivity has40instances and3064adjacent bit pairs, no nonadjacent direct pairs.53local R1tests pass, including geometry/driver mutation rejection.

Hosted pin/core/interface results pending. No other-type placement/PDN/routing/timing, full-grid acceptance, or equal-area advantage is established by preparation. Both fixed widths execute and retain every tile outcome.

First native run40011371177 at234acca0bc1dea7d976c684b38da49fee922b554 admits18/20tile/core/cell cases. S_IO2 fails at both widths: native143signal pins vs155expected, losing12chained transparent clock-feed alias pins. BUG125 tests flattening4output alias assignments directly to their original input bits, preserving the frozen graph. No native admission for S_IO2 yet.

Mixed-type pin mismatch independently visible in retained native geometry: narrow N_IO.N1END[0] center53.28µm vs connected LUT.N1BEG[0]18.72µm on Metal2. Planned ordering disagrees on216/3064bit pairs. BUG126 derives six facing-side families (32/28/56/40/49/24slots), preserves LUT anchors and aligns connected track classes without changing the logical graph. Isolated preparation88files and exact assembled connectivity checkPASS;55R1testsPASS. Hosted repaired screen pending.

Replay40012576053 at39c656a90660a9dcecfc4b2c180639cf01c6b7c0 retains18/20geometry passes; flattening alone still loses the same12S_IO2ports. Canonical-order repair does align retained N_IO.N1END[0] and LUT.N1BEG[0], both18.72µm, but complete neighbor acceptance waits for S_IO2. Local diagnostic OpenROAD dcf36133a369abc8f3c5e5738cd4d82e4903c0e0 import-only probe measures143/143/155ports for original/flattened/deduplicated exports. It isolates four redundant continuous assignments from Yosys export; new guarded removal changes no mapped cells/logical bits. Hosted replay pending.
