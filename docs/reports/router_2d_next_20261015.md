# Native 2D negotiation: next bounded observation

The next experiment is an unchanged-control trajectory observation, not a new seed, placement, capacity adjustment or router binary. [Scalar run38778082059](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38778082059), exact revision6370e1f5ae71a2d768fbe6cb87a062b2c1d21134, retains native133 and both original segment hashes. Its cached2D overflow is already133; assigned3D remains133. Native conditional3D maze repair is skipped because cached2D overflow is nonzero. See `route_trace_analysis_20261015.md` for authenticated source/report/segment hashes and static cut evidence.

## What the actual log already establishes

The unchanged source's single `global_route -congestion_iterations 50` call prints **243 extra-iteration starts across five epochs**, not50 total iterations. Epoch lengths are49,49,49,46,50. Between them it emits native GRT-0273 warnings disabling congested NDR on, in order, `clk`, `delaynet_3_clk`, `clknet_0_clk_regs`, and `delaynet_0_clk`. These are observations of the original router's own behavior, not new policy changes proposed here. All final source/policy/segment guards in38778082059 pass.

Therefore another nominal100-iteration run cannot be interpreted as simply twice the original runtime or one continuous solver trajectory. The original log lacks per-iteration overflow samples; we cannot tell whether the final epoch is still improving at its50-start limit.

## Checkpoint and loop source findings

Pinned primary sources: [FastRoute.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/FastRoute.cpp), [utility.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/utility.cpp).

`copyRS()` stores route trees in `sttrees_bk_`; `copyBR()` restores them only when that vector is nonempty, updating2D usage. The only core calls saving that checkpoint require `i>140` or `i>80 && past_cong<20`. No actual epoch passes50, so this baseline never reaches either save condition. The end-of-run `copyBR()` call therefore cannot restore a saved early tree in this case. A printed minimum-overflow round is not evidence that its tree was saved.

`removeLoops()` follows restoration and removes repeated grid positions while decrementing route usage; it is not another global negotiation pass. The existing GUI2D display precedes both steps, and calls a renderer that pauses. Stock Tcl provides no established selected-net intermediate-tree dump here.

The core changes native history policy after counter50 and again after70, and may terminate early after excessive overflow increases. It increments `i` before printing the `Overflow Iteration` debug summary and before its NDR-reset test. Thus a start49 can be followed by a summary counter50 and an NDR reset; treating those labels as fifty completed starts would be wrong.

## Prepared observer and decision rule

`test_internal/cloud_route_trace.py` now adds existing `set_debug_level GRT congestionIterations 1` alongside its existing scalar hook in the attributed runtime Tcl copy. No source binary, frozen hardware, routing policy, capacities, clock/timing margins or acceptance changes. Exactly one native logged command is required. Original133, marker SHA8e2f5c50…, full segment SHAaee9b65f… and selected-target SHA f00a6206… remain mandatory, along with all original source/protected-policy checks.

The parser retains native per-epoch iteration starts, post-increment summary counters, overflow, increase count/limit, NDR-reset names and optional cached minimum/round. It rejects contradictory/repeated counters; absent or incomplete exact native samples produce `parsed:false`, preserve the raw log, and make no trajectory claim. This is scalar solver history, not intermediate per-net topology. Local focused tests:14PASS/2SKIP (unchanged preexisting Tcl tests lack local interpreter). No local EDA was run. Hosted execution remains pending.

After a matching observer completes, inspect the final epoch's last10 overflow samples and best-round history. If overflow continues falling into the50-start boundary, propose one bounded native budget100 versus50 comparison, retaining capacities/margins/source and all final acceptance guards; this reaches documented native history regimes rather than inventing a new algorithm. If the trajectory plateaus, oscillates or repeatedly worsens, do not spend on a blind budget increase: use the measured throat cut and cached-history behavior to select a narrower topology/negotiation diagnostic. If there are early-stop or NDR resets, report them explicitly rather than inferring budget exhaustion from the command argument.

A candidate below133 is only experimental progress; only zero native overflow can advance to detailed routing, extraction, all original electrical/timing checks and complete physical/function acceptance. Exact-control mismatch rejects the observation. No workflow was dispatched and no physical intervention is selected by this report.

## Actual trajectory and selected next experiment

Run38780941495 succeeds as a diagnostic on8e4c117537401528814ff25fadd64de697654db5.
Original source/133/report/full-segment/target hashes all match. Independent
inspection finds the exact243 starts, epoch lengths49/49/49/46/50 and four
native NDR resets described above. Per-epoch minima are140,138,119,121,110.
The last minimum110 occurs at start14. Final last-ten samples are
138,139,145,135,153,145,149,134,155,133. This is oscillation, not a declining
tail. Do not spend on the previously conditional100-budget increase.
Result JSON SHA256:
`8dead5a818dca11fa619a1601f401b94681d71bd5ffe6e6acfeddb0689fd7a79`.

D097 instead prepares one native early-stop pair50versus15 on the same
authenticated physical views, keeping capacities/margins and all original
producer checks. A fresh50control must reproduce exact133 and route hashes.
Stopping earlier might retain a lower-congestion solution, but changes when
native NDR restarts occur; it does not recover the observed round14 tree by
definition. A worse/equal candidate is rejected without a budget sweep.
The paired workflow is a diagnostic collector, so success alone is not a
chip result. Candidate native return/table/segments and selected policy are
retained separately; nonzero overflow blocks detailed routing and acceptance.
