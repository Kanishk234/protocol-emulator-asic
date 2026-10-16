# Controlled unchanged-net repair: rejected regression

Hosted collection
[38948702750](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38948702750)
at `f4336097ca5d5c351370ee54f9540ddb711338c0`, attempt 1, completes the
bounded experiment. **Native routing still fails, and final observed overflow
increases from 121 to 132. Preserve the 121 control.** Collection success means
the diagnostic outputs passed their checks, not that the chip routed.

The experiment uses the D-100 corrected router build `38851788423` against
pinned upstream `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`. It reproduces
the original 15-iteration routing policy before explicitly rerouting the
unchanged southern pair, with up to four congestion expansions and no placement
fallback. It retains the original geometry and routing capacity policy.

## Independent checks of downloaded output

Both stages retain 3,659 native route nets with identical names. Physical
geometry and connectivity census files match byte for byte before/after in
each stage and across the two stages. The default stage changes no route
geometry; the forced stage changes 440 normalized per-net route geometries,
including both `cell_pad[31]` and `cell_val[30]`. The expanded repair therefore
is not a two-net-only geometry change, even though those are the two initial
seed nets.

The independent audit compares every reporting capacity across all 69,064
canonical interior records and all 550 real preferred boundary edges. They
are unchanged. No negative usage appears. Boundary overflow is zero in both
stages, initially and finally; the forced stage's boundary usage changes, so
its boundary-file hash changes despite unchanged capacities.

| Layer | Default/control observed overflow | Forced final observed overflow |
|---|---|---|
| Metal1 | 19 | 15 |
| Metal2 | 40 | 52 |
| Metal3 | 18 | 24 |
| Metal4 | 44 | 41 |
| **Total** | **121** | **132** |

The default native final table independently matches 121 and its layer
distribution. **There is no post-repair native final table.** The forced call
throws `GRT-0232` before `finishGlobalRouting()` prints that table; the only
table earlier in the log belongs to the initial 121 control. The final 132
value is recomputed from the exported reporting grid, including the measured
zero-overflow boundary, and must not be described as a native final-table
result. Both native Tcl return codes are 1: default `GRT-0116`, forced
`GRT-0232`. The forced result has missing guides for the two seed nets; it is
not a complete accepted routed design.

Incremental per-pass scalar logs use native touched-edge sets, not the
independent complete reporting-grid census. They do not establish full-chip
overflow or a saved intermediate improvement. Five routing passes execute:
the seeded pass and four expansion passes. This campaign has no per-pass full-grid and expanded-membership
snapshots. A further observation should collect those before selecting another
routing intervention. The final outcome does not justify increasing budgets,
moving cells, changing capacities or replacing the protected control.

## Provenance and scope

Artifact: `controlled-native-pair-repair-38948702750`.

- Result JSON SHA-256: `0f55699f33001185e930a1b6f9b8bde73f1a9e17f773fd6bc0ab86fdfe147a64`.
- Patched binary SHA-256: `780f315649499bcba681e0fb2245dbe7d7b4b867c565af800209e3547ebbe70a`.
- Patch SHA-256: `73e5588175fadd8d08793f19c09d4aa2b50c744d0c2b5229c9e503c592fc8aef`.
- Initial/default segments: `19b14132c36cfa3e863edc34d0f23e7783694da80f586c438833783337a1da2c`.
- Forced final segments: `805a3f9af53c39e0ff179433ee9bfd98d8f91d179f3bb303d71248e259e8c90d`.
- Forced final interior grid: `6a648ef741a2bb9071f5bcd33c4eccd9dd0be8fe813770ba903f611ecc7b1c03`.
- Initial/default boundary grid: `20f6e7ba7e8ed300215e48292eff30b04cdc32b9f7be7e35a1cbe67dd75529e9`.
- Forced final boundary grid: `24a84793cd7507483da418601a676c21bb497c3c8ee8e321cf2f8ebbe16efc53`.
- Unchanged geometry: `27523c434dc0e91e0c39a380519c8e9f6bf4dcc2db3998023d924846cd595772`.
- Unchanged connectivity census: `3d8a7d032a84720fa1b4e5a243cccadde5678630f0067d846f25352ba4905aa3`.

Reporting capacities include the native exporter's blockage encoding. This is
identity of the observed interior and real preferred boundary reporting
capacities, not a new raw H/V array export. The final native table, when
available, scans all raw edge positions; it is deliberately not inferred from
the incremental touched-set scalar. The native GCD API regression passes in
this job, but that establishes exercised API behavior on a noncongested fixture,
not chip routing closure. No detailed-routing, physical timing, equal-area,
SDF, silicon or board acceptance follows. The independent audit executes only
Python/file analysis, not EDA.
