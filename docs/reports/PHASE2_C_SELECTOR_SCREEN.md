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


## Fixed-site result and exact congestion diagnosis

Run42128655779's control passes. The edited clock diode remains at its reviewed
site, its supplies and native placement checks pass, and all original/signoff
estimated timing/electrical checks pass. Antennas are0. Overflow improves17→15,
so the screen remains unqualified. No detailed routing or extraction starts.

The next manual `gds-c-select-congestion-readback` is read-only. It loads the exact
saved edited ODB in the immutable stock image, reads actual layer grid capacities
and usage, requires the overflow sum to match15, and reports every exported
route crossing each overloaded edge. Whole artifact ZIP and ODB hashes are
verified before inspection; input bytes must stay unchanged. No PDK setup,
synthesis, placement, routing or timing rerun is needed.7 grid/route regression
cases cover coordinate mapping, H/V edges, invalid values and missing coverage.
This measurement will guide a bounded routing-neighborhood decision rather than
another placement guess. A green readback job is not a green physical screen.

Read-only edge inspection [42131917635](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42131917635) was launched on `28727e44348eaebbfb887314dd4a16872a2d7c5b`; results pending.


## Exact congestion diagnosis and parent-clock experiment

Readback42131917635 succeeds: complete source artifact ZIP digest and ODB hash
verified, input unchanged, saved grid overflow equals live15. All15 overloaded
Metal3 edges are crossed by the changed word0 clock branch; neither edited data
net crosses them. Fourteen lie onY514800 and one onY500400. These native stored
capacity/usage differences identify the branch to repair; they are not a new
STA or closure measurement.

A local-buffer feasibility check found no spare site in the required input-grid
point with all original cells fixed. D-154 instead tests one clock-sink
reassignment to the already existing parent buffer. Runtime checks prove the
new clock is the leaf BUF8 input and old clock its output, with a BUF8 parent;
the pinned PDK cell's combinational identity proof passes. Only the latch GATE
connection changes. Its location, master, data and supply pins remain exact.
Clock latency changes, so all original/signoff timing gates stay mandatory.

This removes the clock diode, retains two data diodes plus wire14386 BUF4, and
reduces estimated added footprint to16.3296µm². Six allowed nets bound rerouting.
89 related regressions, actual PDK identity proof, actionlint and embedded
workflow syntax pass. No native success is predicted; official-flow source/config
reproduction and extracted timing remain open.

Parent-clock experiment [42135330053](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42135330053) was launched on `c3bc97b74c04e95f559455e06b9ef5c39e405065`; native results pending.


## Parent-clock result: retire this variant

[42135330053](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42135330053)
finishes with a passing control and failing edited gate: antenna1, overflow17.
Original-constraint fast/typical/slow hold remains0.0867642/0.312564/0.695068ns;
setup summaries are0 and electrical counts0. These are estimated results, not
positive extracted setup margin. The remaining antenna is _51789_/GATE on the
parent clock. Reassignment did not solve the issue and regresses the legal
antenna0/overflow15 reference42128655779. Retire it; do not launch DRT.

Exact pinned OpenROAD commitdcf36133a369abc8f3c5e5738cd4d82e4903c0e0 lacks
the guide-restoration callback/API present in newer cached source. A possible
next mechanism is inserting a legally placed clock diode already covered by
the original guides before fresh guide initialization. This is unimplemented
and requires explicit native coverage/connectivity plus fresh original-model
capacity/usage validation; saved zero congestion is insufficient. Every existing
strict timing/electrical/antenna/placement gate remains mandatory.


## Covered-clock protection diagnostic (D-155)

The next paired screen tests inserting the passive clock diode before loading
original guides. The site626880,498960 MX was legalized in42122049674; native
placement and supply checks remain mandatory. It retains the original clock
wiring and requires exact original clock route geometry. Normal incremental
routing handles two data diodes and wire14386 BUF4. Same21.7728um2 footprint.

An independent native process loads final ODB/segments through exact pinned
readSegments, which checks route connectivity and every pin's actual-layer
coverage. Require exact44792-net geometry readback and no errors before fresh
STA/antenna audits. endIncremental calls native finishGlobalRouting, which
refreshes saved congestion and prints live demand/overflow. Accept only live
overflow0, all original/signoff timing gates, fast hold>=50ps, electrical0 and
antenna0.89 focused regressions/actionlint/syntax checks pass. No native passing
result, DRT or official-flow reproduction is claimed.


## Covered-clock result: five residual overflow units

[42140616934](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42140616934)
control passes. Edited placement/supply/full inventory checks pass, original clock
route and topology stay exact, and independent native segment/pin validation
passes for44792 routed nets. Original/signoff estimated timing and electrical
checks pass; antenna0. Original fast/typical/slow hold remains
0.0867642/0.312564/0.695068ns. Setup summary0 is not extracted positive margin.

