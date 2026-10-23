# Decisions

Format for each entry: ID, date, status (Proposed / Accepted / Superseded), decision, reason, alternatives considered, cost, evidence.

## D-081: Measure interaction of two individually beneficial reset-placement policies
- **Date:**2026-10-11. **Status:** accepted copied-checkpoint interaction trial, no promotion.
- **Evidence:** net683 relocation38163542037 reduces146→136; net643/row policy38167244563 reduces146→145 with101vs111markers. Both native routes still fail; reductions are not assumed additive.
- **Decision:** combine exactD078 andD080 placements on original38101405271 source. New26-instance plan retains all masters/orientations/statuses/connectivity/power phase and every other placement. Native legality and six identical electrical/timing screens precede paired routing. Report original146 and prior independent136/145 separately; no isolated causal claim from combined result.
- **Cost:** no additional cells; same-row redistribution and two existing ties alter wire geometry. Reject illegality/electrical regressions and measure actual route policy unchanged. No frozen hardware/spec changes.

## D-080: Receiver-local reset tie with one-row whitespace redistribution
- **Date:**2026-10-11. **Status:** accepted copied-checkpoint physical-policy trial, no frozen hardware promotion.
- **Evidence:** native inventory38166250744 authenticates365 actual fragmented rows; row468720 extends to111360DBU with free tail from100320. Independent net694 relocation worsens146→154 despite shorter distance, so arbitrary remote gaps are rejected. net643 connects tie u_shell.u_crc._329__644 to register_329_/RESET_B; original tie row529200 is60.48µm away.
- **Decision:** from exact38101405271 source, move24 cells starting atx21120 on row468720 right1.92µm, consuming actual free tail; move only existing net643 tie from bbox(9120,529200,11040,532980) into(20160,468720,22080,472500), adjacent to its receiver. Exact25-instance plan is test_internal/reset643_plan.json. All orientations/statuses/masters/connections and every other instance/macro/pin stay exact. The tie shifts16 rows, preserving power phase. Native legality and unchanged six electrical/estimated timing screens are mandatory before routing.
- **Cost:** no new cells;24 cells move horizontally and their parasitics/pin access can worsen. No RTL or architecture change. Compare actual same-policy routing before promotion; source netlist remains identical. This is one placement-localization policy, not multiple hardware features.

## D-079: Test the measured net694 interior-slot relocation
- **Date:** 2026-10-11. **Status:** accepted copied-checkpoint experiment; no hardware promotion.
- **Evidence:** read-only audit of actual producer38163199430 and native markers38163542037 finds445 single-load reset ties,116 separated by at least30µm in row coordinates. Of70 marker-associated reset ties,68 lack an improving conservative interior slot within20µm of the receiver row. net694 appears in five markers and has a same-power-phase slot reducing bbox-center Manhattan proxy62.94→49.38µm. These proxies are not routed wirelength.
- **Decision:** from exact fixed-original38101405271, move only existing generic tiehi u_shell.u_spi._244__695 from bbox(40.80,529.20)-(42.72,532.98) to(92.64,506.52)-(94.56,510.30)µm. Preserve MX orientation, status, every other instance, connectivity, masters, macros and pins. Six-row vertical shift retains power phase. Native placement legality and all six unchanged estimated shell electrical/timing cases must pass before paired routing.
- **Cost/alternatives:** no new cells or protocol primitives; lateral displacement increases and routing can worsen. This independent one-cell trial uses the original checkpoint, not the preceding net683 candidate; compare against its146-overflow baseline. Do not add the two moves without testing their interaction. Larger whitespace policies remain necessary for most affected ties.
- **Research:** OpenROAD documents instance padding before legalization and native check_placement separately: https://openroad.readthedocs.io/en/latest/main/src/dpl/README.html . Documentation is contextual; retain our pinned implementation and actual native guards, without assuming newer legalizer options exist.

## D-078: Test one actual reset-net endpoint relocation
- **Date:**2026-10-11. **Status:** accepted bounded copied-checkpoint producer; no promotion.
- **Evidence:** paired native38113003427 reports identical146 overflow and byte-identical marker maps before/after five-cell spacing. Actual census shows three selected combinational cells do not connect to the worst marker's source nets. net683 has exactly two endpoints: SPI register_251_/RESET_B and tiehi_251__684/L_HI. The marker names net683.
- **Decision:** on the exact fixed-original ten-buffer checkpoint38101405271, move only this existing tiehi from bbox89.28–91.20,y510.30–514.08µm to91.68–93.60,y502.74–506.52µm. The two-row shift preserves vertical power phase, orientation, master, status and connectivity. Native legality plus every other instance exact and six unchanged estimated shell STA/electrical cases are mandatory. No padding, RTL, clock-policy or macro move.
- **Hypothesis:** pinned PDK Metal1 L_HI shape changes from y512.465–513.210µm to504.905–505.650µm; receiver RESET_B lies at508.335–508.790µm. Moving this two-pin net into the same coarse vertical band may reduce demand near511.2µm. Actual GRT pin-access/grid selection and overflow must be measured; transformed LEF geometry alone does not prove an improvement.
- **Cost/alternatives:** one existing generic constant cell relocates; no new protocol primitive or cell area. Wiring/parasitics/pin access can worsen elsewhere. Reject native illegality, unexpected movement or electrical/timing failure; compare actual paired routing before promotion. Remaining CRC, configuration and clock source nets still need analysis.
- **Sources:** pinned OpenROAD dcf36133a369abc8f3c5e5738cd4d82e4903c0e0 src/grt/src/GlobalRouter.cpp makeItermPins applies instance transforms to master rectangles; later pin access uses router-specific positions. Pinned PDK2bbec755dc67ca3db0261c3d6163e15735d66710 LEF SHA c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219 (see research report for exact source and measured geometry).

## D-077: Physically test the generic eight-register delay feature
- **Date:**2026-10-11. **Status:** accepted copied-input macro trial, no promotion.
- **Evidence:** intrinsic38113263802 clears all examined delay-case hold/setup at two UART positions/three corners under unchanged margins. Data paths pay additional delay; run catalogue area14.5152µm²/cell, eight cells116.1216µm² excluding physical overhead. This is not routed timing or total chip area.
- **Decision:** authenticate existing original source archive and derive exactly eight identity D delays from its pre-buffer mapped C2 source. Reuse the original no-synthesis physical flow without duplicating output adapters. Keep190.08×196.56µm footprint and original PG, pin rectangles, routing layers,20ns virtual-clock policy and every physical checker. Retain original mapped source, reversible change inventory, exact input hashes and eight surviving delay instances.
- **Benefits/cost:** protocol-agnostic register timing repair, useful to future register-based designs; no UART/SPI/I2C engine or new user resource. Every program pays data-path delay and placement/routing/power cost. Actual physical area/corners/loading costs must be measured. No equal-area superiority or architecture claim from intrinsic data.
- **Limits/alternatives:** existing virtual-clock constraints still cannot prove programmed timing. Full clock/configuration modes, fresh extracted configured STA, loaded functionality and other tile types remain necessary. Genuine sensitization analysis or smaller buffers remain alternatives. Any strict routing/geometry/interface/delay-retention failure rejects the trial. Preserve deferred timing errors independently; diagnostic success only records actual zero physical gates.
- **Evidence:** cloud_c2_delay_harden.py/c2_delay_harden.yaml, actual intrinsic-source validation, exact pre-buffer contraction/tamper controls and AST/YAML pass without local EDA. Standard65min hosted job/3000s native bound, compact artifact retention. No frozen/generated RTL or upstream source edits.

## D-076: Screen generic user-register delay against measured fast hold paths
- **Date:**2026-10-10. **Status:** accepted intrinsic-only copied-netlist diagnostic; no architecture or physical promotion.
- **Data/benefit:**38112173902 reports fast self-feedback hold−0.032927/−0.037383ns at two loaded UART positions. Read the exact pinned fast Liberty used by that run, matching SHAaf12d75a…; it includes non-inverting dlygate4sd1_1 with X=A. A standard data-delay repair is protocol-agnostic and could help every design using registers; no protocol controller or new user resource is added.
- **Decision:** create a reversible copied-netlist change: one identity delay on each of all eight user FF D pins, retaining every original cell/pin/configuration output after contracting those identities. Compare baseline/candidate at two exact loaded-image positions and three original PVT libraries/20ns margins. Both variants omit parasitics: measure intrinsic Liberty behavior, not a mixture of old extraction with new unannotated nets. Authenticate libraries against the precise actual timing run, require real clock arrivals and retain native status labels/negative results.
- **Cost/alternatives:** eight additional catalogue cells; capture native library area in results, with legalization/routing/power cost still unknown. Every user pays extra D-path delay and area, including designs without the observed failure. Smaller buffers, genuine sensitization proofs and native hold repair remain alternatives. No equal-area superiority or routed benefit claim. Clock-frequency reduction alone does not fix same-edge hold.
- **Execution/limits:** standard45min hosted job, twelve120s cases, image provisioning5min. No frozen/generated RTL edits, GDS/ODB mutation, bitstream change, false paths or reduced margins. A favorable intrinsic result only motivates a later legal physical trial and fresh route/extraction/electrical/function/configured timing across images.
- **Evidence:** cloud_c2_delay_screen.py/c2_delay_screen.yaml; exact source contraction, wrong-source and malformed path/status controls plus six prepared constraints/AST/YAML pass without local EDA. Source-verified [OpenROAD hold-repair guidance](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html) describes repairing hold after propagated clocks and preserving setup; exact pinned commands must be verified before physical use. Actual screen pending.

## D-075: Route the authenticated five-move placement against its real baseline
- **Date:**2026-10-10. **Status:** accepted paired hosted diagnostic; no promotion.
- **Evidence:**38112272623 passes native placement, exact five moves/max1.44µm, all3606 masters/orientations/statuses/terminals preserved, fixed macro exact and all six estimated shell STA screens with zero electrical violations/positive setup/hold. Source NL is unchanged; physical routing has not been tested.
- **Decision:** compare exact fixed-original38101405271 baseline to the exact five-move producer, using identical hash-authenticated original50-iteration native GRT policy from38101639866. Same total area/masters/configuration/shell and20ns target. Preserve source-placement, library/macro, routing-layer/adjustment/electrical/margin guards, actual native tables, hotspot reports and failures. No allow-congestion, capacity inflation or extra hardware change.
- **Cost/limits:** free standard45min hosted job, two900s native routes, separate5min image provisioning. Diagnostic collection may succeed with either route failing; result records underlying acceptance separately. Full detailed routing/extraction/geometry/antenna/function/configured timing remain later gates.
- **Evidence:** cloud_hotspot_grt.py and hotspot_grt.yaml; root reproduced source-result/complete-manifest/view/policy hashes, exact geometry and six-corner guards without local EDA. Actual routing pending.

## D-074: Measure conditional configured C2 internal timing in hosted CI
- **Date:**2026-10-10. **Status:** accepted isolated diagnostic; no hardware or timing qualification.
- **Decision:** authenticate final physical C2 views from37814078650 and actual loaded UART evidence from37958116481. Run the two concrete C2 positions at all three original PVT Liberty corners, using extracted nominal SPEF and a genuine20ns propagated clock at N_GBUF_END[3]. Preserve original clock margins. Exactly529 image-derived configuration Q values per tile are stationary conditions; all eight user FF states remain dynamic. Add no false paths, loop cuts or I/O budgets.
- **Checks:** retain annotation, setup/loop/unconstrained reports, expanded internal register paths and actual rise/fall arrival evidence at every user CLK. Missing commands, reports or clock coverage reject diagnostic completion. Preserve every failed case. Pinned OpenSTA command signatures were checked against its source before execution.
- **Cost/limits:** standard hosted40min job, six180s STA cases. Nominal parasitics with three PVT libraries are not three RC corners. Upstream clock/intertile/shell timing, loading-mode capture and universal full-load stability remain outside this conditional probe. Acceptance stays false even when collection succeeds. BMC84 passing38102131236 does not prove arbitrary complete frame loading or mapped latch stability.
- **Evidence:** cloud_configured_c2_sta.py and configured_c2_sta.yaml; source hashes and six prepared constraint bundles reproduced locally without EDA. Actual cloud execution remains pending.
- **Actual result:**38111705892 completes all six cases with eight real clock arrivals each and54 total examined paths per min/max mode across the two positions at each corner. Positive examined setup, but fast hold reports−0.03ns/−0.04ns; no timing pass. Coverage/loading/intertile limits persist. See compact_conditional_c2_sta_20261010.md.

## D-073: Test local whitespace at the measured CRC/SPI shell hotspot
- **Date:**2026-10-10. **Status:** accepted isolated copied-checkpoint placement diagnostic; no promotion.
- **Evidence:**38101639866 fixed-original candidate still fails146 overflow;53 native markers/85 planar overflow remain at x0–121.44,y475.2–525.6µm. Native coordinates are micrometers by pinned dbMarker.cpp. Source38101405271 has legal exact hardware and zero estimated fanout/slew/cap/setup/hold violations at all three explicit corners.
- **Decision:** authenticate that exact fixed-original candidate. Select original movable CORE CRC/SPI cells by actual OpenDB bounding-box intersection with the measured band. Apply one left/right placement site via pinned native per-instance setter; legalize and retain exact masters/orientations/statuses/all terminals/fixed macro with22µm maximum per-axis movement. Require actual site-width/DBU geometry, preexisting spacing-conflict witnesses and zero post-padding conflicts (two sites between two selected cells). Run six explicit baseline/candidate STA screens under unchanged source libraries/macro/20ns/electrical constraints. No blanket clock/driver/RTL change.
- **Cost/limits:** free standard45min workflow, pinned image pull5min, native edit180s and STA300s/process. Whitespace may improve wire demand or worsen displacement/skew; no measured benefit yet. Padding is process-local placement policy, not an ODB-persisted silicon resource. Fail on illegal/unproven spacing, changed topology or electrical rejection. Fresh native routing/extraction/function/configured timing remain separate after any producer pass.
- **Evidence files:** cloud_hotspot_padding.py and hotspot_padding.yaml. Source authentication, geometry controls, AST/YAML and Tcl completeness pass without local EDA. Root reviewed native dpl::set_padding_inst wrapper and creates forced STA run directories before invocation (BUG34).
- **Rejected first trial/follow-up:**38102082569 obtains spacing but changes1602 orientations and moves32 actual boxes beyond22µm. Retain the rejection (BUG66). Enforce positive native22µm displacement bounds, restore source orientations at unchanged legalized bounding-box anchors, retain intermediate canonical census and recheck native legality plus both box/origin movement. This refines enforcement of the original preservation contract; no bound is relaxed or hardware added.
- **Bounded rejection and narrower scope:**38102423038 fails native DPL-0036 before orientation audit/STA/routing; the151-cell target cannot be legalized by this bounded invocation. Next isolated probe targets only five SPI cells whose actual boxes intersect the fixed-original source's worst native left-shell marker at x86.4–93.6,y504–511.2µm, overflow4/capacity20/usage24. Authenticate report38101639866 SHA4892d8460230f76823f9d885a12f5d097a0d559b75fb3803cef8281e8b497bb1; exact five names and five pre-padding spacing conflicts are verified. Retain22µm, one-site spacing, complete preservation and all six STA screens. Reject canonical orientation changes that reverse the vertical power phase before restoring horizontal orientation. This tests a smaller locality hypothesis; it is not a remedy claimed for all146 overflow.
- **Five-cell rejection/policy refinement:**38111705881 legalizes but the power-phase guard rejects u_in_sync._092__506 MY→MX after unrelated odd-row movement. Preserve the rejection before restoration/STA/routing. Source-geometry analysis finds a same-row rightward spacing plan moving seven cells by at most1.44µm; use existing row whitespace without global OpenDP canonicalization. Keep every row/orientation/status, source topology, native one-site padding and placement checks plus22µm maximum movement. No clock, logic or resource change. Native feasibility/electrical results remain pending.
- **Native row rejection:**38112069098 rejects the rightward plan at u_cfg row1 _100_ with DPL-0004 placed-in-rows failure. Cell-box spacing alone cannot prove usable row extent. Refined exact-source plan moves three cells right on the upper row, and hold1200/selected _251__684 left into the measured lower-row gap; five moves total, max1.44µm. Authenticate each original box before mutation, retain all rows/orientations and the complete native checks. Do not move the configuration cells or waive the row failure. Native validation remains pending.

## D-072: Check the actual compact RUN configuration-gate premise before STA
- **Date:**2026-10-10. **Status:** accepted bounded diagnostic, no timing claim.
- **Reason:** existing F2 proves accepted-load provenance, not inactivity of configuration gates during RUN. Current fallback RTL is not the exact compact shared-CRC shell. Case analysis on loaded latch Q values needs a separately stated mode premise.
- **Decision:** authenticate the exact ten compact source files from the existing checkpoint, retain original F2 instrumentation/assumptions, and instrument copies only. Abstract SPI receiver outputs and user-fabric responses while keeping shell/reset/configuration FSM and decoders. Assert RUN has no cfg_strobe/restart/frame_strobe/live_frame_strobe, and word/frame-data stability across consecutive RUN cycles. No RUN, word or frame-strobe constraint is assumed. Require both84-cycle BMC and all84-cycle covers, including reachable RUN.
- **Cost/limits:** pinned hosted formal tools, each task900s, workflow40min. Raw reset is low for first four cycles; original F2 no-rx_valid-during-crc_busy assumption remains explicit. async2sync/dffunmap produce a cycle model, not analog reset/pulse safety. A bounded pass is not an unbounded invariant, mapped529-latch equivalence, all-image safety or configured timing signoff. Preserve actual source/result/tool provenance and failures.
- **Evidence:** cloud_run_config_property.py preparation/source-preservation/wrong-hash/missing-F2/duplicate-wrapper controls and AST/YAML pass without local EDA. Hosted results pending.

## D-071: Isolate buffer insertion from incidental original-cell movement
- **Date:**2026-10-10. **Status:** accepted bounded copied-checkpoint diagnostic; no hardware promotion.
- **Evidence:** ten-buffer37956470190 clears five estimated fanout failures in all three explicit corners but moves1550 original instances. Actual paired GRT38100977984 fails baseline149/candidate169 after150 iterations; native maps38100978078 localize most congestion to left-shell CRC/SPI/clock wiring.
- **Decision:** reuse hash-pinned cloud_cfg_fanout.py source, authenticated cluster8 checkpoint and exactly the same ten buffers/connections/initial centroids. Change only legalization policy: temporarily FIRM all3595 original PLACED instances, preserve existing FIRM macro, restore every original status, and require exact3596 original master/origin/orientation/status records plus contracted topology and native placement legality. Retain failed trial census/database without promotion. Run the same six explicit-corner estimated STA guards only after successful mutation. Never combine driver, CTS or routing-policy changes.
- **Cost/limits:** standard hosted25min workflow, separate pinned-image pull5min, inherited native edit180s and STA300s/process. No frozen source or intrinsic cell change beyond the previously measured ten buffers. Lack of legal whitespace rejects this trial. Success only establishes legal placement and estimated electrical screening; new native GRT/extraction/function/configured timing still required. It cannot by itself fix the baseline shell hotspot.
- **Evidence files:** test_internal/cloud_cfg_fanout_local.py and separate cfg_fanout_local.yaml. Static/census positive and movement/master/orientation/status negative controls pass; run38101405271 pending native execution.

## D-070: Collect native routing hotspot coordinates without hardware changes
- **Date:**2026-10-10. **Status:** accepted bounded reporting diagnostic; no promotion.
- **Evidence:**37958932549 reports148/169 overflow;37960021920 increases search to150 but buffered remains169. Baseline150 did not execute because cold Docker pull exceeded observer120s. Clock NDR fallbacks and1550 moved original cells are clues, not proof of the root cause.
- **Decision:** on authenticated unchanged checkpoints and original routing policy, request native congestion report coordinates and keep them even on genuine GRT failure. A local attributed copy of pinned routing scripts may add only the native report-file/iteration-report flags; verify pinned originals and exact differences. The reporting-only change is recorded in patches/librelane-congestion-report.patch; runtime copies retain upstream headers and attribution. Never edit installed/upstream scripts, allow congestion, inflate capacity or alter electrical/layer/macro/clock constraints. Pull pinned image before short observers. Record diagnostic collection separately from routing acceptance.
- **Cost/limits:** standard hosted bounded jobs only. This adds evidence, not hardware or a performance claim. Cross-check actual hotspots against native pin/macro geometry before choosing one physical change. Full route/DRC/LVS/function/configured timing remain required.
- **Sources:** [pinned global-routing reports](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/README.md), docs/reports/compact_congestion_research_20261009.md.

## D-069: Preserve measured experimental sources before artifact expiry
- **Date:**2026-10-10. **Status:** accepted local preparation; public upload pending explicit approval.
- **Decision:** prepare compact-proven-sources-20261009.tar.gz with30 allowlisted generated C2/control/fanout views, provenance, licenses and manifests. Verify actual finalC2 NL/ODB anchors, passing loaded/interface/estimated-fanout evidence and all input hashes. Retain original setup/fanout/congestion rejection; no qualified-successor flag. Exclude raw logs, secrets and original PDK libraries. Existing base checkpoint remains an explicitly hash-pinned dependency.
- **Reason/cost:** CI artifacts expire; a small durable source bundle avoids losing exact tested views. No silicon or tool behavior changes. Source SHA25662c31885fb9771b7cf3de162b1a34715759768bfa06aa53241f81b8162134a7a,3620241bytes. Public release destination is the existing compact-checkpoint-20261006-iter8, but automatic approval review requires user authorization for this exact payload/destination. The attempted upload did not execute; do not bypass it.
- **Evidence:** preserve_compact_sources.py prepare/verify plus duplicate/traversal/tamper/scope negative controls. Generated archive stays in ignored build/; no raw artifacts committed.

## D-068: Bounded longer global-routing search on unchanged checkpoints
- **Date:**2026-10-09. **Status:** accepted tool-only diagnostic; no promotion.
- **Evidence:**37958932549 authentic cluster8/ten-buffer cases fail native GRT-0116 with complete final congestion148/169 respectively. Both original settings use GRT_OVERFLOW_ITERS50 and keep congestion disallowed; current placement is unqualified.
- **Decision:** replay both exact inputs, changing only GRT_OVERFLOW_ITERS50→150 in the copied cloud config. Authenticate both prior resolved configs and require original50 before overriding, explicit selected value, same library/macro/clock/SDC/layers/adjustments and native before/after placement/connectivity. Keep all D067 complete-table/zero-overflow/guide/wirelength gates. Manual50 remains available for reproduction; push/default150 is the new isolated search. Preserve timeout/nonzero evidence.
- **Cost/limits:** each GRT900s and total hosted job45min remain bounded; more search may not resolve local congestion. No buffer/master/placement change, capacity inflation, congestion allowance, routing-layer expansion or detailed route. A pass would justify further detailed-route measurement only, not timing or physical qualification.

