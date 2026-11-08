# Phase 2: parallel tests that can carry into official hardening

The target remains full2lanes/4pin units/U0full/SRAM/6x4 at20ns, nonnegative all-corner setup, fast hold at least50ps, zero electrical/antenna/route violations and a green unchanged official GDS/precheck. No phase boxes are ticked by these experiments.

## What is portable now

The current combined baseline42305323874 already starts from RTL using TT config generation and stock LibreLane Classic, image, scripts and stage order. Historical custom Metal2-region wrappers are not in this lineage. Its native project controls are technically supported by the official flow, although adoption of config keys beyond AGENTS' main-file whitelist still needs an explicit reviewed exception.

The green experimental checkpoint42394957445 additionally uses six manually placed diodes and two guide detours. Neither these edits nor the current detailed-wire restart are reproduced by normal official hardening. Keep those experiments as diagnosis; do not promote their green result as a reproducible official design. The source/config candidates below explicitly exclude those interventions.

## Independent clean-from-RTL matrix

All five arms prepare the exact verified combined baseline, generate configuration with unchanged TT tools, and run the normal stock Classic flow through final pre-routing STA. They do not load a checkpoint, wrap the engine, add physical cells or edit guides. They repeat source-bound original and signoff three-corner audits with the same strict electrical/antenna/overflow gates. If any arm fails, its artifact is retained and the others continue. No arm proceeds automatically to detailed routing.

| Arm | Single difference from combined baseline | Hypothesis | Main risk |
|---|---|---|---|
| density64 | Placement target56→64% | Change placement distribution above the historical61% effective floor; measure whether local pin-access/routing pressure improves | This increases requested density; it can worsen congestion. Lower54% was clamped and was not a real experiment |
| clock75 | Clock-sink cluster diameter100→75µm; eight-sink limit retained | Tighter physical groups may reduce skew/needed data-delay repair and redistribute clock loading | Extra clock buffers, area, antenna or skew/hold regression |
| late125 | Late hold optimizer target175→125ps; early175ps retained | Reduce late delay-cell/reroute changes after antenna repair; baseline fast hold138.366ps leaves measured screening reserve above50ps | Actual slack is not linear in optimizer target; unchanged50ps gate must reject a regression |
| mode_ff | Replace TXMODE[2:0]/RXMODE[1:0] storage latches with write-enabled root-clock flops, retaining existing IDLE flop | Remove additional latch-launch control paths while preserving live-write timing/reset semantics; a general configuration primitive | Twenty extra latch-to-flop swaps across four units may add area/root-clock load or hurt hold; physical benefit unmeasured |
| debug_align | Pad each180bit host debug record to256bits before dynamic lane selection; retain word-read decode | Reduce unaligned variable selection cost without new stored bits or latency | Whole-design mapping may differ; proof/smokes required before launch, routed benefit unmeasured |

The clock and hold optimizer mechanisms are described in OpenROAD's [CTS](https://openroad.readthedocs.io/en/latest/main/src/cts/README.html) and LibreLane's [timing closure guide](https://librelane.readthedocs.io/en/stable/usage/timing_closure/index.html). Our installed/pinned code and existing native-command validators, not newer advertised features, determine supported behavior.

The mode-storage candidate passes full-module lean/full equivalence (461/560 points, induction cap6),2080cycle/10400phase checks each, exhaustive all65536mode-word values under both reset polarities, and a reset-gating negative control. Five matched chip smoke cases pass. Generic counts show exactly five latches replaced by five enabled flops per unit, all other counts unchanged; this is not mapped area. Both source candidates pass five matched chip smokes and have full22protocol replays running concurrently using matching2/4 software maps and real sigrok decoding. Neither a full-chip formal nor full-suite pass is claimed before that evidence exists.

Actual source preparations are replayed locally: configuration arms alter only src/config.json; the mode_ff/debug_align arms respectively change only src/trw_pin_cfg.v/src/trw_host.v and keep baseline config byte-identical. Existing stock_profile_effective validates real density (rejecting clamping), CTS command arguments and late hold target/reroute execution. The signoff audit is unconditional. Main RTL/config and official jobs stay untouched until a candidate is selected and reviewed.

## Further ideas, ranked after these measurements

1. **Measure and retain debug-record alignment only if the full design benefits.** This fifth arm builds on the successful port-status alignment mechanism and differs from the older rejected per-lane word-first selector. Complete host/SPI equivalence passes1062points at2/4 and1144at3/6. Isolated guarded debug-word mapping at2/4 changes7621.803→4622.2974µm² and1467.61→1321.73ps; these are cone-level results, not full-chip PPA. The3/6 cone has a small delay regression despite area reduction; no3/6physical upgrade is proposed.
2. **Retain a configuration flop frontier chosen by actual extracted paths.** If mode_ff helps, select the next genuinely critical configuration bits from new extracted startpoints. Avoid converting every latch, which could spend area/clock power without fixing the limiting paths. Each change gets phase/reset equivalence and one clean hardening.
3. **Reduce hold-repair demand by clock topology before adding more delay cells.** clock75 is a controlled first test. Use its actual skew/buffer/repair counts to choose a topology direction. Larger hold targets already increased area/overflow sharply; do not assume more delay cells is improvement.
4. **Shrink generic host/control mux structures while preserving latency.** Prefer constant word alignment, common predicate sharing and bounded selection over adding pipeline cycles. Existing parity banks, shared-priority lane logic, C-selector cleanup and host-port alignment are already present; avoid redoing them under new names.
5. **Local placement/pin-access relief from the96marker layout.** If wire repair plateaus, map exact conflicting pins and nearby sites before testing a small source/portable-placement change. A manual physical workaround that cannot be represented by normal project inputs does not solve official reproducibility.
6. **SRAM placement/orientation only after checking power integration.** This is an officially representable macro-block change, but can move setup paths and invalidate Metal4 power alignment. Current markers are not at the macro origin; no evidence yet supports this as the first fix.

Do not repeat the combined early250 experiment (overflow237), ineffective lower-density clamp, failed unrestricted maze reroutes, or already-rejected mirroring/cell-exclusion sweeps without new evidence. Do not cut lane/unit resources, lower protocol coverage, false-path live configuration, increase the20ns period, add protocol-specific blocks or relax acceptance to manufacture a pass.

## Selection and completion

First require a clean-source screen with all gates passing. Compare actual area, effective density, clock/hold-cell count, antenna locations and overflow, not job color alone. Then run normal detailed routing and extracted all-corner timing/electrical/antenna/connectivity on that same candidate. The final routed netlist needs all22protocol cases; source RTL changes also need complete matching functional replay. Review and adopt only reproducible source/config inputs, keeping source lists synchronized. Finally run unchanged official GDS/precheck/gl_test and remaining main CI; update Phase2 checklists only with exact evidence.
