# Independent source review: native corridor observer

Review scope: `patches/openroad_corridor_observer.patch`, after the existing D101 observer and D102 opt-in used-grid restoration. This is a source/applicability review, not a C++ build or native qualification. No tool was built, routing run dispatched, or source patch edited by this reviewer.

Current source-reviewed patch SHA256: `b7493c2fc4e4c7074363550fd0a059064ee739a4fc593f3eaf14081167a5ff65` (independent full review at49c0443, coordinator reviewed the numeric-cast-only follow-up below). Exact `patch --dry-run --fuzz=0 -p1` succeeds for all five files against `/tmp/warp_corridor_base`, the D101+D102 source copy. **Source review passes for a bounded observation qualification; compilation, same-binary identity and native ledger reconciliation remain unverified.**

## Findings corrected during review

1. **Idle-state guard omitted `is_incremental_`.** The pinned `GlobalRouter::startIncremental()` sets that flag directly; it does not require a dirty net or callback to exist. The original callback/dirty/force checks therefore admitted explicitly entered incremental mode. The final guard now rejects `is_incremental_` before collection. This was a collection-contract issue; no route mutation was found in the export itself.
2. **Existing-output refusal was weaker than its error message.** Original `std::ifstream(path).good()` followed by `std::ofstream(path)` could truncate an unreadable but writable existing file, follow a dangling symlink, or race another creator. The final patch serializes first, then uses Linux `open(O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600)`. Existing final paths, including dangling symlinks, cannot be overwritten by this operation. Its bounded write loop handles short writes, retries `EINTR`, rejects zero/failed writes and checks `close` before logging success. Failed serialization creates no file; failed writes preserve a partial artifact without a success witness. This is exclusive creation, not atomic publication of a fully written file; completion/census checks remain mandatory.

Both findings were sent to the patch author and coordinator and independently rechecked in the final patch. Initial reviewed SHA256 was `1686d358f94e807b7d786028354de7fb88a12514e038ee9b831d32c6922ebdfc`; use the final hash above for any build. Linux/POSIX headers are explicit; portability to other operating systems is not claimed.

## Source-supported positive checks

- The command is explicit: SWIG `grt::export_native_corridor_state` calls the new method. No existing routing/default-flow call site is changed, and no automatic environment-triggered invocation is introduced. Reading `WARP_CORRIDOR_DIR` alone does not invoke the export.
- The core method is `const`. It iterates raw arrays, live net/tree state and getters, writing to an output stream. No route/capacity/usage setter, routing invocation, pin-access update, congestion recomputation or used-grid rebuild is added. `FrNet::isSoftNDR()` is a non-const getter in upstream but its body only returns the flag. `GlobalRouter::haveDetailedRoutes()` can initialize its cached block pointer when null; the initialized-route precondition normally already establishes the block. This is not an unconditional claim that every called method is declared const.
- For every layer, horizontal edges cover `y<ny,x<nx-1`; vertical edges cover `y<ny-1,x<nx`. These include the real final horizontal row and vertical column. Both orientations are retained even on nonpreferred layers. Raw `Edge3D.cap`, `usage`, `red` and `real_cap` remain separate, avoiding the encoded OpenDB reporting-grid ambiguity.
- Live `nets_` is used, rather than the active `net_ids_` vector that native routing can clear. Null slots are distinguished. Database mapping is checked before exporting a net. Clock classification, soft-NDR flag, scalar2D edge cost, every live per-layer cost, planar layer bounds, driver and coarse pin coordinates/layers are exported. The `int8_t` costs are widened to integers rather than streamed as characters.
- `STEP` preserves every consecutive pair from every tree edge and keeps multiplicity. The pinned `releaseNetResources()` likewise iterates all tree edges and their `routelen` pairs, without `edge.len` or route-type filtering. It skips layer-changing steps and charges `getLayerEdgeCost(layer)` for planar steps. The observer exports zero for vias and that exact active per-layer cost for planar pairs. It does not deduplicate through `get3DRoute()`, which would lose accounting information.
- Incomplete grid vectors and invalid layer indices throw. Nonunit or otherwise invalid geometry is retained for downstream rejection; it must never be silently expanded into a different accounting model. Tab/newline-bearing net names are rejected instead of corrupting the TSV.
- In-memory stream serialization, exclusive file creation, complete descriptor writes and closing are checked; the native completion log appears only after a successful close. The TSV has explicit schema/indexing, an unverified-ledger flag, a coarse-via limitation, counts and a final completion row. A final TSV row alone cannot substitute for successful native execution and the logged completion witness. The serialization temporarily retains both the stream and byte-string contents; hosted memory/runtime cost remains unmeasured.

The above source facts were checked against pinned OpenROAD revision `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`: [GlobalRouter.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp), [FastRoute.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/FastRoute.cpp), [RipUp.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/src/RipUp.cpp) and [DataType.h](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/fastroute/include/DataType.h), using the local source copies retained for patch review.

## Conditions remaining beyond source approval

The observer's guard does not authenticate the exact121 checkpoint, binary/source identity or PDK. A caller must establish that unchanged control before interpreting any export. The output does not itself join native layer indices to actual technology directions/DBU, authenticate local/merged classifications or physical-to-coarse-pin memberships, or export complete tree-node access intervals. Those joins and any required additional observation remain explicit work under [the native contract](native_corridor_contract_20261019.md).

The raw `STEP` multiset must be checked edgewise against raw3D usage, including any background demand and native multiplicities. The explicit-graph solver uses per-net union occupancy; it cannot silently replace native repeated contributions with one track. Unresolved residuals, uint16 wrapping, invalid steps, missing route/tree/pin inventory or changed control hashes block native-ledger authentication. Coarse vias omit physical cut/DRC feasibility, and net planar layer limits must not be used to delete via-only pin access.

Source-level read-only observation is not proof of unchanged execution. A same-binary disabled/enabled comparison must preserve exact121 segments, interior/boundary data, geometry and net census, and prove the new output/complete markers match the successful native process. Solver results remain about their declared graph; no detailed-route, timing, DRC or chip-acceptance conclusion follows from this observer.


## Coordinator numeric-output follow-up

The author verified pinned Edge3D resource fields are uint16_t, which already
stream numerically; no byte-output defect was demonstrated. Four explicit
int64_t casts make that intent clear without changing values. This sole
follow-up changes patchSHA to b7493c2fc4e4c7074363550fd0a059064ee739a4fc593f3eaf14081167a5ff65;
coordinator inspected those casts and unchanged guards. Exact sequential
no-fuzz application was repeated. The previously reviewed49c0443 patch is
historical; use b7493c2 for any build. Native qualification remains pending.
