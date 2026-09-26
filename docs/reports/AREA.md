# TRIPWIRE area, timing and routing log

One row per `gds` hardening (see `../design/PHYSICAL_DESIGN_AND_CI.md` §10). Judge changes by routing overflow, not cell count.

| Date | Commit | Config | Cells (logic / total) | Flops | Latch bits | Util. | Setup WS typ/slow/fast (ns) | Hold WS typ/slow/fast (ns) | M3 / total overflow | Det. route time | `gds` job / workflow | DRC/LVS/antenna | precheck | gl_test | CI run | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-23 | 9bd6f7d | Phase 0 placeholder: 8-bit counter; template `config.json` (20 ns, density 60) | 79 / 71,078 | 8 | 0 | 0.13% (1,150 µm² of 902,417 µm² core) | +14.41 / +13.61 / +14.85 | +0.47 / +0.89 / +0.23 | 0 / 0 (M3 demand 138 of 194,422) | < 0.1 min | 30.3 min / ~44 min | 0 / 0 / 0 | pass | pass | 35824649426 | Baseline only. 25 of the 27 min of flow steps are Magic DRC over the mostly empty tile, so ~25 min is the runtime floor of any 6x4 run. |
| 2026-09-24 | 09e8697 (branch `spike/r3-sram`) | R3 SRAM smoke test, 2x2: IHP 512x16 macro at (12, 40) FS + walking-ones BIST; macro `config.json` block + `FP_PDN_V*` (D-031) | 1,006 / 5,960 (+ 1 macro) | 97 | 0 | 47.3 % total (macro 45,309 µm², std cells 14,582 µm² = 17.9 %) of 126,685 µm² core | +10.95 / +9.23 / +11.23 | +0.33 / +0.67 / +0.14 | 0 / 0 (M3 demand 2,386 of 17,448) | < 1 min | 7.9 min / 9.7 min | 0 routing DRC; Magic 57,923 (inside the macro, not fatal); LVS 0; antenna 0 | pass | pass | 35961480554 | First macro hardening. Macro clock-to-output A_CLK→A_DOUT 4.29 ns typ / 6.59 ns slow; the slow-corner critical path is macro → BIST compare. 5 Magic illegal overlaps (the expected PDN crossings of the macro's VDD!/VDDARRAY! split). |
| 2026-09-24 | c4ef059 (branch `spike/r2-latch`, run 4) | R2: one R1 lane (12 slots in a latch array, 52 `lgcp` clock gates) + pin harness, 4x2; density 42, `DRT_OPT_ITERS` 8, `pnr.sdc`/`signoff.sdc` (D-032, D-034) | 7,197 / 23,230 | 297 | 700 | 39.6 % (std cells 103,023 µm² of 259,837 µm² core) | flop endpoints +11.53 / +6.58 / +13.65 (EVAL +11.75 / +6.94 / +13.65); latch D pins 0.00 (time borrowing, by design) | +0.32 / +0.67 / +0.13 | 0 / 0 (usage M2 52.6 %, **M3 66.1 %**, M4 9.8 %) | 54 min | 73.0 min / 90.5 min | 0 / 0 / 0 (Magic DRC 0) | pass | pass | 36060938609 | R2 passes on the 4th run. Runs 1–3 (3x2, density 60/60/52) did not finish routing (D-032, D-034). Wire length 471 mm. |

## Synthesis-only estimates (not hardenings)

| Date | What | Source | Result |
|---|---|---|---|
| 2026-09-24 | R1 spike: one lane (12 slots, EVAL/EXEC, ALU) + 2 consumer ports, Yosys onto cmos5l typ, no layout | `spikes/r1_lane/run_r1.sh`; `R1_LANE_TIMING.md` §4 | Latch slots: ~65K µm² per lane (lane 35.0K, ALU 5.9K, slots 24.5K = 636 + 64 latch bits + 52 `lgcp` clock gates); 170 lane flops. Flop slots: slots 51.7K. Three lanes with latches ~196K µm² (22 % of the core). EVAL at 20 ns: worst slack +7.9 ns (slow corner, worst of the re-runs) |
| 2026-09-25 | Whole chip at the frozen spec (v1.0), before any chip RTL: building blocks synthesized alone (`spikes/area/ae_prims.v`) x counts from the spec, R1 lane, R3 macro; layout growth x1.30 from R2 | `spikes/area/run_area.sh`, `estimate.py`; `AREA_ESTIMATE.md` | Placed ~984K-1,083K µm², **109-120 % of the core** (pin units ~84K each, ~504K for six; lanes 196K). Options and savings in `AREA_ESTIMATE.md` §7 |
| 2026-09-25 | First real pin-unit RTL, milestone A (lean feature set), Yosys onto cmos5l typ, no layout | `synth/pin/run_pin.sh`, `ablate.sh`; `PIN_UNIT_RTL.md` §3–5 | Lean unit 29.4K µm² (216 flops; TX 18.4K, RX 9.4K); configuration latches lean 5.1K (119 latches, 9 clock gates) / full 11.4K (307, 22); producer 1.5K. **Lean unit with config, producer and estimated port 38.7K vs the estimate's 41.2K (−6 %)**; the chip at scenario E is ~85 % of the core. Slack at 20 ns +10.8 typ / +5.8 slow (config static). Full unit: milestone B |
| 2026-09-26 | R4 full-size floorplan spike (branch `spike/r4-floorplan`, not yet hardened): 3 lanes (no slot read-back), 6 lean pin units with config latches, fabric (13 producers, 13 ports, generated muxes), SRAM macro + rotation, host SPI stub; Yosys onto cmos5l typ, flat | `spikes/r4_floorplan/check_local.sh`; `R4_FLOORPLAN.md` §1 | 498.8K µm² standard cells + 45.3K macro (2,592 flops, 2,814 latches, 210 clock gates); ~71 % of the core expected at placement. Pre-layout slack at 20 ns +10.63 typ / +5.50 slow. Hardening row follows the run |

## Row notes

**Row 3 (R2 latch slot array, branch `spike/r2-latch`, run 4):**
- **Result:** one lane with its 700-bit latch slot array and 52 library clock gates hardens and passes precheck and `gl_test`: the latch-array pattern test (all 52 words, two patterns) and the lane program test, on the hardened netlist.
- **Timing** (typ / slow / fast), from OpenSTA 2.6 on `final/nl` + `final/spef/nom` with the flow's sign-off settings:
  - settings: 20 ns, 0.25 ns uncertainty, ±5 % derate, propagated clock, 4 ns I/O delays;
  - cross-check: the hold slacks equal the flow's to 3 decimals;
  - EVAL endpoints +11.75 / +6.94 / +13.65 ns; EXEC endpoints +11.56 / +6.64 / +14.41 ns; outputs +9.39 / +5.56 / +11.55 ns;
  - the slow EVAL path starts at a slot latch (static while running), so +6.94 is conservative.
  - The flow's summary shows setup 0.000: the latch data pins, which borrow time (they pass).
- **Why four runs:**
  1. The post-CTS resizer spent 3 h 21 min on the 700 latch pins' 0.000 slack. `pnr.sdc` fixed it: 9.5 s in run 4.
  2. At density 60 on 3x2, routing stalled at 14 (run 1) and 8 (run 2) Metal2 violations.
  3. At density 52, first-pass violations fell from 8,297 to 33, but ~26 would not clear.
  4. On 4x2 at density 42, routing reached 0 at iteration 5.
- **For phase 2:**
  - (a) the latch SDC exception is needed on the real chip;
  - (b) even when it passes, this logic loads Metal3 to 66 % at 40 % utilisation (471 mm of wire), so the slot arrays need local density near 42 % in the 6x4 floorplan, not the template's 60;
  - (c) the 52-word slot read-back mux is the first candidate for cutting wires and area.
- **Source:** `runs/wokwi/final/metrics.json`, `39-openroad-globalrouting`, `44-openroad-detailedrouting`, `55-openroad-stapostpnr` in `GDS_logs` of run 36060938609; `spikes/r2_latch/post_route_sta.sh` for the EVAL/EXEC split (reads the artifact from `build/ci/r2/`).


**Row 2 (R3 SRAM smoke test, branch `spike/r3-sram`):**
- **Result:** the IHP `RM_IHPSG13_1P_512x16_c2_bm_bist` macro hardens, passes precheck, and passes `gl_test` (pin-level walking-ones BIST + address/data-line tests on the hardened netlist). Decision: the macro is kept (D-031).
- **Cells:** 97 flops, 591 gates, 54 inverters, 232 timing-repair buffers, 32 clock cells; 4,953 fillers.
- **Power grid:** the `pdn_cfg.tcl` check found 4 stripes through each macro supply (VDD!, VDDARRAY!, VSS!) and `check_power_grid` passed on VPWR and VGND.
- **For phase 2:** the macro's clock-to-output is 6.59 ns at the slow corner (4.29 typ). A routine word read on rotation slot k and decoded in clock k+1 has the rest of that clock, after 6.6 ns, for its decode logic (ARCHITECTURE §11, §14 R1). The SRAM read data is registered in the macro, so this path starts at the macro, not at a flop.
- **Magic DRC:** 57,923 errors, all inside the macro. Magic's cmos5l deck lacks the SRAM rules; the count matches the Loom smoke test exactly. The precheck's KLayout DRC is the sign-off check and passed.
- **Source:** `runs/wokwi/final/metrics.json`, `39-openroad-globalrouting`, `55-openroad-stapostpnr`, `21-openroad-generatepdn` in the `GDS_logs` artifact of run 35961480554.


**Row 1 (phase 0 counter):**
- **Cells:** the 79 logic cells are 8 flops, 48 gates, 2 inverters, 18 timing-repair buffers (16 of them hold buffers) and 3 clock buffers. The other 70,999 are filler cells.
- **Power:** 95 µW total, of which 56 µW is leakage.
- **Other:** worst setup clock skew 0.26 ns; total wirelength 2,095 µm (global route).
- **Source:** `runs/wokwi/final/metrics.json` and `39-openroad-globalrouting` in the `GDS_logs` artifact of run 35824649426.
- **Useful for later:** the Metal3 resource (194,422 global-routing units) is the capacity our real design's M3 demand will be compared against.
