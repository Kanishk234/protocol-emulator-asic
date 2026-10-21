# Third R1 topology screen: reduced interior mux radix

The authenticated four-track control39689008902 fits all eight workloads in the abstract model but saves only1.83%in idealized cell sum. LUT selection still costs414bits and1132padded mux inputs. D105 uses the third/final initial profile to reduce that interior cost.

`spikes/r1/reduced_radix.py` implements a structural policy with no workload-specific inputs. Escape banks retain eight local wires per direction, at most eight mux choices each, with four local/four global choices. Bipartite matching covers every cell output in each cardinal bank. Local gather selectors use at most two inputs, preserving local feedback where present. Paired LUTs select complementary halves of their four shared paths. Clock/reset/enable/carry selectors, primitive input selectors and border switches retain their four-track choices. Coverage does not prove complete end-to-end routability.

Generated local v2:128LC/4timer/4shift/42IO,438stored bits per LUT tile (286switch),334per primitive (290switch),8736complete-grid bits. All ten tile hierarchies elaborate and their complete latch counts survive technology mapping. Local full-grid cost output is build/r1_radix8_2_mapping_v2; hosted quantitative acceptance pending. First draft fails the live-latch gate (BUG115) and is rejected.

The workflow now fixes three profiles:8/full,4/full,4/radix8_2. It maps every tile type and compiles all six retained personalities plus both concurrent workloads. Every attempted workload outcome is retained, including native fatal classification and explicit unknown/setup observations; a failed workload keeps the campaign red. Mapping failure also stays red while allowing compiler diagnostics from an otherwise generated model. No physical hardening attempt has been consumed.

Next: authenticate hosted source/model/mapping/image evidence and all workload outcomes. Reject capability loss. A successful compiler/cost screen still requires configured-fabric functional tests, declared seed coverage, representative physical flow with correct pin/PDN geometry and complete integrated chip closure. G1 remains protected.


## Physical preparation constraints

Compiler/cell-cost success would admit representative physical work, not chip promotion. Use actual placeable core dimensions after row/site margins, not the whole tile rectangle. Count physical buffers, clock distribution, configuration distribution and routing reserve. Four global tracks still leave fixed configuration/control ports; the six-column model also needs more column frame strobes than G1.

Narrowing a tile changes its absolute power-stripe phase. The original same-local-offset policy relies on G1 tile widths and cannot be reused blindly across six narrower columns. Preserve or explicitly redesign a globally aligned grid; verify same-net overlap, every power pin reached and full-height top-level power ports. Snap widths to the vertical routing grid and heights to cell rows. A representative route must use the actual CMOS5L signal-layer limit and the same20ns target, with original safety margins and complete live configuration. Width/density/channel alternatives are not a license for an unbounded sweep.

No narrower tile geometry or PDN overlay is selected yet. First authenticate all eight compiler outcomes for this fixed graph. Then choose one costed representative footprint and explicit power phase, validate it, and integrate only after its physical gates pass. Full-chip shell/configuration pin access remains a separate required gate.


## Hosted status and full assembly check

[39696113043](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39696113043), source0690b6b41148397e21e054e2c30721226ecd5fc8: both full-radix controlsSUCCESS. Each downloaded independent audit verifies71strict tests,147source/generated inputs,284clean-library files,121FABulous modules, native/report cell counts and all eight exact962-word FASM regenerations. The reduced-radix job passes generation, mapping and checker stages and remains in its bounded eight-workload compiler step at this checkpoint. No candidate fit/nonfit or quantitative hosted cost accepted before complete artifact audit.

Local final build/r1_radix8_2_v3 additionally generates the assembled eFPGA and successfully elaborates it with all tile/primitive modules. The resource generator now retains/hash-binds that assembled source and diagnostics automatically. This proves elaboration, not configured user-design behavior. Compiler campaigns additionally persist a passed=false partial result after each workload and print concise outcomes, so a timeout or cancellation can retain completed evidence. Regression verifies early failures remain visible while later workloads execute.71focused checks pass in build/r1_radix_final_checks.xml.
