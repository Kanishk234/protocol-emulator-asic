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
