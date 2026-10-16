# Upstream pin-access history confirms the D100 correction

Primary-source research on October16 identifies an upstream fix for the same
repeated pin-access credit mechanism. This supports D100's source diagnosis;
it is not routing evidence for WARP and does not justify a tool upgrade.
No upstream code was applied, compiled or executed during this research.

## Immutable change and merge identity

Our pinned OpenROAD commit is
`dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`, dated February17,2026 at22:16:53UTC.
GitHub's comparison reports the fix below **83 commits ahead, zero behind**,
with that pinned revision as the merge base. The fix is therefore absent from
our pinned source; its presence in current upstream is not a reason to assume
our June-dated tool bundle already contains it.
[Immutable comparison](https://github.com/The-OpenROAD-Project/OpenROAD/compare/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0...09f16990f662d522b51094a6c3085c25f3ade024).

The relevant sequence is:

| Commit | Committer date, UTC | Verified source change |
|---|---|---|
| `04c5ae0d30ef2affa2b2b6f9b507fb3eda79741a` |2026-02-20 14:00:12|Changes `addResourcesForPinAccess` to take the supplied net vector rather than traverse the entire database net map.|
| `09f16990f662d522b51094a6c3085c25f3ade024` |2026-02-20 14:30:08|Adds an incremental argument to netlist initialization and suppresses pin-access resource additions during incremental calls.|

Sources: [subset-net change](https://github.com/The-OpenROAD-Project/OpenROAD/commit/04c5ae0d30ef2affa2b2b6f9b507fb3eda79741a),
[incremental-credit fix](https://github.com/The-OpenROAD-Project/OpenROAD/commit/09f16990f662d522b51094a6c3085c25f3ade024).
The second commit's parent is
`8aee38e241dc92355213ccf04d8749767f2c07f3`; that intervening change avoids
calling the helper when the design has no macro/pad instances.

The fixes were merged in
[PR9510](https://github.com/The-OpenROAD-Project/OpenROAD/pull/9510), merge commit
`186c695e9b290ff66576b9f89fc8b5747e17c49e`, on February24,2026 at19:13:41UTC.
The maintainer's explanation explicitly links repeated incremental additions
to excess resources and inaccurate congestion estimates. That explanation is
consistent with WARP's observed capacity drift; it is not an independent
per-cell reconstruction of WARP's203 changed entries.

For current-source context only, the `master` HEAD resolved during this audit
to `d6bc758caed99ca4e58f9168717e57a9da536c10`, committer date
2026-10-16 18:00:20UTC. No mutable `master` source is used as the identity of
the February fix or as a proposed WARP build input.

## Exact upstream versus D100 scope

In the immutable incremental fix, the header changes netlist initialization
to accept an incremental flag defaulting false. Its implementation adds
pin-access resources only for a macro/pad design when that flag is false;
`initFastRouteIncr` explicitly supplies true. The helper still performs its
normal initial reservation. This is a broad correction to native incremental
initialization, not a change to routing capacities chosen by the user.
[Source hunks](https://github.com/The-OpenROAD-Project/OpenROAD/commit/09f16990f662d522b51094a6c3085c25f3ade024).

D100 instead leaves the pinned ordinary/default paths unchanged and skips the
existing helper only while our explicitly bounded forced-unchanged-net mode
is active. Original full initialization has already credited the same pins;
that restricted mode does not move pins or create nets. Both changes prevent
re-crediting pin access during rerouting. D100 is **narrower**, rather than an
identical backport of the upstream implementation. In particular, D100 does
not fix the pinned tool's other ordinary incremental paths. Those would need
separate review if they become relevant to a later physical flow.

This source proof strengthens the rationale for finishing the current
capacity-controlled retry. It does not establish that the corrected pair
fits, that the old139 result was an unchanged-capacity regression, or that
any intermediate metric covered all chip congestion.

## What this does not solve about congestion membership

Neither February change selects additional congested nets or replaces the
native expansion mechanism. The immutable fixed GlobalRouter source still
seeds the incremental congestion set from dirty nets and invokes the existing
congestion discovery/expansion path before rebuilding those nets. The
subset argument belongs to **resource initialization**, not a request to
include every owner of every original full-chip overflow edge.
[Fixed-source incremental implementation](https://github.com/The-OpenROAD-Project/OpenROAD/blob/09f16990f662d522b51094a6c3085c25f3ade024/src/grt/src/GlobalRouter.cpp#L5725).

Therefore this change does not prove that all439 original overflowing-edge
owners are included in WARP's incremental trial. Actual expanded names and
whole-grid per-pass evidence remain the discriminating observations if the
capacity-corrected trial fails. The touched-edge versus whole-grid distinction
in `force_repair_metrics_20261015.md` is unaffected by finding the February fix.

A separate recent upstream change,
[da567521d181f60df9b1dcc5274e139ef524f0f4](https://github.com/The-OpenROAD-Project/OpenROAD/commit/da567521d181f60df9b1dcc5274e139ef524f0f4),
dated October13,2026, refreshes OpenDB congestion reporting after incremental
routing using an engine-maintained dirty-tile list. Its source distinguishes
actual edge writes from footprint comparisons after old routes are already
removed. This confirms another **reporting maintenance** concern, but does
not show that WARP needs that implementation: our collectors explicitly call
the pinned complete native exporter before reading final grids. It neither
supplies missing expansion identities nor makes the older incremental scalar
metrics a full-chip acceptance result. No backport or engine switch is selected.

## Retained source hashes and licensing

Exact raw source downloads were inspected; GitHub commit APIs supplied the
immutable patches, parents, dates, comparison and PR association. Local
read-only metadata is under `/tmp/warp110-*`; no raw upstream source is added
to the project tree.

| Source | SHA256 |
|---|---|
| GlobalRouter.cpp at subset commit04c5ae0… | `6fe1a02681310b4745f5f67ed483fb6d7596021910e171b58251842b6a0ca1cc` |
| GlobalRouter.cpp at incremental fix09f1699… | `f60396ee298406f8267cb014c7e4d8c084175fc807f16768c96af31a2b1a9493` |
| Pinned GlobalRouter.cpp atdcf36133… | `71befc6541b5d2b0d22ec021e8c7f2d3edcd2c0dcf4575b0fb28ad21f5e5af83` |
| Retained pinned OpenROAD LICENSE | `28cfc93cb2b552192bc316259d2c2a1aa5a980018cda1c5cd9b1143c9151aebb` |

OpenROAD's source headers and retained license identify BSD-3-Clause and the
OpenROAD Authors. Preserve the complete upstream license and attribution in
any future build/source artifact. Source inspection and a merged upstream
fix are not substitutes for WARP's native regression, exact-default identity,
capacity-array checks, complete-grid acceptance or downstream physical checks.
