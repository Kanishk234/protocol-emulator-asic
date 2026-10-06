# Phase 2 exit evidence audit

Audit against `docs/design/phases/PHASE2_RTL_CORE.md` and D-049 on 2026-10-05. This does not tick, revoke or reinterpret checklist boxes. Historical passes stay historical; each new physical candidate needs matching evidence.

| Requirement | Existing evidence | Remaining action |
|---|---|---|
| Area estimate and budget decisions | Estimate, D-038–D-040; R4 placement instance area 508,444 µm², 56.34% core | First unchecked exit item. Obtain successful physical evidence for selected candidate and separately agree final resource counts/spec change; D-049 floor approval is not adoption of 2 lanes/4 units. Gross utilization alone is insufficient. |
| Modules and lint | Candidate 3393eea, lint 36799356097, historical synthesis checks | New experiments retain exact RTL; recheck main and any eventually adopted hardware. |
| L1 | unit 36456739733; later main unit results recorded in WORKLOG | Keep green on final main revision; no new functional claim from physical screening. |
| L2 ≥1M and injection | Million-clock zero divergence on frozen candidate; priority/cursor injected bugs detected at99/326 | Physical-only trials preserve RTL. New RTL/storage variant would need fresh million-clock and appropriate independent-model evidence before promotion. |
| Required RTL protocol tests | unit 36799356039, both simulators plus sigrok | Final adopted resource configuration must retain corresponding tests. |
| Required gate-level protocol tests | 36952644578, hardened candidate 4/4; later expanded routed L3 runs | Published l3-placement-routed-gl will test exact new successful route automatically with Icarus13; audit JUnit and sigrok/reference checks. No SDF timing proof. |
| Full6x4 hardening, DRC/LVS/antenna/precheck/typical timing/routing runtime | 36799356107 passed historical checklist; slow setup −10.698ns was explicitly failing | Current split diagnostics do not replace full standard GDS signoff. Need selected candidate's complete checks, runtime and all-corner extracted timing. Latest actual measured slow setup remains −5.630099ns. |
| Viewer | Historical viewer in36799356107 | Regenerate/deploy evidence for eventual final hardening. |
| Main CI green at phase end | Historical467012a; later green runs inWORKLOG | Confirm all required jobs on final main revision before ending phase; docs-only pushes still trigger CI. |
| AREA first row | Historical R4run8 already recorded | Add selected candidate's completed-route/signoff summary with run IDs, not pre-route estimates as final timing. |
| Bug ledger | Continuous ledger through#67 | Keep logging actual new bugs. Prototype/helper failures count too; no unverified fixed status. |

## Physical closure work outside historical typical-only checkbox

Keep 20ns and existing signoff SDC/D-066 semantics. The all-corner placement screen passed estimated setup/hold counts, but electrical slew/fanout violations and extracted routing are unresolved. Active route37412965189 gates DRT behind clean antenna and fresh timing; downstream extraction/L3 are automatically triggered only by successful main-branch routing. Full DRC/LVS/precheck remain distinct from router DRC.

## Prepared independent follow-ups

- `gds-cts-cluster-screen`: fresh placement/CTS/GRT comparison of timing-placement default against CTS_SINK_CLUSTERING_SIZE8; all-corner repair, unchanged RTL/clock/density. Record actual leaf loads, clock skew, hold growth, electrical counts and overflow. Cluster size is not a guaranteed post-resizer fanout cap.
- `gds-lane-slew-screen`: reuse exact all-corner placement repair checkpoint, baseline/oneBUF4 on `_07896_`, moving exactly five audited loads. Buffer starts near source at(298.56,287.28), then DPL legalization and all-corner repair. No DRT in screen.
- `gds-sram-slew-screen`: separate baseline/oneBUF4 on `_04725_`, moving only `_30324_/A2`, start(852.0,192.78), same legalization/repair. No combined lane/SRAM changes.

All compare isolated hypotheses. Buffer-screen baselines execute the same wrapper/DPL/repair sequence but do not change connectivity. The two split variants use a BUF4 noninverting cell, retain source logic and cycles, and validate complete source-net connectivity and supplies before mutation. Local mocked OpenDB tests are guard/connectivity evidence, not physical timing or full formal equivalence. Twenty-three helper/Tcl checks and three workflow parse checks passed. Source artifact remains37408506116; guards refuse renamed/reconnected source nets. Prepared workflows are manual only and are not dispatched before choosing from routed evidence.

## Phase boundary

Stay in phase2. Do not start later-phase tasks or mark area complete merely because global-route estimates pass. After the candidate meets physical requirements and final resource adoption is agreed, rerun all required main CI and update the phase summary with exact evidence.
