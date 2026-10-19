# Independent actual native corridor export review — October 19

Reviewed actual hosted run
[39331845906](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39331845906),
attempt 1, exact source `6b19d036a8c4975a7381191f27dcafc2219ecfc5`.
Retained API identity `build/native112_identity.json` records completed SUCCESS
on `efpga` at that revision. Artifact root is
`build/native112_result/route_force_repair`; result SHA256 is
`129f0765d7f28d3b5b0df8d27f9a86278551402829c5e92870764c363a9f3a95`.
This independent review performed Python/file/Git-object analysis only, with no
EDA, dispatch, source edits, commits or physical promotion.

## Actual ledger result: confirmed

Reparsed and independently recomputed the native parser audit for all six
`<case>/replay/1-openroad-globalrouting/corridor-{initial,final}/native-corridor.tsv`
files. Every recomputed audit equals its retained result object, and every raw
file hash equals its recorded file hash. Each export contains 139,228 raw valid
H/V edges across four layers, a 179×98 grid, 3,659 live native nets and zero empty
slots. Every edge's raw usage exactly equals the summed **per-layer-weighted
STEP multiset**, with zero unexplained usage, excess contributions or modular
wrap matches. This includes both preferred/nonpreferred directions and the real
last-row H/last-column V boundaries.

All three initial exports and the unchanged default final export have identical
SHA256 `1859f6fdaffad9977ab4025867332a5835e68f50b86405719447b1b3c1aa07e6`.
Legacy final SHA256 is
`da188c381a712640e6be96aa00e12a7b4242e4c7960fe5ea17dfe7d1e5ae20b0`;
used-grid final is
`7118a4be802793e382ad9b6c7fff03a6b90d43fa188da1bfd55b60dd221b314b`.
Independently compared every raw edge's capacity, reduction and real-capacity
fields between each case's initial and final exports: all are unchanged, as are
the grid dimensions/origin/tile size.

## Keep the two overflow metrics distinct

| Actual case | Calibrated preferred reporting overflow | Raw both-direction overflow | Raw preferred per-layer overflow | Raw nonpreferred overflow |
| --- | ---: | ---: | --- | ---: |
| Default final | 121 | 121 | 19 / 40 / 18 / 44 | 0 |
| Legacy forced final | 132 | **134** | 15 / 52 / 24 / 41 | **2** |
| Used-grid candidate final | 139 | 139 | 15 / 66 / 26 / 32 | 0 |

The legacy difference is exactly two zero-capacity, unit-usage nonpreferred
raw edges (zero-based layer/grid indexing):

- `V, layer2, x4, y68`: cap 0, usage 1, reduction 0, real capacity 0; sole
  exported owner `net40`, multiplicity 1, layer demand 1.
- `H, layer3, x7, y61`: cap 0, usage 1, reduction 0, real capacity 0; sole
  exported owner `net178`, multiplicity 1, layer demand 1.

M1/M3 prefer H and M2/M4 prefer V. This explains the entire 134−132 difference
without modifying any capacity or inventing a final table. Preserve the legacy
checkpoint's **calibrated132** identity and separately name its **raw134**
both-direction observation. Do not relabel calibrated reporting132 as complete
raw H/V overflow. Both repair calls end GRT-0232 before a final native congestion
table; these final metrics are independently audited exported arrays.

## Multiplicity is real; initial union compatibility is false

The initial121 state has 34,244 weighted planar STEP occurrences but 34,243
weighted Boolean net-edge uses. There is one repeated net-edge pair:
`cfg_word\[23\]`, native slot 149, H on zero-based layer2 at `(13,30)`,
multiplicity 2 and layer demand 1. Raw usage reconciles with the multiset, not
with its deduplicated union. Accordingly the initial/default
`solver_union_accounting_compatible` flag is **false**. The CP-SAT model's
per-net union occupancy cannot silently replace this actual historical ledger.

The legacy final has multiset=union=34,193; used-grid final has
multiset=union=34,206. Both final snapshots have zero repeated net-edge pairs
and no zero layer demands, so their **accounting-only** union compatibility flag
is true. This does not make either regressing route acceptable or authenticate
solver terminals, allowed arcs, boundary releases, pin access or physical vias.

## Control and source scope

The result retains original exact initial segment SHA256
`19b14132c36cfa3e863edc34d0f23e7783694da80f586c438833783337a1da2c`,
unchanged for default final. Legacy final segment identity is
`805a3f9af53c39e0ff179433ee9bfd98d8f91d179f3bb303d71248e259e8c90d`;
used-grid final is
`10dffe113661bd822b02fa099b5c536bc87f310bb672999e09e7acac32296a46`.
These agree with the protected prior121/132/139 reporting checkpoints.
Case summaries retain 3,659 native routed nets, identical physical geometry and
census, unchanged calibrated capacities, native default GRT-0116 and repair
GRT-0232 failures. Required guide census is 3,691; both repair results still
miss exactly `cell_val\[30\]` and `cell_pad\[31\]`. Root separately reran the
portable full control/checkpoint validators; this report's independent work is
the raw parser/audit, raw resource equality and source/metric interpretation.

Independently read all three patch bytes from the exact source Git object and
matched their SHA256 to the result:

- D101: `72257372cd11e3ca3cdc9f53bbda13764f2dedf6bf79c2309f56f3006948c864`.
- D102: `629659917f0d5e052953e3407d7264772421e52030822d940b103db5a4e03dbd`.
- Native observer: `b7493c2fc4e4c7074363550fd0a059064ee739a4fc593f3eaf14081167a5ff65`.

The exact claim that **these actual native exports reconcile weighted tree-step
multiplicity with every raw 3D usage edge** is supported. A claim that the
initial121 state is already compatible with a Boolean union accounting model
is rejected by the actual repeated traversal. Native pin/terminal joins,
release-boundary/model assumptions and physical via feasibility remain separate
unqualified gates. All cases retain `native_repair_passed=false`; result-level
`physical_acceptance=false`. No export or collector success is a routing win.
