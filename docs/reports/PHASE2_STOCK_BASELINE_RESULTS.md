# Completed stock-flow baseline and remaining failures

Run [40042584523](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40042584523), head04e9560b6a71f5ad2a750d8153635d2d04049886, completed23:58:37–01:06:53UTC in68m16s. This is successful measurement through stock Classic before DRT, not timing/electrical qualification. Exact full2/4/U0-full/SRAM hardware,20ns,stock0.25ns uncertainty, unchanged image/scripts/checkers and official workflow.

## Actual saved evidence

Fresh stage43or_metrics_out.json reports the typical corner only:

| Metric | Value |
|---|---:|
| Setup WS |0ns|
| Hold WS |+0.246254ns|
| Slew violations |5|
| Capacitance violations |1|
| Fanout violations |180|

Stage39global routing reports3738total overflow: Metal2=19,Metal3=3657,Metal4=62, with30%layer adjustment. This precedes antenna repair; do not call it a final post-antenna congestion audit. Stage42nested fresh antenna check reports0nets/0pins after102diodes were inserted. Cumulative metrics are not substituted for fresh corner reports. There is no extracted/DRT result, and no new fast/slow result from this stock screen.

Of the180fanout violating report rows,169are clock buffers and11signal drivers. Clock-leaf loads reach17against limit8. Remaining signal failures include fanout2330,fanout2427,fanout2053,fanout2425 and seven smaller violations. The five slew rows are driven by30381/Y, with worst slew3.519276ns vs2.507400ns limit; SRAM A_DOUT[15] capacitance is0.071501pF vs0.064pF. Actual errors remain and DRT stays blocked.

## Next matched physical control

Set the documented stock project option CTS_SINK_CLUSTERING_SIZE=8. This targets169clock fanout failures without any protocol logic/state/latency change. It is the only physical-setting delta from40042584523. Leave clock spacing none, setup extra margin0, density56, GRT adjustment/default repair policies,20ns and0.25ns uncertainty unchanged. Smaller clusters can add buffers/area or change skew/congestion; measurement is required, not an assumed fix. Main adoption of project settings outside the AGENTS whitelist remains separate owner review.

## Additional read-only measurement

After the stock physical screen, use existing postgrt_timing.screen with the same final checkpoint as both inputs. It executes only stock STAMidPNR, twice at each corner, without extra Tcl, repair, placement or routing. All original state/ODB/DEF/NL/PNL/SDC files are SHA-bound and must remain unchanged. Reports must contain fresh setup/hold/slew/cap/fanout metrics at all3corners, finite values and repeatable results. Output explicitly states no physical repair, DRT or qualification performed.

The existing reader carries a legacy GRT_ADJUSTMENT0.16 config value; STA does not invoke routing or consume that routing policy. This is not a change to the physical run's0.3adjustment. Source physical hashes enforce immutability. No custom image, engine scripts, physical ECO or physical-flow step substitution is introduced.

Checks before publication: actual official TT --create-user-config passes; exact one-setting/source/workflow identities checked; pinned CTS schema accepts the field; pinned STAMidPNR declares no physical output views. Workflow shell/Python syntax passes. Executed read-only guard controls accept a complete repeatable fixture and reject source mutation, missing metrics and nonrepeatability; these are guard tests, not physical timing evidence.

Next results must show the effect on all actual counts and fresh corner timing. Congestion, signal fanout and SRAM electrical repair still need resolution even if clock clustering helps. Do not route because the diagnostic job is green.

## Clock8 run40110884653: actual three-corner results

[40110884653](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40110884653), head9be6a644ba128839aa34b65440ee51587c74bb8a, completed in71m01s. Actual repeated read-only STA passed physical-file hash immutability and supplied fresh metrics at each corner. Independently matched the receipt against all6raw or_metrics files; no inherited-corner values used.

| Corner | Setup WS ns | Hold WS ns | Slew | Cap | Signal fanout |
|---|---:|---:|---:|---:|---:|
| Fast |0|+0.0430439|0|2|14|
| Typical |0|+0.218061|5|2|14|
| Slow |-1.31005|+0.528453|50|1|14|

