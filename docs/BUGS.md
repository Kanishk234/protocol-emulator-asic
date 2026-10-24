# Bugs

## 134: Detailed-route wire observer swallowed an unsupported OpenDB method
- **Symptom:** hosted40119792058 atdcf59af completes primitive1 detailed routing with zero router violations, but the audit incorrectly labels all1557required signal nets unwired.
- **Root cause:** `dbWire.getId` is not exposed by this OpenDB Tcl interface. A broad `catch` converted that API error into a missing-wire flag. Synthetic inventory tests did not exercise the real getter; the unrouted input alone could not expose a false negative.
- **Fix/coverage:** explicitly distinguish a NULL wire, require its owning net to match, and query the supported positive opcode `count`. Unsupported methods now fail the observer instead of becoming a missing wire. A read-only replay on the authenticated hosted routed ODB reports all1557wires; the frozen original ODB reports zero. Cell/placement/pin/connectivity,1453cell/334latch/2906PG-terminal inventories match exactly. Tests also reject a false-positive unrouted control and mismatched net populations. Corrected hosted40126282580 at8d1ebea attempt1 SUCCESS:6strict guards, all5input hashes, final ODB/script hashes and complete inventory/1557wire checks authenticated. The final ODB is byte-identical to the earlier route; BUG134 is covered end to end.
- **Scope:** this is a checker defect, not a hardware/routing change. The original run's overall failure stays recorded; zero router violations do not imply foundry DRC/LVS/extracted timing or full-macro acceptance.

## 133: Configured timing depends on automatic combinational-loop cuts
- **Symptom:** the new configured native timing probe has complete clock/path classification, yet six endpoint results differ between static and dynamic OpenSTA loop handling. The same endpoint set is present in both views. A nonnegative worst setup report alone would conceal this model dependence.
- **Root-cause status:** open timing-qualification issue, not a proven RTL or silicon defect. Reconfigurable mux networks contain structural loops; the selected configuration's inactive logic and loop cuts must be reconciled. Earlier ad-hoc source/read ordering did not expose the difference, so a reproducible, source-bound probe is necessary.
- **Coverage:** `spikes/r1/run_timing.py` checks every configuration gate/Q value, frozen topology, all edge-register classes, both endpoint sets and per-endpoint sensitivity; the guard remains failed while sensitivity is present. Seven focused tests reject missing paths, observable unclocked state, truncated/error/duplicate reports, nonfinite results and topology changes. No tolerance relaxation or blanket false paths.
- **Next:** use the preserved reports and selected mux connectivity to prove which feedback arcs are inactive, or test a separately declared unused-routing grounding closure that preserves every active feature. Keep physical timing unqualified and G1 selected meanwhile.

## 132: Mapped/native candidate stalls on a second host-channel command after restart
- **Measured repair (D118):** the original image also fails the short direct-frame restart probe at212060ns; omitting reset passes. A read-only VPI diagnostic identifies repeated X1Y2/W1BEG ↔ X0Y2 routing activity and native LUT data changes without time advancement. Unused default selections permit this circulation; exact minimal SCC is not claimed. Opt-in grounding of186unrouted mux outputs using existing padded GND slots changes593bits and makes both the same native restart probe and the complete native management-SPI/reset/reload/second-transfer sequence pass locally. All8736Q values remain defined; exactly593change relative to the original, and first/reloaded derived Q dictionaries match. Original image/failed control retained. Hosted40109928699 atd5d9228 passes12guards and all3functional controls; root50/55/64inputs, tool hashes/XML/Q comparisons reauthenticated. No hardware or timing acceptance.
- **Symptom:** the complete native primary passes real management-SPI loading, UART/SPI concurrency and response backpressure, USER_RESET and STOP/restart, but stops advancing at 5,460,560 ns while the first second-transfer CH_WRITE completes. Omitting the second image load still reproduces it. Full reload reproduces at 10,712,400 ns.
- **Controls:** generated RTL passes the entire sequence on Icarus 12 and the same Icarus 13 used for native cells. All 8,736 native configuration Q values are identical before/after same-image reload. Interactive scheduler stepping remains at the failing timestamp; shell-visible data=3, valid=1, ready=1, user reset released. The added second SPI payload has not yet been accepted at the failure point.
- **Initial root-cause status:** these observations excluded changed configuration contents and a simulator-version difference alone. A bare-mapped full-shell control timed out during reload and was inconclusive; the later short bare-mapped direct-frame probe reproduces, so placement/output buffering is not required. The measured D118 repair above addresses unused routing defaults; it does not prove a silicon defect.
- **Coverage/status:** D117's mandatory full-shell/reload/second-transfer test is preserved, with bounded wall time and original failure artifacts. The D118-derived image passes it locally; restart-only cannot satisfy the reload gate. No replacement is claimed. Next: continue detailed-route/timing qualification after authenticated hosted40109928699; architecture and clock/reset policy stay unchanged.

## 131: Diagnostic simulation provenance was hashed after execution
- **Symptom:** an input edited while a long diagnostic simulation was running could be recorded with its later contents rather than the version actually used. Found during management-shell harness development; no frozen production result was promoted from such a run.
- **Root cause:** `configured_smoke.py` assembled its input hash record only after the simulator returned.
- **Fix/coverage:** capture all source/image/native-audit/adapter/test/host input hashes before building and executing, then refuse any changed input before producing a passing result. The final shell and direct-frame replays run with stable inputs under this guard. Strict XML remains mandatory; earlier development runs are not the final acceptance evidence.

## 122: Native import census omits materialized constant drivers
- **Date:**2026-10-23.
- **Symptom/check:**39989251719 successfully places all210reference signal pins and retains438latches, then strict cell equality rejects two extra cells.
- **Root cause:** OpenROAD materializes Verilog literals as exactly one sg13cmos5l_tiehi and one sg13cmos5l_tielo. All original mapped cell counts match; this is not configuration storage tied to constants.
- **Fix/coverage:** require every original cell count plus exactly those two physical drivers, explicitly verify L_HI→one_ and L_LO→zero_ bindings, and include their actual area in the native core budget. Regression rejects altered latches, extra buffers/ties or missing drivers. No other import differences admitted; narrowed geometry still pending retry.

## 120: Per-bus pin groups starve the frame-data bus in legacy placer
- **Date:**2026-10-23.
- **Symptom/check:**39987539298 resolves disabled clocks but aborts at reference-width I/O placement: the32-bit frame-data bus receives31slots after equal side segmentation.
- **Root cause:** FABulous2.2emits one group per bus; the pinned legacy placer divides tracks equally among groups regardless of bus width. Overall pin capacity is not the observed failure.
- **Fix/coverage:** combine same-policy buses into one ordered group per side, as in the legacy format. Preserve pattern order and reject unequal policies instead of merging them silently. Regression verifies grouping and policy rejection; exact210pin coverage remains mandatory. No narrowed geometry or routing result accepted from the failed run.

## 121: Mapped-cell smoke inherits unsupported Icarus12 timing-net behavior
- **Date:**2026-10-23.
- **Symptom/check:** first optional mapped-LUT smoke has known frame configuration/global clock but unknown host-ready state with stock Icarus12.
- **Root cause:** this PDK's delayed_* timing-check nets require the documented TinyTapeout Icarus13 setup (scripts/gl_local.sh); the source-RTL smoke's default simulator is insufficient for mapped cells.
- **Fix/coverage:** optional mapped mode uses pinned Icarus13 through build-local executable/backend wrappers, validates version and records both executable hashes. PDK models are unchanged and byte-checked against pinned Git objects. Identical loaded primary testPASS with all16LUT tile instances mapped; other tiles remain RTL, no SDF/physical timing acceptance.

## 119: Physical pin generator emits disabled user-clock ports
- **Date:**2026-10-23.
- **Symptom/check:** native39986366251 imports/floorplans the frozen netlist, then strict I/O placement rejects UserCLK and UserCLKo, which are absent from the actual210-bit interface.
- **Root cause:** the FABulous2.2pin-order helper emits these entries despite the fabric's DisableUserCLK flag.
- **Fix/coverage:** owned adapter removes exactly these two names only when disabled and absent from the mapped interface. Every remaining pattern must match a real port and every real port must match once; unmatched-native checks stay both. Tests reject any other absent/duplicate/missing pin. Local fixed preparation records the two removals and preserves model hashes. No new native success or footprint nonfit inferred from the first setup failure.

## 118: Physical pin preparer rewrites retained primitive metadata
- **Date:**2026-10-23.
- **Symptom/check:** initial preparer passes source admission, then model-hash guard rejects six regenerated primitive JSON files after FABulous loadFabric on relocated artifact paths.
- **Root cause:** the API derives primitive JSON with source-path metadata while loading; operating directly on the downloaded library changes authenticated bytes.
- **Fix/coverage:** generate pins from an isolated copied library; check the original model before and after. Restore exact original metadata bytes from retained control files only after expected SHA equality. Final local preparation passes both model guards; no physical/native result accepted from the first attempt.

## 116: Bounded routing timeout is reported only as unknown worker failure
- **Date:**2026-10-23.
- **Symptom/check:**39696703659 UART+I2C has no native fatal and an unknown classifier result despite explicit600-second watchdog expiry.
- **Root cause:** failure_record retained exception text but not exception type, budget or observed native stage.
- **Fix/coverage:** retain TimeoutExpired classification/budget separately from native fatal diagnosis and mark observed routing/placement stage from native log. Regression checks routing timeout leaves native fatal classification unknown. Never infer structural nonfit from watchdog expiry.

## 117: Configured diagnostic harness setup and failure admission
- **Date:**2026-10-23.
- **Symptom/check:** initial harness omits inactive bidirectional pad mapping; after setup fix, too-short direct word gaps leave configuration incorrect and h_wready unknown. Cocotb runner returns normally with failed XML.
- **Root cause:** diagnostic adapter lacks inout default handling, direct configuration headers overlap the stretched frame strobe, and runner completion alone does not prove test success.
- **Fix/coverage:** tie unused inout inputs safely, space words until frame strobes settle, and require strict executed XML success. Final local configured UART TX/RX+SPI/backpressure/rate checkPASS; source/model hashes retained. Management SPI naturally has larger word gaps; no production configuration RTL changed.

## 115: Reduced-radix paired LUT choices leave dead shared configuration
- **Date:**2026-10-21.
- **Symptom/check:** strict local technology mapping of first radix8_2 draft retains428of438LUT configuration latches and fails admission.
- **Root cause:** adjacent paired LUT input subsets overlap, leaving some shared gather outputs disconnected; synthesis removes dead selector state.
- **Fix/coverage:** choose complementary halves for paired LUTs, preserving all four shared gather paths. Regression checks complete pair coverage. Corrected v2 all-ten-tile mapping retains438LUT/334primitive bits and full8736grid latch census. No cost or compiler result accepted from the first draft.

## 114: Track transformation rejects a legitimate empty corner
- **Date:**2026-10-21.
- **Symptom/check:** first local four-track generation stops before model export with Empty switch matrix.
- **Root cause:** strict nonempty graph screen was applied to a corner tile with no switch connections.
- **Fix/coverage:** transformation preserves empty corners; regression verifies merged direct edges become mux choices while the empty corner remains untouched. Second local generation and full10976-bit RTL census pass. No compiler or physical nonfit inferred from the initial setup failure.

## 113: Configuration census hashes and parses separate file reads
- **Date:**2026-10-20.
- **Symptom/check:** source review finds file hashes were captured before reopening text, allowing a concurrent edit to make the stored hash describe different bytes than the parsed census. No incorrect observed G1 count claimed.
- **Root cause:** hash and parse used separate reads.
- **Fix/coverage:** one immutable byte buffer supplies both digest and UTF8 decoding. Regression forbids reopening via read_text;22cost-checker testsPASS.

## 112: R1 artifact upload drops hidden generated model files
- **Date:**2026-10-20.
- **Symptom/check:**39479506675 compiler passes, but independent downloaded-artifact audit cannot find resource/macro/fabulous/.FABulous/bel.txt. Entire hidden model directory was omitted.
- **Root cause:** upload-artifact defaults exclude hidden files even under selected build directory.
- **Fix/coverage:** enable include-hidden-files only for the owned R1 build-artifact path, which contains the Git-archived public library and generated models. No selected held-out file or private native routing manifest is under that path. Require actual downloaded model hashes and image regeneration before accepting portable evidence. Hosted retry pending.

## 111: R1 resource model omits compiler-required corner PIP filename
- **Date:**2026-10-20.
- **Symptom/check:**39477188058 passes generator/census gates but nextpnr stops before placement on missing pips.nom_slow_1p08V_125C.txt. Native categoryunknown retained; never counted as capacity/routing failure.
- **Root cause:** generic generator emits pips.txt while the production compile API requests its explicit slow-corner filename.
- **Fix/coverage:** diagnostic model exports that filename with placeholder/uncharacterized timing metadata and false timing/physical acceptance. Export test added;47focused checksPASS. Hosted retry pending.

## 110: Cached tile source contaminates a fresh G1 generator control
- **Date:**2026-10-20.
- **Symptom/check:** disposable G1 regeneration from old build/tile_cmos5l cache retains BEL interfaces but loses3546original PIP records; configuration maps differ. Caught by control comparison before any candidate compile.
- **Root cause:** cache CSVs select prior clock-protected LUT/primitive pruning instead of pinned original matrices.
- **Fix/coverage:** archive the exact pinned Git tree into a fresh directory; overlay only owned committed primitive definitions. Compare complete PIP multiplicities/BEL records/configuration maps, bind source/library hashes and reject mutated model inputs. Missing/duplicate graph and map-corruption tests cover the gate; clean local regeneration matches all19450PIPs and six original word streams. Hosted39477188058 source-control stepsPASS.

## 109: Fresh baseline checker CI omits compiler import dependency
- **Date:**2026-10-20.
- **Symptom/check:** hosted39470166731 concurrency-rtl fails collection with missing fasm; compiler census job continues independently. No simulated/fit result from failed step.
- **Root cause:** lightweight job installs simulation dependencies, but its evidence checker imports the compiler bitstream module, which requires fabulous-fasm. Local full venv masked the omission.
- **Fix/coverage:** install existing pinned fabulous-fasm0.2.0 in that job; retain checker XML before simulation.22checker tests and16mode simulations passed locally; hosted retry required.

## 108: Concurrent response tag can change while host is stalled
- **Date:**2026-10-20.
- **Symptom/check:** source review of the uncommitted concurrency draft finds combinational arbitration can change an offered SPI tag when UART data arrives during backpressure.
- **Root cause:** header selection was not latched until handshake.
- **Fix/coverage:** latch the response lane before asserting header valid and hold through payload acceptance. All16mode/primitive simulations explicitly stall the SPI header while UART becomes ready; strict XMLPASS. Fixed before first workload commit a5c7075.

