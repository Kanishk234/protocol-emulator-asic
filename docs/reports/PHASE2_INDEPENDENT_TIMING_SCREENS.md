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

Buffer screens37487199839 and37487199871 completed diagnostic execution. Fresh setup WS0 in each corner. Hold lane fast/slow/typ +0.0442855/+0.244449/+0.110765ns; SRAM +0.051976/+0.264066/+0.138096ns; paired unchanged baselines reproduce +0.0364431/+0.253126/+0.123275ns. Setup/hold estimates alone do not establish reduced slew, congestion or actual routed gain. Electrical/overflow artifact audit pending. Counter screen37489333139 dispatched; local million-clock L2 ongoing, not yet a million-clock pass.

### Matched buffer electrical audit

Downloaded one unchanged baseline and both variants. Slow slew violations baseline3, lane3, SRAM1 (fast/typ0 in all); fanout162 and cap0 per corner in all. All setup/hold counts zero. The unchanged extra repair already reduced source slew8→3, so lane's8→3 is not attributable to its buffer. SRAM improves3→1 against the matched baseline. Final GRT overflow0 in all, demand baseline233,813, lane233,894, SRAM234,477. Instance area baseline508,689µm², lane508,556, SRAM508,687; secondary resizer changes mean these are whole-screen costs, not isolated buffer areas. Prefer SRAM over lane on this evidence, but no extracted gain is established.

Pinned local slow Liberty also contains NOR4_2 with identical `!(A+B+C+D)` function: area21.7728µm² vs NOR4_1 10.8864; BUF4 area14.5152. A separately measured driver-strength change is available if buffered routing proves inadequate; no such sizing trial has been implemented or launched.

The extracted final instance area892,500µm² includes383,267µm² of fill cells. Standard cells463,924 plus SRAM45,309.3 total509,233.3µm², about56.43% of902,417µm² core. Do not mistake filler-inclusive area for logic utilization or guaranteed ECO capacity.

Selected SRAM-buffer screen37487199871 for separate guarded routing; generalized existing gds-placement-route's dispatch inputs to accept audited placement/lane/SRAM source artifacts. The continuation validates source workflow/ID/main branch, exact source state, actual timing-driven placement, all-corner repair and the selected buffer's presence before antenna/timing guards. No combination with CTS or counter variants. Existing automatic extraction/L3 remain tied to that successful route. Twenty-eight gate/extraction/GL helper checks and workflow parse checks passed.

CTS comparison37486833508 completed: cluster8 estimated setup0 but fast hold−0.00424344ns, slow+0.195752 andtyp+0.0863023ns. Baseline fast hold+0.0360107ns. Do not advance cluster8 to routing with this failing hold result. Electrical/fanout artifact audit remains pending. Counter prototype million-clock L2 now passes:1,000,000clocks,zero divergences,JUnit1case0failures/errors,956.26s underVerilator. SRAM route and counter screen remain active; actual WNS is unchanged.

Downloaded CTS37486833508 artifact changes the hold-only assessment: cluster8 reduces estimated fanout violations162→4, slow slew8→0 (all-corner slew/cap0), final GRT overflow0. Area514,551µm² and33,464instances;31hold buffers in last repair. Fresh setup/hold counts all0 except one fast hold violation `_46919_`→SRAM macro,−0.00424344ns. This merits a bounded hold-repair follow-up with unchanged constraints, not rejection or direct routing. Estimated electrical improvements are not extracted signoff. SRAM route still active; counter baseline finished, variant pending at query.


### Completed counter screen and bounded CTS follow-up (2026-10-06)

Counter run [37489333139](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37489333139) passes fresh estimated setup and hold at all three corners. Setup WS is 0; hold WS is +0.0234049 ns fast, +0.203146 ns slow and +0.0996158 ns typical, with zero violation counts. Candidate slow slew count is 9 versus matched baseline 8; fanout is 158 at each corner versus 162; capacitance violations are zero. Repaired candidate area is 508,489 µm² with 33,077 instances. These mixed electrical results and passing estimated timing do not establish an extracted setup improvement.

Local CI commit `54388c8` extends the existing placement-route workflow to a validated CTS-cluster8 source. It performs exactly one additional all-corner repair with unchanged signoff constraints, then requires fresh setup/hold checks before antenna repair and detailed routing. Thirty-nine helper tests pass. Publication and dispatch remain pending: automatic approval review rejected the exact push to `main`; explicit authorization was requested. SRAM route37490897034 remains active. Actual extracted setup WNS remains −1.731802 ns.


The user subsequently explicitly approved the push. Commit `54388c8` is published, and CTS follow-up [37496347122](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37496347122) was dispatched with source37486833508/variantcts. SRAM route37490897034 remains in progress; no new extracted WNS is available.


### SRAM-buffer extracted result (2026-10-06)

Extracted diagnostic [37499559422](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37499559422), following successful SRAM-buffer route37490897034, reports slow setup WS **−1.385050335848 ns**, compared with −1.731802306133 ns on the previous routed placement trial (0.346751970285 ns improvement). Fast and typical setup WS are0. Hold WS is positive at every corner: fast+0.050187910803 ns, slow+0.247750382777 ns, typical+0.123471236730 ns. These are fresh extracted measurements; setup still fails and diagnostic workflow success is not signoff. Routed GL and CTS follow-up remain pending at this check.


### Clock clustering does not survive extraction (2026-10-06)

CTS follow-up route37496347122 completed, but extracted37502135749 reports slow setup−1.996168620234ns and fast hold−0.004409972512ns; slow/typical hold remain+0.196984101273/+0.072321928270ns. This regresses against the SRAM-buffer trial and fails signoff despite its repaired pre-route gates. Do not promote cluster8 from diagnostic success. New independent structural prototypes and local delay priorities are recorded in PHASE2_TIMING_PROTOTYPES.md.
