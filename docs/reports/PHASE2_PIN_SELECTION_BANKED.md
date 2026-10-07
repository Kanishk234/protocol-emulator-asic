# Banked pin-selection prototype

The 125 ps extracted candidate has two slow setup failures from live U0 PIN_A configuration through output-pad feedback and unit 3 selection into its RX timer. This study examines the selection portion without changing the chip contract, adding a pipeline, or caching live configuration.

## Transformation

`pin_select_banked.patch` changes only `trw_pin_io.v`. Invalid C indices 24–31 select `c_active`, preserving `c_in` and unconditional selection. For `sel`, each eight-pad bank compares its selected pad with `c_active`; the upper two index bits then select one of the three bank results or constant true for the invalid bank. All previous-value registers and edge detection retain their behavior. No new state or protocol-specific feature.

## Matched local module probes

Identical Yosys 0.69+24 synthesis/ABC with the pinned typical IHP library; slow-library OpenSTA, ideal wires, 20 ns clock, zero IO delays, 0.01 pF output loads except `sel` at 0.073071 pF (the measured critical-net load). These are module probes, not extracted full-design timing.

| Form | Area (um²) | Worst input→sel (ns) | Pad→sel (ns) | C_ACTIVE→sel (ns) |
|---|---:|---:|---:|---:|
| Frozen baseline |1453.3344|1.753429|1.511804|0.674786|
| Factored validity |1667.2824|2.607234|not pursued|not pursued|
| Padded defaults |1391.5692|1.621771|1.589266|1.145590|
| Polarity before selection |1446.0012|1.597347|1.564838|0.943722|
| Banked comparison |1431.5238|1.475245|1.442738|0.796614|

Reject the factored form. Padded/polarity forms improve index paths but worsen the measured pad path, so do not launch them as fixes for this failure. The banked form reduces module area about 1.5% and pad-path delay 69.066 ps, but worsens C_ACTIVE delay 121.828 ps. Check all endpoint paths and hold after integration; this tradeoff is not an unconditional timing gain.

## Verification and adoption gates

Named module equivalence against frozen `trw_pin_io` proves 19 points with `equiv_simple`; no remaining induction obligations. Tested combination uses frozen 2/4 event-late + shared-RX, independently generated frozen Python encodings. Pin suite passes 41/41, zero failures/skips. Chip suite passes 5/5, and the 2048-clock model/RTL lockstep passes with zero divergence.

Raw evidence: `/tmp/pin-selection-factor-20261007` and `/tmp/pin-selection-banked-verify-20261007`. Main RTL/config/spec unchanged. No physical screen launched. After the current shared-RX routed extraction is available, decide whether this hypothesis addresses its actual residual failures; compare against the exact shared-RX baseline and retain all source provenance, corner timing, hold, overflow and physical gates.

## Follow-up baseline choice

Shared-RX extracted setup regresses to -1.427891 ns at dropped-counter/fabric endpoints, so the follow-up excludes that RX arithmetic change. Prepared bs_event_pin_banked.patch uses only event-late and banked IO against frozen3393eea. This isolates the selector hypothesis against the original125ps candidate; do not carry the shared-RX prototype into this comparison. Local candidate verification is recorded in PHASE2_SHARED_RX_REGRESSION.md.

## Matched physical screen37669663762

Both jobs complete successfully as diagnostics, but the banked source is not timing-clean. Fresh banked setup WS0 at fast/slow/typ; hold WS -0.0223693/+0.147057/+0.0526946 ns. Matched event-late baseline hold +0.0313302/+0.229262/+0.102516 ns, setup WS0. Banked fast hold therefore worsens53.6995 ps and is negative. Final GRT overflow is zero for both; demand244196 versus239415 (+2.00%), usage40.81% versus40.01%. No extracted timing improvement has been demonstrated. Existing source timing guard must refuse direct routing; inspect actual min paths and any bounded repair before deciding.

Artifact11506981784 independently confirms exactly one fast hold violation: lane1 acc_addr[8]→SRAM A_ADDR[8], -0.0223693 ns. Next SRAM address1 path is +0.032286 ns. Slow/typ hold violation counts zero; all setup counts zero. Repair metrics report33156 instances,510973 µm² versus earlier matched baseline510232.98 µm² (+0.145%); the earlier baseline area is not independently downloaded from this new run.

Prepared `scripts/ci/banked_sram_addr_hold.tcl`: accepts only net9161 with BUF2 driverwire9161/X and SRAM A_ADDR[8], rejects changed connectivity/master/power and duplicate insertion, and adds one BUF1 solely to that sink. Five Tcl mock guard tests pass using cached OpenSTA's Tcl runtime. This is not a physical timing result. Attempted real OpenDB validation is blocked by missing libQt5Charts.so.5 in the local OpenROAD installation; no real ODB insertion or legalization has been validated. Caller must independently validate exact source/checkpoint, legalize, recompute routing/all-corner timing, and check antennas before DRT. No physical follow-up launched.
