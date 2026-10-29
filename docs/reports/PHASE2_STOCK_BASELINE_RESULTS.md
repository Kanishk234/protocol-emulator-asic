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


## 2026-10-26: 275ps/100-iteration diagnostic times out after saving physical state

[40427663913](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40427663913) failed because our diagnostic physical step reached its145minute deadline. Direct job log: antenna insertion finishes and saves ODB/DEF/state at03:04:22UTC; native CheckAntennas begins03:04:23; timeout fires03:04:27. This is not a tool-crash or final timing-gate diagnosis. The physical repair log reports0remaining antenna nets after17diodes and27jumpers, but fresh final corner/antenna audits did not complete. Do not infer timing closure or inherit older corner metrics.

The last pre-antenna electrical-repair routing report has61overflow,so extra effort has not established clean routing. It is paired with a larger hold target; no single-knob attribution. Last fully audited fast hold remains43.7279psfrom40410841468,not a new measurement for this failed run.

The final physical checkpoint is intact at43-openroad-repairantennas/1-openroad-diodeinsertion/state_out.json in artifact12706452587(99767800bytes). Downloaded and verified48source/config/macro/state/view files; recovery_40427663913.json binds their hashes,run/head/artifact identity and actual tool versions. Required physical formats exist; no DRT occurred. The checkpoint's metrics/SDF are not used as fresh timing evidence.

D-122adds a separate read-only recovery workflow. It validates actual GitHub provenance,checks artifact bytes before and after restoring original runner paths,retains the exact saved state,then runs the same repeated3corner stock STAMidPNR and fresh CheckAntennas audit. It rechecks original physical hashes plus all48frozen inputs after measurement. No repair,placement,routing,state-path rewriting,custom runtime,image override,SDC/checker/acceptance change or official-template edit. The original failed job remains failed; recovered evidence has its own run ID and does not constitute official GDS or routing qualification.

Recovery pins actual source-run TT tools d66cf179e7bc4d296362ab7e2e3b344dc3c4f665,installer3412659307918422f3f0727917cf9b499aaca588,and unmodified stock image digest sha256:d109140b8f17fc54f4fca998beb8124f4949404ec52e339eebd2250854a18b5a with LibreLane3.1.0.dev3. Docker pulls the ordinary stock tag and verifies its digest; no replacement image. Actual GitHub metadata/48file hashes pass locally;12validator tests reject stale provenance,expired/changed artifacts,missing/changed/unbound views,unsafe paths,wrong runner/recipe and unexpected DRT. Both workflows' shell and embedded Python parse. Full stock physical measurement remains CI-only because this local environment has no Docker/full PDK.

Our diagnostic screen budget is corrected independently: physical step145→190minutes,read-only audit20→30minutes,total job170→240minutes. All physical settings/gates remain unchanged and official gds.yaml untouched. Do not repeat the expensive physical run merely to collect missing read-only measurements. Fresh recovered results pending; no phase boxes ticked and no DRT.


## 2026-10-26: recovered frozen checkpoint reports48.4025psfast hold

[Audit40445418882](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40445418882) successfully measured the exact final physical checkpoint from failed/timed-out40427663913. Independently matched every receipt metric to both fresh raw corner reports and fresh final antenna metrics. Receipt physical-view hashes match recovery_40427663913.json; CI also revalidates all48frozen inputs after audit. No physical repair/state rewrite occurred. The source screen remains failed; audit success is measurement completion only.

| Corner | Setup WS (ns) | Hold WS (ns) | Slew | Cap | Fanout |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fast | 0 | +0.0484025 | 0 | 0 | 0 |
| Typical | 0 | +0.209688 | 0 | 0 | 0 |
| Slow | 0 | +0.491882 | 0 | 0 | 0 |

Final antenna0nets/0pins. Fast48.4025psmisses50psgate by1.5975ps; do not round it into a pass. Setup0is not positive reserve. Known last pre-antenna routing report61overflow remains unresolved,not a final extracted congestion measure or clean-routing claim. No DRT/official qualification.

D-123keeps this baseline hardware/config intact and adds two independent one-setting controls through a choice input on our existing diagnostic workflow. hold300changes only early hold275→300ps. density54changes only placement density56→54percent,retaining275pshold. They run separately from the same baseline; there is no combined case and no rerun of the unchanged baseline. Per-profile concurrency permits both controls to progress independently. stock_control_profiles.json binds each exact config hash/delta to physical40427663913/audit40445418882; each run emits selected_profile.json. No RTL/macro/clock/SDC/gate or official workflow changes.

The hold case can add area/routing pressure and regress other gates; the density case can lengthen wires/change skew and regress timing/antenna. Neither guarantees closure. Pinned schema compilation,baseline+bothcase clean-archive preparation/exact delta/source hashes,unknown-profile rejection,shell/Python syntax and actual TT config generation for both variants pass. No RTL test rerun on byte-identical sources. Physical results pending. Diagnostic190/30/240minute budgets retained; all final gates and DRT guard remain fixed.


## 2026-10-27: independent controls finish; density54 is a proven no-op

Both measurement jobs completed. Each receipt independently matches both fresh raw corner reports and fresh final antenna metrics.

| Control/run | Fast hold (ps) | Typical hold (ns) | Slow hold (ns) | Setup all corners | Electrical/antenna | Last pre-antenna overflow |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| Recovered baseline40445418882/source40427663913 | 48.4025 | 0.209688 | 0.491882 | 0ns | 0 | 61 |
| hold30040447369799 | 31.7554 | 0.184833 | 0.458112 | 0ns | 0 | 106 |
| density5440447377789 | 48.4025 | 0.209688 | 0.491882 | 0ns | 0 | 61 |

hold300 worsens fast hold16.6471ps and increases pre-antenna area from691292um²/45161instances to698793/45649(+7501um²/+488instances). More early hold margin is not monotonic improvement. No DRT qualification; setup0is nonnegative reported slack,not positive reserve.

