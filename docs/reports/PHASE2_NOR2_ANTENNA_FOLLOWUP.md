# NOR2 physical screen: antenna-only follow-up

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
