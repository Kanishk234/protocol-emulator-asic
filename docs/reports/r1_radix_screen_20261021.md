# Third R1 topology screen: reduced interior mux radix

The authenticated four-track control39689008902 fits all eight workloads in the abstract model but saves only1.83%in idealized cell sum. LUT selection still costs414bits and1132padded mux inputs. D105 uses the third/final initial profile to reduce that interior cost.

`spikes/r1/reduced_radix.py` implements a structural policy with no workload-specific inputs. Escape banks retain eight local wires per direction, at most eight mux choices each, with four local/four global choices. Bipartite matching covers every cell output in each cardinal bank. Local gather selectors use at most two inputs, preserving local feedback where present. Paired LUTs select complementary halves of their four shared paths. Clock/reset/enable/carry selectors, primitive input selectors and border switches retain their four-track choices. Coverage does not prove complete end-to-end routability.

Generated local v2:128LC/4timer/4shift/42IO,438stored bits per LUT tile (286switch),334per primitive (290switch),8736complete-grid bits. All ten tile hierarchies elaborate and their complete latch counts survive technology mapping. Local full-grid cost output is build/r1_radix8_2_mapping_v2; hosted quantitative acceptance pending. First draft fails the live-latch gate (BUG115) and is rejected.

The workflow now fixes three profiles:8/full,4/full,4/radix8_2. It maps every tile type and compiles all six retained personalities plus both concurrent workloads. Every attempted workload outcome is retained, including native fatal classification and explicit unknown/setup observations; a failed workload keeps the campaign red. Mapping failure also stays red while allowing compiler diagnostics from an otherwise generated model. No physical hardening attempt has been consumed.

Next: authenticate hosted source/model/mapping/image evidence and all workload outcomes. Reject capability loss. A successful compiler/cost screen still requires configured-fabric functional tests, declared seed coverage, representative physical flow with correct pin/PDN geometry and complete integrated chip closure. G1 remains protected.
