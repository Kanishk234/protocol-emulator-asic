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
