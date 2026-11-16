# Candidate configuration review and constraint parity

Review only: no main hardware/config or official workflow edits. Current owner screen43920762758 remains the selected physical experiment.

## Native support versus adoption authority

All23 config fields flagged by the input auditor have native LibreLane3.1.0.dev4 Variable definitions; none requires replacing a template job or patching a native repair script. Declarations/types/defaults/source locations and exact wheel/config hashes are in `spikes/phase2_stock_flow/pad_owner_or/config_review.json`.

| Group | Fields | Review result |
|---|---:|---|
| SRAM PDN/extraction integration | 7 | FP_PDN V pitch/spacing/offset, custom PDN file, explicit power connections and Magic macro handling. Project inputs through native interfaces; retain exact geometry/source identity and require official LVS/precheck. |
| Clock-tree controls | 3 | NDR strategy and sink cluster size/diameter. Supported settings; affect timing/layout and cannot be silently reset before official GDS. |
| Cell mapping | 3 | Cell exclusions, buffer choice and synthesis strategy. Supported settings; excluded weak cells must remain absent in actual synthesis/final netlists. |
| Global-route/repair controls | 8 | Capacity adjustment, antenna strategy, wire cap, overflow iterations, repair margins and two optional repair stages. Supported, some explicitly experimental; require effective-log checks and runtime assessment. |
| Placement repair margins | 2 | Setup/hold repair targets, not signoff acceptance thresholds. Keep fixed during the current experiment. |

FP_PDN_VOFFSET/VSPACING/VPITCH are accepted aliases for PDN_VOFFSET/VSPACING/VPITCH. Do not rename them during physical qualification merely for cleanup. Custom PDN is a substantial project script, not a template change; its legacy-native procedure wrapping makes pinned-engine testing important. Support does not establish future-version portability or authorize adoption under AGENTS.md. These23changes still need a reviewed project-config policy override/decision when the source qualifies.

## Constraint discrepancy discovered

The candidate's project config sets neither PNR_SDC_FILE nor SIGNOFF_SDC_FILE, so stock Classic uses native base.sdc with0.25ns clock uncertainty. Historical src/signoff.sdc is present but not selected by that project config. Our extracted diagnostic helper did explicitly select it; it changes hold uncertainty to0.10ns. Actual extracted min.rpt confirms0.100000. Therefore reported fast/typical/slow hold+0.301340/+0.510919/+0.880261ns belongs to that legacy diagnostic constraint, not a fresh stock0.25ns signoff run. Slow setup-0.783631ns remains a real failure, and setup uncertainty is unchanged. No stock hold pass is inferred from arithmetic.

Prepared --stock-constraints mode in extracted_timing.py sources only native base.sdc, requires stock uncertainty and no custom PnR SDC, and checks fresh max/min reports at all corners.29focused tests pass, including rejection of the actual legacy report and acceptance of an actual native0.25ns report. No new native extraction was launched yet; future candidate extraction must explicitly select this mode. Historical diagnostic calls remain unchanged rather than silently rewriting old evidence.

## Verification completed independently

Exact owner source passes million-clock L2 with zero divergences, both clean mutation baselines, priority fault detection at99 and cursor fault detection at326. Four required UART/SPI/I2C RTL cases pass with real sigrok decoding (18other cases intentionally not selected in this targeted run). Earlier full suite passed22/22 with optional sigrok disabled. Source/XML hashes and case names in pad_owner_or/parallel_verification.json. None is final routed-netlist evidence.

Next: inspect current screen, then obtain extracted timing under stock constraints on the selected source. Complete resource/config adoption decision and clean-checkout official GDS/precheck/GL only after physical qualification. Do not spend a second physical experiment on a known local regression.
