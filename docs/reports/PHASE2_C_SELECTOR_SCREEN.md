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


Audit42110354960 stopped after route export because the diagnostic looked up an
unescaped hierarchical net name. No completed clock/path audit is available from
that run. The fix resolves only a unique exact logical/escaped spelling and
passes actual database names to the antenna checker.29 Tcl/checkpoint tests pass,
including escaped names and ambiguity rejection. Corrected audit
[42116068868](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42116068868)
was launched on `3296e751f35c6886ad6b0f048932cc91e9608a5c`.


## Successful audit and bounded receiver experiment

Corrected audit42116068868 passed in6m17s. Its repeated signoff-SDC corner
measurements, original physical views and fresh ODB netlist readback reproduce
the source. Antenna count remains4. The tracked live-configuration→channel0
pending-drop pair has estimated slow slack+4.796553ns. This is one selected path,
not whole-design or extracted setup evidence. The affected latch's reported
slow outgoing paths have minimum slack+5.325843ns; its reported fast incoming
hold path has slack+10.194736ns. Clock protection still needs actual remeasurement.

D-153 prepares paired native reopening/control and edited jobs in the manual
`gds-c-select-local-repair` workflow. The edited job adds three local passive
diodes and upsizes wire14386 fromBUF2 toBUF4. All unrelated original placements,
orientations, masters and connections must remain identical; movement is bounded
to20µm per axis, with only five allowed nets changing route geometry. Fresh
NL/PNL exports follow the actual edited database. Estimated added cell footprint
is21.7728µm²; this does not predict routing or clock effects.

Both original and signoff-SDC all-corner audits are required. Original fast
hold reserve≥50ps, electrical0, antenna0 and final live overflow0 remain fixed.
The no-edit arm must reproduce the frozen source; the edited arm must pass
all gates.61 local audit/library/route/checkpoint regressions and workflow syntax
checks pass. Native execution is pending. This diagnostic does not reproduce
the repair through permitted main source/config inputs or qualify official GDS.

Paired diagnostic [42119036887](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42119036887) was launched on `d1207c571587d1b6269ce4669a2067bd5f918da3`; control and edited results are pending.


## First receiver test: invalid edited placement, corrected before retry

Run42119036887's control passes exact geometry and timing reproduction. Its
edited arm reports zero antennas/electrical counts, unchanged reported worst
slacks and17 overflow. Those edited results cannot qualify the design: native
STA-0564 shows the placement invocation had an extra positional argument, and
DPL-0033 identifies three overlapping diodes. The Python Tcl-eval boundary did
not throw, and our earlier gate missed these errors. This is a tool-launcher
bug in our code, not valid evidence of a physically legal antenna solution.

The corrected command passes the displacement pair as one Tcl list. A checked
Tcl wrapper now requires an explicit success marker for placement, placement
checks and Verilog exports. Pre/post-router placement checks and native-error
log rejection are mandatory.71 relevant checks pass, including the malformed
command and swallowed-error regressions. The exact upstream command contract
was checked at OpenROAD commitdcf36133a369abc8f3c5e5738cd4d82e4903c0e0
(`src/dpl/src/Opendp.tcl`). Retest the same plan from original source42078913664;
never resume the invalid edited checkpoint. No acceptance threshold changes.

Corrected paired run [42122049674](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42122049674) was launched on `d54b84d9dba1904702102588ecd629e7d82f81a3`; results pending.


## Legal repair result and clock-corridor placement test

Corrected run42122049674's control passes. The edited arm passes native
legalization and pre/post-router placement checks with no native ERROR entries.
All estimated timing/electrical checks pass, antennas are0, and unrelated
original cells/routes are preserved. It still fails live global overflow:
**17 horizontal Metal3 overflow units**. This is a genuine remaining routing
failure, unlike the earlier invalid-placement run.

Only three diode-connected nets change routes. The clock reroute adds34 Metal3
horizontal grid edges; the two data nets add9. Its new long trunk runs288µm at
Y500400DBU, crossing a heavily used row. The previous clock route uses a detour
and has an existing right-side corridor atY514800. These observations implicate
the clock reroute without proving every overloaded edge belongs to it.

The next bounded placement test seeds only the clock diode15.12µm above its
anchor and requires final Y displacement13..17µm, keeping the original20µm
per-axis limit. It aims to extend that upper corridor. Same diodes/buffer,
footprint, source, timing constraints, native routing and all acceptance gates.
Placement metadata is exported for interpretation.76 related regressions pass.
The test is unmeasured and does not guarantee zero overflow or official closure.

Clock-corridor placement test [42125394009](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42125394009) was launched on `8434831bc07f7c47916089c3afb1078974fdaa1e`; results pending.


## Clock seed rejected; select an explicit legal gap

Run42125394009's control passes, but the edited arm stops before routing when
legalization moves the clock diode outside its reviewed seed corridor. It
provides no new timing or congestion result. The seed row514080 has no three-site
gap within the permitted X range. The adjacent row510300 has an exact1.44µm gap
atX643680 between hold7746 and _33545_, within the original20µm displacement
bound. DEF/LEF inspection confirms grid alignment and no stdcell overlap; the
SRAM macro is outside this region. Native placement checks remain authoritative.

The revised experiment locks only the added clock diode at that reviewed site,
retains the two other diode placements and buffer sizing, and adds explicit
anchor-matched diode VDD/VSS connections (missing in the earlier insertion).
Wrong supply connections and movement away from the exact site are rejected.
Pin locations and final placements are exported.78 related checks pass; no
congestion/timing success is predicted. All original acceptance gates stay fixed.

Explicit-site test [42128655779](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42128655779) was launched on `a277802e7b698d7575fe55d872f4e750c5e0ec56`; native results pending.