Density root cause is explicit native GPL-0302: the real command requests-density0.54,but cell/free-area constraints force uniform minimum0.6100. Requested56%baseline is also below that minimum. NativeGPLreports515394.112um²movable adjusted area/847190.5344um²free area(~60.836%),rounding minimum to61%. Actual density54 ODB/DEF/NL/PNL/SDC hashes are all byte-identical to the frozen baseline,not just equal rounded slack. Do not interpret this as a real physical perturbation or launch more lower-density requests. Source config/resolved values alone were insufficient to prove effect (BUG150).

D-124 retires these two choices and prepares two independent native alternatives against the same unchanged baseline:

- wire400: only GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH300→400um. Test fewer maximum-length repeaters/lower buffer pressure,with possible electrical/antenna/setup/hold regressions on longer segments.
- late75: enable RUN_POST_GRT_RESIZER_TIMING and set GRT_RESIZER_HOLD_SLACK_MARGIN125inactive→75psactive. Early hold remains275ps; native setup margin remains0 and both native full-routing calls remain enabled. This targets actual routed parasitics rather than continuing global early reserve increases. Stock ordering places this repair after antenna repair; D-113previously reintroduced antenna errors. That risk remains explicit,with fresh final antenna/electrical/timing audits mandatory. No tool/script/order/SDC/checker changes or rerouting disablement.

The shared job budget becomes300minutes; only late75gets240minutesphysical,otherprofiles190; read-only audit30minutes. Official job budgets remain untouched. Profiles/config/source hashes remain guarded and both actual TT merged configs retain selected values. New stock_profile_effective validator checks resolved settings,native wire-length command,late-step existence/hold command and enabled rerouting; it records actual GPL density and rejects clamped density-control requests. Eight guard tests pass; it accepts the real existing300um command and rejects the actual density54log. Baseline+bothcandidate exact preparation,schema/shell/Python syntax,unknown-profile rejection and actual TT configs pass. No RTL tests repeated for byte-identical hardware. Results unmeasured; no DRT or phase boxes ticked.


## 2026-10-27: native late75 passes timing/electrical; antenna and congestion remain

Both wire40040459596311andlate7540459607737measurement jobs complete. Each receipt independently matches both fresh raw corner reports and fresh final antenna raw metrics.

| Control | Fast hold (ps) | Typical hold (ns) | Slow hold (ns) | Setup all corners | Electrical | Antenna nets/pins | Last reported overflow |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| wire400 | 36.7189 | 0.188058 | 0.457483 | 0ns | one fanout,other counts0 | 0/0 | 48(before antenna) |
| late75 | 84.0735 | 0.265309 | 0.581982 | 0ns | all0 | 31/31 | 68(after late reroute) |

Late75clears all reported timing/electrical gates,including50psfast hold,but still fails antenna and routing readiness. Setup0does not establish positive reserve. No DRT. The late resizer upsizes one cell and adds only18hold buffers,versus blanket early-repair growth. Effective-profile evidence verifies the75psnative command and the enabled stock step/rerouting.

Antenna analysis is source-bound in late75_antenna_evidence.json:32summary rows cover31unique net/pin pairs. Every failing pair existed before late repair,with unchanged sink type and connection. Earlier repair used27routing jumpers and17physical diodes. Late full routing can replace jumper routes; physical diodes remain instantiated. This supports testing persistent protection,not a guarantee of closure or proof that only one reroute operation caused each marker. Prior BUG144's antenna-after-reroute risk has recurred.

D-125compares two independent single-additional-setting controls against measuredlate75(configSHAverified against the actual selected-profile artifact):

- late_diodes adds GRT_ANTENNA_REPAIR_DIODE_ONLY=true. Keep75pslate/275psearly,mixed-mode alternative disabled,wire300/iteration100/reserve16%unchanged. Native diode-only protection can survive rerouting but extra loads may reintroduce fanout/cap/setup failures or leave antenna errors.
- late_grt15 changes GRT_ADJUSTMENT0.16→0.15 with original mixed antenna repair and same late75timing policy. This reduces global-router capacity reservation by one percentage point; it is an optimization-model change,not a physical spacing/DRC waiver. More optimistic routing capacity does not prove detailed routability. Current per-layer overrides are all0; original/derated resources and native reported adjustment are captured for review. Historical native0.30/0.16resource tables and primary OpenROAD source support the global fallback behavior; no further ineffective-density experiment.

No combined case or baseline rerun. Existing native full rerouting/order,image,20ns/0.25ns/fanout8/50psfast hold and all acceptance checks remain. Exact source/config preparation,baseline/reference/bothcase hashes/deltas,unknown-profile rejection,pinned schema,actual TTmerged values and shell/Python syntax pass. Twelve effective-control tests plus ten audit-adjustment guards pass; actual native late75/16%resource logs validate. Actual mixed-mode source correctly rejects a diode-only claim.

The shared STA helper now optionally preserves an explicit source GRTvalue only for same-checkpoint read-only audits. Legacy callers retain0.16exactly; physical-repair/different-checkpoint overrides reject. This keeps routing metadata faithful for the15%case without invoking any routing or changing saved views. Normal fresh3corner/repeatability/antenna/source-hash safeguards remain. No RTL retest on identical hardware; main source/config and official gds.yaml untouched. New physical results pending; no phase boxes ticked.


## 2026-10-27: independent late diode and routing-reserve controls

Both measurement jobs completed successfully on aabca3379b9f28431a4da6128211a1fe2b19bbcc. Independently matched every reported corner metric to both before/after raw STA metrics and fresh antenna counts to raw antenna metrics. Effective-control receipts confirm native diode-only mode and actual 15% routing adjustment respectively.

| Run/control | Setup F/T/S (ns) | Hold F/T/S (ns) | Electrical | Antenna nets/pins | Final late-routing overflow |
| --- | --- | --- | --- | --- | ---: |
| [40538578732 late_diodes](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40538578732) | 0/0/0 | 0.0726524 / 0.244946 / 0.536568 | all zero | 23/23 | 71 |
| [40538583444 late_grt15](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40538583444) | 0/0/0 | 0.099026 / 0.288230 / 0.625223 | two slow-corner slew violations; others zero | 28/28 | 83 |

