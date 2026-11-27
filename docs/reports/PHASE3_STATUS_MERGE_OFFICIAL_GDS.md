# D-192 official GDS result

The [official GDS run on 76d8c82](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44672634790) failed at extracted slow-corner setup. The [pre-routing screen](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44633793811) passed. The routed artifact was reviewed from `GDS_logs` under `runs/wokwi`.

| Extracted check | Result |
| --- | --- |
| Slow setup worst slack | −1.342952 ns |
| Slow setup violations | 9 |
| Fast hold worst slack | +0.166769 ns |
| Hold violations across all corners | 0 |
| Final route DRC, KLayout DRC, LVS and antenna violations | 0 |
| Slew and capacitance violations across all corners | 0 |
| Precheck, gate-level tests and viewer | Skipped after the GDS failure |

The slow `58-openroad-stapostpnr` maximum-path report identifies eight failures launched at the U0 `bitsync_active` latch. Seven end in the U2/U3 RX timer registers and one in the fabric consumer's `last_seq`. The remaining violation is a U0 configuration latch to the U0 producer's `tok[14]`. The worst mode-latch path arrives at 22.379742 ns against a requirement of 21.036789 ns. Its hold delay cell contributes 0.796733 ns. Even subtracting that entire contribution would leave about 0.546 ns of negative slack before any effect on hold or downstream timing.

The official final pre-routing STA step emits fresh typical-corner metrics only. Earlier slow-corner metrics carried in its state file do not represent a fresh slow-corner measurement. The independent screen measured its own estimated parasitics. Extracted timing remains decisive.

The next experiment should target the mode launch and distribution cone and inspect the independent producer path. Keep this candidate off the qualified baseline until the unchanged official flow passes and extracted setup and hold are reviewed. The two formal and repository-audit failures on this branch are separate from this physical result.

## Cross-unit path trace

The worst slow-corner timing path shares gates `_25243_` and `wire11995` with the routed driver chain of `uo_out[5]` before continuing to U3's RX timer. This matches the architectural path through the pad owner selection and immediate output feedback in `trw_chip`, where all units sense `uo_out` directly. That contract makes simply registering the feedback a functional change.

The timing report lists seven hold delay cells on this path: `hold8937`, `hold8209`, `hold10718`, `hold10719`, `hold10617`, `hold8484`, and `hold8485`. Their reported slow-corner cell delays sum to 4.839 ns. These cells may protect other endpoints, and subtracting their delays is not a prediction of the timing after changing placement or repair. A useful controlled experiment is to preserve the output timing and predecode more of the pad selection before the late level signal arrives, then measure extracted setup and hold on all affected branches. Compare against the previously rejected pad-owner variants before replacing the existing mux.

## Root-clock follow-up

[Screen 44801334512](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44801334512) failed the fanout gate. The repeated PnR and signoff audits each found one violation at all three corners. Driver `_25615_/Y` (`sg13cmos5l_a221oi_1`) drives U3's `b_in` with fanout 9 against a limit of 8. Estimated slow functional setup reserve was +0.917259 ns and fast hold was +0.125274 ns. Routing overflow and fresh antenna counts were zero. The worst functional setup report still starts at U0's BITSYNC mode signal, now a root-clock flop, and ends at the U2 RX timer. The next experiment should reduce the load on the U3 B input and repeat the same screen gates before detailed routing.

The audited netlist connects seven logic inputs, one hold-delay input and one antenna diode to this driver. A useful comparison is the same net immediately before antenna repair and hold repair to establish when it reaches fanout nine. Keep the diode and hold protection in place while evaluating a reduced logic load or an earlier split.

The archived synthesis netlist starts at eight loads. Post-CTS timing repair replaces one direct logic load with hold cell `hold10263`, leaving eight. Post-global-route timing repair still has eight. The final antenna pass adds `ANTENNA_2`, bringing the total to nine. The design-wide constraint is 10, while the pinned standard-cell Liberty declares a default fanout limit of eight. The fresh audit enforces eight on this driver.

A scratch RX event qualifier rewrite passed all 274 Yosys equivalence points on the RX module. In isolated typical-Liberty mapping, it still drove three input loads and increased mapped cell count from 667 to 701. This does not justify screening that rewrite. A tighter implementation fanout target with one load of headroom is a more direct diagnostic. Its effect on buffer count, overflow, setup and hold would need to be screened and any adopted config change would need fresh qualification under the frozen-config rule.

The staged `root-mode-fanout7` diagnostic sets `MAX_FANOUT_CONSTRAINT` to seven in the isolated root-mode copy. The stage test verifies this is the only changed input compared with root-mode. The native resolved config must report seven, and the fresh audits use the same tighter config with the existing timing, electrical, antenna and overflow checks. This may produce failures on other nets if late repairs consume the headroom. Compare the resolved fanout, violation sites, all-corner timing and congestion against run 44801334512 before deciding whether to route. The diagnostic is locally prepared and has no physical results yet.

