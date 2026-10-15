# WARP: evidence report

**October15 reproduction refresh:** clean hosted
[38777288608](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38777288608)
on77edd2d passes the documented fresh source/compile/RTL path. Independent
artifact review verifies loaded30/30, cosim1/1, all14XML hashes/counts,
200 listed-source fingerprints and11 rebuilt-image report hashes against
exact-revision committed images. Emitted images are omitted from the artifact;
the standalone UART image has same-job audit evidence only. This is no
physical/native timing refresh. [Exact evidence and omissions](reports/reproduction_refresh_20261015.md).

**October 15 status:** frozen G1 remains the supported fallback; phase 5 is
incomplete. Paired native routing38820879445 establishes a lower-total point:
original50-budget133 versus15-budget121 on identical authenticated views and
layer resources. Both routes still fail; Metal1/4 overflow worsens while
Metal2/3 improves. No physical acceptance or clock claim follows. Preserve
original50/133 separately from new15/121. Unchanged-control trace
[38676688402](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38676688402)
reproduces **133 native global-routing overflow**, retaining native failure.
It identifies long south/east detours, not routing closure. Exact source and
segment provenance: [route analysis](reports/route_trace_analysis_20261015.md).
Broad redistribution is rejected: native-feedback38453870785 has6000 overflow
and RUDY38321208948 has6544, against133. Keep those outcomes separate from G1.
Loaded active-window USER_RESET/STOP cancellation38676257805 passes on frozen
G1 with authenticated counter9/window256/delay4 parameters and70/88LC, under
D-023 scope. Hosted supervisor38777137622 passes63 checks; the four separate
campaign artifacts are independently verified on77edd2d: phase38777137234,
active-cancel38777137304, C-host38777137259 and nine compiler builds38777137439.
Unit38777137520's tools job passes, but its protocol job correctly exposes an
inapplicable UART skip; corrected discovery still needs its own hosted result.
[Integration evidence](reports/autonomous_integration_20261015.md) and
[numerical-source audit and remaining gates](reports/evidence_audit_20261015.md).

**October11 experimental progress:** actual routed eight-delay C2 reaches zero native physical gates38114298036, passes real SPI-loaded UART/USER_RESET38163199372, and clears the examined conditional internal setup/hold paths in all six extracted cases38164099529. Worst examined hold is+0.042992ns under unchanged margins. Scope and remaining annotation/I/O/loading/intertile/other-tile gates: [report](reports/compact_c2_delay_extracted_20261011.md). Separately, combined reset placement lowers paired native global-routing overflow146→133 in38168159774; both cases still fail routing. These are measured advances, not a complete successor or universal protocol/timing claim.

**Baseline software/bitstream progress:** autonomous delayed UART fault plus concurrent event counting passes genuine same-job SPI-loaded chip-port test38168609080, using57/88LC and2/2timers+2/2shifts. Additional loaded matrix38273574240 passes full UART TX waveform corruption, concurrent event counting and later clean-frame recovery for counter widths3/4; both use57LC, so no counter-width area gain is claimed. [Full-duplex loaded matrix38279446388](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38279446388) also passes concurrent RX during TX corruption for both counter widths. These tests retain existing D-023 RTL-fabric accommodations; native/SDF/full-chip timing and board operation remain separate. Portable C loading/recovery and architecture-authenticated pin mapping are independently tested; source cloud pytest38168413502 passes532checks.

**Portable C end-to-end evidence:** [38293580979](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38293580979) passes compiled-C checked loading through actual simulated SPI and31-byte ordered duplex exchange on a freshly compiled23/88LC hostecho image. Downloaded XML/image/report authentication and exact scope are recorded in [the status report](reports/status_and_hold_allocation_20261012.md).

For a reader with 20 minutes. Sources below include CI run IDs (GitHub Actions
on `efpga`) and historical local reports. The final numerical-source audit is
still open: a local report is not a CI run, and some historical timing views
are unavailable. Claims and their status: `docs/CLAIMS.md`. **Nothing here is
measured on silicon or a board; all results are simulation, formal proof, or
physical-design reports.**

