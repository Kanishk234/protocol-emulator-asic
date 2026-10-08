# Native screen to official build: integration audit

2026-10-08. Preparation only; no candidate is promoted and no phase gate passes.

## Concrete mismatch found

The existing isolated full-design preparation at `/tmp/tripwire-event-nor2-official-prep-20261008` has `PNR_SDC_FILE=dir::pnr.sdc`. That file contains `set_false_path -setup -to [all_registers -level_sensitive -data_pins]`. Its signoff file does not. The current native screen explicitly uses `src/signoff.sdc` for PNR as well. Therefore copying the older preparation unchanged would not reproduce the native experiment's optimization constraints, even if final signoff remains fully timed. Keep D-066 live configuration paths timed throughout the proposed recipe.

## Differences that must be reviewed together

| Input | Older preparation | Current native screen | Integration action |
|---|---|---|---|
| Hardware | Frozen full 2/4 event-late candidate | Same candidate and event-late patch | Preserve exact source fingerprints; main currently has placeholder top |
| Clock/density |20ns/56% |20ns/56% | Retain |
| PNR constraints |Inherited latch setup exceptions |Fully timed signoff SDC | Point both PNR and signoff to audited fully timed constraints |
| Synthesis |Inherited/default strategy |AREA0 or AREA1 | Wait for matched full-chip results before choosing |
| Global routing |Inherited configuration |Uniform adjustment0.16 | Record explicit tested value; no regional wrapper |
| Timing placement |Inherited configuration |Enabled | Reproduce tested setting |
| Mirroring optimization |Inherited configuration |Disabled | Reproduce tested setting |
| Placement/GRT setup margin |Inherited defaults |Both0ns | Preserve actual tested margins; do not increase to chase zero-slack latch paths |
| PNR/resizer corners |Inherited defaults |All three PNR corners; initial resizer slow | Reproduce exact corner lists |
| Fresh post-GRT repair |No separate audited screen invocation |Explicit all-corner repair and fresh STA after GRT | Critical unresolved reproduction difference: native stock image alone does not prove the official flow runs the same sequence |
| Checkpoint ECOs |Not included |Not included in native mapping comparison | Driver/NOR/hold checkpoint success cannot be attributed to native mapping |

Sources: `scripts/ci/rtl_grt_screen.py`, `.github/workflows/gds-native-mapping-screen.yaml`, and the isolated preparation's config/SDCs. This is a static review, not a hardening result. Project-config changes outside the AGENTS whitelist require a reviewed exception before adoption; official template jobs stay unchanged.

## Results-dependent decision

Native comparison37819169130 must supply actual full-chip cell area, routing overflow, all-corner setup/hold and antenna counts for both jobs. Local single-module AREA1 improvement is insufficient. Keep each job's RTL, merged config, effective constraints, corner ordering, repair settings and checkpoint together. Do not combine AREA0 placement with AREA1 netlist or reuse driver checkpoint provenance for these artifacts.

If a native candidate qualifies, first establish how its explicit fresh all-corner repair is reproduced by the unchanged official build, or run a matched stock full-flow experiment that does not rely on that separate repair step. Then obtain detailed-route extraction and routed protocol evidence for that exact recipe. A favorable GRT measurement alone is not authorization to declare official closure.

Driver routing37819598187 is independently testing the small checkpoint repair. Its extracted result can establish whether the loaded-cell hypothesis survives rerouting; it cannot establish clean synthesis reproducibility. Original event-late extracted slow setup−0.179789ns remains the best measured baseline pending better actual extraction.

## Pinned-flow ordering follow-up

Inspected `librelane-3.1.0.dev3` wheel's `flows/classic.py`, `steps/openroad.py` and `scripts/openroad/rsz_timing_postgrt.tcl`. Classic already contains `OpenROAD.ResizerTimingPostGRT`; a custom official job or new physical Tcl hook is unnecessary for invoking native repair itself.

The actual sequence is GlobalRouting → CheckAntennas → RepairDesignPostGRT → DiodesOnPorts → HeuristicDiodeInsertion → RepairAntennas → ResizerTimingPostGRT → STAMidPNR → DetailedRouting. The diagnostic instead resumes ResizerTimingPostGRT directly from the first global-route checkpoint. Added diodes and intervening design repair can change load and timing, so these sequences are not equivalent merely because they share the final repair step.

The native repair script reruns GRT/estimated parasitics, runs setup before hold unless FIX_HOLD_FIRST is enabled, then detailed placement and normally GRT again. Setup cloning, buffering and buffer removal are configurable; hold avoids setup violations by default. Thus the clean-build follow-up should preserve the stock sequence, match fully timed constraints and corner/margin settings, and measure the actual post-antenna repaired checkpoint before DRT. Compare both timing and antenna counts after repair; the earlier antenna check alone cannot establish final antenna cleanliness.

Current screen uses slow-only RSZ_CORNERS before its separate all-corner repair. Setting RSZ_CORNERS to all corners globally would also change earlier placement/CTS resizer steps. That is a separate experiment, not an exact reproduction of this screen. Keep that distinction explicit when reviewing native full-flow configuration options.

## Successful checkpoint candidate and clean-build follow-up

Residual routing37837038264 succeeds. Extraction37844735445 reports setup WS0 in every corner and hold fast+0.062788609ns/slow+0.315522950ns/typ+0.157048712ns. Routed GL37844735520 passes22/22 with no skips. This establishes nonnegative extracted timing and routed functionality for this checkpoint recipe, not official clean-build closure.

Important correction to the ordering audit above: the pinned Classic step list contains ResizerTimingPostGRT, but its RUN_POST_GRT_RESIZER_TIMING option defaults to false. Presence in the step list does not guarantee execution. A reproducible native recipe must explicitly enable it.

Prepared native_stock_screen.py and gds-native-stock-screen.yaml: clean synthesis AREA0/AREA1, stock Classic sequence through post-antenna repair, explicitly enabled post-GRT timing repair, all three resizer corners throughout,125ps hold target, fully timed PNR/signoff constraints, unchanged20ns/56%/SRAM/resource shape. No custom image, named-cell ECO, saved initial checkpoint or second repair. Fresh STA rereads the resulting stock checkpoint. This is a new experiment because earlier placement/CTS now also sees all resizer corners; it is not an exact reproduction of previous native screens. It stops before DRT and does not claim extraction or official signoff. Main hardware and official template jobs are untouched.