Compared with late75 (31 antenna / 68 overflow / fast 84.0735 ps), diode-only reduces antenna count but does not eliminate it; congestion and hold reserve worsen slightly. The 15% routing reservation increases actual derated resources by only 529 tracks (258 Metal2, 34 Metal3, 237 Metal4); capacity is discrete. It improves hold but worsens measured overflow and introduces two slew violations. Neither qualifies for DRT. Setup zero remains nonnegative reported slack without demonstrated positive reserve. Job success means measurement completion only.

Do not combine these settings or launch routing based on green workflow badges. Next inspect residual antenna net/pin identities and pre/post-late diode connectivity, plus spatial overflow attribution. Establish whether violations concern protected existing nets or newly exposed nets before selecting another repair/placement control. Main hardware/config and official GDS workflow remain unchanged; no phase checklist boxes ticked.


### Residual analysis and next controls

Exact pre/post-late DEF connectivity proves all 45 diode instances remain on their original nets. All 23 final failing net/pin pairs existed before late repair; 22 have no diode. For the remaining net, u_chip.g_lane[0].ot[11], the detailed report violates the Metal2 cumulative ratio (349.70 against 200), while Metal3 has a much larger diode-dependent allowance. A diode somewhere on a net does not establish protection at every lower-layer branch. Earlier stage43 also retains one failure (_03256_, wire13975/A). Derived evidence with input hashes is late_diodes_residual_evidence.json.

Final congestion is 70 overflow on Metal3 and one on Metal4. No spatial congestion map is saved in this artifact, so a location-specific hotspot conclusion is not yet supported. Thirteen thousand and sixty-two timing-repair buffers appear before late repair, motivating a reduction in early repair pressure rather than another global capacity-reservation reduction.

D-126 prepares late_ant50 (native antenna-repair margin 10→50%) and late_early175 (early hold target 275→175 ps), independently against measured diode-only late75. The latter keeps the late 75 ps repair target and every final timing requirement. The former changes a native optimization margin, not the checker rule. More margin is not guaranteed to cover newly exposed geometry; lower early margin can increase late work or regress slack. No combined case or DRT launch.

Pinned LibreLane variable definitions and scripts support both controls. OpenROAD describes ratio_margin as added antenna repair margin and placement-estimated repair margins as compensation for parasitic estimation: [global routing](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html), [resizer](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html). Current public documentation is explanatory; the pinned native engine remains authoritative. Twenty-six guard tests pass; actual native values are audited in CI.


## 2026-10-27: lower early hold target clears global-routing overflow

[late_early175 40570933800](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40570933800) completed successfully as a measurement job on c881dfd. Artifact12773650518, size249040508bytes. Independently matched repeated before/after raw STA metrics for all three corners and raw fresh antenna metrics to receipt. Effective control confirms native early175ps, late75ps and diode-only repair.

Setup WS remains0nsallcorners. Hold fast/typ/slow is0.061944/0.227600/0.522836ns, clearing50psfastgate. Cap/fanout0allcorners; slow corner has two slew violations: fanout1194/A 2.941708ns and _35613_/Y 2.937792ns versus2.507400nslimit. Antenna23nets/24pins. Final late full GRT reports0overflow on every layer (previous diode-only71). Final area658184.60um²/43043instances versus691585.89/45209: reduction33401.29um²and2166instances (~4.83%area). Final timing-repair buffers10899; last native late repair inserts19holdbuffers. This supports lower early buffer pressure, not final physical signoff.

This candidate still fails electrical/antenna gates; no DRT. Setup0does not establish positive reserve. Antenna-margin50screen40570929866remainsrunning at check. Next inspect that result and classify lower-pressure candidate's residual antenna/slew sources before selecting any combined or further setting. Official workflow/main hardware unchanged.


## 2026-10-27: antenna margin50 is physically ineffective on the measured reference

[late_ant50 40570929866](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40570929866) completed as a successful measurement job. Artifact12778805602 (258288020bytes), source c881dfd. Repeated fresh before/after raw three-corner metrics and fresh raw antenna metrics independently match the receipt. Effective command audit confirms native ratio_margin50.

Setup0nsallcorners; hold F/T/S0.0726524/0.244946/0.536568ns; electrical0; antenna23nets/23pins; final late overflow71. All five final physical-view hashes (ODB,DEF,NL,PNL,SDC) and source state hash equal measured diode-only reference40538578732 exactly. The parameter was exercised but did not change the saved physical result. Do not claim increased protection or combine this control expecting an improvement. The engine-level reason for the no-op remains unproven; no upstream defect claim.

The lower-early-hold candidate40570933800 remains the useful physical direction: setup0,fast61.944ps,finaloverflow0,area658184.60um²,with two slow slew violations and23antenna nets/24pins. Next diagnose the two slew pins and residual antenna topology on that candidate, then choose a control with demonstrated effect. No detailed routing or new workflow dispatched for this result; main hardware/official GDS unchanged.


### Zero-overflow residuals and D-127 controls

On40570933800, the two slow slew pins belong to the same net _08808_: sg13cmos5l_nor4_1 _35613_/Y drives sg13cmos5l_buf_1 fanout1194/A. Their final DEF cell origins differ by236.94um Manhattan distance. Slews2.937792/2.941708ns exceed2.507400ns. All24antenna entries (23nets) existed unchanged before late repair;23entries have no diode. Twenty entries are on nets whose cell-origin bounding-box Manhattan span exceeds200um. Source hashes and derived rows are in early175_residual_evidence.json. These spans do not measure routed wirelength, pin geometry or antenna ratios, and do not guarantee repair coverage.

D-127 tests late_wire200 (post-GRT maximum wire-length target300→200um) and late_slew30 (native slew repair margin10→30%), independently against measured early175/late75 diode-only. Both retain all timing/electrical/antenna/congestion gates. The pinned repair script forwards these exact values to repair_design; [OpenROAD resizer documentation](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html) explains long-wire buffering and slew repair. No newer commands are backported. Added buffers/drive strength may cost area/congestion or regress hold/antenna; final physical results are needed.

