# Phase 2: building and fitting the chip

**Status:** in progress, updated 2026-10-08. The current timing target is the complete design with2 lanes,4 pin units,U0 full and SRAM at20ns/50MHz in6x4 tiles. Close official timing at2/4 first, then consider3/6 if area permits (D-070). See [phase checklist](../design/phases/PHASE2_RTL_CORE.md).

## The goal

Build the lanes, token fabric, timed pin units, host interface and routine memory, verify them against an independent software model, and make the full chip pass physical checks and timing in the official GDS workflow.

## What we did

The core RTL exists. The frozen2/4 candidate passed one million model/RTL comparison clocks, and injection checks caught two deliberate bugs. UART, SPI and I2C have pin-level reference-model and sigrok evidence. Expanded routed gate-level checks pass22/22 for original event-late125ps run37581139271 and shared-RX run37659138336. These check function without SDF timing simulation; they do not prove physical timing.

Historical official GDS run36799356107 passed DRC/LVS/antenna/precheck and typical timing, but slow setup was -10.698ns. Later full-design extracted experiments improved slow timing. An earlier baseline was original event-late plus125ps hold repair: slow setup -0.179789ns and fast hold +0.037290ns (extraction37581139249). Its two reported failures end at RX timer bits through live pin configuration and pin feedback.

A larger shared-RX arithmetic change proved equivalent and passed function, but its extracted setup regressed to -1.427891ns at dropped-event counter/fabric endpoints. It is not promoted. The smaller banked pin selector retains original RX and passes60pin tests,5chip tests and2048model-comparison clocks. Its routing screen had one -22.37ps SRAM address hold failure.

The banked candidate later routed cleanly and passed22/22 protocol tests, but extracted slow setup regressed to−2.475764ns. It is rejected for promotion.

Small cell-sizing trials then targeted the live configuration→pin-unit decision→dropped-counter path. The hold-repaired route37807978035 is clean, and extracted fast hold improves to+0.109290ns, but slow setup is−0.603908ns. We independently reproduced that result and found8 printed failing paths sharing one upstream driver. Sizing that driver clears those failures on unchanged extracted wires, with small cell-area cost; it still needs fresh physical proof.

Driver extraction37825505569 improved slow setup to−0.147084ns and passed22/22 routed protocol tests. A further three-cell repair then routed successfully37837038264; extraction37844735445 has setupWS0 at every corner and minimum hold+0.062789ns. Routed regression37844735520 passes22/22, no skips. Local all-corner extracted sweeps match CI and tolerate19.85ns against the20ns requirement, demonstrating150ps tested period reserve. This timing-passing checkpoint still reports91slow slew and6slow cap violations (7cap attyp/fast), so it is not electrically clean. Global zero setup remains dominated by latch time-borrowing reports; no strictly positive global setup claim is made.

Clean-build stock screens37853023857 AREA0/AREA1 both report setupWS0 and positive hold; AREA1 fast hold+0.119326ns, final GRT zero overflow and cell area524688.31µm² including SRAM. Electrical checks still fail: AREA1 has21 slow slew violations and one cap violation per corner. Native AREA1 route37859526262 then completed but extracted slow setup regressed to−1.423654ns, with133slow slew and6cap failures. Stock design-repair screen37858535440 clears screen cap counts but leaves18slow slew failures. The earlier residual checkpoint remains the best measured candidate; clean-build closure and official electrical closure remain unproven.

## What we found

Equivalent logic can shift mapping, placement and critical paths elsewhere in the chip. Faster local arithmetic did not guarantee better full-chip timing. Routing screens are useful filters, but extracted parasitics have repeatedly exposed regressions. Live configuration remains timed; no false paths or changed cycles hide failing behavior.

Functional evidence is strong. Physical timing and area must still be judged together on the exact final candidate. Saved-checkpoint improvements also need a reproducible clean-build recipe in the official flow.

## What's left

- Qualify the clean-build native candidate through fresh antennas, detailed routing, extraction and routed protocol verification; resolve slew/capacitance failures.
- Preserve measured setup/hold reserve without losing protocol or live-configuration behavior; distinguish latch-reported zero WS from actual endpoint margins.
- Reproduce the selected full design in official GDS; pass DRC/LVS/antenna/precheck and matching gate-level tests.
- Complete the routable-budget decision, revalidate the adopted hardware and keep required CI green on final main. Phase2 stays open until all exit requirements pass.

## One-line takeaway

The checkpoint candidate passes extracted setup/hold and routed protocols; clean-build extraction, electrical cleanup and official GDS are the remaining physical gates.

Detailed evidence: [closure research](../reports/PHASE2_CLOSURE_RESEARCH.md), [baseline recovery](../reports/PHASE2_SHARED_RX_REGRESSION.md), [repair-only screen](../reports/PHASE2_BANKED_SRAM_HOLD_SCREEN.md), [routed follow-up review](../reports/PHASE2_BANKED_SRAM_HOLD_ROUTE.md).
