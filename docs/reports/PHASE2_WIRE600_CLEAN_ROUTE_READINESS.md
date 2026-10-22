# Clean wire600 preparation and routing continuation

The complete 2-lane/4-unit/U0-full/SRAM design remains at 20 ns in 6x4 tiles.
[Clean reproduction 39718836864](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39718836864)
passed from fresh RTL synthesis without downloading a source checkpoint. All eight
original reviewed source hashes reproduce exactly. The repaired result uses the
same 73 identity buffers and two equivalent strength substitutions as the passing
checkpoint screen.

| Preparation measurement | Result | Requirement |
|---|---:|---:|
| Slow capture setup reserve | 3.871081 ns | ≥3.5 ns |
| Fast hold slack | 0.125034 ns | ≥0.050 ns |
| Actual slew/cap/fanout violations | 0 at all corners | 0 |
| Antenna nets/pins | 0/0 | 0/0 |
| Maximum slew reserve utilization | 44.9812% | ≤45% |
| Maximum capacitance reserve utilization | 42.53% | ≤45% |

Setup WS is reported as 0 at every corner; this is not positive global setup
margin. Guides exist for all 33,937 signal nets but do not prove detailed-route
completeness. The slew reserve passes narrowly. Phase 2 and official signoff
remain incomplete.

## Evidence binding

Run head: `bab5e46186cd8aa1791c5d913d437a271cc89442`.
Full artifact: `wire600-clean-evidence-area1-39718836864`, ID12403112336.
Gate artifact: `wire600-clean-gates-39718836864`, ID12402557245.
The reviewed final preparation netlist SHA256 is
`01397ef7c91e999d144d9ebe346f96de4c661bbf509b7fb0e71a49ec9a8eed57`.

The tracked `scripts/ci/fixtures/wire600_selective/clean_route.json` binds 244
files covering the physical views, audited state, source hardware/constraints,
repair proposal/execution, all-corner report readbacks and reproduction receipts.
Mutable generated configs unrelated to the bound source recipe are excluded.
Downloaded raw evidence remains outside Git. Independent local re-evaluation of
the actual reports passes the preparation gates and full repair topology audit.

## Next verification

- `gds-wire600-clean-route` downloads only this reviewed clean result. It validates
  run provenance and hashes, independently audits topology and antenna readbacks,
  then freshly measures all three corners, capture reserve, electrical reserves,
  antenna and guide coverage. A failed preparation gate prevents detailed routing.
  It repeats neither electrical edits nor global/timing repair. Stock detailed
  routing must finish with zero routing DRC; connectivity audit and fresh
  extraction then require nonnegative setup/hold, fast hold ≥50 ps, zero actual
  electrical violations and zero antenna violations. This is experimental
  physical evidence, not the official GDS/LVS/precheck flow.
- `l3-wire600-clean-gl` independently replays all 22 expanded protocol cases on
  the exact preparation netlist, using pinned Icarus 13 and SRAM/cell models.
  It is functional simulation only. A passing result cannot substitute for
  replay on the eventual final routed netlist.

Ninety focused regression checks pass, including wrong provenance/bytes, missing
clean reproduction claims, source validation blocking routing, original screen
profiles, workflow shell/Python parsing and unchanged pinned source inputs.
No main RTL/config/template changes or phase checklist boxes accompany this step.

## Routed result and targeted follow-up (2026-10-22)

[Route39806020090](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39806020090)
completes0DRC but fails extraction: slow setup−1.467647ns, fast hold+0.118720ns,
slew/cap0, four fanout failures. DRT adds42diodes only; eight added loads are
net8721:+4,21968:+2,lane0slotwdata13:+1,net8083:+1. This confirms why legal
screening fanout does not guarantee legal final fanout. Protocol run39806026713
passes22/22 on the preparation netlist, not the final routed result.

D-106 tests eleven functionally equivalent strength changes and eight extra
identity buffers on the four diode-sensitive sources, from fresh synthesis.
The same old extracted SPEF with a freshly reloaded modified netlist gives slow
capture+0.155355ns,typical+7.429067ns,fast+11.656955ns and fast hold+0.118720ns.
Global setupWS0 remains distinct from positive global margin. This fixed-wire
sensitivity excludes new branches and physical movement; it is not a signoff
pass or a prediction guaranteed to survive routing. Incremental area before
native repair is163.296µm² versus the prior passing profile. Canonical totals
are81buffers/13strength changes/250sink rewires/59nets. All gates remain fixed.
Raw diagnostic receipts/proofs remain under/tmp/tripwire-wire600-fixed-selected11
and/tmp/tripwire-wire600-strength-proofs; report/database artifacts remain outside
Git. The separate gds-wire600-extracted-clean workflow stops before DRT and must
pass all preparation checks before any routing continuation.

