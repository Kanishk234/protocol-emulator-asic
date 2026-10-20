# Independent global coarse aggregation review — October 19

Read-only source/test review of `tools/autonomy/coarse_global.py` and its focused
fixtures. No concrete blocker found for the explicitly restricted unit-demand,
all-native-layer, unlimited-coarse-via model. No actual graph solve, EDA, source
edit or workflow dispatch was performed by this review.

## Aggregation and accounting are sound within the declared premise

Admission requires the full raw usage ledger and selected coarse terminal/access
join. Each selected FrNet must have demand exactly one on every native layer and
planar layer interval0 through nl−1. Nonunit or layer-restricted nets reject; the
aggregation does not silently generalize to them. All old selected planar STEP
multiplicities are removed across the **full** raw graph before constructing the
new cohort model. Negative residual use rejects rather than clamps.

For each original physical edge, available capacity is independently
`max(0, raw_capacity − fixed_other_usage)`. The code then sums these nonnegative
availabilities across layers for each same-coordinate planar link. This is not
`max(0, sum(capacity − fixed))`: an already-overfull layer cannot provide credit
or cancel another layer's actual spare resources. Both H/V resource directions
remain represented. A layer with fixed overflow contributes zero new capacity.

With unit demands, every selected net-edge occupation is one interchangeable
unit, and all selected nets permit all layers. Explicitly unlimited same-coordinate
vias permit layer changes independently at every graph vertex. Under these
premises, summing parallel-layer residual capacities is an exact aggregation of
that **coarse relaxation**. The aggregate graph's `vias=forbidden` describes its
single collapsed layer, not an assertion that physical/native vias disappear;
the provenance, omissions and scope explicitly state unlimited coarse vias.

Positive-residual connected components without any selected pin coordinate are
removed because they cannot participate in any selected terminal connection.
Every selected pin coordinate seeds the retained search, including isolated
pins; disconnected required terminals are not silently dropped. Node/edge/net
variable limits remain hard bounds; the code does not raise them to fit a model.

## Constructive original-layer verification

The proposal checker reconstructs the complete model from the same supplied
snapshot/state/cohort and requires exact equality, then independently validates
the solver's coarse union-occupancy/connectivity witness. It allocates each
selected net's occupied coarse edge to one **original** layer with available
residual capacity, decrements that layer's availability and increments that exact
raw resource's proposed use. Thus an aggregate witness is not accepted merely
because a collapsed-capacity inequality passed.

For each net, explicit adjacent-layer via stacks connect all allocated incident
layers and original native pin layers at each coordinate. A separate 3D BFS
checks all native pins and all proposed links are connected. Multiple pins at
the same x/y may share a collapsed terminal only because the verifier explicitly
constructs the declared unlimited via stack between their native layers.
No physical via/cut capacity, enclosure, spacing or obstacle proof is implied.

The final per-resource guard is
`proposed_usage <= max(raw_capacity, fixed_other_usage)`.
It is sound for **no added overflow beyond fixed background**: if fixed usage
is within capacity, added selected routes may not exceed capacity; if fixed usage
already exceeds capacity, no selected unit may be added there. The guard does
not increase raw capacities or forgive a new overload. Existing fixed overflow
is separately measured and retained. Therefore a successful witness can reduce
original overflow while still leaving a nonzero fixed-background total; it must
not be described as a zero-overflow whole-chip route. The returned original,
fixed-background and proposed raw-overflow metrics keep this distinction visible.

Input manifest hashes identify supplied snapshot/state/source/cohort. Mutable
parsed objects and their recorded SHA fields are not independently authenticated
by this module; the caller must bind them to verified immutable hosted artifacts
and committed generator bytes. Native input authentication, physical/timing
acceptance and native handoff remain explicitly false.

## Independent validation

Executed in the project venv:

```sh
PYTHONPATH=tools pytest -q tools/autonomy/tests/test_coarse_global.py
```

**13 passed in0.11s**, no skips. Fixtures cover original-layer allocation,
fixed background overflow retained without credit, exact old repeated traversal
release, rejection of nonunit demand/layer restrictions/unsupported admission,
hard bounds, modified model and disconnected witness rejection, and no solver
invocation in builder/verifier. The fixed-overflow fixture explicitly assigns
new selected demand to another original layer and checks native pin via stacks.
Three additional independently inspected fixtures cover two selected nets sharing
aggregate capacity while being assigned distinct original layers, pruning only
components with no selected pin, and retaining isolated selected terminals so a
disconnected witness fails. These fixtures do not constitute actual WARP routing
or physical qualification.

Reviewed SHA256:

- Module: `adb4fb8685cf782605a93d6dad1cd6ed7cc2dc07e12e02bd1e3b911948b15a67`.
- Tests: `d018aff5fae7d33a5bf061652dd62cea53c2e0dd2df2237e95af9481c506b6de`.

Actual application still requires source-bound raw/terminal artifacts, exact
cohort/input/model identities, independent constructive witness checks and the
reported remaining fixed overflow. A relaxed witness is not a native OpenROAD
route, guide handoff or physical/timing signoff result.
