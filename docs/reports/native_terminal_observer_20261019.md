# Separate native terminal/access observer

`patches/openroad_terminal_observer.patch` is a separately reviewable, explicit observation extension after D101, D102 and the raw corridor observer. Current SHA256: `5ec2f809d784e5d81e59a1470bef566423f7a35cb1aea573564b35734396393b`. The existing raw `warp-native-corridor-v1` exporter and schema are unchanged. This report records source/dry-apply evidence only; no new binary was built, native trial dispatched or physical acceptance established by this task.

The actual raw qualification39331845906 reconciled all six usage ledgers across139228 edges each; its unchanged initial snapshots and default final matched exactly. Initial `cfg_word[23]` uses `H,layer2,x13,y30` twice, so global union compatibility is false despite correct multiset accounting. This observer supplies the missing membership/access observations; it does not remove that accounting distinction or adapt a corridor automatically.

## Invocation and invariants

New explicit Tcl API: `grt::export_native_terminal_state`. Caller supplies a fresh existing artifact directory in `WARP_TERMINAL_DIR`; output is `native-terminals.tsv`. Success witness, after complete write and checked close:

`WARP_NATIVE_TERMINAL_COMPLETE path=<full output path>`.

No default invocation, routing call, geometry/pin setter, adjustment, net initialization or used-grid rebuild is added. The command rejects forced/incremental/callback/dirty state, missing initialized routes/block/grid, CUGR and detailed routes. It serializes before file creation, then uses Linux `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600`, checked bounded descriptor writes with short-write/EINTR handling and checked close. Serialization failure creates no file; a failed write can preserve partial output but never emits success. Exclusive creation does not mean atomic publication of the completed file. Root-owned0600 exports need the runner's already established bounded artifact-permission handling; permission changes are outside this observer.

The output explicitly starts with `terminal_join_verified=false`. Existing raw121 checkpoint authentication and disabled/enabled identity controls must bind both files to the same process/checkpoint before interpretation. Physical via feasibility, detailed routing, timing and chip acceptance remain unverified.

## Exact schema, tab separated

All rows end in LF. Text fields reject empty/tab/CR/LF values before file creation. Counts/IDs/coordinates are decimal integers. GlobalRouter nets are sorted by database net ID; physical pins retain their original `Net::getPins()` order. Native slots retain `nets_` order, with explicit empty slots. No missing/local/merged classification is inferred from the routed3659 count.

The fixed header rows are:

```
SCHEMA warp-native-terminals-v1
MODEL_GATE terminal_join_verified false
SCOPE coarse_pin_membership_and_tree_access_not_physical_via_feasibility
INDEXING native_layers_zero_based_database_routing_levels_one_based
```

Spaces above separate fields for readability; the real delimiter is tab.

| Row | Ordered fields after tag |
|---|---|
| `DBU` | database units per micron |
| `GLOBAL_GRID` | nx, ny, layer_count, origin_x_DBU, origin_y_DBU, tile_size_DBU |
| `LAYER` | zero-based native index, technology-layer database ID, database routing level, name, actual direction |
| `DATABASE_NET` | DB net ID, name, is_special, is_supply, is_clock_signal_type, present_in_GlobalRouter_map, native_slot_or_minus1, ITerm_count, BTerm_count |
| `DATABASE_COMPLETE` | database net count |
| `GLOBAL_NET` | DB net ID, name, is_local, is_merged, GlobalRouter_isClockNet, observed_pin_vector_size, getNumPins, max_routing_layer_one_based, has_route_map_entry, exported_route_segment_count, native_slot_or_minus1 |
| `GLOBAL_PIN` | DB net ID, physical-pin ordinal, kind_BTERM_or_ITERM, term_DB_ID, instance_DB_ID_or0, master_term_DB_ID_or0, pin_name, driver_or_minus1, on_grid_x_DBU, on_grid_y_DBU, original_connection_layer_one_based, clamped_layer_one_based, coarse_x, coarse_y, construction_eligible, native_slot_or_minus1, membership_count |
| `MEMBER` | DB net ID, physical-pin ordinal, native slot, native coarse-pin index |
| `GLOBAL_COMPLETE` | GlobalRouter map net count, physical-pin row count, membership row count |
| `NATIVE_GRID` | nx, ny, layer_count, native origin_x_DBU, native origin_y_DBU, native tile_size_DBU |
| `NATIVE_EMPTY_SLOT` | slot |
| `NATIVE_NET` | slot, DB net ID, name, native_pin_count, planar_min_layer_zero_based, planar_max_layer_zero_based, driver_index, tree_terminal_count, tree_node_count, tree_edge_count, node_to_pin_map_count |
| `TREE_ACCESS_SUPPORTED` | slot, supported_flag |
| `NATIVE_PIN` | slot, coarse-pin index, x, y, layer_zero_based |
| `NODE` | slot, node index, x, y, stackAlias, botL, topL, hID, lID |
| `VIA_RANGE` | slot, node index, minimum_matching_pin_layer, maximum_matching_pin_layer, matching_pin_count |
| `NODE_UNSUPPORTED` | slot, node index, `no_initialized_routed_tree_access_contract` |
| `NODE_PIN` | slot, tree-node index, native coarse-pin index |
| `NATIVE_COMPLETE` | total slots, live native nets, node-or-unsupported row count, node-to-pin mapping count |
| `COMPLETE` | `warp-native-terminals-v1` |