All169clock fanout failures are gone; remaining14rows are signal drivers. This is a useful measured improvement, not qualification. Fast hold misses50ps by6.9561ps. Slow setup fails by1.31005ns; the sampled failing path starts at unit0configuration word0bit2latch and ends at a rising-edge flop. SRAM A_DOUT[2] cap reaches0.115597pF at fast corner against0.064pF. Shared30381driver slew reaches5.661924ns at slow vs2.5074ns limit. Stage39global overflow3979precedes antenna repair; final nested antenna check is0nets/0pins after91diodes. No DRT is authorized.

## Next native electrical-repair recipe (D-112)

Test three explicit project options together:

- RUN_POST_GRT_DESIGN_REPAIR=true (currently false): execute the existing native Classic electrical-repair step.
- GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=600um (currently0): permit native buffering. The pinned schema explicitly says0inserts no buffers; this is needed when the overloaded driver is an unresizable SRAM macro.
- GRT_ADJUSTMENT=0.16 (currently0.3): expose the previously tested routing capacity while addressing measured Metal3congestion.

This is a coherent recipe test, not a single-variable attribution claim. No hardware/source/ISA/latency, clock20ns/uncertainty0.25ns, native scripts/order/image, checker or official-workflow changes. Keep clock8,spacingnone,setup extra margin0and default10%native electrical margins. Post-GRT timing repair remains disabled; that is not silently bundled in. Default resizer RSZ_CORNERS=None already inherits all3STA_CORNERS in pinned ResizerStep; changing that field alone would be a no-op. Mid-PNR reports default to typical, which is why the separate fresh audit remains necessary.

Cost/risk: buffering/sizing and rerouting may increase area, worsen hold or alter setup. Both global overflow and all fresh corner metrics must be measured again. Main adoption outside the config whitelist remains separately reviewed. Actual TT config generation, pinned-variable compilation and Classic step gating checks pass; exact3-key/source/template and shell/Python audits pass. No new physical result yet and no routing continuation.

## Native electrical-repair run40120999838

[40120999838](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40120999838), heade9bece31fbb85eafa536c17a5479f24cd810ddc4, completed in74m31s. Independently matched the repeated read-only receipt to all6fresh metric files. Source physical files remained unchanged during the audit.

| Corner | Setup WS ns | Hold WS ns | Slew | Cap | Fanout |
|---|---:|---:|---:|---:|---:|
| Fast |0|+0.015865|0|0|0|
| Typical |0|+0.150728|0|0|0|
| Slow |-0.447463|+0.383769|0|0|0|

All actual electrical counts are zero at all3corners. Saved initial and native repair final routing tables both have0overflow (final native repair usage42.38%,wirelength2497629um). Final nested antenna check0nets/0pins after37diodes. These are estimated-parasitic screen measurements, not extracted routing/signoff. Native repair pre-antenna instance area582150.36um²; buffering/sizing cost must remain part of later qualification.

Slow setup improves−1.31005→−0.447463ns, but still fails. Fast hold decreases43.0439→15.865ps, still short of50ps reserve. No DRT/phase qualification. A green diagnostic job is not an all-gates pass.

## Next stock timing-repair control (D-113)

The existing native post-GRT timing-repair step remains disabled. Enable RUN_POST_GRT_RESIZER_TIMING=true, set GRT_RESIZER_SETUP_SLACK_MARGIN=0to avoid chasing borrowed-latch50ps pseudo-margin, and GRT_RESIZER_HOLD_SLACK_MARGIN=0.125ns to target margin above the50ps acceptance gate. Those are exactly3project-field changes; all existing electrical-repair/capacity settings remain. Stock engine/scripts/order,image,full hardware,20ns,0.25ns uncertainty and checker gates unchanged. No main src/config or official-workflow edit; main adoption outside whitelist remains separate owner review.

Cost/risk: late timing repair can disturb electrical loading, antenna, routing and area. Do not assume the newly clean counts survive. Add stock CheckAntennas as a read-only measurement on the final timing-repaired checkpoint, alongside repeated3corner STA. Use only fresh raw antenna metrics and enforce source state/ODB/DEF/NL/PNL/SDC hash immutability after every audit. Do not move or insert physical repair steps in the stock flow. All physical changes remain native Classic behavior.

Actual TT configuration generation, pinned schema variable compilation/step gating, exact3-key/source/template/syntax checks pass. Audit guard controls cover clean data, missing/nonrepeatable corner metrics, physical mutations by either measurement and missing antenna metrics. These controls are synthetic guard checks, not timing evidence. Final source antenna readback must replace inherited pre-timing antenna counts before any routing decision. No automatic routing continuation.