## Strength-profile clean screen passes (2026-10-22)

[39824026639](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39824026639)
passes fresh synthesis reconstruction and all preparation gates for81buffers,
13sizes and59target nets. Slow capture3.735021ns, fast hold0.125034ns, setupWS0,
zero actual electrical/antenna counts, and conservative electrical reserves pass.
All33,945signal nets have routing objects. This is estimated preparation evidence;
new extracted results and exact-netlist protocol replay remain required.

Separate gds-wire600-extracted-route and l3-wire600-extracted-gl continue only this
clean run. Explicit source/root/proposal/audit overrides retain the older profile
unchanged and prevent cross-use of its measurements/netlist. Routing repeats no
edits or global repair; fresh strict preparation checks still precede DRT and
all-corner extraction. Replay runs all22cases on the new preparation netlist;
a later replay on the final routed netlist remains necessary. No main hardware,
constraints, acceptance limits, template jobs or phase checklist boxes change.

The new source binding is scripts/ci/fixtures/wire600_selective/extracted_route.json:
244files from clean run39824026639 at808223d2396f3e981930389088b7bd0e55885825.
The final preparation netlist SHA256 is
2c40479252b0411f115ffb63eb23e97e82e90f9efef76dd52704d6a116a29f1a.
Independent actual-artifact connection audit and report-based preparation gate
recomputation pass.102focused checks pass, including unchanged old-profile
behavior, explicit new-root use and wrong-source/receipt rejection. Full evidence
is under/tmp/tripwire-extracted-clean-full-39824026639 and remains outside Git.

## Targeted route nearly closes setup; one-cell margin follow-up

[39837795296](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39837795296)
finishes detailed routing/extraction with routeDRC0, antenna0/0, all electrical
counts0, and fast hold+0.104631ns. Slow setup remains−0.006391332ns, which still
fails. Both reported violations share26761/mux2_1. Preparation replay39837799952
passes22/22 on the81buffer/13size netlist; final-route replay remains required.

D-107 changes just that mux to mux2_2, keeping every connection and prior repair.
Its area increment is1.8144µm². A fresh netlist reload with the exact latest
extracted SPEF and constraints reproduces baseline timing, then reports slow
capture+0.093824ns and unchanged fast hold+0.104631ns. These are diagnostic results,
not actual re-placed/re-routed measurements. The new clean screen must pass all
unchanged gates before another route is authorized. Canonical totals81buffers,
14sizes,250sink rewires,60nets. Mux output equivalence passes all3corners, wrong
select wiring rejects, full source topology/Tcl preflights pass,107checks pass.
Raw receipts/proofs stay under/tmp/tripwire-mux-margin-fixed and
/tmp/tripwire-mux-margin-proofs-v2. All source hashes are in the frozen review.

## Single-mux preparation clears screening

[39856540600](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39856540600)
passes fresh source reconstruction and all strict preparation gates for81buffers
and14sizes. Slow capture3.735021ns, fast hold0.125034ns, all actual electrical and
antenna counts0, and all conservative reserves pass. The headline estimates match
the prior candidate; only fresh detailed routing/extraction can demonstrate the
intended improvement over the previous−6.391ps result.

The next separate continuations are gds-wire600-mux-margin-route and
l3-wire600-mux-margin-gl. Both bind the successful run39856540600 and its exact
new netlist. They preserve source topology validation, fresh preparation gates,
stock DRT/extraction and all22protocol replay cases. No new repair is applied
during routing, no acceptance limit changes, and final-route replay/official
fullGDS signoff remain required.

Independent full-artifact review confirms26761remains mux2_2 after native repair;
all14reviewed strength masters remain present. Final preparation netlist SHA256:
654bae23a2ace5c8c2275ce2be4b8dd55d071916e75914d9d74be8f1b3aefaca.
The mux_margin_route.json fixture binds244source/physical/measurement files.
Actual edit topology and recomputed strict preparation gates pass.111focused
checks pass, including both older profiles and explicit single-mux source binding.
Full evidence stays under/tmp/tripwire-mux-clean-full-39856540600 outside Git.