AI tools (Claude and Codex) assisted project planning, source/tool/test changes,
prior-art research, report analysis and workflow diagnosis. AI-generated
suggestions are hypotheses until supported by the named checks and retained
evidence. Passing simulation, bounded formal properties and physical checks
are reported separately; AI review does not replace those checks. The worklog
records the experiments, failures, corrections and remaining limitations.

Key CI runs: [frozen-chip GDS, precheck and gate-level tests (36383587262)](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36383587262), [Phase 4 GDS and gate-level tests (36451108163)](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36451108163), [Phase 4 fabric tests and co-simulation (36451328356)](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36451328356), [protocol tests (36451328364)](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36451328364), [formal F1/F2/F4 (36383587298)](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/36383587298).

## 1. The problem and the constraint

The competition asks for a chip that can be reprogrammed after fabrication to speak hardware protocols (UART, SPI, I2C to start), on Tiny Tapeout (IHP 130 nm CMOS5L). WARP puts a small **FPGA fabric** on the chip, and chooses what that fabric contains from measurements.

The hard constraint is area. The historical tile study includes configuration,
switch matrix and routing ([dated setup and limitations](reports/tile_cmos5l.md));
its local per-cell area estimate is not repeated as a current verified number.
The generic **96-LUT4** grid was subsequently hardened in CI36353540402
([G0 results](reports/g0_results.md)).

## 2. What protocol logic is spent on

We wrote the four design-set protocols (UART, SPI controller, I2C controller,
I2C target) as ordinary Verilog and attributed every LUT to what it does.
The corrected hosted refresh
[38820879331](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38820879331)
atf8ed2a0 reports **555 LUT4s** across the current plain-logic design-set
sources: UART144, SPI85, I2C controller141 and I2C target185. Counters account
for125(22.5%), shift105(18.9%) and storage100(18.0%). All24LUT/carry trials,
actual raw cell counts and listed source/output hashes are retained; the
handwritten role map was reviewed after BUG93 exposed renamed state.
These are synthesis counts, distinct from placed fabric cells and the original
historical phase1 profile that motivated G1. The refresh does not reconstruct
that historical revision. [Current evidence](reports/profile_refresh_20261015.md);
[historical method and data](reports/profiling.md).

Before profiling we sealed a **held-out set** of four more protocols (WS2812, 1-Wire, SWD, CAN; commit 0171cf7) that no part of the architecture was allowed to see until the hardware was frozen (D-003).

## 3. The architecture, chosen at equal area

The generic hard blocks selected from profiling are a **loadable 16-bit timer** and an **8-bit shift register with a bit count** (D-002, D-026). The three supported design-set protocols use both; the I2C target uses the shift register but does not fit the chip. Two of each occupy one fabric tile slot in hardened G1(CI36376994834). The chip's fabric **G1** is a 4 × 3 grid with one slot holding them: **88 LUT4 + 2 timers + 2 shift registers**; the baseline **G0** has the same macro with all 12 slots LUT tiles (96 LUT4).

| Fabric (same macro, same area) | Design-set protocols that place and route | Logic cells: UART / SPI / I2C controller / I2C target |
|---|---|---|
| G0: 96 LUT4 | 1 of 4 | 124 / 86 / 115 / 184 |
| **G1: 88 LUT4 + hard blocks** | **3 of 4** | **29 / 47 / 70** / 169 |

Sources: `docs/reports/architecture_comparison.md` (chart `architecture_comparison.svg`), `g1_results.md`, `g0_results.md`; G1 fits checked in CI `fabric` (`compile.protocols --require`, e.g. 36376994866).

Phase 3 then tried three more specializations, each measured and dropped (D-030, D-031, D-034): a faster timer output (no gain for the slowest design), buffering inside the primitive tile (does not fit the tile), and a register-file tile (the I2C target still exceeds available logic). Their historical/local measurements and limits remain in the decision records and `docs/reports/g1_limits.md`. **G1 is the frozen chip** (`hw-freeze` → 3047dea, D-033); the I2C target does not fit and is not supported (D-035).