## 107: Congestion proposal excludes its native positive control
- **Date:**2026-10-20.
- **Symptom/check:** original slot387 route uses zero-capacity H_0_17_2; blanket prohibition prevents reproducing native window overflow23. Positive-control witness caught this before proposal acceptance.
- **Root cause:** feasibility-oriented cap0 exclusion was incorrectly carried into an incremental-overflow objective.
- **Fix/coverage:** permit only the original net on its exact originally used cap0 edge; still charge overflow against unchanged zero capacity. Baseline reproduces23; tests reject new/net-swapped cap0 shortcuts. Integrated1004 testsPASS; independent full-grid checker verifies proposed118, uninstalled.

## 106: Lightweight autonomy tests accidentally require optional OR-Tools
- **Date:**2026-10-20.
- **Symptom/check:** autonomy39456418372 at49da841 fails four joint-campaign orchestration fixtures with ModuleNotFoundError:ortools;672pass/239optional skips remain. Dedicated solver qualification518passes because it intentionally installs the routing extra.
- **Root cause:** the new orchestration fixture mocked native data and planners but called actual mincut discovery for its seed, unintentionally importing the optional solver.
- **Fix/coverage:** fixture supplies the same seed deficit through the independent arithmetic partition checker. Source794dafd. Full base environment simulated with OR-Tools unavailable:676PASS/239expected optional skips; focused75PASS/32expected skips. Dedicated real-solver qualification remains separate; corrected hosted autonomy run pending.

## 105: Topological chain contraction creates unsupported parallel edge pairs
- **Date:**2026-10-20.
- **Symptom/check:** new exhaustive bend/branch tests fail because two internally disjoint chains contract to the same endpoint pair, which the existing graph validator correctly rejects. Caught before committing the reducer.
- **Root cause:** draft contraction emitted one edge per chain without representing their parallel capacity.
- **Fix/coverage:** aggregate parallel unit-demand chain capacities while retaining every original path; expansion assigns each used net to a path with remaining original capacity and revalidates original resource usage/connectivity.126reducer testsPASS, including distinct path allocation, exhaustive original/reduced feasibility and tampered mapping rejection. No native route improvement claimed.

## 104: Arbitrary cut certificate applies planar demand to a crossing via
- **Date:**2026-10-19.
- **Symptom/check:** independent source review constructs a feasible two-layer net using a capacity1 via with demand1, but the draft arbitrary-partition checker compares planar demand2 and falsely reports2>1 infeasible.
- **Root cause:** unlike an axis partition, an arbitrary node subset can separate co-located layers. Its crossing resources need not all charge planar demand.
- **Fix/coverage:** conservatively refuse every via-crossing explicit partition. Regression first validates the feasible via witness then requires checker rejection.21cut testsPASS; source corrected before commit. Actual global certificates use a single collapsed layer, so their arithmetic is unaffected. Existing axis checker unchanged.

## 103: Terminal validator equates database clocks with nonleaf router clocks
- **Date:**2026-10-19.
- **Symptom/check:** independent source review of the new terminal parser finds that joining FrNet.isClock to GLOBAL_NET.isClockNet would reject legitimate leaf-clock observations before any native terminal trial.
- **Root cause:** FrNet clock is built from database signal type CLOCK; GlobalRouter caches a narrower nonleaf-clock classification. Those flags have different meanings.
- **Fix/coverage:** join raw native clock to DATABASE_NET.clock, preserve GLOBAL_NET.clock separately. Hand-computed regression accepts both leaf/nonleaf global flags when DB/native agree and rejects DB/native contradiction.56parser testsPASS; independent final review confirms fix; committed3abf0cb before native qualification39367564921. No failed native terminal result was reclassified.

## 102: Private native exports are unreadable across the Docker boundary
- **Date:**2026-10-19.
- **Symptom/check:** native qualification39331153087 reaches all three routing controls, then host raw parser raises PermissionError opening native-corridor.tsv. Artifact upload also fails EACCES; GitHub retains no artifact. Failed run remains infrastructure, not ledger or routing qualification.
- **Root cause:** the observer intentionally creates exclusive mode0600 files inside root-run Docker. The unprivileged runner owns neither file and cannot read it for Python accounting or upload.
- **Fix/coverage:** retain exclusive0600 native creation, then have the container Tcl wrapper make only the successful regular non-symlink native-corridor.tsv readable0644 before returning control. No recursive chmod, directory permission relaxation or native algorithm change. Actual Tcl fixtures verify successful0600->0644, untouched unrelated0600 file, failed partial0600 and symlink rejection;90runner testsPASS. Fix6b19d03; corrected native replay39331845906 SUCCESS with host parser and artifact upload working, reusing successful build39304728263. All six raw exports independently audit successfully.

## 101: Boundary validator rejects OpenDB decimal-formatted numbers
- **Date:**2026-10-16.
- **Symptom/check:**38853662972 passes native GCD and reproduces exact121, then fails default validation with Malformed or negative boundary edge. Pair repair is not attempted.
- **Root cause:** new boundary parser requires integer text for capacity/usage, while actual Tcl OpenDB getters emit values such as29.0 and12.0. The existing interior parser already supports finite Decimal values.
- **Fix/coverage:** reuse the interior numeric policy for capacities/usage, requiring integral counts while retaining integer coordinates, complete census, negative/nonfinite rejection and exact before/after capacity checks.89focused testsPASS/2existingSKIP; downloaded actual default validates550boundaryedges with zero overflow and unchanged capacities. Retry38948702750 reuses successful D100build38851788423; no solver rebuild. Failed run remains a collector error, not a routing result.

## 100: Forced repair capacity comparison omits real boundary edges
- **Date:**2026-10-15.
- **Symptom/check:** independent source review finds the calibrated interior export omits horizontal last-row and vertical last-column edges; claiming complete capacity-array identity from it exceeds its scope.
- **Root cause:** historical interior format loops x<nx-1,y<ny-1 for every layer. Native reportCongestion scans all real edges, while incremental getOverflow3D scans touched edges. The existing mandatory final native table already prevents accepting hidden boundary overflow, but boundary capacity changes were not explicitly compared.
- **Fix/coverage:** retain exact121 interior hashes; add separate direction-aware initial/final boundary exports, complete edge census, capacity equality and combined overflow reconciliation with the full native table. Query actual layer directions and require pinned CMOS5L Metal1/3 horizontal, Metal2/4 vertical (tech LEF SHA3edd5a1ad31e8307be537d0d1b85c3258fefeb21aac04aaa476e4f72de4cffd5). Root review caught and corrected a reversed draft assumption before commit.76focused testsPASS/2existingSKIP, including actual Tcl export/direction mismatch fixtures. Actual38948702750 captures both states and passes all550boundarycapacity comparisons; old runs retain their observed-interior scope.

## 99: Architecture evidence setup executes a non-executable fetch script
- **Date:**2026-10-15.
- **Symptom/check:**38851943119 stops with permission denied for scripts/fetch_nextpnr.sh before any design compile; no measurement artifact exists.
- **Root cause:** the tracked script has mode100644, but the new workflow invoked it directly.
- **Fix/coverage:** invoke through bash, matching its interpreter; the compiler's missing-tool instruction now names the same executable command. The workflow invocation regression checks direct script permissions and explicit bash invocations;30 focused tests pass. Actual retry38852379083 succeeds with all eight cases and independently checked native artifacts. Compiler diagnostic suite40PASS after the instruction correction.

## 98: Forced unchanged-net repair re-credits existing macro pin access
- **Date:**2026-10-15.
- **Symptom/check:**38849978485 passes custom-default exact121, then forced repair ends GRT0232/grid139 and203 encoded capacity increases despite identical physical census/geometry. Exact capacity guard correctly rejects the case.
- **Root cause:** initFastRouteIncr calls initNetlist for the initial reroute and each expansion; initNetlist unconditionally calls addResourcesForPinAccess across all mapped macro/pad pins, adding edge_cap+1 again. Route clearing releases usage only, not these credits. Our new forced unchanged-pin path incorrectly reused this initialization without suppressing duplicate credits.
- **Fix/coverage:** retain original initial crediting and ordinary incremental behavior; skip only while force_reroute_mode_ is true (no changed/new pins or placement). Corrected build38851788423 and native regression pass; controlled38948702750 preserves all69064interior+550boundarycapacities through actual pair execution. The accounting fix passes, but repair grid132/nativeGRT0232 regresses best121 and is rejected.139 remains an uncontrolled failed result.
- **Upstream confirmation:** immutable09f16990f662d522b51094a6c3085c25f3ade024 suppresses repeated credits during native incremental calls; merged PR9510 after our pinned source. D100 is a narrower forced-only correction. See docs/reports/upstream_pin_access_research_20261016.md.

## 97: Custom Nix store mount hides the container's Python runtime
- **Date:**2026-10-15.
- **Symptom/check:**38829241239 authenticates tools and passes actual GCD regression, then docker cannot start python3; no chip routing stage exists.
- **Root cause:** binding host /nix/store over the complete container store hides its Python/LibreLane dependency paths.
- **Fix/coverage:** query the authenticated tool's runtime closure and bind each individual store output at its identical path read-only. Reject broad store-root/read-write/remapped/duplicate mounts. Add actual container Python+LibreLane+custom-tool runtime smoke before chip input.56focused testsPASS/2existingSKIP; rerun with existing successful build, not a rebuilt solver. Earlier failure remains infrastructure, not routing evidence.

## 95: Reduced router diagnostic looks up normalized bus names in escaped database
- **Date:**2026-10-15.
- **Symptom/check:**38827025802 reproduces exact121 full control, then pad31 stops before routing with Missing selected net; no final congestion report.
- **Root cause:** native segment names are normalized by the parser, while OpenDB stores escaped brackets; direct findNet on the display name fails.
- **Fix/coverage:** resolve normalized names by scanning actual database net objects, require exactly one match, and call the same grt::add_net_to_route API used by pinned set_nets_to_route. Avoid STA pattern matching and keep native selected-net census guard. Add escaped-name fixture; repeat hosted diagnostic. Failed run is not a pin-access finding.

## 94: Controlled formal evidence parser assumes a bare SBY status word
- **Date:** 2026-10-15.
- **Symptom/check:** campaign38820879351 detects10simulation mutants but blocks the parking mutant despite pristine F1 proof exit0 and successful k-induction.
- **Root cause:** actual pinned SBY writes `PASS 0 0`, and split smtbmc logs use `logfile_basecase.txt`/`logfile_induction.txt`; the new parser expected bare PASS/FAIL and a single logfile.txt.
- **Fix/coverage:** accept only the observed status grammar with optional two numeric fields, retain DONE/return-code consistency, and inspect retained engine logfile variants for actual assertion rejection. Add actual-format and malformed-status fixtures; retained pristine artifact now correctly classifies PASS. Update upload pattern for split witnesses. Corrected full campaign pending; prior run is not relabeled successful.

## 93: Current I2C target state escapes the historical profiling role map
- **Date:** 2026-10-15.
- **Symptom/check:** hosted profile38780941523 has valid current LUT totals but assigns zero target FFs to counter/shift; actual retained netlist contains four `g_logic.n` and eight `g_logic.sr` state bits.
- **Root cause:** primitive integration renamed the plain-logic registers while the historical role regexes still matched only `nbit` and `shift`; the fallback labeled them control.
- **Fix/coverage:** extend only the target's role map to its actual generated plain-logic names. Reanalysis of retained native JSON restores4counter/8shift FFs without changing185total LUTs. The evidence collector now rejects a conserving matrix missing expected timing/shift state. New hosted refresh pending; original historical profile remains separately labeled.

## 92: CLI numeric heuristic raises a traceback for ordinary parameter strings
- **Date:** 2026-10-15.
- **Symptom/check:** `--set VALUE=face` or malformed numeric `VALUE=0xGG` can raise an uncaught integer-parser ValueError instead of an actionable compiler result.
- **Root cause:** a hexadecimal-character regex treated bare identifiers as integers, while the conversion exception bypassed CompileError handling.
- **Fix/coverage:** parse only integer-looking strings, support signed decimal/prefixed integers and underscores, preserve nonnumeric Verilog strings/expressions, and report malformed integer literals before compilation. Focused CLI fixtures cover strings, formats, malformed values and existing repeated-option behavior in `tools/compile/tests/test_diagnostics.py`; hosted regression pending.

## 91: Mutation runner counts infrastructure failure as a detected defect
- **Date:** 2026-10-15.
- **Symptom/check:** a missing tool, malformed/missing XML or harness import failure exits nonzero and was reported as a killed mutant.
- **Root cause:** the runner inferred rejection from exit status/text without pristine controls or actual executed testcase/property evidence.
- **Fix:** establish each distinct pristine command first; require exact applicable case census and assertion rejection, or explicit formal property FAIL. Missing tools, setup exceptions, compile errors, timeouts, skipped required cases and contradictory results are errors. Bound child process groups; write fresh campaign evidence under build, preserving the historical committed report.
- **Coverage:** adversarial fixtures and deduplicated-control tests in `tools/autonomy/tests/test_mutation_evidence.py`; actual controlled hosted campaign pending. No claim that every historical detection was false, or that the new campaign has already killed all mutants.

## 90: Phase supervisor trusts row count without validating observations
- **Date:** 2026-10-15.
- **Symptom/check:** adversarial evidence can contain48 duplicate/contradictory phase records with `passed:true` and a passing XML stub.
- **Root cause:** the first supervisor checked aggregate status/count but omitted exact campaign membership and individual observations.
- **Fix/coverage:** require exact3-seed/16-index census, successful byte/read/status observations, valid phase/delay ranges, and actual fixture SHA from the run revision's Git blob. Fourteen adversarial mutations plus complete valid evidence cover rejection/acceptance; actual38777137234 downloaded phase evidence passes the stronger checker. No claim that the original cloud simulation was wrong.

## 89: Strict UART CI exposes an inapplicable registered test
- **Date:** 2026-10-15.
- **Symptom/check:** hosted unit38777137520 rejects fixed-divisor UART XML because runtime-divisor test is intentionally skipped.
- **Root cause:** runtime-only test was registered in every variant using `skip=not RUNTIME_DIV`. Cocotb2 also emits skipped XML for test-filter exclusions, so a filter does not resolve strict executed-case validation.
- **Fix/coverage:** conditionally register the runtime-divisor test only for its applicable variant; preserve its existing test body and strict zero-skips checker. Require7 cases for fixed-divisor and8 for runtime-divisor UART runs. Actual corrected hosted matrix pending; no RTL change.

