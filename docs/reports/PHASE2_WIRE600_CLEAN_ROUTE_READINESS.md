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