## 4. The chip

| | Result | Source |
|---|---|---|
| Tiny Tapeout flow | `gds`, precheck pass; routing DRC 0, LVS 0, antenna 0, Magic DRC 0 | CI 36383587262 (3047dea) |
| Shell timing at 50 MHz target | setup WS +12.48 ns (slow corner), hold WS +0.112 ns (fast); fabric is a black box to STA | same run; not configured-fabric timing |
| Shell | 3,723 standard cells, 60,567 µm² | same run |
| Fabric macro | 1016.64 × 669.06 µm, 88 LUT4 + 2 + 2 hard blocks | `macro/warp_g1`, D-027 |
| Formal | F1 output isolation (unbounded), F2 loader (BMC depth 84), F4 primitives = specification (unbounded) | CI `formal` 36367067725; `docs/reports/formal.md` |

Hardening history and every intermediate run: `docs/design/PHYSICAL_DESIGN_AND_CI.md`.

## 5. Reprogrammable after fabrication, shown on the hardened netlist

Real bitstreams, compiled from Verilog by `tools/compile`, are loaded through the chip's SPI host port (checked: architecture version, length, CRC-32) into the **gate-level chip netlist** and run: a counter, combinational logic, the host byte channel, both hard primitives, and the UART, SPI controller and I2C controller against independent reference devices. CI `gl_test` 36383587262: **21/21** (the fabric is modelled from its RTL, D-023). A loaded design can be replaced by another without a reset; a corrupt load leaves every pin parked and the chip refusing to run until a good load (`test_corrupt_load_over_running_design`).

**Showcase (D-036):** one simulated chip, never reset, loads **six protocols in turn** (UART, SPI, I2C, WS2812, 1-Wire, SWD) and each works against its reference device (`test_showcase_protocol_switching`; CI `gl_test` 36451108163 and `fabric` 36451328356).

## 6. Generality: the held-out protocols

Opened only after `hw-freeze`; each with a reference model written first from its own specification (`docs/reports/heldout_results.md`):

| Held-out protocol | Frozen chip (88 cells) | Plain G0 (96) | Result |
|---|---|---|---|
| WS2812 | **runs**, 32 cells | 82 | 8 LEDs through the host interface, within the datasheet's timing |
| 1-Wire | **runs**, 77 cells | 126: does not fit | reset/presence, READ ROM with CRC |
| SWD | **runs**, 44 cells | 61 | connect, DPIDR, AP write/read, WAIT; packets in host software |
| CAN 2.0A | does not fit (207) | 241 | correct in RTL only |

Every held-out design used the hard blocks, in ways the design set did not (a pulse-width generator, a 480 µs one-shot, an SWD bit clock, a CAN sample point). Chip-level tests pass in CI `gl_test` 36451108163 and `fabric` 36451328356.

## 7. The software side (D-032)

The organizers asked for the flow from a protocol description to a bitstream, how it is loaded, and working examples (`docs/USER_GUIDE.md`, `docs/EXAMPLES.md`): the compile flow (`tools/compile`: Verilog + pin map → checked bitstream + report), a demo-board loader and protocol helpers (`tools/board`, MicroPython), and UART/SPI/I2C examples. **The board code itself is tested against the chip model** (`test_board_loader`, `test_board_examples_spi`, `test_board_examples_i2c`); it has not run on a board.

## 8. Verification

