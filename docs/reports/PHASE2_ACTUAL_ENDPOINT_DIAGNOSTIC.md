# Actual endpoint diode diagnostic

Prepared on frozen minimum-buffer screen41569397169:four final antenna failures,timing/electrical/overflow gates pass. This is mechanism diagnosis on copies of an existing physical design. It is not a source implementation or promotable stock recipe.

## Controlled intervention

Two jobs start with the same61hash-bound files and final physical state. Both freshly verify the four known source antenna failures. One invokes the pinned library's experimental Odb.InsertECODiodes step with an empty list;the other adds one native diode at each reviewed sink:

| Sink | Frozen input net |
|---|---|
|hold7969/A|_10511_|
|wire13568/A|_19518_|
|_38673_/A|net11878|
|wire12579/A|net12579|

The native step temporarily locks existing instances,legalizes new diodes near targets and updates routing. Runtime inspection must establish the step and its diode interface exist in the exact stock image;unknown interfaces fail instead of guessing. No tool scripts or official jobs are patched.

## Evidence required

- Frozen source remains byte-identical before/after.
- All original component masters,positions/orientations and signal connections remain unchanged.
- Added instances are exactly zero or four antenna diodes;inserted diodes share each target's actual net.
- Source failure is confirmed freshly at all four reviewed pins.
- After-step antenna results and per-target membership are measured fresh.
- All three corners are measured before/after with the original frozen SDC explicitly bound.

The empty-insertion control detects effects from native routing refresh alone. A successful mechanism claim requires comparison,not just a green diagnostic job. GRT/diode placement may introduce other violations;those remain visible in raw reports.

## Limits

The experimental step is outside stock Classic and must not be added to official GDS. A favorable result would guide a general source-level protection implementation that still needs functional proof and a fresh unchanged-stock-flow full screen. It would not authorize DRT or phase completion.

The native step exports edited ODB/DEF. Its inherited NL is not an exported netlist of the edited circuit;STA uses the modified ODB,and structural checks use DEF. No GL/LVS/GDS result or consistent promotable artifact bundle is claimed. The workflow explicitly reports qualification_performed=false,promotable_stock_recipe=false,and post_edit_gate_level_netlist_exported=false.

201focused tests,actual frozen61file/target/DEF checks,source-selection rehearsal,Python compilation and shell syntax pass. Native execution remains pending. Preconditions and hashes:actual_endpoint_preflight.json and shared_minbuf2_final_checkpoint.json.
