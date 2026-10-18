# Feasibility of recovering matched G1 primitive timing views

A bounded original-control rebuild is feasible to prepare: the committed tile
sources, original tool recipe and original embedded tile geometry survive.
It is **not yet a recovered timing view**. A rebuilt netlist must match the
committed primitive netlist, and rebuilt geometry must match the primitive
cell embedded in frozen G1 before fresh parasitics can refresh its tile-boundary
cross-check. Determinism has not been established by running that experiment.
No EDA or new artifact search was launched for this feasibility review.

## Existing archive result remains exhausted

`reproduction.md` records the October5 search of historical G1 run36342012141,
artifact10939348491. Its909 members contain chip-level SPEF, not the missing
PRIM2T2S tile netlist/parasitics pair. The retained inventory
`build/g1_timing_archive_audit_20261005.txt` confirms that scope. Newer local
tile experiments do not match the committed netlist and are not substitutes.
This report does not repeat those searches or qualify those experiments.

## Surviving original controls

The G1 primitive netlist and fabric GDS entered the repository at
`7b6a6891071f17b85fff10d320b96457c1d8acfd` and are byte-identical at frozen G1
`3047dea08566bedaed9d061c0ce2313c92f4a193` and in the inspected checkout:

| Committed view | SHA256 |
|---|---|
| `macro/warp_g1/tiles/PRIM2T2S.nl.v` | `13fec76424949b0d25789ca8d0721b74d4acdba5ff93eaeb99dfb4d412f6a170` |
| `macro/warp_g1/warp_g1.gds` | `f437c3cb61d37a9b38edec45b396a7baa6fdcee6f525b5990c83292cfe86a1fc` |
| `macro/warp_g1/rtl/PRIM2T2S.v` | `90d0c6dd588cf0ab1d1cfbd0c2071dff6df74416aa6403c1fefc5c3237c4e974` |

A read-only standard-library GDS record inventory finds a structure named
`PRIM2T2S` and one structure reference to that name in the committed fabric
GDS. Thus the reference geometry is not lost merely because no separate tile
GDS is committed. This is a hierarchy inventory, **not** an executed geometric
XOR or verification of the reference's polygons.

Original design inputs are committed under `arch/tiles/PRIM2T2S/` (tile CSV,
switch-matrix list and config), `arch/prims/` (generic primitive RTL),
`scripts/gen_prim_tile.py`, and `macro/warp_g1/rtl/` (generated tile/config/
switch-matrix RTL). The tile configuration uses the original FABulousTile
flow, its original buffer insertion/substitution policy, `AREA 2` synthesis,
and a null dedicated clock port; it must not acquire the later C2 redesign
or a new clock/timing policy. A content comparison against7b6a689 finds no
changes to the relevant committed source/config/primitive/physical-patch
contents; the generator's executable bit differs.

`spikes/tile_cmos5l/run.sh PRIM2T2S` describes the original local recipe:
copy project tiles/primitives into an isolated tile-library build, apply the
CMOS5L patch, and run the pinned Nix FABulousTile driver. Its normal work path
is shared with old experiments and it deletes/replaces that tile directory.
Do **not** execute it in the existing historical build tree for recovery.
Use a separate exact source export and separate work directory instead.

The physical source pins are available:

- FABulous tile library `7999e5a91dab77357fe9d401b6dfb0758f438bf1`.
- CMOS5L patch SHA256 `1d697a156809c8306e628ed42e79028280cb71119a7929760bda8c5d20055883`.
- Unmodified library flake.lock SHA256 `aaef0ac1bac971f54fe44565fa12284e18dc88718d153a2f92201e957070084f`.
- That lock pins FABulous plugin `dcc038217472822330b33f61fadbc06e0c3cc96d`,
  LibreLane `69b2067bd2b5eb89b84649b76e9edaa9e51e6735`, and nix-eda
  `8f990fb77529c09e540e453cd836af9930ec58db`.
- PDK `2bbec755dc67ca3db0261c3d6163e15735d66710`.

The named tool versions in `docs/VERSIONS.md` are a human summary; the exact
lock/derivation and resulting executable hashes must bind a recovery run.
Use the original stock tile toolchain, never the currently experimental
force-routing binary. The generated/resolved config must be retained with
all substituted steps and effective defaults rather than assuming committed
YAML alone proves the original physical policy.

