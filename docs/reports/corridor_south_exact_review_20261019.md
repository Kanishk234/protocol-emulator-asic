# Independent southern corridor exact-model review — October 19

Reviewed committed extractor `a3eb447` and actual artifacts
`build/corridor112_south/{model,graph,solution}.json`, using authenticated initial
exports from hosted39367564921. Independently reconstructed the graph, selected
admission and release manifest from the retained raw/terminal/segment inputs:
all exactly equal the stored model. No solver invocation, EDA, source edit or
dispatch was performed by this review.

**A simple independent cut proves this declared graph infeasible.** The result
is a collective five-net bottleneck, not merely an unverified CP-SAT answer or an
isolated terminal. Its scope is the fixed cohort/window/exterior model; it does
not establish whole-chip impossibility.

## Input and release identity

Input hashes independently checked through reconstruction:

- Raw native121: `1859f6fdaffad9977ab4025867332a5835e68f50b86405719447b1b3c1aa07e6`.
- Terminal initial: `90be2ecef64627ed67b1c4df920f86f673cac1bcdae4fef4db9587a3e79a18d3`.
- Published segments: `19b14132c36cfa3e863edc34d0f23e7783694da80f586c438833783337a1da2c`.
- Extractor bytes from exact committed Git object:
  `18dfded68e673ef8bf2d2c76a331d5bc6c7615845ecfac5400d5f79d77ac48a6`.

Window is inclusive `[8,0,17,9]`, all four native layers. Selected slots are
32,120,123,124,387: precisely the five raw owners of H/layer0/(16,1), each with
multiplicity1. That raw edge has cap4, usage5, reduction13 and real_cap6.
The model releases exact selected old STEP multiplicities, totaling51 weighted
planar occurrences: slot32 releases10, slot120 10, slot123 11, slot124 10 and
slot387 10. No selected contribution exceeds usage and no residual is clamped.
All five have current demand1 on every layer and native planar interval0–3,
which equals the model's allowed-planar-layer set. No extra restriction is
introduced by shrinking their layer intervals.

All selected terminal/access admissions are supported while the whole-inventory
join remains false;319 unrelated unsupported observations are disclosed. Each
selected published route passes full native pin connectivity and exact planar
STEP-support equality. Exterior route portions, including crossing edges, remain
frozen. Their boundary contacts induce **zero** multi-contact private exterior
components in this graph; none provides an invisible bypass of the cut below.

The validated graph has400 nodes,1020 edges,5 nets and10200 occupancy/flow
variables. There are no existing fixed-usage-over-capacity edges inside it.
Independent per-net BFS using residual edges sufficient for that net's demand,
all declared vias and its private exterior components reaches every required
terminal for each net individually. Thus single-net disconnection and trivial
fixed-overflow rejection do not explain the simultaneous UNSAT.

## Independent capacity-cut certificate

Partition **every layer** at x16|17. The left set contains all window nodes with
x≤16; the right set contains nodes at x17. Each of the five selected nets has a
required terminal on both sides:

| Slot / net | Left required coordinate/layer | Right required coordinate/layer |
| --- | --- | --- |
| 32 delaynet_3_clk | (15,9,1) | (17,1,0) |
| 120 cell_val[27] | (15,9,3) | (17,1,0) |
| 123 cell_val[31] | (14,9,3) | (17,1,2) |
| 124 cell_val[32] | (15,9,3) | (17,1,2) |
| 387 frame_strobe[0] | (9,0,0) | (17,2,0) |

Every connected net must occupy at least one edge crossing this partition. The
model charges distinct nets separately even if they share a physical edge. All
five require unit demand on every planar layer, so total required cut demand is
at least5. Same-coordinate vias never change x and cannot cross this partition.
No declared private exterior component crosses it.

There are exactly40 raw planar edges crossing the cut: four layers times ten y
coordinates. After exact release, **39 have zero residual capacity**. The sole
positive residual is `H_0_16_1`, from `p16_1_0` to `p17_1_0`, cap4, fixed_usage0.
Total available cut capacity is therefore4. Necessary condition5≤4 is false.
This independently certifies infeasibility of the supplied declared graph,
regardless of search budget or CP-SAT internals. The stored solution's generic
`infeasibility_independently_certified=false` field is unchanged; this report
supplies a separate explicit certificate, not an edited solver claim.