Only two data routes change: _02001_ and lane1 ot26. Live overflow improves15→5,
so the strict screen still fails and DRT remains blocked. Preserve the covered
clock mechanism; inspect actual residual edges before choosing a data repair.
Existing read-only inspection [42142331582](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42142331582)
is bound to exact latest artifact/ODB and expected overflow5. No placement,
routing, timing or capacity change occurs during inspection. No official-flow
or extracted closure claim follows.


## Residual diagnosis and driver-side clear protection

Read-only [42142331582](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42142331582)
succeeds and verifies the exact artifact/ODB, unchanged input and all5 overflow
units. Every overloaded Metal3 horizontal edge atY320400 crosses _02001_;
the lane repair crosses none. This isolates the next changed route to preserve.

The driver-side row317520 gap between wire13979 and _46674_ admits a1.44um
antenna diode at830400,317520 MX. Its transformed A-port lies in the original
driver grid cell831600,320400. Native placement and coverage must prove this
geometric hypothesis. Insert it before guide initialization with the clock
diode; require both original routes exact. Same3 diodes/BUF4, footprint and gates.
93 focused regressions/actionlint/syntax checks pass.

Paired [42144728640](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42144728640)
is running on4273bc1695391eaf55720cb46b4f7ad6942aa8e8. No passing native result
or DRT/extracted/official qualification is claimed. Do not relax the final
zero-overflow gate if the local protection does not reproduce its hypothesis.


## Driver-side result: lower overflow but ineffective Metal3 protection

[42144728640](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42144728640)
control passes; edited placement, supplies, original clock/clear geometry,
independent native coverage and original/signoff estimated timing/electrical
checks pass. Only lane ot26 geometry changes. Live overflow falls5→2, but antenna1
returns at _50780_/D on _02001_. Metal3 CAR remains239.71 against200. The diode
is only connected through the original Metal4 bridge, where the allowed ratio
rises to60292; it cannot protect the receiver at the failing Metal3 stage.
Reject this placement as a complete antenna solution. Best antenna-clean
reference remains42140616934 with5 overflow. No DRT/extraction is authorized by
this failing result.

Read-only [42146325916](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42146325916)
is bound to the exact latest artifact/ODB and overflow2. Next resolve those edges
and receiver-local protection connected by Metal3 or below; do not repeat the
same driver-side diode or trade antenna clearance for congestion clearance.


## Two receiver-side Via1 attachment diagnostic

Inspection42146325916 succeeds and confirms both residual edges cross lane ot26.
The next paired screen retains the original routes and attaches the receiver
side diodes at existing Metal2 points: clear939600,313200 and lane586800,226800.
Only these two Via1 guides may be added. Clear diode returns to proven receiver
site938880,313740 R0; lane diode586080,223020 R0 occupies a reviewed row gap.
Native placement and antenna efficacy remain unproved.

Every original atomic routing-grid edge and its multiplicity must match the
frozen source after removing only the two new vias. This accommodates native
segment splitting at a new branch without permitting a different physical path.
Independent native connectivity/pin coverage and all existing timing, electrical,
antenna and live overflow gates remain mandatory.101 focused regressions and a
full44792-net local attachment audit pass, with actionlint and syntax checks.

[42156980762](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42156980762)
is running onfe672fc0dfbb73c6e195aa4f8bfeca6c7424d8e8. Main hardware/config
and official GDS jobs stay unchanged. This guide ECO is not a source/config
reproduction recipe; no DRT, extracted closure or phase completion is claimed.


## Strict screen passes; detailed routing begins

[42156980762](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42156980762)
succeeds in both arms. Edited original/signoff estimated timing and electrical
checks pass, fast original hold0.0867642ns, antenna0 and live overflow0. Native
placement/supply/inventory checks and independent44792-net pin coverage pass.
The two reviewed Via1 attachments preserve every original planar route edge;
no further route geometry changes occur. Setup summary0 is not positive
extracted timing evidence. This is experimental screen qualification only.

[42158728020](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42158728020)
is running on544ec54ef4253b6196b92ad7ae05c88516c47992. It restores the exact
passing artifact with whole-archive digest/provenance and measured-view hashes,
rechecks fresh original/signoff timing/antenna/native coverage, then runs stock
DetailedRouting without repeating repairs. Require route DRC0, antenna0,
preserved logical connections and passing disconnected-pin checks.66 focused
checks, actionlint and embedded syntax checks pass. No extracted closure,
official GDS or source/config reproduction claim follows from launch.


## Detailed route succeeds; extracted timing measurement launched

