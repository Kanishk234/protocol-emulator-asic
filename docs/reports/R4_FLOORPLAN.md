# R4: a full-size TRIPWIRE floorplan at 6x4

**Question:** at what utilisation does a full-size TRIPWIRE route on the 6x4 tile (1289.28 × 710.64 µm die, ~902K µm² core, Metal1–Metal4)? R2 routed one lane only at ~42 % placement density; the plan of record is ~74–85 % of the core. DECISIONS D-043.

**Status (2026-09-26): built and checked locally; run 1 not started** (the branch push is Krithik's). The results sections below are filled in after the `gds` run.

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

## 3. Results

*Pending run 1.* To record (also in `AREA.md`):
- utilisation (global placement, GPL-0019, and final);
- global routing: overflow per layer (Metal2, Metal3, Metal4), usage per layer;
- detailed routing: violations per iteration, route time;
- total `gds` time; timing typ / slow (post-route STA on the routed netlist, as `spikes/r2_latch/post_route_sta.sh`);
- where the congestion is: the GRT congestion report and the DRT violation locations, mapped to lanes, pin units, fabric and host.

## 4. What it means

*Pending.* The answers to look for: does it route at all; if not, at what utilisation it would ("fits at X %"); and whether the congestion is local (the slot arrays, as R2 suggested, which a lower local density or 2 lanes would fix) or global (the fabric multiplexers and the pad muxes, which fewer units would fix).
