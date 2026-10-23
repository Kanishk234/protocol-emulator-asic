# Fresh eFPGA candidate plan — R1 exploration

Date: 2026-10-20. Status: proposed experimental specification and acceptance plan; no implementation selected, no replacement of frozen G1. R1 is a working label, not a promised resource count. Exploration follows D-037; the production architecture contract remains unchanged.

**Measured checkpoint (2026-10-23):** third/final graph screen uses reduced radix with128LC/4timers/4shifts as a diagnostic reference. Six retained personality compiler cases and primary UART+SPI fit; optional concurrentUART+I2C remains a600-second compiler-routing timeout. Balanced geometry reallocates west-border width to primitive columns without changing the1061.76×669.06planned outer footprint. All26actual leaf contexts pass global routing/PGgates (40030916359/40033384495), and corrected40native-leaf primary simulation/configuration observation passes40039667532. These do not select R1 or establish detailed routing, assembled-chip fit, real managementSPI, configured timing, full retained-protocol runtime parity or equal-total-area advantage. G1protection/minimum replacement criteria below remain unchanged.

## Objective and protected baseline

Build a physically routable eFPGA with more useful communication capability than G1 inside the same TT 6x4 CMOS5L envelope at the same 50 MHz target. Fewer routing switches are useful only if measured workloads benefit. Neither a smaller chip nor a larger nominal LUT count alone earns replacement.

G1 has 88 LUT4+FF cells, two timers and two shifts. Authenticated paired compiler run38852379083 atba0cb76 places UART29, SPI47 and I2C controller70 cells; four-register I2C target demands169 and does not fit. These are particular workload settings, not universal resource costs. Fmax90.71/77.97/52.97MHz is compiler-model timing, not configured physical timing. Historical frozen-chip tests also demonstrate WS2812, standard-speed 1-Wire and SWD bit-engine/host-packet personalities, with documented limitations, sequentially. Recompile and rerun all six using matched current sources before comparison; historical held-out resource counts are not new paired measurements.

G1 physical refresh39280550500 passes GDS/precheck/gl_test/viewer with30 executed gate-shell tests and9 precheck rows. Preserve D-023 gate-shell plus RTL-fabric scope; this is not full configured mapped-fabric/SDF qualification.

Existing compact exploration already provides112 LUT4s plus two timers and two shifts. Its protected native routing checkpoint still has121 raw overflow; an uninstalled coarse proposal independently checks at118. Neither is a physically accepted successor. Preserve both evidence sets; R1 must address configuration/pin/channel congestion rather than repeat larger-fabric assembly.

## Intended capability compared with G1

| Dimension | G1 baseline | R1 minimum and intended gain |
|---|---|---|
| Required roles | UART TX/RX, four-mode SPI controller, I2C controller within documented scopes | All preserved with same workload sources, parameters, host servicing and tested operating settings |
| Other existing personalities | WS2812 TX, standard-speed 1-Wire, SWD bit engine with host packet handling | All remain supported; no narrower semantics, new host burden or hidden rate reduction |
| Reconfiguration | Host-loaded bitstreams, CRC/error handling, STOP/reset/pin parking | Same externally visible contract; new architecture ID and regenerated images permitted |
| Parallel operation | No established independent-link benchmark | Primary gain: simultaneous UART TX/RX plus SPI controller, independently paced, with deterministic host demultiplexing and no extra pins |
| Additional concurrency | Unmeasured | Secondary target: UART plus I2C controller; qualify feasibility before promising it |
| Logic/resources | 88 LUT4+FF,2 timers,2 shifts | Initial112–128-cell/2-pair hypothesis is insufficient for the measured mixed UART+SPI workload (138-cell demand). Screen103-cell/3-pair demand against a larger2-pair alternative and full area/routing cost; no count selected |
| Larger designs | Four-register I2C target does not fit | Stretch: existing four-register target without weakening its host/register behavior; not promised by112–128 cells |
| Physical acceptance | Hardened fallback with documented verification scope | Entire integrated candidate closes routing and mandatory physical checks; mapped-fabric loaded behavior required for promotion |
| Area/clock | TT6x4,50MHz target | Same total chip budget and clock target; include shell, storage, routing, clock/power and padding |