The following verifies the essential certificate using only the retained graph:

```python
import json
from pathlib import Path
g = json.loads(Path('build/corridor112_south/graph.json').read_text())
nodes = {n['id']: n for n in g['nodes']}
left = lambda v: nodes[v]['x'] <= 16
cut = [e for e in g['edges'] if left(e['u']) != left(e['v'])]
assert len(cut) == 40 and all(e['direction'] != 'via' for e in cut)
assert all(e['capacity'] >= e['fixed_usage'] for e in cut)
assert sum(e['capacity'] - e['fixed_usage'] for e in cut) == 4
assert len(g['nets']) == 5
for net in g['nets']:
    assert {left(t) for t in net['terminals']} == {False, True}
    assert all(v == 1 for v in net['track_demand_by_layer'].values())
    assert not net['frozen_exterior_components']
```

## Retained solver identity and limits

Graph-file SHA256:
`8c6a07d806c9535320b416ce89bd2e43e913c5c1e8306c2b482d65aeddd28847`;
validated canonical graph SHA256:
`7f49b0ddb0ea3976cdf4c7f4191f4099f1fd8a60da1a1037de251c4dfb73b8d0`.
Both independently match the solution's input/graph digests. Model-manifest file
SHA256 `5e5d0d45b886350549b00ab7939c236c62ba562d1ee3e8d40d7acb3e20d297da`;
solution-file SHA256
`509e8cd298450ed28b7251784079cd0ed13fd0bd0505fdb150f63ac4e2b1171a`.

Stored CP-SAT9.14.6206 status is INFEASIBLE, with no witness, wall0.0695563s,
deterministic_time0 and no branches/conflicts. This review does not rerun it or
interpret its presolve speed as a timing/performance claim. The independent cut
is sufficient to validate the declared-model answer.

Frozen exterior, other nets' fixed occupancy and the window boundary are
constraints of this question. Rerouting a different cohort, changing those
crossing contacts or using a wider window could change cut capacity or required
crossings. This result excludes a simultaneous local repair **under this exact
model**, even with its optimistic unlimited coarse vias. It does not justify
hardware changes, relaxed capacities, a whole-chip impossibility claim or
physical route acceptance. Native-input/physical/timing authentication flags in
the artifacts remain false and were not promoted by this review.

## Reusable cut checker independently reviewed

Subsequently reviewed `autonomy.capacity_cut.certify`, without modifying it.
No concrete false-certificate issue found. It validates the graph, partitions by
an explicit integer x/y coordinate, refuses any net-private exterior relation
straddling that partition, refuses unbounded crossing resources and separates
negative-residual cut violations from this demand-versus-capacity certificate.
For each net with terminals on both sides, minimum demand over **all** declared
layers is a safe lower bound on its necessary planar crossing consumption; using
an unavailable cheaper layer can only weaken the proof. Declared via edges are
co-located by graph validation and therefore cannot cross an x/y cut. Summing
residual capacities and per-net lower bounds is sound for union occupancy.

Independently executed the focused suite: **9 passed in0.12s**, no skips.
Recomputed `certify(graph, axis='x', coordinate=16)` and compared the entire
result to `build/corridor112_south/cut_certificate.json`: exact equality,5>4.
Certificate SHA256:
`c4ae0de72fa3700be4ef94d731d1aac1278fb66e07a5e58f0f92975be6a47746`.
Reviewed checker SHA256:
`f2549ba99070bdaff47e32fdb944d05a31002708e8f79f2ab466cd83bc93934a`;
test SHA256:
`b97d7ed43129f2167827f8a972ac94a15ed1c874f2a0b444913565bd40ea5113`.
No CP-SAT or EDA was invoked. Scope remains the supplied graph, not whole-chip
impossibility or physical signoff.