Do not combine the ineffective antenna50control. Broad heuristic diode insertion was evaluated but not launched: default90umthreshold gives an approximate7412longnets/37484terminals by cell origins, potentially~204030um²in diodes before native skips/actual pin geometry. This rough upper-pressure estimate argues against indiscriminate insertion on an area-constrained candidate; it is not a validated diode count. No custom post-route edits or official workflow changes. Twenty-eight focused guards and exact clean preparations/source/hash/delta/TTmerge/syntax checks pass. New physical results pending.


## 2026-10-27: wire200 reduces antenna and electrical failures; slew30 is unchanged

Both measurement jobs completed on24e996d. Retrieved bounded artifacts12786347392 (wire200,255030752bytes) and12783710710 (slew30,249040635bytes). Independently matched every corner metric against both repeated raw STA reports and final antenna counts against raw fresh antenna metrics. Native command receipts confirm200umwire target and30%slew margin.

| Run/control | Setup F/T/S (ns) | Hold F/T/S (ns) | Electrical | Antenna nets/pins | Final global overflow |
| --- | --- | --- | --- | --- | ---: |
| [40602600864 wire200](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40602600864) | 0/0/0 | -0.0255704 / 0.206156 / 0.535035 | all0 | 7/7 | 0 |
| [40602604357 slew30](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40602604357) | 0/0/0 | 0.061944 / 0.227600 / 0.522836 | two slow slew | 23/24 | 0 |

Wire200 is a real physical improvement for antenna (23→7nets) and electrical (2→0), preserving zero global overflow. It costs20,016.46um²and2355instances against early175reference (final678201.06um²/45398instances). Fast hold is25.5704psnegative and75.5704psshort of50psgate. Native late repair inserts70holdbuffers and reports final75psbefore its subsequent placement/rerouting; fresh final audit regresses. These are stage-level worst-slack measurements, not a proven same-path100.5704psdelay change. Fresh worst path starts latch_53493_andendsFF_49585_. No DRT.

Remaining antenna net/pin/layer entries: u_chip.g_lane[0\].ot[10\]/hold11032/A/Metal2; net2838/_47396_/A/Metal2; u_chip.g_unit[3\].u_cfg.wdata_odd[2\]/hold9026/A/Metal2; u_chip.g_unit[3\].u_prod.tok[12\]/hold9454/A/Metal2; net14151/hold8488/A/Metal2; net10021/fanout3415/A/Metal3; net13162/wire13162/A/Metal3; net2838/_47396_/A/Metal3. These identities must be source-bound before any targeted edit. No claim that a shorter target is a hard routed-length bound or that further shortening guarantees repair.

Slew30 executes the30%native margin but finalODB/DEF/NL/PNL/SDCand source state hashes equal early175reference40570933800exactly. Retire this physically ineffective setting; do not combine it as a fix. Root internal reason is unproven.

Next focus on wire200's newly failing fast-hold path and seven antenna connections, preserving zero electrical/overflow. All existing acceptance gates/main hardware/official GDS remain unchanged; no new workflow or detailed routing dispatched for this result. Setup0is not positive reserve.


### D-128: final hold versus residual antenna exposure

All seven antenna connections on wire200 existed before late repair. Six nets have no diode; the lane0output net has a diode but still violates Metal2. Four failing sinks are delay-cell inputs. The repeated net2838row covers the same sink on two layers, so eight report rows are seven unique net/pin pairs, not eight failing pins. Source hashes and identities are recorded in wire200_residual_evidence.json.

Worst fast hold path: slot latch_53493_/Q→register_49585_/D. Launch clock0.520143ns, capture clock0.895424ns (375.281psdifference), data arrival1.095739ns, data required1.121309ns. Fixed250psuncertainty and library hold apply normally. The path has several logic gates, not merely a direct short feedthrough. Native late stage reports75psbefore final placement/rerouting; exact same-path before/after drift has not been proved.

Prepare two independent one-setting controls: late_hold175 raises late native hold target75→175ps on wire200, while late_wire150 lowers the native wire target200→150um with late75psunchanged. Neither combines the ineffective slew30orantenna50settings. A100pstarget increment is not a guaranteed final100psgain. Every fresh final gate remains mandatory, including electrical0,antenna0,fast≥50psand congestion readiness. Costs are additional delay/long-wire buffers, area/congestion and possible setup/hold/antenna regressions. No detailed routing or official-flow change.


## 2026-10-28: extra late hold reserve and wire150 do not close the screen

Both jobs complete as successful measurement runs on e78b862. Bounded artifacts12792081917 (hold175,255025981bytes) and12793966701 (wire150,261167331bytes) retrieved. Independently matched all three-corner receipt metrics against both repeated raw STA reports and antenna counts against fresh raw metrics. Native command receipts confirm the selected controls.

| Run/control | Setup F/T/S (ns) | Hold F/T/S (ns) | Electrical | Antenna nets/pins | Final global overflow |
| --- | --- | --- | --- | --- | ---: |
| [40621704922 late_hold175](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40621704922) | 0/0/-0.583896 | 0.102520 / 0.337720 / 0.737308 | all0 | 11/12 | 5 |
| [40621707923 late_wire150](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40621707923) | 0/0/0 | -0.164690 / 0.027338 / 0.386555 | all0 | 5/5 | 9 |

Hold175 improves fast hold by128.0904ps relative to wire200, but loses slow setup and worsens antenna/congestion. Final area685386.09um²/45838instances, +7185.03um²/+440instances against wire200. Wire150 reduces antenna7→5nets but fast hold worsens139.1196ps and overflow returns. Final area690335.77um²/47694instances, +12134.71um²/+2296instances against wire200. Neither is a qualified replacement for wire200, and combining them is not supported by the data.

The best reference for further residual analysis remains wire20040602600864: electrical0/overflow0/seven antenna nets, but negative fast hold. It also does not qualify. Next inspect new slow setup paths from hold175 and fast launch/capture paths from wire150 alongside wire200 before selecting another physical experiment; do not assume another margin increment is sufficient. Main hardware/clock/constraints/official workflow unchanged. No DRT, phase checklist tick or new run dispatched in this result review.


