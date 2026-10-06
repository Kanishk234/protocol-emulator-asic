# Resync physical screen and guarded routing plan (2026-10-06)

Source is successful main run37504886226 on6847566, artifacts `gds-drop-counter-bs-resync-37504886226` and exact matched `gds-drop-counter-timing-placement-37504886226`. Frozen base3393eea,2lanes/4units/U0full,20ns,56% density,GRT adjustment0.16,signoff constraints. Downloaded candidate's27tracked RTL/config/info files match the frozen base plus exactly bs_resync.patch. SRAM views remain frozen; source screen artifacts did not upload macro views.

| Fresh repaired metric | Baseline | Resync |
|---|---:|---:|
| Setup WS fast/slow/typical(ns) |0/0/0|0/0/0|
| Setup/hold violation counts, each corner |0/0|0/0|
| Hold WS fast(ns) |0.0360107|0.0379569|
| Hold WS slow(ns) |0.238266|0.227755|
| Hold WS typical(ns) |0.103103|0.100974|
| Slow slew violations |8|1|
| Fast/typical slew violations |0/0|0/0|
| Fanout violations, each corner |162|160|
| Capacitance violations fast/slow/typical |0/0/0|2/1/2|
| Instance area incl.SRAM(µm²) |508444|509241|
| Instance count |33169|33103|
| Final repaired global-route overflow |0|0|
| Final repaired routing demand |233872|243504|
| Final repaired routing usage |39.08%|40.69%|

Resync adds797µm² (~0.157% total area) and9632routing demand (~4.12%). The electrical results are mixed: slew improves but capacitance violations appear. The remaining reported slow slew violation is SRAM A_MEN (0.697599ns versus0.595200ns limit). A zero estimated setup result includes a zero-slack latch-to-latch worst report; it does not demonstrate positive timing margin or an extracted setup improvement. The candidate qualifies for a bounded diagnostic route under the existing setup/hold/antenna gates, not final signoff. No SRAM-buffer or CTS variant is combined with it.

## Prepared source validation

Existing gds-placement-route dispatch gains only bs-resync support. Before downloading any artifact, trusted frozen checkout plus named patch establishes SHA256fingerprints for every tracked source/config/info/macro file. The source run must be successful,on main,with exact run ID and correct workflow path. Downloaded files must match the independently prepared expected hashes; arbitrary RTL changes or accidental changes to other hardware fail validation. Existing clock/density/corner/constraint/state and antenna/fresh timing guards remain.

Route output records source_identity.json. Macro files are included in its artifact so extraction and GL can revalidate all fingerprints rather than incorrectly rejecting absent macro files (BUGS71). Historical unchanged-RTL artifacts without this metadata retain their existing guards. New source identity is validated before routing and downstream, and both downstream workflows require the route to originate on main. No official template job or main hardware changes.

Seventy-seven source/timing/route/GL/extraction helper checks pass. Three workflow files parse. A real-artifact source audit checks27files against the exact patch. The user approved CI/docs publication and routing launch; CI support is committed as f0ab242. Dispatch source_run_id37504886226/source_variantbs-resync after publication; successful routing automatically starts fresh extracted timing and matching22-case functional GL. Only those results can determine whether to adopt resync or form a combined candidate.