## Final-timing run40127505533: hold reserve passes, setup/antenna regress

[40127505533](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40127505533), head8b509d918009de11af2bc8f32d6069a60e8b8731, completed in92m04s. Fresh raw metrics independently match all6corner reads and the final read-only antenna report:

| Corner | Setup WS ns | Hold WS ns | Slew/Cap/Fanout |
|---|---:|---:|---|
| Fast |0|+0.0506384|0/0/0|
| Typical |0|+0.219532|0/0/0|
| Slow |-0.750799|+0.505617|0/0/0|

Final fresh antenna has55nets/57pins. Do not inherit the earlier antenna0result. Native optimizer log reached setupWS0/hold0.125before its final full GRT, but fresh all-corner results after routing are the authority. Saved routing tables show0overflow, not absence of antenna errors. No DRT qualification.

Source-bound current netlist identifies worst endpoint48894as u_chip.dropped[28]; the reported path launches from SRAM read data14through lane0and fabric logic into this dropped-token counter. This was verified in the current44-resizertimingpostgrt netlist, not assumed from an older instance ID. Late setup repair inserted5buffers/pin swaps; hold repair inserted92buffers; final native area587270.59um²before the audit. Full GRT then changed estimated delays/antenna. No claim of an upstream tool bug follows.

## D-114: general late-select counter and earlier stock optimization

Prototype changes only trw_chan_port.v: compute each incremented counter bit independently of late drop_inc, then select it against the clear/hold value. This preserves saturation, reset, configuration-write and simultaneous drop/clear priority. No new state, latency, protocol logic or ISA change.

Verification:

- Complete module equivalence for every N=1..16,109..124equivalence points each, using Yosys equiv_simple/equiv_induct with induction sequence cap4. A known-bad clear mutation atN5is semantically rejected. This is channel-module equivalence, not whole-chip formal verification.
- Strict module lint passes.7/7fabric/channel tests, including independent-model random testing, and4/4top-level RTL tests pass with no skips on the actual variant. Independent XML readback checked counts.
- Representative N5CMOS5L mapping reduces worst src_load-to-dropped-D logic depth8→7; module area2912.3766→2966.8086um²(+54.432). This is a local mapped logic/area diagnostic, not picosecond timing or a full-chip area result.
- Exact CI prepare block replayed successfully from a clean main archive, including the base21file/macro checks followed by the single-file variant patch/hash guard. Actual TT project configuration accepts the prepared variant.

The physical candidate uses stock SYNTH_STRATEGY=DELAY0and PL_RESIZER_HOLD_SLACK_MARGIN=0.15ns; optional RUN_POST_GRT_RESIZER_TIMING=false. Other native electrical/capacity settings stay fixed. This puts synthesis/hold optimization ahead of the existing stock antenna stage, without moving/inserting/changing any physical step or script. Inactive GRT timing-margin fields remain in the config but do not enable that stage. Fresh all-corner and final antenna audits remain required.

This is a coherent source/early-optimization candidate, not attribution to a single knob. Costs: small local counter area increase plus possible DELAY0/early-hold buffering/area/congestion changes; mapped-stage improvements may not survive full-chip placement. All20ns/0.25ns constraints and acceptance gates remain fixed. The variant exists only in spike/ephemeral CI inputs, not main src. Main adoption beyond config whitelist still needs owner review. DRT remains blocked until measured requirements pass.

## Late-select/early-optimization run40162935683: not qualified

[40162935683](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40162935683), headc76a65d87b5e1914f0a14610a2f5ca0c1cc90784, completed in79m17s. Independently matched all6fresh raw metrics and final antenna receipt. Actual results:

| Corner | Setup WS ns | Hold WS ns | Slew | Cap | Fanout |
|---|---:|---:|---:|---:|---:|
| Fast |0|-0.0147214|0|0|1|
| Typical |0|+0.120423|0|0|1|
| Slow |-0.670662|+0.363867|0|0|1|

Fresh final antenna0nets/0pins. Saved initial and native-repair routing tables0overflow (post-repair usage49.41%,wirelength2928492um). The remaining signal fanout row is fanout2335/X:9against limit8 at each corner. Sampled worst slow path launches at configuration latch51769and ends at FF50687; new instance IDs require current-netlist binding before any source interpretation. This is not the prior SRAM-to-counter endpoint merely because the older source had a different critical path.

