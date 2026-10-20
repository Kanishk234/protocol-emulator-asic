# Native proposal handoff review

Pinned source: OpenROAD dcf36133a369abc8f3c5e5738cd4d82e4903c0e0, [GlobalRouter.cpp](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/grt/src/GlobalRouter.cpp#L2630).

`readSegments` initializes grid/net data, appends segments into `routes_`, and checks connectivity and pin coverage for entries present. It does not explicitly clear existing route vectors, enforce a complete expected net inventory, or call `updateEdgesUsage`; database congestion refresh is conditional on an absent GCellGrid. Therefore this command alone cannot authenticate replacement of a populated121 checkpoint or establish the native weighted FastRoute ledger. This is source review, not an executed import experiment.

Next: a bounded round-trip harness must reproduce unchanged segment inventory, geometry, multiplicities, clock/NDR demand and every native resource ledger before accepting any modified input. Require full expected net coverage independently. Only then test the118 coarse proposal. Do not import directly into populated route vectors or infer success from connectivity alone. No import/build/EDA launched; no native gain claimed.
