# Combined host/IDLE detailed-route diagnosis

[Diagnostic 42433571153](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/42433571153) completes after iteration 42, retaining a detailed ODB/DEF/netlist and per-iteration spatial reports. Its success qualifies evidence capture only. The original estimated screen remains green; final route DRC, extracted timing, antenna and official GDS qualification remain open.

## Measured result

There are 96 markers: 57 Metal2 shorts, 11 Metal3 shorts, four Metal4 shorts and 24 Metal2 spacing markers. Their boxes fit within x=512.06–718.18 µm, y=311.915–377.26 µm. They involve 46 distinct source-net pairs; multiple overlapping markers can describe one local conflict. All 46 pairs remain in iterations 40, 41 and 42. Neither manual detour net (`net1380`, `_19607_`) appears in the final marker set; this does not rule out indirect effects.

The largest net contributors include net12641 and net1283 (nine markers each), net3501/net4049 and lane1 output-token bit13 (seven each). Placed endpoints include short local two-pin nets as well as buffered branches, so long-wire splitting alone is not an adequate diagnosis. The SRAM origin is (12,40) µm; the marker rectangle is not its origin. Component origins are not actual pin locations.

A read-only standard-cell LEF/DEF overlap calculation gives approximately73.2% known-cell footprint occupancy over x=500–750,y=300–400µm. Fifty-micron bins range from57.0% to89.1%; adjacent bins can be denser. This partial footprint calculation excludes unmatched masters and routing obstacles and is not proof of sufficient pin access. It does not support describing the entire band as uniformly full. Previous hotspot experiments in PHASE2_REPAIRED_ROUTE_AUDIT.md also encountered this region; their global-route reservation trials introduced timing/antenna regressions and should not be blindly repeated.

## Bounded repair from saved detailed wires

The exact pinned engine offers an alternative to another full route from global guides:

- [io.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/io/io.cpp) imports existing dbWire segments and marks the net as having initial routing.
- [FlexDR.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/dr/FlexDR.cpp) selects incremental mode for the first three initial passes when routed nets exist; subsequent passes use the normal DRC search/repair strategy. This restarts the strategy from saved wires, not from iteration43 or internal worker state.
- [FlexDR_init.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/drt/src/dr/FlexDR_init.cpp) avoids reinitializing already-routed nets during incremental initialization. These source observations justify a trial; they do not guarantee a clean route or limited wire changes.

Separate gds-host-idle-drt-repair restores the original frozen source and exact green checkpoint and repeats all independent coverage and fresh pre-routing gates. It then verifies the full diagnostic ZIP digest, metadata and seven selected file hashes before loading the saved detailed wires. Before repair, source placements and mapped logic must equal the green checkpoint. Inherited SPEF/SDF/Liberty views are cleared from the routed input state.

Native DetailedRouting is bounded through iteration12 (indices0–12), with per-iteration reports, four threads and a120-minute step cap. Subsequent antenna-repair loops are disabled only in this diagnostic. No placement, logic, clock, area policy, signoff constraint, routing technology or acceptance gate changes. The output must retain identical placements and mapped logic; it records residual markers and explicitly refuses all signoff/official qualification claims, even if the marker count is zero. No wire-reset/global-routing command is added. Main source/config and official workflow jobs remain unchanged.

48 focused tests, actionlint, shell syntax and ten embedded Python programs pass. Tool/helper tests validate source tampering/provenance/path refusal, clearing stale timing views, immutable config and fixed20ns constraints; they are not native routing evidence.

If markers decrease, inspect spatial changes before deciding whether further repair is justified. If the strategy plateaus again, use saved layouts to plan local pin-access/placement relief and require a new strict screen before routing that modified placement. A zero-marker result still requires antenna/connectivity, real extracted all-corner timing/electrical checks, routed full protocol replay and official-compatible source/config reproduction before unchanged official GDS/precheck.

Compact measured evidence: spikes/phase2_stock_flow/host_idle_drt_hotspot_42433571153.json. The source manifest binds artifact13605087039 (336453219bytes), SHA256 b22d007b0e9976361e5812d1c067cb34098380c5cd335b30d2e48160ff622dfc. Local ranged extraction independently verifies individual entry CRCs; whole ZIP verification is performed by the workflow before restoration. Raw files stay in CI artifacts and /tmp.
