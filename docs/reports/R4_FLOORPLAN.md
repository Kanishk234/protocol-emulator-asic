# R4: a full-size TRIPWIRE floorplan at 6x4

**Question:** at what utilisation does a full-size TRIPWIRE route on the 6x4 tile (1289.28 × 710.64 µm die, ~902K µm² core, Metal1–Metal4)? R2 routed one lane only at ~42 % placement density; the plan of record is ~74–85 % of the core. DECISIONS D-043.

**Status (2026-09-26): run 1 failed at detailed placement after post-CTS hold repair (DPL-0036), at ~70 % global-placement utilisation (~77 % after the flow's growth). Routing was never reached.** §3–4. **Run 2 (4 pin units, density 62, 2026-09-26/27) placed at 58.9 % and passed CTS and hold repair, then spent 5 h 51 min in global routing without finishing and hit GitHub's 6 h limit; no overflow numbers, no artifacts.** §5–6. **Run 3 (same design, no clock NDRs, 2026-09-27) ran the whole flow in 5 h 25 min and does not route: global-routing overflow 4,883 (4,651 on Metal3, the only horizontal routing layer, at 92.8 % usage), 12,872 detailed-routing violations at the end. About three quarters of the violations are in the lanes' area.** §7. **Run 4 (2 lanes, density 51, 2026-09-27): global routing with 0 overflow (Metal3 74.2 %); detailed routing reached 874 violations in its 4 allowed iterations, 1,428 after the antenna re-routes; job 2 h 55 min.** §9. **Run 5 (the same with `DRT_OPT_ITERS` 64, 2026-09-28): routes clean. 0 DRC, LVS match, 0 antenna, typ timing met, gl_test and precheck pass; `gds` job 2 h 58 min, precheck 1 h 56 min.** §10. **Run 6 (the real chip at the protocol floor, 2026-09-28): placed at 56.1 %, global-routing overflow 5,350 (Metal3 87.3 %); detailed routing reached 16 violations after its 64 iterations (4 h 53 min), then GitHub's 6 h limit stopped the antenna re-route. No artifacts.** §11–12. **Flow growth analysed: hold repair at a 0.25 ns hold uncertainty is ~50K µm²; run 7 (hold uncertainty 0.10 ns, run 6's design) prepared, §13. RTL area pass on `main`: 407.6K → 391.7K at the floor, §14.**

---

## 1. What is being hardened

Branch `spike/r4-floorplan`, built by `spikes/r4_floorplan/apply_to_branch.sh` from single sources on `main`.

| Block | Source | Yosys µm² (cmos5l typ, per module) |
|---|---|---|
| 3 lanes (lane + ALU + latch slots and K) | `spikes/r1_lane` | 3 × (35.1K + 5.9K + 24.5K*) |
| 3 routine sequencer stubs | `r4_seq.v` | 3 × 2.9K |
| 6 lean pin units + config latch blocks | `src/trw_pin_*.v` | 6 × (29.8K + 5.1K) |
| fabric: 13 ports (7/8/9 sources) + release terms | `r4_port.v`, `r4_fabric.v` (generated) | 13 × 2.2–2.6K + 3.8K |
| host SPI stub | `r4_host.v` | 9.1K |
| top: pad sync, owners and pad muxes, 7 producers, port registers, host read mux, SRAM rotation | `tt_um_tripwire.v` | 54.3K |
| **total, flattened** | | **498.8K** + the SRAM macro (45.3K) |

\* 33.9K in the per-module run, which cannot see that the slot read address is a constant; the flattened run removes the read multiplexer, as D-039 asks.

- Cells (flat): 2,592 flops, 2,814 latches (3 × 700 slot/K bits + 6 × 119 configuration bits), 210 clock gates, the macro.
- Scenario G (2 full + 2 lean units, 3 lanes) was ~483K before layout: R4 is area-equivalent.
- **Pre-layout timing at 20 ns** (OpenSTA, ideal clock, no wires, configuration latches static): +10.63 ns typ, +5.50 ns slow. The worst path starts at a pin unit's output register (`g_unit[5].u_unit.u_tx.lvx`) and goes through the pad owner mux onto `uo_out` and back into a unit as pin B/S (§14 P7: a unit may read a `uo` pad directly), then into the TX take logic.

**Local checks** (`spikes/r4_floorplan/check_local.sh`): lint clean. 5/5 pin-level tests on the RTL and 5/5 on the Yosys gate-level netlist (TT Icarus 13): SRAM words through the host rotation slot, a lane forwarding HOST_IN to HOST_OUT, a pin unit sending a UART frame on `uo0`, a pin-unit event reaching the host, a routine fetched through the rotation (CALL → SETST → RET). They also run in the branch's `gl_test`.

## 2. Flow settings (branch `src/config.json`, D-043)

| Key | Value | Why |
|---|---|---|
| tiles | 6x4 | the real tile |
| `PL_TARGET_DENSITY_PCT` | 73 | lowest legal: ~71 % expected placement utilisation (≈ 1.19 × Yosys + the macro, the ratio seen on R2) |
| SRAM `MACROS`, `PDN_*`, `FP_PDN_V*` | R3's, macro at (12, 40) FS | known-good recipe (D-031) |
| `PNR_SDC_FILE` / `SIGNOFF_SDC_FILE` | R2's latch exception | the resizer otherwise spins on latch pins (D-032) |
| `DRT_OPT_ITERS` | 3 | a stalled route ends and uploads `GDS_logs` inside 6 h (D-034) |

## 3. Results: run 1 (2026-09-26) — failed at placement, before routing

`gds` on `spike/r4-floorplan` (1ca1bdc), run [36269756517](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36269756517). Logs: the `GDS_logs` artifact, unpacked in `build/ci/r4/` (not committed). The flow stopped at step 37, `OpenROAD.ResizerTimingPostCTS`, with **DPL-0036: detailed placement failed**. It never reached global or detailed routing, so there are no overflow or routing-violation numbers. The whole flow took about 5 minutes of step time.

**Area through the flow** (core 902,417 µm²; the macro is 45,309 µm² of it):

| Stage | Standard cells µm² | Utilisation (cells + macro) | Source |
|---|---|---|---|
| Our Yosys (typ, flat) | 498.8K | — | `check_local.sh` |
| LibreLane synthesis | 521.4K (36,896 cells: 2,598 flops, 2,814 latches, 210 clock gates) | — | step 06 `stat.rpt` |
| Global placement | 593.2K movable, incl. tap/endcap and pin padding | **70.0 %** (GPL-0019; D-043 predicted ~71 %) | step 28 |
| After design repair (4,470 fanout/slew buffers, 2,661 tie cells) | 559.8K | 67.1 % | step 34 metrics |
| After CTS (30.1K of clock buffers; `clk` has 2,598 register sinks + 211 macro/clock-gate sinks) | 590.9K | 70.5 % | step 35 metrics |
| After post-CTS hold repair (**3,921 hold buffers, +10.1 % area**) | ~650K | **~77 %** | step 37 log |

Then legalization failed on 43 instances (hold buffers and fanout buffers): the rows around them were full. The log does not give their coordinates, so which block they sit in is not known from this run.

**Timing** (mid-PnR STA after CTS, typical corner only): setup +8.94 ns worst (no setup violations at any corner, RSZ-0098). Hold: 99 violations at typ, worst −0.65 ns, nearly all on the SRAM macro's inputs (`A_DIN`, `A_ADDR` from the host write registers: flop → macro, with −0.46 ns clock skew between the register clock tree and the macro/clock-gate tree). The resizer, repairing all corners with the template's 0.1 ns hold margin, saw **2,315 endpoints** with hold violations (mostly at the fast corner) and fixed them all, costing 3,921 buffers.

## 4. What it means

1. **At ~70 % placement utilisation the full chip does not even place.** The flow's own growth after global placement (clock tree +5.6 %, hold buffers +10.1 %) takes it to ~77 %, and legalization fails. So the real ceiling is below 70 % at global placement, before any question of routing. R2's ~42 % remains the only density we know routes.
2. **The layout growth assumption holds.** Flow synthesis to post-hold was ×1.25 (521K → ~650K); AREA_ESTIMATE used ×1.30 from R2. Our Yosys numbers are ~4.5 % under LibreLane's own synthesis.
3. **Hold repair is the largest part of the layout growth at full size:** +10 % area on its own (R2 needed 364 hold buffers for one lane; here 3,921). Most of it is fast-corner hold across the whole design with the template's 0.1 ns margin, on top of the clock skew between the big register tree and the gated/macro tree. It is inside the ×1.30 factor, not on top of it, but it is the part that grows fastest with size.
4. **Failing runs are cheap:** ~5 min of flow time, so several configurations can be tried in a day.
5. **Routability is still unmeasured.** The next run has to get past placement to answer the question R4 was for.

**Run 2 candidates (one change, D-034 rule):**
- (a) **4 pin units instead of 6** (drop two lean units: ~−75K µm², GPL ~62 %, after growth ~70 %). This is also a real candidate cut. It needs a unit-count parameter in the R4 top.
- (b) Same design, `PL_RESIZER_HOLD_SLACK_MARGIN` 0.1 → 0.03: fewer hold buffers. It only moves the failure point a few percent, and it weakens hold margin, so it doesn't answer the routing question.
- (c) 2 lanes instead of 3 (~−70K). Also a real cut, but lanes are the area that routed in R2; units and the fabric are the unknowns.

Recommendation: (a), with density = its reported GPL utilisation + 2.

## 5. Run 2: 4 pin units (approved 2026-09-26)

One change from run 1 (D-034 rule): **4 pin units instead of 6**, and the density that follows from it.

- `localparam NU = 4` in `overlay/src/tt_um_tripwire.v`. Units 4–5 keep their numbers (host addresses, fabric numbering and tests are unchanged) but are absent: their producers are tied to constants, host writes to their configuration blocks are ignored, and `gen_fabric.py` reads NU and leaves out the `U4.tx` and `U5.tx` ports. The lane ports' multiplexers lose those two inputs in synthesis, as a real 4-unit fabric would.
- `PL_TARGET_DENSITY_PCT` 73 → **62**.
- Also on the branch, from `main`: the pin-unit rule changes P34/P38/P43 (eec4fcf), a few gates per unit. They are included in the numbers below, so they are not a second layout change.

| | Run 1 (6 units) | Run 2 (4 units) |
|---|---|---|
| Yosys flat, standard cells | 498.8K µm² | **417.7K µm²** (−81K) |
| Flops / latches / clock gates | 2,592 / 2,814 / 210 | 2,076 / 2,576 / 192 |
| Pre-layout slack typ / slow | +10.63 / +5.50 ns | +10.28 / +5.08 ns |
| Expected GPL utilisation (1.19 × Yosys + macro) | ~71 % (measured 70.0 %) | **~60 %** |
| Expected after CTS and hold repair (× 1.10, run 1's rate) | ~77 % (failed) | ~66 % |
| `PL_TARGET_DENSITY_PCT` | 73 | 62 |

`check_local.sh`: lint clean, 5/5 on the RTL and 5/5 on the Yosys gate-level netlist (TT Icarus 13).

If it places, this run gives the first routing numbers for a full-size floorplan: global-routing overflow per layer and detailed-routing violations per iteration. If GPL-0302 fires (density below the real utilisation), use the logged GPL-0019 figure + 2.

## 6. Results: run 2 (2026-09-26/27) — placed, stuck in global routing

`gds` on `spike/r4-floorplan` (ed3b949), run [36279959944](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36279959944). The `gds` job was stopped by GitHub's 6 h limit (23:36 → 05:36 UTC). Because the job was cancelled, `GDS_logs` was not uploaded; everything below is from the job log (`gh api …/actions/jobs/108509785917/logs`, not committed).

| Step | Time (UTC) | Result |
|---|---|---|
| Floorplan | 23:40 | effective utilisation 54.1 % (IFP-0104) |
| Global placement | 23:40 | **58.9 %** (GPL-0019; predicted ~60 %) |
| Design repair | 23:42 | 106 slew, 1,293 fanout, 6 capacitance violations repaired |
| CTS | 23:42 → 23:43 | ~1 min, as in run 1 |
| Post-CTS resizer | 23:43 → 23:45 | no setup violations; **1,869 hold endpoints, 3,067 hold buffers**; detailed placement **passed** (run 1 failed here) |
| Global routing | 23:45 → cancelled 05:36 | **never finished** (5 h 51 min) |

**What the global router did:** the Metal2–Metal4 resources after the 30 % derate were 154.7K / 184.9K / 152.8K. The router ran its 50 overflow-removal iterations (`GRT_OVERFLOW_ITERS`), still had overflow, disabled the 2×-spacing non-default rule (NDR) on one clock net (GRT-0273, first `clknet_0_clk_regs`), and ran another 50 iterations. It repeated this every ~5.5 min for the rest of the job, one clock net at a time: `clk`, the `delaynet_*_clk` hold-delay nets, and the gated clocks of lane slot words and pin-unit configuration words. The design has **1,307 clock nets** (GRT-0019), and the NDR goes on the non-leaf ones (`CTS_APPLY_NDR` = `half`, LibreLane's default), so this loop could not end inside 6 h. The overflow figures are printed only when global routing ends, so **they were never printed**. GRT-0102 also hit its 1,000-message limit at 01:31.

**What it means:**
1. **4 pin units at 58.9 % placement fit through placement, CTS and hold repair.** Run 1's failure point (~77 % after hold repair) is gone. Hold repair was again the largest growth: 3,067 buffers (run 1: 3,921).
2. **At 58.9 % the global router had overflow on the first pass and was still reporting it after ~65 rounds.** That is the first direct routing evidence for the full chip: congested. How much, and on which layers, is still unknown.
3. **The timeout came from the flow, not only the design.** Clock NDRs let the router keep trying to relax one net at a time. With a job limit, every future run with global-routing overflow will end the same way, with no numbers.
4. Still the only known routable point is R2's ~42 %.

**Run 3 proposal (one change, flow setting only):** same design, `CTS_APPLY_NDR` = `none` in the branch `config.json`. The router then runs its 50 iterations once and ends (`GRT_ALLOW_CONGESTION` is already on), so the run reports the overflow per layer, and detailed routing runs under `DRT_OPT_ITERS` 3. Removing the clock NDR also frees a little clock-routing space; the run is still valid for measuring the data-signal congestion. Approved by Krithik 2026-09-27 (D-043).

## 7. Results: run 3 (2026-09-27) — routed through, not clean

`gds` on `spike/r4-floorplan` (462bf06: run 2's design with `CTS_APPLY_NDR` = `none`), run [36327551624](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36327551624), `gds` job 5 h 25 min (14:53 → 20:18 UTC). The flow ran to LVS and then stopped on a LibreLane error (below). `GDS_logs` uploaded (1.8 GB unpacked; local copy in `build/ci/r4/run3/`, not committed).

| Step | Time (UTC) | Result |
|---|---|---|
| Global placement | 14:57 | 58.9 % (as run 2); the placer's own congestion estimate: 6.9–9.0 % of tiles overflowed |
| CTS, post-CTS resizer | 14:58 → 15:00 | no setup violations; 1,869 hold endpoints, 3,067 hold buffers (as run 2) |
| Global routing | 15:00 → 15:05 | **ended in 4 min 22 s** (50 iterations, overflow allowed). Cells + macro 594.6K µm² = **65.9 %** of the core |
| Antenna repair | 15:05 → 15:07 | 45 → 1 violation |
| Detailed routing | 15:08 → 19:31 | first pass 3 h 15 min; then two antenna re-routes (below) |
| Signoff | 19:32 → 20:18 | STA, Magic DRC (42 min), LVS |

**Global routing, final congestion (GRT-0096):**

| Layer | Direction | Resource | Demand | Usage | Overflow |
|---|---|---|---|---|---|
| Metal2 | vertical | 154,688 | 131,856 | 85.2 % | 72 |
| Metal3 | horizontal | 184,901 | 171,595 | **92.8 %** | **4,651** |
| Metal4 | vertical | 152,817 | 67,808 | 44.4 % | 160 |
| Total | | 492,406 | 371,259 | 75.4 % | **4,883** |

Wirelength 3.84 m; 39,050 nets. For comparison, R2 (one lane at ~42 %) routed with 0 overflow at 66.1 % Metal3 usage.

**Detailed routing (violations after each optimisation iteration, `DRT_OPT_ITERS` 3):**

| Pass | Iter 0 | Iter 1 | Iter 2 | Iter 3 | Time |
|---|---|---|---|---|---|
| First route | 46,596 | 25,219 | 23,102 | **6,004** | 15:13 → 18:22 |
| Re-route after antenna repair 1 (48 nets) | 17,027 | 12,926 | 12,741 | 9,769 | 18:29 → 19:01 |
| Re-route after antenna repair 2 (9 nets) | 14,349 | 13,689 | 13,697 | **12,872** | 19:07 → 19:31 |

Final: 8,673 shorts and 4,190 spacing violations, mostly on Metal2 (6,531 shorts, 3,596 spacing), then Metal3 (1,865 / 591), Metal4 (277 / 3). The antenna re-routes (`DRT_ANTENNA_REPAIR_ITERS` 3) cleared the antennas but doubled the violations and added 1 h 10 min.

**Where the violations are.** Synthesis flattens the design, so cells were assigned to blocks through the hierarchical net names they connect to (about a third of the cells get a block this way), and each violation to the block with the most cells in its 40 µm square. Approximate: **lanes 9,491 (74 %)**, pin units 2,650 (21 %), port configuration and the rest 730. The lanes fill the lower two thirds of the die and the pin units the top third; the densest squares (up to ~1,300 violations per 80 µm square) are in the middle of the die, in lanes 0 and 2, near the fabric and port configuration.

**Timing after routing** (STAPostPNR): typ and fast meet setup; **slow corner −10.89 ns worst, 706 violating paths** (worst: a slot latch → flop). Hold met at all corners (worst +0.10 ns, fast). 43 max-capacitance and 514 max-slew violations (slow). Before routing the resizer found no setup violations at any corner, so this comes from the routes (detours and shorts); it is not a timing result for the design until routing is clean.

**Signoff and the stop:** Magic DRC 60,326 (the tool says divide by 3–4), consistent with the routing shorts. LVS: same device count (39,341) but 38,433 nets in the layout against 39,219 in the netlist (**786 nets merged by shorts**), "Top level cell failed pin matching". LibreLane then failed reading netgen's JSON (`JSONDecodeError: Invalid \escape`, probably an escaped `g_lane\[…\]` net name in the mismatch list), so precheck and gl_test did not run. This is a tool problem that shows only when LVS already fails, not a design bug.

**What it means:**
1. **The NDR change worked:** global routing ended in 4 min and the full flow fits in 5 h 25 min. That leaves ~35 min under the 6 h limit, so every R4 run at this size is close to it.
2. **The full chip with 3 lanes and 4 pin units does not route at 58.9 % placement (65.9 % after the flow's growth).** Global-routing overflow is 4,883, and detailed routing ends at 6,004 violations before the antenna re-routes and 12,872 after. That is not a near miss.
3. **Horizontal routing is the limit.** Metal3 is the only horizontal routing layer (Metal1 has no routing resource here; Metal2 and Metal4 are vertical). It holds 95 % of the overflow at 92.8 % usage, while Metal4 is only 44 % used. The die is wide (1289 × 711 µm), which lengthens horizontal wires.
4. **The lanes, not the pin units or the fabric, carry most of the violations** (~74 %, approximate attribution). That goes against run 1's reading that the lanes were the known-routable part: one lane routes at 42 %, but three lanes packed at ~59 % do not.
5. For Metal3 to come down to R2's range (~66–80 % usage), horizontal demand has to fall by ~15–30 %. Density cannot do it (`PL_TARGET_DENSITY_PCT` cannot go below the utilisation), so the lever is less logic, or a different block arrangement.

**Run 4 candidates (one change, D-034 rule):**
- (a) **2 lanes instead of 3** (~−70K µm², GPL ~51 %). Takes out area where ~3/4 of the violations are. Also a real candidate cut for the chip (area budget: `AREA_ESTIMATE.md`, D-038–D-040).
- (b) Same design, `DRT_ANTENNA_REPAIR_ITERS` 0: gives the first-pass result (6,004) without the re-routes and saves ~1 h. Measures nothing new about routability.
- (c) Same 3 lanes, fewer slots per lane (the latch slot array is the densest part of a lane). A design change to the R1 lane, more work than (a).

Recommendation: (a). Decision: team (D-043).

## 8. Run 4: 2 lanes (approved 2026-09-27)

One change from run 3 (D-034 rule): **2 lanes instead of 3**, and the density that follows. Everything else as run 3 (4 pin units, `CTS_APPLY_NDR` = `none`, `DRT_OPT_ITERS` 3).

- `localparam NL = 2` in `overlay/src/tt_um_tripwire.v`. Lane 2 keeps its number (host addresses, fabric numbering and tests are unchanged) but is absent: its producers `L2.O0`/`L2.O1` are constant, host writes to its slots are ignored, its SRAM rotation slot stays idle, and `gen_fabric.py` reads NL and leaves out the `L2.I0`/`L2.I1` ports. The other ports' multiplexers lose lane 2's inputs in synthesis, as a real 2-lane fabric would.
- `PL_TARGET_DENSITY_PCT` 62 → **51**.

| | Run 2/3 (3 lanes) | Run 4 (2 lanes) |
|---|---|---|
| Yosys flat, standard cells | 417.7K µm² | **337.4K µm²** (−80.3K) |
| Flops / latches / clock gates | 2,076 / 2,576 / 192 | 1,829 / 1,876 / 140 |
| Pre-layout slack typ / slow | +10.28 / +5.08 ns | +10.27 / +5.05 ns |
| GPL utilisation (1.164 × Yosys + macro, run 2's measured ratio) | 58.9 % (measured) | **~48.5 %** |
| After CTS, hold repair and global routing (run 3: ×1.12) | 65.9 % (measured) | ~54 % |
| `PL_TARGET_DENSITY_PCT` | 62 | 51 |

`check_local.sh`: lint clean, 5/5 on the RTL and 5/5 on the Yosys gate-level netlist (TT Icarus 13).

**Protocols with 2 lanes:** All 20 programs in `programs/` use at most 2 lanes: CAN, LIN and IR NEC use 2, the other 17 use 1 (and every program fits in 4 pin units). So every protocol still runs on a 2-lane chip; what is lost is running them together: at most two 1-lane protocols at once, and a 2-lane program (CAN, LIN, IR NEC) alone, where 3 lanes allowed a 2-lane program plus a 1-lane one, or three 1-lane protocols.

**What to look for:** Metal3 usage and overflow against run 3 (92.8 %, 4,651), and whether detailed routing gets to 0 violations. R2 routed clean at 66 % Metal3 usage. If it routes, the next question is how far between ~48.5 % and 58.9 % the density can go back up (for example, by adding back logic), since this is below the plan of record. Expect ~5 h for the job again if routing does not converge.

## 9. Results: run 4 (2026-09-27) — no global overflow, detailed routing stopped early

`gds` on `spike/r4-floorplan` (3fc5b1a), run [36349736069](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36349736069), `gds` job 2 h 55 min (20:54 → 23:49 UTC). Stopped after LVS on the same LibreLane JSON error as run 3. `GDS_logs` in `build/ci/r4/run4/` (not committed).

| | Run 3 (3 lanes) | **Run 4 (2 lanes)** |
|---|---|---|
| Yosys (flat) | 417.7K µm² | 337.4K µm² |
| Global placement | 58.9 % | **47.6 %** (predicted ~48.5 %) |
| Hold repair | 1,869 endpoints, 3,067 buffers | 1,662 endpoints, 2,860 buffers |
| After global routing (cells + macro) | 594.6K µm² = 65.9 % | 493.8K µm² = **54.7 %** |
| Global-routing usage M2 / M3 / M4 | 85.2 / 92.8 / 44.4 % | 56.9 / **74.2** / 15.4 % |
| Global-routing overflow | 4,883 (M3 4,651) | **0** |
| Global routing time | 4 min 22 s | 22 s |
| Detailed routing, first pass (iterations 0–3) | 46,596 → 25,219 → 23,102 → 6,004 | 19,924 → 12,101 → 10,799 → **874** |
| After antenna re-route 1 / 2 | 9,769 / 12,872 | 1,196 / **1,428** (Metal2 1,244, Metal3 183, Metal4 1) |
| Detailed routing time | 4 h 23 min | 1 h 55 min (first pass 58 min) |
| Post-route setup typ / slow | met / −10.89 ns (706 paths) | met / **−5.98 ns** (425 paths, slot latch → flop) |
| Hold | met | met (worst +0.11 ns, fast) |
| LVS | 786 nets merged | 50 nets merged (the shorts) |
| Magic DRC | 60,326 | 58,188 (R3's macro alone: 57,923, inside the macro) |

**Where the violations are** (same method as §7): lanes 641 (45 %), pin units 511 (36 %), port configuration 265 (19 %). No hotspot: they are spread over the die, mostly Metal2 shorts and spacing.

**What it means:**
1. **At 47.6 % placement (54.7 % after the flow's growth) the full floorplan is routable in global routing: 0 overflow, Metal3 at 74 %,** close to R2's clean 66 %. Run 3 at 58.9 % was not. So the routable ceiling for this design lies between ~48 % and ~59 % at placement.
2. **Detailed routing was stopped by our own guard, not by congestion.** `DRT_OPT_ITERS` 3 (D-034, set to keep a non-converging route under 6 h) ends the first pass after 4 iterations, still falling steeply (10,799 → 874 in the last one). The antenna re-routes (`DRT_ANTENNA_REPAIR_ITERS` 3) then start from that unfinished route and end higher (1,428). With 0 global overflow, more iterations are the expected fix, and the remaining iterations are short (the last first-pass iteration took 9 min).
3. **Timing:** typ met; the slow corner's −5.98 ns comes from routes around unresolved shorts (−10.89 in run 3); pre-layout slack at slow was +5.05 ns.
4. **For the chip:** the RTL chip at 2 lanes and 6 units (2 full) is ~442K µm² (D-047 numbers), ~62 % at placement: above this window. The budget has to come down to roughly R4 run 4's size, or the ceiling has to be found between 48 % and 59 %.

**Run 5 proposal (one change, flow setting only):** same design, **`DRT_OPT_ITERS` back to LibreLane's default (64)**. With no global overflow the route should converge; the job is expected to take well under run 3's 5 h 25 min. It answers whether 47.6 % routes clean (0 DRC, LVS clean), which the budget needs before the switch (D-047). Approved by Krithik 2026-09-27 (D-043).

## 10. Results: run 5 (2026-09-28) — routes clean

`gds` on `spike/r4-floorplan` (e20d390: run 4's design with `DRT_OPT_ITERS` 64), run [36363295528](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36363295528). `gds` job **2 h 58 min** (00:44 → 03:42 UTC); `gl_test` **passed** on the hardened netlist; `viewer` passed; **precheck passed** (1 h 56 min, 03:42 → 05:38 UTC, most of it the KLayout DRC of the full 6x4 GDS). The whole workflow took 4 h 54 min. `GDS_logs` in `build/ci/r4/run5/` (not committed).

| | Run 4 | **Run 5** |
|---|---|---|
| Global placement | 47.6 % | 47.6 % (same design) |
| Global-routing overflow | 0 (Metal3 74.2 %) | **0** (Metal3 74.2 %), 24 s |
| Detailed routing | 874 after 4 iterations, 1,428 after the antenna re-routes | **0** (262 → 88 → 87 → 1 → 1 → 0 by iteration 5; 0 after the antenna passes); 1 h 58 min |
| Antenna | 0 | **0** |
| LVS | 50 nets merged | **match** ("circuits match uniquely") |
| Magic DRC | 58,188 | 57,924 = the SRAM macro's own baseline (R3: 57,923 with the macro alone) |
| Utilisation after the flow | 54.7 % | 54.9 % (standard cells 52.5 %) |
| Timing typ / slow / hold | met / −5.98 / met | **met** / −6.01 ns (437 paths) / met (+0.10 ns fast) |

**What it means:**
1. **A full-size TRIPWIRE floorplan routes clean on the 6x4 tile at 47.6 % placement (54.9 % after the flow)**: 2 lanes, 4 lean pin units, the fabric, the SRAM and a host, with 0 DRC, LVS clean, 0 antenna, typ timing met and `gl_test` passing, in under 3 h. R4's question has its lower answer.
2. **The routable ceiling lies between 47.6 % (clean, run 5) and 58.9 % (not routable, run 3).** Run 4's failure was only our iteration cap.
3. **The slow corner misses by 6 ns** on slot-latch → flop paths (EVAL), with routing clean, so this is the design's real slow-corner number, not a routing artefact. The typical corner (the phase 2 sign-off corner) is met. The slow corner is reported honestly (L8-STA) and is a candidate for work later (the EVAL path, or the latch-slot timing).
4. **A full-size hardening takes about 5 h end to end:** ~3 h `gds`, then precheck ~2 h (in parallel with `gl_test`, ~3 min). The precheck's live log stops updating during the DRC, which looks like a hang; it is not.
5. **For the budget:** the protocol floor (D-049: 2 lanes, 4 units with U0 full, 12 slots) is ~395K µm² ≈ 56 % at placement by the RTL numbers, more with the BITSYNC engine's growth (D-052, ~58 %). That is inside the untested 48–59 % window. The next measurement that settles the budget is a run at the floor's size, ideally with the real `trw_chip` at those counts.

## 11. Run 6 (pushed 2026-09-28 06:03 UTC, 7a0548d): the real chip at the protocol floor

Asked for by Krithik (D-043's next measurement). One change of design, and the density that follows. It replaces run 5's stand-in with the real chip at the smallest size that still supports every protocol (D-049).

- **Design:** `src/` is main's RTL (B2c and the retimed BITSYNC engine included) with the branch's spec at the floor: `fabric.lanes` 2, `units` 4, `pin_config.units` with only U0 full, and the host-map counts that follow. `tools/gen/gen.py` regenerates `trw_fabric.v`, `trw_defs.vh` and `tripwire_spec.py`. `tt_um_tripwire` is a wrapper of `trw_chip`, so the SRAM's flattened path is `u_chip.u_sram.sram` (checked with a local Yosys flatten; `config.json` `MACROS` and `PDN_MACRO_CONNECTIONS` follow). `info.yaml` and `test/Makefile` list the chip's 19 sources. `test/test.py` has 4 pin-level tests taken from `test_internal/chip/test_chip.py` (identity, time and SRAM; a lane forwarding HOST_IN to HOST_OUT; UART from U0 and from lean U3; a routine on the rotation), so `gl_test` checks the hardened netlist.
- **Size:** Yosys **398.7K µm²** (run 4's stand-in: 337.4K), so **~56.4 %** expected at global placement ((1.164 × Yosys + 45.3K) / 902.4K core). `PL_TARGET_DENSITY_PCT` 51 → **59**. `DRT_OPT_ITERS` stays 64.
- **Pre-layout timing:** +7.35 ns typ, +0.42 ns slow (the worst path is inside the BITSYNC engine's timer; before the retiming, BUGS #51, slow was about −10 ns).
- **Local checks:** Verilator `-Wall` clean; `test/` 4/4 on the RTL; `test_internal/chip` 10/10 at the floor's counts. The branch's `unit` and `rtl` workflows will show known failures: 11 pytest cases and the L1-CHAN / L1-HOST harnesses hard-code the spec's 3 lanes, 6 units and U1 full (the numbering, 13 ports). Those are test assumptions, not RTL faults.
- **What to look for:** global-routing overflow (run 3 at 58.9 %, 3 lanes: 4,883; run 4/5 at 47.6 %: 0), then whether detailed routing reaches 0. If it routes clean, the floor fits on 6x4 with margin to spare, or none, which is what the budget needs. If it does not route, the job may run to the 6 h limit with 64 iterations and leave no artifacts. The fallback is then a rerun with `DRT_OPT_ITERS` 3, to read the overflow.

## 12. Results: run 6 (2026-09-28) — congested; stopped by the 6 h limit in detailed routing

`gds` on `spike/r4-floorplan` (7a0548d), run [36384571157](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36384571157). The `gds` job ran 06:03 → 12:03 UTC and was **cancelled by GitHub's 6 h limit** in the first antenna re-route of detailed routing; precheck, `gl_test` and `viewer` were skipped, and no artifacts were uploaded. Everything below is from the job log (`gh api …/actions/jobs/108807151528/logs`, local copy `build/ci/r4/run6/gds_job.log`, not committed).

| | Run 5 (stand-in, 2 lanes, 4 lean units) | **Run 6 (real `trw_chip` at the floor)** |
|---|---|---|
| Yosys (flat) | 337.4K µm² | 398.7K µm² |
| Global placement | 47.6 % | **56.1 %** (predicted 56.4 %) |
| Post-GPL repair | 917 fanout violations, 2,873 buffers | 1,145 fanout violations, 3,453 buffers |
| Hold repair | 1,662 endpoints, 2,860 buffers | 1,891 endpoints, 290 buffers |
| After global routing (cells + macro) | 493.8K µm² = 54.7 % | **567.7K µm² = 62.9 %** (6,670 repair buffers, 77.6K µm²) |
| Global-routing usage M2 / M3 / M4 | 56.9 / 74.2 / 15.4 % | 76.0 / **87.3** / 35.3 % |
| Global-routing overflow | 0 | **5,350** (Metal3 5,100, Metal2 159, Metal4 91) |
| Global routing time | 24 s | 3 min 42 s |
| Detailed routing, first pass | 0 at iteration 5; 1 h 58 min in all | 37,402 → 21,390 → 19,844 → 4,882 → … → 93 (iteration 38) → **16 after iteration 64**; **4 h 53 min** (iteration 0 alone 55 min) |
| Antenna re-route 1 | 0 | 3,414 → … → 60 when the job was cancelled |
| Signoff (STA, DRC, LVS) | done | not reached |

**What it means:**
1. **The real chip at the protocol floor (398.7K µm², 56.1 % at placement) is congested on the 6x4 tile:** 5,350 global-routing overflows, nearly all on Metal3 (the only horizontal layer), like run 3 (58.9 %, 4,883). The router nearly got there anyway (16 violations after the first pass), but it took almost 5 h, and the flow still needed the antenna re-routes and ~45 min of signoff. The same run would need about 7 h; the `gds` job has 6 h.
2. **A local hardening is not an answer:** the competition hardens every entry with the same Tiny Tapeout `gds` workflow, so the design has to pass inside that job. The target is a route that finishes with margin, as run 5 did (3 h job).
3. **So the protocol floor as built today is above the ceiling for this flow.** The routable point we know is run 5's 47.6 % (337.4K µm²). Somewhere between 47.6 % and 56.1 % the route stops fitting in the job. The chip has to come down by roughly 40–60K µm² (to ~340–360K), or its routing demand has to drop in some other way.
4. **Where the area is** (Yosys, hierarchical, 412.5K µm² before flattening): pin units ~201K (U0 full 73.8K of which the BITSYNC engine 34.8K; three lean units 91.4K, their TX 18.7K each; configuration latches 26.6K; pad owners 9.7K), lanes 150K (two × lane 44.5K + ALU 5.9K + slot store 24.5K), fabric 27.6K + producers 7.7K, host 22.2K (SPI 9.2K).
5. The 2,148 tie cells are the flops' unused asynchronous reset pins tied high (sync reset; run 5 had 1,852). They are not a problem to fix.

**Next (needs a decision, D-049/D-043):** the choices and the recommendation are in `docs/HANDOFF.md` §3 and the session's WORKLOG entry. No run 7 is prepared yet.

## 13. Where the flow's growth comes from, and run 7 (prepared 2026-09-28)

**The growth after synthesis is larger than the design's own margin.** Run 6's cell reports, step by step (cells + macro):

| After | Cell area | Repair buffers |
|---|---|---|
| synthesis / floorplan | 466.2K µm² | — |
| post-GPL design repair (1,145 fanout violations, `MAX_FANOUT_CONSTRAINT` 10) | 491.6K (+25.3K) | 3,470 |
| CTS (clock tree: ~1,100 clock buffers and inverters) and the post-CTS resizer (hold repair, 1,891 endpoints) | **567.7K** (+24K clock tree, **+52.3K hold**, "+10.1 %") | 6,670 |

Run 5 shows the same pattern (2,873 fanout buffers, 2,860 hold buffers). So hold repair alone adds about as much as the whole R4 run 5 → run 6 difference in logic.

**Why hold repair is so large.** Our constraints (the branch's `pnr.sdc` sources LibreLane's `base.sdc`) set `set_clock_uncertainty 0.25`, which applies to hold as well as setup, and the resizer repairs hold at all three corners with a 0.1 ns margin. Timing run 5's post-CTS netlist (`35-openroad-cts/tt_um_tripwire.nl.v`, propagated clock, no wire parasitics) locally at the fast corner (−40 °C, 1.32 V):

| Hold uncertainty | Endpoints violating | Endpoints below the 0.1 ns repair margin |
|---|---|---|
| **0.25 ns (now)** | **1,546** (median slack −0.05 ns; 1,517 flop D pins spread over the whole design) | 1,834 |
| 0.10 ns | 29 | 581 |
| 0.05 ns | 28 | 60 |

The ~28 that remain are real (mostly the SRAM macro's input hold, −0.52 ns). Almost all the rest are ordinary short flop-to-flop paths that fail only because of the 0.25 ns hold uncertainty. After CTS the flow times with the propagated clock tree, so the skew is modelled, and clock jitter does not affect hold (launch and capture are the same edge); 0.1 ns on top of the fast corner is a normal, still conservative, hold uncertainty. Setup keeps 0.25 ns.

**Run 7 (prepared in the worktree `~/tw-r4`, one change):** run 6's design unchanged, with `set_clock_uncertainty -hold 0.10` added to `pnr.sdc` and `signoff.sdc` (sign-off must use the same value, or it would report hold violations the flow did not repair). DECISIONS D-056 (proposed). What to look for: the hold endpoints and buffers after the post-CTS resizer (run 6: 1,891 and +52.3K), the utilisation after global routing (run 6: 62.9 %), the global-routing overflow (run 6: 5,350), whether detailed routing finishes inside the job, and hold met at sign-off at every corner. If it routes, the RTL area pass (§14, on `main`) is margin on top.

## 14. The RTL area pass (2026-09-28, on `main`)

Behaviour-preserving changes, each with the unchanged tests and mutants passing (floor = 2 lanes, 4 units, U0 full; Yosys cmos5l typ):

| Change | Saving at the floor |
|---|---|
| Lanes: one read port per ALU operand side and one register write port for the step in EXEC (they are mutually exclusive), instead of a 16-bit register mux per use and an 8-source write mux per register | −13.0K (51.5K → 45.0K per lane) |
| Pin TX: one burst-timer decrement for the three cases | −1.3K |
| BITSYNC engine: the TX queue loads right-aligned and reads bit `qn−1` (MSB first, CRC) or bit 0 (LSB first), no barrel shifter | −1.1K |
| **Total: the floor chip 407.6K → 391.7K µm²** (timing +7.32 typ / +0.47 slow) | **−15.9K** |

Measured and not worth it: an indexed source select in the fabric ports (+0.35–0.5K), the host's address decode without subtractors (+0.04K, synthesis already folds them). Measured and required by the spec: the routine machinery (15.9K of a lane), the engine's parallel resync arithmetic (8.5K, B2c's timing fix), the host's lane-debug readback (4.1K). The remaining behaviour-preserving opportunities are small (a few K), so the RTL pass ends around 385K; the flow's hold repair (§13) is the larger lever.