This combined candidate fails slow setup, actual fast hold and fanout. Fast hold is64.7214ps short of the50ps project gate. Do not route/promote. Formal channel equivalence and local mapped-depth improvement remain valid functional/local diagnostics, not evidence of whole-chip timing improvement. Because counter RTL, synthesis mapping and early-hold policy changed together, do not attribute the physical outcome to the counter alone. Next isolate those changes against the electrically/antenna-clean stock baseline before selecting another physical control. No new workflow launched from this status check.

## D-115: forwarded event accounting, matched physical configuration

Prototype changes only the channel's internal dropped-counter representation. Define F(count,event) as saturating increment for drop, otherwise zero for clear, otherwise hold. Store an8bitbase and two pending event bits. Public count=F(base,pending); at an edge base_next=public_count and pending_next=current_event. Therefore public_count_next=F(public_count,current_event), the original recurrence. Drop is masked by cfg_we before capture; drop still wins simultaneous clear. Reset clears all internal fields. No architectural count-readback cycle is added.

Evidence in forwarded_drop_evidence.json binds the predecessor f0cf047...and new source79ba846ddf5a8036f47ec0c42e89f26c67d0d5b29eaa27f87aaa11ffda7f6abb:

- Channel-module equivalence for allN1..16,100..115points each,using equiv_simple/equiv_induct with induction sequence cap4. Delayed-visible-count and wrong clear-priority mutants atN5both fail semantically. No whole-chip formal claim.
- Strict module lint,7channel/model tests and4topRTLcases pass, no failures/errors/skips. XML independently parsed.
- RepresentativeN5mapping: late-event path to event-register D4logic levels vs7to old counter; area3178.98vs2966.8086um²(+212.1714). Public-count readback gains6combinational levels; this is an explicit new path to measure, not free timing.
- Actual critical consumerC3usesN7. Local typical-Liberty/ideal-wire STA reports worst src_load-to-register combinational delay1.249745→0.720858ns and mapped area3449.061→3579.093um²(+130.032). These are local comparative diagnostics with OpenSTA2.6.0,4nsinput delay and6fFoutput load, not pinned-CI whole-chip slack or routed timing. N5shows1.031928→0.495255ns under the same assumptions.
- Exact updated CI prepare block successfully replayed on a clean main archive: validated original21files/macros, applied prior late-select patch, then only the expected forwarded-counter source hash changed. Actual unchanged TT --create-user-config passes. Workflow shell/embedded Python checks pass.

Physical config is byte/JSON-identical to40162935683: no synthesis/hold/timing/route-policy change. This isolates the new RTL representation. Stock image/Classic scripts/order,all20ns/0.25nsconstraints,full2/4/U0-full/SRAM and acceptance gates stay fixed; main source/official gds.yaml remain untouched. Internal cost is two state bits per consumer plus combinational readback logic. Native physical effects on host readback timing,new hold paths,clock buffering,area and fanout require the fresh3corner/antenna/congestion audits. DRT remains blocked until every required gate passes.


## 2026-10-25: matched forwarded-counter result and configuration predicate follow-up

[Run 40179640229](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40179640229) completed as a measurement job. Independent inspection matched each receipt metric to both fresh corner reports and matched final antenna counts to their fresh raw report.

| Corner | Setup WS (ns) | Hold WS (ns) | Slew | Cap | Fanout |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fast | 0 | -0.0124152 | 0 | 0 | 3 |
| Typical | 0 | +0.117042 | 0 | 0 | 3 |
| Slow | -0.780544 | +0.349326 | 0 | 0 | 3 |

Final antenna: zero violating nets/pins. Last post-GRT design-repair congestion table: total overflow 36 (initial global routing reported 42). These are pre-DRT results, not extracted signoff. Fast hold is 62.4152 ps below the 50 ps gate. Against matched predecessor 40162935683, setup worsened by 109.882 ps, fast hold improved only 2.3062 ps, and fanout failures increased from one to three. Do not route or promote this candidate. Reported setup zero on borrowing-latch paths is not evidence of positive setup reserve.

