# Review-only targeted unchanged-net routing experiment

**Current D100 correction awaits native qualification.** The original patch
compiled and executed, but its chip trial was rejected for changed capacity
accounting; the measured outcome and correction are recorded below. The accompanying
`patches/openroad_force_reroute.patch` is a concrete review artifact against
OpenROAD `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`. It is not an accepted
router change or a claim that the compact successor routes. No upstream tree,
frozen hardware, PDK geometry or routing capacity policy was changed.

## Why this experiment

Exact121 static analysis finds no unused perimeter path to the four selected
macro portals under current demand. Individually releasing either southern
net does not open the cut; releasing both `cell_pad[31]` and `cell_val[30]`
does in an optimistic free-via graph. This supports testing joint negotiated
repair. It does not prove simultaneous routability or legal physical access.
D098 singleton/pair diagnostics must be interpreted before commissioning a
custom build; a demonstrated isolated access defect changes this hypothesis.

Stock incremental Tcl attaches database callbacks, but unchanged nets fail
`pinPositionsChanged` in `GlobalRouter::updateDirtyNets`; simply marking them
dirty cannot invoke repair. Selected-net global routing drops the other nets
and is diagnostic only. The proposed interface instead preserves complete
routes and reuses the existing incremental congestion expansion mechanism.

Pinned primary sources:
[implementation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp),
[header](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/include/grt/GlobalRouter.h),
[SWIG](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.i),
[Net methods](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/Net.h).
Upstream files retain BSD-3-Clause headers. Retain upstream LICENSE and
attribution in any source/build artifact; never patch installed upstream in place.

## Proposed behavior

The C++ method `forceRerouteNets` accepts one or two exact mapped dbNet handles.
The deliberately narrow SWIG interface `grt::force_reroute_pair first second`
accepts two handles, avoiding Tcl glob interpretation of bus names. Resolve
both by scanning actual database objects and requiring exactly one normalized
name match (BUG95); do not pass unescaped display names to `findNet`.
Do not wrap this in a second start/end incremental pair: the method owns that
lifecycle. An ordinary GRT-0116 occurs in `finishGlobalRouting` after the full
route map has been assigned, so same-process continuation has a concrete
source basis. Reloading an ODB is not equivalent to preserving that state.

Before mutation it rejects an active callback, preexisting dirty nets,
uninitialized/empty routing state, CUGR, congestion acceptance, detailed wires,
null/duplicate/unmapped/foreign-block/special/supply/clock/local/merged nets,
less-than-two-pin nets and absent/empty selected routes. Clock recognition
checks both database signal type and the router's `isClockNet`. The rejected
merged-net case avoids silently overriding native merged-route coverage rules.

Only explicitly selected unchanged nets bypass the pin-position guard. All
other dirty-net logic retains its normal behavior. The existing incremental
engine clears the selected routes, initializes their routing resources,
reroutes, and merges replacements into the complete route map. If congestion
persists, it can expand to actual congestion competitors. Forced mode allows
at most four expansion reroutes after the initial selected reroute. It never
enters the existing `detailedPlacement` fallback, so it requests no placement
or connectivity modification. Existing per-run congestion budgets still apply;
a separate hosted wall-clock cap is mandatory. Four expansions are a resource
bound, not a claim that four are sufficient.

Both success and error paths detach/delete database callbacks and restore
incremental mode, critical-net percentage and congestion-report step. The
normal end path still invokes `finishGlobalRouting(true)` with congestion
acceptance disabled. An error is **not transactional**: partial routes or
FastRoute allocations may already have changed. Discard the process and its
candidate after any error; cleanup does not permit retrying damaged state.
A dedicated runner must retain exception/error details and collected diagnostics.

When forced mode is unused, the selected set is empty, the new mode boolean
is false, the original dirty-net guard remains equivalent, the original
30-expansion behavior and its placement fallback remain enabled. This is a
source-level intent; default-route equivalence still requires actual execution.

## Required build and regression gates

1. Review the decision and this patch before building. Pin the complete
   upstream commit/submodules, compiler and dependency/build recipe, source
   hashes, patch hash and output binary hash. Preserve the original stock
   executable and pinned container as the authenticated control. A newer label
   or merely successful compilation does not establish comparability.
2. Build against the actual pinned headers and SWIG/OpenSTA/OpenDB versions.
   No C++ compiler, linker or SWIG check has yet run. Verify overload conversion,
   exception propagation and Tcl dbNet handle types. Add an actual minimal
   regression in the upstream-style routing test harness before chip use.
