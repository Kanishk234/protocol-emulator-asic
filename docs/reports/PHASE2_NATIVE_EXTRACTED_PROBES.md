# Native extracted failure: targeted drive and hold-delay probes

2026-10-08. Independent fixed-parasitic experiments, not a physical pass or official clean-build recipe.

## Baseline and first measurements

Actual extraction37859526262/artifact11587186953 supplies NL and nominal SPEF; pinned three corner standard-cell/SRAM libraries and standalone fully timed constraints are used. All six original20ns baseline slack measurements match CI within1e-6ns. Unsupported replacement masters, failed commands and missing-cell/black-box diagnostics are rejected. No state, connectivity, clock, uncertainty, derate or protocol behavior changes.

24 initial STA processes:

| Master-change probe | Slow setup WS ns |
|---|---:|
|Original native extracted|-1.423654079|
|place7221 BUF1→4|-0.850912273|
|24876 INV1→2|-1.201975465|
|30202 NOR3_1→2|-1.140968204|
|30203 INV1→2|-1.269306421|
|37732 NAND2_1→2|-1.140968204|
|Feedback BUF4+INV2|-0.850912273|
|Combined five|-0.565561831|

The failing endpoint47345 maps to dropped[67]. After the five-cell probe the bottleneck moves to RX rt[23], endpoint46391. This confirms multiple critical branches; unchanged global worst slack does not prove an individual resize has no local benefit.

15 second-stage processes: adding24896 NOR2_2 and29918 NOR3_2 to those five improves slowWS to−0.262710750. Additional place6637 BUF2 or43915 AND3_2/43917 NOR2_2 offers no further global gain. Remaining worst endpoint46883 lies on a different pin path.

15 delay-probe processes: replacing hold12888 DLYGATE4SD3 with SD2 improves to−0.099536382; replacing both hold12888 and hold12418 with SD2 gives setupWS0 at every corner. SD1 also gives0 but offers no global advantage, so prefer the less aggressive SD2 probe. Seven strength changes plus two SD2 substitutions add29.0304µm² of library area. No reroute area or extracted gain is claimed.

Worst hold remains fast+0.094072364ns/typ+0.196308970ns/slow+0.370721012ns in all three stages. Positive global hold in the fixed-parasitic probe does not guarantee rerouted hold. Best original residual candidate37844735445 remains preserved and is not superseded by this local estimate.

## Clean-build implication and prepared comparison

The native flow inserts setup-costly hold delays. A bounded native hold-target100ps screen is prepared against the stock125ps baseline, changing only GRT_RESIZER_HOLD_SLACK_MARGIN. Actual signoff uncertainty and20ns timing contract stay fixed. Native source remains full2/4 bs-event-late AREA1, all resizer corners, unchanged56% density and SRAM. No named-cell ECO, technology-cell RTL, new state or extra cycles. Electrical design repair stays at the original default in this comparison so the changed option is isolated.

The100ps option is an experimental repair target, not a lowered acceptance threshold: any continuation still needs nonnegative all-corner setup/hold, at least50ps fast hold, zero routing overflow and fresh antenna clearance. Screen qualification does not establish routed/extracted closure or fix all electrical failures. This comparison tests whether native synthesis/repair can reduce unnecessary delay rather than prescribing nine opaque cell IDs in official RTL.

54 targeted helper checks pass, including default recipe preservation, bounded margin rejection and actual orchestration/receipt propagation for100ps/125ps. Raw scripts, probe logs and comparisons stay in/tmp/tripwire-native-{cone,residual,delay}-probes-37859526262.

## Minimization and older checkpoint electrical audit

30 further all-corner minimization processes: reverting the two INV2 substitutions and30202 NOR3 sizing retains setupWS0 and unchanged hold. Final six-change estimate is place7221 BUF4,37732 NAND2_2,24896 NOR2_2,29918 NOR3_2,hold12888 SD2 andhold12418 SD2. Added library area18.144µm². Reverting37732, weakening place7221 toBUF2 or reverting24896 reintroduces negative setup in tested controls. This is a measured reduced set, not an exhaustive minimum-cell proof. Total84 local STA processes across the original and reduced probes; no physical pass claimed.

Fresh review of earlier passing extraction37844735445 checks.rpt finds slew counts slow91/typ3/fast1 and cap counts slow6/typ7/fast7. That checkpoint passes measured setup/hold and routed protocol tests but is not electrically clean. Official readiness must address these constraints as well as clean-build setup reproduction; do not treat earlier timing closure as all-requirements closure.

## Hold100 screen result

Run37866086829 succeeds in42min on7b87718. SetupWS0 every corner; holdfast+0.100882ns/typ+0.204349ns/slow+0.382839ns. Post-repair area514025.08µm² including SRAM (−10663.23µm²/~2.03% vs125ps baseline),33245cells vs33898; finalGRT39.56% with zero overflow. Electrical violations remain slewslow18/typ1/fast1 and cap1everycorner. The reduced native hold target changes physical cell choices and reduces area, but extracted setup benefit is unproven until this exact checkpoint is routed/extracted. Evidence artifact11589244417. No promotion or official closure.

## Prepared hold100 routing qualification

Exact screen37866086829/head7b87718 now has a guarded native_stock_route hold100 profile and separate gds-native-hold100-route workflow. It preserves100ps repair target but requires the same50ps fast-hold gate, nonnegative all-corner timing and fresh antenna clearance before DRT. Congestion-disallowed post-timing cleanup preserves repaired guides; successful zero-DRC DRT triggers extraction.72 helper checks pass with both source profiles and exact source/config rejection. No extracted improvement or electrical readiness inferred from the screen.
