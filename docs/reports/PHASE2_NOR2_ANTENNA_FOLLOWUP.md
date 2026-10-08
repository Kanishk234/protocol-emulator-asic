# NOR2 physical screen: antenna-only follow-up

## Follow-up reporting correction

Run [37733684248](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37733684248) completed diode repair but stopped before fresh STA: incremental antenna rerouting did not print the full congestion table required by the guard (BUG78). This run establishes no post-repair timing verdict.

The local correction performs an explicit full global-routing pass after diode repair and before parasitic estimation and view export. It disallows congestion on that pass, requires the fresh complete zero-overflow table, and then runs independent antenna checks and all-corner STA on the resulting route. This reroute may reintroduce antenna violations; those remain a failing gate. No repeated sizing, timing repair, or DRT is added. The wrapper requires exactly one insertion point. All 239 related helper tests pass, along with shell syntax and diff checks; these are orchestration tests, not physical closure evidence.

Publication and physical rerun are pending under the latest AGENTS.md user-run Git rule. Publish only the screen correction and its documentation; exclude the local DRT continuation, FIPE document and old SRAM prototypes.

Corrected screen [37732392933](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37732392933) passes source identity, guarded NOR2 replacement, legalization, strict fresh-netlist comparison and zero-overflow GRT. Independently read artifact11530157875. Its final gate fails because of42 antenna nets/45 pins, not timing:

| Corner | Setup WS(ns) | Hold WS(ns) | Setup/hold violation counts |
|---|---:|---:|---:|
| Fast |0|+0.0932422|0/0|
| Slow |0|+0.393552|0/0|
| Typical |0|+0.211997|0/0|

These are estimated global-route results, not fresh extracted closure. The original strongest extracted candidate remains -0.179789ns setup/+0.037290ns fast hold. The full reroute after sizing changes wire geometry; its antenna failures require physical cleanup before DRT can be considered.

Prepared explicit `repair_antennas` option on the same manual screen, defaultfalse. The selected follow-up executes one standard bounded OpenROAD.RepairAntennas step between fresh antenna checks. No timing-resizer pass or DRT is added. Fresh legalization/routing within antenna repair must report zero layer overflow; fresh all-corner STA and antenna checks must pass.

The wrapper exports logical/powered views after antenna repair without repeating NOR2 sizing. The runner permits only additional pinned antenna diodes on existing nets; any removed/changed original cell or connection, other new logic, stale view or absent ECO is refused. Inherited SPEF/SDF/Liberty views are cleared. Detailed gate metrics now print in the log.

237 related helper tests pass, including repeated-sizing avoidance, exact diode-only changes and fresh repaired views. Existing source checkpoint and timing constraints remain unchanged. Original-RX/event-late official integration is prepared separately in `/tmp/tripwire-event-nor2-official-prep-20261008`: generator/static source-list checks pass,19RTL sources match the previously tested original candidate,125ps native configuration proposal is unapplied. Source alone does not reproduce this physical ECO or custom reservation.

Local routing continuation/workflow integration remains unpublished and unlaunched until a measured clean checkpoint exists. Phase2 remains incomplete; no checklist tick or official timing claim.

## Actual failure and replacement audit (BUG79)

Screen37735461986 reached fresh STA and passed all three setup/hold gates: setup WS0 in every corner; hold fast+0.119457ns, slow+0.418565ns, typical+0.231292ns. It failed the independent final antenna gate:47 nets/52 pins. The repair log first shows42 antenna violations,28 jumpers on24 nets,36 inserted diodes, then0 violations. The subsequently added full audit reroute recreated violations. This is a physical antenna regression caused by the audit reroute, not a timing-report parsing failure.

Replace that audit with strict incremental repair: explicitly set GRT_ALLOW_CONGESTION=false in the antenna flow; wrapper checks the policy before repair and before estimation/export, and emits completion evidence without a global_route call. The runner rejects absent/duplicate completion evidence or a repair command allowing congestion. OpenROAD's incremental FastRoute path retries congestion and errors if overflow remains when congestion is disallowed. Independent antenna checks, diode-only netlist checks and all-corner STA still gate eligibility. This replaces the full-rerouting correction above.240 helper tests pass; no extracted or official closure is claimed. Physical rerun remains necessary.
