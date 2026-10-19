# Native observer qualification, October 19

Build39304728263 at75d4378 succeeds, including linked Tcl API availability
and rejection before initialization. The read-only patch does not itself
qualify native resources, terminals or the exact solver model.

First qualification39331153087 at675b659 fails as infrastructure: all three
control cases finish before host accounting, but root-owned0600 native TSV
files cannot be read by the unprivileged collector. Upload also fails EACCES;
GitHub API lists no artifact. No raw ledger result can be recovered from this
run. The failed status is retained and logged as BUG102.

Fix6b19d03 changes the container Tcl wrapper only: after successful export,
require the known TSV to be a regular non-symlink file and set that file0644.
Native exclusive0600 creation remains unchanged; failed partial files and
unrelated files remain private.90 runner tests pass, including actual Tcl
permission/error/symlink fixtures. No C++ rebuild or routing-policy change.

Retry39331845906 at6b19d03 reuses build39304728263. It must reproduce exact
121/default,132/legacy and139/used-grid controls before auditing six raw TSVs.
The retry includes source patch metadata for strict portable native auditing.
Results remain pending. After download, separately require byte-identical
three initial snapshots and default final, reconcile every raw edge against
weighted route-step multiplicity, and inspect scalar/per-layer/soft-NDR state.
Physical pin joins, endpoint via access, exterior connected components,
physical legality and timing remain separate gates even if accounting passes.

## Actual corrected outcome

[Retry39331845906](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39331845906)
completes SUCCESS at6b19d036a8c4975a7381191f27dcafc2219ecfc5, attempt1.
Downloaded original result SHA256:
`129f0765d7f28d3b5b0df8d27f9a86278551402829c5e92870764c363a9f3a95`.
Separate API identity, exact Git-object patch hashes, all control/observer
checks and six raw exports pass the portable `--candidate --native-corridor`
audit. Raw accounting has zero mismatched edges, zero unexplained usage,
zero excess contributions and zero wrap discrepancies on every one of139228
valid H/V edges in all six states. Each snapshot has3659 live nets and94
native clock nets. No physical or timing acceptance follows.

The three initial snapshots and default final are byte-identical with SHA256
`1859f6fdaffad9977ab4025867332a5835e68f50b86405719447b1b3c1aa07e6`.
The independent checkpoint checker verifies that stronger native-state
identity, including IDs, coarse pins, costs and resources. Physical pin joins
and endpoint access remain unauthenticated.

| Metric | Default initial/final | Legacy repair final | Used-grid repair final |
|---|---:|---:|---:|
| Existing calibrated preferred reporting overflow |121|132|139|
| Raw both-direction overflow sum |121|134|139|
| Raw ledger mismatched edges |0|0|0|
| Repeated same-net planar edge pairs |1|0|0|

The legacy extra two raw units are nonpreferred V(layer2,x4,y68) and
H(layer3,x7,y61), each capacity0/usage1. Layer indices are zero-based.
Do not replace historical preferred132 with an unlabeled134 or call132 a
both-direction total. Neither repair has a final native postrepair table or
physical acceptance; this refinement strengthens rejection.

Initial net `cfg_word\[23\]`, slot149, traverses H(layer2,x13,y30) twice.
That edge has capacity11, usage8, reduction6 and real capacity17; it is not
itself overflowing. Initial weighted multiset usage34244 versus union34243
therefore blocks equating the whole native initial ledger to the solver's
per-net union model. Preserve multiplicity when releasing native routes;
do not deduplicate the source snapshot to force compatibility.

## Actual cost hypothesis test

All four soft clock nets have scalar1/layerdemands(1,1,1,1) initially. Both
repair finals reset their scalars to2 while layer demands remain one:
`clk`, `clknet_0_clk_regs`, `delaynet_0_clk`, `delaynet_3_clk` (slots0,3,29,32;
OpenDB IDs242,3065,3090,3093). The raw3D ledger still reconciles exactly.
The scalar-substitution hypothesis falsely predicts positive residual on200
legacy edges and198 rebuilt edges; actual residual is zero throughout.
Reject that explanation for a 3D accounting error. Its effect on2D negotiation
is unmeasured and is not a proven cause or fix for failed routing.

Local autonomy suite now381 executed passes/zero skips, strict XML checked.
Actual ignored audits are build/native112_portable_audit.json,
build/native112_checkpoint_audit.json and build/native112_costs/. Raw artifacts
remain in CI and ignored build/native112_result/.

Next work is a separately reviewed read-only physical-pin/tree-access observer
and bounded exterior-connectivity adapter. The exact solver remains qualified
on declared graphs, not yet applied as an authenticated WARP repair. Preserve
G1 and original133/best121; no route-improvement claim.
