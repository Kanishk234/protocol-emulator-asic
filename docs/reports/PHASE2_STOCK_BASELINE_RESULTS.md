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
