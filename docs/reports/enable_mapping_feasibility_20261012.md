# Enable mapping feasibility: research, not a hardware change

The hold allocation in producer38167697696 includes150 direct FF → delay → feedback mux → same FF paths. Shared enables are a candidate for reducing feedback logic, but membership alone establishes neither a removable delay nor a routing gain.

[Yosys clockgate documentation](https://yosyshq.readthedocs.io/projects/yosys/en/v0.55/cmd/clockgate.html) describes grouping eligible enabled flip-flops and selecting integrated gates from Liberty. [dffunmap](https://yosyshq.readthedocs.io/projects/yosys/en/0.46/cmd/dffunmap.html) supports preserving enables while unmapping synchronous reset. Tool versions and the actual mapped result must be checked; this is not evidence that our current synthesis pipeline performs either transformation.

Read-only inspection of the [pinned IHP fast-corner Liberty](https://github.com/IHP-GmbH/IHP-Open-PDK/blob/2bbec755dc67ca3db0261c3d6163e15735d66710/ihp-sg13cmos5l/libs.ref/sg13cmos5l_stdcell/lib/sg13cmos5l_stdcell_fast_1p32V_m40C.lib) finds integrated `sg13cmos5l_lgcp_1` and scan-capable `sg13cmos5l_slgcp_1`, **both marked `dont_use : true`**. The scan variant also has `dont_touch : true`. Exact downloaded library SHA256: `af12d75a72d19648fa690027d29843fbae550aa91f4e40dd3339c7116d6e425d`. We have not overridden either flag, inserted gates or changed chip sources. Library presence alone does not make clock-gating insertion a supported optimization.

Before considering such a candidate:

1. Identify why the cells are excluded in the pinned PDK and flow. Retain the default exclusion until its reason and a supported alternative are established.
2. Measure actual eligible enable groups in the scratch shell synthesis; preserve reset priority and every load/RUN/STOP transition. A synchronous reset must still receive a clock when the enable is inactive.
3. Prove sequential reset/enable equivalence on the mapped candidate, including reset while otherwise disabled. Binary equivalence does not settle gate-model unknown-state behavior.
4. Verify integrated-cell model behavior, generated-clock propagation, clock-gating checks and CTS at the original constraints, followed by actual SPI-loaded configuration and protocol tests.
5. Compare total same-clock physical area and congestion, including added gate/enable buffering/clock tree. Do not assume fewer data muxes means fewer routing violations.

This is a general shell implementation hypothesis, not a protocol block or a successor architecture decision. Current engineering rules restrict non-configuration latches and the hardware remains frozen; any implementation proposal must resolve those rules before promotion. The immediate D089 per-delay timing query is independent and leaves hardware unchanged.