Current netlist identifies the worst slow path as U0 word0 bit1 (TXMODE), latch `_52313_`, through joint-mode decode, output pad9 feedback, selection and RX logic into U0 producer token bit3, FF `_50188_`. This differs from the predecessor's dropped-counter endpoint. Current worst fast hold is lane0 host_wdata[15], FF `_51706_`, to staged host memory write data h_wd[15], FF `_51620_`. Do not reuse older run cell IDs or classify this as the previous cfg input hold path.

Fanout failures are fanout3308/X (12 versus 8), fanout1891/X (9 versus 8), and fanout2692/X (9 versus 8). The logical-netlist roots are U0 cfg.wdata_q[2], combinational control gate `_27794_`, and lane0 host_wdata[4], respectively. Final DEF now confirms the mechanism: net3308 has ANTENNA_21..24 in addition to its eight logical sinks; net1891 adds ANTENNA_18; net2692 adds ANTENNA_20. Thus antenna repair turns exact-limit eight-load branches into 12/9/9 loads. Both exported logical and powered netlists omit those physical antenna cells, so only the DEF establishes this attribution. Next electrical work should reserve headroom before native antenna repair, retaining the actual eight-load acceptance limit and final read-only audit. Do not remove antenna cells or silently change stock step order.

Two local pin-input mux experiments were rejected: parallel terms increased representative mapped area from 1453.3344 to 1527.4224 um² while worsening worst pad-to-select ideal-wire delay from 0.659256 to 0.761983 ns. Folding selection polarity into the terms improved that delay to 0.616443 ns, but increased area to 2006.3106 um². These are small standalone typical-Liberty diagnostics with cached OpenSTA 2.6, not full-chip physical timing. Neither is queued for CI.

D-116 instead caches the existing joint TX/RX mode predicate when word0 is written. One staged predicate bit and one high-phase configuration latch per full unit replace the repeated binary-mode decode on the live pad-feedback path. All binary configuration fields and their timing remain intact. Lean units produce constant false. Unit use is parameter-gated for compatibility; the full chip explicitly selects the cache. This adds no protocol behavior, ISA operation, architectural cycle or reduced resources.

Local evidence binds the three-file patch and baseline/candidate source hashes in `spikes/phase2_stock_flow/mode_predicate_evidence.json`. Four actual-RTL temporal-induction proofs pass (full/lean, latch/flop), with alternating-clock and stable-before-rising-edge input assumptions and comparison after the first word0 write. A wrong-mode mutation fails the property. Four simulation cases compare existing cfg/restart against the predecessor, exhaust all 65,536 word0 values, and apply 10,000 seeded random write/idle/reset cycles, checking both settled phases. These are configuration-property proofs, not whole-chip formal verification. All 120 pin-unit and four top-level RTL cases pass without skips/errors; full-chip strict lint passes with unchanged existing narrow annotations.

The separate diagnostic workflow prepares this patch after the forwarded-counter baseline, with exactly three allowed source-hash changes. Physical config, stock flow/image/scripts/order, official workflow, clock/uncertainty and acceptance gates remain fixed. Exact preparation from a clean archive and shell syntax pass. The repeatable proof/simulation helper is `mode_predicate_checks/check.py BASELINE WORK`, run in the project venv; WORK must be new. The pin harness adapter is a separate test patch. No main source/config edit or DRT launch. Full-chip timing, hold, fanout, area and congestion benefits remain unmeasured; publication and physical screen are the next step under the repository's Git rule.


## 2026-10-26: mode cache clears reported setup; native antenna/hold follow-up

[40214888335](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40214888335) completed. Independently verified the receipt against both fresh raw corner reports and fresh antenna metrics. Setup WS is 0 ns at fast, typical and slow: slow improves from -0.780544 ns. This is nonnegative reported setup, not positive setup reserve on borrowing latches.

| Corner | Setup WS (ns) | Hold WS (ns) | Slew | Cap | Fanout |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fast | 0 | -0.0333446 | 0 | 0 | 3 |
| Typical | 0 | +0.0781532 | 0 | 0 | 3 |
| Slow | 0 | +0.278575 | 0 | 0 | 3 |

Final antenna nets/pins remain zero. Pre-antenna instance area is 626574 um² versus 630609 previously; count 40375 versus 40818. Last reported post-GRT electrical-repair congestion table has overflow54; this precedes antenna repair and is not a final extracted congestion result. No DRT qualification. Fast hold misses the 50 ps project gate by83.3446 ps.