3. Test no-op/default routing against stock on a tiny known case and the exact
   full121 checkpoint: original sources, capacities, native failure, full
   segment hash `19b14132c36cfa3e863edc34d0f23e7783694da80f586c438833783337a1da2c`
   and native overflow121 must match with force mode disabled. A mismatch
   rejects causal attribution rather than being interpreted as improvement.
4. Test the explicit method on a simple unchanged two-net contention case.
   Prove both selected nets are really rerouted, all unmodified complete routes
   survive, and stale edge usage is not double-subtracted. Reject every invalid
   input class above, and inject routing failure to verify callback cleanup.
5. Test four-expansion exhaustion and instrument actual reroute counts; require
   that the placement fallback never runs in forced mode. Verify placement,
   masters, connectivity, boundary pins, macro geometry/OBS and capacities before
   and after. No setup failure, timeout or incomplete grid is a route rejection
   proving the hypothesis false; retain it as an experiment error.
6. Only then compare the southern pair on the authenticated complete121 state
   in a bounded hosted run. Retain all changed nets, guides, segments and native
   grid. Existing native expansion may include clock/NDR nets even though seed
   nets are nonclock: retain that census and every native soft-NDR change.
   Check actual capacity arrays and original per-net policy rather than assuming
   incremental initialization leaves them identical. Newly introduced confounds
   block an unchanged-policy claim.
7. Require zero native overflow, complete full-chip guide/terminal coverage,
   unchanged net census and all original physical/electrical/timing guards.
   Detailed routing, antenna, DRC/LVS, extraction, configured timing and real
   loaded-bitstream tests remain separate downstream gates on the same layout.
   Lower nonzero overflow is retained experimental progress, never acceptance.

## Checks actually performed

Read-only source review confirmed the referenced Net methods and existing
incremental routing calls. `patch --dry-run -p1` against copies of the three
exact fetched upstream files succeeds. This verifies patch applicability only.
No compiler, SWIG generation, routing regression, custom tool build or EDA run
was performed. No measured benefit is claimed.

Input SHA256:

- GlobalRouter.h: `6ca244c7503f8d13eafc7999edb5f9b09e9072620f67504107964a4284537e7b`
- GlobalRouter.cpp: `71befc6541b5d2b0d22ec021e8c7f2d3edcd2c0dcf4575b0fb28ad21f5e5af83`
- GlobalRouter.i: `dcb136715e9e15a8f2c577e2dc621cf0a25a0640d210b059669e7ccc975681d1`
- Proposed patch: `91ed3c40bb8d498890f65f18e8337b63407a9276c76b3177f7f01263c57914c6`

## D098 actual result and build qualification

Corrected38827410988 at647a536 reproduces exact121 full control and zero
overflow/return0 for pad31, val30 and the pair (actual routed census1/1/2).
All endpoints match the full control. Six encoded Metal3 capacity entries
decrease; none increases, and none lies on the successful reduced paths.
Original total resource tables still differ, so these are not identical-array
full-chip comparisons. They establish native coarse access in reduced cases,
not detailed pin legality or full-chip feasibility. ResultSHA
b87a603f98e2cb0ea245d286b876b6be14acf4ad4b31f9a7e41e5dc9141fd188.

This evidence qualifies a build/interface experiment under D099. The manual
`router_force_build` workflow uses the existing FABulous7999e5a toolchain lock
(SHAaaef0ac1bac971f54fe44565fa12284e18dc88718d153a2f92201e957070084f);
read-only Nix evaluation independently confirms its OpenROAD source is exactly
dcf36133a369abc8f3c5e5738cd4d82e4903c0e0, with no original package patches.
The override adds only this patch. The hosted build retains derivation, source
and binary identities, upstream license, logs and the runtime closure. A linked
Tcl smoke test must reject uninitialized state through the actual C++ method.
This still does not execute a chip repair or waive the default-equivalence and
real contention-regression gates above. No local compiler/EDA run occurred.

## Guarded follow-on execution

A separate branch-only manual `router_force_repair` workflow awaits the selected
successful build, authenticates its run/attempt/source/patch and runtime closure,
then runs a pinned upstream Nangate45 GCD regression with the stock and patched
tools. The fixture checks default identity, three actual invalid rejections
(duplicate/null/database-clock), a native two-net reroute witness, zero native
overflow, unchanged unselected routes/physical census and complete guides.
It is a noncongested API regression, not a proof of congestion convergence.
Other invalid classes and injected expansion-exhaustion cleanup remain untested;
the chip trial accepts only the two fixed authenticated nonclock seed nets in
a disposable process, with strict before/after guards. This does not qualify
the general API for production use.

