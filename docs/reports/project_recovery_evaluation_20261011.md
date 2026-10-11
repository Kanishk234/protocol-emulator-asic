# WARP evaluation and execution plan — 2026-10-11

The frozen G1 is the documented submission fallback. The compact successor is an experimental collection of checkpoints, not yet one accepted chip. The goal is to assemble a reproducible successor that passes physical, electrical, loaded-function and timing gates together. More experiments alone are not completion.

## What currently works

| Track | Evidence | What it proves / limitation |
|---|---|---|
| Frozen G1 | 36383587262; Phase4 36451108163 | Recorded Tiny Tapeout GDS/precheck and gate-level tests pass. Fabric uses D-023 RTL modelling; these runs do not prove all native macro internals or every bitstream's timing. |
| Compiler and examples | 36451328356/36451328364; seed sweep38101717810 | Required design-set examples compile/run; reproducibility37690896748 passes fresh README setup. No new silicon/rate claim. |
| Stronger-driver compact physical layout | 37708459393, official precheck37960021923 | Native routing/full geometry/shell LVS and all nine official checks pass on that layout. Fanout33 remains; macros abstract in shell timing. |
| Ten-buffer shell candidate | 38101405271 | All six estimated electrical/setup/hold cases pass, but native routing subsequently fails. This is not the physical layout above. |
| Reset net683 relocation | 38163199430 / 38163542037 | Actual native paired overflow146→136 with unchanged policy; both reject congestion. |
| Reset net694 relocation | 38165505343 | Legal one-cell move, exact all-other placements/connectivity, all six estimated screens pass. Paired routing38165931145 rejects this candidate:146→154 native overflow, same50iteration policy. It starts independently from146 baseline, not136 net683 candidate. |
| Delayed actual C2 tile | 38114298036 / 38163199372 / 38164099529 | Physical gates0; real-loaded UART/reset passes; examined conditional internal setup/hold pass at two positions/three libraries with own nominal SPEF. Source virtual-clock setup fails. Other tiles, loading, I/O and intertile timing remain open. |
| C2 annotation follow-up | Authenticated retained graph38163199372 and six reports38164099529 | Four unannotated drivers have no cell loads/output aliases in this exact tile graph; does not resolve other unconstrained endpoints. |

## Why closure is taking so long

1. **The passing results belong to different builds.** The clean routed shell still has fanout failures; fixing fanout perturbs placement/routing. The actual passing delayed C2 has not replaced all tile types in a fully verified chip. A collection of green diagnostics cannot be combined by assertion.
2. **The shell is locally routing-dense.** Earlier ground-up audit finds dense west-shell rows and pin-access conflicts (compact_route_root_causes.md). The current reset audit finds445 single-load ties,116 separated by at least30µm in row coordinates,70 associated with congestion markers;68 have no improving conservative interior slot within20µm of their receiver rows. These are placement proxies, not measured routed wirelength or proof that ties cause all overflow.
3. **More router iterations and indiscriminate spacing have not solved it.** Same-policy five-cell spacing leaves146 overflow; broader legalization violates displacement/power-phase guards. Repeating those runs is unlikely to help without a different physical hypothesis.
4. **Functional and timing macro assumptions matter.** A configuration can load correctly while its native mux mapping misbehaves. Shell timing with blackboxed tiles does not time programmed user logic. Conditional C2 timing intentionally leaves loading/intertile/I/O endpoints uncovered.
5. **Infrastructure has consumed iterations.** Expired three-day artifacts, relative Docker paths and evidence serialization/import bugs produced failures before meaningful checks. These are recorded separately from actual design failures (BUG69–71); fresh control generation and manual historical replay reduce them.

## Critical path and independent work