A structural Yosys count using standard-cell Liberty pin directions found 2,304 standard-cell drivers with eight direct cell input loads before final antenna repair and none above eight. After repair there were 2,303 at eight and exactly one above eight, `_25615_/Y`. This excludes non-standard-cell input loads and does not substitute for STA. A global target of seven can affect thousands of existing eight-load drivers, so check buffer growth and slack regressions alongside the original violation.

[Fanout-seven run 44854556261](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44854556261) completed native pre-routing and failed only fanout in the final audit. Its repeated fast and slow PnR reports list five drivers, all clock buffers with eight loads against the diagnostic limit of seven. The original U3 signal fanout violation is absent from those reports. Before changing the candidate again, compare the same saved views with the original qualified constraint policy and verify every remaining corner and implementation cost. Keep the stricter screen result recorded as failed.

The complete fanout-seven reports confirm the same five clock-buffer violations in all twelve audits. Each buffer has eight loads against the configured limit of seven. Both screen versions have zero antenna violations and zero preceding full-route overflow.

| Final pre-routing metric | Root mode | Fanout seven |
| --- | ---: | ---: |
| Slow functional setup reserve | +0.917259 ns | +0.206176 ns |
| Fast hold slack | +0.125274 ns | +0.073803 ns |
| Standard cells | 43,189 | 44,713 |
| Standard-cell area | 646,244 µm² | 661,917 µm² |
| Timing repair buffers | 12,315 | 13,751 |

The tighter target added 1,436 timing repair buffers and consumed 0.711 ns of estimated slow setup reserve. Even if a separate audit using the original constraint policy clears the clock buffers, the fanout-seven build is a poor route candidate on these measurements. Prioritize a targeted reduction in load on the root-mode U3 B-input cone. Set aside reuse of the global seven setting unless a later controlled run recovers setup margin. Both results remain pre-routing only.

A targeted scratch rewrite shared pin B's rising/falling terms between TX, LINKED_RX and event qualification. Yosys proved all 1,659 lean and 2,868 full pin-unit equivalence points. Isolated lean synthesis reduced direct B-input loads from two to one. Matched flattened root-mode chip synthesis did not reproduce that result: U3 stayed at two loads, U1 stayed at two, and U2 rose from two to three, despite a 48-cell reduction. This mapping uses a local typical Liberty and is a structural proxy for the native flow. The rewrite remains scratch and was not staged for another multi-hour screen.

The native synthesis netlist already has eight direct loads on U3 B: seven combinational inputs and the B history flop. The initial two-load local mapping used Yosys's default ABC strategy and underrepresented the native cone. Reusing the archived DELAY 0 script and ABC constraints locally moved the root-mode proxy to four U3 loads. In that proxy, the B-edge rewrite moves U3 from four to three loads, leaves U2 at four and moves U1 from three to four (37 fewer mapped cells overall). The proxy still misses the native baseline of eight and uses a different Yosys build and synthesis setup. Before a physical screen, test the rewrite at the pinned native synthesis stage with a matched baseline and compare every unit's direct loads.

The pinned native synthesis rerun reproduced the root-mode loads at 7/5/7/8 for U0–U3 (44863436159). B-edge sharing reduced them to 2/4/3/2 (44863438174) with four fewer mapped cells, 29,652 versus 29,656. Both receipts use the same merged config and engine, with only the RX and pin-unit files differing. Commit ff4c0f5 launched full pre-routing screen 44864256912 on the exact synthesis candidate and original fanout policy. Review post-repair margins and violations before routing.

## B-edge RTL regression

The simulation source hashes match the staged inputs from synthesis run 44863438174. The Icarus lean and full pin-unit suites each passed 60/60. The Verilator chip L3 run passed 22/22 with no failures or skips and sigrok enabled for cases with decoder checks. An initial sandbox run returned an empty UART decode after the waveform check passed. The same capture decoded correctly outside the sandbox, and the passing rerun used that environment. These are RTL results. Post-repair timing and electrical checks are pending in run 44864256912.

| Local result | XML SHA-256 |
| --- | --- |
| Lean pin unit | `bb0e02fd49e191e61ecba9f7cb43f09df6b5ef994db335b269a7c985317239f5` |
| Full pin unit | `072a605f5257fab6a3134d9388d1a5f81cfe563e0ed0c91950623fea55738577` |
| Whole-chip L3 | `cdb15f92fd9275dbf279d48ee86c53033c45f1406f04128a26ae22677b2e9d19` |