After that regression passes, the custom tool must reproduce exact121 with
repair disabled in a separate run. The actual pair trial additionally hashes
the initial121 grid and full segments in the same process before invoking the
API. It retains full instance/terminal/geometry/OBS/guide/net inventories and
compares capacity arrays. GRT0232 is an exhausted diagnostic failure; its
initial121 table is never mislabeled as the final result. Final native success
requires an actual final table, zero calibrated grid and complete guides.
All output retains physical_acceptance:false pending downstream signoff.

Root review and integrated local regression168PASS/2SKIP; new escaped-name Tcl
fixtures execute using Python Tcl, while two existing Tcl-shell fixtures lack
a shell interpreter. YAML and shell syntax checks pass. No native regression
or chip-repair execution has yet occurred.

## Native observation and pin-access credit correction

Hosted38849978485 executes the native GCD API regression and reproduces the
custom default exact121 checkpoint. The forced southern pair then reaches
GRT-0232 with final calibrated grid139 (Metal1/2/3/4:9/51/32/47). Full instance,
terminal and geometry inventories remain unchanged, but203 encoded capacity
entries increase:126 onMetal2 and77 onMetal3. This fails the experiment's
capacity-control requirement. It is not an unchanged-capacity comparison or
an accepted route, and139 must not be used to reject the clean joint-reroute
hypothesis on its own.

Pinned-source review identifies a concrete mechanism. `initFastRouteIncr`
calls `initNetlist` for the initial selected reroute and each congestion
expansion. The original `initNetlist` unconditionally calls
`addResourcesForPinAccess`. That function traverses **all** known macro/pad
pins and uses `addAdjustment(..., edge_cap + 1, false)`: it is an increment,
not an idempotent declaration. Initial full routing already added those
access credits; calling it again during unchanged-net repair credits the
same physical access repeatedly. The forced run has an initial reroute and
four expansions, so this path can execute five additional times. The observed
encoded-capacity increase is consistent with repeated access crediting; this
source mechanism does not claim a per-cell accounting reconstruction of203.

The review-only patch now skips only that call while `force_reroute_mode_`
is true. Its default-false path still executes the original function, and
ordinary incremental routing remains untouched. This does not remove the
initial full-route pin access resources. `findFastRoutePins` reads saved
on-grid pins; `makeFastrouteNet`/`addNet`/`clearNetRoute`/`releaseNetResources`
reset route trees and usage but do not remove those capacity credits.
`initAuxVar` initializes scratch arrays. Forced mode permits neither new
nets/pins nor physical movement and stops before placement fallback, so
there is no legitimate new pin access to reserve in this restricted path.
If those restrictions change, this skip requires renewed review rather than
being generalized to ordinary incremental repair.

Updated patch SHA256:
`73e5588175fadd8d08793f19c09d4aa2b50c744d0c2b5229c9e503c592fc8aef`.
`patch --dry-run -p1` succeeds against unchanged copies of the same pinned
three upstream files. This correction has not been compiled or executed.
A new pinned build must repeat native GCD/default identity before one bounded
chip retry, and the existing cellwise before/after capacity guard must pass.
The139 trial and its failed control are retained. No capacity acceptance,
congestion threshold or hardware/timing constraint is relaxed.

## Boundary capacity evidence refinement (BUG100)

The historical calibrated179×98 export contains only the interior69064 cells.
It excludes genuine horizontal last-row and vertical last-column edges.
The existing passing gate requires a final native congestion table; its pinned
`computeCongestionInformation` scans all real preferred edges, so an interior
zero alone has never sufficed for acceptance. The before/after capacity claim
from old artifacts must nevertheless be limited to the observed interior.

The updated runner preserves that exact interior hash and exports separate
initial/final real-boundary sidecars, comparing their capacities and reconciling
interior plus boundary overflow with the native full table. Pinned CMOS5L LEF
SHA3edd5a1ad31e8307be537d0d1b85c3258fefeb21aac04aaa476e4f72de4cffd5
specifies Metal1/3 horizontal, Metal2/4 vertical. Runtime `getDirection` must
match; pinned OpenDB Tcl enum bindings return those literal direction strings.
Focused tests76PASS/2existingSKIP include executed Tcl and malformed, missing,
changed-capacity and boundary-only-overflow rejection. Hosted sidecar evidence
is pending; this does not retroactively add boundary observations to old runs.
