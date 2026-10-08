# Original event-late candidate: targeted cell sizing

The strongest extracted baseline remains route37574267994 / extraction37581139249: slow setup -0.1797886335ns, fast hold +0.0372895059ns. Shared-RX and banked selection both regress after extraction. This study preserves the original netlist logic and changes only drive strength on its measured residual path.

## Reproduced baseline

Isolated `/tmp/event-125ps-local-eco` contains the exact routed netlist, nominal extracted SPEF, source hashes, guarded replacement inventory, scripts, reports and `comparison.json`. Cached OpenSTA2.6.0 with the pinned IHP standard-cell and SRAM Liberty files reproduces all three corner setup/hold measurements within1e-6ns. Slow start/end identities match CI.

The artifact's written routing SDC carries a latch setup exception inherited from PNR. Local replay removes that command to match actual CI signoff's fully timed constraints; the initial replay with the exception was discarded. This does not modify main constraints or change CI evidence.

## Fixed-wire probe results

| Replacement | Slow timer23 slack(ns) | Slow timer22 slack(ns) | Added library area(µm²) |
|---|---:|---:|---:|
| Baseline |-0.179788634|-0.052855499|0|
| `_27853_`: NOR2 strength1→2 |+0.103142388|+0.230075523|3.6288|
| `_27962_`: NOR4 strength1→2 |+0.044478200|+0.171411335|10.8864|
| Both |+0.327405661|+0.454338789|14.5152|

All replacement variants have reported global setup WS0 at every corner and hold fast/slow/typ +0.037289508/+0.369336575/+0.165097162ns. All12 verified corner invocations finish with no STA errors. Global WS0 is not a claim of positive official WNS; transparent latch paths can report zero even when these two endpoint checks have positive margin.

Buffer-only strength1→2 probes at place6860/place6758 leave negative slow setup (-0.072607/-0.105194ns respectively); they are lower priority. Each replacement checks the exact original master and matches exactly one instance before creating an isolated netlist. No RTL/state/latency/protocol or source wiring changes.

## Next physical experiment

Prioritize the single NOR2 replacement: largest individual measured gain for the smaller area cost (3.6288µm², about0.0007% of the baseline repair instance area). Its exact connections are A=`_21095_`, B=`_02509_`, Y=`_02510_`; original master `sg13cmos5l_nor2_1`, replacement `sg13cmos5l_nor2_2`. Check source provenance, master, connectivity, power and compatible pins before changing a physical checkpoint.

These probes reuse original extracted wires. They include changed Liberty loading but do not establish legal placement, new pin-access geometry, rerouted parasitics or all affected physical checks. A bounded physical follow-up must legalize/reroute, check all-corner setup/hold and antennas, extract fresh parasitics, and validate the final netlist. Keep the original checkpoint as reference; no broad hold repair or architectural rewrite is implied. A clean official build also needs a portable way to identify/apply the repair rather than relying on synthesis instance names. No physical dispatch, official promotion or phase tick occurred in this study.

## Repair-only workflow prepared (2026-10-08)

Local `gds-event-nor2-screen.yaml` accepts only successful main route37574267994 and original source37533969613/event-late. Trusted source fingerprints are reconstructed before downloading the artifact. Independently audited artifact11464617506: pre-route state and all five checkpoint views exist, cell/master/connections match the proposed repair, and exact one-cell netlist comparison passes. The checkpoint netlist SHA256 is `83e58066e2482c3db647c04b2004b94c74b30f206e4bbce1eacbfdca7f92da07`.

The pinned LibreLane3.1.0.dev3 global-routing script reads the checkpoint once. A guarded wrapper injects the master replacement and normal detailed-placement legalization, then runs the existing routing script with the existing Metal2 reservation. GlobalRouting normally exports only ODB/DEF, so the wrapper also writes fresh logical/powered netlists. The runner checks that exactly the intended logical cell master changes, explicitly adopts these fresh views, and clears inherited SPEF/SDF/Liberty views. This avoids timing or forwarding an obsolete pre-ECO netlist.

Fresh routing must report zero overflow on every Metal1–4 layer. Fresh antenna checks and fully timed per-corner STA must pass; failure makes the workflow red. No new broad resizer pass, antenna repair or DRT is launched. A subsequent guarded DRT/extraction/GL follow-up remains necessary even after screen success; this workflow does not complete Phase2 or prove official timing.

215 targeted/related helper tests pass, including exact master/connectivity/power/pin guards, failed and repeated replacement refusal, stale-netlist rejection, unintended logical change rejection, provenance, overflow completeness and wrapper ordering/delegation. Mock OpenDB tests are guard evidence only. The local OpenROAD binary still lacks QtCharts, so actual physical mutation awaits CI. Main hardware/configuration/template jobs remain unchanged; workflow and helpers are local and unpublished.
