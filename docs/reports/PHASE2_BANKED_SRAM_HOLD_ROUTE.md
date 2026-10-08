# Banked selector repaired checkpoint: routed follow-up review

Repair-only run37690561695 passed on main3c494c0. Independently audited artifact11513594590:36 source hashes match frozen3393eea plus the tested event-late/banked IO patch, exact checkpoint files exist, and saved timing/antenna readiness passes. The SRAM seed buffer remains in the repaired netlist. No detailed routing has run for this candidate.

| Measurement | Post-antenna result |
|---|---:|
| Setup WS fast / slow / typical |0 / 0 / 0 ns|
| Hold WS fast |+0.0700513 ns|
| Hold WS slow |+0.376972 ns|
| Hold WS typical |+0.198153 ns|
| Setup / hold violation counts |zero at every corner|
| Antenna nets / pins |0 / 0|
| Final GRT overflow |zero on every layer|

The targeted BUF1 insertion plus125ps bounded all-corner repair inserted422 hold buffers. Repair instance area526445 µm²/count34104 versus banked source510973/count33156 (+3.03% area); versus prior event baseline510232.98, +3.18%. Final routing demand246676/usage41.22%. Area cost and routing timing must be judged with actual detailed route and extraction; positive GRT hold is not a guarantee of routed hold.

## Prepared continuation

Extend the existing manual gds-placement-route workflow with optional repaired_source_run_id. Original workflows remain unchanged in behavior when it is empty. For this candidate, require original source37669663762, variantbs-event-pin-banked and successful main repair37690561695. Download the repaired artifact, reconstruct trusted expected source hashes before download, validate both workflow provenances, and require exact saved source identity/checkpoint/20ns/full timing constraints.

`banked_sram_hold_route.py` accepts only the reviewed repair run. It independently checks saved all-corner timing/50ps fast margin/antenna gates and source file identities, then reruns fresh per-corner timing on that same post-antenna checkpoint. Only if those gates still pass does it launch OpenROAD.DetailedRouting. The continuation uses the ordinary region-reservation image: no SRAM reinsertion and no repeated timing repair. Any optional hold-target or post-antenna-repair request is rejected on this branch. Direct routing of the original hold-failing banked screen remains refused.

Artifact layout remains runs/placement-route/drt and gds-placement-route-RUNID. Existing extraction and expanded routed-GL workflows can therefore follow completion without changing their source/DRC guards or trigger blocks. Their outputs still do not replace official full GDS/DRC/LVS/precheck.

245 local helper tests pass; source artifact gates and36source hashes independently replayed. New tests reject wrong repair branch/workflow/run/status, changed checkpoint/identity policy, setup/hold/antenna regression and missing50ps budget; workflow checks cover exclusive original/repaired artifact downloads. No DRT dispatch yet.

After publishing separate tools/tests, workflow and report groups, launch:

```sh
gh workflow run gds-placement-route.yaml --repo Kanishk234/protocol-emulator-asic --ref main \
  -f source_run_id=37669663762 -f source_variant=bs-event-pin-banked \
  -f repaired_source_run_id=37690561695 -f pre_route_hold_target=source \
  -f repair_postantenna_hold=false
```

The strongest measured extracted baseline is original event-late125ps: setup -0.179789 ns, fast hold +0.037290 ns. Measure this new route against it; reject regression and preserve all protocol/live-configuration behavior. Official positive-WNS closure remains unproven.