## Existing hosted capability and its limit

There is no current workflow that directly rebuilds the original G1 primitive
tile from that committed recipe. `tile_harden.yaml` and `tile_preflight.yaml`
are owned workflows, but their Python adapters authenticate a specific C2
source archive, mapped netlist, interface and replay policy. Changing an input
archive string does not make them an original-G1 rebuild. `native_final_tile`
also targets C2. Their workflow names must not be presented as existing G1
recovery support.

The router build workflow demonstrates hosted availability of the original
pinned Nix flake/stock tools; the clean reproduction workflow demonstrates
current compiler/RTL reproduction. Neither produces the missing original tile
physical views. A separate, bounded, manually dispatched original-control
workflow would need to wrap the isolated stock FABulousTile recipe and retain
its results. That adapter is not implemented or dispatched by this report.

## Required matching gates before using fresh SPEF

1. **Source and recipe identity.** Export the chosen exact G1 source revision;
   hash every listed tile/primitive/generated RTL/config/patch input, original
   Nix lock, PDK/rules and actual tool binaries. Retain full resolved config,
   command, thread/seed settings and the completed stage/view manifest. Do not
   assume identical nominal seeds guarantee deterministic placement/routing.
2. **Fresh final netlist identity.** Require byte equality of the completed
   fresh PRIM2T2S final netlist to the committed hash above. A mismatch rejects
   recovery. Do not force a pass by substituting the committed netlist into a
   different physical result. Even equality is only the first matching gate.
3. **Original embedded geometry identity.** Read the committed G1 macro GDS,
   select its PRIM2T2S structure and complete recursive dependency closure,
   and compare it with the fresh tile in local coordinates. Normalize database
   units exactly, hierarchy transforms, polygon ordering/fracturing, paths and
   overlap unions. For every layer/datatype require an empty exact polygon XOR;
   retain all compared layer inventories and nonempty-reference checks. No
   coordinate rounding tolerance, ignored layer, new obstruction or waived
   difference may turn a changed layout into a match. Compare bounds and all
   pin/text labels and their transforms separately; polygon XOR alone ignores
   text. Existing repository KLayout Region/XOR code provides a pattern, but
   this complete tile comparator has not been implemented or executed.
4. **Bind the reconstructed electrical views.** Retain fresh final ODB, NL,
   GDS, LEF, extraction rules and SPEF hashes from the same completed flow.
   Establish that the geometry being compared is the geometry represented by
   the extraction input, with original standard-cell/pin/layer definitions.
   Audit actual SPEF net/pin names and parasitic annotation coverage against
   that fresh NL; establish the extraction's connectivity/port correspondence
   rather than relying on filename equality. Any LVS/correspondence limitation
   must be explicit. Netlist equality plus an unrelated GDS file is not a
   matched-view proof.
5. **Only then repeat the scoped timing cross-check.** Reuse the documented
   tile-boundary clock/input/output constraints and compiler timing-model
   comparison, with named library and RC corner. Retain actual reports and run
   identity. This is a new extraction of matched geometry, not recovery of the
   missing historical SPEF bytes, and not configured full-chip/SDF signoff.

`tools/timing/tile_check.sh` currently requires NL/SPEF and a matching committed
netlist, but it does **not** implement the geometry/view-binding gate above.
It must not be used alone to certify a rebuilt SPEF as frozen-layout timing.
A failed geometric match leaves the historical reproduction gap open; the
result can only be labeled a distinct experimental tile.

## Practical next decision

The source and reference layout are sufficient for one controlled recovery
attempt, subject to the matching gates. The immediate blockers are an absent
original-G1 hosted adapter/comparator and unproven deterministic physical
reproduction, not missing Verilog or permission to change frozen hardware.
Prepare and review that concrete adapter/comparator before spending a hosted
hardening. Do not perform a seed/tool/version sweep to chase a layout match.
If the single original-recipe rebuild differs, retain the mismatch and reassess
reconstruction from the original geometry rather than treating a new layout's
SPEF as old evidence.

No source, architecture, frozen macro or timing contract was edited. No phase
box is ticked, and no matching-geometry, parasitic or timing pass is claimed.