| Layer | What | Evidence |
|---|---|---|
| Protocol designs | RTL tests against independent reference models (and sigrok), both forms (hard blocks / plain logic), 8 designs | CI `unit` 36451328364 |
| Chip, RTL fabric | chip-level tests loading real bitstreams through the pins | CI `fabric` 36451328356 |
| Chip, gate level | the same tests on the hardened shell netlist with fabric RTL | CI `gl_test` 36451108163 |
| Formal | F1, F2, F4 in CI; F3 FIFO depth2/depth4 unbounded ABC PDR proofs | CI `formal`36383587298; F3 both tasks36491754401, retained engine PASS/property-proved logs inspected; proof/RTL unchanged from that commit |
| Shell random transactions | SPI transactions checked against an independent model, with command × state and error coverage | `test_internal/uvm`, seed1 passes in hosted unit38780941428; historical local census remains in its report |
| Co-simulation | the UART as a bitstream vs its source RTL: identical TX waveforms, equal RX | `test_internal/cosim`; CI `fabric` 36451328356 |
| Mutation | All6 pristine controls pass; all11 planted defects have executed assertion/property rejection | Hosted38823961384 at454b9e0; `docs/reports/mutation_evidence_repair_20261015.md` |
| Timing model | historical local primitive boundary-path cross-check; matching original tile netlist/SPEF unavailable for a fresh audit | `tools/timing/README.md`, D-028; [artifact gap](reports/reproduction.md) |

Bugs and investigations, with the checks and limits recorded for each: `docs/BUGS.md`.

## 9. Known limits

