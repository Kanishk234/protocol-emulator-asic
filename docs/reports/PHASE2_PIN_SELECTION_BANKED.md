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