## D-067: Measure actual routing cost of the ten-buffer fanout remedy
- **Date:**2026-10-09. **Status:** accepted paired bounded global-routing experiment; no promotion.
- **Evidence:**37956470190 passes explicit three-corner estimated shell fanout/slew/cap/setup/hold with ten identity buffers on cluster8;1550 cells move during legalization. Stronger-driver37708459393 is a different layout/tree and cannot supply this checkpoint's route acceptance.
- **Decision:** compare exact cluster8 checkpoint37811985079 against exact buffered checkpoint37956470190 using only stock OpenROAD.GlobalRouting with identical authenticated original library/macro/clock/SDC/routing settings. Require native legal placement, before/after instance/master/connection equality, complete actual final congestion table with zero H/V/total overflow, positive native wirelength and actual guides. Preserve both outcomes and all reports/state hashes even on failure.
- **Cost/limits:** standard cloud45min job, each GRT900s. Candidate cost remains ten buffers and measured legalization displacement; congestion/wirelength are measured rather than inferred from cell count. No synthesis, new driver resize, antenna repair, detailed route, extra resource or protocol tuning. Zero global overflow cannot certify detailed-route/geometry/function/extracted or configured timing. Next step is fresh native routing and extracted checks only when actual congestion evidence supports it.
- **Source:** [pinned OpenROAD global-routing interface](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/README.md).

