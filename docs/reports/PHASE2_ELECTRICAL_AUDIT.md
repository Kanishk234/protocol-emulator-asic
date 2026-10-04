# Repaired checkpoint electrical audit

Evidence: signoff-aware repair run [37185455158](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37185455158), fresh single-corner `after-*` checks and repaired DEF/netlist. These are pre-antenna estimated parasitics; coordinates are component origins, not pin positions. No electrical fix or final-route result is claimed.

| Corner | Slew violations | Fanout violations | Cap violations |
|---|---:|---:|---:|
| Fast | 0 | 164 | 0 |
| Slow | 3 | 164 | 0 |
| Typical | 1 | 164 | 0 |

## Specific slew targets

| Pin | Corner | Limit (ns) | Slew (ns) | Excess (ns) |
|---|---|---:|---:|---:|
| SRAM `A_MEN` | Slow | 0.595200 | 0.968795 | 0.373595 |
| `_30324_/A2` | Slow | 2.507400 | 2.594301 | 0.086901 |
| `_30323_/Y` | Slow | 2.507400 | 2.593404 | 0.086004 |
| SRAM `A_MEN` | Typical | 0.476000 | 0.584123 | 0.108123 |

`_30323_` is a `sg13cmos5l_nor4_1` at (800.64, 207.90) µm. Its output `_04725_` feeds `_30324_/A2`, a `sg13cmos5l_a21oi_1` at (353.76, 226.80), spanning 446.88 µm in x and 18.90 µm in y. `_30324_` drives `u_chip.u_sram.men`. The SRAM placement origin is (12, 40), but exact macro pin location/extent must be used before measuring its enable wire. Trace includes NOR inputs `_04634_`, `net1405`, `_04641_`, `_04642_`; A21OI's other inputs are `_04724_` and `net2872`.

Controlled hypotheses, separately: move/clone the relevant logic nearer its consuming branch, strengthen the NOR output, or insert a remote-branch buffer; then remeasure macro-input slew, all-corner hold/setup, area and routing overflow. The two long-net pin violations and SRAM-input violation are distinct checks; do not assume one buffer repairs all three. No protocol-shaped hardware addition is needed.

## Clock fanout

All 164 fanout rows are `clkbuf_leaf_*_clk_regs/X`. Largest is `clkbuf_leaf_48_clk_regs/X` with 18 loads against a limit of 8; next leaves 4 and 62 have 17. Leaf 48 is a `buf_8` at (91.68, 687.96), leaf 4 a `buf_8` at (44.16, 291.06). Source CTS config has sink clustering enabled, with cluster size/max diameter and CTS max cap/max slew unset. This supports a separate CTS clustering/load-distribution experiment, not indiscriminate data-path buffering or relaxation of the library limits. Smaller leaf groups can add clock buffers and change skew/hold, so compare all corners and route burden before promotion.

## Independent work completed / pending

- Separate `l3-repaired-gl` workflow runs all 22 reference-model/available-sigrok protocol cases on the saved repaired netlist using Icarus 13 and pinned cells/macros. It records the netlist SHA256 and validates slow signoff-aware margin-zero repair config. Simulation is functional evidence, not timing simulation or final-netlist evidence.
- Separate extraction diagnostic is prepared to accept only a successful completed repaired route with final state/ODB/DEF/netlists and zero route DRC. It follows the pinned flow's cleanup/connectivity/fill/extraction/multicorner STA ordering and requires fresh reports from each corner. A timeout is rejected. It is not dispatched before the required route exists and does not replace full DRC/LVS/precheck/viewer/submission validation.
- Nine local orchestration/guard regression cases pass; workflow YAML and embedded Python parse. Actual L3 and future extracted diagnostics require their own CI evidence.
