# Independent timing screen comparison

Frozen R4 3393eea, 20 ns, density 56, pinned LibreLane/PDK, signoff SDC. Values are fresh global-route estimated WS, not extracted routed signoff. Zero setup WS here does not establish positive margin. Repair used the slow corner only; all six independent baselines reproduce the same timing.

| Run | Variant | Slow setup before (ns) | Slow setup after (ns) | Fast hold after (ns) | Final logged GRT overflow |
|---|---|---:|---:|---:|---:|
| [37399927459](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37399927459) | rx-factor | -0.235318 | -0.0952376 | -0.0275806 | 0 |
| [37399927459](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37399927459) | baseline | -0.909935 | 0 | -0.0424919 | 0 |
| [37400509726](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37400509726) | baseline | -0.909935 | 0 | -0.0424919 | 0 |
| [37400509726](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37400509726) | pad-mux | -1.38536 | 0 | -0.0414423 | 0 |
| [37403722938](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37403722938) | baseline | -0.909935 | 0 | -0.0424919 | 0 |
| [37403722938](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37403722938) | timing-placement | 0 | 0 | -0.0045709 | 0 |
| [37403722954](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37403722954) | input-decode | -1.70015 | -0.117449 | -0.0485544 | 5 |
| [37403722954](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37403722954) | baseline | -0.909935 | 0 | -0.0424919 | 0 |
| [37403723111](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37403723111) | cached-input | -0.682983 | 0 | -0.004589 | 37 |
| [37403723111](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37403723111) | baseline | -0.909935 | 0 | -0.0424919 | 0 |
| [37403723129](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37403723129) | baseline | -0.909935 | 0 | -0.0424919 | 0 |
| [37403723129](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37403723129) | load-select | -0.992729 | 0 | -0.0232197 | 0 |

Timing-driven placement is the first follow-up: no hardware/storage addition, no estimated setup deficit before or after repair, and fast hold improves from −0.0424919 ns to −0.0045709 ns after repair. Cached-input approaches the same hold result but costs 192 latch bits; defer adoption. RX and stateless input-decode retain setup deficits; pad/load-select do not improve setup before repair relative to baseline. These are whole-flow comparisons, not isolated path-delay attribution.

Next experiment: matched baseline/timing-placement with all three corners loaded for the resizer repair, while fresh STA still uses one corner per process. Existing workflows retain their slow-only defaults. Fourteen orchestration/checkpoint tests pass, including eight combinations of corner mode, reused repair and explicit SDC. Detailed routing remains deferred until fresh setup/hold/electrical results are audited. Area and detailed critical-path artifacts still need examination; logs alone do not establish their improvement. Latest actual extracted slow setup remains −5.630099 ns.

## All-corner repair and route continuation

Run [37408506116](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37408506116) completed both jobs. Timing placement: all-corner estimated setup WS 0; hold fast +0.0360107 ns, slow +0.238266 ns, typical +0.103103 ns, all setup/hold violation counts zero. Baseline retains slow setup −0.274897 ns. Final logged GRT overflow is zero for both; demand 233,872 vs 259,955, a 10.0% reduction. Repair inserted 39 hold buffers vs 98 in baseline.

Downloaded placement artifact audit: total instance area 508,444 um² (standard cells 463,135, macro 45,309.3), 33,169 instances. Electrical violations remain: slow slew 8; fast/typ slew 0; fanout 162 in each corner; capacitance 0 in each. Do not treat timing passes as electrical/signoff closure. Worst slow report begins with latch _48984_ to latch _49160_, zero slack; zero is not positive margin. Raw artifact lives under /tmp/placement-multicorner-37408506116.

Prepared guarded gds-placement-route continuation of this exact frozen-hardware artifact, no resynthesis or new RTL. Validates source workflow/SHA, actual timing-placement config, constraints, all-corner repair, saved files and fresh source timing counts. Runs antenna check/repair/check, then six fresh single-corner before/after STA processes; aborts before DRT on dirty antenna or negative timing/nonzero timing violation counts. This is a routing diagnostic, not full signoff; electrical issues remain recorded. Thirty-two helper tests pass, including refusal of negative/missing timing or nonzero violation counts for each setup/hold corner.

## Latest actual extracted timing

Placement route [37412965189](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37412965189) completed successfully. Automatic extraction [37417248079](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37417248079) reports slow setup WS −1.731802306 ns, fast/typ setup0. Hold fast −0.035371207 ns, slow +0.115164992 ns, typ +0.012006063 ns. Actual slow setup deficit is 3.898297 ns smaller than the previous −5.630099 ns (69.2% reduction), comparing whole flows. Setup and fast hold still fail; zero global-route estimates did not survive extraction. Expanded routed L3 37417248117 completed: downloaded JUnit records22/22,0failures/errors/skips. This is functional verification without SDF.

## Extracted path audit and independent follow-ups (2026-10-06)

Downloaded extraction artifact37417248079 confirms119 slow setup violations and4 fast hold violations. Slow setup max report has119 failing path pairs:115 start at `_49057_` (U0 PERIOD config word4 bit10),3 at `_49139_` (U0mode word0 bit0),1 at `_46978_`. Worst path `_49057_`→`_48168_` (dropped[31]) is−1.731802ns; next dropped[30]−1.716378 and dropped[25]−1.707015. These are path-pair counts, not119 independent root causes. Live configuration remains timed.

Fast hold failures:

| Source | Destination | Slack(ns) |
|---|---|---:|
| lane0slots[634] latch `_50495_` | lane0ex_kt `_46718_` | −0.035371 |
| lane0slots[633] latch `_50494_` | lane0ex_ot[1] `_46708_` | −0.029308 |
| lane0slots[579] latch `_50270_` | lane0ex_ot[0] `_46707_` | −0.028054 |
| U0config word0 bit8 `_49101_` | U0RX sst[0] `_48522_` | −0.002471 |

Extracted electrical counts fast/slow/typ: slew3/101/13, fanout187/187/187, capacitance2/1/1. Post-route fanout now includes data drivers as well as162 clock leaves; do not apply the pre-route 'all violations are clocks' finding to this extracted report. Prepared data slew targets remain worst: `_30323_/Y` SRAM-enable4.354481ns and `_33713_/Y` lane-control3.998465ns versus2.5074ns limit. This supports separately measuring their buffers.

Dispatched existing isolated comparisons: CTS37486833508, lane buffer37487199839, SRAM buffer37487199871. Each has an independent baseline; no simultaneous combined hardware change.

Additional measurement prototype: drop_counter.patch changes only trw_chan_port's existing8-bit saturating DROPPED update to parallel per-bit toggle logic precomputed from registered state. It preserves reset, saturation, config-write/drop exclusion and clear/drop priority; no state/latency/spec addition. Late drop gating remains per-bit, targeting the actual failing endpoint cone. Yosys proves98 equivalence points atN=1/5/6/7/9/16 using equiv_simple plus successful induction;7/7fabric and5/5chip tests pass. Fresh2048-clock L2 comparison passes underVerilator and Icarus. Matched baseline/drop-counter screen uses timing-driven placement and all-corner repair. This is unmeasured until its physical results exist; no guarantee of WNS improvement or formal whole-chip claim. Raw local evidence under/tmp/drop-counter-trial-20261006.