## D-066: Export only valid existing external power accesses
- **Date:**2026-10-09. **Status:** accepted abstract-only cloud experiment; no hardware promotion.
- **Evidence:** official37814339758 passes eight checks; Pin check rejects two internal Metal4 side-grid access boxes ending18.68um below the top boundary. Twenty-four existing full-span supply accesses remain available.
- **Decision:** derive the native LEF from an in-memory copy of the authenticated driver ODB. Remove exactly the two identified access metadata boxes only after proving complete same-net existing Metal4 conductor coverage. Retain all24 valid access rectangles, every signal pin, supply BTerm/net association, die and native special-wire/via geometry; exact native before/after census is mandatory. Never rewrite source ODB/GDS or invent coordinates. Run all nine unchanged official checks.
- **Reason/alternatives:** external abstracts may expose a subset of actual conductor accesses; an internal side-grid segment need not be an external boundary access. Extending physical rails would require new routing/DRC/LVS and is deferred unless existing-conductor proof fails.
- **Cost/limits:** no silicon-area or protocol resource change; two fewer advertised external access rectangles. No timing, fanout, native function or complete fabric acceptance follows. The official result remains pending.
- **Sources:** [pinned official power-pin checks](https://github.com/TinyTapeout/tt-support-tools/blob/d66cf179e7bc4d296362ab7e2e3b344dc3c4f665/precheck/pin_check.py), [native box destruction](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/odb/src/db/dbBox.cpp), [native LEF access export](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/odb/src/lefout/lefout.cpp).

## D-065: Retest actual hardened C2 through the real loader
- **Date:**2026-10-09. **Status:** accepted bounded native diagnostic; no physical/timing promotion.
- **Evidence:**37814078650 actual hardened C2 finishes route/antenna/Magic/KLayout/LVS with zero findings but fails deferred virtual-clock setup and has62 fanout violations. Exact final NL13cac0eabdbdcaf000b1e57c521fc9d417aac957be18a68c5808f8c920529e7c is available; its native behavior has not been retested.
- **Decision:** compare authenticated passing five-tile control37659171115 with only C2 replaced by that actual final NL. Run normal/USER_RESET for each with unchanged D023 harness, fresh raw connectivity JSON/source hashes and actual SPI configuration audit. Require9164 actual latches known/image-matched,28TX/28RX,STOP/reset and exactly one passing/non-skipped XML case each. Retain all four outcomes even if one semantic case fails; no state force or input edits.
- **Cost/limits:** free standard cloud45min job, four cases each300s. No new resource, protocol block or configuration format. A functional pass cannot qualify timing, electrical limits, complete macro geometry or any other untested tile. Original failed hardening outcome retained alongside final source hash.

## D-064: Buffer the five measured configuration-column fanout nets
- **Date:**2026-10-08. **Status:** accepted bounded placement/estimated-STA diagnostic, no routing or promotion.
- **Evidence:**37811985079 cluster8 clears all clock fanout violations but leaves five configuration-column outputs with12 loads against effective Liberty limit8. Original design MAX_FANOUT_CONSTRAINT10 remains unchanged. Input cluster8 ODB0a0af0c1a0e4c413f52c43de70772dfff857a7c98402fa9b5b7e8dac19a53f99, NL5bcc7ceb770d8f20fce68e43b90b8a23bdcb1aa05fc7e17f2672248bbc23c9fe and original SDC2fd4e213532d83ee258899b6fc1ed48c4e5d91ddb0ccbe21eea0226cc90fd56e authenticated.
- **Decision:** add exactly two identity buffers per target net, each driving six original loads. Require supplied Liberty function A, unchanged all original masters/terminals after contracting ten buffers, unchanged fixed macro and native legal placement. Measure baseline and candidate across all three original corners by explicitly setting PNR_CORNERS; same library files, clock/SDC/electrical constraints. Baseline must reproduce five fanout failures per corner; candidate must report zero per corner.
- **Cost/limits:** standard cloud25min job, edit3min and each estimated-STA5min bound. Ten added buffers plus legalization can cost area, load, power and skew; no generic architecture/equal-area improvement claim. No repair_design blanket resizing or second CTS; detailed route and extracted all-corner setup/hold/slew/cap/function remain required before selection.

## D-063: Harden the exact passing C2 at its original physical interface
- **Date:**2026-10-08. **Status:** accepted one-tile cloud diagnostic, no frozen hardware or full-chip promotion.
- **Evidence:** passing C2 loaded native control37709917442; matched-pin37811985092 original and passing NL both reproduce306 signal ports and exact die. Use passing NL03c21b8e400e1774390e67b0939422959d37e26849adca18fa082f492cf5cdaf and tile-harden-c2 archive356c909c1415d2d56f7925e304b3d862055ed471af585cc206af92257c2bb2d8.
- **Decision:** bypass synthesis, replay original physical settings/pinned I/O and output-only buffering adapters. Preserve190.08x196.56um die, exact PDN, all20 routing obstructions, signal Metal2–4 and signal/power interfaces. Configuration-only loading against actual3.1 succeeds; exact sequence PDN→I/O→output buffer→global placement checked. Retain standard detailed route/antenna/disconnect, Magic/KLayout and actual GDS LVS/extraction checks, stage-completion and zero-count gates. Preserve failed baseline checkpoints before investigating known filler/decap geometry separately.
- **Cost/limits:** free standard cloud120min job/110min container bound. No protocol primitive or chip source change. Extra buffers/diodes/fillers may change area/power/parasitics. Original CLOCK_PORT=null remains, so extracted STA is diagnostic and cannot establish configured timing. Passing final netlist needs loaded-image retest and complete fabric integration before selection; every required check stays enabled.

## D-062: Strict official precheck on the passing experimental driver layout
- **Date:**2026-10-08. **Status:** accepted bounded cloud diagnostic; no submission or hardware promotion.
- **Evidence:** driver37708459393 has fresh native/antenna/critical-connectivity0 and Magic/KLayout/shell LVS0, but official Tiny Tapeout precheck is untested. Use accepted overlaid GDS bb415750feace175e140d2fbb3a9aca4b72731c248a884b46999eb933e3f3246 and matching final ODB b71f5f377faee63410781c4f108a7b9b06d26e2552ce9f3418b5f227fbf67285; raw streamout is a different layout hash.
- **Decision:** authenticate compact-precheck-source.tar.gz SHA25604ed04ee60dc4f586309fed368b86b9577cdc9821ffdc0519cafd790eb83b2e6. Export native top-block LEF and power-aware Verilog from that unchanged ODB. Invoke unmodified tt-support-tools d66cf179e7bc4d296362ab7e2e3b344dc3c4f665 official precheck in its pinned Nix environment, following tt-gds-action3412659307918422f3f0727917cf9b499aaca588. Require all nine IHP checks present and passing, no skipped checks or geometry changes.
- **Cost/limits:** free standard cloud65min job, official checks40min bound. No local EDA, pin edits, PDK edits or check waivers. Fanout33, native C2 function and configured-fabric timing remain independent blockers even if precheck passes. Source package contains only public-project generated views, metadata/license and attribution, published to the existing experimental release.

- **First official result:**37811985173 rejects unreferenced overlay originals as extra top cells and short-decimal native LEF through official fp3 parsing. Single-top hierarchy export with exact referenced shapes/labels/instances and DBU equality plus exact-value fp3 formatting corrects packaging only. Authentic source remains unchanged; all nine original checks must pass. BUG54/result report records failed evidence.

## D-061: Preserve original C2 storage while remapping combinational gates
- **Date:**2026-10-08. **Status:** accepted bounded diagnostic; no architecture or frozen-hardware change.
- **Evidence:**37709917442 control passes both28-TX/28-RX loaded cases, but original synthesis and finalC2 substitutions fail UART X with all9164 actual configuration latches known/matching. Failure exists before physical processing; precise combinational/reset cause not established.
- **Decision:** import actual Liberty functions, retain all529 configuration latches/eight user FFs as black boxes, remap only original synthesisC2 combinational logic. Require exact storage instance/type/parameters/bindings/frame interfaces and binary state-cut proof of external outputs plus all storage D/control pins for arbitrary binary Q/input values. Only then run six loaded cases: passing control, original known-failing synthesis negative control, and candidate, each with normal RUN and USER_RESET. Original actual failure remains recorded. Experiment green requires both positive stages pass and both negative cases reproduce UART X after complete known/matching configuration; unexpected negative success or unrelated failure rejects it.
- **Costs/limits:** standard cloud50min job/38min stage, individual cases300s/proof bounded180s. Two-valued combinational proof is not sequential/four-state equivalence, configured timing or physical qualification. Candidate area/gate inventory must be measured before any architecture comparison; no new protocol primitive and no configuration/user-state force or model weakening. A useful candidate needs matching physical views and actual final-netlist retest. D-058 input hashes/Apache attribution retained.
- **First setup correction:**37809673029 loses combinational declarations after flatten/ABC (BUG48). Restore missing black-box port declarations with read_liberty -lib -nooverwrite after ABC, preserving storage. No proof/check waiver; ABC-reported combinational loops may still reject an unsupported proof.

## D-060: Exact mapped C2 floorplan and signal-pin preflight in cloud
- **Date:**2026-10-08. **Status:** accepted bounded physical diagnostic; no full tile/chip hardening or promotion.
- **Evidence:** passing regenerated C2 SHA25603c21b8e400e1774390e67b0939422959d37e26849adca18fa082f492cf5cdaf lacks matching physical views. Original geometry/pin inputs recovered from RUN_2026-09-29_17-38-37; original pin ODB7d2156e7a74e402aa83077051e2c63e73c58c4baa88cd4d6d64ca15290a1f5df. Configuration-only API validation passes locally; no local EDA.
- **Decision:** direct pinned LibreLane container API, fresh candidate-specific unoptimized JSON header, Floorplan/SetPowerConnections and unchanged attributed upstream FABulous I/O adapter only. Compare original-synthesis and passing mapped signal-pin names/directions/rectangles and die against authenticated original pin ODB. Preserve190.08x196.56um die, original core margins and pin layers/extensions/thickness; bypass synthesis. Input archive tile-preflight-c2.tar.gz SHA256d1d87cf442e6fbec1219edfbe243415f40e36fa0d9e07e5fc642ff19db33a64a; plugin dcc038217472822330b33f61fadbc06e0c3cc96d/io adapter4517d4d40cfbadd7dfadc3d7415cd9ade794f3bbaefb21a5ce7bec9db4eefb32, Apache notices/license retained.
- **Costs/limits:** standard cloud25min job, container10min bound; no routing/PDN/PG-pin geometry/LVS/native retest/timing acceptance. Original CLOCK_PORT=null remains;20ns field is not timing proof. Success unlocks a later faithful physical flow rather than changing the frozen macro. Official [custom-flow API](https://librelane.readthedocs.io/en/stable/usage/writing_custom_flows.html) supports this entry point; [plugin documentation](https://librelane.readthedocs.io/en/stable/usage/writing_plugins.html) motivates direct-container API instead of an unsupported dockerized external plugin.
- **First setup correction:**37809673093 cannot import odb in ordinary Python (BUG49). Native read-only OpenROAD Tcl exports the same die/port/rectangle inventory; strict parser rejects missing/duplicate/malformed evidence. Source/pin/geometry gates remain unchanged.

## D-059: Compare original pre-CTS baseline with sink clustering eight
- **Date:**2026-10-08. **Status:** accepted bounded fanout diagnostic; no reroute or clock-contract change.
- **Evidence:**37708459393 clears fresh slew/setup/hold/cap but leaves33 fanout violations:27 clock leaves and six configuration drivers. Pinned Liberty default maximum8. Exact original pre-CTS ODB13edf934051de947fddb8b10aac70ccec2561bd77f06b986185af3e9594a0a1f recovered from original07-CTS/state_in.json.
- **Decision:** two fresh cloud CTS/ResizerTimingPostCTS/STAMidPNR runs on authenticated pre-CTS source; change only CTS_SINK_CLUSTERING_SIZE from null to8. Native placement checks, every signal-net driver/sink census including dummy loads, unchanged fixed-macro placement and supplied-corner estimated fanout/slew/cap/setup/hold/skew retained. Archive fanout-preflight-source.tar.gz SHA256d32c6375fffb932ce77cce3da5df82dc3477c78e8ba7feed222fa10fb87db112 includes license/attribution; same experimental release only.
- **Costs/limits:** standard cloud40min job, each physical case15min, no detailed routing. This uses original driver/macro, not the accepted driver ECO. Extra buffers can cost area/power/congestion and change skew/hold; actual measurements decide. Six configuration fanout violations require separate work; no constraint relaxation. Estimated STA/report generation never qualifies routed/configured timing. Do not build a second clock tree atop a post-CTS/routed database.
- **First setup correction:**37809673156 original PAD_LIBS=null is incompatible with pinned3.1 iteration (BUG50). Normalize only that empty selector to the pinned default{}, retaining/hash-checking all six original standard-cell/I/O timing libraries. Audit resolved CTS macros/clock/SDC/library/fanout inputs; no constraint relaxation.

## D-058: Isolate C2 synthesis versus physical native behavior
- **Date:**2026-10-07. **Status:** accepted bounded native functional diagnostic; no hardware promotion.
- **Evidence:** original mapped macro fails loaded UART (BUG33); regenerated original-control37659171115 and mux-tree37659112021 pass28 TX/28 RX patterns/USER_RESET/STOP. Four local original tile runs have final netlists exactly matching the failing authenticated macro, but no matched base-tile synthesis run was recovered. C2 synthesis SHA2562c9faa6dc332004212c2719a8ca740b902d8c720f5f7da664007d3df7eedf6d9; original final e0aef98643db5a98650e7bc6401de5db72731e89457aae3fd9962ae39b6c6f8c.
- **Decision:** replay hash-bound five passing original-control NLs, then make two separate single-C2 substitutions: original synthesis and original final. Six actual SPI-loaded edge-pattern/USER_RESET cases, with unchanged D-023 data-routing harness, stock PDK models and no configuration/user-state force. Each case bounded300s; continue collecting other stages after semantic failures, but any failure/missing/invalid/skip XML keeps the job failed. Retain full stage/input hashes and logs/XML/snapshots. Source C2 synthesis packaged as31KB diagnostic data with Apache license/attribution on existing experimental release: native-stage-c2.tar.gz, SHA256addc14251bafe63eb19cda6dcb5e0dcf2afc81d9a7bdb8d67f6a92f9d4120d7f.
- **Costs/limits:** standard cloud job45min, stage35min. No routing or cell/resource change to frozen design; copied physical views do not qualify substituted netlists. This locates a first failing stage, not full sequential/four-state equivalence or configured timing. A promising mapping must be hardened from its exact NL and retested at final physical output before replacing the original macro. No unsupported mux-only causal claim. See compact_fanout_native_next_20261007.md.
- **Audit correction:**37708777882 fails before UART because the named-Q inventory includes optimized-away constant-x aliases (BUG47). Generate unoptimized matched connectivity JSON per stage and audit actual latch bindings, retaining strict unknown/mismatch failures for real storage. Classify only proven unused aliases separately; no configuration/user-state force. Repeat all six cases before interpreting stage divergence.

## D-057: Route and re-extract the legal stronger-driver ECO
- **Date:**2026-10-07. **Status:** accepted bounded one-master scratch trial; no promotion.
- **Evidence:**37688389888 fresh-wire slow slew9→0 estimate;37689324316 native source/final placement checks pass, one driver master change and three cells moved, other connectivity/placement/orientation unchanged. Legal placement-only ODB SHA2567b2811c291443d4208bcb1154fbe37ab6eeb7be6702c52060f135d0318509adf. Stale routes/parasitics are explicitly invalid.
- **Decision:** authenticate that ODB, check placement again, measure stale-wire starting DRC, then native incremental bootstrap and at most six proven late-cost repair passes. Require unchanged ECO masters/placement/topology plus final fresh native0; run stock antenna/critical-connectivity gates. Only then fresh extraction/fill/streamout, existing measured pSD policy, full Magic/KLayout/GDS-based shell LVS, and strict three-corner slew/setup/hold/cap checks. Preserve clock target and macro abstraction. Retain fanout33 as a separate open gate rather than hide it. Standard cloud route80min, native15min, downstream check step200min/job220 overall bound.
- **Costs/limits:** one cell adds5.4432um2 nominal area; three site shifts alter wires and may add congestion, hold repair, loading or power cost. Every protocol pays this shared configuration-shell cost; no new fabric primitive or compiler/bitstream contract. Existing no-decap/widened-pSD policy unchanged. Exact per-master filler inventory now binds to freshly filled DEF because three extra logic sites change fill occupancy; non-pSD XOR/clone/bbox/source-hash checks remain. Modified original-source diagnostic helpers may autoqueue redundant baseline replays; cancel only those repeats after launch, preserving the new trial and current accepted baseline. No frozen config/source/macro/PDK edit or waiver. Success remains scratch shell scope, not matched native-fabric function/configured timing/precheck/reproduction.

- **Failure/corrected input:**37690243797 measures22 source markers/bootstrap27, then DRT-0206 on u_cfg._17_ while reusing moved-pin wire escapes. BUG46. Before repair, rip complete signal wires for the exact three moved cells' nets, preserving PG rails/unaffected routes and every logical/port membership. Measure resulting unrouted input; do not compare it with the original22 as acceptance. Final native0 and all downstream gates stay strict. No additional cell/resource change.

## D-056: Preflight legal placement for one stronger configuration driver
- **Date:**2026-10-07. **Status:** accepted bounded scratch placement diagnostic; no promotion.
- **Evidence:** fresh-wire37688389888 reproduces9 slow slew violations and a21oi_2 in-memory substitution clears all9;33 fanout violations remain. Authenticated37674839060 DEF/LEF has packed driver width2.40um versus3.84um candidate, requiring3 extra sites. Two fill2 cells provide1.92um space left of the tie/NAND/driver chain.
- **Decision:** authenticate extracted ODB02b8bd30f3fb12e4a66e2322b5f3906c236dd93eed8b8cd1eeeff95f6e796a61 and read Liberty before swap. Remove only fillers in scratch; change only u_cfg._54_ to a21oi_2 and shift driver, adjacent NAND and tie left1.44um each. Require legal original/final placement, unchanged all non-filler connectivity/orientation, exactly one master change, and no other cell movement. Bound tool3min/step5/job15 on standard cloud runner. Retain placement-only ODB/DEF explicitly marked routes/parasitics invalid.
- **Costs/limits:** nominal driver area increases5.4432um2, three cells move, loading/power costs not measured; every protocol pays this shell cost. No additional fabric resources or architecture/clock change. Existing hold cell stays unchanged. This preflight cannot claim routed DRC/antenna/LVS/timing or configured function. New routing, filler replacement, extracted all-corner timing and physical checks are mandatory before any promotion. No PDK/source/frozen macro edits or waived checks.
- **Alternative/source:** OpenROAD [detailed placement documentation](https://openroad.readthedocs.io/en/latest/main/src/dpl/README.html) describes re-legalization after resizing and placement checks. A bounded hand-selected site shift minimizes changed cells for this measured row; if it fails, investigate the exact legality report instead of widening global placement or accepting overlap. Pinned tool execution remains authoritative.

## D-055: Validate measured filler policy on the recovered zero route
- **Date:**2026-10-07. **Status:** accepted combined scratch physical verification under D-037; no promotion.
- **Evidence:**37669731197 reaches fresh native0/antenna0/critical disconnected0, unchanged topology and retained checked ODB9cac79d86dd15707efdd385c32d3990347cb4695874bc802d0bfe20a5e90e9ba. Fourth late-cost pass enters stubborn flow. Separate older-source widened-filler37669173193 gives full Magic0; these results cannot be combined into a same-layout acceptance claim without fresh checks.
- **Decision:** authenticate the actual checked0 database, perform new wire extraction/shell STA and plain-filler streamout, then apply the measured pSD overlay to fresh GDS with source hash/count/non-pSD equality checks. Run full Magic and stock KLayout/GDS-based shell LVS on that same output. Preserve stock macro abstraction and original clock target. Bound95min stage/110min standard cloud job; retain all evidence.
- **Cost/limits:** combines separately measured decap removal and implant correction as one filler policy. Decoupling, leakage/capacitance and power/noise costs remain uncharacterized; implant changes do not increase the nominal footprint. Shell STA keeps macro black-boxed and does not prove configured-fabric timing/native function. No frozen config, cell netlist, primitive/compiler or PDK edits. No check waiver; macro timing/function and clean-source reproduction remain required even if geometry passes.

- **Verified result:**37674839060 succeeds22m14s: native0 source, fresh Magic0/KLayout0/GDS-based shell LVS0, final GDS7475586c234ce15f0d51b47a9882990b58a703e9c4f387083bd3f09aa4cf7a7a. Fresh shell setup/hold pass all supplied corners, but slow slew9/fanout33 remain. See compact_clean_layout_20261007.md. No configured timing/native-function or successor promotion follows.

## D-054: Screen fully contained Metal1 pin access before routing
- **Date:**2026-10-07. **Status:** accepted bounded diagnostic under D-037; frozen hardware untouched.
- **Evidence:** exact retained37668791436 route/LEF audit reproduces two short clusters: NAND signal escape crosses its VSS spur and NOR B escape crosses C. Late-cost37669731197 remains active independently.
- **Decision:** on authenticated original iteration52 ODB, run native pin_access with via-only Metal1 access and fully contained via enclosures on Metal1, using pinned tool/API. Source hash binds recent retained source copy. Do not reroute in this preflight; inspect warnings/statistics and retain generated AP database. Bound10min tool/15min job on standard free runner. A green job means analysis completed, not route closure or every target pin is qualified.
- **Costs/limits:** no added cells/footprint/resources; tighter access may reduce choices, increase upper-metal congestion/delay or make pins inaccessible. All bitstreams pay any eventual routing cost. Preserve same clock, pin connectivity and PDK rules. Further routing requires native0, antenna/critical connectivity, full DRC/LVS and fresh extracted/configured timing. No performance claim or promotion.
- **Primary source:** [OpenROAD pin-access arguments](https://openroad.readthedocs.io/en/latest/main/src/drt/README.html#pin-access-arguments); pinned dcf36133 TritonRoute.tcl exposes the same options. No upstream edit or acceptance exception.

- **Verified rejection:**37673914480 fails native DRT-0073: inputs A of u_cfg.u_fsm._097_ and u_cfg.g_col[0].u_col._24_ (both sg13cmos5l_nand4_1) have no access point. Downloaded analysis.log identifies both pins; no AP database or reroute completed. Reject this global containment policy rather than launch a long route with inaccessible pins. Independently,37669731197 already passes fresh native routing0 without this policy. No rule or access gate relaxed.

## D-053: Screen late repair costs instead of restarting the early schedule
- **Date:**2026-10-07. **Status:** accepted bounded scratch measurement under D-037; no frozen hardware change.
- **Evidence:**37657068016 stock reload restarts track assignment/optimization0 and ends5 markers after17 iterations. Original37516794406 reaches0 only after iteration53. Pinned OpenROAD dcf36133 initialization resets schedule state; checkpoint ODB is not a serialized router-state continuation.
- **Decision:** authenticate original iteration52 hash33dceb8d52df9d5ea8cc3741b71b9b3e1e79ae4fb95b1eb559b3ca3eb40390bc; reproduce3 source markers. Bootstrap native incremental mode then test two late-cost steps (offsets-2/-3,32 maze iterations,DRC/marker/fixed-shape costs256/256/800,decay.999). These are experimental exposed algorithm APIs, not exact continuation53. Audit unchanged masters/placement/net connectivity, commit final views, require step count and fresh whole-chip native DRC0, then stock antenna/critical-connectivity checks. Pin container/tool, cap native step80min, retain source/reports/views.
- **Cost/limits:** standard runner time; no new cells/resources, bitstream or clock-target change. Different routing can alter parasitics and rates; no geometry/LVS/native-function/configured timing acceptance inferred. Follow-up must pass full physical checks and extracted timing. Do not copy prior-art disconnected-pin/PDN check exceptions.
- **Primary sources:** [schedule](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/dr/FlexDR.cpp), [costs](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/global.h), [step initialization/commit](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/TritonRoute.cpp). Upstream files are read-only; our Tcl lives in test_internal/.

- **First cloud result/follow-up:**37668791436 fresh source3,bootstrap17,late steps7→3; full native check3 and unchanged topology. Two late steps both remained GUIDES, not STUBBORN, because each was effective. Extend same-cost alternating offsets to at most6 steps so an ineffective guide pass can transition to stubborn work;80minute cap unchanged. Pinned [state machine](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/dr/FlexDRFlow.cpp) explicitly uses effectiveness and ignores offset/size when comparing arguments. Nonzero still fails; stock downstream gates remain. No claimed route or timing improvement.

## D-052: Measure wider filler pSD geometry in scratch fixtures
- **Date:**2026-10-07. **Status:** accepted isolated diagnostic under D-037; no chip promotion.
- **Evidence:**37657638270/37658318703 reproduce17 pSD.e/f boxes at correctly mirrored ground boundaries for fill1/2/4/8. 37660478954 synthetic5/30nm gaps produce81 boxes;300nm gives32 contact-spacing boxes. Neither width nor gaps qualify. Exported polygons show N+ diffusion bordering both sides of the shared ground pSD stripe.
- **Decision:** clone pinned fill1/fill2 only in synthetic fixture GDS; add a0.30um inward pSD extension through our patches/ helper, leaving original PDK files untouched. Require identical non-pSD regions and bounding boxes; record added implant area and source hash. Include geometry-identical flattened ground-pair control with per-layer XOR checks, untouched library fixtures and invalid-orientation positive control. Run full pinned Magic rules with both import controls on free standard runners.
- **Costs/limits:** nominal footprint and logic resources unchanged; broader implant can change junction capacitance, leakage, diffusion interpretation and density. All protocols pay any eventual physical cost. No measured chip power/area/timing benefit, primitive or architecture-contract change. Fixture report success is not DRC acceptance. Chip use requires full DRC/LVS, legal placement/power connectivity, fresh native routing and extracted timing; no waiver or upstream in-place modification.
- **Attribution:** geometry derives from IHP-Open-PDK2bbec755dc67ca3db0261c3d6163e15735d66710, Apache-2.0; upstream licenses remain in the fetched PDK. Overlay code lives in patches/ihp_filler_psd_trial.py.

- **Verified/follow-up:**37662382228 reproduces17 boxes in unchanged ground pair and geometry-identical flattened control, but widened-pSD fill1/fill2 give0 in isolated/horizontal/both mirrored-boundary fixtures. Both import modes agree and invalid control still fails. Added implant area0.186/0.330um2 per fill1/fill2. Prepare manual cloud-only full Magic replay of authenticated37648945387 GDS with the same overlay, exact20714-instance inventory and whole-chip non-pSD XOR checks. Source still3 native markers; no rerouting, chip promotion, LVS or timing pass inferred. Full report generation remains distinct from reported zero.

- **Whole-layout follow-up:**37662990606 stops at non-pSD XOR guard.37663775123, using stable instance iteration and normalized region comparison, verifies20714 replacements and empty non-pSD delta; Magic times out30min before reporting. Baseline same-chip stock Magic took12m19s. Match stock suspendall/selected-chip listall sequence instead of global catchup; bound full step45min/job55. This is a reporting/control-flow alignment, no reduced rules or acceptance. No DRC result or cause-specific speed improvement claimed until cloud completes.

- **Whole-chip verified/follow-up:**37669173193 completes whole-chip Magic report0 with20714 replacements and no non-pSD delta, authenticated GDS3ee36af59b8b5964f1796b7b2756e7dad859572d3e23266c848b05fc58ae9f9b. Prepare KLayout and GDS-based shell LVS on that exact artifact; set MAGIC_EXT_USE_GDS true only in copied scratch config so extraction checks actual changed geometry. Preserve stock macro abstraction (shell scope), original logical netlist and source native3 limit. No routing, native-function or configured-timing acceptance inferred. Pinned upstream extract_spice.tcl explicitly selects GDS versus DEF/LEF; upstream untouched.

## D-051: Isolate the Magic filler rule without changing hardware
- **Date:**2026-10-07. **Status:** accepted diagnostic under D-037.
- **Evidence:**37648945387 has6350 Magic pSD.e boxes, all overlapping plain top-level fillers; none inside macro bounds. Pinned KLayout shared pSD deck implements only pSD.c1, so its zero does not clear pSD.e/f.
- **Decision:** cloud-only read-only full-style Magic checks of pinned fill1/fill2, decap4/decap8 and inverter control; retain every report and deck/library hashes. No design, PDK or template-job edits. Bound job12minutes/tool step7minutes.
- **Cost/limits:** free standard runner time only; no hardware cost. Isolated cells do not reproduce row abutment, complete-chip DRC/LVS, native function or timing. Workflow success only certifies completed report generation; reported DRC counts remain failures to diagnose.
- **Verified/follow-up:**37653631748 completes five zero-error isolated checks in retained Magic log. Extend same measurement with untouched-cell horizontal arrays, two same-orientation rows and alternating mirrored rows using exact nominal LEF pitches. Preserve generated fixture GDS; this is a reproducer, not new hardware. Report returned reason-list presence because count output is printed (BUG43).
- **Control refinement:**37657067983 horizontal/mirrored pairs have no findings; intentionally same-orientation rows exercise pSD.e/f and other overlap rules. Match stock readonly/noduplicates/euclidean settings, compare maskhints true (stock) versus false only as an isolated import diagnostic, and cover both mirrored rail-boundary types. Disabling hints is not accepted production DRC or a rule waiver.
- **Reproducer:**37657638270 ground-sharing mirrored pairs of either fill1 or fill2 produce17 pSD.e/f boxes; opposite mirrored boundary/horizontal arrays produce0. Matching flags and both maskhint values give identical results. Extend library-only screen to fill4/fill8 with exact LEF pitches before a new chip filler experiment. No hardware change or waiver.
- **Further measurement:**37658318703 larger fill4/fill8 also reproduce17 ground-boundary boxes. Export exact source polygons and screen synthetic5/30/300nm row gaps to identify contact/abutment behavior. Actual chip rows/rails unchanged. Any useful gap remains only a diagnostic; placement legality, power connectivity, all spacing rules and fresh routing/LVS must pass before hardware use.

## D-049: Same-wire diagnostic of the frame-index slew hotspot
- **Date:**2026-10-07. **Status:** accepted isolated measurement under D-037; no physical promotion.
- **Evidence:** exact37552604692 extracted slow-corner report has9 slew violations, all on frame_idx[0], driven by u_cfg._54_/a21oi_1. Worst2.562529ns versus2.507400ns limit. Same report has33 fanout violations. Source is the saved3-marker intermediate route, macro black-boxed.
- **Decision:** cloud-only comparison of original driver against equivalent a21oi_2, substituting only in memory and reusing identical old wire SPEF/constraints. Require baseline to reproduce all nine exact violation pins and preserve target connectivity. Retain before/after electrical/path/annotation reports and input hashes. No DB write, placement, routing, configuration force or frozen hardware/PDK edits.
- **Cost/benefit:** generic configuration distribution helps all bitstreams if confirmed. Pinned LEF size2.4x3.78→3.84x3.78um adds5.4432um2 before repairs; larger input loading and changed pin access/hold/routing can cost every user. Actual new layout cost/timing is unmeasured. Official PDK combinational gate networks match for the two variants.
- **Limits:** same-old-wire results are conditional electrical estimates. No configured-fabric, fast-corner, legal placement, zero-route or full timing claim. A useful result requires one separately hardened driver change and fresh extraction/all checks. Decap experiment remains independent/untouched.

## D-047: Screen a structurally preserved LUT mux tree (scratch only)
- **Date:**2026-10-06. **Status:** accepted isolated diagnostic experiment; no hardware promotion or resource/spec change.
- **Evidence:**37546145073 proves three native unregistered LUT constants under all529 observed configuration-latch Q values, arbitrary binary tile inputs and arbitrary user state. Actual native four-state UART still fails and those outputs areX. This establishes false unknowns in those three cones, not the complete UART root cause.
- **Decision:** screen a standalone LUT4 implementation using five actual CMOS5L mux4 cells, maintaining the full16-bit runtime truth table and4-bit input contract. Prove binary equivalence against pinned FABulous LUTK for every configuration/input and test partial unknown inputs against independent truth-table completions with actual pinned PDK models. Candidate is confined to spikes/lut_mapping, not arch/src/macro or generated upstream code.
- **Cost/limits:** five mux4 instances per LUT; physical area/routing/timing comparison against actual existing mapping is pending. No new configuration storage or protocol-specific behavior. If later integrated, every workload pays any area/delay cost, including users not affected by simulation unknowns. No equal-area improvement or configured-fabric timing claim. LUT-cell/compiler/bitstream/native loaded integration and physical hardening remain required before promotion.

## D-048: Exclude decap fillers in isolated geometry replay
- **Date:**2026-10-06. **Status:** accepted one-field scratch physical experiment; frozen config unchanged.
- **Evidence:**37545941476 replays saved iteration52 with no routing and reproduces KLayout248 (1 M1.a,247 M1.b). Joining its exact marker coordinates to post-fill DEF and pinned LEF dimensions associates every marker with decap fillers:241 decap8-only,3 decap4-only,2 decap4/8 boundaries,1 decap8/fill2 boundary,1 decap4/fill2 boundary. Width marker lies in FILLER_185_58/decap8. This locates violations in inserted decap geometry, but does not yet establish that removing them resolves LVS67.
- **Decision:** replay the same authenticated3-marker ODB with only FILL_CELLS changed to plain fill1/fill2; extend downstream checks through LVS. No routing, signal/macro/netlist change, DRC waiver or frozen src/config change. Preserve full output views and marker databases.
- **Cost/limits:** fewer decap filler cells can reduce local decoupling and change power behavior; power/IR/noise implications require measurement before promotion. Plain fillers still provide their normal well/rail structures. Logic resources, bitstream and protocol behavior unchanged. The input's3 routing markers prevent claiming final routing certification or configured-fabric timing from this experiment. Clock target and constraints unchanged.

---

## D-001: Build on FABulous
- **Date:** 2026-09-25 · **Status:** Proposed (confirm in phase 0)
- **Decision:** Use FABulous for fabric generation, synthesis mapping, place and route, and bitstream generation, pinned to one release.
- **Reason:** Open source, supports custom fabrics and primitives, has a physical implementation flow and IHP precedent, and has been used on Tiny Tapeout before (Tiny FABulous).
- **Alternatives:** OpenFPGA (not developed in parallel); writing a fabric and toolchain from scratch (too much work for the schedule).
- **Evidence:** to be added in phase 0 (reference fabric demo).

## D-002: Domain-specific but protocol-agnostic
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** Specialize the fabric for protocol emulation, but never add a dedicated protocol block. Hard blocks and cell features must be general primitives useful to more than one protocol. Each addition needs profiling data, benefiting protocols, area cost, and cost to non-users.
- **Reason:** The brief rules out "a UART block, an SPI block and an I2C block"; generality after fabrication is the point.

## D-003: Design set and sealed held-out set
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** Optimize the architecture on a design set (UART, SPI controller, I2C controller, I2C target). Evaluate generality on a held-out set chosen and committed in phase 1, untouched until the hardware freeze.
- **Reason:** Without a held-out set, a specialized fabric can overfit to the protocols it was tuned on, and the generality claim can't be checked.

## D-004: Equal-area comparison
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** Architecture variants are compared at equal total area (fabric, configuration, routing, shell) and equal clock target.
- **Reason:** A variant using fewer LUTs is not better if its hard blocks cost more area than the LUTs saved.

## D-005: G0 is the fallback submission
- **Date:** 2026-09-25 · **Status:** Superseded by D-008 (a generic fabric holds ~96 LUT4s at 6x4; one UART needs ~215)
- **Decision:** The generic baseline fabric with the complete shell (phase 2) must be a valid, submittable chip before any specialization work.
- **Reason:** Guarantees a working entry if specialization runs late.

## D-006: Provisional pin allocation
- **Date:** 2026-09-25 · **Status:** Proposed (finalized in `ARCHITECTURE.md` §1, phase 1)
- **Decision:** Shell host interface on `ui[0]` CS_N, `ui[1]` SCK, `ui[2]` MOSI, `uo[0]` MISO, `uo[1]` IRQ. Everything else goes to the fabric: `ui[3..7]` (5 inputs), `uo[2..7]` (6 outputs), `uio[0..7]` (8 bidirectional, needed for open-drain I2C and 1-Wire).
- **Reason:** the TT `check-docs` step rejects an empty pinout, so `info.yaml` needs a pinout before the spec exists. SPI-like host port with polled status per OVERVIEW; IRQ is optional and can be dropped.
- **Alternatives:** host port on `uio` (costs bidirectional pins the protocols need); a 2-wire host port (fewer pins, slower loads).
- **Cost:** 5 of 24 pins go to the shell.
- **Evidence:** none yet; revisit with the pin needs of the design set and the showcase.

## D-007: Local tool PATH order
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** System `/usr/bin` comes first; `~/oss-cad-suite/bin` is appended to the end of PATH (`scripts/check_all.sh` and `scripts/gl_local.sh` do this themselves). Python runs only in `.venv`.
- **Reason:** CI's `test` and `lint` jobs use Ubuntu 24.04's apt Icarus 12.0 and Verilator 5.020, which are also the WSL system versions. The OSS CAD Suite ships its own newer Icarus and Verilator; appending it keeps the CI versions in front while still providing Yosys, nextpnr and SymbiYosys.
- **Evidence:** local `iverilog -V` 12.0, `verilator --version` 5.020 (Debian 5.020-1); `scripts/check_all.sh` and `scripts/gl_local.sh` pass (2026-09-25). Versions in `docs/VERSIONS.md`.

## D-008: A generic fabric is probably not a viable fallback at 6x4; revisit D-005
- **Date:** 2026-09-25 · **Status:** Accepted (Kanishk, 2026-09-25): G1 is the fallback only; the goal is still the full specialized architecture from phase 3. Supersedes D-005
- **Finding:** `docs/reports/capacity_early.md`, updated by the tile hardening `docs/reports/tile_cmos5l.md`: measured ~5.1K µm² per LUT4 at 97 % density on CMOS5L, so **~96 LUT4s** fit at 6x4 with margin. Earlier synthesis-only numbers follow. The stock FABulous LUT4AB tile costs ~4.5K µm² of cells per LUT4 on cmos5l (77 config bits per LUT, 53 % of the area). At 42–60 % density a generic 6x4 fabric holds roughly **60–90 LUT4s**. A scratch UART (TX + RX, 16-bit divisor) needs **~215 logic cells**.
- **Proposal:** the fallback submission becomes **G1 = G0 + the smallest set of general hard primitives that lets the design set fit** (first candidates: loadable counter/timer, shift register), instead of pure G0. G0 stays the baseline for the equal-area comparison (D-004), measured at equal area, even if it fits nothing.
- **Also worth trying before adding hard blocks:** a slimmer routing architecture and tile (fewer wires per channel, fewer config bits per LUT) than the stock general-purpose one.
- **Alternatives:** keep D-005 and shrink the design set (e.g. UART TX only); go to the hybrid fallback (OVERVIEW decision points) now.
- **Cost:** the fallback depends on hard-block integration (Yosys mapping, nextpnr, bitstream) working, which is a known risk (OVERVIEW top risks).

## D-009: Phase 0 decision point: a known path exists to put a FABulous fabric through Tiny Tapeout
- **Date:** 2026-09-25 · **Status:** Accepted (answer to the phase 0 decision point); integration choice Proposed
- **Answer:** yes. Tiny FABulous (`docs/notes/tiny_fabulous.md`) hardened tiles with LibreLane's `FABulousTile` flow, stitched them with `FABulousFabric`, integrated the fabric as a macro in a top-level LibreLane run, and submitted through TT's `custom_gds` action. Its tile library already has IHP-specific tiles.
- **Our plan (proposed):** harden the fabric as a macro locally (or in our own workflow), commit it under `macro/`, and integrate it in the **template's** `gds` job with a `MACROS` block. The TRIPWIRE R3 spike integrated the IHP SRAM macro this way and passed precheck and `gl_test`. This keeps the template's jobs, precheck and `gl_test` intact (CLAUDE.md CI rules). Fall back to Tiny FABulous's `custom_gds` route only if the template flow can't integrate the fabric; that needs a DECISIONS entry and the organizers' OK (phase 0 email question 2).
- **Next evidence:** harden one tile on cmos5l with `FABulousTile` (needs OpenROAD/KLayout/Magic locally: Nix or the LibreLane container).

## D-010: Patch the FABulous tile library for CMOS5L's 5-layer metal stack
- **Date:** 2026-09-25 · **Status:** Accepted (spike)
- **Decision:** use `mole99/fabulous-tiles` at 7999e5a (the Tiny FABulous tile library) with `spikes/tile_cmos5l/cmos5l.patch`, applied to a fresh clone in `build/`, never to the upstream checkout. The patch (1) gives `ihp-sg13cmos5l` its own routing-obstruction list (Metal1–Metal4 + TopMetal1) ahead of the `ihp-sg13*` entry, which lists Metal5/TopMetal2; (2) adds a `pdk::ihp-sg13cmos5l` section to the tiny library's `common.yaml`, with the power grid of the PDK's own LibreLane config (Metal4 vertical, TopMetal1 horizontal, 50 µm pitch) and `RT_MAX_LAYER: TopMetal1`.
- **Reason:** CMOS5L has only 5 metal layers (`libs.tech/librelane/config.tcl`: "M1-M4-TM1, no Metal5/TopMetal2"). The upstream IHP settings are for SG13G2 (7 layers) and reference layers that don't exist.
- **Consequence to watch:** one fewer signal layer than SG13G2, so the SG13G2 tile size and 96 % density may not route. Measured in `docs/reports/tile_cmos5l.md`.
- **Revision (run 2, same day):** `RT_MAX_LAYER: Metal4` (the TT CMOS5L top level routes only to Metal4; TopMetal1 is its power grid) and KLayout stream-out with the Magic stream-out/DRC/LEF/extraction and LVS steps skipped in the tile config (BUGS #2; the PDK has no CMOS5L LVS yet). Run 1 used `RT_MAX_LAYER: TopMetal1`. Run 3 adds a driver fix to `tiles.py`: apply `meta.substituting_steps` removals (the librelane CLI does, the driver did not).

## D-011: The `unit` workflow arrives with the first Python tool
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** phase 0's "add `lint` and `unit` workflows" is met by `lint` now; `unit` (pytest over `tools/`) is added in the same commit as the first Python tool with tests (phase 1: `tools/areamodel/` or `tools/refmodels/`). The phase 0 box is ticked for `lint`, the `gds` paths filter and concurrency, and marked as deferred for `unit` with this reference.
- **Reason:** there is no Python code yet; a `unit` workflow with nothing to test would pass without checking anything.
- **Meanwhile:** `fabric` (added early) runs the FABulous flow in CI.

## D-012: Close phase 0 with the organizer email outstanding
- **Date:** 2026-09-25 · **Status:** Accepted (Kanishk: "start phase 1, email doesn't matter")
- **Decision:** phase 0 is closed with its two email items marked waived, not passed. Phase 1 starts.
- **Reason:** the email's answers (eFPGA eligibility, a hardened macro inside the template flow) don't change phase 1's work. Every other phase 0 exit item has evidence.
- **Follow-up:** if the email is sent, log the date and the answer here.

## D-013: Held-out set sealed: WS2812, 1-Wire, SWD, CAN
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** `docs/design/HELDOUT.md`: H1 WS2812 TX, H2 1-Wire controller, H3 SWD host, H4 CAN 2.0A. PS/2 and JTAG stay free (stretch/design set).
- **Reason:** phase 1's criteria: a spread of timing-coded (H1, H2), clocked with turnaround (H3), bidirectional/open-drain (H2, H3, H4), and CRC plus bit-stuffing (H4). PS/2 and JTAG are too close to the design set (a device-clocked shift register, SPI-like shifting) to test generality.
- **Seal:** the commit that adds `HELDOUT.md` (hash recorded in the phase 1 checklist).

## D-014: Provisional user-design interface
- **Date:** 2026-09-25 · **Status:** Proposed (formalized in `ARCHITECTURE.md` v1, phase 1)
- **Decision:** every protocol user design exposes: `clk`, `rst_n` (from the shell; held low while the fabric is stopped or loading); its pins as input / output / output-enable signals; a host → design byte channel `h_wdata/h_wvalid/h_wready`; a design → host byte channel `h_rdata/h_rvalid/h_rready`; and an 8-bit `h_status` the host can read at any time. Settings (e.g. a UART divisor) are Verilog parameters fixed in the bitstream by default; a design may also offer a run-time register (`RUNTIME_*`) so both can be profiled.
- **Reason:** protocols have to be written and profiled before the shell exists; a byte channel in each direction plus status is the smallest host path that serves UART, SPI and I2C. Fixing settings in the bitstream is how an FPGA is normally used, and it is much cheaper: the UART is 171 LUTs with a fixed divisor and 262 with a run-time one.
- **Alternatives:** a memory-mapped register window (more flexible, more fabric logic); wider channels.
- **Revision (SPI controller):** the host → design channel carries a 1-bit `h_wlast` flag with each byte, marking the end of a transaction (e.g. SPI chip-select release); designs that don't need it ignore it.
- **Cost:** the shell must provide both byte channels (the write side with `h_wlast`) and the status read (ARCHITECTURE §2).

## D-015: The `unit` workflow (closes D-011)
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** `.github/workflows/unit.yaml` added with the first Python tool (`tools/refmodels/uart.py`): pytest over `tools/`, and the cocotb RTL tests of every design-set protocol (UART now, others as they land), with sigrok installed as the second decoder.

## D-016: Capacity go/no-go: GO for the specialized eFPGA (4 x 3 tiles + primitives)
- **Date:** 2026-09-25 · **Status:** Accepted (phase 1 decision point; revisit with the phase 3 measurements)
- **Evidence:** `docs/reports/capacity.md` (area model `tools/areamodel/`, tile hardening, profiling).
- **Decision:** continue with the pure specialized eFPGA, not the hybrid fallback. Planned G1: a 4 × 3 grid of LUT-size tiles next to a shell column; one tile slot holds primitives (2 loadable timers + 2 shift registers with bit count, settings in configuration bits); the host byte channel (holding register/FIFO, valid/ready, overrun) lives in the shell; I/O cells get input synchronizers, registered outputs and open-drain mode. That leaves 88 LUT4s.
- **Fit:** UART (~50 LUT4 with glue), SPI controller (~45) and I2C controller (~77) each fit 88. The I2C target (~220) does not; options in order: register-file primitive, smaller register map, showcase on the I2C controller. Running two protocols at once does not fit.
- **Primitive rules (D-002):** timer and shift register are used by 4 of 4 design-set protocols; host channel and I/O features are shell/I/O, not fabric blocks; the register file has one user so far and needs its own justification before it is built.
- **Alternatives:** hybrid (PIO-style sequencers + small fabric): not needed for 3 of 4; generic-only fabric: fits nothing (D-008).

## D-017: Tile power stripes on a global grid that the TT chip grid can land on
- **Date:** 2026-09-26 · **Status:** Accepted (spike; verified by the chip-level hardening)
- **Problem:** in TT's CMOS5L flow a user block has only vertical Metal4 power stripes (no TopMetal1), each ≥ 2.1 µm wide and running the full block height (precheck). A macro's Metal4 power pins must therefore be overlapped, same net, by those stripes; any chip stripe that crosses the macro anywhere else shorts to its wiring. Lessons from the TRIPWIRE R3 spike on `main` (IHP SRAM macro, 6 CI runs, `spikes/r3_sram/overlay/src/pdn_cfg.tcl`).
- **Decision:** the tiles' Metal4 power stripes are 2.1 µm wide at a pitch of **109.92 µm (half the LUT tile width, 219.84 = 2 × 109.92)**, with a tile-type offset so that, in the stitched fabric, every column's stripes sit on one global grid: fabric-local x = 20.00 + 109.92 k (VPWR) and + 4.1 (VGND). West-column tiles (W_IO4, NW_term, SW_term) use local offset 20.00; LUT-width tiles (LUT4x8_ha, N_term, S_IO2) and east-column tiles (E_IO4, NE_term, SE_term) use 61.28 (= 20.00 + 109.92 − 68.64, since every LUT-width column starts at 68.64 + 219.84 j). Tiles stacked in a column form continuous full-height power columns. The chip level uses the same pitch and width, offset to the macro's x position, with the R3 spike's pdn_cfg.tcl (it releases the macro during stripe generation and checks that every stripe crossing a macro lies inside same-net pins).
- **Why not per-tile 50 µm stripes:** tile widths (219.84, 68.64) are not multiples of 50, so no uniform chip grid can hit the stripes of every column.
- **Cost:** wider stripes take Metal4 routing tracks inside the tiles (2 × 2.1 µm per 109.92 µm, vs 2 × 1.0 per 50: about the same share, 3.8 % vs 4.0 %). IR drop with a 110 µm pitch: to check at chip level.

## D-018: Phase 1 spike top: 16-LUT fabric behind a minimal shell
- **Date:** 2026-09-26 · **Status:** Accepted (spike; replaced by the phase 2 shell)
- **Decision:** `tt_um_warp` = the fabric macro `warp_tiny` + `wp_fabric_cfg` (FABulous's bit-bang receiver and frame-configuration FSM, copied unmodified into `src/fabric_gen/`, + per-row frame registers and per-column frame selects). Pins: `ui[0]` RUN, `ui[1]`/`ui[2]` bit-bang config clock/data, `ui[3..6]` fabric inputs, `uo[0]` config active, `uo[2..5]` fabric outputs, `uio[0..7]` fabric bidirectional pins. Outputs and output enables are parked (0) unless RUN is high and no configuration session runs; the user design's reset and SYS_RESET are held during a session. Supersedes the D-006 pinout for this spike.
- **Reason:** phase 1 must harden a small fabric through the TT flow with live configuration (configuration latches driven from pins, not tied off). FABulous's own loader matches its bitstream format by construction.
- **Not yet:** the SPI-like host interface, loader checks (length, checksum, version) and host byte channels (ARCHITECTURE, phase 2).

## D-019: `src/config.json`: fabric macro placement and power grid
- **Date:** 2026-09-26 · **Status:** Accepted (spike; verified by the CI `gds` run and precheck)
- **Changes** (one entry per change, CLAUDE.md):
  1. `MACROS.warp_tiny`: instance `u_fabric` at (11.52, 7.56), orientation N; GDS/LEF from `macro/warp_tiny/`; netlists of the fabric and its 9 tile types. Location on the Metal2 (0.48) and Metal3 (0.42) track grids.
  2. `PDN_MACRO_CONNECTIONS`: `u_fabric VPWR VGND VPWR VGND`.
  3. `PDN_CFG`: `src/pdn_cfg.tcl`, the TRIPWIRE R3 spike's script (from `main`, unmodified below a WARP note). It releases the macro while stripes are built and fails the step unless every stripe over the macro lies inside same-net power pins and every macro pin is reached.
  4. `FP_PDN_VPITCH` 50 → **109.92**, `FP_PDN_VSPACING` **2.0**, `FP_PDN_VOFFSET` **20.64** (`FP_PDN_VWIDTH` stays 2.1): the chip stripes land on the fabric's power columns (D-017). The template marks these keys "do not change"; the R3 spike changed the same keys for the same reason and passed precheck.
- **Risk:** a 109.92 µm stripe pitch is wider than the template's 50 µm for the shell's standard cells (IR drop); PSM/IR report to be checked in the run.
- **Revision (2026-09-27, BUGS #9):** the first location (11.52, 7.56) put the fabric's pin-heavy west face (152 pins) and south face (67 pins) against the die edges; chip-level routing did not converge (run 36277723397). New location **(890.88, 113.40)**: east side of the die, centred vertically, west and south faces toward open core. x = 11.52 + 8 × 109.92 keeps the power-grid phase; `FP_PDN_V*` unchanged. Rule for any macro: check which faces carry its pins before choosing a location.
- **Revision 2 (2026-09-27, before the next run):** adopt the macro settings the R3 SRAM spike needed on CMOS5L (its `src/config.json` on `main`): `DRT_OPT_ITERS` **16** (a non-converging route fails in well under an hour instead of running to the 6 h limit, which cost ~4 h in run 36277723397); `MAGIC_MACRO_STD_CELL_SOURCE` `PDK`; `ERROR_ON_MAGIC_DRC` false (Magic's CMOS5L deck reports false errors inside macros; the precheck's KLayout DRC is sign-off); `ERROR_ON_ILLEGAL_OVERLAPS` false (chip stripes over the macro's Metal4 obstruction on its power columns); `MAGIC_EXT_ABSTRACT_CELLS` `["warp_tiny"]` (LVS treats the fabric as a black box). The macro's `nl` is now the port-only black box `src/warp_tiny.v` (not in `info.yaml` source_files), so synthesis and STA see only its pins; the fabric's full netlists stay in `macro/warp_tiny/` for simulation. Pre-run checks done: no TopMetal1/TopVia1 in the macro GDS (layers ≤ Metal4 + prBoundary), unique cell names, pin faces W 152 / S 67 / E 24 (Metal3/Metal2).
- **Revision 3 (2026-09-27, BUGS #11):** run 36293031051 passed `gds` and `gl_test` but failed the precheck pin check: the 38 µm channel east of the fabric got a short channel stripe from pdngen. Fabric moved to **x = 780.96** (11.52 + 7 × 109.92): the east channel (148 µm) holds a full grid stripe pair. Rule: beside a macro leave no channel or one that a full-height grid stripe pair crosses. Verified locally with TT's merged config before pushing: power grid (all LOOMPDN checks), 24 full-height stripes / 0 short, routing 0 overflow / 0 DRC.

## D-020: The template `fpga` workflow does not apply once the fabric is a hard macro
- **Date:** 2026-09-27 · **Status:** Accepted
- **Decision:** the template's manual `fpga` workflow (iCE40 build of `tt_um_warp`) is no longer run as a phase gate. Its last green run (36201219254) was on the placeholder design.
- **Reason:** since D-018 the top instantiates the hardened fabric macro `warp_tiny` as a black box (`src/warp_tiny.v`); an iCE40 build has no implementation for it. An FPGA prototype of WARP means synthesizing the generated fabric RTL (`macro/warp_tiny/warp_tiny.v` + tile RTL) onto a larger FPGA; that is phase 7 (optional), with its own build.
- **Workflow file:** unchanged (CLAUDE.md: never edit the template's jobs); it stays available for manual use.

## D-021: Shell v1 implementation clarifications to ARCHITECTURE §2–4
- **Date:** 2026-09-27 · **Status:** Accepted (ARCHITECTURE.md updated to match)
- **Decision:** the phase 2 shell (`src/wp_shell.v`) fixes points v1 left open or got wrong:
  1. **LOAD_BEGIN is also allowed in LOADING** (restarts the load). v1 allowed it only in UNCONFIGURED/LOADED/ERROR, so a host that lost a load midway (never sent LOAD_END) could only recover with the chip reset.
  2. **When load errors are reported:** a wrong ARCH_VERSION at LOAD_BEGIN (nothing is forwarded); a bad sync word or no words at all (BUGS #12), a LENGTH mismatch and a CRC mismatch at LOAD_END, checked in that order (0x13, 0x11, 0x12). A bad first word stops forwarding immediately; words beyond LENGTH are not forwarded. Reporting at LOAD_END means a host streaming LOAD_DATA never gets its error overwritten mid-stream.
  3. **ERROR_CODE priority:** a load error always replaces the code; a bad command (0x01) is recorded only when no error is pending. READ_STATUS clears it (and ch_overflow) once its ERROR_CODE byte has been clocked out.
  4. **Host timing** (from the two-flop synchronizers): SCK ≤ clk/8; CS_N falling to the first SCK rising edge ≥ 8 clk; CS_N high between transactions ≥ 4 clk. MISO changes right after each detected SCK rising edge.
  5. **Parking gate after the output registers:** `pin = reg & running`, so pins are 0 in the same cycle `running` drops (a register-only gate would leak one cycle). F1 is proved on this structure.
  6. **Channel FIFO depth 2** per direction (resolves the §7.3 OPEN item for now; revisit with the fabric's area). FIFOs are emptied whenever the design is not running.
  7. **FABulous's bit-bang receiver is removed** (`src/fabric_gen/bitbang.v`); the shell delivers words to `ConfigFSM` directly.
- **Reason:** found while writing the RTL, the host software (`tools/host/protocol.py`) and the tests; all are small and none changes the host command set or the STATUS layout.
- **Alternatives:** keep v1 as written (item 1 leaves a stuck state; item 3 loses the cause of an ERROR).
- **Cost:** none in area worth measuring; item 4 limits host SCK to 6.25 MHz at 50 MHz (a 3 K-word bitstream loads in ~16 ms).
- **Evidence:** `test/test.py` 12 pin-level tests (all pass locally 2026-09-27); `formal/f1_isolation.sby` (k-induction PASS 2026-09-27); `formal/f2_loader.sby`.

## D-022: Compile flow and real-bitstream tests for the current fabric
- **Date:** 2026-09-27 · **Status:** Accepted
- **Decision:**
  1. **`tools/compile/`** turns a user design + a pin map (YAML: user port → WARP pin, `.o/.oe/.i` for bidirectional pins; ARCHITECTURE §10, D-014) into a `.wbit` file and a JSON report (architecture version, tool versions, LC/IO/GBUF use, Fmax at the slow corner, pins, CRC, unmapped ports). Steps: a generated wrapper `warp_top` (one explicitly instantiated IOBUF per used IO cell, its IN/EN/OUT wired exactly as in the fabric, so value, enable and input are independent signals as the host channel needs, D-024; a GBUF on the clock; revised 2026-09-27 from tristate pads); Yosys `synth_fabulous` (pinned 0.66) with the tile library's primitives and with the IO pad mapping done explicitly (the pinned version's pad mapping targets the stock FABulous IO cell); nextpnr-generic `--uarch fabulous` on the fabric's pips/bels at the `nom_slow_1p08V_125C` corner, fixed seed; WARP's own bitgen (`tools/compile/bitgen.py`, BUGS #13).
  2. **Architecture identity** in `arch/warp_tiny/arch.yaml` (`arch_version` 0x0001, rows, macro path); `arch/warp_tiny/pins.csv` is the pin → IO BEL map; the fabric definition moved from `spikes/fabric_tiny/warp_tiny.csv` to `arch/warp_tiny/fabric.csv`. A unit test keeps arch.yaml, the shell's ARCH_VERSION, the host default and the committed bitstreams on one number.
  3. **`.wbit` format** (`tools/compile/bitfile.py`): magic, ARCH_VERSION, word count, CRC-32, then the words from the sync word on. The host library refuses a file whose ARCH_VERSION differs from READ_ID before sending anything (`checked_load_transactions`); the shell refuses it again at LOAD_BEGIN.
  4. **All 4 configuration rows are written**, the edge rows included (they hold the clock/reset IO and the GBUFs); FABulous 2.2's bitgen leaves them out by default.
  5. **Generated macro views for simulation:** the tile RTL FABulous generated in the tile build is exported with the macro (`macro/warp_tiny/rtl/`), next to the netlists; the fixed primitives come from the pinned tile library (`scripts/fetch_tiles.sh`). `test/Makefile` selects the fabric model: the black box (default, CI `test`), the RTL (`WARP_FABRIC=rtl`, CI `fabric`), or the macro's gate-level netlists (`GATES=yes`, CI `gl_test`).
  6. **Test bitstreams are committed** (`test/bitstreams/*.wbit` + their FASM and report), built by `scripts/build_test_bitstreams.sh` from `tools/compile/examples/`, because the template's `gl_test` cannot run the compile flow. The `fabric` workflow rebuilds them and fails if they differ (`--check`). They are build products of committed sources, not CI artifacts.
- **Reason:** PHASE2 needs the compile flow, a host that rejects foreign bitstreams, and `gl_test` with two real bitstreams; all of it has to work with the current 16-LUT fabric first so the G0/G1 fabric only changes `arch/` and `macro/`.
- **Alternatives:** FABulous's own `compile_design` (fixed project layout, the stock pad mapping, and bitgen with BUGS #13); running the compile flow inside `gl_test` (the template job cannot be edited).
- **Cost:** ~0.5 MB of generated tile RTL in `macro/warp_tiny/rtl/`; ~2.4 KB per test bitstream.
- **Evidence:** 2026-09-27 locally: `test/` 15/15 with `WARP_FABRIC=rtl` (counter4 and logic4 loaded over SPI and checked at the pins, one after the other in the same chip); `tools/compile` 9 pytest (bitgen equals fabulous_bit_gen word for word on all non-CLK features of both designs). counter4: 7/16 LCs, 162.6 MHz at the slow corner; logic4: 5/16 LCs (no register-to-register path).

## D-023: Simulating the fabric with real bitstreams: 4-state handling, and the gl_test fabric model
- **Date:** 2026-09-27 (revised the same day) · **Status:** Accepted
- **Context:** 4-state, zero-delay simulation of an FPGA fabric meets problems silicon does not have. Unused routing sits on default mux inputs and forms combinational loops, across tiles and inside them.
  (a) A loop that starts at X stays X, and the gate-level LUTs (synthesized gates, unlike the RTL's mux-tree LUT model) pass X on from inputs the configured function ignores: with the hardened macro's netlists, correctly loaded designs read X at their pins although all ~1,500 configuration latches held clean 0/1.
  (b) While one configuration is written over another, a half-written configuration can close a loop that rings; the simulator never advances past it.
  (c) Even with a complete configuration, a gate-level LUT's static hazard on an input its function ignores, fed back to that input through a default-routed loop, glitches forever in zero-delay simulation (seen with logic4 loaded after counter4 once the compile flow's IO wiring changed, 2026-09-27).
  In silicon a loop holds some definite 0/1 (a), a ring during a load (b) stops when the load completes (the design is held in reset and every pin parked meanwhile), and the gates have delay (c).
- **Decision:**
  1. **`gl_test` simulates the shell at gate level and the fabric macro from the RTL it was hardened from** (`test/Makefile`: `GATES=yes` defaults to `WARP_FABRIC=rtl`; the macro's generated RTL in `macro/<fabric>/`, primitives from the pinned tile library via `scripts/fetch_tiles.sh`). TT's check is then what it is for: our synthesized, hardened logic with real bitstreams through the real host interface. The macro's gate-level netlist can still be simulated locally (`WARP_FABRIC=gl`); CI run 36342012141 did so, 16/16, before the IO-wiring change.
  2. **Testbench modelling of the loops** (`tb.v` includes `test/fabric_settle_{rtl,gl}.vh`, generated by `scripts/gen_fabric_settle.py`): `tb.hold_x` holds the fabric's nets at X for the whole of a load (no ring can form; the configuration path, found by tracing the tile netlists, is excluded, and latches and flip-flops keep their state underneath the force); after the load `tb.settle_routing` pulses the inter-tile routing wires to 0 for 1 ns so each loop settles to a definite value, with the design still in reset. This is simulation modelling in the testbench; the tests use top-level ports only.
- **Gap and plan:** the macro's gate-level netlist is no longer exercised by CI with real bitstreams. It was synthesized by the tile flow from the same RTL, and its one CI run passed, but nothing checks the two are equivalent. Plan (phase 2/3): a per-tile-type formal equivalence check of each tile's netlist against its RTL (EQY/Yosys), which covers every configuration rather than a few bitstreams. In the OVERVIEW risk register.
- **Risk noted (silicon):** during reconfiguration a partially written configuration can form a ring oscillator for the duration of the load (b); nothing leaves the chip (pins parked, F1), it costs switching power only while loading. In the OVERVIEW risk register.
- **Alternatives:** unit-delay gate-level simulation (would need SDF annotation of the PDK cell models in the template's gl_test); loading an all-zero configuration between designs (the zero load itself passes through half-written configurations); forcing internal nets to 0 (leaves gates inconsistent with their inputs; hangs).
- **Evidence (local, 2026-09-27):** `scripts/gl_local.sh` (Yosys gate-level shell + fabric RTL + real bitstreams) 16/16; `WARP_FABRIC=rtl` 16/16; black box 13 + 3 skipped.

## D-024: G0 fabric layout and where the host channel enters the fabric
- **Date:** 2026-09-27 · **Status:** Accepted (G0 stitched 1016.64 × 669.06 µm; chip placement D-025)
- **Decision:** `arch/warp_g0/fabric.csv`: 4 × 3 `LUT4x8_ha` (96 LUT4+FF) framed by `W_IO4` (west), `E_IO4` (east), `N_IO` (north) and `S_IO2` (south) columns/rows plus corner terms. All tile types are already hardened on CMOS5L (N_IO added 2026-09-27: 219.84 × 56.7 µm like N_term, 0 DRC, 0 antenna). IO cells (BELs): west 12, east 12, north 4, south 8 = 36. Allocation:
  - user pins (ARCHITECTURE §1): FAB_IO0..7 on 8 west cells; FAB_IN0..4 and FAB_OUT0..5 on 11 east cells; clock and user reset on 2 south cells (as in warp_tiny);
  - host channel (§7.3): 11 signals into the fabric (h_wdata[7:0], h_wlast, h_wvalid, h_rready) and 19 out (h_wready, h_rdata[7:0], h_rvalid, h_status[7:0], h_attention). Each IO cell gives the fabric one input (its pad side) and two outputs (value and enable, both plain wires into the shell), so the 15 spare cells (4 west, 1 east, 4 north, 6 south) carry 15 in / 30 out: enough without narrowing h_status (resolves the §7.3 OPEN item).
- **Reason:** no new tile type (a 4-cell north IO tile would need its own definition, DECISIONS entry and hardening risk); keeps the §7.3 interface whole.
- **Alternatives:** a new N_IO4 tile; narrowing h_status to fit fewer cells; host channel only on the north edge (4 cells: too few).
- **Cost:** the enable output of a host-channel cell is used as a data bit, so the compile flow's pin map must name both roles (already supported: `.o`/`.oe`); the shell's host-channel wires spread over three fabric edges (chip-level routing, to watch in the 6x4 hardening).
- **Evidence:** pending the G0 stitch (`FABRIC=warp_g0 spikes/fabric_tiny/run.sh`) and the design-set synthesis check in `docs/reports/capacity.md` (only the SPI controller comes close to 96 LCs; G1 needs the primitives, D-008).

## D-025: G0 in the 6x4 chip: placement, placement density, routing derate, per-column frame decode
- **Date:** 2026-09-27 · **Status:** Accepted (evidence: local pre-flight; CI hardening 36353540402 on e5b1f98: `gds` 45.8 min, precheck pass, `gl_test` 17/17, routing DRC/LVS/antenna 0, setup WS +10.63 ns, hold WS +0.121 ns)
- **Context:** the 6x4 CMOS5L chip routes only on Metal2–Metal4, and **Metal3 is the only horizontal layer**. The G0 macro (1016.64 × 669.06 µm) fills the core's height except 34 µm, and nothing routes over it. All TT pins are in the top-left corner (x 30–191 µm). So every wire between the west (shell, TT pins) and the fabric's far faces shares a few Metal3 tracks in the strips above and below the fabric. The first placement's global routing had 9,290 overflows, almost all *over* the macro: the router pushed ~118 crossing nets through it.
- **Decision (`src/config.json`, `src/wp_frame_select.v`):**
  1. Macro at **(121.44, 30.24)**: x on the power-grid phase (11.52 + 109.92 k, D-017) with a 148 µm east channel that holds a full stripe pair (BUGS #11; x = 231.36 would leave 38 µm with none); y leaves 26.46 µm below (frame-strobe logic) and 7.56 µm above.
  2. **No standard cells in the east channel** (`FP_OBSTRUCTIONS` x ≥ 1148.16): the shell stays west, so shell-internal wires do not cross the fabric.
  3. **`PL_TARGET_DENSITY_PCT` 75** (default 60): the shell packs into the west column instead of spilling into the strips around the macro, where every cell adds crossing wires.
  4. **`GRT_ADJUSTMENT` 0.15** (default 0.3): global routing reserves less of each track for detailed routing; the strips are the scarce resource and the design is small (25 % of tracks used).
  5. **Per-column frame decode:** FABulous's `Frame_Select` needs all 20 one-hot frame bits at every column; `wp_frame_select` takes a 5-bit frame number and decodes it under its column, so 11 wires run along the fabric instead of 26. Same behaviour for every bitstream with one frame per header (all the compile flow writes).
- **Measured (global-routing overflow, local LibreLane):** first placement 9,290 → y moved up 8,210 → east channel blocked 4,734 → per-column decode 4,153 → **density 75 % + derate 0.15: 23**.
- **Alternatives:** no IO on the fabric's east face (all user pins on west/north/south cells: needs an east edge tile without IO, a rebuilt macro, and one fewer fabric input; kept as the fallback if detailed routing fails); a larger TT tile (cost; the crossing problem stays).
- **Evidence:** local `scripts/preflight.sh` 2026-09-27 (Nix LibreLane 3.0.0, TT merged config): global-routing overflow 23, **detailed routing 0 violations, 0 antenna**, 22 vertical Metal4 power stripes all full height. G0 RTL suite 17/17 with the per-column decode. CI hardening: to be recorded here.

## D-026: G1 hard primitives: timer and shift register (D-002 entry)
- **Date:** 2026-09-27 · **Status:** Accepted 2026-09-28 (ARCHITECTURE §8's method complete: built, proven (F4), Yosys mapping, nextpnr placement, bitstream configuration, and compiled user designs using both blocks loaded through the host interface on the hardened chip: `test_prims`, `test_uart` in CI `gl_test` 36367067731)
- **Decision:** G1 adds two general primitives (ARCHITECTURE §8, cycle-exact spec v2), placed in a primitive tile that takes one LUT-tile slot of G0:
  - **`wp_timer`** (`arch/prims/wp_timer.v`): loadable 16-bit down-counter with terminal count; config RELOAD[15:0], ONESHOT; ports rst, load, half, en → tc.
  - **`wp_shift`** (`arch/prims/wp_shift.v`): 8-bit shift register with a step count; config LEN[3:0], MSB_FIRST; ports rst, load, step, sin, d[7:0] → sout, done, q[7:0].
  - Planned tile content: 2 timers + 2 shift registers (32 block inputs, like a LUT tile's 32 LUT inputs; 22 outputs spread over the tile's 32 output muxes), clocked by the tile's global clock. **Protocol-agnostic:** no protocol state machine, framing or bus behaviour is in hardware; each block is a counter or a shifter any protocol can use.
- **Profiling data behind it** (`docs/reports/profiling.md`, ranks 1–2): counters are the largest function (23 % of the design set's 648 LUT4s): upper-bound saving 150 LUTs + 51 FFs (UART 63, I2C controller 48, SPI 24, I2C target 15); shift registers with bit counts 17 %: 111 LUTs + 56 FFs. The real compile flow confirms plain G0 fits none of the four (`docs/reports/g0_results.md`: SPI 95, UART 127, I2C controller 160, I2C target 205 LCs of 96).
- **Protocols that benefit:** timer: UART (2), SPI controller (1), I2C controller (1), and the I2C target's timeout if added; shift register: all four (UART TX/RX, SPI MOSI/MISO, I2C data both ways).
- **Area (measured 2026-09-27):** the primitive tile `PRIM2T2S` (`arch/tiles/PRIM2T2S`, generated by `scripts/gen_prim_tile.py` from the LUT tile) hardened on CMOS5L in the LUT tile's footprint, 219.84 × 185.22 µm, with 35,094 µm² of standard cells (92.3 % utilisation) against the LUT tile's 36,047 µm² (94.8 %): **0.97 × a LUT tile**; routing 0 DRC, KLayout DRC 0, antenna 0. Phase 1's estimate was 1.07 ×; before: estimated 1.07 × a LUT tile per primitive tile (`capacity.md`: 2,751 µm² per timer and 1,538 µm² per shift register including configuration bits, against ~740 µm² per LUT4 without routing); measured when the tile is hardened. **Cost to protocols that don't use it:** the slot's 8 LUT4s (G1 = 88 LUT4 + 2 timers + 2 shift registers, against G0's 96); a design using neither block loses 8 % of its logic capacity.
- **Verification so far:** F4 (`formal/f4_prims.sby`): each block equals a spec model written from ARCHITECTURE §8 for all configurations and inputs, unbounded (k-induction), 2026-09-27; `test_internal/test_prims.py`: RTL against the independent Python reference model (`tools/refmodels/prims.py`, 28 property tests), random configurations and stimulus, cycle by cycle.
- **Tools (2026-09-27):** users instantiate `WP_TIMER #(.RELOAD, .ONESHOT)` / `WP_SHIFT #(.LEN, .MSB_FIRST)` (`tools/compile/prims/warp_prims.v`); Yosys keeps them as the BEL cells (`warp_plib.v`) with one parameter per configuration bit, nextpnr places them on `PRIM2T2S`, and the bitstream sets the bits (checked on `tools/compile/examples/prims2`). The G1 fabric (`arch/warp_g1`, `macro/warp_g1`) has G0's size and ports.
- **Measured benefit (`docs/reports/g1_results.md`, local):** with the same sources and flow, G1 places UART 29, SPI controller 47 and I2C controller 70 of 88 LCs; G0 places only the SPI controller (86 of 96; UART 124, I2C controller 115). The I2C target fits neither (205).
- **Still to do before Accepted (ARCHITECTURE §8's method):** G1 in the chip (one hardening), and a compiled user design using each block after loading through the host interface (`test/test_bitstream.py`); the full equal-area comparison against G0 (D-004) in phase 3.

## D-027: G1 replaces G0 in the chip
- **Date:** 2026-09-27 · **Status:** Accepted (CI 36367067731 on d6f5dcd: `gds` 43.6 min, precheck pass, `gl_test` 19/19, routing DRC 0, LVS/antenna/Magic 0, setup WS +10.73 ns, hold WS +0.143 ns)
- **Local pre-flight (2026-09-27, LibreLane 3.0.0 Nix):** global-routing overflow 20 (G0: 23), power stripes 22/22 full height, but **21 detailed-routing violations**, all on `clk`: its route from the TT clock pin drops through the 7.6 µm strip above the fabric onto the macro's Metal4 blockage near its top-left corner (x ≈ 137.7 µm, y 653–699 µm). The G1 LEF is byte-identical to G0's apart from the name, and G0 routed with 0 violations in CI (LibreLane 3.1.0.dev3) with the same floorplan; the netlist differs only in the architecture-version constant. So this is placement noise at a known tight spot (D-025), not G1's macro. CI hardening decides; if it fails there, the next hardening moves the macro down one row (7.6 → 11.4 µm above it) as its one change.
- **Context:** G0 is hardened and green in CI (36353540402) but runs only the SPI controller of the design set; G1 (D-026) runs UART, SPI controller and I2C controller in the same macro size (`docs/reports/g1_results.md`). The phase 2 fallback submission needs protocols that run.
- **Decision:** `arch/CURRENT` = `warp_g1`, ARCH_VERSION 0x0003 (shell parameter, `tools/host/protocol.py`, `arch/warp_g1/arch.yaml`). `src/config.json` changes only the macro's name and files (`MACROS.warp_g1`: `macro/warp_g1/warp_g1.{gds,lef}`, black box `src/warp_g1.v` generated from the macro RTL; `MAGIC_EXT_ABSTRACT_CELLS`). Location, orientation, obstruction, density and routing derate stay as D-025: the G1 macro has G0's size (1016.64 × 669.06 µm) and identical ports, and its pin placement comes from the same fabric flow. This is the one hardware change of the next hardening.
- **Tests:** the chip suite's bitstreams are rebuilt for G1 (`scripts/build_test_bitstreams.sh`), plus `test_prims` (both block types configured by a real bitstream) and `test_uart` (the design-set UART on the primitives, through the host interface). The RTL fabric model includes `arch/prims/*.v`.
- **Consequence:** G0 stays in `arch/warp_g0` and `macro/warp_g0` as the equal-area baseline (D-004); its bitstreams are no longer loadable on the chip (architecture check).

## D-028: Compile flow uses nextpnr 0.11.1 for hard-primitive timing
- **Date:** 2026-09-27 · **Status:** Accepted
- **Context:** BUGS #17: the pinned nextpnr (0.10-82, OSS CAD Suite 2026-06-29) gives no timing arcs to custom BELs, so every path through `wp_timer`/`wp_shift` was untimed and G1 Fmax figures were optimistic. Upstream nextpnr's FABulous back end reads per-BEL-type arcs from `.FABulous/placement_estimate.txt` since 2026-07.
- **Decision:** the compile flow (`tools/compile`) takes nextpnr-generic 0.11.1-34-gc4fbb55a from OSS CAD Suite 2026-09-27 (`scripts/fetch_nextpnr.sh`, `~/.cache/warp/ocs-2026-09-27`; `WARP_NEXTPNR` overrides); Yosys and FABulous stay on the 2026-06-29 suite (FABulous 2.2 pins it; newer Yosys breaks `synth_fabulous`, docs/VERSIONS.md). The primitives' arcs come from OpenSTA (`tools/timing/`) into `macro/<fabric>/fabulous/.FABulous/placement_estimate.txt` (`scripts/gen_prim_timing.py`, generated; margins clock-to-out ×1.5, setup/combinational ×3.0, set by a cross-check against STA of the hardened tile, `tools/timing/tile_check.sh`). A fabric with primitives and no arcs is a compile error.
- **Check:** on the G1 fabric files without the new file, 0.11.1 produces byte-identical FASM and the same Fmax as 0.10-82 for uart16, spi8, i2c8. With the arcs (final margins): UART 90.7 MHz, SPI controller 78.0, I2C controller 53.0 (slow corner).
- **Cost:** a second tool download in CI (`fabric`, cached) and locally; nextpnr warns that `bel.v3.txt` is absent (only needed for per-instance arcs; not used).

## D-029: Phase 2 decision point: G1 is a valid fallback submission
- **Date:** 2026-09-28 · **Status:** Accepted
- **Question (OVERVIEW decision point, end of phase 2):** is the chip as it stands (shell + G1) a submission that meets the competition's required protocols if later phases slip?
- **Evidence:** G1 hardened in the 6x4 chip with precheck and `gl_test` 19/19 (CI 36367067731); UART, SPI controller and I2C controller compile onto it (29, 47, 70 of 88 LCs; nextpnr slow-corner estimates 90.7, 78.0, 53.0 MHz with primitive arcs, D-028) and pass pin-level tests through the host interface on the fabric RTL (21/21 locally; the SPI and I2C chip tests reach CI `gl_test` with the next push); F1 (unbounded), F2 (BMC 84), F4 (unbounded) pass (`docs/reports/formal.md`).
- **Decision:** yes, G1 is the fallback: UART, SPI and I2C (controller side) run on it.
- **What is missing for a stronger submission:** the I2C target (does not fit, `docs/reports/g1_results.md`); an SPI target design; protocol rates on the chip clock (only nextpnr estimates, no STA cross-check yet); the phase 3 equal-area comparison of variants; held-out evaluation (phase 4); any hardware test.

## D-030: Phase 3 candidate 1: timer with a registered terminal count (measured; not kept alone)
- **Date:** 2026-09-28 · **Status:** Measured, not kept on its own (parked: `build/c1/parked/`, not committed)
- **Need (data):** `docs/reports/g1_limits.md`: every design-set critical path goes through a primitive; the timer's clock → `tc` arc (2.98 ns, a 16-bit compare after the counter) was the largest primitive arc.
- **Change:** `wp_timer` keeps a flop `zero` equal to (count == 0), computed a cycle ahead from (count == 1) and the static configuration; `tc` = en & armed & zero. Same ports and cycle-exact behaviour: F4 re-proved unbounded (k-induction) with the invariant zero == (count == 0) asserted; white-box tests against the Python model pass. Protocols that benefit: every timer user (UART, SPI, I2C controller). Cost to non-users: none (same tile, same ports).
- **Measured:** standalone slow corner: clock → `tc` 2.98 → 0.88 ns; input setup 1.40 → 1.47 ns; area 2,428 → 2,416 µm² (no cost). With the arcs in the compile flow (same margins): UART 90.7 → 100.5 MHz, SPI controller 78.0 → 76.2, I2C controller 53.0 → 52.1. The worst design is limited by paths **into** the timer (its input setup, ×3.0 after the hardened-tile check), which this change does not touch.
- **Decision:** not kept alone: the design set's minimum Fmax (I2C controller) does not improve. The real limit is physical: the primitive tile is hardened with the tile library's settings, which disable the resizer and design repair (`arch/tiles/PRIM2T2S/config.yaml`), so a NOR inside the timer drives 33 loads unbuffered (2.90 ns, `tools/timing/README.md`). Next candidate (D-031): harden the primitive tile with buffering/repair of the primitives' internal nets, then re-measure; this change is re-evaluated together with it.

## D-031: Phase 3 candidate 2: primitive tile hardened with design repair (measured; not feasible)
- **Date:** 2026-09-28 · **Status:** Not feasible at the tile's size; not kept
- **Need (data):** D-030: the design set's slowest path ends inside the timer, after an unbuffered NOR driving 33 loads (2.90 ns) in the hardened `PRIM2T2S`; the tile library's flow has no design-repair step (its config also nulls it: "don't resize the buffers").
- **Tried (local tile runs, 2026-09-28):** (1) removing the library's null for RepairDesign: no effect (the FABulousTile flow has no such step); (2) inserting `OpenROAD.RepairDesignPostGPL` after `OpenROAD.AddBuffers` (the tile driver in `build/tile_cmos5l` extended to apply step insertions): repair fixed 106 fanout violations and 1 slew violation but added 153 output-port buffers and 58 tie cells, and detailed placement failed; (3) the same without output-port buffers and tie separation: still 106 fanout violations (the tile SDC's max fanout 10), and detailed placement failed again.
- **Result:** the primitive tile is 92.3 % utilised in the LUT tile's footprint (D-026); there is no room for the buffering the timer's control nets would need. Keeping the footprint (so the fabric grid and macro stay the same) rules this out; a larger primitive tile would change the fabric and the equal-area comparison.
- **Decision:** not kept; the tile config is restored. G1 keeps its timing model (`tools/timing/README.md`): every design-set protocol still estimates above 50 MHz (I2C controller 53.0). D-030 stays parked. Options left if timing becomes binding (e.g. a held-out protocol in phase 4): restructure the timer's control logic in RTL to lower its fanout, or a primitive tile with one timer fewer.

## D-032: Organizers: an eFPGA entry is accepted; the software side is required
- **Date:** 2026-09-28 · **Status:** Accepted (requirement)
- **Source:** reply from the competition organizers to Kanishk's email (2026-09-28; paraphrased): an eFPGA entry is fine; the blog describes a CPU-style approach only because it is the most common; what counts is that the chip can be reprogrammed after fabrication to support new protocols, within its timing and I/O limits. The main extra thing expected is **the software side**: (1) the flow from a protocol description to a bitstream, (2) how the bitstream gets loaded onto the chip, and (3) working examples for the supported protocols (UART, SPI and I2C to start); the equivalent of a CPU entry's assembler and example programs.
- **Where WARP stands:** (1) `tools/compile` (Verilog + pin map → `.wbit` with report, D-022/D-028); (2) the shell's checked SPI loader (ARCHITECTURE §3, F2) and `tools/host/protocol.py` (builds and checks every host transaction), exercised through the chip's pins in `gl_test`; **missing: a loader that runs on real hardware** (the Tiny Tapeout demo board drives the chip from its RP2040, MicroPython); (3) `protocols/uart`, `spi_ctrl`, `i2c_ctrl` compile onto the chip's fabric and pass through the host interface on the hardened netlist (`gl_test` 21/21).
- **Plan changes:** phase 4 adds "loader for the Tiny Tapeout demo board" and "end-to-end examples (source → bitstream → load → run) for UART, SPI and I2C"; phase 5's user guide (`docs/USER_GUIDE.md`) covers exactly the three items above. Held back from claims until tested on hardware: anything the board loader has not done on a real board (CLAIMS rules; no hardware yet).

## D-033: Final architecture: G1 (phase 3)
- **Date:** 2026-09-28 · **Status:** Accepted (pending the `hw-freeze` tag by the user)
- **Data:** `docs/reports/architecture_comparison.md` (equal area): G1 places 3 of the 4 design-set protocols against G0's 1, all three above 50 MHz in the timing model; the measured candidates did not improve the design set (D-030: worst design 53.0 → 52.1 MHz; D-031: not feasible), and the unbuilt ones fail on the data (`docs/reports/g1_limits.md`): LUT tiles with two control sets (3–7 control sets per design vs 11 LUT tiles: not binding), a second primitive tile (no design-set user, costs 8 LUT4s), a register-file tile (the I2C target would still need ~105–110 LCs of 80).
- **Decision:** the final architecture is **G1** as hardened at 3047dea (CI 36383587262: precheck pass, setup WS +12.48 ns at 50 MHz, `gl_test` 21/21), including the BUGS #18 reset fix. No further fabric changes; after `hw-freeze`, hardware changes only for logged bugs.
- **Not reached:** the I2C target does not fit (169 LCs of 88). It stays a design-set protocol that the final architecture does not run; I2C is supported through the I2C controller.

## D-034: Phase 3 candidate 3: register file for the I2C target (measured; does not make it fit)
- **Date:** 2026-09-28 · **Status:** Measured, not kept
- **Context:** the user chose to keep the hardware open to look for a way to fit the I2C target (the one design-set protocol G1 does not run).
- **Measured:** the tile library's `RAM_32x4_2R_1W` (32 × 4, two read ports, one write port; two side by side for 8-bit registers) holding the I2C target's registers (bus read on one port, host read on the other, shared write port; experimental source `build/c3/i2c_target_rf.v`, not a protocol file), synthesized on G1's cells: **4 registers 169 → 123 LCs, 2 registers 123 → 110 LCs**. A tile holding the register file would take a LUT slot (80 LUT4 left).
- **Why it still does not fit:** after the register map, the design is ~110–120 LCs of bus state machine, host command decoding, status and port logic, about 1.5 × the fabric. Yosys's generic LUT4 mapping agrees (D-033). The fabric cannot grow in the 6x4 chip: the macro already spans the core's width beside the shell column, and a fifth tile column (219.84 µm) does not fit.
- **Decision:** not kept. No fabric change we can build at 6x4 makes the I2C target fit. Remaining options are on the design side (a much smaller I2C target: fewer features, not fewer registers) or scope (document the I2C target as not supported; I2C is supported through the I2C controller). The user decides (hardware kept open).

## D-035: I2C target not supported on the chip; hardware freeze on G1
- **Date:** 2026-09-28 · **Status:** Accepted (decided by the user)
- **Context:** D-033/D-034: no fabric change buildable at 6x4 makes the I2C target fit (169 LCs of 88; 110–123 even with a register-file tile). The phase 3 exit item "all design-set protocols recompiled and passing on the final architecture" cannot pass as written.
- **Decision:** the I2C target is **not supported** on this chip and leaves the set of protocols the chip is claimed to run; it stays in `protocols/i2c_target` as a tested RTL design (its tests still run in CI) with the fit result documented. I2C is supported through the I2C controller; the organizers' list (UART, SPI, I2C, D-032) is covered. The phase 3 exit item is amended to "every supported design-set protocol" (UART, SPI controller, I2C controller). The hardware freezes on G1 as hardened at 3047dea (D-033); the user tags `hw-freeze`.
- **Consequence:** no claim of I2C target support (`docs/CLAIMS.md`); `protocols/i2c_target/README.md` says it does not fit.

## D-036: Phase 4 showcase: one chip, six protocols, switched at run time
- **Date:** 2026-09-28 · **Status:** Accepted
- **Context:** the planned showcase (I2C target with fault injection, PHASE4) cannot run: the I2C target does not fit the frozen chip (D-035). The optional concurrency demo does not fit either: every pair of the protocols that run exceeds the fabric (88 LCs) or its 2 timers + 2 shift registers (UART alone uses all four blocks; SPI + SWD need 91 LCs).
- **Decision:** the showcase is the project's core claim itself: a single simulated chip, never reset, loads six bitstreams one after another through the host interface (UART, SPI controller, I2C controller, WS2812, 1-Wire, SWD) and each one works against its independent reference device on the pins (`test/test_bitstream.py::test_showcase_protocol_switching`). Three of the six are held-out protocols the architecture was never tuned for.
- **Consequence:** PHASE4's showcase items are amended accordingly; the fault-injection idea is covered by the mutation campaign (`docs/reports/mutation.md`).

## D-037: Reopen architecture exploration against broader communication workloads
- **Date:** 2026-09-28 · **Status:** Accepted (user direction; exploration only)
- **Context:** G1 is the measured baseline: an 88-LUT4 fabric with two timers and two shift registers. It runs six protocol personalities sequentially, while the G1/G0 comparison measured fit and timing rather than simultaneous independent links. The user wants the eFPGA architecture itself made as capable and distinctive as possible for general communication, without protocol-specific hard blocks.
- **Decision:** reopen phase 3 architecture exploration. Preserve G1 and `hw-freeze` as the known-good baseline; the tag records the previous candidate and does not prohibit a separately versioned successor. Do not change silicon RTL, `arch/`, `macro/`, `info.yaml`, or the architecture contract until candidate designs have a written spec and comparative measurements.
- **Method:** compare alternatives at the same total chip area and clock target (D-004), using a workload matrix that includes supported roles, throughput, response latency/jitter, concurrent operation, host servicing, routed fit, and timing. Keep protocol behavior in programs or user fabric; hard resources must remain reusable across unrelated communication tasks (D-002). The already-revealed held-out set is training data for this revision; choose and seal a fresh held-out set before tuning the successor.
- **Candidates to screen:** (1) G1 unchanged baseline; (2) FABulous-specific configuration/interface remapping and a smaller 5 × 3-grid tile; (3) shared-program, independently paced event lanes connected to the LUT fabric; (4) a small pure sequencer fabric as a control architecture; (5) rebalanced routing graphs; (6) generic CRC/LFSR datapaths. `docs/reports/architecture_screen.md` and `docs/reports/architecture_research.md` contain the initial measurements and research; none selects a successor. Any sequencers expose generic pin wait/read/write, relative or absolute timing, shift/data movement, capture, and bounded queues, never UART/SPI/I2C opcodes.
- **Acceptance:** a successor is preferred only if exact-area, routable results improve a stated objective across the training suite and do not regress the sealed suite beyond an explicit tradeoff. Demonstrate at least one useful simultaneous communication/monitoring behavior, not only sequential reconfiguration. Run full chip hardening and end-to-end tests before replacing G1 as the submission candidate.
- **Evidence and limits:** `docs/design/ARCHITECTURE_EXPLORATION.md`; the shared-image lane, ready/valid bridge and 8-/16-word RAM/configuration-image screens are in `spikes/event_lanes/` and `docs/reports/architecture_screen.md`. The user transform compiles separately to G1 (17/88 LUT4s), but the event macro, config mapping and physical lane-to-fabric route have not been built. PRISM prior art is expanded in `docs/notes/prior_art.md` and `docs/reports/architecture_research.md`. Baseline evidence remains `docs/reports/architecture_comparison.md`, `g1_results.md`, `g1_limits.md`, and `heldout_results.md`. This decision authorizes design-space exploration, not selection of a new architecture.

## D-038: Compact 5 × 3 boundaries and preserve configuration locality (scratch)
- **Date:** 2026-09-30 · **Status:** Proposed for promotion; experiments authorized under D-037. Frozen G1 is unchanged.
- **Decision:** Test smaller physical north/south tiles with the existing 5 × 3 graph and primitives; preserve separate column decoders through supported deferred flattening; retain cell rows outside the macro and measure explicit decoder placement. A separate scratch wrapper may suppress only frame-strobe inputs proven unconsumed by a hash-bound trace through the generated fabric. No configuration-storage bit or consumed strobe is forced.
- **Data:** 37.80/49.14 µm north/south tiles: all 14 variants and stitched macro pass routing/KLayout checks; macro is 1120.32 × 676.62 µm, 758,030.92 µm². Full SPI/UART RTL and mapped-shell tests pass. Matched full-shell GRT overflow falls from 11,405 to 1,523 with decoder locality and a one-row vertical halo. Tighter 34.02/45.36 µm base tiles also pass; their remaining variants/stitch are in progress. The generated-fabric input trace consumes all 160 data inputs but only 92 of 140 strobe inputs, with per-column counts 4/17/17/17/17/17/3.
- **Who benefits:** every mapped user design shares this physical/configuration interface; no protocol is singled out and no protocol block is added. Resources remain 112 LUT4s, two timers and two shifts. Only the existing design-set UART image is used for the load test; no held-out workload is touched.
- **Area cost:** the measured compact macro saves 29,643.67 µm² relative to its 1120.32 × 703.08 µm predecessor. Whole-chip area/clock superiority against G1 is not established. Suppressing unused strobes has only a preliminary synthesis screen; routed cost remains open.
- **Cost to non-users:** tighter placement/routing margin and potentially harder tile hardening; physical timing may change and must be measured. There is no logical resource loss in the edge-only change. The unused-strobe wrapper retains the bitstream format; static tracing and real loading test it, but it has not been selected.
- **Further placement data:** the combined masked/early-release/Metal1 pipeline gives 155 overflow / 362,577 µm. Narrowing middle-row placement fences to 21.12 µm gives 67 / 314,294 µm on the same macro and clock target; repairs retain the 0.1 ns extra hold margin. Detailed routing is active, not passed. A south-only 672.84 µm geometry is also being stitched from six new zero-DRC variants plus eight checked reused views.
- **Rejected screens:** shifting the compact macro upward to y=22.68 µm worsened overflow to 3,264; the original wide exclusive row-register regions crowded the remaining shell and worsened overflow to 174,271 despite fewer hold buffers. Those dimensions are rejected; the narrower row-fence experiment above remains open.
- **Evidence:** `spikes/compact_edges/README.md`, WORKLOG sessions 36–37, ignored run artifacts cited there. Full-chip detailed route/DRC/precheck, macro timing and full gate-level loading remain open. No claim that this beats frozen G1 or competitors.

## D-039: Share the shell's registered configuration word with its serial CRC (scratch)
- **Date:** 2026-10-05 · **Status:** Experiment under D-037; not selected for frozen G1.
- **Decision:** In one isolated compact-chip variant, replace the CRC engine's captured 32-bit shift register with a bit selector reading `cfg_word`, the shell's existing registered configuration output. Keep the reflected IEEE CRC, big-endian byte order, 32 processing cycles, loading format, command behavior, clock and fabric unchanged. The data-assembly wire `{pay, rx_byte}` is not stable after the word-complete edge and must not be used for this sharing.
- **Data:** Lead real-shell DRT pass 0 reaches 268 markers at iteration 16, all west of the macro (`compact_narrow_rows_drt_20261005/drt-run-0`); 211 are Metal2. CRC-related shell nets occur in the west-channel hotspot. Baseline CRC RTL stores 32 CRC bits, 32 copied word bits and a six-bit counter. The scratch replaces the copied word with a five-bit selector plus active flag. This is an RTL state count, not a physical area saving.
- **Who benefits:** all bitstreams use the same management loader; no protocol-specific engine or new user resource is added.
- **Cost:** adds a word-bit selection mux and fanout on `cfg_word`; whole-chip area, timing and congestion must be measured on the same lead macro. Benefit is unestablished until physical comparison. The helper requires a stable word during busy and cannot replace a generic standalone capturing CRC engine.
- **Safety and acceptance:** monitor word stability during the real SPI load, compare every cycle against the original CRC and final results against zlib, run the F2 loader check at its existing 84-cycle bound and 60-cycle cover, and run the real UART image through the shell. Do not promote based on removed registers alone; judge placement/GRT/DRT and timing. Invalid or overlength words are never accepted; their CRC need not match a rejected payload, but error precedence and inability to RUN must remain covered.
- **Evidence:** `wp_crc32_shared_word.v`, optional `--shared-word-crc` preparation / `WARP_COMPACT_SHARED_CRC=1` route mode, `test_internal/test_shared_crc.py` and the shell stability monitor. Unit and real SPI/UART/STOP pass; stability checked for all 26,944 CRC processing cycles. F2 BMC passes at 84 cycles; cover reaches step 52 within 60. Matched GRT gives 93 overflow / 285,645 µm versus 67 / 314,294 µm for the lead, with 512 versus 605 hold buffers. Pre-PDN mapped shell area is 44,443.7 versus 46,753.5 µm²; final routing remains open. Full evidence and limitations: `docs/reports/compact_shell_crc.md`. Frozen RTL, hardware contract and submission configuration are unchanged.

## D-040: Local frame-index branch buffers (scratch physical experiment)
- **Date:** 2026-10-05 · **Status:** Experiment under D-037/D-038, no promotion.
- **Decision:** Add one non-inverting `sg13cmos5l_buf_2` per column for each of frame_idx bits0/1 in an isolated pre-placement OpenDB variant. Only decoder input loads are moved to each local branch; global source logic, configuration storage and bitstream format are unchanged. Added cells join existing column placement groups; supply pins connect to existing VPWR/VGND. This is an implementation-buffering experiment, not a new fabric resource or protocol block.
- **Data:** Saved lead repair2 antenna check identifies a long frame_idx[1] buffered branch feeding column6, cumulative Metal3 ratios201.56–203.25 against200. Loads span x72.96–1154.88µm. CRC duplication reduction does not address this configuration branch directly (`docs/reports/compact_route_diagnosis.md`).
- **Who benefits:** all bitstreams share configuration decoding; protocol behavior remains entirely programmable.
- **Cost:** 14 buffers,127.008µm² added cell area before later repair, extra propagation and routing loads. No LUT/timer/shifter resource loss; all designs pay loading-path timing/power overhead. Real configuration setup/hold and final antenna/DRC must pass.
- **Initial matched result:** same sharedCRC/compact macro/20ns target/0.1ns hold margin/row fences: GRT overflow93→27, estimated wirelength285645→281448µm, hold buffers512→522. Driver correctly stops at nonzero-overflow guard. A separate two-iteration DRT diagnostic is active. Actual post-CTS mapped-shell/RTL-fabric SPI/UART/STOP passes (23.92s), with all14 buffers present; no timing or physical success claimed.
- **Evidence:** `buffer_cfg_branches.tcl`, optional `WARP_CFG_BRANCH_BUFFERS=1` in the existing locality stage; `chip_shared_crc_cfgbranches/runs/compact_local_grt`, `shared_crc_cfgbranches_20261005.log` under `build/arch_explore/compact_edges`. Frozen source, architecture contract and submission config unchanged.

## D-041: Pre-place antenna protection at local configuration branch inputs (scratch)
- **Date:** 2026-10-05 · **Status:** Isolated physical experiment under D-037, not selected.
- **Decision:** Optional `WARP_CFG_BRANCH_DIODES=1` adds one process `sg13cmos5l_antennanp` cell on the source side of each D-040 frame_idx[0:1] column branch, grouped with its decoder. Keep all automatic repair and signoff checks. Inputs and supplies connect explicitly; bitstream format and user logic remain unchanged.
- **Data:** Tighter D-040 macro first DRT pass reaches87markers, but antenna check identifies frame_idx[0] at355.52/200 plus two buffered trunks at356.03/200 and387.24/200, and frame_address[31] at234.13–234.83/200.14 local branch buffers reduce route congestion but do not protect all long trunks. This experiment targets index trunks only, not the remaining column-address violation.
- **Who benefits:** configuration loading for every protocol; no dedicated protocol block or new user resource.
- **Cost:**14 diode cells,76.2048µm² before later repairs; diffusion loading, routing and potential timing/power cost still require measurement. No logical LUT capacity is removed.
- **Initial comparison:** same tighter macro/sharedCRC/local buffers/clock/hold margin: GRT stays0overflow; estimated wirelength276069→275796µm and hold buffers522→514. These preliminary changes do not establish physical success. Full stock route active separately in `compact_edges_tighter/chip_shared_crc_cfgdiodes/runs/compact_local_route`; baseline continues unchanged.
- **Acceptance:** full route, exact antenna count/ratios, DRC and timing checks plus real loaded mapped-shell behavior; no disabled-check diagnostic qualifies. Source-side diode locality can be changed by repair buffering, so inspect actual final connectivity rather than assuming protection from cell count.

## D-042: Screen clock routing above Metal2 in the scratch compact shell
- **Date:** 2026-10-05. **Status:** isolated physical experiment, not promoted.
- **Evidence/hypothesis:** completed tighter D-040 stock route has144 west-side markers,141 on Metal2; clock trunk `clknet_0_clk_regs` appears in27 markers and connects eight widely separated clock buffers. Test freeing Metal2 for local shell signals by setting only `RT_CLOCK_MIN_LAYER=Metal3`.
- **Scope/cost:** same1120.32×669.06µm macro, total area, logic/configuration, placements, clock target and hold margin; no new cells or protocol resource. Any loaded protocol uses clock distribution. Tradeoffs include higher-layer contention, vias and changed parasitics/timing. This is routing guidance, not a guarantee that every clock-access segment leaves Metal2.
- **Method:** copy original config and exact pre-GRT state from tighter `chip_shared_crc_cfgbranches`; modify only clock minimum. New directory `chip_clock_m3_screen`, bounded GRT run `clock_m3_grt`. Current diode full route untouched. Pinned LibreLane script supports the variable; primary reference: https://openroad.readthedocs.io/en/latest/main/src/grt/README.html (`set_routing_layers -clock`).
- **Initial result:** zero overflow remains; estimated total wirelength276069→276156µm, identical3497cell/805813.14µm² totals including the fabric macro. No DRT, antenna or timing improvement established. Do not launch a second full route based on this coarse result alone; first check actual guides and same-stage bounded DRT if warranted after the active run.
- **Acceptance:** stock detailed-route/antenna/DRC/timing plus loaded-image checks, at unchanged complete area/clock. No baseline or frozen G1 edits.
- **Bounded result:** `clock_m3_drt_screen` finishes two optimization iterations in13m08s:3784 native markers versus3482 for the matched baseline. The first iteration also worsens3837versus3441. Set aside; no full route justified by this screen. Antenna repair was disabled only in this diagnostic; flow completion is not physical success.

## D-043: Local padding around the measured CRC routing conflict (scratch)
- **Date:** 2026-10-05. **Status:** isolated placement/routing screen under D-037; not promoted.
- **Evidence/hypothesis:** the completed D-040 tighter route's largest exact net pair is `net37`/`u_shell.crc[2]`, with20of144 final markers. Their12 unique endpoint cells crowd the west CRC region. Test four placement sites of padding on each side of only these cells, rather than globally padding the shell.
- **Method:** start from the exact D-040 pre-GRT database/config; retain baseline Metal1–4 routing and clock guidance. Re-legalize with a20µm per-axis displacement bound and check legal placement, unchanged instance/master/connectivity and fixed macro location before writing a new scratch database. Pinned OpenROAD lacks the newer incremental-placement flag; record all collateral movement. Run GRT first, then only a bounded same-stage DRT comparison if overflow remains zero. Keep the active diode route untouched.
- **Cost/benefit scope:** no new logic, protocol block, configuration format or fabric resource. Every protocol pays any changed parasitics; padding reserves otherwise available placement space and can displace neighboring cells. Complete area/clock stay fixed before automatic repair; later repair costs and timing must be measured. No improvement is assumed from legal placement or cell count.
- **Implementation/reference:** `spikes/compact_edges/pad_crc_hotspot.tcl`; [OpenROAD detailed placement documentation](https://openroad.readthedocs.io/en/latest/main/src/dpl/README.html), checked against installed command help. Full stock DRC/antenna/timing and loaded-image gates remain mandatory for promotion.
- **Screen refinement/result:** four sites fails legalization; two sites fits but unrestricted legalization moves1539cells. Retained two-site probe anchors3055remote cells temporarily, restores their original status, and moves256local cells. GRT remains0overflow,277632µm versus276069baseline, same3497cells/805813.14µm²; no detailed-route improvement yet. Bounded diagnostic active in `chip_crc_padding_local_screen/runs/crc_padding_drt_screen`. Original failed and broad-motion probes retained, not routed.
- **Completed bounded result (October6):** two iterations finish3477markers versus3482baseline; first iteration4105versus3441 is worse. This marginal final difference does not justify a full route. Endpoints survive into actual DRT input, but no useful physical improvement is established. Do not promote.

## D-044: Test the pinned router's complete search/repair schedule
- **Date:** 2026-10-06. **Status:** scratch flow experiment under D-037; no hardware promotion.
- **Evidence:** all compact stock attempts use `DRT_OPT_ITERS=16`. Exact installed OpenROAD revision dcf36133 has a65-stage schedule, indexed0–64. Stage17 performs a broader ALL rip-up; stage23 includes NEARDRC neighbors; stages25/33/41 change clip sizes, with stronger repair costs later. Stopping at16 excludes these strategies. This is a confirmed flow limitation, not yet a proven cause of non-convergence.
- **Decision:** isolated warm-start run from completed144-marker D-040 database/state, with only iteration budget changed to64 in copied config. Keep existing guides, placements, logic, macro,20ns clock, hold margins and automatic antenna repair/checks. A new invocation restarts its internal schedule; it is not continuation at internal stage17. Do not claim the effect of late-stage strategies separately from warm starting without a matched control.
- **Cost:** no new fabric resource or protocol-specific block; longer compute time and possible rerouting/diode/parasitic changes. Complete starting area and clock match. Every design pays any resulting timing/loading effect; final checks remain mandatory.
- **Method/evidence location:** `build/route_root_audit_20261006/chip_schedule64`, stock flow through disconnected-pin checker first. Only advance toward extraction/timing/GDS/checks after zero native DRC/antenna/disconnected pins. No edits to frozen config, upstream or active inputs.
- **Primary source:** [exact pinned FlexDR strategy/main loop](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/dr/FlexDR.cpp#L1506). The early cap was intentionally inherited as a fail-fast control; its adequacy for the denser successor had not been tested.

## D-045: One larger NOR3 at the measured intra-cell pin hotspot
- **Date:** 2026-10-06. **Status:** scratch physical screen under D-037; not promoted.
- **Data:** read-only best144-marker geometry audit finds36 markers around A/B/C/Y pins of `u_shell._1073_`, `sg13cmos5l_nor3_1`. The local x0–50/y300–350µm bin is94.50% occupied by cells, with no filler cells in the snapshot. Pin proximity is evidence for a hypothesis, not causal proof.
- **Decision:** prepare a separate pre-GRT copy with only that gate changed to `sg13cmos5l_nor3_2`, locally re-legalizing within20µm displacement bounds while anchoring remote cells and restoring their status. Do not change the active D-044 run. Verify port contract, all net connections, exactly one master change, legal placement, functional behavior and timing before selecting. Keep20ns clock and existing hold margins.
- **Who benefits/cost:** generic management-shell implementation, all bitstreams; no protocol-specific block or architecture/configuration change. PDK sizes2.4×3.78→4.32×3.78µm add7.2576µm² before downstream repairs. The larger cell has wider/different input pin shapes, but adds load/area and may worsen local density, timing or routing. Non-users pay the same management-shell overhead. There is no established improvement or equal-total-area superiority.
- **Evidence/method:** installed PDK LEF pin geometry and Verilog NOR function match; `spikes/compact_edges/resize_pin_hotspot.tcl` refuses existing outputs and checks placement/connectivity. Evaluate a bounded GRT/DRT screen before committing compute to a full route; stock full checks remain required. `docs/reports/compact_route_root_causes.md` records the measured hypothesis and alternatives.
- **Completed placement/GRT/functional screen:**20µm and40µm anchoring halos fail local legalization (fanout149/fanout41). Minimal same-row rightward compaction passes `check_placement`, preserves every pin/net connection and every other master, and moves13neighbors by at most1.92µm. Actual GRT remains0overflow,275652µm wirelength/3497instances/805820µm² reported instance area (rounded). Saved GRT ODB exports the new NOR master; real842-word SPI/UART/STOP on that actual mapped shell with RTL fabric passes58.69s. Evidence `build/route_root_audit_20261006/chip_nor3_pin_screen` and `simulation_chip_nor3_functional_20261006_mapped_shell/results.xml`. No SDF/full mapped-fabric or detailed-route pass. D-044 iteration6 removes the original NOR cluster without sizing, so this is a verified backup screen; no second full DRT launched.

## D-046: Move expensive experiments to standard hosted CI
- **Date:** 2026-10-06. **Status:** implemented workflow; physical acceptance pending.
- **Reason/authorization:** user requests free cloud execution to avoid laptop heat and explicitly authorizes this session's grouped commits and push, overriding the standing no-agent-commit rule for this session only.
- **Decision:** separate standard Ubuntu24.04 hosted experiment jobs; no template-job edits, main changes, self-hosted runner or paid/larger runner. Publish preserved iteration8/15-marker inputs as a hashed experimental prerelease asset, not committed build output. Bound routing step300minutes and retain concise artifacts one day. Stock native failures block downstream signoff. Native mapped-fabric failures propagate independently.
- **Scope/cost:** no hardware/resource/spec change. Hosted LibreLane3.1.0.dev3 Docker/four threads differ from local3.0.0 Nix packaging, so this is not a pure iteration-budget experiment. Source OpenROAD/PDK pins remain matched. Public standard-runner compute is free under GitHub rules; storage is separately limited. Checkpoint reproduction does not close clean-source rebuild, native/SDF functionality or configured-fabric timing gates.
- **Evidence:** cloud Python/shell/YAML static checks and relocation of122 hash-verified files pass locally with no EDA computation. Workflow/results are recorded in WORKLOG; [acceptance/research plan](reports/compact_acceptance_and_competitors.md), spikes/cloud/README.md.


**D-047 matched-control update (October6):** five-mux regenerated native UART
passes37552796495/37553037381, but original-LUT resynthesis37553190074 also
passes. Do not attribute the correction solely to the new primitive. Both use
fresh copied inputs and identical synthesis flow apart from primitive choice;
old physical views remain unqualified. Prefer isolating synthesis differences
before changing architecture. Area/routing/configured timing costs stay open.


**D-048 correction (October7):**37552604692 failed248 KLayout/75 LVS after27m34s
job time. Actual DEF still has5667 decaps/1095 plain fillers because the
separate DECAP_CELLS selector was active (BUG41). This did not exercise decap
removal and cannot reject the hypothesis. Corrected one-field copied config
sets DECAP_CELLS=[] and preserves original FILL_CELLS. Require actual post-fill
inventory confirmation before DRC/LVS. Retain original clock, routing, logic,
macro, geometry checks and power tradeoff; no frozen config change.


**D-048 verified result:**37648945387 completes18m02s with actual0 decaps and
20714 plain fillers. KLayout248→0, LVS75→12. Magic reports6350, all pSD.e,
versus1828 before; no full physical pass or waiver. Same saved3-marker route
source and original frozen hardware. Retain decoupling/power tradeoff.

**D-049 verified diagnostic:**37651173629 reproduces all9 exact baseline slew
pins and the stronger same-wire driver has0 slew violations. Both retain33
fanout violations. Inputs/report artifacts downloaded and parsed. This is
slow-corner shell-only old-wire estimation, not a routed resized driver,
configured-fabric or all-corner timing pass. No master change promoted.

**Fresh-source follow-up:**37674839060 now supplies recovered-route physical
checks0 and new extracted wires, still with9 slow-corner slew violations.
Refresh the same in-memory driver comparison using authenticated extracted
ODB02b8bd30f3fb12e4a66e2322b5f3906c236dd93eed8b8cd1eeeff95f6e796a61
and hash-recorded SPEF/SDC. Bounded standard cloud job20min; no saved modified
DB, physical legalization or promotion. Retain exact nine-pin reproduction
gate and fanout reporting; the prior old-wire result alone cannot qualify a
resize on the newly recovered layout.

## D-050: Bounded repair and evidence recovery from the near-finished route
- **Date:**2026-10-07. **Status:** accepted isolated cloud experiment; no hardware promotion.
- **Reason:** final native0 database37516794406 was not retained (BUG40). No-decap replay37648945387 on saved iteration52 has0 KLayout but12 LVS differences, two fewer layout nets and four extra signal-pin incidences on VGND. Native source still has3 markers; remaining signal shorts are a hypothesis, not a proved cause of LVS12.
- **Decision:** warm-start the authenticated iteration52/3-marker ODB with16 iterations and15-minute routing-step limit, retaining stock antenna/disconnected checks. Only after native0 run no-decap geometry/LVS; retain final checked ODB/DEF/GDS/netlist/SPEF and exact metrics/hashes. Keep original driver; do not combine D-049 resize. One physical field change is DECAP_CELLS=[] already measured in D-048. Frozen source/config/macro/PDK stay unchanged.
- **Cost/limits:** bounded compute, possible diode/parasitic changes; decap/power cost remains open. No new resource or protocol-specific hardware. No full native-function/configured timing acceptance. Magic result is recorded separately; partial KLayout/LVS success cannot make all-three-geometry-zero true. A timeout/nonzero native result stops geometry and preserves completed evidence.

## D-082: Measure one existing buffer relocation on the combined placement

**Date:**2026-10-11. **Status:** isolated copied-checkpoint experiment; native
legality/electrical/routing pending, no frozen architecture change.

Actual38168159774 improves146→133 but still rejects congestion. Authenticated
marker/connectivity audit finds73/91markers sharing fanout-repair branches,
without causal attribution. Exact365native row fragments and3606instance boxes
identify a free site for existingfanout35 (buf_1,MY): bbox
[102720,457380,104640,461160]→[96000,472500,97920,476280]DBU.
The21.84µm displacement preserves site/orientation/power phase; source row
ROW_124_1 spans2880..111360 at472500, with a free96000..111360 tail.

Reproduce combined26-move control, then add this one buffer move. All other
instances/connectivity stay exact; no cells, protocol blocks or area are added.
It affects generic CRC/configuration shell routing, not a dedicated protocol.
Its output-net35 cell-center aggregate proxy worsens36.96µm while input-net40
improves87.36µm. This deliberate tradeoff requires measured electrical and native
routing results, not selecting by proxy alone. Six electrical/setup/hold guards
and native legality precede routing; compare to measured133 control at identical
clock/routing policy, retain original146control reproduction, reject regression.
No protocol fit/rate or equal-area superiority claim follows.

## D-083: Reject fanout35 regression; qualify a smaller same-row buffer move

**Date:**2026-10-12. **Status:** isolated copied placement, native guards pending.
Paired38178351037 reproduces146original but fanout35 yields143, worse than
combined133; rejectD082 as an improvement. Preserved133control starts this trial.
Existingfanout234 buf_1 R180 shifts left1.44µm on the same row:
bbox[57600,559440,59520,563220]→[56160,559440,58080,563220]DBU.
ActualROW147_1 spans2880..111360; independent all3606bbox overlap check clears
the target excluding the moved cell. Same orientation/power phase and all other
placements/connectivity must stay exact, with original26-move control replay.
Net234 shares six candidate markers; aggregate terminal-center proxy improves
2.88µm, not a wirelength or causal routing claim. No cells/area/protocol blocks
are added; no user protocol is tuned. Native legality/six electrical guards then
identical-policy routing must qualify this candidate. Reject if not better than
133; do not borrow physical or complete timing passes from other builds.

## D-084: Keep default counter width after a measured no-gain workload comparison

**Date:**2026-10-12. **Status:** software/user-bitstream comparison completed.
Cloud38273574240 compares COUNTER_BITS4vs3 for the same DIV16/delay4/window4
autonomous UART fault workload, same frozenG1 area/clock/compiler/pins. Both
use57/88LC and2/2timers+2/2shifts and pass realSPI-loaded full TX waveform,
fault/event and clean-frame recovery tests. No resource gain is measured;
retain existing four-bit default and broader configurable interval domain.
This does not modify chip architecture or qualify native physical timing.

## D-085: Compare routing net ordering without changing capacity or placement

**Date:**2026-10-12. **Status:** isolated native routing diagnostic, pending.
Buffer234 also worsens combined133→141 in38274085899; rejectD083 as a routing
improvement and retain exactcombined133source38167697696. Two displacedbuffer
experiments failed, so next test changes routing order instead of placement.

On identical authenticated original146 and combined133 checkpoints, compare
no-randomization control with seed41 using OpenROAD set_global_routing_random,
explicit capacities_perturbation_percentage0. This shuffles nets without the
optional edge-capacity perturbation. All track reductions/layers/50iterations,
margins, cells, netlists and placement remain fixed; no allow_congestion,
infinite capacity, negative adjustment, partial-net route or timing waiver.
The copied pinned Tcl is instrumented with patches/grt_net_order.tcl; originals
and headers remain untouched. Runtime records exact patch/copied-script hashes
and native command evidence. Source instrumentation fixtures authenticate both
pinned hashes; actual command support/execution and outcomes require cloud.

This changes one algorithm policy, adds no hardware/area/protocol block, and
benefits no protocol until matched physical/function/timing qualification. A
zero-overflow result would still require detailed routing and full sign-off.
Primary source: [OpenROAD global routing](https://openroad.readthedocs.io/en/latest/main/src/grt/README.html).

## D-086: Test horizontal mirroring with unchanged placement bboxes

**Date:**2026-10-12. **Status:** copied-checkpoint native producer pending.
ActualD085 seed41 worsens combined133→143; seed0 reproduces133. Resource
totals match acrossseeds for eachphysicalplacement. Rejectseed41 as a gain.
Next test uses pinned optimize_mirroring to change cell pin access without
shifting bboxes, adding cells, altering masters/netlists or changing clock/routing
capacity. Reproduce exactcombined26move control and authenticate its census,
geometry/result; then allow only horizontal mirrors of movable CORE cells.
All3606bboxes, masters, connections and statuses stayexact; vertical orientation
phase must match. Macro/fixed changes or unsupported transforms reject.
Native legality and all six electrical/preliminary setup/hold guards precede
routing; no geometric/HPWL gain implies congestion improvement.

This is one placement policy, no architecture/resource/area/protocol change.
Every loaded design pays any wiring/timing tradeoff; no successor promotion or
protocol rate claim follows. Tool primary documentation describes a wirelength
heuristic, not a congestion guarantee:
[OpenROAD detailed placement](https://openroad.readthedocs.io/en/latest/main/src/dpl/README.html).

## D-087: Calibrate a native grid observer before alternate-engine routing

**Date:**2026-10-12. **Status:** read-only copied-script cloud preflight pending.
Mirroring38281724422 worsens combined133→151; rejectD086. AlternativeCUGR is
supported by pinnedOpenROAD, but skips FastRoute's standard final report.
Add read-only getGCellGrid/getGridX/Y/getCapacity/getUsage collection to unchanged
FastRoute control runs first. Catch/rethrow the exact native global_route error
after observation; no congestion bypass, placement/capacity/clock change or
missing-report-as-zero acceptance. Keep native table/TR reports separately from
grid fields; calibrate dimensions/semantics before alternative-engine judgments.
This adds no cells/area/protocol features and stays in copied runtime scripts
with patch/license/hash attribution; no frozen hardware or template-job edits.
Pinned API: [OpenDB](https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/odb/include/odb/db.h).

## D-088: Evaluate pinned CUGR with calibrated grid and complete-guide gates

**Date:**2026-10-12. **Status:** isolated alternate-engine cloud experiment pending.
Read-only preflight38282629603 reproduces146/133 native failures; independent
grid parser reproduces eachMetal1–4 overflow exactly. Ten fixtures reject
missing/duplicate/nonfinite/negative/out-of-range cells and guide census gaps.
Now select pinned -use_cugr on the same authenticated original/combined physical
placements, netlists, libraries, clock/margins and capacity-adjustment policy.
No net randomization, capacity perturbation, congestion bypass or cell edits.
The engine's internal algorithm differs;50 remains the command argument, not
a claim of equal algorithm steps or equal runtime.

CUGR does not emit FastRoute's final table. Report native OpenDB grid fields
explicitly as grid observations, preserve native failure status, require exact
fullgrid dimensions/Metal1–4coverage and zero observed overflow. If nativeflow
succeeds, also require nonempty usage/guides, complete required-net guide census,
immutable placement/topology and finite wirelength. Partial guides/missing data
reject; no invented FastRoute table. Detailed routing, DRC/antenna/LVS/official
precheck, native loaded behavior and complete timing remain mandatory afterward.
This adds no hardware/area/protocol-specific block; guides/timing tradeoffs apply
to all loaded programs and do not establish a protocol/rate advantage.
Copied Tcl/patches retain source hashes, licenses and policy attribution.
Pinned engine: [OpenROAD](https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp).

## D-089: Query hold-delay paths before proposing repair changes

**Date:** 2026-10-12. **Status:** read-only cloud observation prepared; no hardware change.
Producer38167697696 contains590 delay cells and150 direct FF feedback paths.
The default fast-corner endpoint report includes238 distinct delay cells and
only8 of those feedback paths; endpoint-worst reports do not cover every repair.
Use LibreLane's existing `STA_EXTRA_CORNER_TCL_FILE` hook to query worst
constrained min/max paths through each actual delay input at each original PVT
corner. Keep authenticated ODB/netlist/SDC/config, placement parasitics, original
clock uncertainty/transition/derates and electrical/timing guards unchanged.
Absent paths remain explicitly absent, never zero slack or removable repairs.
No hard blocks, area/resource changes, held-out tuning or clock gating is
implemented. Every loaded protocol retains the same silicon and constraints.

The upstream [corner script](https://github.com/librelane/librelane/blob/3.1.0.dev3/librelane/scripts/openroad/sta/corner.tcl) supports the extra Tcl hook.
[OpenROAD repair timing](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html) inserts hold repairs after CTS; its buffer budget is a limit, not evidence that reducing repairs preserves timing.
Observation is not full extracted or configured-fabric timing acceptance.

## D-090: Rebalance only delay cells with measured hold headroom

**Date:**2026-10-12. **Status:** producer38316322592 passed native placement and3-corner shell guards; routing38316844576 worsens133→145, reject for routing.
D089 run38315257114 completes all590 per-delay min/max queries at each of3
original PVT corners and retains all electrical/setup/hold guards. The150
direct feedback paths all belong to configuration registers and have fast
hold slack0.176544–0.217264ns. Keep those repairs untouched. Exactly251 other
delay cells have measured worst constrained fast hold slack >=0.3ns.

On a scratch copy of producer38167697696, replace only that measured251-cell
set from dlygate4sd3_1 to smaller dlygate4sd2_1. Both pinned Liberty cells have
X=A behavior, but their delays/footprints differ; no deletion, bypass or false
path. Actual OpenDB must preserve all pins/nets/instance origins/orientations,
all unselected boxes and the fixed macro; changed boxes must shrink inside
original bounds. Native placement legality plus3 original-corner electrical
and setup/hold checks must pass, with >=0.1ns worst hold slack retained.
No constraints, derates, capacity, protocol blocks or frozen sources change.

This is a generic physical-cell policy: every loaded protocol uses the same
shell. Potential cost is less hold headroom; actual area cost/saving and routing
effect remain pending native producer/GRT evidence. Fewer/smaller cells alone
do not establish congestion improvement. Only a passing producer can proceed
to paired routing against the best133 control; full physical/native timing
gates remain mandatory and architecture superiority is not claimed.

## D-091: Congestion-driven redistribution after smaller-cell routing regression

**Date:**2026-10-12. **Status:** isolated placement producer prepared.
D090 reduces standard-cell footprint but paired38316844576 worsens native
overflow133→145; reject that placement/master policy for routing. Preserve
original best133 control38167697696 and all its masters, including hold repairs.
Use native global_placement with skip_initial_place, routability_driven and
density0.55, then detailed_placement. No timing-driven resizing, clock-cell
insertion, I/O relocation, capacity change, margin relaxation or hardware edit.

Native checks must prove identical instances/masters/nets/statuses/dimensions,
fixed macro and identical physical boundary pins/die/rows. After legalization,
verify every CORE cell's vertical power phase against its actual fragmented
ROW record, rather than restoring an old orientation after an odd-row move.
Source38167697696/row inventory38166250744 covers3605CORE cells with this checker.
Then original3-corner setup/hold/electrical checks and>=0.1ns worst hold guard
must pass before routing. Total physical outline/resources and20ns clock stay
equal; altered placement can change wire delay/skew for every loaded protocol.
No area/rate/congestion benefit is claimed before native measurements.

[OpenROAD global placement](https://openroad.readthedocs.io/en/latest/main/src/gpl/README.html) describes RUDY-based congestion estimation and cell inflation in its placement objective; the estimate is not a zero-overflow guarantee. Native command/help and all failures are retained in cloud artifacts.

## D-092: Move congestion intervention before clock-tree construction

**Date:**2026-10-12. **Status:** isolated pre-CTS comparison prepared.
CorrectedD09138318370803 passes native placement, immutable physical boundary
pins/die/rows/masters/connections/macro and3605CORE row power-phase checks.
It moves3599instances, but fast hold slack0.05714ns loses the retained0.1ns
guard. Reject before routing; do not weaken the guard or reuse that layout.

Use the authenticated original pre-CTS archive. Compare original placement
versus GlobalPlacement/DetailedPlacement before CTS, then rebuild CTS and
ResizerTimingPostCTS in both cases with cluster8. New placement uses density55,
routability-driven, skip-initial placement and no timing-driven resizing.
All original libraries/macros/clock/uncertainty/transition/derates/SDC/fanout
constraints remain exact. No frozen source, instruction/resource or protocol
block changes. Native exporter preflight runs on the unchanged source first.
Fixed macro/boundary pins/die/rows and actual post-repair power phase must pass;
explicit single-corner STA records every electrical/setup/hold count at all3
original PVT corners. Nonzero electrical counts or hold below0.1ns are rejects,
even if the evidence-collection job is green. No chip or configured timing
acceptance follows. Cost is a new clock tree/repair allocation and changed wire
delay for all programs; actual area/congestion effect is pending measurement.

[OpenROAD repair timing](https://openroad.readthedocs.io/en/latest/main/src/rsz/README.html) places timing repair after CTS with propagated clocks.
[LibreLane global placement](https://librelane.readthedocs.io/en/latest/reference/step_config_vars.html) supplies the placement variables and standard stages used by this scratch flow.

## D-093: Restore known fanout distribution after the pre-CTS experiment

**Date:**2026-10-12. **Status:**38320631258 producer passes all declared native/electrical/timing guards; routing comparison pending.
ActualD09238319615838 completes both cases. Control reproduces original pre-buffer
ODB0a0af0c1…/netlist5bcc7ceb… byte-for-byte. Reflow rebuilds clock/repairs and
retains fast hold0.100232ns plus positive setup/hold and zero slew/cap at all3
corners. Both retain the known5 configuration-distribution fanout violations.
Reflow has3645instances versus3596control; count alone is not an advantage.

Apply the established10 buf_2 identity-buffer repair (two6-load groups on each
of5 measured column nets) to the authenticated reflow views. Generalize only
original-count protection to3645; FIRM-lock all existing PLACED instances during
legalization and restore their exact statuses. Contract buffer branches to prove
every original connection unchanged; require identical master/origin/orientation
for all originals and fixed physical macro/pins/die/rows. Native legality and
actual ROW power phase precede all3 original-corner timing/electrical checks,
including>=0.1ns hold. No constraints, source/spec, capacity or user protocol
changes. The buffers cost actual native footprint/wires for every program;
benefit is removal of the known distribution electrical violations, not a
claimed routing improvement. Only a passing producer proceeds to GRT versus133.

## D-094: Replace misleading placement congestion proxy with native routing feedback

**Date:**2026-10-12. **Status:** isolated estimator comparison prepared.
Actual38321208948 retainscontrol133overflow but fanout-clean reflow reaches6544;
rejectD092/D093 reflow for routing despite its producer gates. Native geometry
shows north-corridorCORE cells increase76→443 (control38167697696 versus
producer38320631258), west3231→2892, east remains7. Membership/distribution
suggests corridor pressure, but is not proof of each violation's cause.

Keep the same pre-CTS reflow density55, source, CTS8 and repair/clock policy;
change only placement estimation from RUDY to native FastRoute via
-routability_use_grt. Copy pinned GPL Tcl at runtime, retaining license headers
and exact sourceSHA b293515d…; upstream source stays untouched. Require actual
native command execution and exact Metal1–4/adjustment0.3/layer-adjustments/
macro-extension policy. The unchanged final GRT zero-overflow gate still applies;
temporary placement estimation is not a final congestion waiver. All physical
interface/power phase and3-corner electrical/timing rejection gates remain.
No source/spec/resource or protocol changes; every program pays any altered
wiring/repair tradeoff. Actual area and routing benefit remain unmeasured.

[OpenROAD global placement](https://openroad.readthedocs.io/en/latest/main/src/gpl/README.html) documents native GRT as a more precise, higher-runtime alternative to its default RUDY estimate. Native-runtime failure or missing source/flag evidence rejects this experiment; no physical advantage is assumed.

**D-094 outcome, October13:**38453870785 native route rejects candidate6000overflow versus133control. Three-corner repaired producer success38452773248 did not predict routing closure. Reject broad native-feedback re-placement, preserve best133control, and inspect localized routing topology before further placement experiments. Historical RUDY workflow replays are manual-only; no architecture or routing-capacity waiver.

## D-095: Evidence-driven autonomous development with an active agent team

**Date:** 2026-10-15. **Status:** user-authorized session setup; hosted validation pending.

Use the coordinator plus explicitly assigned specialists for independent research,
implementation and adversarial evidence review. Persist actionable tasks and rejected
hypotheses in `docs/autonomy/backlog.json`; follow
`docs/design/AUTONOMOUS_DEVELOPMENT.md`. GitHub remains the substantial test/EDA
executor. Preserve frozen G1 and authenticated best133; no hardware, capacity,
clock, spec or acceptance change follows from this infrastructure.

Add a bounded allowlisted test supervisor with atomic state, a single-writer lock,
source/revision and attempt checks, actual XML/image/parameter verification,
downloaded evidence fingerprints, finite launch/concurrency limits and a STOP
file. It supervises tests; the live session supplies engineering judgment. No
model credentials or unattended AI worker are provisioned. User Git approval is
for this session; it does not grant future sessions or scheduled code writes.

Default branch remains TRIPWIRE `main`. GitHub schedules run on the default
branch, so do not advertise an `efpga`-only cron as active. Use branch-filtered
push/manual observation and an explicitly launched bounded supervisor instead.
Sources: [GitHub workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
[OpenAI non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

**D095 session follow-up:** the actual hosted strict-XML failure exposed BUG89
(an inapplicable UART test), fixed by conditional discovery rather than weaker
acceptance. Actual four-check campaign on77edd2d is independently verified.
Read-only route/grid research now supports one bounded observation: enable
existing pinned `GRT/grtSteps` scalar reporting on the unchanged133 control.
Require identical full native segment and selected-target hashes in addition
to original marker/policy/source checks. Scalar stages may locate where
congestion arises; they do not provide selected-net topology or physical
acceptance. No random-seed, placement, resource, margin or hardware change.

## D-096: Refresh attributable evidence before another routing-budget experiment

**Date:** 2026-10-15. **Status:** prepared for hosted measurement.

Actual38778082059 contains243 negotiation starts across five automatic
NDR-reset epochs even though the unchanged command budget is50. Final epoch
reaches50; the pinned checkpoint-saving branches are not reached. Enable
only existing `GRT/congestionIterations` logging to measure the trajectory,
retaining exact source, capacities, margins,133 control and final-route hashes.
Do not infer that a larger budget will help from the command limit alone.
Only an improving final trajectory can justify a separate bounded native
budget comparison; no geometry, architecture or acceptance change is made.

Separately refresh the original design-set synthesis profile on pinned hosted
tools, preserving all24 trials, parameters, attribution roles and listed-input
hashes. This closes a local-only evidence gap, not an architecture advantage
or a reconstructed historical run. Preserve held-out boundaries and label
current results separately from historical profile values. Retain emitted
example images in clean-reproduction artifacts for independent byte checks.

## D-097: Test one native early-stop budget after observing oscillation

**Date:** 2026-10-15. **Status:** paired diagnostic prepared.

Actual trajectory38780941495 retains exact133 control/source/segments. Final
epoch oscillates: its last ten overflows are138,139,145,135,153,145,149,134,155,133;
the transient minimum is110 at start14. Reject an unsupported larger-budget
run. Instead test native budget15 versus original50 on identical authenticated
views, one bounded pair, with unchanged layer resources/capacities, libraries,
clock margins, physical interface and original three-corner producer guards.
This is a hypothesis that earlier stopping can retain a lower-congestion
solution, not an assertion that budget15 reproduces the observed round14:
native NDR resets and their histories will also occur at different times.

Replay50 must match original133, marker and full/target segment hashes in the
same job. Candidate15 changes exactly GRT_OVERFLOW_ITERS, retains native error
and actual diagnostics, and is rejected if overflow does not improve133.
Nonzero improvement is still experimental; only native zero overflow with
successful return justifies downstream detailed-route/extraction/complete
timing/function qualification. No source, silicon, placement, resource or
protocol architecture change. Existing standalone trajectory workflow is now
manual-only to avoid a duplicate control replay on shared-helper edits.

**D097 outcome:** paired38820879445 atf8ed2a0 authenticates original133,
then candidate15 reaches121. Same104726 routing resources, same source views,
native return1 in both cases. Per-layer overflow13/53/31/36 becomes19/40/18/44;
retain a lower-total routing point, not a uniform layer or full-chip win.
Full candidate segment SHA19b14132c36cfa3e863edc34d0f23e7783694da80f586c438833783337a1da2c.
Next observation exports the calibrated native grid at this exact15/121 point;
require the same segment hash/121 and native per-layer grid/table agreement.
Original133 remains the reference for original50 policy. No further budget
sweep or physical acceptance follows from this retained measurement.

## D-098: Isolate southern connections before choosing a routing correction
- **Date:**2026-10-15. **Status:** accepted bounded diagnostic, no hardware promotion.
- Exact121 grid38824245540 shows both southern target allocations share Metal3 grid edge(16,1), with nine other net owners; freeing both opens an optimistic perimeter path while each alone does not. This implicates joint congestion but does not exclude terminal-access defects.
- Reproduce exact15/121 full control, then independently route cell_pad[31], cell_val[30], and the pair from identical authenticated physical inputs. Use pinned supported set_nets_to_route, preserving all cells/obstructions/margins. Unselected nets intentionally lack guides: reduced successes are never full-chip acceptance.
- Export calibrated native capacity arrays in every case. Net selection may change pin-dependent capacity adjustments; record differences explicitly rather than interpreting them as controlled improvements. Original full-control resource/hash guards remain mandatory. Only these two fixed diagnostic nets may bypass the full-resource equality rejection; their actual arrays/tables remain retained.
- Keep native congestion errors, actual routed-net census and full-source provenance. No congestion allowance, removed obstruction, hardware change, new binary, or capacity increase. Runtime Tcl copies retain existing upstream attribution. Upstream supported interface is pinned in docs/reports/routing_policy_research_20261014.md.
- If isolated nets fail: inspect pin access/grid and construct a minimal upstream reproducer. If isolated routes pass on identical capacities: pursue joint congestion reoptimization, not another unmeasured placement/seed sweep. Existing incremental engine may support an explicitly forced selected-net patch, but stock unchanged-pin callbacks are insufficient; custom tool work needs its own decision and baseline identity check.

## D-099: Prepare explicit bounded unchanged-net repair as a review artifact
- **Date:**2026-10-15. **Status:** accepted hosted build/interface qualification only; chip experiment unqualified.
- **Reason:** stock incremental dirty-net filtering skips unchanged pins, although its congestion-expansion path jointly releases competing routes and merges replacements. Exact121 evidence motivates a two-net seed only if D098 excludes isolated pin-access failure.
- **Artifact:** patches/openroad_force_reroute.patch against OpenROAD dcf36133a369abc8f3c5e5738cd4d82e4903c0e0; upstream files/licenses stay intact. Expose a narrow exact-dbNet pair interface, bypass the pin-change condition only for explicitly selected mapped nonclock/nonmerged signal nets, bound expansion to four and prevent native detailed-placement fallback. Clean callbacks on exceptions; discard failed process state.
- **Gates:** patch applicability is checked only. Compilation/SWIG/minimal regression/default exact121 equivalence and geometry/capacity/full-net-coverage audits must precede a chip experiment. No tool patch is active and no benefit is claimed. See docs/reports/force_reroute_design_20261015.md for source hashes and unresolved checks.
- **Alternatives rejected:** fake pin movement, unchanged dirty callbacks, blindly extending an oscillating budget, and treating subset routing as a full-chip result. No architecture, timing constraint or capacity change.

## D-100: Correct repeated pin-access crediting before judging forced repair
- **Date:**2026-10-15. **Status:** accepted one controlled software correction/retry, no chip promotion.
- Actual38849978485 confirms default custom tool exactly reproduces121 but forced repair ends139 with203 increased capacity entries; geometry/connectivity unchanged. The capacity guard rejects this confound.
- initNetlist re-adds macro/pad credits every incremental initialization; unchanged forced pins retain their original credits, while clearNetRoute/releaseNetResources affect usage only. Guard addResourcesForPinAccess with !force_reroute_mode_ in our attributed patch. Ordinary upstream/default flow unchanged. Two independent reviews and exact-source dry-run agree; compiled/native proof pending.
- Repeat pinned build, real GCD regression, default exact121 and one same-process pair trial. Keep all capacity/geometry/census/final-grid gates. Preserve prior failed result and old binary provenance. No resource/capacity waiver, source hardware change or margin relaxation. PatchSHA73e5588175fadd8d08793f19c09d4aa2b50c744d0c2b5229c9e503c592fc8aef.
- Defer 3D-gate bypass: its hard-capacity single-edge search cannot negotiate simultaneous displacement through a full cut and needs unreachable-path recovery. Fix the demonstrated accounting defect first.
- October16 evidence: corrected build38851788423SUCCESS55m09s, native GCD passes38853662972 and exact default121 is retained. New boundary parser setup failureBUG101 prevents pair execution; corrected38948702750 reuses the built tool. Upstream independently fixed the same crediting mechanism in09f16990f662d522b51094a6c3085c25f3ade024 (PR9510), after our pinned revision; see upstream_pin_access_research_20261016.md. This supports the diagnosis, not routing closure or an unreviewed upgrade.
- Actual38948702750: accounting guard passes all69064interior+550boundarycapacities; nativeGRT0232/observedgrid132 regresses exact121, with no final postrepair table and incomplete selected guides. Reject this bounded strategy, retain the corrected tool and best121. Observation-only expansion/pass snapshots require identical final132 hashes before interpretation.

## D-101: Observe bounded repair passes before changing the routing strategy
- **Date:**2026-10-16. **Status:** accepted observation-only software experiment, no physical promotion.
- Controlled38948702750 preserves exact initial15/121, geometry/connectivity and all69614 observed real preferred-edge capacities, but the bounded southern pair plus four expansions ends nativeGRT0232/observedgrid132. Intermediate native counters cover touched sets, not whole-chip overflow. Actual expanded membership and earlier whole-grid states are unobserved.
- Add attributed force-mode-only instrumentation after each existing merge: sorted actual net membership/new names, canonical interior and real preferred boundary capacity/usage, and complete merged segments. Explicit output-directory opt-in; no net-selection, iteration, cost, capacity, placement, timing or default-flow change. Preserve pinned upstream/license and all original guards.
- Require compiled native regression and exact initial121; final native exports must reproduce controlled132 segment/interior/boundary hashes before interpreting snapshots. Last snapshot must match final exports semantically; every snapshot needs complete3659net inventory, exact grid/edge census and unchanged observed capacities. Capture per-pass hashes and membership provenance; retain raw evidence only as CI artifacts.
- If final identity differs or any source/capacity/geometry/census gate fails, reject observer equivalence. Do not present a transient scalar as an available checkpoint, or partial guides as success. This observation can distinguish omitted congestion ownership from later pass regression; it does not itself improve routing. Preserve best121 and original50/133 separately.

## D-102: Restore positive-usage membership in one force-only controlled trial
- **Date:**2026-10-18. **Status:** accepted bounded software experiment, no physical promotion.
- D101 actual38950416231 exactly reproduces rejected132; full-grid passes125/123/139/140/132 never improve121. See force_observer_result_20261018.md. Pinned incremental clearUsed drops retained positive-usage membership used by congestion discovery; upstream50d692bea57e0840f2bd738223ea8700fbcb5362 rebuilds it (upstream_incremental_scope_20261016.md).
- Apply separately attributed patches/openroad_force_used_grid.patch after D101. Explicit force-only environment value1 enables the helper; unset preserves legacy behavior, other values reject before mutation. Restore flag on existing cleanup. Scan only valid positive-usage H/V edges, including real boundaries. No direct usage/capacity, placement, cost, history, ordering or budget edits; native downstream history updates may differ because membership is corrected.
- Qualify pinned build/GCD first, then same-binary exact121 default and exact132 legacy observer before candidate. Candidate must retain all geometry/census/capacity/guide/native-final-table guards and emit native activation witnesses. Collector success never means physical acceptance. Reject regressions against121; preserve original50/133 and legacy132 separately. No frozen hardware/spec/clock change or broad tool upgrade.
- Local evidence: both patches apply sequentially to exact pinned source files; source helper bounds and existing logger API inspected. Native build and actual candidate results pending. PatchSHA629659917f0d5e052953e3407d7264772421e52030822d940b103db5a4e03dbd.

**D102 actual outcome, October19:** build39143345968SUCCESS32m57s; collector39143364213 succeeds with exact121/default and exact132/legacy controls. Explicit used-grid candidate ends nativeGRT0232/observed139(15/66/26/32), preserving geometry/census/capacities. Five-pass full-grid121/145/142/133/139; all439 initial overflow owners enter the first expansion. Thus discovery correction is measured but insufficient; reject routing policy versus121, no retry without new evidence. See used_grid_result_20261019.md. Distinguish this valid139 from the older capacity-confounded139. No physical promotion.

## D-103: Change the diagnostic method before another routing-policy replay
- **Date:**2026-10-19. **Status:** accepted bounded software/observation work; no native routing or physical promotion.
- D102 restores all439 initial overflow owners yet full-grid139 regresses121. This rejects missing initial ownership as a sufficient explanation and does not justify blind seeds/budgets or repeating the same repair. Retain the clock-preserving policy as a source-supported proposal, not a bundled next trial.
- Add an isolated explicit-graph CP-SAT feasibility oracle with pinned optionalortools9.14.6206, one-worker/time/model-size limits, per-net union occupancy and declared layer/via demand. Independently check constructive witnesses; report UNKNOWN as inconclusive and INFEASIBLE only for the supplied graph. All outputs keep native_inputs_authenticated=false and physical_acceptance=false.
- Actual hosted qualification39290648912 atde26ea4 passes117 executed tests with no skips, independently rechecked XML and version/fullSHA. Includes independent exhaustive tinygraph comparisons; this does not route WARP.
- Before native application, export/reconcile raw H/V resources, exact pin-grid/boundary conditions, live soft-NDR/clock/per-layer costs and weighted native contributions. Existing encoded reporting grids are insufficient. Separate observation-only patch requires review/build/exact121/132/139 controls and raw-usage reconciliation; no invented unit weights.
- DGR/CUGR2 is a separately scoped alternative requiring capacity-compatible export; AlphaChip targets placement and AutoTuner is not a reason to reopen rejected knobs. Research in routing_escape_options_20261019.md. Different reasoning agents/models can challenge assumptions, but only checkable artifacts change acceptance.

- **D103 observation artifact:** patches/openroad_corridor_observer.patch against exactdcf36133 afterD101+D102, source-reviewedSHAb7493c2fc4e4c7074363550fd0a059064ee739a4fc593f3eaf14081167a5ff65. ExplicitAPI/read-only native rawcost/resource/STEP export, guarded idle state and exclusive output; no default call or algorithm change. ODB companion patches/corridor_contract_observer.tcl and schema in native_corridor_contract_20261019.md. Build39304728263 at75d4378 succeeds, including linked API smoke. Exact121/132/139 controls and ledger reconciliation remain pending in39331153087 at675b659; compiled observation is not native model qualification.

- **D103 terminal follow-up:** raw observer qualification39331845906 reconciles
  all6 snapshots exactly and preserves native checkpoint identity. Native pins
  still lack physical membership/alias/access joins. Add separate explicit
  terminal observer patchSHA5ec2f809d784e5d81e59a1470bef566423f7a35cb1aea573564b35734396393b,
  after existing3patches, with independent source review and exact no-fuzz
  dry-application. Export database/GlobalRouter/native inventories, physical
  membership, layers, existing node aliases and via-range sentinels; no route,
  cost, geometry or configuration change. Local/degenerate unsupported access
  stays explicit. Build and native join qualification remain pending; retain
  exact121/132/139 controls and all raw ledger/capacity/identity gates before
  interpretation. This is software observation, not a hardware contract change.

## D-104: Qualify clean source and full configuration cost before R1 topology selection
- **Date:**2026-10-20. **Status:** accepted bounded software exploration under D-037/user-approved R1 plan; no production hardware selection.
- Paired39471254787 shows UART+SPI demands103cells with3timer/shift pairs, versus138cells using2pairs; UART+I2C123versus173. An extra reusable pair benefits both workload families. No new primitive behavior or hard protocol block is introduced. Actual added physical area remains unmeasured, including routing/pins/configuration and cost to nonusers.
- Count the complete fabric: G1 has7860stored bits, including6032switch bits, rather than treating interior6656as the whole macro. Source counts are not physical area. Do not rank pruning by removed PIP count alone.
- Start with an exact regenerated G1 graph/configuration control from a clean pinned Git archive; cached tile sources are not authoritative. Reject mismatched graph multiplicities or bit mappings before any candidate model compile.
- Use an isolated oversized128-LUT/four-pair model only to establish compiler capacity/representation for the concurrent workloads. Its11408stored bits and unchanged tile geometry do not demonstrate equal-area viability; physical_candidate=false and timing_acceptance=false. It is not a selected R1 architecture and must not enter production inputs.
- Gate: source/control identity, strict checker XML, real native compiler/image diagnostics, then a physically plausible costed topology. Configuration loads must ultimately work through the real interface on mapped fabric before promotion. No weaker margins/capacity credits, no changed G1 ABI/RTL and no held-out-pool tuning. New owned r1_models workflow executes bounded qualification; template jobs unchanged.


- **D104 four-track software screen (2026-10-21):** owned spikes/r1/fold_tracks.py transforms only copied pinned library files. Directional global wire widths8→4; eight local jump tracks, existing primitives, clocks, carry and external pins retained. Canonical merged switch outputs become explicit mux choices. Regenerate tile/config/switch RTL and configuration maps; do not edit generated production sources or upstream in place. Local generated full-grid census10976bits confirms the graph projection; LUT configuration remains566bits. No physical area/timing/routing claim. Use the same diagnostic capacity-control ABI in isolated model directories only; never load on G1. Matched four/eight-track hosted campaigns must retain all six original personalities plus both concurrent workloads. This is the second topology including the oversized eight-track control; no third variant selected. Reject lost retained capability; require physical cost evidence before promotion.


- **D104 technology-mapping screen (2026-10-21):** regenerate both controls through the same tile/config/switch generator before comparing. Explicit optional emit-rtl stages a separate copied library even for the eight-track control; qualified source library stays unmodified. Use pinned CMOS5L Liberty/latch map, identical Yosys synthesis recipe, reject residual generic/unmapped cells or any mismatch with each tile's full configuration-latch census. Map all ten tile types and weight by actual grid copies. Report idealized cell cost only: no shell, physical buffers, clock/power/padding or signal routing is included. Preserve same20ns eventual physical target; synthesis-area screen is not timing or equal-total-area acceptance. Pinned source and all input hashes, native netlists/statistics and checker XML retained by the owned workflow. No physical hardening attempt or new production architecture.


- **D104 mapping outcome:** authenticated39689008902 shows four-track whole-grid idealized cell sum only1.83%smaller, LUT tile2.24%larger despite306→210port bits. Independent pinned-Liberty/netlist audit verifies full live configuration and cell-area accounting. Reject packing this unchanged mapped6x3grid into G1's unchanged outline/border layout: interior slot smaller than mapped cell area before physical overhead. Retain as compiler/control evidence, not physical successor. No new hardening attempt. Reserve remaining initial topology for materially lower interior mux/configuration cost; preserve all8training workloads, primitives/clock/reset/carry and held-out exclusions. Physical/functional gates are not waived.


## D-105: Third bounded R1 screen reduces interior switch radix
- **Date:**2026-10-21. **Status:** accepted experimental software screen under D037/D104 and the approved three-profile plan; no production architecture change or physical acceptance.
- Evidence:39689008902 preserves eight workload fits after global tracks8→4, but idealized whole-grid cell cost improves only1.83% and LUT tile grows2.24%. A LUT tile still spends414bits on selection and1132padded mux inputs. Interior switch cost is the next measured target.
- Third/final initial profile radix8_2 keeps four global tracks and eight local jump wires. In LUT/primitive tiles only, each cardinal local-escape mux uses at most eight choices (four cell outputs, four routing sources). Deterministic bipartite matching retains every original cell output in each cardinal bank with four local slots per escape destination. This coverage is not a full routing guarantee.
- Shared input gather muxes select at most two sources, retaining a local feedback input where present; paired LUT input selectors use complementary two-source halves so all shared gather outputs remain connected. Primitive input selectors, clock/reset/enable/carry selectors and border switches are unchanged from the four-track control. No protocol identity, placement or seed is used to construct the graph.
- Regenerate source copies, config maps, tile/switch/config RTL and compiler/bitstream models. Validate protected selectors/coverage, exact generated switch census and full live mapped latch census. First draft loses10latches because shared paths become dead; BUG115 rejects it. Corrected local438LUT/334primitive stored bits, whole grid8736; all ten local mappings preserve their full census. Physical cost remains pending hosted evidence.
- Compare all three fixed profiles, map all tile types and compile all eight workloads. Preserve every failure/unknown outcome; no early stop after one workload, no next profile or seed search disguised as a fix. Reject lost required capability; physical geometry, configured functionality, seed robustness and full-chip checks remain gates. G1, held-out exclusions and native121/118evidence stay unchanged.


## D-106: Exact mapped LUT floorplan/pin preflight before representative routing
- **Date:**2026-10-23. **Status:** accepted bounded observation under D037/D105; no production hardware selection.
- Freeze LUT netlist JSONSHA65ad88d47ac9186eb9210280d8d0ae8e3a80916a89f8b669ccf01683075c6c75 from audited39696703659/source9768c77. Export existing mapped cells without resynthesis.438live configuration latches and210signal bits must survive native import, with every cell type/count unchanged.
- Compare two fixed widths219.84(reference) and154.08µm at185.22µm height; retain same site/row margins and I/O-layer policy. Footprint is the only comparison variable. The narrowed width is a preflight hypothesis, not a selected chip layout or routing claim.
- Generate pin order from a disposable library copy; adapt FABulous2.2single-tile YAML to the pinned physical I/O parser format. Normalize only one-bit-vector Verilog print metadata to preserve scalar carry pin spelling; assert cells/ports/connectivity unchanged. Reject altered source model or missing/overlapping/out-of-die signal rectangles, changed native cell inventory, or cell area exceeding actual core area.
- Use pinned LibreLane image and CMOS5L PDK, Floorplan/SetPowerConnections/IOplacement only. CLOCK_PORT=null means this establishes no configured timing; no placement, PDN, detailed routing, signoff or full-chip acceptance is implied. Preserve20ns eventual target. Representative routing and per-column PG alignment remain open after this observation gate.
- New owned r1_physical_preflight workflow retains complete inputs/native artifacts. Template jobs untouched; R1 model workflow paths are narrowed so subsequent physical-preflight edits do not repeat the unchanged compiler campaign. No physical hardening/full-chip attempt consumed by floorplan/pin preflight.


- **D106 compatibility follow-up:**39987539298 resolves port names but legacy equal per-bus segmentation leaves31slots for32FrameData bits at reference width. Merge only identical-policy bus groups per side, preserving order; strict210pin matching and rejection of differing policies remain. Footprints/cells/graph unchanged. Optional exact mapped-LUT functional check now uses the existing Icarus13tool binding with unmodified pinned PDK models; all16LUT tile instances mapped, other tile typesRTL. Local loaded-primary testPASS; no SDF/fullmapped/timing/physical promotion.


- **D106 native literal accounting:**39989251719 proves reference210pin geometry/nonoverlap and438latches, but exact census observes one tiehi/one tielo for constant literals. Preserve exact original mapped cell counts; admit exactly these2driver cells with explicit L_HI→one_/L_LO→zero_ bindings and include their native area. No generic import-change allowance. Same run hosted mixed mapped-LUT primary testPASS, independently audited47inputs/twoexecutables; no whole-fabric gate-level/SDF/timing/physical acceptance.


## D-107: Paired representative PDN/placement/global-route experiment
- **Date:**2026-10-23. **Status:** accepted bounded diagnostic under D037/D106; no production replacement or timing acceptance.
- Start from successful preflight39996455894/source46682a2, frozen mapped netlistSHAb743335546eb7cbecd98d9fd129a26855e900ca4f868caea2f5a43167faf6b1a and hashed input bundle. Same219.84/154.08widths and185.22height, original site/row margins, pin policy and physical logic. Footprint is the only paired policy difference, including its boundary obstructions.
- Use original pinned tiny-tile96%density policy, timing-driven placement off, output-only buffers via pinned plugin scriptSHA7b9526fc…, and no synthesis/timing repair/CTS. Require all438configuration latches and every original nonbuffer cell count unchanged; record added physical support cells and cell area.
- Fixed Metal2–Metal4 signals; Metal4vertical power grid, single-layer PDN with Metal1rails, original2.1width/2.0spacing/109.92pitch. First interior column local VPWRcenter53.28µm/core-relative offset50.40; VGNDcenter57.38. Derive from macro-local12µm power phase and68.64µm west border. Verify actual full-height Metal4power pins and native zero power-grid violation count. Other column phases are not qualified by this representative test.
- Native global route has fixed50iterations and0.3capacity adjustment. Allow-congestion only retains diagnostics; independent final-table/metric checks reject nonzero overflow. No seed/iteration/layer/capacity sweep. Both fixed widths execute independently even if one fails,45min native limit/case,65min job limit.
- CLOCK_PORT=null retains leaf-interface contract and makes configured timing acceptance false. Stored20ns is the eventual target, not achieved timing. No detailed routing, antenna/signoff, extracted/SDF timing, primitive/border tile validation or whole-chip acceptance. This representative screen does not consume a full-chip hardening attempt. Preserve all failed checkpoints and native metrics.

**D107 buffer adapter provenance correction (2026-10-23):**40007850249 exposed that SHA7b9526fc… describes the cached explicit-cell adapter, not unchanged upstream dcc038217472822330b33f61fadbc06e0c3cc96d. Own the two buffer_ports argument changes in patches/r1_explicit_buffer_cell.patch; stage pinned upstream SHA bd134f7e… and apply with zero fuzz, checking final SHA7b9526fc…. Original copyright/Apache notice retained. Explicit configured buffer master avoids implicit technology choice; both footprints retain identical policy. No upstream in-place edits or hardware change.

**D107 native geometry qualification (2026-10-23):**BUG124 corrects checker semantics only: each exact-x stripe group must contain a full-height rectangle; auxiliary positive/in-bounds same-phase boundary rectangles are permitted. Both native40009049924cases reached zero-overflow GRT and zero final PGviolations before the overstrict assertion. No physical policy/netlist change; replay retains scope and pending integration gates.

## D-108: All-type R1 native pin/core and assembled-neighbor gate
- **Date:**2026-10-23. **Status:** bounded diagnostic continuation of D106/D107, not production selection or a new graph profile.
- Successful representative LUT run40009616432 establishes first-column LUT PDN/placement/GRT only. Before full-grid hardening, freeze all ten mapped JSONs from39696703659/source9768c77 by SHA, export without synthesis, generate border-aware pin policies from copied source, and import all types at the two existing footprints. Border width68.64µm and row height56.70µm follow pinned tiny-tile table; interior height185.22, widths219.84/154.08. PRIM matches its row/column LUT footprint.
- Preserve every original mapped cell and all configuration latches. Allow at most one extra tiehi/tielo for native literals, require exact constant-net binding, and include native area. Require real pins/directions, in-die nonoverlapping geometry and cell area within native core. Native sequence remains Floorplan/SetPowerConnections/IO only; retain every type outcome after failure.
- Parse the actual assembled generated fabric into a connectivity-only Yosys JSON using frozen black-box macro headers. Its40instances currently have3064adjacent bit pairs and no direct nonadjacent pairs. For each actual adjacent connection require one output/one input, opposite edge placement, same routing layer and identical tangential center. Verify native dimensions match the declared grid. No name-based inference of neighbor net pairs and no resynthesis.
- Owned r1_interfaces workflow retains76prepared files plus manifest/native artifacts, pinned container/PDK/I/O adapter; unchanged G1 and no full-chip hardening attempt. This gate adds no PDN/routing/timing claim for other tile types or column phases. Full-grid PGphase, placement/detailed routing, configured functionality/timing and equal-total-area evaluation remain open; preserve secondary UART+I2Ctimeout and sealed exclusions.

**D108 first native result and repairs:**40011371177 at234acca admits18/20geometry/core/cell cases; S_IO2 loses12transparent clock-feed alias ports during import (BUG125). A bit-identity-checked print-only normalization flattens4output-to-output aliases to their original input; no physical cells inserted. Other-type native geometry also confirms border ordering mismatch (BUG126): derive six common facing-side track orders from actual3064connections, requiring identical class sets and retaining proven LUT anchors. Store original pin orders and all changes in the artifact (88prepared files). Local55R1tests and exact assembled connectivity replayPASS; native retention/alignment remains pending. No graph/resource/production change or new physical policy sweep.

## D-109: Loaded functional proof with every R1 tile mapped
- **Date:**2026-10-23. **Status:** bounded diagnostic continuation, no production selection.
- Extend existing frame-FSM configured smoke from16mapped LUT instances to all40mapped instances, including2primitive and22border/I/O instances. Freeze ten exact exported netlist SHA hashes from D108, including the4print-only S_IO2alias normalizations. Use unchanged audited primary image and unchanged pinned PDK model bytes/Icarus13binding. Reject any netlist mismatch; preserve previous RTL/mixed-LUT modes.
- Check concurrent UART TX A5/RX69 and SPI mode0 3C/FF, host-response stalls and compiled dividers through the same loader/adapter ports. BUG127 removes only hierarchy-dependent debug logs, leaving assertions/stimulus intact. Local all-mapped1strictPASS with47input hashes; hosted replay required.
- Scope is pre-layout all-mapped fabric functional behavior for this primary sample, with RTL configuration frame FSM. No management SPI shell/CRC/parking, post-route extraction/SDF/configured timing, exhaustive protocols or whole-chip acceptance. No hardware/resource/graph change or full-chip hardening attempt.

**D108/D109 duplicate-alias correction:**40012576053 rejects alias flattening alone. Local three-way native import probe isolates duplicate continuous port assignments:143/143/155ports original/flattened/deduplicated. Own the print normalization (4rewrites plus4duplicate removals) in preparer, with frozen-bit/direction/cycle/conflict guards; no hardware insertion. Updated S_IO2export SHA7790459362b2aba666c2e205888a96ceebafd290f303a83ba0c13a15ccfdc87c; other9exports unchanged. All-mapped hash policy follows this exact export. Canonical mixed-type witness now matches in native geometry. No narrowed gate weakened or physical policy swept.
