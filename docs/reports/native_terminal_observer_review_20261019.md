# Independent native terminal observer source review — October 19

Reviewed `patches/openroad_terminal_observer.patch`, SHA256
`5ec2f809d784e5d81e59a1470bef566423f7a35cb1aea573564b35734396393b`,
against pinned OpenROAD `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0` after
D101, D102 and the qualified native-resource observer. No concrete source
blocker found for bounded build/runtime qualification. This is not a compiled
binary test, actual terminal join, solver-model authentication or physical
access/via acceptance.

Independently executed `patch --batch --fuzz=0 --dry-run -p1` in the clean
`/tmp/warp_terminal_base` tree: all five files pass. Inspected resulting source
in `/tmp/warp_terminal_candidate`, pinned Pin.h/Pin.cpp, Net.h/Net.cpp,
DataType.h, GlobalRouter.cpp, FastRoute.cpp and utility.cpp. No patch/source
edits, EDA, build or workflow dispatch were performed by this review.

## API, output and read-only behavior

The explicit `grt::export_native_terminal_state` API requires a nonempty
`WARP_TERMINAL_DIR`, initialized idle GlobalRouter state, existing routes,
nonnull block/grid, positive tile size, no detailed routing/CUGR, no active force
operation, no incremental mode/callback and no pending dirty nets. It has no
default routing call site. Serialization completes in memory before Linux
exclusive `O_CREAT|O_EXCL|O_NOFOLLOW` final-file creation (mode0600). EINTR,
short/zero/failed writes and close status are handled; no successful witness is
printed after a failed write/close. Existing final files and dangling symlinks
cannot be truncated. Parent directories remain caller-controlled; this is not
an atomic directory traversal or crash-durability guarantee.

Native slot lookup uses map `find`, bounds and pointer identity checks; it never
inserts entries. Missing native nets return explicit −1. Global/net inventories
are sorted using local copies, not by mutating router state. `Net::isLocal`
(Net.cpp:75) only compares existing pin positions. `Pin::isDriver`
(Pin.cpp:161) only reads existing BTerm/MTerm IO types despite its nonconst
signature. `getNetMaxRoutingLayer` (GlobalRouter.cpp:1245) only reads cached net
signal type and configuration. No observed code changes routes, tree data,
placement, resources, costs, history or classification.

## Exact source membership semantics

The observer mirrors `GlobalRouter::findFastRoutePins` (pinned
GlobalRouter.cpp:1253–1288): get current on-grid DBU position, clamp connection
layer to the net-specific maximum **before** grid conversion/deduplication, use
C++ integer division by grid tile size, and preserve source eligibility,
including its unusual acceptance of grid `y=-1`. It does not normalize the
source eligibility to the stricter actual-export graph bounds.

Global pins export ordered ordinals, underlying BTerm/ITerm IDs, ITerm instance
and master-terminal IDs, raw on-grid position, original/clamped layers,
eligibility and native slot. Every native pin at the computed x/y/clamped-layer
position is reported as a MEMBER; no fake one-to-one relation is imposed on
physical pins merged by native deduplication. Unresolved database references retain
missing identity fields as IDs0/name UNRESOLVED/driver−1 rather than invented
identity; an existing ITerm ID remains observed even when its instance/master
reference is unresolved. Distinct
clock classifications from the database, GlobalRouter and native export can
subsequently be compared without assuming equality.

The source's driver selection is subtle: root starts at0 and changes only for a
newly inserted unique driver pin; a later duplicate driver does not replace an
existing root. The observer does not rerun that builder. It exports each resolved
physical pin's actual driver flag and the existing native driver index separately.
A downstream validator must replay ordered dedup/root rules and compare those
observations; this source review does not label the join already verified.

## Node access and sentinels

Full database and GlobalRouter inventories include explicit native-slot absence;
native slot/pin vectors and all node-to-pin map entries are separately retained.
Counts distinguish database nets, GlobalRouter pins/membership rows, native
slots/live nets, tree nodes and node-to-pin mappings. Sparse/dropped/merged nets
are not hidden by inventing a common count. Invalid identities/vector lengths
throw; unsupported mappings/access must remain classified downstream.

TreeNode `assigned` and `stackAlias` lack default initialization in DataType.h.
The observer avoids reading node access/alias state for empty/degenerate/unrouted
contracts: access requires global 3D stage plus at least two native pins and tree
terminals and nonempty nodes/edges. Unsupported nodes emit only their indices and
explicit unsupported status. For routed trees, layerAssignment
(utility.cpp:1306 onward) initializes alias/access state; subsequent routing
maintains it. The patch does not read `assigned` at all.

Supported nodes export x/y, stackAlias, bot/top layer and hID/lID as raw observed
values. Sentinel −1, global layer-count or BIG_INT values are not silently coerced
to valid access. VIA_RANGE reproduces `getViaStackRange`
(utility.cpp:418–441): match all native pin x/y at the node, take min/max native
pin layers, and retain no-match low=32767/high=−1 plus an explicit match count.
This matches pinned Linux short/int16 semantics and does not fabricate a physical
via. All potentially byte-width coordinate/layer values are explicitly cast to
numeric integers for streaming. Existing raw-resource TSV/calibration is unchanged.

## Remaining qualification obligations

Compile/link/SWIG smoke and actual checkpoint observations remain required.
Authenticate exact121/default and unchanged legacy/candidate controls, verify
output completion and immutable raw bytes, independently parse all counts and
sentinels, join database/GlobalRouter/native IDs and ordered pins, reproduce
clamp/dedup/root selection, validate native node-to-pin/alias references and
cross-check existing resource exports. No raw access field or coarse pin match
by itself proves physical pin enclosure, legal via templates, obstacle clearance,
terminal connectivity or a native corridor model. The emitted terminal model gate
correctly remains false pending those joins. No physical promotion follows from
this source review or from compilation alone.

Final-hash hardening independently inspected: both native matching/export loops
check nonnegative pin count, exact count-to-X-vector size and equal X/Y/L lengths
before indexing. ITerm name/driver resolution checks instance and master-term
pointers before dereferencing. Repeated the five-file no-fuzz dry-apply against
the exact after-three-patch baseline successfully for the final hash above.
No new blocker found; compilation/runtime obligations remain unchanged.
