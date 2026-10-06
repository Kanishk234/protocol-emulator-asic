# Compact native unknown-state diagnosis

The compact design has not passed native UART simulation. This is a separate
gate from routing and timing. Diagnostic companions have unconnected outputs;
actual mapped output continues to determine pass/fail. No configuration or
user storage is forced. The existing D-023 routing hold/pulse still limits the
scope of these tests.

## Evidence

- [37523983755](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37523983755):
  immediately before the first corrupt timer clock, all8707 mapped configuration
  bits are known and match the loaded image. Timer count is15, all16 D inputs
  are unknown, and all reset pins are inactive. Configuration corruption is
  not observed at that instant; the upstream cause is still unresolved.
- [37533766076](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37533766076):
  a separately loaded whole-RTL companion remains known where native route
  vectors become unknown. Incoming routes differ, so this comparison alone
  cannot identify a bad local gate.
- [37534251857](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37534251857):
  all35 per-tile companions compile and load from the actual native frame input
  ports. At4423490ns,49 data-output ports differ on RTL-known bits despite
  sharing actual native tile inputs. The diagnostic logs the first24. Native
  UART and separate host-reset probes still fail. Tile internal state is
  independent and can differ; these output differences are not an equivalence
  proof or a hardware correction.

## Distinguishing two explanations

[Piper and Vimjam, X-Propagation Woes](https://dvcon-proceedings.org/wp-content/uploads/x-propagation-woes-masking-bugs-at-rtl-and-unnecessary-debug-at-the-netlist.pdf)
describe both RTL conditional optimism, which can hide uncertain behavior, and
gate-level pessimism from lost correlations at reconvergent logic. A known RTL
value beside a native unknown does not distinguish them. Our inference is to
check exact local inputs, configuration, state and all binary input completions
before selecting a mapping, reset or simulation correction. The paper does not
establish which explanation applies to WARP.

The next focused diagnostic at7f5442a observes the same-input TB timer and
24 LUT cells in Tile_X1Y2, Tile_X2Y1 and Tile_X2Y3. For each LUT it reports the
truth table, effective index, reset/enable, registered state, combinational and
selected output, retained native aliases, and conservative output possibilities
over every unknown index completion. A singleton set can establish a local
truth-table result; a two-value set remains uncertain. Independent companion
state and incoming internal tile routes must still be accounted for. No output
is replaced, and no passing companion can override a native failure.

[37534707478](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37534707478)
passes RTL control but stops before RUN because the optional native LUT_out
alias is removed and indexed lookup raises KeyError (BUG37). This is a probe
failure, not new UART evidence. Attribute lookup corrects the diagnostic;
hosted verification of the focused snapshots remains pending.

## Focused result

[37535155011](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37535155011)
verifies the optional-alias fix and reaches the actual UART failure again. At
4423490ns the same-input RTL timer has count15, rst0, loadX, halfX and en0.
The RTL conditional retains the count with unknown load; this cannot prove
the corresponding hardware next state is determined.

Unregistered constant LUT outputs provide smaller diagnostic targets:

| Tile / cell | Local RTL truth table | Binary outputs | Native O |
|---|---|---|---|
| X1Y2 LD | all0 | 0 | X |
| X2Y1 LB | all0 | 0 | X |
| X2Y1 LD | all1 | 1 | X |

These truth tables determine the combinational output regardless of LUT input
values. The next read-only probe traces their actual mapped output cones,
including configuration dependence, before concluding whether a mapping,
configuration binding or simulation correlation explains the discrepancy.
For X2Y3 LD the local index is x001 and all possible completions yield1, but
internal mapped inputs also need accounting. No chip correction is established.

A lightweight static audit of the cached exact-revision PDK ihp_mux2/ihp_mux4
UDP tables checks all27/729 combinations over0/1/X against their possible
binary outputs. Both match. This excludes a simple missing selector rule in
those tables; it does not prove the full mapped logic handles reconvergence
correctly. PDK models remain unchanged.

Acceptance still requires actual native loaded behavior, zero final routing
and physical violations, and timing through the configured fabric. The frozen
G1 physical success does not supply those compact or native proofs.
