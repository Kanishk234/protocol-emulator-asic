# C-selector source experiment

The extracted full-design result from run **42069613808** fails slow setup at
**−2.66890162 ns**. Hold, electrical and antenna checks pass. The worst reported
path crosses live unit configuration, output-pad feedback, C-pin selection and
fabric consumption/drop logic. Improving only the final counter is too narrow.

The next source experiment removes the redundant index clamp on C and computes
`sel = !c_on || (c_pad == c_active)` directly. A/B inputs, registers, cycle
semantics, live configuration behavior and the architectural contract are
unchanged. Unattached C indices still produce `c_in=c_active` and `sel=1`.

## Local evidence

`spikes/phase2_stock_flow/pin_input_decode/c_select_candidate.json` binds the
reference, candidate and patch. The comparison scripts prove combinational
equivalence for arbitrary binary inputs, including all 32 C indices. The delay
register block is unchanged. Verilog-2005 compilation passes. Five full-chip RTL smoke tests pass on an
isolated full source preparation (SRAM, lane/fabric forwarding, pin-unit UART,
routines and UART loopback); this is not the full protocol suite. Source binding
and physical-profile regressions pass 58 tests; actionlint and embedded Python
syntax checks pass.

Pinned IHP Liberty mapping, BUF2 input driver, equal loads on C/selection outputs:

| Slow output load | Reference delay | Candidate delay | Reference area | Candidate area |
|---|---:|---:|---:|---:|
| 6 fF | 1577.58 ps | 1107.67 ps | 435.4182 µm² | 422.7174 µm² |
| 26.7 fF | 1768.30 ps | 1254.77 ps | 464.4486 µm² | 437.2326 µm² |
| 50 fF | 1833.40 ps | 1284.40 ps | 464.4486 µm² | 446.3046 µm² |

These are isolated longest-cone ABC estimates, with no extracted wiring. They
are not specific measurements of the failing pad-to-selection arc and cannot
be added to routed WNS. The current −2.669 ns deficit remains unresolved.
The comparison receipt also records alternative decode/banked forms and the
rejected pad-owner rewrite, whose small delay gain costs area.

## Full-design screen preparation

The separate diagnostic workflow `gds-stock-official-baseline-screen` has a new
manual profile, `rtl_shared_minbuf2_cselect`. It prepares the same full
2-lane/4-unit source and physical recipe as reference **41569397169**, then
applies only the bound C-selector patch. Source inventory checks reject any
other source change. The physical configuration hash is unchanged.

The stock Classic sequence, existing screening gates and three-corner checks
remain intact. An additional read-only estimated-routing audit uses the exact
unchanged `src/signoff.sdc`, checking setup/hold, 50 ps fast hold reserve and
zero electrical counts. This distinguishes constraint differences from later
extracted RC effects. Antenna and final-source overflow checks still come from
the existing qualification gate. No detailed routing starts in this workflow.

This profile was published and physically screened in run42078913664. Main
hardware/config and the official `gds.yaml` jobs are unchanged. The diagnostic
recipe's extra physical settings and the earlier checkpoint ECO are not a
qualified clean official-flow implementation. A passing screen still requires
detailed routing, extraction, final netlist protocol replay and unchanged
official GDS/precheck qualification before Phase 2 can close.


## Result: run 42078913664

The stock screen completed in 2 h 42 min and failed only its antenna gate.
Both estimated timing audits passed, with setup WS0 in all corners; this is
not evidence of positive extracted setup headroom. Original-constraint hold
was fast/typical/slow **0.0867642/0.312564/0.695068 ns**. Under unchanged signoff
constraints it was **0.236764/0.462564/0.845068 ns**. All electrical counts and
final global-routing overflow were zero. No detailed routing was launched.

Final physical size was 44837 cells /684795 µm² versus reference45099/688086.
The four remaining antenna failures are new targets: `_50780_/D`, `hold11285/A`,
`_51789_/GATE` and `wire14386/A`. The latch clock-pin failure needs explicit
clock-loading/skew review. The prior source's targeted repair cannot be reused.
Raw corner metrics, antenna identities and final NL hash were independently
checked from selected artifact entries. See the bound result receipt in
`spikes/phase2_stock_flow/c_select_screen_result_42078913664.json`.

The next step is a receiver/geometry-specific repair assessment with all gates
fixed. The previous extracted −2.669 ns setup result remains the latest actual
extracted measurement; the new source's extracted timing is unknown.


## Next diagnostic: bound geometry and clock readback

The manual `gds-c-select-geometry-audit` restores the exact failed screen and
checks 43 bound files before using it. Eight downloaded bound files have been
independently matched locally. Source and physical-view hashes come from the
source run's receipts; the full ODB/DEF contents were not separately downloaded
locally. CI must match every bound file before loading the database. The
artifact's published ZIP digest is bound but has not been independently hashed
locally. Pinned macro/info expectations are reused and rechecked on restore.

The audit runs no repair or routing. It exports route segments, four targeted
antenna reports and receiver/driver placement/orientation information. It also
reports paths around the affected latch clock and tracks the earlier failing
configuration-to-fabric-drop pair by functional net names rather than stale
cell numbers. The signoff-SDC corner results must reproduce the source within
1e-6 ns; electrical and antenna counts must reproduce. A successful diagnostic
means the readback is reliable; the design still has four antenna failures.

This measurement is needed before selecting a clock-load-sensitive repair.
Native receiver protection remains a diagnostic until a permitted source/config
recipe reproduces the result under unchanged official GDS jobs.

Audit [42110354960](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42110354960) was launched on commit `7907fa47464e933210847dd3d6c510e0d49ac255`; results are pending.


Pinned LEF inspection rejects DFRBPQ1→2 as an antenna fix: both D pins have
0.1092 µm² gate area. BUF2→4 grows A gate area from0.2132 to0.3146 µm², giving
a first-order ratio estimate226.65→153.60 if geometry stayed fixed. Actual
upstream loading and rerouting still require measurement. The delay and latch
clock receivers have no larger equivalent input cell. See
`c_select_receiver_feasibility.json` for the pinned geometry receipt.