Current worst reported slow path is lane0 host_sel[2] FF _50977_ to U0 carrier_active latch _51616_; the old mode-to-token failure is no longer the reported worst path. Current worst fast hold remains lane0 host_wdata[15] FF _51006_ to staged host memory write h_wd[15] FF _50920_. Bind these IDs only to this run.

Final DEF proves the current fanout roots: U0 cfg.wdata_q[5] branch fanout3295/net3295 has seven non-antenna loads plus six antenna cells ANTENNA_26..31 (13 vs8); U1 cfg.wdata_q[8] branch fanout3142/net3142 has eight non-antenna loads plus ANTENNA_63..65 (11 vs8); producer-token branch fanout2796/net2796 has eight non-antenna loads plus ANTENNA_25 (9 vs8). The stock antenna log reports26jumpers/62diodes in its first pass and19jumpers/3diodes in its second, so jumper capability already exists in the current native engine. Physical antenna cells are absent from exported logical/powered netlists; use DEF for load accounting.

D-117 tests exactly two diagnostic settings on unchanged D-116 hardware: PL_RESIZER_HOLD_SLACK_MARGIN150→250ps and GRT_ANTENNA_REPAIR_JUMPER_ONLY=true. The latter is a documented variable in pinned LibreLane3.1.0.dev3, forwarded by unchanged antenna_repair.tcl as -jumper_only. This chooses a native repair mechanism; it neither disables antenna checks nor removes existing antenna cells. New runs start from clean synthesis. The hold setting is an optimization target; the actual acceptance gate stays50psfast hold. Stock fanout8,20ns,uncertainty0.25ns,all electrical/antenna gates,image/scripts/order and official template remain fixed.

This is a paired physical-policy test, not single-knob attribution. Risks: jumpers may leave antenna violations unresolved or consume routing resources; extra hold buffers may increase area/congestion or harm setup. Schema compilation of both exact settings, clean-archive workflow preparation, source-hash identity, actual unchanged TT --create-user-config and shell syntax pass. native_antenna_hold_evidence.json binds the two-field delta and hardware hashes to40214888335. No new RTL simulation is needed for byte-identical hardware. Main src/config and official gds.yaml remain unchanged. Do not start DRT unless fresh final gates pass; physical result pending.


## 2026-10-26: jumper-only stalls; return to setup-clean baseline with banked staging

[40353011505](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40353011505) completed as a measurement job. Receipt metrics independently match both fresh raw corner reports and the fresh antenna raw report.

| Corner | Setup WS (ns) | Hold WS (ns) | Slew | Cap | Fanout |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fast | 0 | -0.00505285 | 0 | 0 | 0 |
| Typical | 0 | +0.228556 | 0 | 0 | 0 |
| Slow | -0.412522 | +0.559065 | 12 | 0 | 0 |

Final antenna45nets/50pins fails. Fast hold is55.05285ps below the50psgate. Last pre-antenna repair congestion table reports50overflow; no final/routed congestion claim. Native log: initial69antenna violations,29jumpers on25nets, then45violations; both later iterations add0jumpers and leave the same45violations. Extra iterations are not justified by this plateau. Jumper-only is not a qualified replacement for mixed repair. As this test paired two settings, do not attribute setup/hold changes to either one alone. No DRT.

Current slow path is SRAM read to channel2 last_seq FF _50704_. Current worst hold is lane0host_sel[2] FF _50977_ to lane0state[2] FF _49090_; it is not the previous host-write-data endpoint. Cell IDs are run-specific.

D-118 returns the diagnostic physical config byte-for-byte to the last all-corner setup-clean run40214888335: early hold150ps and ordinary native mixed antenna repair. Then change only trw_pin_cfg.v: split unit-local staged write data into independently enabled even/odd-word banks and feed each stored word directly from its static bank. Carrier words use their own constant-selected bank; sample-delta/mode caches and visible timing are unchanged. Separate enables prevent synthesis from merging the two staging registers. This general storage optimization targets configuration-net load/spread while retaining normal antenna repair. It does not guarantee that every producer-token fanout branch or hold path will close.