## Passing B-edge screen and official trial

[Run 44864256912](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44864256912) passed the pre-routing audit with +2.042368 ns estimated slow functional setup reserve, +0.114573 ns fast hold, zero timing or electrical gate failures, zero antenna violations and zero preceding full-route overflow. The final pre-routing state contains 43,173 standard cells and 12,299 timing-repair buffers. Verified the screen result against its trial and engine hashes and matched all screened input hashes to the synthesis artifact. The exact four changed RTL files were published as ad30aad on `tripwire/d192-b-edge`. The unchanged [official GDS workflow 44871062205](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/44871062205) started on that branch. Extracted timing, detailed-route violations and official downstream jobs remain pending.

## B-edge extracted setup failure

Official run 44871062205 completed Build GDS with a setup failure. The
final metrics report zero route DRC, antenna, electrical and KLayout DRC
violations. Fast hold is +0.106438 ns. Precheck, gate-level tests and viewer
were skipped. The slow-corner max-path report shows all six violations
launching from `_50125_`, U0's configuration latch for `PERIOD[1]`.

| Capture register | Slow setup slack |
| --- | ---: |
| U0 BITSYNC `ts_p` | −0.064993 ns |
| Fabric consumer 0 `last_seq` | −0.270084 ns |
| Fabric consumer 1 `last_seq` | −0.239508 ns |
| Fabric consumer 2 `last_seq` | −0.280696 ns |
| Fabric consumer 3 `last_seq` | −0.334733 ns |
| Fabric consumer 8 `last_seq` | −0.890324 ns |

The endpoint names come from the final netlist. The common hold cell
`hold10175` adds 1.090065 ns on the worst setup path. Three downstream
hold cells add another 1.889703 ns on that path. Removing those cells would
change hold closure. The targeted scratch trial uses enabled root-clock
flops for the eight fractional PERIOD bits in the full pin unit, following
the existing IDLE write-edge behavior. Verify the phase behavior and
re-measure hold before any physical adoption.

The fractional PERIOD storage [screen 45889902134](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/45889902134) passed with +1.918533 ns estimated slow functional setup reserve, +0.133569 ns fast hold, zero electrical and antenna violations, and zero preceding full-route overflow. The staged inputs matched the screen's complete candidate digest map. The exact candidate was committed at 9d9d1e1 on `tripwire/d192-period-root`, with only `trw_pin_cfg.v` changed among physical inputs compared with the earlier B-edge trial. The unchanged [official run 45900025983](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/45900025983) started. Extracted timing and downstream checks remain pending.

## Fractional PERIOD extracted result

[Run 45900025983](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/45900025983) completed detailed routing and missed slow setup at −0.831264 ns, with nine violating endpoints. Fast hold was +0.163210 ns. Electrical, antenna, detailed-route DRC and KLayout DRC counts were zero, and the LVS step was clear. Precheck, gate-level test and viewer were skipped.

The extracted reports and final netlist show that all nine failures launch from U0 BITSYNC `drv_b` (`_48304_`) and share `hold10980`. The capture set is U0 BITSYNC `tb[24:22]`, U2 RX `rt[23]`, fabric consumer 0/2/8 `last_seq` and consumer 0/2 `pending_drop_n`. The earlier `PERIOD[1]` latch is absent from the failing path set. The worst `drv_b` to `tb[24]` path includes the common hold cell, several distribution buffers and two downstream hold cells. Evaluate the shared launch and pad-feedback segment before staging any further variant.

All nine failing paths share the distribution prefix ending at
`net12980`. Eight enter the AND3 at `_25188_`, and the U2 RX path enters
its NAND3 counterpart at `_25189_`. Both cells combine the distributed
`drv_b` with the registered SE0 state. A scoped induction proof on the
exact candidate proved `se0_r -> drv` after reset, so the extra
`drv &&` is redundant at `tx_se0`. The one-line variant passed all 60
full pin-unit cases and 54 CI-helper tests. Diagnostic commit c071211
launched [screen 45921497134](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/45921497134)
with only that BITSYNC RTL difference over the prior physical candidate.
The mask-based self-drive comparator prototype remains parked.

The SE0 follow-up [screen 45921497134](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/45921497134) passed the repeated all-corner checks. It reported +2.485875 ns slow functional setup reserve, +0.120712 ns fast hold, zero slew/capacitance/fanout and antenna violations, and zero preceding full-route overflow. All 35 candidate input hashes matched the download. Relative to prior official trial 9d9d1e1, the only physical-input change is the one-line redundant SE0 qualifier removal in `trw_pin_bs.v`. Official GDS workflow bytes match. The screen stops before detailed routing and extraction. The exact follow-up patch is staged locally under `build/` for isolated official qualification.
