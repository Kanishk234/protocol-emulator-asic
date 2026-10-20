# Incremental congestion proposal: 121 to 118, not yet installed

The authenticated native control remains 121 raw-grid overflow. A new eight-net coarse proposal independently checks at 118. This is a partial improvement under the exported model, not native routing closure or physical acceptance.

## Why change the objective

Prior frozen-background feasibility trials required eliminating all selected-net overflow. Their valid restricted-model cuts exclude that stronger target, not every partial improvement. The new bounded SCIP model minimizes overflow against unchanged original capacities, then occupied edges. It returns PROPOSAL rather than a capacity-feasible routing status.

Window [0,0,85,5], selected slots [32,73,94,120,123,124,387,1918], all four native layers. The window falls from 23 to 20; the exterior stays 98. There are 88688 variables, with a 150000-variable admission cap and 30-second/1024-MB/one-worker solve limits. SCIP reports optimal within this model. Via and pin-access modeling remain coarse; this is not a detailed-route guarantee.

## Controls and independent checks

A native positive-control witness exposed an initially overstrict zero-capacity policy: slot387 already uses H_0_17_2 at a native pin. The corrected policy permits only that original net on its exact original zero-capacity edge and charges actual overflow against zero. It grants no capacity or general shortcut. Corrected baseline reproduces window overflow23; corrected five-net target22 is infeasible. The eight-net proposal reaches20.

Retained ignored artifacts: build/corridor112_congestion_joint/{model.json,qualified-solution.json,whole-grid-proposal-check.json,independent-check.json,qualified-source-manifest.json}. Graph SHA256: 044769eb4e968a7bce32c11b04cac74d2fe50d7592b086b525a51168d31a39e7. LP SHA256: c8b9db24cef0cfc41bed24ac136ca7e035160f0b8d580f774a9b9cf157c2e072.

A separate standard-library-only checker, importing no project parser/model/solver, directly reads original raw resources, STEP multiplicities, native pins and published segments. It checks all 139228 resources, all 134 changed-resource vectors, exact released multiplicities and full exterior-plus-interior connectivity for 19 native pins. Result: original121, proposed118, native_route_installed=false, physical_acceptance=false, timing_acceptance=false.

Local integrated qualification: build/autonomy112_congestion_final.xml, strictly verified 1004 executed passing tests with no skips/errors/failures. New congestion/proposal tests include independent exhaustive objective comparisons and tampered-witness rejection. No second-agent source review of these new modules is claimed.

## Next acceptance gate

Review the pinned native segment/guide import implementation before any handoff. Preserve native capacities, clock/NDR demand, inventories and complete connectivity; reproduce a lower full native overflow before retaining this as a native gain. Zero overflow, detailed-route DRC, LVS, antenna, timing and configured-design checks remain necessary for compact-design acceptance. Frozen G1 stays the release fallback. No hardware change or phase box was approved by this proposal.
