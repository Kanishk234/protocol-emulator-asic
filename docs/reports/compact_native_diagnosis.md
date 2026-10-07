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

## Bounded mapped-logic proof

At17cc085 a cloud-only diagnostic checks the three all0/all1 cases above using
the actual mapped tile netlist and pinned functional Liberty. It captures real
native configuration-Q values at the observation instant. Sequential cells are
cut to arbitrary symbolic outputs; only configuration Q is constrained. Tile
inputs and user state remain free. The first SAT query must find a feasible
assignment, then a second query checks the constant-output property for every
assignment. Each target has a60-second process cap; unsupported cells are not
ignored. Script-generation and result-parser checks pass; actual hosted proof
execution is pending.

This is a binary combinational property under one captured configuration. It
does not prove sequential initialization, native four-state behavior, complete
fabric equivalence, SDF behavior or timing. Native simulation failures remain
failures regardless of proof results. The workflow retains constraints,
prepared connectivity, scripts and logs as artifacts, not committed raw output.
The method follows the official Yosys
[cutpoint](https://yosyshq.readthedocs.io/projects/yosys/en/v0.53/cmd/cutpoint.html)
and [SAT](https://yosyshq.readthedocs.io/projects/yosys/en/v0.49/cmd/sat.html)
command contracts; those references are methodology, not WARP proof evidence.

37536118708 does not reach SAT because an unused incomplete Liberty cell is
rejected (BUG38). Functional import now skips such entries while hierarchy-check
requires every instantiated cell.37545251399 passes import but loses captured
aliases during cleanup.37545630704 preserves them and reaches feasible SAT
counterexamples; however529 actual configuration latches have only505 named
ConfigMem.Q aliases. The24 missing outputs leave selectors free, so these
counterexamples do not establish a hardware fault (BUG39). The earlier8707
matching-bit audit covers the named-storage subset. The next37546145073
captures every actual latch Q and retains those proof wires; result pending.

## Verified local property

[37546145073](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37546145073)
captures all529 actual latch Q values per target and proves all three constant
outputs listed above. Both feasibility and proof queries succeed with arbitrary
binary tile inputs and user state. The ordinary actual native UART still fails.
This establishes false unknowns in these three combinational cones under that
configuration, not an explanation of every UART unknown or sequential boot.

D-047 screens a standalone five-mux4 LUT implementation with actual pinned
cell models, full binary equivalence against FABulous LUTK, and independent
partial-input truth-table tests. No chip/generator/model correction has been
installed. Area, routing, timing and real loaded integration remain open.

[37546784325](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37546784325)
passes binary equivalence against pinned LUTK for every16-bit truth table and
4-bit input, plus2916 partial-input simulations with actual pinned PDK models.
The follow-up37552796495 regenerates scratch native LUT tile netlists and tests
SPI-loaded UART against the unchanged RTL control. Copied macro physical views
do not qualify those new netlists; physical/timing acceptance is
still pending. Upstream change lives in patches/fabulous_lut_mux_tree.patch and
is applied only to a separate staged source.

[37546984612](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37546984612)
checks all9164 actual configuration latches by their real frame-data/strobe
wiring. All are known and image-matching before RUN and immediately before
timer corruption. Native UART still fails. This closes the previous name-subset
coverage gap without claiming a functional correction.

Acceptance still requires actual native loaded behavior, zero final routing
and physical violations, and timing through the configured fabric. The frozen
G1 physical success does not supply those compact or native proofs.

## Matched resynthesis results (October 6)

[37552796495](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37552796495)
and tracked-patch follow-up
[37553037381](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37553037381)
pass the unchanged RTL control and actual regenerated native UART test.
The test loads 842 real words through SPI, checks UART TX/RX and STOP parking,
and rejects failures/errors/skips in its acceptance XML. The existing D-023
routing harness remains; this is zero-delay simulation, not SDF or hardware.

Crucially, matched original-LUT control
[37553190074](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37553190074)
also passes. Its downloaded manifest confirms original_control; simulation log
reports TESTS=1 PASS=1 FAIL=0 SKIP=0 and actual SPI loading. Both experiments
resynthesize the same five LUT tile types with the same Yosys/latch mapping/ABC
flow. Therefore the five-mux primitive is not established as necessary for this
UART correction. Differences from the original hardened synthesis flow remain
under investigation; a passing resynthesis does not prove the old netlists
incorrect in binary hardware operation.

Next checks retain all regenerated tile netlists and acceptance XML explicitly,
and run UART after the real USER_RESET command. Any new netlist needs matching
hardened physical views, binary equivalence/resource audits and configured-fabric
timing before promotion. The copied old LEF/GDS/SPEF cannot qualify it.

The original tile config uses SYNTH_STRATEGY=AREA 2, whereas this scratch helper
uses Yosys's default abc -liberty script. This is one candidate difference, not
an isolated cause. LibreLane documents that its strategies select different ABC
scripts and that the best strategy must be measured:
[official synthesis configuration](https://librelane.readthedocs.io/en/latest/reference/step_config_vars.html).
