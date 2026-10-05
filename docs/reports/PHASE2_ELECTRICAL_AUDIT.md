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

### No-mirroring checkpoint 37360552753

This newer state has estimated setup/hold passing all corners and clean antenna, but 19 slow slew records remain. Saved post-antenna DEF/netlist groups them into four driven nets plus SRAM A_MEN. Coordinates below are component origins; spans are placement bounds, not routed wire lengths.

| Net / driver | Connections including driver | Driver origin (µm) | x/y span (µm) |
|---|---:|---|---|
| `_12745_` / `_39031_` NOR3_1 | 9 | (294.24,298.62) | 608.64 / 147.42 |
| `_04725_` / `_30323_` NOR4_1 | 3 | (800.64,207.90) | 448.32 / 18.90 |
| `_04693_` / `_30187_` NAND4_1 | 4 | (297.60,287.28) | 669.12 / 124.74 |
| `_08831_` / `_34785_` O21AI_1 | 2 | (685.92,64.26) | 258.72 / 0 |

Long branches and weak one-drive cells support testing targeted slew repair/load splitting or sizing, separately from the active route. They do not prove the best repair or its timing/routability cost. Do not modify the active checkpoint. Separate `l3-hotspot-gl.yaml` prepares the expanded 22-case functional suite for this new repaired netlist, validates source workflow/gates/no-mirroring/slow margin-zero config and records SHA256. Its results are independent of final routing and do not provide SDF timing evidence.

- Separate `l3-repaired-gl` workflow runs all 22 reference-model/available-sigrok protocol cases on the saved repaired netlist using Icarus 13 and pinned cells/macros. It records the netlist SHA256 and validates slow signoff-aware margin-zero repair config. Simulation is functional evidence, not timing simulation or final-netlist evidence.
- Separate extraction diagnostic is prepared to accept only a successful completed repaired route with final state/ODB/DEF/netlists and zero route DRC. It follows the pinned flow's cleanup/connectivity/fill/extraction/multicorner STA ordering and requires fresh reports from each corner. A timeout is rejected. It is not dispatched before the required route exists and does not replace full DRC/LVS/precheck/viewer/submission validation.
- Nine local orchestration/guard regression cases pass; workflow YAML and embedded Python parse. Actual L3 and future extracted diagnostics require their own CI evidence.
