# Independent v2 exterior-connectivity review — October 19

Reviewed `tools/autonomy/corridor_solver.py` and its focused tests, read-only.
No concrete blocker found for qualification of the declared abstract v2 model.
This is not authentication of native WARP exterior connectivity or physical
routing. No EDA, source/test edits or workflow dispatch was performed.

The v2 contract explicitly changes boundary semantics and requires each net's
`frozen_exterior_components`. Components contain at least two distinct existing
boundary terminals, stay within that net's terminal set, and are disjoint within
each net. Unknown, duplicate, overlapping and non-boundary members fail. v1
rejects the new fields and retains its old boundary contract. Canonicalization
copies inputs, sorts component membership/order and preserves semantic layer
order. The declared relation is not inferred from shared coordinates or another
net's terminals.

Each component is implemented as an anchor star of signed aggregate flow
variables **inside the per-net loop**. These variables are used only in that
net's node conservation equations. They create no global geometric edge, shared
occupancy bit or capacity exemption on actual physical edges. Another net cannot
borrow the relation. The independent BFS witness checker adds only the currently
checked net's component adjacency, and only reachable components enter the root
closure. Disconnected components still need actual selected edges to connect.

Signed exterior-flow bounds of ±(terminal_count−1) are sufficient: no star arm
needs more than the total non-root sink demand. Node conservation enforces one
unit for every non-root terminal and the corresponding source demand. The BFS
checker separately verifies reachability and rejects disconnected extraneous
selected edges. Pruning unused disconnected solver occupancy can only decrease
resource consumption and is followed by witness validation. Each selected real
edge still charges one declared per-layer/via demand per occupying net; exterior
relations do not alter real-edge fixed usage or capacity constraints.

The declared variable budget counts all real-edge occupancy/flow pairs and every
component star link before model allocation. The global exterior-link limit is
also enforced. Final model variable count is checked, and CP-SAT model validation
remains required. Existing one-worker/version/time limits, explicit omissions,
UNKNOWN scope and false native/physical/timing authentication flags are retained.
No independent infeasibility-certificate claim is introduced.

Independently executed in the project venv:

```sh
PYTHONPATH=tools pytest -q tools/autonomy/tests/test_corridor_solver.py
```

**213 passed in 0.62 s**, with no skips. The existing 117 tests remain alongside
96 additional tests, including 81 independently enumerated tiny multi-net graph
cases. The exhaustive oracle computes edge-subset/set closure rather than using
production flow/BFS helpers. Specific fixtures cover private-relation leakage,
required links between exterior components, competition for actual shared-edge
capacity, explicit v1/v2 schema separation, variable/link bounds and canonical
ordering. These are abstract fixtures, not extracted WARP graphs.

Reviewed SHA256:

- Solver: `6fa5fc03d7ab3fec5bd07509ba803c8671932f8ae64b05b064a336dc41dafe6d`.
- Tests: `e825df73d04d854b405827e69a29841f1813004c882116e6d80b0c90941928db`.

Before native use, a separate authenticated extractor must establish that every
component actually represents frozen same-net connectivity after the selected
interior resources are removed, account for all required boundary contacts, and
keep its exterior resource consumption fixed. Per-net equivalence declarations
cannot stand in for physical pin/via feasibility or bypass the initial121
multiset-versus-union distinction. No native application follows from this
source/test review alone.

## Hosted follow-up

Coordinator downloaded actual39333075002 at1dc0aedeaaa3a40c7bdeec66bd29e29aead9e862:
results.xml independently passes strict213executed/0failure/error/skip; retained
packages/source-revision match. This qualifies the declared model extension,
not native WARP input extraction or a physical repair.
