# R4: a full-size TRIPWIRE floorplan at 6x4

**Question:** at what utilisation does a full-size TRIPWIRE route on the 6x4 tile (1289.28 × 710.64 µm die, ~902K µm² core, Metal1–Metal4)? R2 routed one lane only at ~42 % placement density; the plan of record is ~74–85 % of the core. DECISIONS D-043.

**Status (2026-09-26): run 1 failed at detailed placement after post-CTS hold repair (DPL-0036), at ~70 % global-placement utilisation (~77 % after the flow's growth). Routing was never reached.** §3–4. **Run 2 (4 pin units, density 62) is set up; §5.**

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