Source inspection corrects the initial estimate: UART uses two timers/two shifts and SPI uses one of each, so the fully primitive-backed concurrent workload needs three timers/three shifts. Screen mixed hard/soft versions on G1; do not assume extra primitives are the best area tradeoff. UART29+SPI47 is not proof of fit: combined control, pin muxing, host arbitration and routing add costs. Establish paired G1 results before claiming this is new capability. If G1 already passes the same concurrency workload, R1 must improve measured concurrency capacity, a larger workload, or another predeclared user-visible metric; merely matching it is insufficient.

## Proposed architecture direction

Retain synthesizable-Verilog-to-bitstream programming, LUT4+FF logic, carry support unless profiling justifies its removal, reusable timers/shifts and the management shell behavior. Reuse verified tools and tests; rebuild the fabric organization and physical interface where evidence supports it.

First screen small clusters with strong local wiring and a sparse, regular inter-cluster network against a regular mesh control. Keep local feedback and primitive connections short; measure distinct signals crossing cluster boundaries rather than reducing connectivity blindly. Do not assume FABulous already supports the desired graph: generator, nextpnr and bitstream representation must pass a compatibility spike before selecting it.

Place timers/shifts and I/O according to actual workload connectivity. Preserve flexible user pin mapping within the architecture's published constraints; do not hardwire a protocol personality. Use two timers/two shifts as the protected control; the new concurrency census now justifies screening additional generic primitives, since fully hard UART+SPI requires three of each. Existing paired primitive tiles may provision four of each; quantify unused-resource cost and layout before selection. Add primitives only with multi-protocol benefit, area cost, tool mapping and a decision record.

Treat configuration distribution as part of the architecture. Compare localized configuration endpoints and hierarchical distribution against the existing interface, minimizing long high-fanout branches at shell/fabric boundaries. Clock distribution stays on supported clock infrastructure. Any change in configuration latency, storage, reset behavior or bitstream format is specified and measured; no asynchronous/gated-clock shortcuts.

Reserve routing channels and pin-access space before allocating remaining area to logic. Derive channel widths, cluster size, pin ordering and resource counts from physical screens. No fixed numeric channel width or capacity promise before measurement. Use no more than three initial topology/resource variants; no broad unbounded parameter search.

Do not combine an event processor, new memory subsystem, new LUT size and new routing graph in the initial candidate. Existing event-lane research remains evidence to consult if the eFPGA-only path fails; it is not silently included in R1.

## Gates, outputs and bounded effort

1. **G0: paired baseline and requirements (up to two active working days).** Archive exact sources/tools/settings for G1 and compact controls. Compile six supported personalities, four-register target and explicit UART+SPI/UART+I2C workloads on G1. Define host framing, pin allocation, rates, latency/jitter and failure behavior for concurrency before hardware work. Record resource/control/routing demand, configuration costs and existing G1 limits. Fresh four-role evaluation sealed October20; read HELDOUT_R1_MANIFEST.json only, and exclude its entire six-role pool from training until freeze; previously revealed protocols are training data. Output a requirement matrix and explicit primary gain. Stop if no credible new user benefit is identified.
2. **G1: architecture/tool compatibility (up to two active working days).** Specify at most three fabric variants, topology and configuration semantics. Generate from scratch in an isolated exploration tree; prove Yosys mapping, nextpnr representation, bitstream addressing and real loader operation on a tiny example. Maintain independent reference-model discipline. Produce storage/switch/pin/net census and full area estimates. Reject unsupported graphs or estimates with no plausible total-area margin.
3. **G2: representative physical screen (up to three active working days).** Harden a minimal connected cluster plus realistic adjacent channel/configuration distribution; include representative fanout, pin density, clock/power obstructions and boundary connections. Test real loaded bits on mapped logic. A tiny easy block passing is necessary but not evidence the full chip routes. Retain at most two survivors; reject variants requiring inflated capacities, waived margins or disabled guards.
4. **G3: full-size feasibility (up to three active working days).** Integrate one selected variant including the real shell, configuration storage, pad interface, clock and power. Run matched physical screens. Require zero native full-grid global overflow with unchanged reporting conventions before detailed route. Permit at most two single-variable physical correction trials for a diagnosed cause; then reject or record a new decision backed by new evidence. Do not spend repeated weeks polishing nonzero-overflow layouts.
5. **G4: functional gain and signoff (up to four active working days).** Compile and load all six existing personalities plus the predeclared gain workload. Verify independent devices, long concurrent traffic, host backpressure, STOP/reset/error/reload, open-drain behavior and no dropped data within the declared servicing limits. Complete detailed routing, DRC/LVS/antenna, setup/hold/corners and TT precheck. Qualify primitive timing and configured mapped-fabric loaded operation; record any residual verification scope explicitly. Freeze the candidate, then evaluate the new sealed set once. Changing hardware afterward invalidates that evaluation's held-out status.
6. **G5: replacement review.** Produce paired source-bound capability/area/timing/resource and qualification tables. Refresh final CI, docs and clean-checkout reproduction. Promote only after every hard requirement passes and the user-visible gain is demonstrated. Otherwise keep G1. No automatic update of production architecture, submission sources or release tags.

