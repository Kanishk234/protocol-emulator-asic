# Phase 3: Specialize, compare, hardware freeze

**Reopened for successor architecture exploration by D-037 (2026-09-28).** The completed G1 checklist below records the first architecture decision and remains the baseline evidence. G1 and the `hw-freeze` tag remain intact while separate successor candidates are explored under `docs/design/ARCHITECTURE_EXPLORATION.md`.

**Dates:** Nov 16 – Dec 6, 2026
**Goal:** turn the generic fabric into a protocol-specialized one, one measured change at a time, and freeze the hardware on the best variant the data supports.

## Method
Work through the ranked specialization list from `docs/reports/profiling.md`, top first. For each candidate:

1. Write a DECISIONS entry: the need (with profiling data), protocols that benefit, expected area cost, cost to protocols that don't use it.
2. Implement it: primitive RTL, behavioral model, fabric definition in `arch/`.
3. Make the tools use it: Yosys mapping (explicit instantiation first), placement and routing, bitstream configuration.
4. Test it: primitive corner cases (reset, simultaneous controls), then a compiled user design using it, loaded through the real interface.
5. Harden it: **one hardware change per hardening**; record area, routing overflow and timing.
6. Compare it with the previous variant at **equal total area**: coverage and performance on the design set.
7. Keep it only if the measured benefit justifies the cost. Record the result either way.

Stop adding features by Nov 30 regardless of how many remain.

## Tasks
- [x] Candidate 1 (from profiling): full method above. (Ranks 1–2 of the profiling list, timer and shift register, were built as G1 in phase 2, D-026. First phase 3 candidate from the G1 measurements, `docs/reports/g1_limits.md`: registered terminal count, D-030: F4 re-proved, measured, not kept alone)
- [x] Candidate 2: full method above. (Primitive tile with design repair, D-031: three tile runs, not feasible in the tile's footprint)
- [ ] Candidate 3 (only if time allows): full method above.
- [ ] Optional experiment, only if profiling points to it: multi-context configuration (store 2 contexts and switch between them). Measure configuration-storage cost vs. capacity gained.
- [x] Equal-area comparison of all variants: coverage × performance chart (Pareto front) in `docs/reports/architecture_comparison.md`. (with `architecture_comparison.svg`)
- [x] Choose the final architecture from the data; DECISIONS entry. (D-033: G1)
- [x] Final hardening: precheck, timing at the chosen clock, routing overflow within limits. (CI 36383587262 on 3047dea: precheck pass, setup WS +12.48 ns at 50 MHz, routing DRC 0)
- [x] `gl_test` with at least two real bitstreams on the final netlist. (36383587262: 21/21, eight real bitstreams)
- [x] Tag the commit `hw-freeze`. After this, hardware changes only for bugs, each with a DECISIONS and BUGS entry. (tag `hw-freeze` → 3047dea, pushed by the user 2026-09-28)

## Phase exit checklist
- [x] Each attempted specialization has a DECISIONS entry with its measured result (kept or dropped) (D-030, D-031; not-built candidates with their data in D-033)
- [x] `docs/reports/architecture_comparison.md` with the equal-area comparison and chart
- [x] Final architecture hardened, precheck passed, timing met (CI run ID: 36383587262)
- [x] `gl_test` green on the final netlist with two real bitstreams (CI run ID: 36383587262)
- [x] All design-set protocols recompiled and passing on the final architecture (amended by D-035 to every *supported* design-set protocol: UART, SPI controller, I2C controller, `gl_test` 21/21 in 36383587262 and `fabric` 36383587292 on 3047dea; the I2C target does not fit and is not supported, D-033–D-035)
- [x] `hw-freeze` tag created (by the user) (→ 3047dea)
- [x] All CI workflows green on `efpga` (a578359: lint 36443265794, unit 36443265785, docs 36443265803, test 36443265742, fabric 36443265750; gds/formal last ran on the frozen hardware at 3047dea, 36383587262 / green)
- [x] `docs/summaries/PHASE3.md` written