## 88: Protocol CI accepts missing or incomplete XML evidence
- **Date:** 2026-10-15.
- **Symptom/check:** adversarial XML fixtures show `! grep -q failure results.xml` succeeds for a missing file (grep exits2), and for empty, skipped or error-only suites.
- **Root cause:** shell text search does not establish that any test actually executed successfully.
- **Fix:** all eight protocol loops in WARP's `unit` workflow now use the common strict XML checker; both unit jobs use project venvs. Missing/malformed/empty results, failure/error/skip elements and nonzero failure counters reject the run.
- **Coverage:** `tools/autonomy/tests/test_check_xml.py`, 24 local passing tests; actual hosted workflow result is recorded in the session handoff after push. No hardware or template-job edits.

**BUG88 follow-up:** the same strict checker now covers real-bitstream and co-simulation XML in WARP's `fabric` workflow, plus default protocol suites in `scripts/check_all.sh`. Idle-fabric shell checks retain their separately intentional skipped bitstream cases; this change does not silently claim those executed.

## 87: Python board SPI exception leaves chip-select asserted
- **Date:** 2026-10-15.
- **Symptom/check:** injected read/write/wait failures leave CS low; a subsequent command can continue an interrupted transaction.
- **Root cause:** `Warp.xfer` released CS only on its normal return path.
- **Fix:** attempt CS-high/SCK-low/MOSI-low idle on any interruption; preserve FAB_IN and the original exception, even if cleanup fails. Never retry a partially accepted command. Transport cleanup is best effort, not rollback.
- **Coverage:** faults at all86 pin-operation boundaries and secondary cleanup failure in `tools/board/tests/test_warp.py`; independently rerun board+host suites542PASS, `build/autonomy_board_host.xml`. Software pin-adapter scope; no physical board claim.

## 86: Trace replay depends on expired historical artifact
- **Date:**2026-10-14.
- **Symptom/check:**38676296904 fails source-fetch with no valid artifacts; native routing never starts.
- **Root cause:** old best133 source and original policy artifacts have finite retention. A durable approved pre-CTS archive exists but trace replay still fetched old derived outputs.
- **Fix/coverage:** regenerate derived control from approved archive and enforce exact recorded view hashes; retain exact13-field RT_/GRT_ policy subset from authenticated660afb…config with normalizedSHA691d8fec… . Native regeneration/replay pending; no physical result from failed setup.

**BUG86 follow-up:** hosted38676688402 regenerates authenticated best133 views and reproduces133 native overflow with exact original markers, unchanged sources and actual segment exports. Infrastructure repair succeeds; routing remains failed. See `docs/reports/route_trace_analysis_20261015.md`.

## 85: Repeated compiler parameter option silently drops earlier group
- **Date:**2026-10-14.
- **Symptom/check:**38676021166 active-window loaded test compiled but waveform had16 low cycles rather than256.
- **Root cause:** workflow used --set twice; argparse default store kept only WINDOW_CYCLES=256, dropping COUNTER_BITS=9 override and retaining four-bit counter. Simulation final full-window assertion caught truncation; cancellation coverage is not established by this run.
- **Fix/coverage:** pass both overrides in one group and require exact compiled report params before simulation. CLI repeated-group regression/fix prepared separately. Corrected cloud loaded result pending.

## 84: Native placement checker compares omitted input to resolved defaults
- **Symptom/check:**38334401344 failed after placement with GRT_ADJUSTMENT mismatch.
- **Root cause:** input omits routing defaults; resolved native config contains0.3. Actual candidate and control resizer policies match.
- **Fix/coverage:** compare resolved candidate and control resizer policies and require exact original five-field policy. Actual cloud configs and three focused regressions pass; jointly changed capacities rejected. Corrected full cloud result pending.

## 83: Congestion-placement geometry exporter lacks database handle
- **Date:**2026-10-12.
- **Symptom/check:**38317781400 completes global/detailed placement then fails exporting geometry with missing variable block.
- **Root cause:** reusing the exporter omitted the original editor's top-level database handle assignment; census has its own local handle.
- **Fix/coverage:** explicitly bind block after read_db; regression checks the handle precedes geometry export. No candidate acceptance or timing/routing result from this run; native retry required.


## 82: OpenROAD master-swap editor lacks Liberty timing cells
- **Date:**2026-10-12.
- **Symptom/check:**38315996276 crashes with signal11 before candidate STA; stack ends in dbStaCbk::inDbInstSwapMasterBefore → equivCellsArcs → ConcreteCell::portCount.
- **Root cause:** the copied-ODB editor called swapMaster without first loading Liberty; OpenSTA's callback lacks timing-cell models for its equivalence check.
- **Fix/coverage:** load original fast-corner standard-cell/IO Liberty files after read_db and before swapMaster. Source-library files remain pinned and all3-corner STA checks remain unchanged. Regression checks editor ordering; cloud retry needed. No accepted producer or routing result from the crash.


## 81: Read-only timing diagnostic recreates downloaded source directory
- **Date:**2026-10-12.
- **Symptom/check:**38314895635 fails before STA with FileExistsError for reset_combined/original_source.
- **Root cause:** producer artifact includes its authenticated original payload; the new diagnostic assumed it was absent.
- **Fix/coverage:** reuse existing payload only after manifest/source hashes and path-containment validation, with no overwrite; extract the authenticated archive only if absent. Local tests cover reuse, tampering and traversal rejection. Native retry required; no physical outcome from the failed launch.


## 80: Native observer argument is overwritten by a Tcl path
- **Date:**2026-10-12.
- **Symptom/check:**38287135030 completes native CUGR then adapter fails with PosixPath has no attribute collect.
- **Root cause:** the new observer argument reused a name already assigned to the census Tcl script path in the shared runner.
- **Fix/coverage:** distinct observer_module argument plus lexical-shadow regression; observer gate rejection remains per-case so both physical controls can be measured. CUGR weighted grid retains nonzero overflow and six tiny negative usage observations; signed values may be recorded without clamping, but cannot satisfy a clean gate. No success inferred from native returncode0.

## 79: Alternate-router adapter retains observer output directory
- **Date:**2026-10-12.
- **Symptom/check:**38286631182 fails before meaningful native routing with missing stage log under build/grid_observer; workflow uploads build/cugr and finds no artifact.
- **Root cause:** new adapter changed its input and instrumentation scope but retained the old main output path. Scope guard correctly rejects the copied script, then shared runner cannot find its unstarted native log.
- **Fix/coverage:** use build/cugr consistently and verify input/output directory names before launch. Source/configured-workflow path regression checks run locally without EDA; cloud retry required. No design/routing failure or passing result inferred from this run.

## 78: Loaded fault-window test omits shell output-register latency
- **Date:**2026-10-11.
- **Symptom/check:** actual loaded38168413654 sees the correct four-cycle inversion at chip cycles7..10, while the test expects user-logic cycles6..9.
- **Root cause:** expectation includes synchronized input/edge acceptance but omits ARCHITECTURE §6's one-clock registered output latency.
- **Fix/coverage:** chip-port expectation includes that documented extra clock; source tests retain acceptance-relative timing. No RTL, synchronizer or fault timing change; cloud retry must establish remaining loaded checks.

## 76: Operating report accepts impossible or reversed pin mappings
- **Date:**2026-10-11.
- **Symptom/check:** adversarial report fixtures with FAB_IN99 or a reversed FAB_IN0 role pass syntactic metadata validation.
- **Root cause:** compiler report pin names/roles were not checked against the selected architecture's actual pin table.
- **Fix/coverage:** authenticate pins.csv against compiler provenance; reject unknown pins, incompatible roles and duplicate definitions. Tests cover each failure and actual38167697759 pin table; report includes actual fabric locations/chip labels. This establishes mapping consistency only.

## 77: Triggered fault loaded workflow assumes the wrong bitstream filename
- **Date:**2026-10-11.
- **Symptom/check:** independently downloaded compiler38168186117 produces trigger.wbit; pending loaded workflow specifies uart_trigger_fault_top.wbit.
- **Root cause:** workflow assumed top module filename rather than the pin-map-derived compiler output name.
- **Fix/coverage:** use actual trigger.wbit in same-job load environment; cloud retry required. No simulation pass inferred from compiler success.

## 75: C loader rejects a valid recovery because of an old sticky error
- **Date:**2026-10-11.
- **Symptom/check:** independent shell-model recovery tests show successful configuration reaches LOADED while a previous wrong-architecture or bad-command error remains sticky, causing the new C loader to return WARP_LOAD.
- **Root cause:** successful LOAD_BEGIN/LOAD_END do not clear old ERROR_CODE; the driver assumed final errors belonged to the current load.
- **Fix/coverage:** after architecture/non-RUNNING guards, explicitly read/clear prior errors before LOAD_BEGIN, then check final load state/error. Model regressions cover both recovery paths; no RTL change or ambiguous-I/O retry.

## 74: Helper one-cycle delay test samples before combinational settling
- **Date:**2026-10-11.
- **Symptom/check:** cloud38167100528 fails only helper[3-0-1] at time120; other two parameter cases pass and compiler38167100577 succeeds separately.
- **Root cause:** bench drives enable=1 then immediately samples elapsed in the same simulator delta cycle. With CYCLES1 the paused terminal count is already0, so enable→timer.tc→elapsed must settle before observing it.
- **Fix/coverage:** insert#1 after resume input drive, preserving all tested clock edges, timer interval expectations and helper RTL. Cloud retry required; local EDA deliberately not run.

## 73: Replay origin-only bounds admit an incoherent quantized trace
- **Date:**2026-10-11.
- **Symptom/check:** adversarial review finds stamps[0,0,0,1,2], quantum2, maximumgap1 pass origin-only cumulative bounds despite no coherent absolute-clock schedule.
- **Root cause:** cumulative uncertainty relative to the origin can hide incompatible consecutive timestamp advances later in a trace.
- **Fix/coverage:** propagate the reachable clock interval through each unwrapped timestamp bin before allowing slicing. Independent exhaustive four-event/two-bit traces compared to enumerated absolute-clock schedules plus the explicit failing regression pass; full host tests45PASS. Relative output windows remain correlated and do not infer pin values or a waveform.

## 72: New C channel reader can consume an unreported arriving byte
- **Date:**2026-10-11.
- **Symptom/check:** deeper host-driver review against actual wp_spi_target/wp_shell handshake found direct empty CH_READ polling unsafe. STATUS snapshots near CS start, but rd_hit latches FIFO validity at opcode completion; a byte arriving between these events can be popped even when returned status.rx_valid was0. Initial scripted callback tests did not model this interval.
- **Root cause:** driver assumed opcode-time status and read-hit sampled at the same point.
- **Fix/coverage:** poll harmless READ_ID first; issue CH_READ only after observed RUNNING/rx_valid under exclusive host ownership, matching existing Python behavior. Add callback regression requiring no empty CH_READ and ordered progress/error cases. Corrected driver plus root integrated board/host tests pass locally; scripted arrival-race fixture asserts empty polls use only READ_ID before the nonempty read. No board speed claim or RTL change.

## 71: Candidate extracted-STA adapter passes relative Docker paths
- **Date:**2026-10-11.
- **Symptom/check:**38163818509 authenticates/prepares all six cases, then all containers reject working directory with returncode125; no STA command executed.
- **Root cause:** new candidate adapter omitted the original STA CLI's resolve() conversion for output/physical/PDK paths.
- **Fix/coverage:** resolve those paths before invoking the unchanged STA engine. Original case hashes, own SPEF, loaded-result authentication and all margins remain unchanged. Retained actual logs establish setup-only failure; static check verifies all three paths are resolved. Actual retry38164099529 executes all six native cases with complete reports/eight clock endpoints each; examined setup/hold violations0. No timing conclusion from the failed launch itself.

## 70: Loaded candidate workflow depends on an expired control artifact
- **Date:**2026-10-11.
- **Symptom/check:**38162860520 stops before any candidate simulation because37659171115 no longer has downloadable artifacts. Automatically triggered historical replay38162860294 also fails its artifact prerequisites.
- **Root cause:** generated controls were retained for only three days; later diagnostics treated them as durable inputs.
- **Fix/coverage:** regenerate and test original controls from the already-approved durable checkpoint inside the candidate job; retain required exact five netlist hashes, all three control XML checks and actual candidate normal/USER_RESET tests. Record the fresh control's actual run ID. Make historical original-view workflow manual-only so shared helper updates do not automatically start obsolete input-dependent replays. Candidate static checks pass; fresh cloud execution is required. No publication of the separately pending source archive or manufactured old test evidence.

## 69: Native Decimal metrics prevent physical evidence serialization
- **Date:**2026-10-11.
- **Symptom/check:**38114298036 completes all physical stages with seven native zero gates and exact interfaces, then fails to retain the physical summary with `Object of type Decimal is not JSON serializable`. Original virtual-clock setup failure remains genuine.
- **Root cause:** LibreLane State metrics retain Decimal values; the summary used the standard JSON encoder directly.
- **Fix/coverage:** normalize native metrics once with a Decimal-specific encoder before constructing the summary; integral/finite values retain numeric semantics, nonfinite sentinel values remain explicit strings, unsupported objects still reject. Local serializer fixtures pass. Independently authenticated actual retained metrics/pin inventories prove seven zero physical gates, 306 exact signal ports and all eight live delay instances; no rerouting or timing waiver. Next cloud execution must exercise the repaired report writer.

## 68: Physical delay helper eagerly imports simulation dependencies
- **Date:**2026-10-11.
- **Symptom/check:**38113928620 fails before physical execution with missing cocotb; no routing was attempted and no physical artifacts were produced.
- **Root cause:** importing the shared identity-delay transformation also imported the configured simulation audit through the timing-screen module, although physical preparation does not use that audit.
- **Fix/coverage:** load configured timing dependencies only within timing execution or the timing-screen command entry point. The physical helper imports and authenticates the actual intrinsic result under project-venv Python with site packages disabled. Cloud retry must still validate native physical execution; this import check is not a physical pass.

## 67: Paired routing observer treats omitted CTS setting as a change
- **Date:**2026-10-10.
- **Symptom/check:**38112711226 runs baseline native GRT and reproduces146 overflow, then stops its observer before the padded case because CTS_SINK_CLUSTERING_SIZE is absent in the resolved stage config.
- **Root cause:** the new stricter observer compares an input-only CTS parameter8 with the GRT stage's filtered config. Both the original38101639866 and new actual GRT configs omit it; this flow runs no CTS stage. Clock uncertainty0.25, transition0.15, derating5 and every routing policy remain present/exact.
- **Fix/coverage:** accept only this specific omission when both actual configs omit it and input stays8; otherwise reject. Preserve source clock-cell census and all real margin/layer/library/macro guards. Retain native table/report before post-route policy checks so a wrapper rejection cannot discard the measured baseline. Actual retained config pair passes; changed margins, changed input CTS size and a differing original presence are rejected. Padded routing remains unexecuted in the first run; corrected paired execution pending.