[42158728020](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42158728020)
succeeds: fresh preflight gates, completed detailed route DRC0, antenna0 and
logical-cell conservation pass. The stock pin checker reports0 critical and1
noncritical disconnected pin; its full table identifies top-level ena. This is
not a claim of zero total disconnected pins. Whole routed artifact digest and
state/metric/table hashes bind the next measurement to this exact result.

[42252231999](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42252231999)
is running on1299efb737147f19fb6662fe08daf3fd42b41ec6. It restores the exact
route, finalizes/extracts parasitics and measures all fast/slow/typical setup/hold
and electrical reports under unchanged signoff constraints. Require six timing
values, all three electrical reports, fast hold>=50ps, all setup/hold>=0 and
antenna0.60 focused checks/actionlint/syntax pass. No synthesis/rerouting/repair
is repeated. Source/config reproduction, official GDS and Phase2exit remain open.


## Extraction result: setup and one slew connection still fail

[42252231999](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42252231999)
completes extraction but fails strict gates. Slow setup is-2.9278127418ns;
fast/typical setup summaries are0. Extracted fast/typical/slow hold is
0.1797761990/0.4099084521/0.8159451123ns. Antenna, fanout and capacitance checks
pass. Slow has two slew rows on one connection: _48011_/Y(A221OI1) and
wire12345/A(BUF2),2.581115/2.583109ns against2.507400ns. Other corners are
electrically clean.

The actual worst path is unit0 IDLE configuration latch _51861_ through pad13
selection/feedback logic to channel1 pending_drop _50696_/D. Arrival24.242085ns
versus required21.314272ns. Among58 reported output stages, NOR4 _27522_,
NAND3 _27530_ and NOR4 _46365_ contribute1.474222,1.134735 and1.002023ns.
The previous C-selector/bitsync path is not the controlling endpoint now.
Next measure small NOR4 sizing changes against a reproducible fixed-SPEF
baseline and assess equivalent IDLE/pad-feedback source factoring. No repeated
screen/routing run is launched without a measured remedy. Clean DRT remains
valid; extracted closure and official-flow reproduction remain unproved.


## Measured repair limits and shared-launch source experiment

Fixed-SPEF [42254731067](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42254731067)
reproduces baseline and tests six cases. Best NOR4 pair+delay2 improves slow
setup-2.927813→-2.260117ns, retains179.776psfast hold and leaves both slew rows.
These changes alone do not justify another detailed route. All20 reported
worst baseline paths share the IDLE configuration latch.

D-157 replaces that one stored bit per unit with a root-clock enabled flop,
with equivalent write-gated reset and phase visibility.461lean/560full module
equivalence points pass with induction cap6/no blacklist;2080cycle/10400phase
checks pass per variant. Five chip smoke tests pass. Generic cell counts swap
one latch for one enabled flop per unit, no extra bits. Native physical cost
and timing are unmeasured. Reproduction is in verify_idle_ff.py.

[42259881584](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42259881584)
runs this single source change on the exact C-selector physical recipe. A
separate22case RTL suite is running locally with matched2/4 software and actual
offline sigrok decoders; no full-suite pass is claimed yet. The alternate
parallel S/A selector has binary combinational proof, five smoke passes and
~0.20–0.22nsisolated slow-cone improvement, but remains separate and unpromoted.
No actual WNS gain or official closure is claimed from these local studies.


## Two independent source repairs now under physical measurement

The D-157 critical-configuration storage prototype passes all22existing RTL
protocol cases with real offline sigrok checks, plus five chip smoke tests and
461lean/560full module equivalence points. Its exact source is being measured in
[42259881584](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42259881584).
The alternate parallel S/A selector is proved and locally promising but remains
separate/unpromoted.

D-158 fixes the host status-mux structure by padding10-bit records into16-bit
words before indexing. This removes runtime multiply-by-ten/unaligned shifting
without stored bits, host-interface changes or extra cycles. Host/SPI module
proofs902/920points at stated parameters and five chip smoke tests pass. Isolated
NC9 slow6fF mapping improves5017.7988→1520.4672um2 and2035.03→977.29ps; these
are not physical gains. Exact preparation is source/hash guarded and matches
tested RTL. Independent physical source screen
[42262602008](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42262602008)
is running with the identical reference native recipe.

Both screens retain2/4,20ns, fast50ps and every zero-violation/overflow gate;
main hardware/config and official jobs are untouched. No experiment combines
both hardware changes. All local simulators have finished. Further physical
repair decisions depend on these source-screen measurements. Current actual
extracted setup remains-2.9278127418ns; the-2.260117nsfixed-RC sensitivity case
is unqualified and is not substituted for measured physical timing.
