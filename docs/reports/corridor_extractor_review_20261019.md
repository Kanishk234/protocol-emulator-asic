# Independent bounded corridor extractor review — October 19

Reviewed `tools/autonomy/corridor_extract.py`, its focused tests and
`native_terminals.audit_selection` with its additional tests. No concrete blocker
found for a bounded declared-model experiment. No CP-SAT invocation, EDA, source
edit or dispatch was performed by this review. This does not authenticate a
native graph or establish physical routing feasibility.

## Admission and resource accounting

Subset admission reruns the complete raw/terminal cross-join and requires exact
raw usage reconciliation. It admits only an explicit nonempty list of unique
existing native slots, up to128. Unsupported records tied to a selected slot or
DB ID block admission; records without either identity also block admission.
Excluded diagnostics are counted and the whole-inventory gate remains separately
false where appropriate. This does not convert the observed285 local/32 absent/
2 supply-net diagnostics into a global pass.

The extractor releases only selected old planar STEP occurrences whose **both**
endpoints lie in the inclusive window. It uses each occurrence's multiplicity
and current per-layer demand, whose complete usage ledger was already required
to reconcile. Remaining fixed use is raw usage minus that exact selected sum;
negative residuals reject rather than clamp. Nonselected consumption remains
fixed. Both raw H/V directions and all valid interior-window edges are included,
with raw capacities. New selected topology is explicitly per-net Boolean edge
union: removal of a repeated old traversal is a proposed new-route choice, not
an assumption that the historical native ledger was already a union.

Each selected net retains complete per-layer demand and its native planar layer
interval. All adjacent-layer vias at every window coordinate are explicitly
unlimited and zero planar demand. This deliberately relaxes physical via and
native search-access restrictions; no hidden physical cut-capacity value or unit
NDR demand is invented. Solver feasibility is only capacity/connectivity in this
declared coarse graph.

## Frozen exterior and boundary semantics

Published segment parsing requires full raw-net name inventory with no duplicate
or unknown net names. Selected segments must be Manhattan, have known layers,
convert to exact in-bounds grid centers and be nonzero. Expanded selected planar
support must equal the native STEP support as a union. Full selected native pins
must be connected by a published-route component before extraction.

Retained exterior edges are exactly those whose endpoints are not both inside
the window, including crossing edges. A crossing's inside endpoint becomes a
required boundary terminal. Exterior connected components induce equivalence
only between that net's boundary endpoints. They are not shared geometry or
resources and cannot connect another net. The v2 solver still requires all inside
pins and boundary contacts to connect through selected window edges or these
explicit private equivalences. Exterior physical consumption and connectivity
are frozen; no outside route/resource repair is modeled. Accordingly an
INFEASIBLE answer applies to this window, selected cohort, retained contacts and
fixed outside policy only. It cannot prove whole-chip impossibility or exclude a
repair that changes the outside route/cohort. Frozen outside overflows themselves
are outside the window solve's capacity constraints.

## Coordinates, limits and provenance

Pinned FastRoute get3DRoute converts native x to
`tile_size*(grid_x+0.5)+x_corner` (FastRoute.cpp:1126 onward). The inverse used here
is exact for even pitch and rejects odd pitch, noncenter endpoints and out-of-grid
selected positions rather than rounding. Native index/layer data and terminal
layer names/directions were already cross-joined. Max node/edge size is checked
before graph allocation; variable count includes real-edge occupancy/flow pairs
and exterior star links and is bounded by the hard solver limit. Solver graph
validation remains an additional gate. The solver's optional lower per-call
variable limit still applies when actually solving.

Provenance binds supplied snapshot/terminal SHA fields, SHA256 of the supplied
segment text encoded as UTF-8, selected slots and window, then hashes that
manifest into the graph's recorded source digest. This is a reproducible identity
of supplied inputs, **not** proof that those SHA fields/objects/text came from a
specific workflow. The caller must authenticate immutable raw files, exact
run/attempt/source/patch/checkpoint and retained published segment bytes before
using the extracted graph. Parsed objects are mutable and the adapter does not
independently reload/authenticate their source files. All native-input, physical
and timing authentication flags correctly remain false.

## Independent tests

In the project venv, executed:

```sh
PYTHONPATH=tools pytest -q tools/autonomy/tests/test_corridor_extract.py tools/autonomy/tests/test_native_terminals.py
```

**78 passed in0.28s**, no skips:15 extractor fixtures and63 terminal/subset
fixtures. Cases include exact boundary crossings, a real retained exterior
detour, repeated old traversal release followed by union occupancy, invalid
windows/geometry/inventory, changed planar support, admission/size gates and
no solver invocation/determinism. These are hand-sized declared fixtures, not an
actual WARP routing solution or native extractor qualification run.

Reviewed SHA256:

- Extractor: `18dfded68e673ef8bf2d2c76a331d5bc6c7615845ecfac5400d5f79d77ac48a6`.
- Extractor tests: `6d162a29b366541a5a666f0f1c311d6cbb1998363396977d113f19be5385ad9d`.
- Terminal module with subset admission: `bffe63713c839621329a0b5e0e42896fd70a9301eca7859b503c754afc81d01a`.

Before interpreting an actual solve, retain the exact source-bound input files,
window/cohort/release manifest and graph hash. FEASIBLE needs the independent
solver witness checker; UNKNOWN remains inconclusive; INFEASIBLE remains scoped
to the declared model. Native routing handoff, detailed physical checks and
unchanged whole-chip acceptance criteria remain separate future obligations.
