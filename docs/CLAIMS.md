# TRIPWIRE claims and evidence

**Current qualification:** claim 28 and [the baseline](BASELINE.md) supersede the pending official-integration status of earlier experimental claims. Earlier rows describe the artifact and date named in each row, not additional present-day blockers.

Every claim made in the README or the submission, with its evidence and blind spot.
Evidence status is one of: **proven unbounded**, **proven bounded (depth N)**, **tested**, **simulated only**, **not yet verified**.

Never claim: zero latency, sub-ns timing, USB/Ethernet support, real-hardware testing, or "formally verified" without naming the property and its bound.

| # | Claim | Evidence (check ID, run, file) | Status | Blind spot |
|---|---|---|---|---|
| 1 | The chip RTL runs `programs/uart.trw`, `spi_controller.trw` and `i2c_controller.trw` loaded through its SPI host link: UART TX at 9600, 115200 and 1 Mbaud, UART RX at 115200 and 460800 baud with framing errors reported, SPI controller mode 0 at 1, 5 and 8.3 MHz, I2C controller at 100 kHz, ~400 kHz and 1 MHz with clock stretching (up to longer than an SCL period), NACK and repeated START | L3 on `trw_chip` through the pins (`test_internal/chip/test_l3.py`), each against a reference model (`tools/protomodels`) **and** sigrok's decoder; RTL and the Yosys gate-level netlist (TT Icarus 13), 2026-09-27, local runs (WORKLOG) | simulated only | Matching R4 hardened netlist passed the required four cases in run 36952644578 and expanded 22-case suite in run 37144286224 (GDS 36799356107, candidate 3393eea); no hardware or slow-corner timing closure. Main TT top is not switched (D-047). Not covered (the shipped programs do not implement them, D-048): UART parity, SPI modes 1–3 and 16-bit, I2C arbitration loss. Continuous UART RX above ~460 kbaud overruns (see Known limits) |

| 2 | The expanded22-case L3 protocol suite passes on the SRAM-buffer trial's final routed netlist | [Run37499559483](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37499559483); downloaded JUnit22cases/0failures/0errors/0skips; scenarios in `test_internal/chip/test_l3.py` | simulated only | Specific scenarios, not exhaustive conformance or simultaneous operation; no SDF, silicon or timing-closure claim |
| 3 | The SRAM-buffer2/4 trial has extracted slow setup WS−1.385050335848ns and positive hold WS at all three measured corners | [Extracted diagnostic37499559422](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37499559422), after route37490897034; PHASE2_INDEPENDENT_TIMING_SCREENS.md | tested | Still fails setup; split diagnostic is not official complete GDS signoff; applies to this exact2/4 physical trial, not frozen3/6 |
| 4 | Isolated bs-resync rewrite preserves bit-clock-module behavior under the stated equivalence proof and improves the targeted ideal-wire mapped-delay probe |893module-equivalence points, equiv_simple plus induction closing at step1 withseq2 cap;21unit tests,5chip tests,2048L2 clocks; PHASE2_TIMING_PROTOTYPES.md | tested | Not whole-chip formal proof; local13.808641→10.669182ns delay is not extracted WNS and physical screen remains pending |

| 5 | The event-late 2/4 trial with 150 ps repair has extracted fast hold +0.067033714 ns but slow setup −0.389409405 ns | [Extraction 37566926240](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37566926240), routing37559740009; PHASE2_EVENT_HOLD_HEADROOM.md | tested | Fails setup; split diagnostic, not official GDS closure |
| 6 | That repaired netlist passes the expanded 22-case protocol suite | [Routed GL 37566926287](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37566926287), actual log22PASS/0FAIL/0SKIP | simulated only | No SDF or silicon evidence; specific protocol scenarios, not exhaustive conformance |
| 7 | Isolated late-selection RX timer arithmetic preserves trw_pin_rx under the named module-equivalence proof at FRAC4/8 | Yosys equiv_simple and equiv_induct with seq2 cap, equiv_status -assert; /tmp/rx-timer-late-20261006 and PHASE2_RX_TIMER_LATE.md | tested | Module proof, not whole-chip formal verification; mapped delay gains have substantial area cost and no routed timing evidence |

| 8 | The residual three-cell2/4 checkpoint has nonnegative extracted setup WS at all three measured corners and minimum hold+0.062788609ns, and passes22/22 routed protocol tests | Extraction37844735445 after routing37837038264; GL37844735520; PHASE2_EXTRACTED_TIMING_MARGIN.md | tested | Global setupWS0 includes latch time borrowing; electrical checks still report slew/cap violations; not official clean-build signoff, SDF simulation or hardware evidence |
| 9 | The same extracted checkpoint tolerates a clock-period reduction from20ns to19.85ns in the local all-corner STA sweep |21 STA processes; all six20ns baseline metrics match CI within1e-6ns; PHASE2_EXTRACTED_TIMING_MARGIN.md | tested | Fixed parasitics and constraints, not a new physical build or a universal150ps per-path margin; slow setup fails at19.75ns |

| 10 | The full 2/4 event-late checkpoint passes extracted setup/hold and electrical gates at 20 ns across the three measured corners, with zero final route DRC and antenna violations | [Route/extraction 38784492656](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38784492656); final netlist SHA ac646d7424b75d53d61c5726dac5a83780753dd397e4b2b45c1a90b11ed8221d; PHASE2_CLEAN_EXTRACTED_BASELINE.md | tested | Setup WS 0 is not positive global setup margin. Checkpoint ECO experiment, not official clean-build GDS/LVS/precheck. Exact-byte protocol GL [38796998628](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38796998628) passes 22/22 exercised cases; no exhaustive conformance, SDF or silicon claim |

