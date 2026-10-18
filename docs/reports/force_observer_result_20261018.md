# Complete-grid observer outcome, October 18

[Build38950370119](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38950370119) and [qualification38950416231](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38950416231) completed successfully at cb542492775ba0ee3b5a68e38e923956c09708dd. These are diagnostic successes; routing remains rejected. Downloaded result SHA256: `baad2989fc4c59b7db3762bcccff08959856fe9c12c4cda6037a3581c4d86791`.

The coordinator reran validate_stage for both actual downloaded cases and validate_observer for the repaired case. Default reproduces exact121. Observer reproduces all three final rejected132 segment/interior/boundary hashes from38948702750. Every pass retains3659 merged nets, all69064 interior cells and550 real preferred boundary edges, with unchanged capacity arrays. Physical census and geometry match before/after.

| Pass | Actual input nets | Newly added | Complete reporting-grid overflow |
|---|---:|---:|---:|
| 0 | 2 | 2 | 125 |
| 1 | 53 | 51 | 123 |
| 2 | 489 | 436 | 139 |
| 3 | 637 | 148 | 140 |
| 4 | 678 | 41 | 132 |

No observed pass improves121. In particular, the touched-only native counter24 does not establish a full-chip improvement. The final GRT0232 failure has no native final congestion table and lacks the two selected guides. No transient snapshot is promoted to a usable checkpoint.

The next single-change experiment is D102: force-only restoration of positive-usage grid membership after incremental clearUsed, adapted from immutable upstream50d692be (see upstream_incremental_scope_20261016.md). This tests a source-supported omission affecting congestion discovery and native history updates; these measurements do not prove that it will close routing. Preserve default121 and same-binary legacy132 controls before enabling the candidate. Retain native return, full grid, capacities, geometry, census and final guide/table guards; physical acceptance remains false even if global routing succeeds.

## Initial-owner coverage cross-check

Read-only attribution on the exact initial121 segments/grid independently reproduces103 overflowing cells and439 distinct preferred-route owners. Intersecting that **initial** owner set with validated native pass inputs gives2/46/376/426/438 owners; missing counts437/393/63/13/1. Names are normalized through the strict observer parser, including native escaped brackets.

The sole omitted initial owner at the final pass is `net1134`. Its route is byte-semantically unchanged, and its initial overflowing Metal2 edge at grid(1,65) remains overflowing in the final reporting grid. This is a concrete missed owner, rather than an inference from a partial scalar. It does not establish that routing this net alone resolves congestion: almost all initial owners already entered the expansion, and all measured passes remained worse than121. Later changed routes can introduce new owners/overloads; this analysis deliberately makes no later ownership claim from preferred-only initial attribution.

The ignored reproducible summary is build/observer109_initial_owner_coverage.json. The D102 helper body was also compared directly with immutable upstream50d692be and matches exactly; the WARP opt-in scope and activation reporting are separate adaptations.