## 66: Unbounded padding legalization changes orientations and moves distant cells
- **Date:**2026-10-10.
- **Symptom/check:**38102082569 native placement and requested spacing complete, but strict producer rejects changed orientation at _117_ before STA/routing. All masters/statuses/terminals remain exact;151 selected CRC/SPI cells obtain the requested gaps.
- **Root cause:** default detailed placement canonicalizes1602 instance orientations and physically moves334 bounding boxes, including32 beyond22µm (maximum56.7µm). getOrigin differences additionally count1377 unchanged-box orientation normalizations, so1707 origin changes overstate physical movement. This is a rejected localized-policy experiment, not a routed hardware pass.
- **Fix/coverage:** implemented native positive22µm legalization bounds and original-orientation restoration at the unchanged legalized bounding-box anchor, followed by fresh native legality, spacing, topology and both origin/box movement guards. Do not waive22µm or orientation invariants. Bounded38102423038 fails native DPL-0036 on eleven repeated entries/five unique CRC/SPI/fanout cells before restoration or STA; retain the failed broad target. Next scope is five cells at the worst measured marker (D-073). A new explicit vertical-phase guard rejects odd-row power reversal before restoration; positive/negative transform checks pass. No STA/routing result is claimed from either failed trial.

## 65: Bounded-property wrapper rejects successful SBY metadata
- **Date:**2026-10-10.
- **Symptom/check:**38101606932 workflow fails although both engines return0 and complete PASS; bounded checks cover84 frames, both RUN covers reach step57.
- **Root cause:** wrapper compares the entire status file to literal PASS; pinned SymbiYosys writes PASS followed by exit-code/elapsed metadata (actual PASS 0 321 and PASS 0 30).
- **Fix/coverage:** accept exact PASS or PASS with zero exit-code/numeric elapsed metadata, require subprocess return0, retain raw status and reject malformed/nonzero/PASS-prefix strings. Actual retained statuses and negative controls pass locally without EDA. Retry38102131236 succeeds: BMC84 PASS 0 357 and cover84 PASS 0 31, RUN reachable at57. Original properties/assumptions/bounds remain unchanged. This does not qualify timing or arbitrary full-load behavior.

## 64: New manual-only branch workflow is not registered for dispatch
- **Date:**2026-10-10.
- **Symptom/check:** after5319e91 is pushed to efpga, dispatching cfg_fanout_local.yaml returns GitHub HTTP404 before any diagnostic job starts.
- **Root cause:** a new workflow existing only on the project branch is not available through the workflow dispatch endpoint yet; main holds the separate design.
- **Fix/coverage:** add an efpga-only push trigger restricted to this diagnostic's helper and workflow, following existing branch diagnostic workflows. Preserve manual dispatch, native guards, limits and unchanged template jobs. The next push must produce a real run before claiming execution.

## 63: Congestion collector assumes every native route emits a report
- **Date:**2026-10-10; preventive source review, not an observed failed CI.
- **Symptom/check:** the collector would reject a genuine zero-overflow route if no marker file exists. Both actual cases in38100978078 have nonzero overflow and reports, so this did not affect that run.
- **Root cause:** pinned FastRoute writes the TR file only when its marker category exists; a clean route can have no congestion category.
- **Fix/coverage:** permit an absent report only with an actual parsed final native zero-overflow table and unchanged protected routing/library/macro policy. Record `report_present:false` without inventing a hash, file, marker count or pass. Missing/empty reports with nonzero overflow remain errors. Lightweight zero/absent positive and missing/empty nonzero negative controls pass; existing native failure remains explicit.

## 62: Cold container pull consumes native observer timeout
- **Date:**2026-10-10.
- **Symptom/check:**37960021920 baseline native-placement observer times out120s during first image download; candidate later reaches genuine150-iteration congestion169. No new baseline routing measurement exists.
- **Root cause:** image provisioning happens inside the short observer subprocess timeout.
- **Fix/coverage:** explicit pinned-image pull with separate5min workflow setup bound before native observers. Keep observer120s, routing900s and45min job bounds; no routing check waived. Both cases execute genuine150-iteration routing in38100977984 and retain failed149/169 overflow; report collection38100978078 also completes. Provisioning failure is fixed, congestion remains.

## 61: Abstract audit overcounts existing supply accesses
- **Date:**2026-10-09.
- **Symptom/check:** precheck37958932525 passes native API and conductor checks but aborts on expected two removals/26 survivors before mutation.
- **Root cause:** the original exported LEF has13 rectangles per supply net, including one short entry each:26 total,24 survivors. The initial census expectation incorrectly counted28 total.
- **Fix/coverage:** independently count authentic native LEF37814339758 and require12 full-span survivors per net/24 total after exactly two removals. Keep exact geometry/connections/grouping invariants and all official checks. No result accepted from the failed run. Verified corrected37960021923 passes all nine official checks with exactly24 retained accesses.

## 60: Native abstract census assumes an unexposed object-ID method
- **Date:**2026-10-09.
- **Symptom/check:** precheck37958116017 aborts before abstract mutation: pinned Tcl dbBPin lacks getId.
- **Root cause:** upstream C++ dbObject::getId exists but is not inherited by the pinned exposed Tcl class. Native binding availability was not proven by the source API check.
- **Fix/coverage:** use native SWIG pointer-derived object handles for exact surviving BPin grouping and SWire/SBox identity. Every remaining used method is declared in the actually wrapped pinned db.h. Keep exact all-other-pin/connection/special-wire/die invariants and existing-conductor proof; no abstraction is accepted from this failed run. Verified37960021923 passes native invariant census and all nine official checks.

## 59: Native power-interface observer loses multiple-box separators
- **Date:**2026-10-09.
- **Symptom/check:** retained C2 audit37957273575 aborts parsing the original VPWR access before candidate comparison.
- **Root cause:** inherited Tcl join delimiter is an unquoted semicolon. Default-space serialization had worked for single-box signal pins but merged three real rectangles per supply port.
- **Fix/coverage:** quote the delimiter as {;} in the observer clone. Strict parsing remains unchanged; Tcl formatting and retained308-port census controls preserve all three rectangles per PG net. No physical or original timing-status changes. Verified37958116371 matches all306 signal and both PG ports with every rectangle preserved.

## 58: Internal supply access metadata fails external boundary contract
- **Date:**2026-10-09.
- **Symptom/check:** official37814339758 passes eight checks but Pin check rejects two Metal4 supply rectangles ending18.68um below top (limit10um).
- **Root cause:** native full-block abstract exports short internal side-grid access entries alongside24 full-span external supply entries. This is distinct from BUG54 formatting.
- **Fix/coverage:** D066 removes only the exact two metadata boxes in an in-memory export copy after native same-net conductor coverage proof. Exact all-other-pin/BTerm/connection/die/special-wire census must match; source ODB/GDS stay unchanged. Gap/narrow-conductor controls reject. Verified37960021923 passes all nine official checks, preserving actual conductors and all remaining pins.

## 57: Optional runtime debug aliases disappear during native serialization
- **Date:**2026-10-09.
- **Symptom/check:** final-C2 native37956821834 loads9164 actual configuration latches successfully but aborts before RUN with KeyError for c_out_mux. No candidate UART result was obtained.
- **Root cause:** OpenROAD netlist serialization removes optional c_out_mux/c_reset_value aliases starting at floorplan. The unconditional debug logger assumes they survive.
- **Fix/coverage:** consult the exact matched cone for these two debug fields. Proven absent aliases are explicitly logged; declared bits use only same-bit observable aliases, and missing live bits/nonscalar names still fail. Actual LUT_flop/O reads, all storage/configuration checks and external UART/STOP/reset checks remain strict. Positive/negative mock controls pass, including preserving observed X; verified37958116481 passes all four actual loaded normal/USER_RESET control/candidate cases.

## 56: Mid-PnR STA reports only its first loaded timing corner
- **Date:**2026-10-08.
- **Symptom/check:**37814494048 completes baseline STA with PNR_CORNERS listing fast/slow/typ, but strict three-corner gate finds only fast metrics.
- **Root cause:** pinned sta/corner.tcl explicitly takes the first corner for its per-process reports. Loading all three libraries does not produce all three independent reports.
- **Fix/coverage:** six explicit processes: baseline and candidate at each original fast/slow/typ corner, with that single PNR_CORNERS/DEFAULT_CORNER selection. All original library maps/clock/SDC/macro/constraints retained; exact requested metric mandatory. Actual fast5 accepted only as fast; wrong/missing/extra-corner controls reject. Verified37956470190 reproduces baseline5/candidate0 independently at fast/slow/typ. No coverage waiver.

## 55: Configuration fanout STA replay omits required run directory
- **Date:**2026-10-08.
- **Symptom/check:**37814078677 inserts/legalizes ten buffers and passes exact3596-instance/18073-terminal contraction audit, then CLI rejects nonexistent baseline_sta --force-run-dir before timing.
- **Root cause:** new helper omitted mkdir required by LibreLane's existing-directory CLI path validator; other physical helpers already create it.
- **Fix/coverage:** create each unique STA run directory before invocation. Preserve baseline-five/candidate-zero/all-three-corner and protected-input gates. AST/whitespace pass; actual timing result pending. Canceled only the redundant unchanged replay37814339957 to avoid repeating this known setup failure; tile/precheck remain active.