## 2026-10-28: coupled-path diagnosis and strict qualification

The failed slow setup path in hold175run40621704922 launches from SRAM A_DOUT[11] and ends at_49700_/D. New hold15671,hold15800,hold15681,hold15682andhold15683instances are absent before late repair and present afterward. Their final slow cell arcs are0.737336,0.660899,0.644429,0.651298and0.659160ns (sum3.353122ns). They are significant delay on the setup-critical path. This does not prove the entire before/after change is that sum: routing, other cells and clock paths also change. ResizerStep's default RSZ_CORNERS=None loads all STA_CORNERS, confirmed by native logs; setting a missing corner list is not the supported fix.

D-129 independently tests native clock-level balancing and a single-cell exclusion against wire200. [OpenROAD CTS documentation](https://openroad.readthedocs.io/en/latest/main/src/cts/README.html) describes balance_levels as attempting similar depth across non-register cells such as clock gates. Pinned LibreLane forwards CTS_BALANCE_LEVELS directly. EXTRA_EXCLUDED_CELLS is supported by pinned synthesis and PnR code and applies globally, not only to late hold repair. Exclude only sg13cmos5l_dlygate4sd3_1; smaller delay/buffer choices remain. Both mechanisms have area/congestion/timing risks and neither is claimed to close the screen. Main RTL/resources/protocol behavior, native tool/order/full rerouting and every timing constraint remain fixed.

The workflow now runs stock_screen_gate.py after fresh audits. Green requires all existing final gates simultaneously, not measurement completion alone. The gate checks final source/view hashes, both repeated raw all-corner metrics, raw final antenna counts and the last global-routing overflow total bound to the actual final physical checkpoint. It rejects missing/invalid/stale data and never rounds fast hold up to50ps. Always-upload remains active after gate failure. screen_qualification.json explicitly distinguishes pre-DRT qualification from official GDS signoff. No automatic detailed routing.

Fifty focused tests pass. Both exact clean preparations/source hashes/single-setting config deltas, pinned schema, actual TT merged values and workflow shell/embedded Python syntax pass. The newly added strict gate is a project diagnostic step; template gds.yaml and main src/config remain unchanged. Raw data stays in artifacts/local build directories; derived identities and hashes are in coupled_timing_root_cause.json. Physical controls pending.


## 2026-10-28: both root controls fail the genuine screen gate

Both native physical flows and read-only audits complete successfully on758768d. Both fail only Require all final screening gates; evidence upload succeeds. Retrieved artifacts12801548799 (balance,255032042bytes) and12803669470 (fine delay,259582869bytes). A transient artifact egress503 required one bounded missing-report retry; both critical report sets are now complete. Independently matched every fresh corner metric to both repeated raw STA reports and antenna counts to raw fresh metrics. Qualification failures are real threshold failures, not source/provenance errors or tool crashes.

| Run/control | Setup F/T/S (ns) | Hold F/T/S (ns) | Electrical | Antenna nets/pins | Final global overflow |
| --- | --- | --- | --- | --- | ---: |
| [40642215343 root_balance](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40642215343) | 0/0/0 | -0.0255704 / 0.206156 / 0.535035 | all0 | 7/7 | 0 |
| [40642218333 root_fine_delay](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40642218333) | 0/0/0 | -0.146046 / 0.0133134 / 0.298826 | two slow slew | 8/8 | 6 |

Native clock_tree_synthesis executes balance_levels, but final ODB/DEF/NL/PNL/SDC hashes equal wire20040602600864exactly. The source state JSON hash differs; do not claim every artifact is identical. The control does not change the measured physical implementation or improve skew. Level balancing alone is not an effective fix here.

The coarse delay cell is actually absent in root_fine_delay; native effect receipt counts6356dlygate4sd2cells and5141buf1cells. Final area689051.17um²/46767instances. It worsens fast hold, introduces slow slew, adds one antenna net and restores congestion. This falsifies the proposed global cell-exclusion fix on this recipe, despite the earlier demonstrated new delay-cell contribution on the hold175setup path. Do not confuse a local contribution with proof that globally excluding the cell solves the coupled design.

Neither should be combined or promoted. Keep wire200 as the electrically clean zero-overflow reference, still unqualified because fast hold and seven antenna nets fail. Further work should localize clock-wire delay and isolate short latch branches from shared SRAM setup paths; another global hold/cell/wire sweep is not supported. No new dispatch or DRT in this review. Final qualification remains strict and official gds.yaml/main hardware unchanged.


## 2026-10-28: equivalent RTL late arbitration preselection

The SRAM OUT port bit influences rt_ok. In the reference that signal gates the12ready candidates before a priority encoder and53-bit slot selection. Preselecting both the ordinary ready winner and urgent-ready winner moves this late decision after those networks. The chosen slot, fire, routine take and all lane state updates remain equivalent; no cycle or stored state is added.

Packaged default-AW9 whole-lane/ALU sequential equivalence proves2157points, with induction sequence cap2. An independent combinational winner contract proves every ready/urgent/rt_ok/slot-word combination and rejects the wrong urgent winner. Replay rejects unknown baseline bytes before applying the patch. Six lane, four top-level and five chip tests pass. Full-design -Wall lint passes with existing promoted annotations. Broader22-case protocol replay remains in progress at preparation time; simulated cases are not exhaustive protocol conformance.

Paired local mapping with the same typical library measures44610.804→48823.992um²per lane (+4213.188),3340→3795cells (+455),same sequential area11855.2896um². Parsed unweighted gate depth mem_rdata[11]→a_lat[4] is25→14,and maximum reachable flop-D depth26→15. These are structural comparative diagnostics, not STA or routed slack. The optional --map-library packaged replay records the library hash, both mapped stats and depths. Full physical congestion and timing remain unmeasured.

Use the exact measured hold17540621704922project config, not another physical sweep: only the new lane patch changes hardware. One hash-guarded rtl_preselect profile applies the patch after the existing five source patches; metadata explicitly says hardware changed. All20ns/uncertainty/hold/electrical/antenna/overflow gates stay fixed, and no detailed routing starts automatically. Main hardware and official GDS template remain unchanged. Baseline and candidate lane hashes plus patch hash are in late_arbitration_evidence.json; raw logs/mapped files stay in ignored build directories.

Verification environment notes: the first chip invocation imported main's older generated tables; the matching full checkout passes all five tests. Sandboxed sigrok returned empty decoder text with a libusb initialization error even on VCD input; host-permitted decoding of the same saved WS2812waveform produces the expected three colors. The full protocol replay uses host permissions for offline decoding rather than skipping sigrok. Neither issue was accepted as an RTL regression or a passing check.


Late arbitration full-regression completion: Icarus22/22existing protocol cases pass,0failures/0skips,including offline sigrok checks,122863560.02nssimulationin920.96s. The correct candidate source hash is unchanged f011e364a216397c01f9633e4c38e2df412258861343c262f8d6d5e09e6b93c5; XML hash is recorded in late_arbitration_evidence.json. Generator --checkpasses. A duplicate Verilator replay was stopped after six passing cases; no full Verilator22case claim. All local test sessions are complete/stopped. This verification does not establish physical timing; single native screen40723256006is running on the same RTL hash and the measured hold175config.


## 2026-10-28: full-width arbitration screen fails; prepare shared-data priority selection

[RTL preselect40723256006](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40723256006) completes native physical flow and fresh audits, then fails only final qualification. Artifact12845070147,265967076bytes. Every corner metric independently matches both raw repeated STA reports and final antenna counts match raw fresh metrics. Setup F/T/S0/0/-0.612733ns; hold F/T/S-0.0871405/0.143666/0.549590ns. Slow slew2,allcap/fanout0,antenna11nets/pins,finalglobaloverflow311(310Metal3,1Metal4). Final area694915.32um²/47115instances,versus685386.09/45838for measured hold175 (+9529.23um²/+1277instances).

Worst setup has moved to U0word0IDLEbit7latch_53571_→FF_52461_. No SRAM-start paths occur in the bounded1000worst-path report; exact SRAM slack is not established by that omission. New worst fast hold is FF_52025_→FF_52030_. Local gate-depth improvement did not establish global physical closure. Do not promote this failing full-width variant or claim the original SRAM path remains the worst. Area and routing pressure increased; causation is not reduced to one variable from this observation alone.

D-131preselects the two12-bitpriority masks,then shares the original53-bitslot-data reduction. This retains late priority-encoder bypass with much less duplicated data logic. Packaged whole-lane equivalence proves2169points,sequencecap2; the one-stepwinnercontract passes and rejects the wrong urgent winner. Same-library local mapping:44610.804→44817.570um²(+206.766perlane),3340→3356cells(+16),same sequential area11855.2896. Memorybit11→a_lat4gatelevels25→18,maxreachableflopD26→18. About95.1%less added mapped area than full-width preselection; this is structural mapping,not routed timing or total die-area prediction.

Strict full-design lint,6lane/4top/5chip simulations pass. Matched-source full22protocol replay is running with offline sigrok checks retained. The single rtl_shared_priority screen uses exactly the measured hold175config and one hash-guarded RTL delta. Main source/config/official jobs and every final gate remain unchanged. No DRT or physical-pass claim. Source hashes/proof/mapping receipts are shared_priority_evidence.json; replay checker takes --variant shared.


## 2026-10-28: shared priority passes setup/electrical/overflow; hold reserve and six antennas remain

[40762963258](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40762963258) completes native flow/audits and fails only final qualification. Artifact12854346751,254012844bytes. Repeated raw three-corner metrics and fresh raw antenna counts independently match receipt. Setup WS0allcorners; hold F/T/S0.003200/0.219866/0.542820ns; slew/cap/fanout0allcorners; antenna6nets/6pins; finalglobaloverflow0. Fast hold is nonnegative but46.8psbelow the unchanged50psreserve,not a screen pass. Finalarea676087.29um²/45150instances. Against the same-config measured hold175reference: slow setup−0.583896→0ns,overflow5→0,antenna11→6,area−9298.80um²/−688instances; fast hold102.52→3.2ps. Against the full-width version,overflow311→0. No positive setup reserve is established by reported0.

The exact shared-priority RTL also completes22/22Icarus protocol cases,0failures/0skips,with offline sigrok enabled (1534.87s). XML/source hashes recorded in shared_priority_evidence.json. All local protocol work has finished; no full passing screen or official GDS claim.

Six residual antenna pairs include one word3gated-clock leaf. It drives six latch gates,with five nearx602–615umand one _52119_atx1010.4um. Including the driver,cell-origin Manhattan span419.82um. The reviewed latch and worst-hold FF positions are byte-equivalent coordinates across CTS,post-GRTdesignrepair,antenna insertion and final timing repair; this particular separation is already present at CTS,not introduced by later displacement. Worst hold is lane1regs[18]→outputtoken[20],with launch/captureclock0.516511/0.742330ns. These are source-bound geometry/timing observations,not proof of the only remaining cause.

D-132tests only native CTS_SINK_CLUSTERING_MAX_DIAMETER=100um,retaining enabled clustering,size8and byte-identical RTL,early/late175ps,wire200. [CTS docs](https://openroad.readthedocs.io/en/latest/main/src/cts/README.html) describe the sink-cluster diameter option. Do not substitute CTS_CLK_MAX_WIRE_LENGTH: the [repair_clock_nets command](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html#repair-clock-nets) covers input-to-root wiring,not the reviewed leaf. The diameter is an optimization target,not a new acceptance rule or guarantee of final geometry. New grouping can add buffers,change skew/area/routing and regress gates; five data-net antenna failures may remain. All final gates stay mandatory.

Native command/size/enable guards,54focused tests,pinned schema,exact source/one-setting delta/actualTTmerge/syntax checks pass. No new RTL simulations are required for byte-identical source; final extracted GL will still be needed later. Geometry/source hashes are in shared_clock_cluster_evidence.json. Official GDS/main source/config untouched; no DRT.


## 2026-10-28: residuals return after successful native repair

The completed shared-priority run 40762963258 provides a sharper diagnosis than the final failure count alone:

- Native antenna repair reports 3 violations, inserts 3 diodes twice, then reports zero. Its subsequent raw antenna-check metrics confirm **0 nets / 0 pins**.
- The following timing-repair step first reroutes, then its hold optimizer reaches the requested **0.175 ns** worst slack and reports completion. There is no evidence here that a buffer cap or iteration cap prevented reaching that internal target.
- Detailed placement follows, mirrors **20,806 instances**, then fully reroutes. The independent final audit subsequently measures **0.0032 ns fast hold** and **6 antenna nets / 6 pins**. The optimizer's internal number is not final signoff or a same-path slack delta.

Tracing all six final antenna nets through saved DEFs finds five with unchanged connection sets after antenna repair. Only `_08608_` gains the new failing `hold15407/A` branch. None of the six has a directly attached antenna-cell instance in the reviewed snapshots. All six have at least one common instance whose orientation changes during the final legalization; one data-net driver (`wire15104`) also changes origin. Thus the earlier observation of unchanged reviewed latch/FF origins must not be interpreted as unchanged pin geometry or wire routing.

The raw violated rules are cumulative-area rules. `net10748` and `net13566` reach **203.18 / 200** and **203.24 / 200**, about 1.6% over the limit; the strongest data-net failure `_06952_` reaches **444.95 / 200** on Metal3. The clock leaf reaches **319.59 / 200** cumulatively, not the summary's partial ratio of 281.29. This distinguishes near-threshold routing sensitivity from the larger branches without waiving any rule.

A prepared, unlaunched fallback `rtl_shared_no_mirror` changes only native **PL_OPTIMIZE_MIRRORING=false** against measured shared-priority source/config. It tests whether removing repeated pin-orientation optimization makes the repaired geometry more stable. This flag applies to earlier detailed-placement stages too; it is not an isolated final-stage switch and is not proven to cause or cure the failures. It may increase wirelength, congestion or timing delay. The existing full reroute, stock stage order, 20 ns clock, SDC and every qualification gate remain fixed. The current clock-diameter experiment is not combined with it.

Fifty-nine focused guard tests pass, including rejection of mirroring in any of the three reviewed legalization logs. Exact clean preparation, unchanged source hash, single-setting config delta and actual Tiny Tapeout config merge pass. Merged project config leaves rerouting at its native `true` default, enforced by the existing resolved-config guard. The fallback was initially held out of dispatch choices. The user subsequently authorized an independent parallel launch; the diagnostic workflow now exposes it separately, retaining the clock-control default and without combining changes.

Source-bound connectivity, origins, orientations, raw violated rules and report hashes are recorded in `spikes/phase2_stock_flow/shared_residual_history_evidence.json`. This is diagnosis, not a qualifying screen. A read-only all-corner audit would be required to judge the earlier post-antenna checkpoint; its zero antenna count alone does not justify skipping required final qualification.


## 2026-10-28: clock diameter control clears hold reserve; only antenna gate remains

[40779354529](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40779354529), source ee9eed451c8b4ac2cc051fefd7b25084e237b51c, completes physical flow and independent audits; only final qualification fails. Artifact 12861176866 (253260280 bytes) was read selectively. Each corner's before/after raw metrics independently matches the receipt, as do fresh antenna metrics. Native command auditing confirms 100 µm cluster diameter, enabled eight-sink clustering and unchanged other controls.

| Check | Shared reference 40762963258 | Clock100 40779354529 |
|---|---:|---:|
| Setup WS fast/typ/slow (ns) | 0 / 0 / 0 | 0 / 0 / 0 |
| Fast hold (ns) | 0.003200 | **0.0935213** |
| Typical hold (ns) | 0.219866 | 0.340985 |
| Slow hold (ns) | 0.542820 | 0.739804 |
| Slew/cap/fanout violations, all corners | 0 | 0 |
| Final GRT overflow | 0 | 0 |
| Final antenna nets/pins | 6 / 6 | **5 / 5** |

The 50 ps fast-hold gate now passes with 43.5213 ps above that threshold. Setup remains nonnegative without demonstrated positive reserve. Final raw area is approximately 674347 µm² with 45015 instances; this improvement does not add area against the measured reference. The saved final late-route table independently reports zero overflow.

All five residual antenna endpoints are hold/wire buffer inputs; no clock net appears in the final violation list. Their violated cumulative-area ratios versus 200 are: lane1 ot[27]→hold11171/A **244.20**, net12867→wire12867/A **210.02**, net14359→wire14359/A **201.10**, _22096_→wire12360/A **202.98**, net13931→wire13931/A **218.71**. Ratios below 200 in a partial-ratio summary are not rule passes. The native post-antenna checker again reports zero before the later final physical operations expose these failures.

Keep this as the improved timing/electrical/overflow reference, not a qualifying screen. No additional full rerun or gate change is justified by a legitimate failure. The independent no-mirroring control 40781730206 is still running at this check. Evaluate its native-effect guard and complete final metrics before choosing a combined control or any further change. Raw report hashes, exact corner data and rule details are in shared_cluster100_result.json. No DRT/extracted/official GDS or Phase 2 completion claim.


## 2026-10-28: branch tracing and low-cost checkpoint audit

All five final clock100 data-net branches are already present before antenna repair; they are not five new nets introduced afterward. Tracing through native buffer/delay chains identifies lane1 output-token bit27, lane1 register bit60 and U0 configuration write-address bit3, plus two combinational decode cones. Their pre-antenna cell-origin spans are approximately152,199,211,202 and199 µm, depending on the branch. These observations motivate geometry/protection work, not protocol-specific hardware or a functional rewrite.

Reviewed the pinned native heuristic inserter and stock Classic order. The optional heuristic step is already present after post-GRT design repair and before native antenna repair. It uses pin-coordinate spans, skips existing protected/port/special nets, and adds a diode at each terminal of selected internal nets. No separate clock-net exclusion appears in this code. Both placement paddings are currently zero, while the native documentation warns that this option needs placement room.

A deliberately approximate DEF-origin proxy at the default90µm threshold counts8,900nets/40,136terminals. With the pinned antenna-cell library area5.4432µm², that is218,468µm² of diode area alone, about32%of the current reported instance area. At150µm the proxy still counts19,681terminals/about107,128µm²; higher thresholds begin missing reviewed short branches. This is not a measured insertion count or an exact pin-coordinate model. It rejects blindly enabling this broad option without area/capacitance assessment; no heuristic physical experiment is launched. Source hashes, upstream traces and threshold estimates are in shared_cluster100_protection_plan.json.

The more focused independent task is a repeated all-corner read-only audit of the frozen post-antenna checkpoint from40779354529. Its raw antenna count is zero, but timing at that exact checkpoint has not yet been established. The existing separate checkpoint-audit workflow now supports an explicit shared_cluster100_postant choice, with55hash-bound input files and matching source/artifact/toolchain metadata. Only physical-run files are restored under runs; the source's completed corner audit is excluded to prevent stale output reuse. Original stock image digest and source-view hash stability remain mandatory.

The new audit invokes no synthesis, placement, repair or routing and performs no qualification. Its purpose is to determine whether optional native late timing repair is necessary on the improved source. Any promising result still requires a full strict native screen before DRT; a failure usefully identifies needed repair without another physical rerun. Seventy-seven focused guards/tests, actual GitHub provenance and55-file validation, selector execution, YAML/shell/embedded-Python checks pass. Main source/config, official GDS jobs and all gates remain untouched.


## 2026-10-28: read-only pre-late audit confirms late repair cannot simply be omitted

[Checkpoint audit40793477453](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40793477453) completes successfully in about7minutes. Its success means valid measurements, not a qualifying design. Actual frozen source/image validation and source-view hashes remain intact. Artifact12863176502(122795880bytes) contains repeated raw measurements; all before/after corner metrics and fresh antenna metrics independently match the receipt.

| Measurement | Saved post-antenna, before late repair | After late repair and rerouting |
|---|---:|---:|
| Setup WS fast/typ/slow (ns) | 0 / 0 / 0 | 0 / 0 / 0 |
| Fast hold (ns) | **−0.00651512** | **0.0935213** |
| Typical hold (ns) | 0.121036 | 0.340985 |
| Slow hold (ns) | 0.349841 | 0.739804 |
| Electrical violations, all corners | 0 | 0 |
| Antenna nets/pins | **0 / 0** | **5 / 5** |

The earlier checkpoint misses the50psfast reserve by56.51512psand also has negative actual hold. Thus disabling optional late native timing repair alone is ruled out for this exact source/recipe. The final checkpoint gains about100psin the worst fast-hold summary, but the endpoints may differ: this is not a same-path causal delta. Zero antennas before late operations cannot substitute for final qualification.

No new physical run, gate waiver or DRT is justified by this audit. Continue to evaluate the separate no-mirroring result. If it does not preserve the repairs, a further native strategy would move sufficient hold repair earlier, before antenna repair, followed by a complete strict screen. That strategy is untested on the clock100 source; earlier-source margin sweeps were not conclusive closure and must not be claimed as proof. Exact audit data/provenance are in shared_cluster100_postant_result.json.


## 2026-10-28: disabling mirroring does not qualify

[40781730206](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/40781730206) finishes in about3h40. Native flow and audit complete; final qualification correctly fails. All three legalization logs pass the no-mirroring effect guard. Artifact12868231790(254252499bytes) was read selectively; repeated raw corner/electrical and fresh antenna metrics independently match the receipt.

Setup WS F/T/S0/0/−0.128148ns; hold F/T/S0.0710488/0.31385/0.731379ns. Slew/cap/fanout violations are0throughout, but antennas remain6nets/6pins and final late-GRT overflow is48. Last raw Total row independently confirms48. Area approximately683964µm²/45788instances. Against shared-priority reference, fast reserve passes but setup/overflow worsen; the control does not solve antenna reappearance. Against clock100 it has more failures and higher area. Do not promote this control or assume combining it with clock100 fixes the design.

Keep clock10040779354529as the stronger measured reference: setup0all,fast93.5213ps,electrical0,overflow0,antenna5. The read-only checkpoint audit rules out simply omitting late repair on that source. Next investigate sufficient earlier hold repair before antenna repair, with a full strict native screen required to qualify any changed recipe. No official-flow edits or acceptance relaxation. At the final status check no main-branch workflow is running; GitHub still lists two stale queued diagnostics created2026-10-07,not active new experiments. Exact failed-control data/provenance are in shared_no_mirror_result.json.


## 2026-10-28: prepare early275/late75 on the clock100 reference

The next diagnostic keeps the final native repair/reroute stage and its final-ODB-bound overflow evidence. It changes only two optimizer targets against measured40779354529: post-CTS hold target175→275ps, post-GRT target175→75ps. All source,100µmclock clustering,eight-sink mode,wire200,diode-only repair,mirroring/native defaults and20ns/SDCremain fixed. This paired strategy tests whether more repair before antenna insertion and less afterward can preserve antenna cleanliness. It does not assume a linear target-to-slack response or isolate each target independently.

The earlier proposed late-stage omission is not used: the exact earlier snapshot fails hold, and the existing gate correctly requires congestion evidence from the actual final physical checkpoint. No fallback to earlier zero-overflow tables or change to the gate implementation is introduced. Both native commands and resolved values must match the new targets; full late rerouting remains mandatory. A75psoptimizer target does not lower the50psindependent final acceptance requirement.

Earlier repair may add area or damage slow setup/routability, and final mirroring/rerouting may still expose antennas. Keeping the native pipeline intact makes every final gate directly comparable with the clock100reference. Eighty focused guards pass. A clean archived checkout with exact CI preparation reproduces the same complete RTL/SDC/Tcl hashes and only the two selected configuration changes; actual TT merge, per-profile reference/config-hash binding and embedded syntax checks pass. The RTL is unchanged from the22/22protocol replay; no new simulation pass or physical result is claimed. Evidence is early_repair_schedule_evidence.json. Only one new physical screen is planned; no broad sweep, main promotion or official workflow edit.
