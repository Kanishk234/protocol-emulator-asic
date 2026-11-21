# R1 closure status — November 20, 2026

Timing is measured and still fails. R1 is experimental; G1 remains selected.
The latest fixed-placement SPI image passes native/reset/reload and complete
zero-loop timing-model checks, but setup is **−52.591743 ns** and hold is
**−1.916775 ns** in run44857324411. It is worse than the earlier qualified
image and is not adopted. A green diagnostic workflow does not mean closure.

No physical macro geometry, hardware ABI, production source or clock target
changed. All timing numbers below use the unchanged20ns period/0.25ns
uncertainty, connected nominal RC, slow setup/fast hold cells and the original
conditional zero-I/O-delay macro boundary.

## Evidence that remains valid

| Gate | Evidence | Result and scope |
|---|---|---|
| Declared macro-interface LVS | 44627346549 | All449root ports/devices match uniquely against independently source-proven SPICE. Enclosing chip/power integration is separate. |
| Connected extracted RC | 44621669039 | Original geometry matches on all21layers; all named terminals have correct resistor connectivity. |
| Better measured original-source image | 44794158025 | Native/reset/reload, four8736-bit audits, zero loops/full active annotation. Setup−9.795382ns/hold−1.867277ns still fail. |
| Latest fixed-placement SPI image | 44857324411 | Original A control, repaired rerouted A, repaired D and management/reset/reload pass; four8736-bit audits and direct/reload states agree. |
| Latest configured timing model | 44857324411 | Four completed zero-return-code executions;370FF classified,249endpoints,14235active pins fully annotated, zero loops and identical static/dynamic-policy slacks. |
| Timing requirements | 44857324411 | Fail: setup−52.591743ns at X3Y3/_1734_/D, hold−1.916775ns at X6Y1/_1730_/D. No adoption. |

Root independently replays strict XML, every configuration frame, all four
execution receipts and slacks, and reverses all four analysis scripts
byte-for-byte to the original baseline. The original negative control is
retained. See [latest qualified negative result](r1_clock_fixed_e_loop_44857324411.json)
and [better measured image](r1_upstream_cleanup_44794158025.json).

## What the latest work fixed

The new source initially selected clock bank A, clocking all370registers and
producing a worse qualified result in44802619585. A fresh bank-D placement
failed native initialization in44829301770. Holding all other user-cell
locations fixed still exposed a rerouted-A native stall in44832060001;
clock bank alone did not explain it.

Read-only full-width and scalar VPI diagnostics localized non-advancing native
activity. Four separately proved unused-input selector changes then address
distinct failures: F.I1 atX3Y2 restores native traffic/reload; B.I3 atX1Y2,
G.I2 atX6Y2 and E.I1 atX2Y3 remove successively exposed timing loops. Each
uses actual truth-table/carry/active-route checks and exact image/frame
reconstruction. No signal is forced and no timing arc is waived.

Runs44853914939,44854958011 and44855809222 retain the failed timing controls.
The final E repair recovers the original filtered dynamic query without a tool
upgrade or query change. A manual plural-only search briefly missed the final
singular loop warning; that commentary was corrected. The strict parser never
accepted it, and explicit singular/plural regression cases now cover both forms.

## Next experiment

D168 stages a registered hard-timer terminal pulse in an isolated SPI user
source derived from the pinned original. Existing one-shot mode with HALF−2
and reload on accept/registered pulse is intended to preserve the original
pin/host cycle timing while cutting a timer-to-state combinational path.
Production RTL is untouched. Local mode0/HALF4 passes unbounded PDR output
equivalence after initial reset; arbitrary future host/MISO/reset inputs are
covered for that configuration. All eight mode/HALF4and25 proofs and32source
protocol tests are required before any compile. No fit, native or physical
timing claim is made for this new source candidate.

## Remaining acceptance gates

Both setup and hold must pass on the same real image and unchanged constraints.
Native functionality and a qualified negative timing result are necessary
progress, not closure. Do not promote the worse fixed-placement source image
or tick a phase exit box.

Enclosing physical power, full shell/chip integration, loading-mode timing and
complete corner qualification remain open. The missing regular-grid VGND stripe
was tested only in a synthetic overlap probe; an actual full-chip PDN repair,
connectivity/DRC and timing qualification have not been established.