These are effort ceilings and checkpoints, not promised runtimes; hosted queue time is separate. Initial decision checkpoint is after G2, at most seven active working days, with about fourteen active days total before a go/no-go review. Start with a campaign allowance of eight full-chip EDA attempts including correction trials; reserve remaining attempts for a survivor, not three independent full-chip branches. Tool-build jobs are tracked separately. Stop earlier on failed gates. Re-budget only with written evidence and explicit scope; protect final submission validation time.

## Replacement rules and rejection conditions

All six G1 personalities must retain their documented functional behavior and operating settings. Preserve host/reset/parking/CRC safety. Paired compile-seed coverage uses the same declared small seed set (for example1,2,3,4); publish failures rather than selecting one lucky result. Model timing and configured timing remain separate metrics. No unmeasured power claim.

R1 must pass physical closure and establish a material gain. Preferred gain is useful concurrent operation that G1 cannot perform under the exact same external requirements. A four-register I2C target fitting and operating would be an alternative clear gain. If neither is feasible, any timing/host-service alternative must be quantified and declared before the final comparison, not chosen afterward to rescue a weak result. Extra LUTs or reduced wirelength alone do not satisfy the replacement rule.

Reject if preserved workloads fail, rates are reduced to manufacture fit, required host work grows without an agreed benefit, physical closure requires weaker constraints, or the new sealed evaluation exposes an unaccepted regression. No architecture-general claim follows from training-suite success. Report all candidate costs and failures.

## Execution and isolation

Keep G1 and compact checkpoints immutable. Exploration changes live separately; generated RTL is regenerated from its source, never patched by hand. Reuse authenticated evidence collection, independent resource/connectivity verification and rejection memory from the current routing work. GitHub executes heavy EDA and reproducible tool qualifications; the session owns hypotheses and acceptance. Use disjoint specialist tasks when available, without restarting agents to evade usage limits. No derived private routing manifest or external AI packet is transmitted while its specific approval remains pending.

For each experiment record source SHA, source/model hashes, tools, workload/settings, hypothesis, predicted distinguishing result, cost bound, actual result and rejection reason. One hardware variable per hardening. Phase6 G1 release work stays separate; successor exploration follows the reopened phase3 comparison gates rather than inheriting closed phase evidence.

## Measured G0 checkpoint

Compiler job39470166731 confirms all six G1 personalities fit, while UART+SPI needs103cells/3timers/3shifts with both engines hard-backed, or138cells/2pairs with soft SPI. All four variants fail native G1 placement. See ../reports/fresh_baseline_20261020.md. This corrects the initial resource hypothesis; no topology chosen. The separate hosted simulation job failed setup and has a dependency fix pending retry.

## Immediate next action after plan review

Run G0 baseline/concurrency characterization and write the exact capability specification. Do not select a topology or begin new production hardware from this planning document alone. The committed architecture contract changes only after the written candidate spec and comparative measurements required by D-037.

Evaluation seal established before topology tuning: HELDOUT_R1_MANIFEST.json binds four randomly selected roles by SHA256. Selected identities were not printed/read by the coordinator; all six pool roles remain excluded until freeze. This is procedural separation, not an independent evaluator. UART+I2C secondary workload now passes all four primitive selections locally against the existing independent target, including clock stretching and repeated START. Hosted expanded15case census pending.

Expanded census39471254787 at5f03060 passes both jobs; downloaded44executedPASS. UART+I2C needs123cells/3primitivepairs (allhard) or173cells/2pairs (hardUART/softI2C). See R1_REQUIREMENTS.md for the measured capability contract and area-screen alternatives. No new physical hardening launched.
