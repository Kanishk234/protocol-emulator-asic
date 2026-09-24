# TRIPWIRE area, timing and routing log

One row per `gds` hardening (see `../design/PHYSICAL_DESIGN_AND_CI.md` §10). Judge changes by routing overflow, not cell count.

| Date | Commit | Config | Cells (logic / total) | Flops | Latch bits | Util. | Setup WS typ/slow/fast (ns) | Hold WS typ/slow/fast (ns) | M3 / total overflow | Det. route time | `gds` job / workflow | DRC/LVS/antenna | precheck | gl_test | CI run | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-23 | 9bd6f7d | Phase 0 placeholder: 8-bit counter; template `config.json` (20 ns, density 60) | 79 / 71,078 | 8 | 0 | 0.13% (1,150 µm² of 902,417 µm² core) | +14.41 / +13.61 / +14.85 | +0.47 / +0.89 / +0.23 | 0 / 0 (M3 demand 138 of 194,422) | < 0.1 min | 30.3 min / ~44 min | 0 / 0 / 0 | pass | pass | 35824649426 | Baseline only. 25 of the 27 min of flow steps are Magic DRC over the mostly empty tile, so ~25 min is the runtime floor of any 6x4 run. |

## Synthesis-only estimates (not hardenings)

| Date | What | Source | Result |
|---|---|---|---|
| 2026-09-24 | R1 spike: one lane (12 slots, EVAL/EXEC, ALU) + 2 consumer ports, Yosys onto cmos5l typ, no layout | `spikes/r1_lane/run_r1.sh`; `R1_LANE_TIMING.md` §4 | Latch slots: ~65K µm² per lane (lane 35.0K, ALU 5.9K, slots 24.5K = 636 + 64 latch bits + 52 `lgcp` clock gates); 170 lane flops. Flop slots: slots 51.7K. Three lanes with latches ~196K µm² (22 % of the core). EVAL at 20 ns: worst slack +8.2 ns (slow corner) |

## Row notes

**Row 1 (phase 0 counter):**
- **Cells:** the 79 logic cells are 8 flops, 48 gates, 2 inverters, 18 timing-repair buffers (16 of them hold buffers) and 3 clock buffers. The other 70,999 are filler cells.
- **Power:** 95 µW total, of which 56 µW is leakage.
- **Other:** worst setup clock skew 0.26 ns; total wirelength 2,095 µm (global route).
- **Source:** `runs/wokwi/final/metrics.json` and `39-openroad-globalrouting` in the `GDS_logs` artifact of run 35824649426.
- **Useful for later:** the Metal3 resource (194,422 global-routing units) is the capacity our real design's M3 demand will be compared against.
