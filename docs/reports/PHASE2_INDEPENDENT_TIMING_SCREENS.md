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