## 54: Experimental view packaging violates official precheck input contract
- **Date:**2026-10-08.
- **Symptom/check:** official37811985173 fails six of nine checks: multiple GDS top cells and apparent LEF/template die mismatch.
- **Root cause:** filler overlays leave unreferenced original masters in the GDS. Official checks choose a unique top, unlike earlier explicit tt_um_warp geometry checks. Native LEF emits valid short decimals; pinned official parse_fp3 left-pads fractional digits, so1289.28 becomes1289.028.
- **Fix/coverage:** publish only actual chip plus its complete referenced hierarchy, requiring exact per-cell shapes/labels/instance transforms/arrays and database-unit equality after readback. Format only LEF geometry tokens to three decimals with exact Decimal equality, rejecting rounding. Preserve authenticated original GDS/ODB and unmodified nine official checks. Formatting/precision negative controls and AST pass; cloud acceptance pending.
- **Follow-up verified:**37813220689 publication preserves724 referenced cells including shapes/labels/instances/DBU, removing only orphan original fill1/fill2. Eight official checks pass, including full IHP DRC. Pin parser then rejects native double whitespace after RECT; normalize geometric-statement separators only. All842 actual RECTs match its exact syntax with original Decimal values unchanged; final pin result pending.
- **Primary sources:** [pinned official pin checker](https://github.com/TinyTapeout/tt-support-tools/blob/d66cf179e7bc4d296362ab7e2e3b344dc3c4f665/precheck/pin_check.py), [KLayout hierarchy selection](https://www.klayout.de/0.28/doc/code/class_SaveLayoutOptions.html).

## 53: Default instance-array serialization fails protected macro audit
- **Date:**2026-10-08.
- **Symptom/check:** fanout37810652597 completes baseline CTS/resizer/STA, then strict MACROS comparison rejects the resolved configuration.
- **Root cause:** pinned LibreLane3.1 adds array:null to the unchanged macro instance; original3.0 serialization omits this default. All view paths, location and orientation match.
- **Fix/coverage:** canonicalize only omitted-versus-null array. Changed views, location, orientation and non-null arrays still reject in artifact-based controls. Library/clock/SDC/fanout/native-placement audits remain. Baseline reports32 fanout violations at estimated typical corner; not all-corner acceptance. Corrected paired run pending.

## 52: Native pin observer treats LibreLane Path as pathlib Path
- **Date:**2026-10-08.
- **Symptom/check:** tile37810652641 completes original three-step floorplan flow then fails on LLPath.parent, before pin comparison.
- **Root cause:** state output paths use LibreLane's string wrapper, which lacks pathlib parent.
- **Fix/coverage:** convert explicitly with Path(str(path)) before observation. Fresh design header retains only its actual top module, excluding imported Liberty definitions misidentified as hierarchical macros. No netlist/pin/geometry alteration. AST/whitespace checks pass; actual original/candidate geometry comparison still pending.

## 51: Constant folding removes evidence alias for retained storage pin
- **Date:**2026-10-08.
- **Symptom/check:** native37810652570 passes restored cell declaration/check gate, then original-storage audit rejects _1700_.RESET_B before proof/simulation.
- **Root cause:** original _0815_ reset wire is driven by tiehi_2243_; Liberty folding preserves value1 but deletes the original named binding used by the strict audit.
- **Fix/coverage:** retain one original named wire per storage-pin bit before flatten/opt. No forced values or state changes. Artifact-based alias restoration passes all537 state-cell bindings; mutation of reset1 to0 still rejects. Binary proof and loaded native tests remain mandatory; cloud result pending.

## 50: Legacy null pad-library selector breaks pinned physical preflight
- **Date:**2026-10-08.
- **Symptom/check:** fanout37809673156 passes source placement/load observation but stops before CTS on OpenROAD.prepare_env/filter_views TypeError: NoneType not iterable.
- **Root cause:** original LibreLane3.0 resolved config has PAD_LIBS=null; pinned3.1 default is an empty dictionary, and prepare_env iterates it. Original LIB already includes standard-cell and I/O Liberty files at all three corners.
- **Fix/coverage:** normalize only the legacy empty selector to{}, retain/hash all six actual timing files and check resolved libraries/macros/clock/SDC/fanout constraints remain unchanged. Baseline/cluster8 still differ only by clustering size. No library or gate removed. Corrected cloud result pending.

## 49: Tile preflight imports OpenDB outside its embedded interpreter
- **Date:**2026-10-08.
- **Symptom/check:** tile37809673093 fails before floorplanning with ModuleNotFoundError: odb in ordinary container Python.
- **Root cause:** the pinned image exposes OpenDB through OpenROAD's embedded interpreter, not ordinary python3. Direct LibreLane flow APIs remain available in ordinary Python.
- **Fix/coverage:** run a read-only native OpenROAD Tcl observer for die, signal-port directions and every pin rectangle; parse its retained output with strict unique/nonempty/shape checks. Missing/duplicate/malformed census controls and Tcl completeness pass. Physical pin equality gates unchanged; no local EDA. Corrected cloud result pending.
- **Primary source:** [OpenDB interpreter documentation](https://openroad.readthedocs.io/en/latest/main/src/odb/README.html#python).

## 48: ABC remap recreates cells after flatten deletes port declarations
- **Date:**2026-10-08.
- **Symptom/check:** native remap37809673029 fails check-assert with74 undriven output/user-D/clock warnings, before proof or simulation.
- **Root cause:** flatten deletes21 combinational module definitions; ABC creates new mapped instances without restoring their port direction declarations. Both original storage black boxes remain.
- **Fix/coverage:** read_liberty -lib -nooverwrite immediately after ABC restores only missing black-box declarations and preserves existing storage definitions. This skips functional reimport of the unused clock-gate cell (BUG38). Actual mapped/deleted-type census, syntax/order controls pass; storage/check/proof/native gates unchanged. Corrected cloud result pending.
- **Primary source:** [pinned Yosys0.33 Liberty frontend](https://github.com/YosysHQ/yosys/blob/yosys-0.33/frontends/liberty/liberty.cc).

## 47: Named configuration audit counts an optimized-away alias as storage
- **Date:**2026-10-07.
- **Symptom/check:** native stage37708777882 fails all six cases before UART; control14 unknown named signals, original synthesis/finalC2 substitutions12. The stronger audit therefore cannot yet locate a functional divergence.
- **Root cause:** report_loaded_config inventories names ending ConfigMem.Inst_frameN_bitM.Q as storage. Passing C2 mapped NL SHA25603c21b8e400e1774390e67b0939422959d37e26849adca18fa082f492cf5cdaf retains Inst_frame4_bit2.Q only as a declaration (line2237) and assignment to1'hx (line14229), without a live cell load/driver. Names are not an actual storage-cell inventory.
- **Fix/coverage:** matched connectivity JSON for each stage, generated without optimization from its exact mapped netlists, plus source hash and exact alias-reference census. Only JSON literal-x aliases with exactly wire+assign references may be classified separately. Every actual configuration latch must bind scalar D/GATE to FrameData/FrameStrobe and have known Q matching the loaded image. Unknown/mismatching real storage remains a failure; no signal force or model change. Lightweight loaded-alias/unproven-alias/bad-binding controls and mocked actual-Q unknown/wrong/correct controls pass; all five passing NLs identify only the unused frame4_bit2 alias. Corrected six-case cloud result pending.
- **Verified:**37709917442 control passes both cases with9164 actual latches known/matching. Four original synthesis/finalC2 cases fail later on real UART X, with the configuration audit passing; no remaining phantom-alias failure.

## 46: Moved ECO pins retain stale routed signal-net connections
- **Date:**2026-10-07.
- **Symptom/check:**37690243797 legal driver ECO starts22 native markers, bootstrap27, then first late pass fails DRT-0206 checkConnectivity on u_cfg._17_ (driver u_cfg._53_/Y). No routed or timing acceptance.
- **Root cause:** legal cell moves invalidate existing pin escapes. Reusing those partially stale complete-net wires as an incremental input leaves a pin unvisited; the native connectivity gate correctly rejects it. The failed net connects the moved driver's input, so it belongs to the intended affected signal set.
- **Fix/coverage:** remove complete ordinary signal wires only for nets touching the exact three moved cells before routing; preserve all power rails, other routing and logical/port connectivity. Require exact moved-cell inventory, unchanged topology after ripup and after routing, fresh native0 and stock antenna/critical-connectivity checks. Retain ripped-net names and failure evidence. Corrected cloud result pending; no check waiver.
- **Primary API:** pinned OpenDB dbWire::destroy removes wire geometry rather than logical dbNet/ITerms; [pinned header](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/odb/include/odb/db.h). Runtime checks required Tcl binding before mutation.
- **Verified:** corrected37708459393 passes. Eight affected signal nets ripped, bootstrap59 markers then first late pass0; fresh full-chip native0, stock antenna/critical connectivity0 and downstream Magic/KLayout/shell LVS0. Fresh all-corner slew/setup/hold/cap0; fanout33 remains separate.

## 45: Placement preflight misreads a void successful checker return
- **Date:**2026-10-07.
- **Symptom/check:**37688867787 fails before resizing with custom "Source placement is not legal", without native placement violations.
- **Root cause:** script compares check_placement's empty successful return to numeric0. Pinned OpenROAD dcf36133 Opendp.i defines check_placement_cmd as void; CheckPlacement.cpp raises DPL-0033 on actual violations. Current general documentation's numeric-return description did not match this pinned API.
- **Fix/coverage:** invoke native check directly with retained baseline/candidate placement reports; native errors still fail the job. Source and final checks both retained. Corrected cloud result pending; no placement acceptance inferred from fixing setup.
- **Primary sources:** [pinned command](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/dpl/src/Opendp.i), [pinned failure gate](https://github.com/The-OpenROAD-Project/OpenROAD/blob/dcf36133a369abc8f3c5e5738cd4d82e4903c0e0/src/dpl/src/CheckPlacement.cpp).
- **Verified corrected run:**37689324316 succeeds; actual source/final legality checks pass and strict topology/master/movement audit remains. Downloaded result and placement-only ODB hash verified; routes/timing remain unqualified.

## 44: Board loader truncates malformed fields and skips negative chunks
- **Date:**2026-10-07.
- **Symptom/check:** independent audit reproduces negative chunk emitting BEGIN/END without DATA, oversized architecture/word truncation and65536-word length wrapping to0 in tools/board/warp.py. Host BUG42 validation had not reached the board API.
- **Root cause:** MicroPython board transaction builder serialized values without unsigned-width/chunk/length validation; Warp.load queried the device before checking malformed inputs.
- **Fix/coverage:** validate chunk, architecture, every word and16-bit length in both transaction builder and before any device I/O. Meaningful boundary/no-I/O tests and valid maximum-length parity/CRC; project-venv board+host317 tests pass. Existing unit workflow37663965540 passes on675a03c and covers them. No physical/bitstream/SPI format change or real-board claim.

## 43: Isolated Magic count field is empty despite completed checks
- **Date:**2026-10-07.
- **Symptom/check:**37653631748 produces five reports with an empty count field. Full log records five zero-error checks and empty reason lists; workflow green only means reports completed.
- **Root cause:** Magic `drc count total` prints its result instead of returning a Tcl value suitable for interpolation.
- **Fix/coverage:** keep count output in the retained log, label each cell there and write `has_findings` from the returned `drc listall why` list. Check that every baseline and array fixture produces a report. Tcl completeness passes; hosted extended-array verification pending. This reporting correction does not resolve complete-chip DRC.
- **Verified:**37657638270 and37658318703 retain explicit box counts derived from the returned reason lists, including17 ground-boundary boxes. Baseline/no-finding cases report0. These counts measure reports, not chip acceptance.

Format for each entry: number, date, symptom, root cause, the check that caught it, the check that now covers it, fix commit.

## 42: Host loader accepts negative chunk size and truncating fields
- **Date:**2026-10-07.
- **Symptom/check:** load_transactions(words, chunk=-1) builds LOAD_BEGIN/LOAD_END but no LOAD_DATA; words outside32 bits and architecture IDs outside16 bits are truncated by byte packing.
- **Root cause:** transaction builder relied on range/byte helpers without validating the caller's chunk, word or architecture fields.
- **Fix/coverage:** reject non-positive/non-integer chunks, non-unsigned32-bit words and non-unsigned16-bit architecture IDs before building load transactions. Host tests include all three boundaries, valid randomized loads and CRC preservation. Local31 host tests pass; hosted verification pending. No shell/bitstream format change.

## 41: Plain-filler experiment leaves the separate decap selector active
- **Date:**2026-10-07.
- **Symptom/check:**37552604692 reproduces248 KLayout errors and75 LVS errors; intended decap removal did not occur. Result summary has null counts because failed deferred checkers do not write final state_out.
- **Root cause:** fill insertion combines DECAP_CELLS and FILL_CELLS. Only FILL_CELLS was changed; DECAP_CELLS remained sg13cmos5l_decap_*. Exact post-fill DEF has5667 decaps and1095 plain fillers,6762 total. This run does not test the no-decap hypothesis.
- **Fix/coverage:** change only DECAP_CELLS to an empty list in the copied config. Stage filler insertion separately and require zero actual decap instances plus nonzero plain fillers before expensive physical checks. Read KLayout/Netgen metrics from their completed states even when deferred checkers fail. Static inventory/parser checks pass against failed-run evidence; corrected cloud verification pending. Frozen chip/PDK unchanged.

## 38: Functional Liberty import rejects an unused clock-gate cell
- **Date:**2026-10-06.
- **Symptom/check:**37536118708 native UART fails; separate optional SAT stops before solving because sg13cmos5l_lgcp_1 has an internal output without a function.
- **Root cause:** full functional import attempts to model unused Liberty entries whose state-table semantics the importer does not support.
- **Fix/coverage:** ignore incomplete entries at import, then hierarchy-check every instantiated cell so a used missing model still fails.37545251399 verifies import succeeds; no native/model/hardware change or proof success implied.

## 39: Native configuration capture misses renamed latch outputs
- **Date:**2026-10-06.
- **Symptom/check:**37545251399 SAT setup cannot bind aliases removed by cleanup.37545630704 retains aliases and finds counterexamples, but some configuration selectors remain free.
- **Root cause:** capture selected only ConfigMem.*.Q names. Exact netlist audit finds529 configuration latches, with24 outputs without those aliases;530 logical configuration bits include one merged latch. The earlier8707 matching-bit audit is a named-storage subset. Missing constraints invalidate interpreting these counterexamples as a mapped-LUT fault.
- **Fix/coverage:** preserve proof aliases and capture Q directly on every actual sg13cmos5l_dlhq_1 instance. Static529/505/24 cell/alias audit passes. Hosted37546145073 proves all three local constant properties with feasible constraints. No signals are forced in simulation; only the isolated proof constrains observed configuration values. BUG33/native UART remains open.

## 40: Cloud evidence omits final physical database and marker coordinates
- **Date:**2026-10-06.
- **Symptom/check:**37516794406 reaches0 native markers, but artifact's latest drt_iter snapshot is iteration52 with3markers. KLayout counts survive while its lyrdb and final zero-route ODB are absent.
- **Root cause:** bounded collector retains intermediate drt_iter ODB and small log/rpt/json/xml files, excluding final physical views and lyrdb.
- **Coverage/workaround:** separate geometry replay37545941476 retains full ignored run directory including physical views and marker databases. Its source remains intermediate3-marker ODB; cannot reconstruct or claim the final0 database from it. Update long-route evidence retention before another route is needed; collector now retains the final completed state views separately, with exact metrics and hashes, plus all lyrdb files. Synthetic regression verifies final0 ODB retention even when the latest intermediate snapshot has3 markers. Hosted retention verification remains pending; it does not recover the missing historical final database.

## 37: Optional native LUT alias raises KeyError through indexed lookup
- **Date:**2026-10-06.
- **Symptom/check:** focused diagnostic37534707478 stops before RUN while looking for LUT_out, an alias removed by synthesis; it does not reach the later UART check.
- **Root cause:** cocotb indexed lookup raises KeyError for missing handles, whereas optional-alias handling catches AttributeError. The pre-push netlist audit had confirmed LUT_out was removed but did not exercise the handle access behavior.
- **Fix/coverage:** use attribute lookup, matching existing optional native probes and their AttributeError handling. Lightweight fake-handle check covers retained and removed names. Hosted37535155011 verifies the correction and reaches actual UART X; BUG33 remains unresolved.

## 36: Diagnostic NOR gate used NAND's inverted input name
- **Date:**2026-10-06.
- **Symptom/check:** native diagnostic37521273371 passes RTL control but stops before RUN with KeyError:A_N in sensitivity filtering.
- **Root cause:** nor2b ports are A/B_N; diagnostic incorrectly reused nand2b's A_N/B convention. Official pinned PDK models are unchanged and not at fault.
- **Fix/coverage:** use A or !B_N for NOR input sensitivity (output inversion does not change sensitivity). Lightweight schema audit invokes filtering for every distinct gate interface in actual mapped fabric; controlling-input checks pass. Hosted rerun pending. This diagnostic error does not resolve or reproduce the later UART failure by itself.
- **Hosted verification:**37521660597 successfully executes filtered traces through the actual later UART X; no KeyError. BUG33 remains open.

---

## 1: Template gate-level source list omits the flip-flop UDPs
- **Date:** 2026-09-25
- **Symptom:** `gl_test` fails at elaboration with `Unknown module type: ihp_dff_r` as soon as the design has flip-flops. (Seen on the TRIPWIRE branch, gds run 35821375890; carried over preemptively since WARP uses the same template.)
- **Root cause:** in the IHP-Open-PDK revision the CMOS5L action pins, the flip-flop UDPs live in `sg13cmos5l_stdcell/verilog/sg13cmos5l_udp.v`, which the upstream `cmos5l` template's `test/Makefile` does not list.
- **Caught by:** `gl_test` (CI).
- **Now covered by:** `gl_test` on every `gds` run, and `scripts/gl_local.sh` once added.
- **Fix:** add the UDP file to the gate-level `VERILOG_SOURCES` in `test/Makefile`. Fix commit: pending.

## 2: Magic stream-out hangs on a FABulous tile in CMOS5L
- **Date:** 2026-09-25
- **Symptom:** LibreLane step `Magic.StreamOut` on the `LUT4x8_ha` tile (`spikes/tile_cmos5l`) prints `DEF read, Line 67..70 (Error): No cut layer specified in VIARULE` (4 errors), then runs at 100 % CPU with an empty log for 9+ minutes; stopped by hand. No GDS produced.
- **Root cause (found 2026-09-26):** a **Magic version mismatch**. The PDK's CMOS5L tech file (2bbec75) says `Magic version 8.3.657 is required by this techfile, but this version of magic is 8.3.623` (the LibreLane 3.0.0 / FABulous-plugin Nix environment), and then fails to parse its `cifinput` section. With a partly loaded tech file Magic cannot read the generated via arrays (`No cut layer specified in VIARULE`) and hangs. Removing the TopMetal1 power grid (4 → 3 errors) did not help, as expected given this cause.
- **Caught by:** the tile hardening spike (manual).
- **Now covered by:** nothing yet. Next: KLayout stream-out for tiles and the fabric (as Tiny FABulous does), and a check that the flow finishes in bounded time.
- **Update (run 2):** hung again in the same way; skipping the step through the tile's `meta.substituting_steps` had no effect, because `tiles.py` builds the flow from a dict and does not apply them.
- **Fix (workaround):** our patch to the tile driver applies step removals; tiles skip Magic and use KLayout stream-out (run 3: GDS written, KLayout DRC 0). Root cause in Magic still open; Magic LEF writing is also skipped, so the fabric needs another LEF source. Fix commit: pending (spike).

## 3: UART test harness: first byte invisible to sigrok, writes during ReadOnly
- **Date:** 2026-09-25
- **Symptom:** `protocols/uart/test`: sigrok decoded `[FF 55 A5 3C 81]` instead of `[00 FF 55 A5 3C 81]` (our model decoded all six); two tests failed with "Attempting settings a value during the ReadOnly phase".
- **Root cause:** test code, not RTL. (a) The recorded TX line started at the edge where the first start bit began, so the VCD had no idle-high → low edge before it and sigrok skipped the frame. (b) The record/collect helpers returned in the ReadOnly phase and the caller then drove a signal.
- **Caught by:** the sigrok leg of `test_tx_back_to_back` (an independent decoder) and cocotb's phase check.
- **Now covered by:** the same tests: the VCD gets 2 bit times of idle first; helpers end with `NextTimeStep()`.
- **Fix:** in the same commit as the tests.

## 4: SPI target model skipped a response byte; SPI controller spec allowed a too-fast SCK
- **Date:** 2026-09-25
- **Symptom:** (a) `tools/refmodels/spi.py` with the CS-fall and first SCK edge in the same clock missed that edge (CPHA 1); (b) across CS transactions the model skipped a response byte (e.g. host got `C3` instead of `5A`); (c) the SPI controller at `HALF=3` read wrong MISO bytes in every mode.
- **Root cause:** (a, b) model: it handled only one event per clock, and it loaded the next response both when a byte completed and when the next transaction started (CPHA 0 puts the next byte's MSB on the line before knowing whether the transaction continues). (c) spec: MISO passes a two-flop synchronizer (2 clocks) and a target may take 1 clock after its change edge, so the sampling edge must be ≥ 4 clocks after the change edge. The RTL comment said `HALF >= 3`.
- **Caught by:** (a) the model's own hypothesis round-trip test; (b, c) `protocols/spi_ctrl/test` (multi-transaction tests, `HALF=3` run).
- **Now covered by:** `test_target_roundtrip`, `test_responses_continue_across_transactions` (model); the SPI RTL suite at MODE 0–3 with `HALF` 4, 5, 7. Spec changed to `HALF >= 4` (SCK ≤ clk/8).
- **Fix:** in the same commit as the SPI tests.

## 5: I2C controller changed SDA in the same clock as SCL fell (found in review, before any test)
- **Date:** 2026-09-25
- **Symptom:** none observed; found by reading the first draft of `protocols/i2c_ctrl/i2c_ctrl_top.v`: the next data bit (and the ACK release) was driven in the same clock that SCL was pulled low, i.e. zero hold time. The draft also returned the wrong bits of the 9-bit shift register as the reply.
- **Root cause:** the bit sequence had no phase between "SCL low" and "SDA change"; reply bits were taken before the 9th sample was shifted in.
- **Caught by:** design review of the draft.
- **Now covered by:** `check_bus()` in `protocols/i2c_ctrl/test` (SDA may change while SCL is high only at START/STOP) and every reply check. It cannot see zero hold time at one sample per clock, so the fix is structural: a separate `S_B_SET` phase of Q clocks after SCL falls before SDA changes.
- **Also:** the I2C model test `test_nack_on_data_byte` first expected 4 replies for 5 bytes (the test miscounted; the model was right).
- **Fix:** before the first commit of the I2C controller.

## 6: I2C target test harness read host replies one clock late
- **Date:** 2026-09-25
- **Symptom:** `protocols/i2c_target/test`: three tests got `[]` from the host register reads.
- **Root cause:** test code. The design presents a read reply right after the clock edge that takes the command; with `h_rready` held high the reply is consumed at the next edge. The helper looked after that next edge.
- **Caught by:** `test_bus_write_then_host_reads`, `test_auto_increment_wraps`, `test_other_address_ignored`.
- **Now covered by:** the same tests; the helper samples `h_rvalid` right after the accepting edge.
- **Fix:** in the same commit as the tests.

## 7: `tools/profile` package broke every cocotb test
- **Date:** 2026-09-25
- **Symptom:** `protocols/uart/test`: `AttributeError: module 'profile' has no attribute 'run'`, no test ran.
- **Root cause:** the protocol test Makefiles put `tools/` on `PYTHONPATH`; a package named `profile` there shadowed Python's standard-library `profile` module, which cocotb imports.
- **Caught by:** the UART RTL suite (run after resizing the UART counters).
- **Now covered by:** every protocol suite (they import cocotb with `tools/` on the path); the package is `tools/profiling/`.
- **Fix:** renamed before the first commit of the profiler.

## 8: First D-017 stripe offsets put the east tiles' ground stripe outside the tile
- **Date:** 2026-09-26
- **Symptom:** `OpenROAD.GeneratePDN failed` for E_IO4, NE_term, SE_term (68.64 µm wide) after the tile stripe grid change.
- **Root cause:** arithmetic: offset 61.28 put the VPWR stripe at local 63.11–65.21 and VGND 4.1 µm further right, past the core edge (65.76). I had checked the power stripe position but not the ground stripe and the 2.88 µm core margins.
- **Caught by:** the tile flow's power-grid step.
- **Now covered by:** the same step, plus a written constraint in D-017 (every column type must fit a full VPWR+VGND pair: grid phase between 3.9 and 19.3 µm; chosen 12.00) and a pin-position check of every tile LEF before stitching.
- **Fix:** grid phase 12.00 (offsets 9.12 west / 50.40 others), before any commit.

## 9: Chip-level routing could not finish: fabric pins faced the die edge
- **Date:** 2026-09-27
- **Symptom:** CI `gds` run 36277723397: detailed routing still at ~10,500 violations (Metal1 3.6K, Metal2 5.4K, Metal3 1.5K) after 27 iterations, > 3.5 h into the job (log excerpt pasted by the user).
- **Root cause:** placement. The fabric macro sat at (11.52, 7.56), with its west face 8.6 µm from the die edge and its south face 3.8 µm from the bottom, but 152 of its 243 signal pins are on the west face (FrameData[127:0], west IO) and 67 on the south face (FrameStrobe[59:0], clock/reset). Every wire had to escape through a few tracks. I chose the location for the power and track grids only and did not check the macro's pin faces.
- **Caught by:** the chip-level `gds` job (detailed routing did not converge).
- **Now covered by:** the placement rule in D-019 (revision): pin-heavy macro faces must face open core; the pin-face count of the macro LEF is checked before choosing a location. The next `gds` run is the check.
- **Fix:** macro at (890.88, 113.40), same power-grid phase.

## 10: `"//"` comment keys inside a MACROS entry stopped LibreLane at config load
- **Date:** 2026-09-27
- **Symptom:** CI `gds` run 36292542000 failed after 3 min: `One or more keys unrecognized for dataclass Macro: //`.
- **Root cause:** I put `"//"` comment keys inside `MACROS.warp_tiny` in `src/config.json`. LibreLane accepts them at the top level only.
- **Caught by:** LibreLane config loading in CI.
- **Now covered by:** a local run of TT's merged config (`src/config_merged.json` from `tt_tool --create-user-config`) with the Nix LibreLane before pushing: it loads the config and runs through synthesis, floorplan, macro placement, the power grid (all LOOMPDN checks pass), global routing (0 overflow, 3.5 % usage) and detailed routing (0 violations, < 2 min). A comment in `config.json` warns against nested `"//"`.
- **Fix:** comments moved above the block.

## 11: Precheck pin check: pdngen added short power stripes beside the fabric
- **Date:** 2026-09-27
- **Symptom:** CI run 36293031051: `gds` and `gl_test` passed, precheck failed the pin check: `Port VGND/VDPWR is too far from bottom/top edge of module: 98.06 > 10 um` (4 errors).
- **Root cause:** with the fabric at x 890.88, the standard-cell rails in the 38 µm channel between the fabric and the core's east edge were not crossed by any grid stripe (the last pair runs inside the fabric, the next would be off the die). pdngen then adds a short "channel" stripe pair (x 1270.08 / 1274.40, y 98.06–612.58, the fabric's height plus halo), and TT requires every power port to span the block height.
- **Caught by:** TT precheck pin check (`pin_check.py`).
- **Now covered by:** a local stripe check after the power grid (every vertical Metal4 power stripe must reach within 10 µm of the top and bottom edges), run on TT's merged config before pushing. It flags both short stripes in the failed run's final DEF and finds none with the fix. Rule added to D-019: leave either no channel or one wide enough for a full grid stripe pair beside a macro.
- **Fix:** fabric at x = 780.96 (one grid step left): the 148 µm east channel holds a regular stripe pair; 24 full-height stripes, 0 short; routing 0 overflow, 0 DRC locally.

## 12: A zero-length load reached LOADED
- **Date:** 2026-09-27
- **Symptom:** the F2 cover run reached RUNNING in 15 cycles, too few for any real load: LOAD_BEGIN with LENGTH 0, then LOAD_END with the CRC of no words (0x00000000), passed every check.
- **Root cause:** the sync-word check ran on the first LOAD_DATA word; with no words there was no first word, so nothing flagged the load. A host could then RUN whatever partial configuration an earlier failed load left in the latches, which ARCHITECTURE §3 forbids.
- **Caught by:** `formal/f2_loader.sby` cover task (the trace length, not an assertion: the shadow loader had the same blind spot).
- **Now covered by:** LOAD_END rejects a load with no words as a format error (0x13); the F2 shadow requires at least one word; pin-level test `test_empty_load_rejected`.
- **Fix:** `src/wp_shell.v` LOAD_END check `fmt_err || wcount == 0`.

## 13: FABulous bitgen drops the global-clock mux selects
- **Date:** 2026-09-27
- **Symptom:** with the real fabric RTL, `counter4` loaded and reached RUNNING but its outputs stayed X; `logic4`, also clocked, worked.
- **Root cause:** `fabulous_bit_gen` 0.3.1 (`_apply_fasm_features`) skips every FASM feature whose name contains "CLK", meant for the bit-less `GCLK_END0.Lx_CLK` pips. It also drops `Xn Ym.N_GBUF_ENDk.GCLK_BEG0`, the select of the LUT tile's 4-input global-clock mux in the tile library. nextpnr routed counter4's clock through GBUF C (mux input 2); the select stayed 0, so the flip-flops never saw a clock. logic4's clock happened to use GBUF A (input 0, the all-zeros default). Stock FABulous fabrics have no such mux, which is presumably why upstream has not hit it; Tiny FABulous's own copy of the script has the skip commented out.
- **Caught by:** `test/test_bitstream.py::test_counter4` on the fabric RTL, then tracing the clock hop by hop from the pad to the LC (GBUF feed, SW_term, N_GBUF, the GCLK mux).
- **Now covered by:** `tools/compile/bitgen.py` (no skip, all rows); `test_gclk_mux_select_is_written`; `test_counter4` (clock through GBUF C). `test_matches_fabulous_bit_gen_except_clk_features` checks our generator equals upstream's on everything else.
- **Fix:** WARP's own bitgen in the compile flow. Upstream not edited (worth reporting to FABulous).

## 14: Compile flow merged two carry chains' start cells
- **Date:** 2026-09-27
- **Symptom:** `hostecho` (two 8-bit adders) failed place and route: `Carry cell ... carry_statrt has illegal multiple fanout on Co net`.
- **Root cause:** the compile flow's `opt_merge -share_all` (added to merge the identical enable/reset LUTs ABC duplicates per flip-flop, D-022) also merged the two adders' identical carry-start `LUT4_HA` cells; one carry output then fed two chains, which the fabric's carry wiring cannot do.
- **Caught by:** building `tools/compile/examples/hostecho` (nextpnr packing).
- **Now covered by:** `opt_merge -share_all t:LUT1 t:LUT2 t:LUT3 t:LUT4` (plain LUTs only); `hostecho` is a committed test bitstream, rebuilt and checked by the `fabric` workflow.
- **Fix:** `tools/compile/compile.py` synthesis script.

## 15: Placement failed with free logic cells: too many clock-enable nets for the tiles
- **Date:** 2026-09-27
- **Symptom:** the I2C controller on G1 needed 78 of 88 LCs but nextpnr found no legal placement (`Unable to find legal placement for cell ... FABULOUS_LC`), for every seed. On G0, the SPI controller (95 of 96) failed the same way.
- **Root cause:** the 8 LCs of a `LUT4x8_ha` tile share one clock-enable and one set/reset wire (`J_EN`, `J_SR` in the tile's switch matrix). Yosys mapped every enable it found onto the flip-flops (`-complex-dff`), so the I2C controller had 12 distinct enable/reset pairs, most of them used by a single flip-flop, for 11 LUT tiles. Each pair needs a tile of its own, whatever the LC count says.
- **Caught by:** `python -m compile.protocols` on G1 (place and route), then counting the flip-flops' (E, R) nets in the synthesized netlist.
- **Now covered by:** the compile flow runs `dfflegalize -mince 4 -minsrst 4` between `synth_fabulous`'s stages (`MIN_CTRL` in `tools/compile/compile.py`): an enable or synchronous reset used by fewer than 4 flip-flops becomes LUT logic. The same designs also got smaller (uart 37 → 29 LCs, spi_ctrl 51 → 47, i2c_ctrl places at 70; thresholds 2, 4 and 8 compared, `docs/reports/g1_results.md`). The protocol fit tables are the regression check.
- **Fix:** `tools/compile/compile.py` synthesis script. Consequence for architecture work: LC count alone is not capacity on this tile; the number of control sets is a second limit (phase 3 input).

## 16: I2C target rewrite left sda_o undriven
- **Date:** 2026-09-27 (caught before commit)
- **Symptom:** Verilator: `Signal is not driven: 'sda_o'` in the rewritten `protocols/i2c_target/i2c_target_top.v`; the RTL tests all passed.
- **Root cause:** the rewrite (shared register ports, hard shift register) dropped `assign sda_o = 1'b0`, the open-drain pin's output value. Undriven, it would float in simulation and be left to synthesis on the chip. The tests drive and watch only `sda_oe` (the open-drain model), so they could not see it.
- **Caught by:** a Verilator `-Wall` lint of the design, run by hand; CI linted only `src/`.
- **Now covered by:** the `lint` workflow lints every protocol user design in both forms (`PRIMS=0/1`) with `-Wall`; all 8 are clean (Verilator 5.020, the CI version).
- **Fix:** the assign restored.

## 17: Fmax of designs using the hard primitives left out every path through them
- **Date:** 2026-09-27 (found in review; no rate was claimed from these numbers)
- **Symptom:** `compile` reports and `docs/reports/g1_results.md` gave Fmax for UART (123.5 MHz), SPI (88.9) and I2C controller (69.2) on G1; the critical paths shown were all LUT to LUT, although these designs have paths from the timer's `tc` and the shift register's `q` into logic, and from logic into the blocks' `load`, `step` and `en`.
- **Root cause:** nextpnr's FABulous back end gives timing arcs only to the tile library's own cells (LUT 3.00 ns, clock-to-Q 1.00 ns, setup 2.50 ns, fixed) and times routing with the fabric's extracted pip delays. The WARP primitive BELs (`wp_timer`, `wp_shift`) get no arcs, so their pins are neither start nor end points and every path through them is dropped from the analysis.
- **Caught by:** reading the critical-path reports while documenting the timing model (PHASE2 item).
- **Now covered by:** the report marks the column as incomplete and no rate is claimed; OVERVIEW risk updated; the phase 2 timing-model item stays open until the primitives have timing arcs (or a documented conservative bound) and a configured design is cross-checked by STA.
- **Fix (2026-09-27/28, D-028):** primitive timing arcs from OpenSTA of each primitive synthesized alone (slow corner), written to `placement_estimate.txt`; the compile flow uses nextpnr 0.11.1 (OSS CAD Suite 2026-09-27), which reads it (upstream nextpnr reads per-BEL arcs since 2026-07), and refuses a fabric with primitives but no arcs. Cross-checked against STA of the hardened primitive tile (`tools/timing/tile_check.sh`): the first margin (×1.5) under-covered the timer's in-tile setup (4.0 vs 1.4 ns standalone), so setup/combinational arcs use ×3.0, clock-to-out ×1.5. Result: UART 90.7 MHz, SPI 78.0, I2C controller 53.0 (were 122.0, 88.9, 69.2 with those paths untimed), all above 50 MHz.

## 18: Reset release not synchronized to the clock
- **Date:** 2026-09-28
- **Symptom:** TT's Verilator lint in the `gds` job: `SYNCASYNCNET: Signal flopped as both synchronous and async: 'rst_n'` (present since the phase 2 shell; noticed by the user in the linter summary).
- **Root cause:** the TT `rst_n` pin (driven by the demo board, asynchronous to `clk`) goes unsynchronized to FABulous's `ConfigFSM` as an asynchronous reset and to the shell, the pin logic and the user reset as a synchronous reset. Its release can land at any point of the clock cycle, so flip-flops can leave reset on different cycles, or go metastable (the configuration FSM and its strobe register included). Effect in the worst case: a wrong state right after reset (e.g. a first load that fails and must be retried); no effect once reset has been released cleanly.
- **Caught by:** the TT workflow's lint summary (not an error there); our `lint` waives upstream files (`src/lint.vlt`) and does not run this check on the whole top.
- **Now covered by:** the full-top Verilator `-Wall` lint without waivers reports no `SYNCASYNCNET` (and no `WIDTHTRUNC`); `test/` suite 21/21 on the fabric RTL, black-box mode 13 + 8 skipped; F1 PASS (k-induction). CI 36383587262 on 3047dea: gds, precheck, `gl_test` 21/21, setup WS +12.48 ns.
- **Fix:** `src/tt_um_warp.v`: a 2-flop reset synchronizer (`rst_sync`, no reset of its own); every block is reset from `rst_s_n`, and the configuration path (ConfigFSM's asynchronous reset) from its own copy one flop later (`rst_cfg_n`), so no net is used as both a synchronous and an asynchronous reset. Reset now takes effect 2 clocks after `rst_n` falls and ends 2 clocks after it rises (3 for the configuration path). Also `src/wp_fabric_cfg.v` passes Frame_Data_Reg's `Row` sized to its width (the `WIDTHTRUNC` warning; no logic change). The next hardening's one change.

## 19: Active-low outputs are asserted while the chip is stopped
- **Date:** 2026-09-28
- **Symptom:** `test_board_examples_spi`: the SPI target model saw an empty CS-low transaction before the real one.
- **Root cause:** by design (ARCHITECTURE §4, F1), every fabric output is parked while the chip is not RUNNING: `uo_out[2..7]` at 0 and `uio` released (output enable 0). A user output that is **active low** on a `uo_out` pin, such as the SPI controller's CS_N on FAB_OUT2, is therefore asserted from reset through loading, and again after STOP. No SCK edges happen then (SCK parks at 0 = idle for mode 0/1), so no data moves; but a device that acts on CS alone (e.g. a flash leaving deep power-down) sees it. The parking itself is the chip's safety property and stays; the hardware is frozen.
- **Caught by:** `test/test_bitstream.py::test_board_examples_spi` (a reference target on the pins from reset on).
- **Now covered by:** the test asserts the behaviour (at most one empty transaction before RUN); `docs/EXAMPLES.md` documents it and the fix at the pin-map level.
- **Fix:** user-level: put active-low outputs on bidirectional pins (`FAB_IO*.o` with an enable, plus a pull-up), which park released (high through the pull-up). No hardware change.

## 20: Fabric RTL test reused the idle-fabric simulator from the previous command
- **Date:** 2026-09-28
- **Symptom:** following the README from a clean source export, `scripts/check_all.sh` passed, but the next command, `make -C test WARP_FABRIC=rtl`, failed `test_counter4`: the counter stayed at zero. The second command's log had no Icarus compile step.
- **Root cause:** `test/Makefile` put both the default `stub` model and the `rtl` fabric model in `test/sim_build/rtl`. Cocotb's Makefile saw the executable built for `stub` as current and reused it, even though `WARP_FABRIC` changed.
- **Caught by:** the Phase 5 clean-source README reproduction, in the documented command order.
- **Now covered by:** `test/Makefile` uses `sim_build/$(WARP_FABRIC)` for RTL simulations, so a change between `stub` and `rtl` requires a new compile. The clean-source reproduction reruns the two commands in order.
- **Fix:** separate simulator build directories by fabric model. No chip RTL change.

## 21: LibreLane DRC XML merges violations from different metal layers
- **Date:** 2026-09-30
- **Symptom:** session 34's generated XML reported all 3,384 shorts as `Metal3.Short`, unlike the native router report: 471 Metal2, 1,278 Metal3 and 1,635 Metal4 shorts.
- **Root cause:** pinned LibreLane `common/drc.py::DRC.from_tritonroute` indexes its violation dictionary by violation type alone, retaining the first layer while appending coordinates from subsequent layers. Total counts and coordinates remain useful; the XML category is not reliable for layer attribution.
- **Caught by:** comparison of `cfgmacro_x121_m4obs/39-openroad-detailedrouting/tt_um_warp.drc`, the router log and generated XML.
- **Now covered by:** session 34's corrected layer counts and the compact-edge experiment README explicitly require native router reports for layer attribution. Upstream code is unchanged.
- **Fix:** use the native `.drc` report/router log when reporting layer counts; an upstream converter fix remains open.

## 22: Concurrent FABulous tile parsing corrupts shared primitive JSON
- **Date:** 2026-09-30
- **Symptom:** concurrent north/south scratch tile hardening failed with `JSONDecodeError: Invalid control character` while reading `primitives/IOBUF/fabulous/IOBUF.json`; serial reruns passed.
- **Root cause:** FABulous's `fabric_definition/yosys_obj.py` writes parsed BEL metadata beside the shared primitive. Two tile drivers in the same library can overwrite/read that file concurrently.
- **Caught by:** the compact-edge north/south hardening experiment.
- **Now covered by:** `spikes/compact_edges/run.sh` runs tile drivers sequentially; all 14 changed tiles completed with clear routing and KLayout DRC. Per-tile run IDs are in the experiment README.
- **Fix:** serialize tile parsing in a shared library. Upstream code is unchanged.

## 23: Scratch simulation driver exits successfully after a cocotb failure
- **Date:** 2026-09-30
- **Symptom:** the new hardened-fabric/post-CTS-shell test returned process status 0, but its results XML contained a failed test (`X` in a status read after RUN).
- **Root cause:** `runner.test()` wrote the result XML without raising for that failed test; the scratch driver checked neither test count nor failure/error elements.
- **Caught by:** inspecting `simulation_chip_mask_narrow_rows_mapped_fabric_mapped_shell/results.xml` and `test.log`. Earlier reported passes were checked against their XML and remain valid.
- **Now covered by:** `spikes/compact_edges/simulate.py` explicitly rejects missing testcases and failure/error elements after the simulator finishes.
- **Fix:** validate XML and raise on failure. The hardened-fabric unknown-value issue is separate and remains under investigation; no gate-level pass is claimed for that run.

## 24: I2C decoder failure hid sigrok's environment error
- **Date:** 2026-10-05
- **Symptom:** the I2C controller's independent bus checks passed but the sigrok byte comparison returned an empty list.
- **Root cause:** sandboxed libusb initialization returned `LIBUSB_ERROR_OTHER`; sigrok exited 0 with empty stdout and the harness discarded stderr. This was an execution-environment failure, not an observed RTL fault.
- **Caught by:** `scripts/check_all.sh`, then a diagnostic rerun of `protocols/i2c_ctrl/test`.
- **Now covered by:** `sigrok_decode` rejects an empty decoded byte list and includes stdout/stderr in the assertion. The full check rerun outside the sandbox passes (`build/check_all_20261005.log`).
- **Fix:** retain decoder diagnostics in the test and run libusb-dependent checks with the required execution permission. No RTL change.

## 25: Scratch shared-word CRC read a changing byte-assembly wire
- **Date:** 2026-10-05
- **Symptom:** the scratch CRC passed stable-input unit comparisons but the real 842-word SPI load failed with CRC error `0x12`.
- **Root cause:** the first integration read `{pay, rx_byte}` directly. The shell shifts `pay` on the same edge as word completion, so that concatenation changes immediately after the original CRC would have captured it. Host word spacing alone does not make this wire stable.
- **Caught by:** `simulation_chip_shared_crc/results.xml` real SPI load, before any physical selection.
- **Now covered by:** the full SPI/UART/STOP scratch test and `test_internal/shared_crc_probe.py`, which checks that the actual registered input remains stable throughout CRC processing. The stable-word unit test still compares every cycle to the original CRC and final values to zlib.
- **Fix:** the optional scratch shell connects CRC to the existing `cfg_word` register, updated at the word-complete edge; bit consumption begins on the following edge. The corrected real load/UART test passes (`build/arch_explore/compact_edges/shared_crc_shell_20261005.log`). Frozen G1 is unchanged; the physical experiment is still unselected.

## 26: Independent input monitor misses events on a synthesized gate shell
- **Date:** 2026-10-05
- **Symptom:** Existing SPI-loaded UART+monitor passes RTL fabric/shell testing, but a newly synthesized gate shell with RTL fabric transmits correctly and returns zero event count after20 input pulses.
- **Root cause:** under investigation. Read-only tracing shows synchronized fab_in transitions known, event_previous FF updates, resets/enables known, but the counter enable is zero at sampled clock edges. Mixed gate/RTL input-to-enable scheduling/timing is a hypothesis, not proven silicon behavior. No user state or configuration forced.
- **Caught by:** `build/g1_monitor_gate_20261005/results.xml`, Icarus13/project-venv cocotb; synthesized shell is not the hardened netlist. White-box traces in `probe3.log`/`probe4.log` and `test_internal/uart_monitor_gate_probe.py`.
- **Fix for the observed test:** sample the shell input into one additional fabric FF before forming the edge enable; adds one cycle of observation latency and one LC (36→37). Both actual loaded regressions PASS: `uart_monitor_sampled_20261005/rtl_results.xml` (23.23s) and `g1_monitor_gate_20261005/sampled_results.xml` (33.82s), under `build/`. This resolves the observed mixed-model mismatch; physical timing/root-cause proof remains open. No frozen hardware change.
- **Coverage:** `test/test_uart_monitor.py`, overlapping TX/events, RX/events, counter wrap, framing status and host reset; prospective same test on gate shell. Fix commit: pending.

## 27: Failed compiler rebuild could leave a stale success report
- **Date:** 2026-10-05
- **Symptom:** rebuilding into an existing output directory could fail place/route while retaining `report.json` from an earlier successful design.
- **Root cause:** success reports were written only after completion, with no invalidation when a new build began.
- **Caught by:** a deliberate stale-success report followed by the over-capacity binary-I2C build (95/88 LCs), `build/compiler_fit_diagnostic_20261005/verification.txt`.
- **Fix:** invalidate prior success/failure reports at build start; place/route failures write a separate `failure.json` with utilization and actionable capacity diagnostics.
- **Coverage:** compiler diagnostic regression in `tools/compile/tests/test_diagnostics.py`; actual vendor-tool check above. No hardware change.

## 28: Failed compiler rebuild retained an old loadable image
- **Date:** 2026-10-05
- **Symptom:** invalidating reports alone still left the earlier `.wbit` at the path users would load after a failed rebuild.
- **Root cause:** images were overwritten only on success, without invalidation when rebuilding the same target.
- **Fix:** remove the exact target image after reading the pin-map top/name and before synthesis; preserve differently named images. A subsequent success generates the image normally.
- **Caught/covered by:** extended compiler diagnostic tests and actual95/88-LC binary-I2C failure (`build/compiler_stale_image_20261005/verification.txt`). Fresh successful fault-demo rebuild remains byte-identical to the already loaded/tested image. No chip change.

## 29: Default primitive timing audit could select a newer experimental tile
- **Date:** 2026-10-05
- **Symptom:** default tile timing check selected the latest completed PRIM2T2S run even when its netlist differed from the committed G1 tile; historical run paths were absent.
- **Root cause:** selection used recency and file existence, without binding the routed artifacts to the chip being assessed.
- **Caught by:** fresh audit/source check; committed netlist SHA25613fec76424949b0d25789ca8d0721b74d4acdba5ff93eaeb99dfb4d412f6a170 differs from latest run2c49c0e6dba54229e6d9e267df28dc373a5191258fb08b716bb7ee7ff6973dc0. No completed local run is byte-identical to the committed tile; semantic equivalence of other runs is not established.
- **Fix:** default selects only matching netlists and requires matching SPEF; an explicitly supplied variant is rejected unless `WARP_TIMING_ALLOW_VARIANT=1`, which labels the comparison experimental. A byte mismatch is conservative rejection, not proof of functional difference.
- **Coverage:** `build/primitive_path_audit_20261005/default_missing_artifact_check.log` rejects unavailable matching evidence; explicit missing-artifact and variant checks; shell syntax passes. Historical timing numbers remain historical; no refreshed G1 timing pass claimed.

## 30: Bare OpenDB cell swap crashes the pinned STA callback
- **Date:** 2026-10-06
- **Symptom:** isolated pin-hotspot resize crashes with signal11 before placement; no output database is written.
- **Root cause:** geometry-only helper reads an ODB without Liberty, then calls `dbInst.swapMaster`. The pinned callback `dbStaCbk::inDbInstSwapMasterBefore` reaches `sta::ConcreteCell::portCount` without loaded Liberty cell objects. This is a scratch-tool setup issue, not an observed chip fault.
- **Caught by:** `build/route_root_audit_20261006/chip_nor3_pin_screen/placement.log` stack trace and exit139.
- **Fix/coverage:** require `WARP_SIZE_LIB` and `read_liberty` before `read_db`/swap. Actual rerun `placement_with_liberty.log` reaches detailed placement, which separately reports a local legalization failure; no routing or legalization pass claimed from resolving the crash. Frozen/upstream files untouched.

## 31: Hosted fault-monitor compile omitted its monitor dependency
- **Date:**2026-10-06.
- **Symptom/check:** hosted compact experiments37511778394; monitor compiles/audits and passes loaded RTL in22.72s, then fault synthesis reports missing uart_monitor_top.
- **Root cause:** new cloud driver supplied fault top and UART sources but omitted the intermediate monitor module present in the documented local compile command.
- **Fix:** include protocols/uart_monitor/uart_monitor_top.v only for the fault case. No hardware/compiler change.
- **Coverage:** hosted37512249763 at f671c1b passes all four fresh compile/audit/loaded RTL cases; independently checked four XMLs, exactly one case each, no failure/error/skip. See `docs/reports/hosted_experiments_20261006.md`. The first run remains failed; no native/SDF result is implied.

## 32: Docker no-TTY flag followed eager container launch
- **Date:**2026-10-06.
- **Symptom/check:** compact37512885358 attempt2 route job downloads/verifies inputs and Docker image, then exits with the input device is not a TTY before OpenROAD starts.
- **Root cause:** cloud driver placed docker-no-tty after dockerized; LibreLane's eager container callback launches before later options are applied.
- **Fix:** place docker-no-tty first. No source/PDK/physical checker changes.
- **Coverage:**37516278474 passes container launch and reaches directory validation;37516794406 passes that validation and remains in the routing step. No final routing pass implied. [Pinned CLI contract](https://github.com/librelane/librelane/blob/3.1.0.dev3/librelane/__main__.py).

## 33: Tighter native fabric retains unknown user state after real load
- **Date:**2026-10-06.
- **Symptom/check:**37512885358 attempt2 native job: tighter RTL control passes; actual mapped fabric fails UART recording with X at output. All8707 configuration bits are known and image-matching;26944 CRC processing cycles have stable input. Selected user registers already unknown before RUN despite shell user_reset=1/user_rst_n=0.
- **Root cause:** unresolved. Known configuration is insufficient to distinguish mapped logic/reset behavior from zero-delay combinational/model pessimism. No hardware/model fix claimed.
- **Next coverage:** derive a read-only cone JSON from the exact mapped tile and trace LB register D logic at pre/post RUN; separately probe the real USER_RESET command while retaining ordinary native failure. No configuration or user-state force. Existing D-023 routing harness remains explicitly limited; native/SDF acceptance is open.
- **Follow-up:**37516794406 cone extraction/RTL control pass; native baseline18.81s and real USER_RESET probe19.12s both fail with UART X. Known configuration does not identify the root cause. Next diagnostic follows selected mux branches and actual UART output at Tile_X6Y2, with tile boundaries labeled explicitly.
- **Failure-time evidence:**37519661148 shows UART X at4423540ns persists after same-edge delta-cycle settling. Actual selected output cone reaches Tile_X6Y2.E2END[7]. Next read-only probe follows exact macro connections across tiles and stops at clocked state; no hardware fix established.
- **Isolated state source:**37521660597 filtered UART cone ends at Tile_X2Y3_LUT4x8_ha_C2.Inst_LH_FABULOUS_LC.LUT_flop after41unknown nodes, D=X/RESET_B=1 at failure. Next probe checks that register's exact data/reset paths and configuration selectors. This identifies a source state boundary, not the original cause of unknown state.
- **Timer evidence:**37522773342 timer count becomes configured15/armed1 after RUN, then counter goes entirely unknown while armed remains1. Added first-known-to-X edge watcher with stable pre-edge D/reset snapshots; later feedback X alone does not identify original corruption.
- **Before corruption:**37523983755 at4423490ns timer count remains15, but D inputs are allX with reset pins1. All8707 configuration bits still match the loaded image. Trace follows upstream logic; original cause remains unresolved. Unknown mux selectors are filtered only when Boolean sensitivity proves irrelevance under known inputs.
- **Direct comparison:**37532673220 still reaches trace cap despite selector filtering. Added separate RTL companion sharing real shell/configuration input ports and ordinary D-023 routing pulse; native outputs remain authoritative. Compare timer control/state and tile route vectors without changing actual mapped netlist, configuration or user storage. Hosted verification pending.
- **Matched-input result:**37535155011 reaches UART X with same-input companion snapshots. At4423490ns local timer load/half are unknown while RTL retains count15. Unregistered constant LUTs (X1Y2 LD=0, X2Y1 LB=0/LD=1) have native O=X. Next probe traces those actual mapped cones; neither benign pessimism nor a hardware root cause is established. See compact_native_diagnosis.md for scope and run evidence.
- **Verified local false-X:**37546145073 proves those three constants in actual mapped logic for arbitrary binary tile inputs/user state under all529 observed configuration latch values per tile.37546984612 independently audits all9164 actual latches against loaded frame image, all known/matching at pre-corruption. D-047's five-mux4 candidate passes exhaustive symbolic binary equivalence and2916 partial-input tests in37546784325. Whole native UART remains unresolved; regenerated native candidate37552796495 pending, no physical/timing promotion.

## 34: Hosted LibreLane requires existing forced run directory
- **Date:**2026-10-06.
- **Symptom/check:**37516278474 route passes Docker launch, then CLI rejects nonexistent forced native_route directory before OpenROAD.
- **Root cause:**3.1.0.dev3 validates force-run-dir with exists=True; our fresh cloud root omitted its run directories.
- **Fix/coverage:** create both empty native/geometry run directories under the already freshness-checked output root before invoking CLI.37516794406 passes validation and continues in the routing step; physical checker results pending.

## 35: Distribution Yosys cannot parse PDK model specify syntax
- **Date:**2026-10-06.
- **Symptom/check:**37516278474 native RTL control passes; new read-only cone extraction fails parsing PDK Verilog line43's specify syntax before native tests.
- **Root cause:** distribution Yosys parser does not support this PDK model timing syntax, even when read as black-box library.
- **Fix/coverage:** read signal port directions from the pinned standard-cell Liberty with read_liberty -lib, then read actual tile netlist without mapping/optimization.37516794406 successfully emits actual_tile_cone.json and reaches both native tests. Simulation uses unchanged official Verilog/UDP models. BUG33 remains open; fixing extraction does not qualify hardware.


**BUG33 resynthesis follow-up:**37552796495/37553037381 five-mux candidates
pass actual SPI-loaded native UART. Matched original-LUT resynthesis37553190074
also passes, so a mux-only causal claim is unsupported. Original hardened
netlists still fail; regenerated netlists require matching physical/timing
validation. Next coverage adds real USER_RESET and preserves candidate netlists.

## 96: New branch-only manual workflow is not yet registered for dispatch
- **Date:**2026-10-15.
- **Symptom/check:** initial router_force_build.yaml dispatch at6665d84 returns GitHub404; no build launched.
- **Root cause:** the new workflow exists only on efpga while repository default main is TRIPWIRE, and a manual-only workflow has not been registered there.
- **Fix/coverage:** narrowly trigger on pushes editing its own workflow on efpga; retain manual replay, read-only token and finite build timeout. Do not modify main or interpret404 as a build failure. Verify actual Actions run identity after registration.

## 123: Representative route buffer adapter provenance mismatch
- **Date:**2026-10-23.
- **Symptom/check:**40007850249 both widths fail frozen input admission before native flow.
- **Root cause:** expected cached adapter hash includes explicit SYNTH_BUFFER_CELL arguments on both buffer_ports calls; workflow fetched unchanged pinned upstream lacking those two arguments. Netlist hash is correct.
- **Fix/coverage:** owned patches/r1_explicit_buffer_cell.patch under D107, staged copy, upstream SHA bd134f7e02a401ade48c365f0c9ed2b6d950526ccc92c71a777d039ff0fd8e0e and patched SHA7b9526fcc9676d6f266e457344c6b71921eebea7e2600c3df489de1475c1f2e6 checked before flow. Zero-fuzz patch and exact digest replay locally; hosted retry required. No routing conclusion from admission failure.

## 124: Full-height power pin checker rejects auxiliary boundary patches
- **Date:**2026-10-23.
- **Symptom/check:**40009049924 both widths finish GRT with zero final overflow, then fail full-height pin assertion.
- **Root cause:** native BPin geometry includes full-height stripes plus 200nm edge patches. Checker incorrectly required every rectangle to span the height.
- **Fix/coverage:** validate every rectangle positive/in bounds/on correct phase; group by exact stripe x bounds and require a full-height rectangle for each group. Boundary-only patches remain rejected. Focused positive/negative tests and retained ODB-hash/result replay pass at both widths; hosted replay pending.

## 125: Native south-I/O import drops chained multi-output alias ports
- **Date:**2026-10-23.
- **Symptom/check:**40011371177 all-type gate passes18/20cases; both S_IO2 pin stages reject N_GBUF_BEG/E_GBUF_END/E_GBUF_BEG patterns. Native DEF has143pins versus155frozen signals; all12clock-feed alias ports absent.
- **Root cause under test:** exported four-bit chain N_GBUF_BEG=E_GBUF_END then E_GBUF_BEG=N_GBUF_BEG is not retained by native import. No clock-feed cells are present on this transparent path. Other18imports/censuses pass.
- **Repair hypothesis/coverage:** flatten only the4output-to-output aliases to the identical frozen input bit; validate bit IDs/directions and reject cycles/mismatches, no cell insertion. Exact assembled ports/cell connections unchanged locally; hosted retention replay required. Do not filter absent ports or weaken strict unmatched checks.

## 126: Border direction-group order misaligns actual neighbor pins
- **Date:**2026-10-23.
- **Symptom/check:**40011371177 retained native narrow N_IO.N1END[0] center53.28µm versus connected LUT.N1BEG[0]18.72µm, same Metal2/opposite edges. Planned order reveals216/3064connected bit pairs with inconsistent indices.
- **Root cause:** generic per-tile pin generation orders port direction groups differently at borders; same-type LUT alignment does not cover mixed-type neighbors.
- **Fix/coverage:** derive common ordered track equivalence classes from actual generated fabric connections, separately for six facing-side families. Preserve proven LUT N/E anchor order, require every facing side exposes identical unique classes, emit exact scalar pin regexes. Missing/aliased classes, wrong sides and unsupported order policies rejected. Local55R1testsPASS and isolated10tile preparationPASS; native rerun required. Logical graph/configuration unchanged.

## 127: Configured smoke debug log assumes an RTL-only hierarchy
- **Date:**2026-10-23.
- **Symptom/check:**first all-mapped local launch loads image, then raises AttributeError on SW_term.GBUF_D_IN before traffic; strict XML rejects it.
- **Root cause:** nonasserting clock debug log references an RTL-only internal name removed by mapped export.
- **Fix/coverage:** remove internal hierarchy diagnostics; retain all loader and adapter-pin traffic/backpressure/rate assertions. Local full-mapped40instance test now executes1PASS, strict XML and47input hashes checked. No RTL/PDK/image change or stimulus relaxation.

**BUG125 isolated root cause/fix:**40012576053 at39c656a still admits18/20and drops the same12S_IO2ports: alias flattening alone is rejected as a solution. Export also contains4duplicate assignments to E_GBUF_BEG, first directly from E_GBUF_END and again through N_GBUF_BEG. Local native import probe (OpenROAD dcf36133a369abc8f3c5e5738cd4d82e4903c0e0, distinct from hosted acceptance tool) yields original143/flattened143/deduplicated155ports. Add exact duplicate removal after frozen-bit-checked flattening; reject conflicting/cyclic drivers. No buffers/cells inserted. Hosted corrected replay required. BUG126 N_IO/LUT witness now matches18.72µm on both sides in retained40012576053geometry.

## 128: Uniform narrow primitive footprint omits placer pin-density reserve
- **Date:**2026-10-23.
- **Symptom/check:**40014699181 both154.08µm primitive columns fail GPL-0301 before routing; both219.84µm cases pass final global overflow/PGchecks.
- **Root cause:** narrow core26350.5312µm², physical cells+92output buffers25427.0016µm², native pin-density area adjustment1426.445µm² rounded. Effective26853.446µm² exceeds core (101.909%). GPL/DPLpadding are both0; raising placement density cannot fix this capacity failure. Uniform154.08primitive outline rejected; no evidence of compiler/config/latch loss.
- **Proposed coverage:** D111one measured corrective width164.64only at primitive columns, preserving96%density/routability reserve/graph/layers/clock. Derived using rounded-up pin-adjusted area plus largest225.660µm² reference routing inflation; core-height/margins/site grid fixed.57local R1testsPASS; corrected native routing pending. No whole-grid/timing acceptance.

## 129: External east power pair does not prove east-border tile is powered
- **Date:**2026-10-23.
- **Symptom/check:** D111primitive growth1082.88µm outer width retains a chip east-channel pair, but fixed68.64east-border tile starts at macro-local1014.24 and its next VPWRstripe is local96.96, outside the tile.
- **Root cause:** chip-channel geometric check misses each leaf's independent Metal4grid phase. The leaf primitive routing pass does not qualify the proposed full layout.
- **Fix/coverage:** static layout_budget.py checks a complete in-core VPWR/VGNDpair in all eight column footprints and rejects this layout. D112reallocate21.12µm from underfilled west border (68.64→47.52) to two primitive columns, preserving1061.76outerwidth/eastborderphase8.16. Pure arithmetic/onebuffer-per-output model passes; native westborder/newprimitive-phase/interface gates still required.60local R1testsPASS; no production change.

## 130: Diagnostic adapter omitted auxiliary system reset
- **Date:**2026-10-23.
- **Symptom/check:** input-coverage review after native-primary gate40037694777 finds Tile_X0Y4_SYS_RESET_RESET_topunconnected; the adapter defaulted only *_OUT_topinputs. Primary sample passed despite this diagnostic limitation.
- **Root cause:** input-discovery regex excluded the differently named auxiliary reset, while ordinary rst_ncell was driven. Production top already drives auxiliary active-high user_reset; no production defect or hardware change.
- **Fix/coverage:** discover every scalarTileinput, explicitly drive auxiliary~rst_nand default unused inputs0; reject missing reset or empty input bindings. New covering guard plus70prior focused casesPASS (71total). Corrected all40native primary local1strictPASS; all43scalar inputs driven and8736configuration Qstates defined. Snapshot SHA unchanged across reset-adapter fix. Hosted corrected replay pending; earlier primary evidence remains limited to its recorded adapter.