Cost before optimization:16additional FF bits per unit (64for4units), write-enable logic and extra host-data input load. Representative standalone typical-Liberty mapping: lean area6626.1888→7734.7872um², full14513.1966→15645.4956um²; one full/three lean estimated delta4458.0942um². Staging-bit5 input loads: lean10→6/5, full24→13/12. These module comparisons exclude placement/routing and do not predict actual die area, timing or antenna closure. Extra load and clock sinks can worsen hold/setup/congestion.

Actual-RTL contract proofs cover written configuration words, restart and initialized carrier/sample-delta/mode outputs at settled falling edges, using alternating clock/stable-before-rising-edge input assumptions. All four full/lean/latch/flop temporal-induction proofs pass at seq4/cap16; a wrong-bank mutation fails. Simulation compares cfg/restart/carrier/sample-delta/mode against the predecessor after both phases, exhausts all65536word0values and applies10000seeded random writes/idle/reset cycles in all4variants. All120pin-unit+4topRTLcases pass, no skips/errors, and strict full-chip lint passes. The reproducible source-bound driver and fixtures are config_banks_checks/check.py; patch/hash evidence is config_banks_evidence.json. This is not whole-chip formal verification.

Exact clean-archive CI preparation applies the bank patch after the verified mode-cache patch, allows only the expected cfg source hash change, and binds config bytes to40214888335. Main src/config and official gds.yaml remain unchanged. No raw logs committed and no phase boxes ticked. Fresh physical setup/hold/electrical/antenna/congestion must pass before DRT. New physical result pending.


## 2026-10-26: banked staging preserves setup and makes hold nominally positive

[40378317785](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40378317785) completed. Independently checked each receipt metric against both fresh raw corner reports and final antenna raw report.

| Corner | Setup WS (ns) | Hold WS (ns) | Slew | Cap | Fanout |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fast | 0 | +0.03518 | 0 | 0 | 4 |
| Typical | 0 | +0.178185 | 0 | 0 | 4 |
| Slow | 0 | +0.442697 | 0 | 0 | 4 |

Final antenna0nets/0pins. Last pre-antenna post-GRT repair congestion table has0overflow; this is not a final extracted congestion claim. Pre-antenna area636056um²/count40968 versus626574/40375 for matched40214888335: actual+9482um²/+593instances, larger than the standalone mapping estimate because physical optimization changes too. All nominal setup/hold slacks are nonnegative, but reported setup0is not positive reserve and fast hold35.18ps misses the50psgate by14.82ps. Fanout4also blocks DRT.

Final DEF identifies every extra physical antenna load: _30848_/Y drives six non-antenna pins plus ANTENNA_5..10 (12vs8); fanout3336/net3336 originates U0wdata_odd[5] with eight original loads plus ANTENNA_36..38 (11vs8); fanout3354/net3354 originates U0wdata_even[6] with eight original loads plus ANTENNA_40..42 (11vs8); fanout3350/net3350 originates U0wdata_even[9] with eight original loads plus ANTENNA_39 (9vs8). Further cfg banking alone cannot address the independent logic net _30848_. Current worst fast hold is lane0time_now[9] FF _51080_ to time_now[11] FF _51082_, on the same clock leaf. Do not reuse earlier host-path attribution.

D-119 retains exact banked hardware and native mixed antenna repair. Change only GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH600→300um and PL_RESIZER_HOLD_SLACK_MARGIN150→175ps. The shorter native buffering target aims to reduce long exposed wire segments before antenna repair; the modest hold-target increment addresses the remaining14.82psfast deficit. This is a paired physical recipe, not single-setting causal attribution. It may still leave antenna/fanout failures and can increase area/congestion or regress setup/skew. The unsuccessful250ps/jumper-only result does not prove175pswill work.

Pinned LibreLane3.1.0.dev3 schema compilation, exact clean-archive source/config preparation, shell syntax and unchanged hardware hashes pass. Actual unchanged TT config generation also passes. No RTL retest is needed for unchanged hardware; prior bank proofs/124regression cases remain applicable. wire300_hold175_evidence.json binds the baseline/candidate config hashes and exactly two fields. Stock20ns/0.25ns,fanout8,fast hold50ps and all final electrical/antenna gates remain fixed; official workflow/main src/config untouched. No DRT or phase completion claim. New physical result pending.


## 2026-10-26: wire300 clears final electrical/antenna; hold-only control

