# Official-flow portability and SRAM locality preparation

## Finding

A clean build can receive a standard-cell locality policy through the existing LibreLane Classic `Odb.ManualGlobalPlacement` step and `MANUAL_GLOBAL_PLACEMENTS` key. This is a plausible integration route, not proof of official GDS closure. No main configuration or template job changed.

Inspected exact upstream sources:

- Tiny Tapeout action CMOS5L revision `3412659307918422f3f0727917cf9b499aaca588`: default LibreLane `3.1.0.dev3`, calls `tt_tool.py --create-user-config`, then `--harden`. [Action](https://github.com/TinyTapeout/tt-gds-action/blob/3412659307918422f3f0727917cf9b499aaca588/action.yml).
- Support tools CMOS5L revision `d66cf179e7bc4d296362ab7e2e3b344dc3c4f665`: generated user configuration overrides matching base keys; hardening invokes LibreLane on merged config and clears the old wokwi run. Archived ODBs and helper files are not automatically inputs. [Project entry](https://github.com/TinyTapeout/tt-support-tools/blob/d66cf179e7bc4d296362ab7e2e3b344dc3c4f665/project.py).
- Pinned LibreLane `3.1.0.dev3`: Classic runs RepairDesignPostGPL, ManualGlobalPlacement, DetailedPlacement, CTS and subsequent native timing/routing repair. [Classic](https://github.com/librelane/librelane/blob/3.1.0.dev3/librelane/flows/classic.py).
- Built-in placement key describes coarse, unfixed, non-legalized placement; operation uses instance names, converts micron coordinates to DB units, marks PLACED and fails on missing instances. [Step](https://github.com/librelane/librelane/blob/3.1.0.dev3/librelane/steps/odb.py), [operation](https://github.com/librelane/librelane/blob/3.1.0.dev3/librelane/scripts/odbpy/placers.py).

## Actual clean-build evidence

From artifact11715973741 (route38172640071), retrieved inherited native-stock-screen stage32 RepairDesignPostGPL,37 ResizerTimingPostCTS and43 ResizerTimingPostGRT netlists. Direct SRAM buffers wire9447/wire9439/wire9438/max_cap9445 already exist at stage32; all16 directly connected BUF4s are available for the normal manual-placement stage. This corrects the initial concern that these names might only exist too late. They remain implementation-generated names, so new synthesis/PDK/recipe changes can invalidate them.

Clean pre-placement NL SHA `2b3925b0d3fb308d16ea07b3b10e9f72598b74cec330c1b147072a8ac47ba9f0`; DEF SHA `337c6b32c5325e2da7a68d139f4f7ecc7b80d836e85e8e3456470302e5f8661d`. Original clean source37990280838 and retained routed source38172640071 have separate planner provenance and hashes. The new screen refuses a pre-manual clean topology that differs from the reviewed reference.

## Prepared experiment

`sram_bank_plan.py` validates exact NL/DEF and macro/standard LEF geometry, derives all16 SRAM pin centers from the fixed12,40 FS macro, reserves complete legal-row footprints sequentially and checks the combined final geometry. It proposes14 existing-buffer moves on retained DRT, or16 on the distinct original clean post-GPL stage. Added cells/master changes/logical changes0. Candidate fragment uses micron coordinates for built-in manual placement; raw hypothetical DEFs and proposals stay/tmp.

`sram_bank_clean_screen.py` prepares a fresh run from RTL through native Classic post-GRT timing repair, using the stock image and stock stage ordering. It adds the manual-placement dictionary to the trusted native AREA1/clock8/20ns/56%-density recipe and enforces congestion disallowed. Original signoff files, macro configuration and100psrepair/50psacceptance targets remain fixed. Audits pre-placement topology, actual manual coordinates and post-DPL coordinates, zero global overflow, fresh antennas and all-corner timing. It deliberately refuses qualification if antennas or50pshold/setup gates fail; always-upload workflow retains failure evidence. No archived physical state is passed as the new flow's initial state.

Separate `gds-sram-bank-clean-screen.yaml` uses frozen full2/4 candidate3393eea, event-late variant and retained artifact only as trusted/reference data. Upload includes the new clean run and reference recipe/post-GPL views, not every inherited physical tree.97focusedtests pass, plus actual source generation on routed and clean stage layouts. Physical experiment not executed. This screen tests SRAM placement policy alone; it does not automatically reproduce every earlier electrical/strength ECO, nor claim to supersede the selected lineage.

## Remaining official adoption work

1. Inspect running residual data extraction38179535945; preserve its evidence and avoid blindly stacking physical candidates.
2. Publish and run reviewed clean-bank screen; measure final buffer positions, timing, electrical, overflow, added repair cells and antenna burden. Unfixed placements can change during later resizer steps.
3. If beneficial, evaluate full clean flow through DRT/extraction and exact-netlist GL, with resource/area/routing checks. Demonstrate stable instance mapping or replace brittle names with a general reproducible identification policy where supported.
4. Main adoption needs a reviewed exception to AGENTS/physical-design config whitelist: at least MANUAL_GLOBAL_PLACEMENTS and the chosen native recipe keys beyond clock/density/SRAM. D-080 explicitly reserves a separate reviewed exception for native mapping adoption. Do not silently edit src/config.json, generated user_config, template jobs or installed tool code.
5. Integrate approved hardware/config/constraints on one main commit; official GDS/precheck/gl_test/viewer plus independent all-corner zero-electrical audit must pass on that commit. A current-branch GDS run without integration would rebuild the existing main design instead.

This experiment does not change architecture, firmware/protocol support or50MHz. Legal geometry does not establish pin access, power integrity, routability, timing or electrical closure.

## Initial launch failure and correction

Clean bank38180541456 failed before synthesis because the launcher did not create the nested flow directory required by the pinned --force-run-dir CLI. BUG92 records the cause. Corrected helper creates a fresh empty directory before CLI invocation and refuses reuse; regression checks the actual directory at launch, stock-image selection and no checkpoint initial state.99focusedtests pass. This failure provides no physical evidence for or against SRAM locality; corrected rerun remains under the previously approved experiment scope.