| Priority | Action | Completion gate | Dependency |
|---|---|---|---|
| P0 | Compare net694 actual GRT to exact146 baseline | Retain both native outcomes/marker maps; reject worsening or unchanged candidate | Completed38165931145; reject worsened154 candidate. |
| P0 | Export native fragmented rows/blockages and quantify legal local whitespace | Authenticated read-only DEF/census, immutable source; identify sites with actual row boundaries and macro/blockage subtraction | New cloud_reset_row_inventory workflow |
| P0 | Reserve targeted receiver-local tie space or redistribute a small affected region | One copied-checkpoint policy; native legality/power alignment, unchanged masters/connections/macros/pins and six electrical screens | Actual rows, then measured placement policy decision |
| P0 | Route the selected fanout-clean shell | Zero native overflow then detailed-route/antenna/critical-disconnect gates | Legal/electrically clean placement candidate |
| P1 | Qualify every fabric tile type using its own mapped netlist/physical views | Exact interfaces, genuine configuration, physical checks and loaded compiled designs on matched native views | C2 lead exists; other types need equivalent evidence |
| P1 | Specify complete timing modes from the hardware contract | RUN and configuration-loading clocks, real shell/boundary paths, constraints coverage and RC/PVT accounting; no undocumented exclusions | Can audit existing modes now; actual extracted integration later |
| P1 | Integrate a single matched complete chip | Same-build full DRC/LVS/antenna, official TT precheck, shell electrical/setup/hold and native loaded tests; configured relevant paths timed | Shell route plus matched tiles |
| P1 | Make that result reproducible in the unmodified official TT job | Clean input provenance, complete GDS/precheck/gl_test and all required workflows green on efpga | Accepted integrated candidate; no experimental waiver |
| P2 | Improve breadth through software/examples on frozen hardware | Compiled resource fit, real-interface tests, scope/rates/limits documented | Independent of compact routing; existing UART/SPI/I2C/showcase/capture work retained |
| P2 | Finish evidence audit | Every numerical public claim traced to its exact run/build/mode; equal-area claims retain comparison provenance | Independent except final successor numbers |

## Alternatives if local reset relocation is insufficient

- Use actual free rows to create a small receiver neighborhood, allowing controlled standard-cell movement rather than forcing ties into occupied sites. Keep fixed macros/pins and actual power phase legal. Measure routing demand; do not select by cell count alone.
- Move tie localization earlier in copied shell placement, before rows are packed. OpenROAD's repair_tie_fanout places a copy near each load, but current nets are already single-load: blindly cloning again is not a demonstrated fix. Inspect our pinned implementation and placement sequence first.
- Revisit the shell/fabric channel allocation or a less aggressive compact footprint if local density cannot support legal pin escape. This changes geometry/cost and needs its own decision and same-build qualification; no claim of equal-area superiority follows.
- Preserve frozen G1 and ship compiler, loader, verification and documented protocol improvements there if the successor fails. These improvements are not dependent on a compact floorplan. Architecture changes remain behind the freeze/phase rules.

OpenROAD primary references: [placement padding and legality](https://openroad.readthedocs.io/en/latest/main/src/dpl/README.html), [tie-fanout repair](https://github.com/The-OpenROAD-Project/OpenROAD/blob/master/src/rsz/README.md). Current online documentation may describe newer options; execute only commands supported by our pinned image.

## Working policy

Use cloud runners for heavy EDA. Inspect native results, not only workflow conclusions. Each experiment changes one physical hypothesis and retains exact input hashes. Promote only measured improvements; do not bypass congestion, power-phase, timing or foundry checks. Keep a single current acceptance matrix so newer results do not silently inherit older passes. No phase completion, universal-protocol support, USB/Ethernet support or silicon claim is established here.

Measured follow-up: paired38165931145 result SHA700f317f91b7a43719f63d063bf1af208cc11729faee9129b928c4ab38f44664; native baseline146, net694154. Both native routes reject congestion. Candidate marker SHA209a8c2cce5a77150fc0286fe4f5a87620c6baf0a5c98485c21c02a4af8c93ad. The shorter placement proxy failed as a routing predictor; do not combine or promote this move. Actual row inventory38166250744 is executing independently.
