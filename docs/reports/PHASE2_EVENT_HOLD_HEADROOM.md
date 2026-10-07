# Event-late hold-headroom experiment (2026-10-06)

Leading measured candidate: event-late source37533969613,route37546499438,extraction37551577987 and routed GL37551578053. Extracted setup WS0at all corners; fast hold−0.014614976310ns,slow+0.104597222733ns,typical+0.030520697944ns. Final min report contains three violating entries: lane1ex_imm[6]−14.615ps,[7]−7.615ps,U0TXct[0]−6.856ps. GL log confirms22/22tests,0failure/skip. Its setup worst report includes a flop→latch zero-slack borrowing path; positive useful-path headroom remains to audit.

Original repaired screen config uses GRT_RESIZER_HOLD_SLACK_MARGIN0.05ns and SETUP0.0ns. Pre-route fast hold+0.0313302ns became−0.014615ns after route/extraction. The proposed isolated experiment uses a100ps hold-repair target on the same verified source checkpoint before antenna/DRT, aiming to retain headroom through physical changes. No guarantee that a larger target achieves it; actual extracted results decide.

Existing route workflow gains optional pre_route_hold_target choice source(default)/0.10. The new choice is restricted to bs-event-late and performs exactly one all-corner repair with setup target0.0 and hold target0.10. Require fresh setup/hold checks to pass at all corners and fast hold WS≥0.05ns before continuing. Existing post-antenna timing/antenna and route DRC gates remain. Saved headroom comparison is included in downstream extraction artifacts. Constraints,20ns clock,resources,RTL,source identity and official template jobs are unchanged.

Helper validates the selected hold target against resolved repair configuration and rejects unbounded/NaN/infinite values.131combined helper tests pass, including default preservation, explicit target propagation, all-corner/headroom gating and invalid-target rejection. Both edited workflows parse,choice/default checks and git diff check pass. Tcl tests use cached OpenSTA's Tcl runtime via temporary launcher, not physical OpenDB.

Proposed dispatch: source_run_id37533969613,source_variantbs-event-late,pre_route_hold_target0.10,repair_postantenna_holdfalse. CI/docs publication and launch pending scoped authorization. No physical hold improvement,combined RTL adoption or official timing pass claimed. Local resync combinations and SRAM-delay prototype remain separate unpublished work.

## Measured 100 ps trial and proposed 150 ps follow-up

Run37557256170 failed before antennas/DRT at the unchanged50ps headroom gate. Fresh fast hold improved31.3302→48.7026ps; slow229.262→376.427ps; typical102.516→178.650ps. Setup WS remained0allcorners. Extraction37558180965 andGL37558180997 skipped; there is no new extracted result.

The actual repair log reports241 endpoints below its100ps target and255 inserted buffers (+0.8% area). It reached100ps internally, then legalized (maximum displacement14.9um) and rerouted. Fresh STA's worst path is slot latch `_50151_` (`lane0.slots[461]`) through `_34673_`, `_34675_`, `_34676_`, `_34677_` to `_46523_` (`lane0.acc_addr[4]`), +48.703ps. Next reported endpoints are U2RXsst[2]+55.372ps, U2TXer[1]+55.628ps and lane0ex_imm[3]+59.044ps. This is not the original extracted event failing endpoint set. Saved artifact11454893508, local audit `/tmp/event-headroom-audit`.

Prepare an optional150ps repair target on the original trusted event source37533969613 (not an automatic retry of the mutated state). Keep zero setup target, one repair, fresh all-corner pass,50ps minimum fast hold, antenna/DRC guards and final extracted checks. Default remains source;100ps remains reproducible. Extra buffering may hurt setup or routing; no physical success asserted. Changes are local pending publication.

All1000 entries in this trial's slow max report end at latches and have zero reported slack. This report cannot establish execution-path setup margin; a separate flop-endpoint report is needed without changing constraints or hiding latch checks.
