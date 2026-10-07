# Residual timing paths and local combinations (2026-10-06)

## Extracted resync bottleneck

Audited extracted main run37529099235, source route37521491667. Slow setup WS−0.325227853853ns. The slow max report contains11violating path entries, all launched by U0 configuration word0 bit2 (`_48777_`), the TXMODE high bit. Worst endpoint `_47917_` is `u_chip.dropped[14]`. Thus the reported setup bottleneck moved from PERIOD arithmetic to mode/event qualification and fabric accounting. Keep this live configuration path timed under D-066; do not freeze modes or apply false paths.

Fast hold WS−0.008052669870ns. The min report contains5violating entries with endpoints lane0 state[0],lane0 execution immediate[1]/[0],lane1 execution immediate[7],and U0 BITSYNC TX queue[5]. These are configuration/slot-latch-to-state paths, distinct from load-flat's SRAM address hold failure. A repair designed only for SRAM does not establish resync hold closure. Report entries are not a guarantee that every violating path was printed.

## Load-flat bounded repair changed the worst hold path

Run37547755184 left exactly1fast hold violation by fresh metrics: lane1 `acc_addr[0]`→SRAM `A_ADDR[0]`,−0.0216314ns. It passes two address-selection gates and `place7589` on `net7589`; arrival0.955153ns. The original lane0/address-bit1 path is no longer the worst failing entry. Therefore do not blindly add delay to the original bit1 branch or repeat the same broad resizer pass.

Next physical hypothesis is a guarded local delay insertion on the actual bit0 SRAM data branch of this exact repaired checkpoint. Check its full connectivity and source identity before mutation, legalize/update routing, and require fresh all-corner setup/hold plus antenna checks before DRT. A buffer can also reduce upstream loading, so added cell delay alone does not predict net hold improvement. Use measured slack to decide; reject regressions. No delay insertion was applied or launched here.

Local insertion helper `scripts/ci/sram_addr_hold.tcl` is now prepared. It accepts only the exact net7589 two-pin branch, BUF1 driverplace7589 and pinned SRAM endpoint, rejects duplicate changes/missing power rails, and moves only SRAM A_ADDR[0] behind one BUF1. Placement is provisional beside the driver; caller must legalize and recompute timing/antennas. Five Tcl connectivity/guard checks pass using the cached OpenSTA Tcl runtime because standalone tclsh is unavailable. These are mock OpenDB checks, not an actual ODB mutation or a measured hold fix. The combined helper suite115checks passes; physical workflow integration remains to do after validating the exact checkpoint/route path.

## Local combination evidence

Each combination is a single reviewed patch against frozen R4, preserving2/4,all behavior,live writes and20ns. It contains exactly the existing resync rewrite plus either event qualification or producer-load flattening. These are local proof/probe experiments while isolated event routing remains active, not a substitute for its extracted results.

| Candidate | PERIOD→RX-load(ns) | Mapped module area(µm²) |
|---|---:|---:|
| Resync alone |10.669182|41905.9494|
| Resync + event-late |10.119960|41659.7958|
| Resync + load-flat |10.311445|41552.4060|

Identical-library ideal-wire probe conditions match PHASE2_EVENT_TIMING_PROTOTYPES.md. On the module `active`→RX-load query (a partial proxy for mode activation, not the full chip TXMODE path), baseline7.145837ns,resync7.115667ns,resync+event6.795213ns. Event gating modestly improves the relevant activation query; the complete routed mode path remains unmeasured for the combination. Gains are substantially less than summing isolated improvements.

Both combinations prove892module equivalence points and pass21bit-clock tests,5chip tests and2048L2 clocks. Named local verifier support is prepared; main RTL/spec and physical workflow choices are unchanged. Raw evidence is `/tmp/timing-combinations-20261006`, `/tmp/resync-critical-audit` and `/tmp/load-residual-audit`.

Prioritize resync+event for a later clean-synthesis matched screen if the isolated event route supports it. Audit/repair hold separately on the selected candidate. No combined physical dispatch, official pass or phase tick.