| 11 | Isolated unit-local configuration staging preserves the checked configuration behavior and passes the 22-case RTL protocol suite | Clocked-host sequential module equivalence for basic/full × latch/flop builds (403/385/445/399 points, induction cap6), 10400 phase comparisons per build; full Verilator22/22, no skips, 2026-10-20; [PHASE2_CFG_STAGING.md](https://github.com/Kanishk234/protocol-emulator-asic/blob/9b440582c489b228f8306a137f3a722bdfa8ed2a/docs/reports/PHASE2_CFG_STAGING.md) | tested | Proof assumes actual same-clock registered host drive; not arbitrary asynchronous inputs or whole-chip formal. Specific simulated protocol cases only, no SDF, routed timing, official GDS or silicon evidence |
| 12 | That isolated trial reduces locally mapped U0 staging-bit4 latch loads from153to22, with64more flops and about1.258% more standard-cell area | Paired frozen event-late baseline/trial Yosys flatten/dfflibmap/ABC with the same typical CMOS5L library, macro unchanged; mapping_comparison.json and stat files in /tmp/tripwire-cfg-staging-verified-20261020; [PHASE2_CFG_STAGING.md](https://github.com/Kanishk234/protocol-emulator-asic/blob/9b440582c489b228f8306a137f3a722bdfa8ed2a/docs/reports/PHASE2_CFG_STAGING.md) | tested | Local mapping differs from native LibreLane synthesis. Native screen39378465307 fails slew reserves and the independently checked setup guard. No extracted timing, route overflow or total die-area improvement is established |

| 13 | The isolated resync/event plus unit-local staging combination passes the checked module equivalence, phase and 22-case RTL protocol regressions | 892bit-clock proof points, four registered-host configuration proofs (403/385/445/399), 10400phase comparisons per build;60full-pin/5chip tests,2048L2clocks; Verilator22/22 no skips in207.42s; [PHASE2_CFG_STAGING.md](https://github.com/Kanishk234/protocol-emulator-asic/blob/9b440582c489b228f8306a137f3a722bdfa8ed2a/docs/reports/PHASE2_CFG_STAGING.md#exact-netlist-diagnosis-and-composed-follow-up) | tested | Named module proofs with host-drive scope, not whole-chip formal; simulated cases only. Native screen39458833532 measures+2.531ns slow capture and+116ps fast hold but fails setup/slew reserves; no routed or official GDS clearance |

| 14 | Isolated TX cursor late selection passes the checked arithmetic and protocol regressions and improves one local ideal-wire timing metric | 511module equivalence points;60pin/5chip tests,2048L2clocks,22/22expanded Verilator protocol cases without skips; paired mapping saves85cells/0.097% standard-cell area; slow-library input→cursor D12.693307→11.702561ns; [PHASE2_ARITHMETIC_FOLLOWUPS.md](https://github.com/Kanishk234/protocol-emulator-asic/blob/9b440582c489b228f8306a137f3a722bdfa8ed2a/docs/reports/PHASE2_ARITHMETIC_FOLLOWUPS.md) | tested | Module/default-parameter proof and simulated cases, not whole-chip formal or exhaustive conformance. Ideal-wire local timing, not extracted or official closure; no physical reserve pass yet |

| 15 | Isolated cached fabric selection preserves the checked port behavior and passes the22-case RTL protocol suite | For every legal N1..16: original→named-reference equivalence98points and reference→cached99..114points, induction cap4; wrong-enable mutation rejected;7fabric/5chip tests,2048L2clocks, Verilator22/22 no skips in348.97s; D-096 and source-hashed /tmp/tripwire-cached-port-select-20261020/cached_select_receipt.json | tested | Module proofs with reset/state correspondence, not whole-chip formal or pre-reset behavior. Local mapping adds52flops/0.898% standard-cell area; isolated ideal-wire timing is not physical or official closure. Native screen pending |

| 16 | The clean-reproduced full2/4/U0-full/SRAM experimental candidate passes measured extracted timing/electrical/routing/antenna gates, final22-case protocol replay, LVS and unchanged Tiny Tapeout precheck on its exact GDS | Route39868597887; final GL39880054906 XML22/22/0skips; LVS39883160399; precheck39890538270 XML9/9 including SG13CMOS5L DRC; PHASE2_PASSING_ROUTE_INTEGRATION.md | tested | Specific experimental artifact, not main official GDS workflow/Phase2 completion. SetupWS0 is not positive global margin; no SDF/silicon/exhaustive protocol claim. Raw Magic diagnostic39883160399 remains failed on recorded macro-contained markers; official continuous source/recipe integration unfinished |

The candidate in claim16 was subsequently reproduced end-to-end from fresh RTL without downloaded physical checkpoints in [39907035580](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39907035580). Fresh extracted results reproduce setupWS0/fast hold+107.281ps, electrical0; GDS/LVS pass and unchanged TT precheck XML9/9 passes with0CMOS5L DRC items. This remains separate orchestration, not the main official GDS workflow. See PHASE2_PASSING_ROUTE_INTEGRATION.md for artifact hashes and the main-integration gap.

| 17 | Isolated lane arbitration preselection preserves the checked default-AW9 lane behavior and shortens one local mapped SRAM-input cone without new state | 2157whole-lane/ALU equivalence points, induction sequence cap2; one-step winner contract and wrong-urgent mutant rejection;6lane/4top/5chip tests,22/22protocolcases no skips with offline sigrok,and full-design lint; late_arbitration_evidence.json and replay helper | tested | Named module equivalence, not whole-chip formal, four-state pre-reset behavior or routed timing. Gate levels25→14are unweighted local mapped counts, not slack; area adds4213.188um²per lane in that mapping. Simulated protocol cases only; physical40723256006fails setup/hold/electrical/antenna/overflow; no Phase2/official GDS claim |

| 18 | Isolated shared-data priority preselection preserves the checked default-AW9lane behavior and reduces one local mapped SRAM-input logic depth with small mapped overhead | 2169whole-lane/ALU equivalence points,induction sequencecap2; one-step winner contract and wrong-urgent mutant rejection;6lane/4top/5chip tests,22/22Icarus protocol cases with0skips,and strict lint; shared_priority_evidence.json | tested | Named module equivalence,not whole-chip formal or physical timing. Localunweighteddepth25→18and+16cells/+206.766um²perlaneare comparative mapping only. Simulated protocol cases only. Physical40779354529passes setup/50psfast hold/electrical/overflow but fails five antenna nets; setupWS0does not establish positive reserve. No Phase2/official GDS claim |

| 19 | Coarse host configuration-address predecode preserves the checked write interface and configuration visibility | config_word_select_evidence.json: SPI139/host924or942equivalence points (sequence cap2),four full/lean latch/flop phase contracts (induction up to16),wrong-selector negative controls;7host/4top/5chip/22protocol RTL tests and strict lint | tested | Named module/property proofs,not whole-chip formal or pre-reset four-state equivalence. Exercised RTL protocol cases,not exhaustive conformance,SDF or silicon. Six additional mapped flops; local area varies with mapping order and does not establish routed area/timing/antenna closure. Physical41506944920fails fast hold(−22.3809ps),three antenna nets and7overflow; no qualifying physical/official result |

D-138 is a prepared physical diagnostic, not a new passing-design claim. Its source matches claim18/reference40779354529. Native minimum-buffer settings and170 guard checks do not establish timing or antenna closure; see minimum_buffer_evidence.json. Clock-spacing41532160370 timed out before final qualification. Minimum-buffer41569397169 completes with setupWS0all corners,fast hold144.394ps,electrical0,overflow0,but four antenna failures; see minimum_buffer_result.json. No qualifying screen or extracted/official result follows from this.

| 20 | Native net/instance protection preserves the tested tiny relay connection under20µmwire repair that splits the unprotected control |41684924544;protected_endpoint/result_41684924544.json;independent final-netlist/raw-metric checks | tested | Tiny stock-flow feasibility only. Both cases antenna-clean;does not establish diode efficacy on failing antennas,all-corner/extracted timing,full-design screen or official GDS closure |

| 21 | The isolated constant-bank root-clock storage prototype preserves the checked slot-module behavior and passes the matched22-case RTL protocol suite | slot_root_storage/evidence.json; verify_slot_root_storage.py:768ASIC/752FPGA equivalence points, inductioncap6; mapped IHP-cell3125cycle/12288phase replay and wrong-reset negative control; XMLSHA880b91a24b74fcdc4e9d160948338da8f1d5249c9895d58cde6b4d0e8e16db79 | tested | Prototype only; no whole-chip formal, final routed GL, extracted timing, silicon or official GDS closure. Isolated mapped area is not final physical area. |

| 22 | Candidate43390348317 passes the checked million-clock RTL/model scenario and chip/SRAM RTL tests | Source258186504e4b9f73d2711067e456494def705d2b; pending_drop_polarity/parallel_verification.json binds RTL and XML hashes:1,000,000clocks/zero divergences,6/6chip/SRAM checks | tested | Two lanes/four units/U0full. One deterministic scenario; not exhaustive, refreshed mutation, final GL, silicon, extracted timing or official GDS evidence. |

| 23 | The same checkpoint has positive measured GRT-estimated setup reserve at functional flop/output endpoints | Native read-only audit43629200280: fast12.527966ns/typ8.897943ns/slow2.533495ns,2414flops/24outputs; source view hashes unchanged and ordinary metrics reproduced | tested | Estimated routing only; ordinary latch/all-endpoint checks retained. AggregateWS0 remains clamped. Does not establish extracted timing, antenna/DRC closure or Phase2 completion. |

| 24 | Exact pad-owner candidate passes the checked million-clock scenario, both injection controls and required RTL decoder cases | pad_owner_or/parallel_verification.json binds source and XML hashes:1,000,000clocks/zero divergences; priority/cursor faults detected99/326; four UART/SPI/I2C cases pass with real sigrok | tested | Two lanes/four units/U0full; deterministic RTL evidence, not whole-chip formal, final routed GL, stock-constrained extracted closure or official GDS.18unselected cases in targeted decoder run are not credited. |

| 25 | Same-edge engine output materialization improves the matched ideal-wire timing frontier and passes the checked RTL behaviors | level_cache/candidate.json: slow setup6.125→6.510ns, measured IDLE-launch6.801030→8.817179ns, +0.18% cell area/+4flops; scoped engine proofs/mutants,5two-phase chip comparisons,22/22protocol cases | tested | ASIC root-clock IDLE contract; optional sigrok disabled in expanded suite. Not whole-chip formal, FPGA fallback qualification, native physical or official GDS closure. |

| 26 | The configured native8x4 full2-lane/4-unit candidate passes the current pre-route gates | Screen44017640255/e04f800: slow functional setup+2.784036ns, stock fast hold+.102192ns, fresh antenna/electrical0; source/view/netlist/engine checks and independent artifact review pass | tested | Supported final-antenna project config, not unmodified Classic ordering. Routing evidence: preceding full-route overflow0plus congestion-prohibited native incremental repair. Not extracted timing, routed protocol replay, main adoption, official GDS/precheck, silicon or Phase2 completion. |

| 27 | The exact qualified candidate passes detailed routing and stock-constrained extracted timing/physical gates | Workflow44031468510/c5824b6: fresh route DRC0; extracted functional slow setup+0.163304ns, fast hold+.150773287ns at0.25ns uncertainty, timing/electrical/antenna violations0; extracted_result_44031468510.json | tested | Ordinary aggregate setupWS0remains distinct from positive functional reserve. Independent routed artifact review passes; full routed protocol replay passes44123392388; main integration is D-184; official GDS-precheck still pending; no silicon or Phase2 completion claim. |

| 28 | The integrated full design passes the unchanged official Tiny Tapeout workflow | 44189196098/e19556e: GDS,precheck10of10,GL3of3,viewer success; required main CI green; final artifact review confirms routing/KLayout/LVS/antenna0, all-corner timing/electrical0, fast hold+0.150773ns; exact officialNL matches22-case replay44123392388 | tested | D-185explicitly waives unsupported SRAM MagicDRC/abstract-overlap gates;10known raw markers remain. Ordinary setupWS0is distinct from+0.163304nsactual slow functional reserve on matching physical data. No silicon claim; Current L2 passes1,000,000clocks/0divergences with both injected faults detected; closure CI7f3ae9a is all green and Phase2exit criteria pass. |

## Known limits (state them wherever the related claim appears)


- **Host link throughput.** At SCK = clk/8 (the §9 limit) one HOST_OUT read (status and data in one transaction) takes ~560 clocks, so the host drains at most ~89K tokens/s at 50 MHz. A program that turns every received byte into a HOST_OUT token overruns its pin unit (§4.5: the new token is dropped and OVERRUN set) when bytes arrive faster than that: continuous UART RX above ~460 kbaud (a byte every ~1,085 clocks). Found by L3 on the RTL, 2026-09-27. Faster streams need buffering in firmware (a lane or SRAM ring) or a faster host clock.


## Phase 3 firmware evidence

| ID | Claim | Evidence | Status | Limits |
|---|---|---|---|---|
| 29 | The existing qualified chip runs SRAM-backed I2C memory firmware in the exercised 400 kHz and 1 MHz scenarios | [Milestone report](reports/PHASE3_I2C_MEMORY.md), phase3_i2c_ack_revalidation.json: 24 focused model/controller/oracle checks included in 360 model/compiler regressions; RTL and exact official NL each pass all three profiles with required sigrok; corrected conservative sampled ACK setup bounds 620/220/340 ns | simulated only | No new hardware/GDS/timing claim; volatile immediate writes, not full 24xx02 or electrical conformance. Mid-byte aborts, compiler-derived ACK bound and silicon testing remain unqualified; subsequent independent peer evidence is claim 30. |
| 30 | The SRAM-backed I2C memory firmware interoperates with an independent third-party RTL controller | [Peer report](reports/PHASE3_I2C_PEER.md), phase3_i2c_peer_result.json: pinned MIT controller a65be404; Verilator/Icarus and exact official NL each pass both profiles, including measured 1 MHz, required sigrok, readback, wrap and wrong-address NACKs | simulated only | Testbench-only peer; no new ASIC protocol block or physical result. Not exhaustive protocol/electrical conformance, compiler-bound proof or silicon testing. |
| 31 | Separate guarded I2C memory firmware recovers the exercised interrupted-transfer cases using existing hardware | [Guard report](reports/PHASE3_I2C_GUARD.md), phase3_i2c_guard_result.json: 190 guarded model recovery cases, RTL and exact official-netlist timing/recovery plus independent RTL-peer interoperability | simulated only | Uses U0 + U1 and reserves uo7; original one-unit example unchanged. Finite coverage, not full conformance; compiler reaction bound and silicon testing remain open. |
| 32 | Compiler reports conditional local urgent-slot selection using encoded readiness and both scheduler modes | [Selection report](reports/PHASE3_REACTION_SELECTION.md), phase3_reaction_selection_result.json: 24 focused checks, 10,000 independent-model snapshots, 597 full-suite tests; all 22 firmware images unchanged | static analysis, finite cross-checks | Assumes readiness at one eligible EVAL; possible competitors remain unknown delay. No end-to-end pin clock bound, liveness/deadlock certificate, L6-FUZZ completion or formal proof. |
| 33 | Opt-in compiler contracts bound memory ACK token submission at 4 clocks for address and 2 for write data | [Token-bound report](reports/PHASE3_ACK_TOKEN_BOUND.md), phase3_ack_token_bound_result.json: 2,080 cases across both programs, 6,240 independent model runs, Icarus/Verilator exact lane checks, 636 full Python tests | conditional bounded checking | From an already visible lane input token to a visible output token, with idle initial pipeline, free outputs and no new arrivals. Not a pin-to-pin bound, full ACK deadline, formal proof or whole-program deadlock certificate. |
| 34 | Conditional linked-edge composition gives 8/6 clocks to arm address/write ACKs on the unchanged memory firmware | [Edge-budget report](reports/PHASE3_ACK_EDGE_BUDGET.md), phase3_ack_edge_budget_result.json: 716 Python tests, 1,120 model ACK paths, 350 internal ACK checks per RTL simulator and 40 exact-official-netlist port checks | conditional budget plus finite observations | Assumes documented entry, queue, selection and arrival premises and 20 ns profile clock. General environment invariants are not proved. Port-only netlist checks do not inspect internal premises; no SDF, analog, silicon, WNS or Phase 3 completion claim. |
| 35 | Straight-line memory routines have conditional service envelopes of 19/51/31 clocks for refresh/store/read-advance | [Service report](reports/PHASE3_MEMORY_SERVICE.md), phase3_memory_service_result.json: 6,144 model runs and 96 actual lane/SRAM RTL cases per simulator; access counts checked | conditional architecture-derived bound plus finite cross-checks | Requires a running lane with one SRAM slot per four clocks and no selected reflex actions or host/configuration writes. Corrects the old 48-clock store report. No universal arrival/queue, delimiter-interference, formal, physical timing or Phase 3 completion claim. |
| 36 | An explicit two-reflex interference budget gives a 59-clock memory-store envelope | [Delimiter report](reports/PHASE3_DELIMITER_SERVICE.md), phase3_delimiter_service_result.json: 1,616 model and 1,616 cases per RTL simulator; observed store maximum52clocks; model guard/multicast checks and blocked-consumer negative control | conditional service plus finite cross-checks | The two-action budget is an assumption, not a proved external arrival count. Guard settling is measured only in the model from an internal published command. No unconditional pin deadline, new physical result, formal proof or Phase3completion claim. |
| 37 | The guarded I2C memory showcase meets its finite 400kHz/1MHz demonstration and compiler-matched ACK checkpoint | [Deadline evidence](reports/PHASE3_I2C_DEADLINE_EVIDENCE.md), phase3_i2c_deadline_evidence.json: 828 Python tests, 198 wire/service workloads, 1,586 matched delimiters, 2,354 completed routines; prior matching-image RTL/netlist ACK receipts linked | finite tested workloads plus conditional compiler bounds | New wire-to-guard metrics are model-only: at most26clocks and at least12clocks before the next first SCL rise. Original one-unit recovery gap remains outside the guarded claim. Volatile immediate-write memory, not full EEPROM/NVM, analog, universal arrival/deadlock, formal, new physical signoff or Phase3completion claim. |
| 38 | A firmware SPI memory window serves READ/FAST_READ at the tested 250/333/500kHz rates | [SPI memory report](reports/PHASE3_SPI_MEMORY.md), phase3_spi_memory_result.json: 939 Python tests plus final four-phase checks; Icarus/Verilator/exact-official-netlist each2of2; 12 complete reads and22abort/recovery pairs per simulator/artifact; independent spi/spiflash decoding | finite functional simulation | Mode0, 256-byte volatile aliased window, documented CS timing; selected header/dummy MISO unspecified. No program/erase/ID/status/NVM, full flash-device, analog, exact maximum frequency, new physical signoff, exhaustive recovery or Phase3completion claim. |
| 39 | Firmware 1-Wire profiles perform real standard-speed overdrive entry, faster ROM reads and standard exit | [Overdrive report](reports/PHASE3_ONEWIRE_OVERDRIVE.md), phase3_onewire_overdrive_result.json: 952 Python tests; model and Icarus/Verilator/exact-official-netlist each2of2; byte-identical transition captures, independent decode and four presence corners | finite functional simulation and sampled timing checks | Single-peer ROM-layer subset with idle host reconfiguration; original standard image retained. One specifically audited stock decoder recovery warning remains with raw-edge and synthetic-control evidence. No DS18B20-overdrive, EEPROM-function, multidrop, parasite-power, analog, silicon, new physical signoff or Phase3completion claim. |


| 40 | Existing PS/2 firmware rejects tested framing/parity faults and recovers on the following clock-complete frame; raw captures independently decode without recorder-only edges | [PS/2 evidence](reports/PHASE3_PS2_FRAMING.md), phase3_ps2_framing_result.json; 144 model scenarios/288 frames, full Python1117pass; three selected chip cases pass on Icarus/Verilator/exact official netlist44189196098 | tested | All eight start/parity/stop fault combinations at three model rates; sixteen chip frames at fastest tested rate. Sigrok validates valid-start prefix and legacy RX; raw oracle classifies malformed starts. No arbitrary lost/extra clocks, partial-frame recovery, analog, SDF, silicon or Phase3completion claim. |


| 41 | Existing hardware multicasts validated UART RX to host capture and a second-lane valid-byte echo | [UART multicast evidence](reports/PHASE3_UART_MULTICAST.md), phase3_uart_multicast_result.json; eight model tests and both profiles on Icarus, Verilator and exact official netlist44189196098, zero selected failures/skips | tested | 115200/460800baud; both blocking consumers must be serviced. Three malformed stop frames per chip profile produce raw ERR tokens and no echo. Sustained no-host-service model workload overruns RX as expected. No on-chip SRAM recorder, sustained1Mbaudcapture, arbitrary malformed-line recovery, analog, SDF, silicon or Phase3completion claim. |


| 42 | Three complete real-device recordings decode identically to sigrok when replayed on the unchanged qualified hardware | [Recorded-capture report](reports/PHASE3_RECORDED_CAPTURES.md), phase3_recorded_captures_result.json; original SR hashes pinned, model/Icarus/Verilator/exact official netlist3/3PASS; Python1145PASS | tested | STM32 UART42bytes, PCA9571 I2C one access with address/data/ACK/START/STOP, CC1101 SPI five MOSI bytes. Digital samples preserved with less than20nsedge quantization; SPI uses bounded64-word SRAM capture. No real TRIPWIRE hardware test, analog validation, arbitrary traffic, full archive or Phase3completion claim. |


| 43 | Adding an unserviced tap leaves the tested UART/SPI/I2C blocking paths unchanged | [L4-TAP report](reports/PHASE3_METAMORPHIC_TAP.md), phase3_metamorphic_tap_result.json; 16modelpairs/517960comparedclocks, three blocking negatives; Icarus/Verilator/exact official netlist3/3PASS; Python1164PASS | tested | Finite workloads; model checks every active-path clock, RTL/gates compare protocol traces and transaction-observed host delivery. Tap drops6/5/30in chip cases; its own drops/IRQ change intentionally. No unbounded isolation, whole-chip formal, SDF, silicon, full L4 or Phase3completion claim. |


| 44 | Two-lane UART/SPI/I2C pad loopbacks preserve the tested byte stream with deterministic inter-frame idle insertion | [LOOP/IDLE evidence](reports/PHASE3_METAMORPHIC_LOOP_IDLE.md), phase3_metamorphic_loop_idle_result.json; 24modelruns/eightprofiles/192roundtrips plus three disconnected negatives; both RTL simulators/exact official netlist3/3PASS; Python1175PASS | tested | Test-only firmware fits existing2lanes/4units; baseline/idle images identical. Independent UART TX/RX, SPI MOSI/MISO and I2C write/read decoding; actual later frame starts move. Finite data/rate/idle profiles only; no silicon/analog, timing-signoff change, full L4 or Phase3completion claim. |


| 45 | Declared fast-path lane/unit permutations preserve tested UART/SPI-controller/I2C-target sampled traces and host observations | [PERM evidence](reports/PHASE3_METAMORPHIC_PERM.md), phase3_metamorphic_perm_result.json;24modelcomparisons/753633clocks plus three wrong-owner negatives; both RTL simulators/exact official netlist3/3PASS; Python1187PASS | tested | One declared unit permutation and L0→L1 move, separately/together; finite profiles. Unaligned SRAM-backed I2C controller is a retained counterexample, not included in the positive claim. This receipt's aligned phase diagnostic is model-only/native; subsequent hardware qualification is claim46. D-191wording approved; no unrestrictedPERM, physical-delay equality, formal, SDF, silicon, fullL4 or Phase3completion claim. |


| 46 | The finite D-191scoped L4 suite passes all five relations for the named UART/SPI/I2C profiles | [SCALE/native phase](reports/PHASE3_METAMORPHIC_SCALE_PHASE.md), phase3_metamorphic_scale_phase_result.json plus linked LOOP/IDLE/TAP/PERM receipts; eight SCALEpairs/815intervals; both RTL simulators/exact official netlist4/4PASS; Python1198PASS | tested | Declared exactly representable clock/bit intervals only; fixed latency and host/interburst timing separate. Actual pre-load clock and host TIME verify native routine grant phase; unaligned counterexample retained. Finite modes/rates/seeds/mappings, no whole-waveform2x, arbitrary unaligned invariance, analog, silicon, whole-chip formal or Phase3completion claim. |

| 47 | Native channel composition preserves outstanding blocking tokens/order and isolates taps under static configuration | [Channel formal evidence](reports/PHASE3_FORMAL_CHANNELS.md), phase3_formal_channels_result.json; three ABC PDR unbounded proofs PASS; Z3 depth40 covers reached14/15/16; five RTL mutations rejected with VCD witnesses | proved (scoped) | One HOST_IN producer/four blocking consumers; initial reset then static accept-all configuration. Exactly-once safety and common generation order; eventual consumption requires readiness, with next-clock progress proved separately for always-ready consumers. Paired four-tap composition proves noninterference for this route. No runtime reconfiguration, all-route coverage, whole-chip proof or aggregate Phase3formal completion. |

| 48 | Native pin RX indicates blocked-completion overrun and preserves the existing producer token | [RX formal evidence](reports/PHASE3_FORMAL_PIN_RX.md), phase3_formal_pin_rx_result.json; ABC PDR unbounded PASS; depth20 covers at3/3/5; five mutations rejected with VCD witnesses | proved (scoped) | Default FRAC=8 RX plus native producer, symbolic inputs/configuration/release after initial reset. Covers RX overrun indication and accepted data, not sticky unit flags, BITSYNC merge, physical timing or full F-CHAN-4/Phase3completion. |

| 49 | Lean pin-unit sticky flag set/clear/restart priority and native RX merge hold under stated interface premises | [Pin-unit formal evidence](reports/PHASE3_FORMAL_PIN_UNIT.md), phase3_formal_pin_unit_result.json; two parameter-set ABC PDR unbounded proofs PASS, two depth16 cover tasks PASS, five faults rejected with witnesses | proved (scoped) | FULL=0 default and qualified cache parameters; static configuration, legal period, monotonic live and stable pending TX, configuration-derived cache inputs. Full/BITSYNC proof remains unresolved; native status-collision replay and configuration/command admission issue retained in report. No complete F-CHAN-4, whole-chip or Phase3completion claim. |

| 50 | Scratch status merge candidate retains or reports concurrent status intents in the tested scope | [Status merge evidence](reports/PHASE3_STATUS_MERGE_CANDIDATE.md), phase3_status_merge_candidate_result.json; two replays/64matrix combinations pass; three semantic faults rejected; Icarus and Verilator FULL1suites each60/60PASS; selected whole-chip Verilator55/55PASS | tested (candidate only) | D-192not adopted; existing pending register, no new state. Matrix forces intent boundaries and checks one transition, not unbounded whole-engine proof. Native loss-accounting defect retained; no main RTL change, area/routing/timing measurement or new official GDS claim. |

| 51 | D-192candidate status queue output/order/retention/loss and scoped full pin-unit integration pass unbounded proof | [Candidate formal evidence](reports/PHASE3_STATUS_MERGE_FORMAL.md), phase3_status_queue_formal_result.json and phase3_status_integration_formal_result.json; ABC PDR PASS for extracted cone and actual FULL1qualified-cache unit; bounded covers PASS; original-source and three semantic controls FAIL with witnesses | proved (candidate, scoped) | Initial reset; arbitrary intent/data boundary inputs for cone; static legal configuration and stated host/cache premises for integration. Actual-engine triple-status exclusion is asserted/proved, not assumed. Candidate only; no main adoption, whole-chip formal, reconfiguration, physical timing or Phase3completion claim. |

The original Phase 3 ACK oracle could retain an interrupted low interval. Its setup interpretation is superseded by `phase3_i2c_ack_revalidation.json`; original functional receipts and the independent peer evidence are retained. This correction does not change the qualified Phase 2 physical result or assert analog/pad timing.

Recovery evidence: 22 model cases and four representative RTL/official-netlist cases pass for the limited scenarios in [the recovery report](reports/PHASE3_I2C_RECOVERY.md), with receipt phase3_i2c_recovery_result.json. In the original one-unit program, completed-byte STOP-before-ACK recovery fails and remains explicitly outside that program’s passing claim; model and RTL tracing identify a stale pending ACK. No complete I2C recovery/conformance claim.

For the four-unit `trw_pins` RTL, pad owner readback and the pad's data and enable match an independent owner-selection model after an initial reset. The proof covers arbitrary subsequent writes, resets, pad assignments and unit outputs, including pin A priority over pin N and ignored host-pad owner writes. Local `formal/pad_ownership.sby` passed unbounded ABC PDR safety and reached both A and N drive covers within eight steps. This covers the pad mux portion of F-OWN-1. Open-drain behavior inside the pin unit is a separate obligation.

The open-drain portion of F-OWN-1 also passed locally. In `formal/pad_open_drain.sby`, a selected open-drain A output from the actual pin unit never drives the muxed pad high. Unbounded ABC PDR passed for both full and lean pin units, and each bounded cover reached an enabled open-drain pad. The wrapper allows arbitrary configuration and other unit outputs, assumes an initial reset, and checks only pad drive behavior. Pin N retains its specified push-pull behavior. Together with `formal/pad_ownership.sby`, this provides local F-OWN-1 evidence for the four-unit design.

The actual two-lane chip RTL advances through the four SRAM slots in order after reset. Lane 0, lane 1, and host memory enables are confined to slots 0, 1, and 3 respectively. Slot 2 is idle, and the SRAM command bundle matches the selected source in each occupied slot. Local `scripts/formal_sram_rotation.py` passed unbounded ABC PDR safety with symbolic SRAM read data. All four phases were reached at steps 2–5 in a depth-eight cover. This gives F-ROT-1 slot-routing evidence. It does not establish progress for work that has yet to produce an eligible request or SRAM data correctness.

The actual lane RTL passed unbounded ABC PDR checks of slot priority, urgent-slot arbitration against a ready routine, and handoff to EXEC (F-SCHED-1). The same proof covers the one-cycle pending-flag interlock and the committed ALU flag value (F-SCHED-2). It assumes initial reset and that a released token stays released until its producer changes sequence. A separate unbounded proof on the actual fabric and consumer ports establishes that premise for all nine producers, including arbitrary configuration writes. Bounded Z3 covers reached both arbitration outcomes, a same-flag clear/set overlap, and enabling a blocking subscriber on an already released token. All four tasks passed from a clean export of fd57f9b using `scripts/formal_scheduler.py`.

The F-DEC-1 field-slice check in `scripts/formal_decode.py` passed 52 Yosys SAT assertions over arbitrary 53-bit slot and 16-bit routine words. The harness extracts the actual lane declarations and compares them with independently generated YAML slices. A corrupted tag expression produced a counterexample. This covers bit extraction, including the routine class and subopcode fields. Execution semantics and opcode dispatch are outside this check.

The model campaign in `scripts/fuzz_tripc_pipeline.py` compiled 10,000 two-lane acyclic programs with seed 0x7a17 and replayed 29,819 tagged tokens at each of two scheduler cadences. Both cadences delivered the exact expected tag/data sequence and fired each stage once per token within the test window. Each lane had one urgent slot and the host sink was serviced. This is a finite cross-check of a restricted pipeline family and the compiler's local selection result. The compiler does not issue a general deadlock or overrun certificate for this campaign, so the L6-FUZZ exit gate remains open.

A 12-step Yosys SAT check in `scripts/formal_tx_cursor.py` covers one LEVEL or OE command after reset on the native pin TX RTL for both full and lean configurations. With LEVEL mode and prescaler encodings zero or one, the command can be issued on any of the first three active clocks and request zero to three ticks. The reference checks command acceptance, LATE, and the output update edge. A reference shifted by one clock produces a counterexample in both configurations. This is bounded F-PIN-1 evidence for a single action. Longer histories, other modes and an unbounded proof remain open.

The same runner checks a queued LEVEL followed by a held OE command over 14 steps. The OE command waits for the first action's due decision, then uses that action's cursor as its base. Both cached full and lean TX configurations passed for first delays of two or three ticks, second delays of zero to two ticks, and prescaler encodings zero or one. The one-edge-late second deadline was rejected in both configurations. This extends bounded coverage to a held command and simultaneous output updates.

The queued TX proof also covers a second LEVEL command targeting the same pad. A zero-delay second command suppresses the first command's output pulse when both are due on the same edge. A positive-delay second command allows the first level until the second deadline. Both full and lean variants passed at depth 14, and both shifted-deadline controls still failed.

An 18-step TX cursor check covers SYNC, GAP and LEVEL offered on consecutive active clocks. In both native pin-unit configurations it verifies that SYNC re-anchors the cursor, GAP advances it, and the output changes at the resulting deadline or at the earliest edge for a late command. It checks LATE for both zero-delay and nonzero-delay cases. The bounded scope covers zero to three ticks for each delay at prescaler encodings zero and one. Both one-edge-shifted controls were rejected.

The extracted native TX cursor arithmetic passes a combinational Yosys SAT check over the full quotient, delay and prescaler ranges. It checks signed delay subtraction, early/late classification, the underflow boundary, prescaler rollover and saturation. The remainder starts within its prescaler range, and an admitted delay must fit in the cursor. Moving the underflow boundary by one tick produced a counterexample. This is an arithmetic lemma for F-PIN-1. Complete sequential scheduling and admission proofs remain open.

The opt-in `tripc --channel-schedule` check was compared with the independent fabric model for 11,025 declared periodic schedules. The compiled graph has one unfiltered blocking consumer and one unserviced tap on the same producer. Every safe schedule agreed with the model over two combined schedule periods, and every failing schedule returned the same first overrun clock. This checks the compiled-binding adapter and the one-channel occupancy contract. Firmware-derived schedules, multichannel deadlock and the L6-FUZZ gate remain open.

The periodic pipeline checker models two blocking channels joined by one unconditional reflex, including output reservation at EVAL, load at EXEC and next-clock release. It agreed with the compiled `tripc` pipeline running in `tripsim` on safe occupancy and the first overrun clock across 882 declared rate/phase/cadence combinations. The schedules are supplied externally and the analysis is exposed as a library function. General graph deadlock and L6-FUZZ remain open.

The campaign in `scripts/fuzz_tripc_schedules.py` checks declared schedules on 10,000 randomized compiled forwarding programs using seed 0x21f0. It varies lane count and order, port mappings, constants, arrival and sink-service phases and both scheduler cadences. The model agreed on 4,754 safe schedules and 5,246 first overrun clocks. Safe results were replayed through one extra combined phase period. This covers host-to-host unconditional chains with explicit schedules. Firmware-derived service and the full compiler gate remain open.

The routed X-propagation preflight monitored all 2,418 `sg13cmos5l_dfrbpq_1` flop outputs and all pad outputs on official netlist 44189196098 (SHA-256 `537f41adee4320df81a0b7e907f011510cc578ab3c2a17105e00a80e0bacbcc9`). All remained known for 16 samples following a normal reset and UART firmware load, after 32 settling clocks. The Icarus 13 result XML SHA-256 is `5dc9cf94cb3110015648c87574894c7ba628d1b62f9495305095fb60bd699b04`. A separate scratch reset-only run had known pads and internal unknowns before initialization. The no-reset control had unknown pads. This finite local result covers the monitored flop type and one program; latch and SRAM state, other programs, and L8-XPROP CI coverage remain open.

The reproducible BITSYNC drive proof in `scripts/formal_pin_se0.py` establishes `se0_r -> drv` after an initial reset on both the qualified source and the staged SE0 candidate. The proof uses temporal induction with arbitrary subsequent inputs. A mutation that sets SE0 on release produces a counterexample within eight steps on both sources. This is scoped to the drive invariant. The queue checks use their separate harness and the physical candidate still requires extracted timing.

The routed X-propagation replay now also passes after normal SPI and I²C controller initialization on official netlist 44189196098. Both profiles write and read SRAM addresses 0 and 511 through the SPI host before firmware load. All three profiles pass 16 sampled clocks after the settling window with known pads and all 2,418 monitored flop outputs known. Icarus 13 result XML SHA-256 is `746eb1b70a76398e9e733cc057d2a5669caf6b26183f04f9cc60d9b8b8b35a37`. This covers the stated startup and SRAM access cases. General L8-XPROP CI coverage remains open.

The two-copy fabric check in `formal/fabric_isolation.sby` proves that arbitrary differences in L1's producer valid, sequence, load and payload inputs cannot change L0's input availability, head, configuration readback or drop counts when L0 selects only a pin producer or HOST_IN. The proof uses the actual fabric and port RTL, an initial reset, and otherwise shared inputs and configuration writes. ABC PDR passed unbounded, distinct peer data with an available L0 head was covered at step three, and allowing L0 to select L1 produced the expected counterexample. This checks the input boundary of F-ISO-1. SRAM sharing and whole-lane composition remain outside the proof.

The same fabric proof establishes that L0's two output release signals are invariant to differences in L1's consumer takes when L1 has no blocking subscription to L0. L1 may still tap L0. ABC PDR passed unbounded after initial reset, and the cover reached a held L0 output while L1 takes differed in step three. Permitting L1 to block on L0 produced a counterexample to output release equality.

The declared channel schedule checker also covers a single filtered blocking consumer when the input schedule supplies an explicit repeating `arrival_tags` sequence. In 1,600 schedules with two-tag sequences and varied arrival/service periods and phases, it agreed with the independent fabric model on safe occupancy or the first overrun clock. The check includes a rejected token's one clock of producer occupancy. Conditional firmware service and the general L6-FUZZ gate remain open.

The channel graph also reports tags accepted by a blocking lane input for which no loaded reflex slot can dequeue that tag. The check considers each encoded slot's readiness predicate and assumes the loaded slot and binding configuration. A model regression confirms an admitted EVENT holds HOST_IN when the only dequeuer requires DATA. Restricting the accept mask to DATA releases the producer instead. The warning is conditional on the producer actually emitting the tag and establishes no progress for tags with a possible dequeuer.

For a compiled lane producer with no CALL slots, the warning intersects the input's accept mask with an upper bound on that output's tags. Tests cover explicit output tags, guarded and unguarded preserved tags, and MKCTL's forced CTRL tag. External producers and lanes with CALL retain the conservative all-tags bound. The bound does not establish which compiled slots will fire.

The compiler can also identify accepted tags whose matching dequeue slots all require a lane STATE unreachable from reset. The state analysis includes every compiled reflex transition consistent with its state guard, assumes fixed slots and no host STATE writes, and treats all states as possible when a CALL is present. A model regression shows a held DATA token releases after a transition to the required state is added. Possible transitions in this analysis have no guarantee of firing.

The queued TX reference-clock proof now covers prescaler encodings zero to three at depth 24 for full and lean configurations, including repeated rollover of the prescaler remainder while two actions are queued. Each variant rejected the one-clock-late reference. The TX cursor is relative and has no absolute timestamp counter. The check covers the queued LEVEL/OE cases in the harness.

The compiler also warns when a token arriving in reset STATE prevents the transitions needed to enable its own dequeue. The model confirmed that DATA first holds the producer, while sending EVENT first advances the state and allows the subsequent DATA to drain. The check assumes fixed slots and bindings and no host STATE writes, and it treats a CALL as allowing all states.

A seeded compiler regression compared the accepted-tag stall diagnostic to the independent model on 1,000 compiled state chains with two to six states. It varied the held tag, transition guards, payload and scheduler cadence, and checked whether the head token drained. The warning and model agreed in every case, including both stalls and releases. This covers the generated single-input, no-routine programs; the general L6-FUZZ gate remains open.

The host slot decoder in `scripts/formal_host_slots.py` passed a combinational SAT check with arbitrary decoded write commands and lane RUN state. Each lane's slot write strobe matches the slot address, lane select, word alignment and halted-state predicate. Removing the RUN guard produces a counterexample. This covers the slot portion of F-HOST-1 at the decoded SPI boundary. The shared SRAM and pin configuration obligations remain open.

The single-action TX proof now runs for 28 steps and covers all prescaler
encodings from zero through seven, including the 24-clock requested delay
at the upper bound. Full and lean checks passed, and each rejected the
one-clock-late reference. Sequential action histories remain separately
bounded.

The randomized state-chain warning test now runs 1,000 cases directly
and another 1,000 through a forwarding lane, checking that the token
actually arrives at the receiving producer before comparing the warning
to the model. Both campaigns exercise stalls and releases. A second
10,000-program unconditional forwarding run at seed 0x5e0 agreed on
4,837 safe schedules and 5,163 first overruns. These remain scoped
results under declared inputs and service.

The consecutive SYNC, GAP, and LEVEL check now covers 29 steps and
prescaler encodings zero through three. Both full and lean passed for all
modeled delays (zero to three ticks per command) and rejected the
one-edge-late reference. The check remains bounded.

An unbounded induction check on native pin TX proves the pending record
cannot accept another timed action or change payload before it is due.
After a due event with no replacement, or after reset/restart, the record
is empty on the next clock. Both full and lean passed with arbitrary
inputs after an initial reset. Removing the admission guard produces a
counterexample in both variants. This proves queue safety for F-PIN-1.
The exact deadline and complete action execution remain separate checks.

A two-lane model regression drives periodic arrivals through a forwarding
reflex to a stateful consumer. In all six DATA-first schedules the
compiler's warned stall propagated upstream and the third arrival was
the first overrun. EVENT-first drained under the same periods and
cadences for the eight-arrival observation window.

The native TX pending check also proves registered LEVEL, OE, RXSET and
SAMPLE dispatch matches the due record and any immediate command for
arbitrary input histories after reset. When an immediate command and
a due record target the same dispatch type, the immediate payload wins.
Full and lean passed unbounded induction. Dropping queued SAMPLE
dispatch produced a counterexample in both configurations. The proof
covers dispatch signals and payloads. Exact due-clock arithmetic,
burst start and final pad effects retain separate obligations.

Native TX induction also proves an admitted immediate or due queued burst
sets the active record on the next edge, a due queued burst cannot be
replaced on that edge, and reset/restart clears activity. Both full and
lean passed after an initial reset. Suppressing the active update produced
a counterexample for both. Exact deadlines and burst waveform execution
remain separate obligations.

The recurring two-lane regression checks a consumer that returns to
IDLE after each DATA. Alternating EVENT and DATA drains for eight
arrivals at three periods and two scheduler cadences. Repeating EVENT,
DATA, DATA stalls on the extra DATA and overruns at arrival five across
the same six schedules.

Native TX induction also checks the registered OE effect and reset
default, and checks that a due LEVEL action updates the stored level and
clears echo when no higher-priority burst effect owns the edge. Full and
lean passed with arbitrary inputs after initial reset. Removing the OE
update caused a counterexample in both. Carrier-modulated pad behavior
and complete TX deadlines remain separate.

Native full TX induction proves the cached pad level matches the
registered logical level masked by the captured carrier state, with the
idle polarity supplied for the post-edge configuration. The lean output
check uses the live idle polarity. Removing the cached carrier mask
produced a counterexample. Exact carrier periods remain a separate
timing obligation.

The queued TX deadline model covers all second delays from zero through
three ticks at depth 29 with prescaler encodings zero through three.
Both full and lean configurations passed, including the longest
24-clock combined delay. The shifted-deadline controls failed as
expected.

The routine-unlock compiler regression also covers countdown branches
with one and four iterations. At both scheduler cadences a one-clock
arrival period overruns while the consumer is waiting. At a 64-clock
period the observed four arrivals drain. This is a finite model check
of the compiled programs.

A scratch check of the exact A-pad host RTL proved by induction that
LIVE remains set on the edge following an active clock with reset
deasserted, across arbitrary decoded host writes. A mutation that
clears LIVE on a halt command produced a counterexample. This
discharges the monotonic-LIVE premise of the candidate RX integration
proof between resets. Stable configuration and pending TX are still
interface premises.

Native fabric composition also proves that each of the four pin-unit
TX ports bound as a blocking, accept-all HOST_IN subscriber holds its
available tag and payload until taken after configuration. ABC PDR
passed unbounded and the bounded covers reached stall and drain.
Reset and reconfiguration remain outside the hold interval. Tap-mode
TX and other producer bindings remain outside this instance.

The declared channel schedule compiler check now supports multicast
with independently phased blocking subscribers and per-port tag
filters. Its first-overrun result matched the independent fabric for
1,000 schedules. The 10,000-program acyclic pipeline campaign also
checked that every ready urgent slot with a next-EVAL selection
guarantee fired on the eligible clock at both cadences. These results
cover the stated graph forms and supplied traffic/service schedules.
