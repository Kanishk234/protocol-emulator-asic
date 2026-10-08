# Phase 2: building and fitting the chip

**Status:** in progress, updated 2026-10-07. The current timing target is the complete design with2 lanes,4 pin units,U0 full and SRAM at20ns/50MHz in6x4 tiles. Close official timing at2/4 first, then consider3/6 if area permits (D-070). See [phase checklist](../design/phases/PHASE2_RTL_CORE.md).

## The goal

Build the lanes, token fabric, timed pin units, host interface and routine memory, verify them against an independent software model, and make the full chip pass physical checks and timing in the official GDS workflow.

## What we did

The core RTL exists. The frozen2/4 candidate passed one million model/RTL comparison clocks, and injection checks caught two deliberate bugs. UART, SPI and I2C have pin-level reference-model and sigrok evidence. Expanded routed gate-level checks pass22/22 for original event-late125ps run37581139271 and shared-RX run37659138336. These check function without SDF timing simulation; they do not prove physical timing.

Historical official GDS run36799356107 passed DRC/LVS/antenna/precheck and typical timing, but slow setup was -10.698ns. Later full-design extracted experiments improved slow timing. The strongest measured setup candidate is original event-late plus125ps hold repair: slow setup -0.179789ns and fast hold +0.037290ns (extraction37581139249). Its two reported failures end at RX timer bits through live pin configuration and pin feedback.

A larger shared-RX arithmetic change proved equivalent and passed function, but its extracted setup regressed to -1.427891ns at dropped-event counter/fabric endpoints. It is not promoted. The smaller banked pin selector retains original RX and passes60pin tests,5chip tests and2048model-comparison clocks. Its routing screen had one -22.37ps SRAM address hold failure.

A guarded SRAM address buffer plus bounded repair now passes pre-routing checks in37690561695: setup WS0 at all corners, post-antenna fast hold +0.0700513ns, positive slow/typ hold, zero antenna violations and zero global-routing overflow. The repair adds422hold buffers and increases area about3.03% from its source checkpoint. A continuation is prepared to measure detailed routing and extraction; no closure claim is made from routing estimates.

## What we found

Equivalent logic can shift mapping, placement and critical paths elsewhere in the chip. Faster local arithmetic did not guarantee better full-chip timing. Routing screens are useful filters, but extracted parasitics have repeatedly exposed regressions. Live configuration remains timed; no false paths or changed cycles hide failing behavior.

Functional evidence is strong. Physical timing and area must still be judged together on the exact final candidate. Saved-checkpoint improvements also need a reproducible clean-build recipe in the official flow.

## What's left

- Route and extract the reviewed repaired banked candidate, then compare with the original -0.179789ns baseline.
- Achieve positive setup WNS and nonnegative all-corner hold, without losing protocol or live-configuration behavior.
- Reproduce the selected full design in official GDS; pass DRC/LVS/antenna/precheck and matching gate-level tests.
- Complete the routable-budget decision, revalidate the adopted hardware and keep required CI green on final main. Phase2 stays open until all exit requirements pass.

## One-line takeaway

The full chip works in simulation and the strongest extracted setup result is179.8ps short; the next repaired candidate passes preliminary timing gates but still needs routing, extraction and official validation.

Detailed evidence: [baseline recovery](../reports/PHASE2_SHARED_RX_REGRESSION.md), [repair-only screen](../reports/PHASE2_BANKED_SRAM_HOLD_SCREEN.md), [routed follow-up review](../reports/PHASE2_BANKED_SRAM_HOLD_ROUTE.md).