Emission order: header/DBU/grid/layers; all database rows/footer; each GlobalRouter net followed by its physical-pin/member rows; global footer; native grid; each native slot with its net/access flag/pins/nodes-and-via-ranges/mappings; native footer; final completion. A complete-file footer without the successful native process/witness is insufficient.

### Membership semantics

`nativeTerminalSlot()` uses a const `db_net_id_map_.find`, validates existing slot/pointer identity, and returns `-1` for absence. Every database net and every GlobalRouter map entry is recorded, including absent native, local, merged and zero-pin cases. `nativeTerminalMatches()` validates nonnegative native pin count, exact vector/count agreement and equal coordinate-vector lengths before indexing; it returns **all** actual x/y/layer matches. Duplicate or missing matches are preserved for a future auditor to reject or classify, never hidden by choosing one arbitrarily.

The physical tuple is derived with the exact pinned `findFastRoutePins()` arithmetic: clamp connection layer to `getNetMaxRoutingLayer`, subtract grid origin, divide by tile size with C++ signed truncation, and retain the unusual eligibility test allowing `y==-1`. Global clamped layers are one-based; the match uses `clamped_layer-1`. Even ineligible tuples are recorded, not normalized. Native absence is explicit at net level even if there are no physical-pin rows.

Physical term identity uses existing BTerm or ITerm IDs; ITerms additionally carry instance and master-term IDs. Null term/instance/master-term references retain zero IDs/name `UNRESOLVED`/driver `-1`; no such row can authenticate a physical join. `Pin::isDriver()` is a non-const API but its pinned implementation only reads database I/O types; it is called only after the required references are nonnull. The default/duplicate-driver behavior is not reconstructed by choosing a new root: actual pin ordering, driver flags and actual native driver index are all retained for independent comparison.

No database net is treated as equivalent to another because it shares a name fragment, position or protocol role. Physical DB pins outside the GlobalRouter map are classified by database inventory/counts, not presented as observed GlobalRouter pin memberships. A future consumer must distinguish this unavailable membership from a successfully joined local net.

### Access initialization and unsupported state

Pinned `layerAssignment()` initializes every routed tree node's aliases/access variables. `TREE_ACCESS_SUPPORTED` requires native3D mode, at least two native pins and tree terminals, and nonempty tree nodes/edges. For empty, degenerate or unrouted access contracts, the observer emits `NODE_UNSUPPORTED` per existing node and does **not** read potentially uninitialized `stackAlias` or `assigned`. It never reads `assigned` in any case. This flag relies on the unchanged completed initial checkpoint; it does not prove arbitrary interrupted router state safe.

Supported nodes retain actual signed alias/access values. `botL/topL==-1`, `botL==num_layers`, or `hID/lID==BIG_INT` can be native sentinels. They must not be coerced into legal access layers/edge indices. `VIA_RANGE` independently repeats `getViaStackRange()`'s const x/y matching against every FrNet pin, preserving minimum32767/maximum-1/count0 when there is no pin at that node. Internal Steiner nodes can legitimately have no physical pin match; terminal-required ranges need a later role-aware check. Every `node_to_pin_idx` pair is exported with its original indices, not repaired by map insertion.

`get3DRoute()` uses alias/access state and `getViaStackRange()` to add endpoint via geometry absent from raw STEP. The new observation enables that connectivity join; it neither changes raw resource accounting nor proves physical via cuts/enclosure/accessibility. Planar layer bounds and via-only access must remain distinct.

## Evidence and next qualification

Pinned declarations were checked directly in `Pin.h`, `Pin.cpp`, `Net.h` and OpenDB `db.h` at revision `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`. This caught non-const driver and technology-layer getter signatures before any build. Reviewed local source copies are `/tmp/warp_terminal_Pin.h`, `/tmp/warp_terminal_Pin.cpp`, `/tmp/warp_terminal_Net.h`, `/tmp/warp_terminal_db.h`.

Clean exact-after-existing-three-patch source: `/tmp/warp_terminal_base`; proposed source: `/tmp/warp_terminal_candidate`. `patch --dry-run --fuzz=0 -p1` passes all five changed files. Temporary generation uses source copies, not in-place edits of upstream/project-generated RTL. Dry application is not compilation.

Before building, independently review pointer/const API use, unsupported-node guards, exact construction arithmetic, all membership and census fields, exclusive output and absent default invocation. Then a separately authorized hosted qualification must preserve exact raw121/132/139 controls and initial/default-final identity, verify new export/witness inventory, join both schemas by DB ID/name/native slot/pin indices, and report unsupported access or membership mismatches explicitly. A successful join still does not supply a physical via model or automatically make the union solver compatible with every native net.

## Coordinator build and adapter follow-up

Build39333325323 at e5c2e25f0ebceb6f725c2d3b71b59d6cea17da61 succeeds,
including all existing linked smoke checks plus the new terminal API's
uninitialized-state rejection. Hosted build job31m13s, not routing/hardening
runtime. Parser3abf0cb, collector13b08c9 and portable auditor8782e28 preserve
explicit native control/ledger/checkpoint/witness/patch gates. Independent
parser review corrects the initial database-clock versus nonleaf-global-clock
comparison before native use;56focused cases pass. Local full autonomy545
executed passes/zero skips; integrated parser/collector/auditor189 passes.
Native qualification39367564921 at8782e28 is pending. Compilation and model
fixtures do not establish a native terminal join or physical via feasibility.