- **No hardware results**: no silicon, no board. Protocol Fmax values in the historical local reports are compiler-model estimates, not validated whole-chip rates; original routed primitive timing views remain unavailable for a fresh cross-check (`tools/timing/README.md`, [artifact gap](reports/reproduction.md)).
- **Capacity**: 88 cells; the I2C target and CAN do not fit. One bitstream runs at a time, but it can contain concurrent functions: UART-plus-event-monitor fits at 37/88 cells and passes local loaded RTL/synthesized gate-shell tests (`docs/reports/g1_uart_monitor.md`, C11) and fresh hosted compile/loaded RTL in37512249763. There is no new hardened macro/SDF result from that hosted demonstration.
- **Fault-control showcase**: the UART/monitor plus externally timed TX line inversion fits at38/88 cells and passes two-case loaded RTL and synthesized-shell suites (`docs/reports/g1_uart_fault_monitor.md`, C12). This controls selected corruption and preserves monitoring; it is not an autonomous fault scheduler or a silicon result.
- **Soft capture**: UART plus a two-entry six-bit timestamp queue fits at83/88cells and passes loaded ordering/overflow/wrap/backpressure/TX/RX/reset tests (`docs/reports/g1_uart_capture.md`, C13). Default timestamps wrap at64clocks; an85-cell option trades four-clock resolution for256-clock wrap, with loaded quantization/wrap checks. The eight-bit stored timestamp version exceeds capacity at91cells. No new hardware or native gate timing evidence.
- **Host link**: one byte per SPI transaction; a protocol needing a byte every few µs (WS2812) needs a fast host.
- **Parked outputs are 0**: active-low signals on `uo_out` pins are asserted while stopped (BUGS #19); use a bidirectional pin with a pull-up.
- **Gate-level fabric**: chip tests simulate the fabric from its RTL, not its hardened netlist (D-023); per-tile netlist-vs-RTL equivalence is not done.
- **Prior art**: FPGA fabrics on Tiny Tapeout exist (Tiny FABulous, SKY130), as does a Verilog-programmed protocol engine on IHP (PRISM); what WARP adds is the measured, held-out-tested choice of architecture (`docs/notes/prior_art.md`).

## 10. October7 verification and experimental successor

Fresh README reproduction37690896748, commit962da93, executes documented
setup/check/rebuild/compile commands with pinned tool/package checks and no
prior build output. Downloaded strict XML verifies30 loaded-fabric cases and
1 UART source-versus-fabric cosim case, no failures or skips in either suite.
Default idle/parameter-specific skips are separately recorded. This closes
the clean-machine README item, not missing historic routed-tile timing evidence.
Details: `docs/reports/reproduction.md`, C-readme-reproduction.

Independent loaded G1 UART phase/read-delay stress37671919707 passes48 bytes
over3 seeds, including early/late bit-edge phases and delayed reads, with no
framing/overrun/stale-byte failures. This improves robustness evidence for the
fallback without a hardware change or a new physical rate claim (C-uart-phase).

The compact successor remains an experiment. Native repair37669731197 and
same-layout physical follow-up37674839060 provide routing/Magic/KLayout/shell
LVS0, with shell setup/hold passing but slew9/fanout33 still open. Stronger
driver placement37689324316 is legal, but its first route37690243797 failed
connectivity on stale moved-pin wires. Corrected37708459393 now passes native0,
antenna0, Magic0/KLayout0/shell LVS0 and fresh all-corner slew/setup/hold/cap0.
Fanout33 remains. Actual report/hashes: compact_driver_native_20261008.md.
Native C2 stage37708777882 failed all six cases before UART: the diagnostic
found14 unknown named configuration signals in the control and12 in each
C2 substitution. BUG47 proves these were unused constant-X aliases, not live
latches. Corrected37709917442 passes both control cases with9164 real latches
known/matching; original synthesis/finalC2 substitutions fail real UART X
despite the same complete configuration pass. The functional issue is present
at original synthesis, with exact cause still under investigation.
At that historical checkpoint, d826baf docs37708777806/lint37708777982/test37708777749/unit37708777707
all pass. No compact promotion, matched native/configured
timing or equal-area superiority claim follows from these scratch results.
Exact hashes/limits: `docs/reports/compact_clean_layout_20261007.md` and
`docs/reports/compact_fanout_native_next_20261007.md`.

## 11. October 10 compact diagnostic update

The unchanged stronger-driver layout now passes all nine unmodified official
IHP prechecks in [37960021923](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37960021923).
This complements its native physical results in37708459393; it does not
qualify the subsequent fanout-buffer layout or configured fabric timing.

The regenerated C2 tile's exact routed final netlist passes real SPI-loaded
UART, STOP and USER_RESET in both candidate cases, with both controls also
passing in [37958116481](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37958116481).
All9164 actual configuration latches match the842-word image; each case checks
28TX/28RX bytes. This is one substituted tile type with regenerated control
netlists elsewhere, no SDF. The original mapped C2 failure remains a separate
open issue; the passing final tile retains its original deferred virtual-clock
timing failure and62 fanout violations per corner from37814078650.

The shell ten-buffer experiment eliminates the five remaining fanout violations
in all three explicitly evaluated estimated corners in37956470190. It moves
1550 original cells, so it cannot inherit the stronger-driver layout's route.
Paired actual150-iteration global routing in
[38100977984](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38100977984)
still fails: cluster8 baseline149 overflow, ten-buffer candidate169. The
50-iteration native hotspot collection in
[38100978078](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38100978078)
successfully retains actual coordinate/net reports while preserving routing
failure148/169. Diagnostic collection success is not routing acceptance.

At that historical checkpoint, planned experiments aimed to isolate incidental
legalization movement and establish genuine image-selected register clocks. Neither full compact qualification,
an operating frequency nor equal-area superiority is established. See
`docs/reports/compact_congestion_research_20261009.md` and
`docs/reports/compact_configured_timing_plan_20261009.md`.

The fixed-original counterfactual subsequently passes in
[38101405271](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38101405271):
all3596 original placements/orientations/masters/statuses remain exact, movement0,
with the same ten buffer connections and all three explicit estimated candidate
fanout/slew/cap/setup/hold violation counts0. See
`docs/reports/compact_fixed_original_buffers_20261010.md`. Fresh native routing
and extraction remain necessary; this is no configured-fabric timing pass.

Its fresh paired native GRT38101639866 still fails148baseline/146candidate,
improving the older moved-cell169 result without closing routing. BMC84/cover84
38102131236 passes the explicit bounded RUN-mode properties, not arbitrary
complete-frame or mapped-latch stability. Conditional internal C2 timing
38111705892 examines the exact loaded UART image with a propagated clock and
nominal SPEF across three PVT libraries: setup positive on examined paths,
fast hold−0.03/−0.04ns at two positions. No full timing pass; unconstrained
loading/I/O/intertile paths persist. See
[conditional timing report](reports/compact_conditional_c2_sta_20261010.md).
Independent frozen-G1 seed sweep38101717810 compiles all nine design-set trials;
its model timing is not ASIC timing or newly loaded functionality.