[40399598426](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40399598426) completed. Every receipt metric was independently matched to both fresh raw corner reports and fresh final antenna raw metrics.

| Corner | Setup WS (ns) | Hold WS (ns) | Slew | Cap | Fanout |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fast | 0 | -0.00375733 | 0 | 0 | 0 |
| Typical | 0 | +0.124138 | 0 | 0 | 0 |
| Slow | 0 | +0.355552 | 0 | 0 | 0 |

Final antenna0nets/0pins; last pre-antenna electrical-repair congestion report0overflow. Reported setup is nonnegative, not positive reserve. Fast hold misses the50psgate by53.75733ps; detailed routing remains blocked. Post-route/physical signoff has not been performed.

Current worst fast path: lane0host_wdata[11] FF _51576_ to h_wd[11] FF _51490_. Native post-CTS repair explicitly loads all3corners, repairs with hold_margin0.175/max_buffer_percent50, inserts4670hold buffers and finishes at0.175nsWNS before subsequent placement/routing/electrical/antenna work. It does not hit its buffer limit. Final worst endpoints differ, so do not claim the entire slack difference is one path's loss. Increasing buffer-count limits or changing corner lists is unsupported by this evidence.

D-120 changes exactly one diagnostic setting versus40399598426: early hold target175→250ps. Keep wire300,banked/mode-cache RTL,native mixed antenna repair and all other settings byte-identical. The additional75psearly target is intended to cover the remaining53.75733psfinal deficit; no guaranteed linear gain. Earlier250psresults used different hardware/wire/antenna policy and do not answer this matched control. Added buffers can still regress setup,area,congestion,electrical or antenna closure.

Pinned schema,exact clean-archive CI preparation,source hashes,shell syntax and actual TT config pass. No RTL simulation rerun is needed on identical hardware. wire300_hold250_evidence.json links the baseline/candidate hashes to the preceding wire300control. Main hardware/config,official GDS workflow,20ns/0.25ns/fanout8/50psfast hold gates,stock scripts/order/image and final audits remain unchanged. No DRT or phase completion claim; new physical result pending.


## 2026-10-26: hold250 yields43.7279ps; preserve clean electrical/antenna

[40410841468](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40410841468) completed. Independent inspection matches the receipt to both fresh raw corner reports and fresh final antenna metrics.

| Corner | Setup WS (ns) | Hold WS (ns) | Slew | Cap | Fanout |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fast | 0 | +0.0437279 | 0 | 0 | 0 |
| Typical | 0 | +0.200147 | 0 | 0 | 0 |
| Slow | 0 | +0.469578 | 0 | 0 | 0 |

Final antenna0nets/0pins. All nominal timing slacks nonnegative, but setup0is not positive reserve and fast hold43.7279psstill misses50psby6.2721ps. Initial GRT final report9overflow; last post-GRT electrical-repair/pre-antenna report44overflow,concentrated43onMetal3and1onMetal4. This is not a final extracted congestion measure, nor evidence for clean DRT. No DRT qualification.

Pre-antenna area683548um²/count44654 versus656895/42934 at175psearly hold: +26653um²/+1720instances. Hold improves47.48523psfor75psadditional early target, but the response is not guaranteed linear. Global routing explicitly exhausts extra iterations50/50 in both stages. This justifies testing more routing effort, not claiming a larger budget will solve local capacity pressure.

D-121changes exactly two diagnostic settings versus this run: PL_RESIZER_HOLD_SLACK_MARGIN250→275ps and GRT_OVERFLOW_ITERS default/resolved50→explicit100. Preserve wire300,all banked/mode-cache hardware,mixed antenna repair and other policies. The modest25psincrement targets the remaining6.2721psreserve gap; extra native routing effort targets observed overflow. This is a paired physical control,not single-setting attribution. Risks: further area/buffers/routing pressure,setup/hold/antenna/electrical regression and additional runtime. Acceptance limits,congestion allowance,clock/uncertainty,stock scripts/order/image and official workflow are unchanged.

Pinned variable compilation,exact clean-archive preparation/source hashes,shell syntax and actual TT config generation pass. No RTL test rerun for byte-identical hardware. wire300_hold275_iter100_evidence.json binds baseline/candidate config hashes and exact two-field delta. Main source/config and official GDS workflow untouched; all final physical gates still require measurement. New result pending; no phase boxes ticked.
