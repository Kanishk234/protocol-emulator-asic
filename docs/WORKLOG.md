# Worklog

Newest entry at the top. One entry per session: what was done, boxes ticked (with evidence), next step.

## 2026-09-29 (session 24: remove the orphan lane in a scratch candidate)
**Done:**
- Confirmed `clock_protected.csv` is a PIP removal list, not a retained-PIP list. The two `J2END_GH_BEG3` inputs, `N2END1` and `E1END3`, remain legal candidate arcs; my initial interpretation was backwards and is discarded.
- Traced the missing fanout: the candidate removes both outgoing PIPs from `J2END_GH_END3` to `LG_I3` and `LH_I3`. With no surviving sink in the hardened tile, synthesis removes the `J2END_GH_BEG3` mux and its `N2END[1]`/`E1END[3]` inputs. The two failed rows are retained source arcs on an orphaned path, not a signal that the placement flow dropped a live workload path.
- Confirmed none of the preserved UART, SPI-controller, or I2C-controller routes selects these edges. Removing only the two source arcs fails FABulous's unconnected-output check because the four-lane `J2END_GH` jump is still declared. A separate ignored scratch variant narrows that jump to three lanes in a LUT-only Base definition, regenerates the tile at 529 bits (from 530), and regenerates the 5 × 3 CAD/bitstream model.
- Reran nextpnr on the new model for UART, SPI-controller, and I2C-controller. All three routed normally; each FASM compiled to 842 words. The routes changed, as expected from a changed routing graph. Simulated the UART bitstream through `wp_fabric_cfg` and the generated fabric RTL: TX emitted `0x96` LSB-first with correct start and stop bits.
- Started the matching CMOS5L tile flow. Yosys synthesis passed with 1,619 cells and 29,836.6 µm² estimated area, close to the 530-bit reference's 1,580 cells and 29,820.5 µm². Physical optimization did not complete: FABulous's OpenROAD Python hook failed to import `librelane` in the Nix OpenROAD Python environment. This is a runner environment failure, not evidence that the tile does or does not fit; no physical signoff is claimed.
- No architecture, RTL, or timing files were changed. Scratch artifacts remain under ignored `build/`; the tracked pruning manifest and shared tile definitions remain unchanged.
- No architecture, RTL, or timing files were changed. The previous measured delay distribution remains partial LUT-tile characterization; no candidate Fmax claim is valid.
**Boxes ticked:** root cause found for the two absent timing arcs; three rerouted workloads and bitstream generation passed; UART configured-fabric RTL check passed. No new timing coverage or physical signoff claimed.
**Next:** repair the OpenROAD Python environment so the scratch 529-bit tile can finish the same CMOS5L hardening flow, then establish whether the reduced switch matrix is physically beneficial. Afterward characterize inter-tile wires, remaining tile classes, and BEL arcs before regenerating candidate timing files or enabling Fmax.

## 2026-09-28 (session 23: characterize candidate LUT switch delays)
**Done:**
- The first probe accidentally paired an older 375-bit aggressive tile snapshot with the clock-protected candidate and was discarded. Re-ran against the 378-bit clock-protected `RUN_2026-09-28_20-53-31` final RTL, netlist and SPEF; the switch-matrix RTL SHA256 matches both the current tile source and candidate macro copy. A temporary `/tmp` adapter was needed for this installed FABulous/Yosys combination; no active timing or design files were changed.
- Measured 862 of 864 internal LUT-tile PIPs. Two arcs into `J2END_GH_BEG3` failed because `N2END[1]` is absent from the physical timing graph. Delays ranged 0.001–6.089 ns (median 0.766 ns; p95 2.597 ns). Raw rows are in ignored `build/arch_explore/route_prune/timing/lut4x8_clock_protected_slow_delays.csv`.
- The model returned all 202 external LUT-tile PIPs, but 198 are FABulous's fixed 0.001 ns stitched-wire assumption; only four global-buffer twists use extracted tile delays (0.085–0.091 ns). This does not characterize physical inter-tile wires.
- This only characterizes candidate LUT-tile internal switches. It does not time external routing, the other tile classes, or all BEL arcs; no candidate PIPs file was replaced and no Fmax claim is valid yet.
**Boxes ticked:** partial physical characterization of candidate LUT-tile internal PIPs; timing-model integration remains incomplete.
**Next:** resolve the two missing graph arcs; replace the stitched-wire assumption with measured inter-tile delays; characterize remaining tile classes and validate BEL timing; then regenerate candidate timing files and rerun design-set routes. Keep G1 frozen and candidate Fmax disabled until full coverage is validated.

## 2026-09-28 (session 22: exercise candidate design-set workloads)
**Done:**
- Compiled the design-set `hostecho` example on the consistent clock-protected 5 × 3 candidate (23/112 LCs; 842-word WBIT). Its Fmax field is based on placeholder PIP delays and is not a timing result.
- Through the scratch seven-column shell and host SPI protocol, all candidate workload checks passed: UART 8N1 TX of 0x96; SPI controller mode 0 against the reference target (three bytes); I2C controller against the open-drain reference target (write/read/NACK); and hostecho CH_WRITE/CH_READ, USER_STATUS, attention/IRQ, and USER_RESET.
- I2C first exposed a scratch wrapper bug: its per-pin inout outputs were not reduced into the shell's `io_en` vector. Connecting those vectors cleared the unknown outputs and the complete I2C test passed.
- All testbenches, generated shell, WBITs, and results remain under ignored `build/`. No active architecture/shell RTL or held-out design was touched.
**Boxes ticked:** three required design-set protocol smoke/regression paths plus generic host-channel behavior on candidate RTL shell. Not physical signoff.
**Next:** characterize candidate route delays from physical tile/fabric data; measure full 5 × 3 fabric and shell congestion/area; test additional SPI modes and I2C target capacity if feasible; preserve G1 as fallback until those gates pass.

## 2026-09-28 (session 21: validate candidate shell integration)
**Done:**
- Generated an ignored scratch seven-column shell wrapper from the candidate pin map, using the repository's `wp_shell`, synchronizers and frame loader plus the regenerated 5 × 3 macro RTL. The active `src/tt_um_warp.v` remains untouched.
- The first wrapper left the candidate macro's `FrameData`/`FrameStrobe` ports unconnected; this caused unconfigured X outputs. Connected both buses and loaded the candidate UART WBIT over the actual host SPI interface.
- Host SPI load reached LOADED, RUN succeeded, CH_WRITE accepted 0x96, and FAB_OUT0 emitted one valid 8N1 0x96 frame. Start/data/stop checks passed. The unused `h_attention` output was tied low for this UART-only run.
- Scratch wrapper, test, and simulator outputs stay under ignored `build/`; G1, active shell, and held-out set remain unchanged.
**Boxes ticked:** candidate UART test through scratch shell SPI/configuration/run path. This is RTL simulation only, not physical integration.
**Next:** automate candidate wrapper generation and add candidate passthrough/host-channel coverage; check the I/O map for all shell roles; calibrate PIP delays before timing claims; then evaluate full macro/shell physical feasibility and congestion.

## 2026-09-28 (session 20: confirm candidate UART simulation)
**Done:**
- Traced the earlier 0x96 payload mismatch to the scratch testbench: it subscribed to `negedge tx` after the valid/ready handshake, so it could miss the start edge and sample later bits at the wrong phase. The primitive shift register had loaded 0x96 and was emitting the correct LSB-first sequence.
- Re-armed the edge observer before asserting `h_wvalid` and added explicit assertions for start, all eight data bits, and stop. The candidate UART bitstream passed after configuration through `wp_fabric_cfg` into the regenerated 5 × 3 macro RTL.
- Together with session 19's passthrough test, confirms a dynamic fabric I/O/LUT path and one primitive-based protocol workload on the candidate. This remains direct macro-level RTL simulation, not shell/top-level integration or physical signoff.
- All harnesses and outputs remain ignored scratch artifacts under `build/`; G1 and the held-out set remain untouched.
**Boxes ticked:** UART direct macro RTL load-and-transmit simulation.
**Next:** see session 21 for scratch shell integration evidence; check the full candidate I/O map and physical feasibility before advancing.

## 2026-09-28 (session 19: validate candidate fabric logic path)
**Done:**
- Compiled a scratch combinational passthrough (`FAB_IN0` → `FAB_OUT0`) on the consistent clock-protected 5 × 3 candidate; routing and bitgen succeeded (842 words).
- Loaded that exact WBIT through `wp_fabric_cfg` into the generated candidate macro RTL. The routed output followed input values 0 → 1 → 0 after configuration. This confirms a basic candidate config/LUT/I/O path in simulation; it does not explain or clear the UART payload mismatch.
- Scratch design and testbench remain under ignored `build/`; active G1, shell, and held-out set unchanged.
**Boxes ticked:** first candidate dynamic logic-path proof; UART/primitive behavior and shell integration remain open.
**Next:** inspect the UART compile mapping and candidate primitive/control pins, then isolate the wrong payload bits with targeted probes. After that build a scratch seven-column shell/config integration; no timing claims until candidate PIP delays are calibrated.

## 2026-09-28 (session 18: audit candidate tile/model consistency)
**Done:**
- While preparing RTL bitstream-load simulation, found the reduced candidate artifacts do not share one tile definition: the current clock-protected tile RTL has 530 configuration bits, its separate software-generation tile copy has 527, and the generated scratch macro RTL still has 566.
- Replaced the ignored software-generation tile artifacts from the exact hardened tile, regenerated the FABulous model and feature map, and copied the matching tile RTL into the scratch macro. The candidate RTL declares 530 bits and its config map spans 0–529.
- Recompiled UART, SPI-controller and I2C-controller on the consistent protected 5 × 3 model. All route and bitgen; each 842-word bitstream independently matches FASM-to-word regeneration and the five-row frame check. The 4 × 3 and aggressive 5 × 3 routeability claims remain unverified. Candidate timing PIPs still have placeholder delays; ignore Fmax.
- Started a direct RTL load-and-transmit simulation against the regenerated macro. The first harness released reset too early; after holding user reset through configuration it reached host-ready and emitted the UART start bit, but the transmitted byte failed its data-bit check. Functional operation is not demonstrated. The full shell also needs seven frame columns and a new pin integration; the frozen shell supports six.
- No active architecture, macro, or shell files changed; G1 and held-out set remain untouched.
**Boxes ticked:** consistent protected candidate model and software route/bitgen checks only; no dynamic-functional or physical integration gate advanced.
**Next:** debug the direct configuration simulation, then build a scratch shell with the seven-column decoder and candidate pin map. Generate candidate-specific realistic PIP delays before making timing claims or attempting full-fabric hardening.

## 2026-09-28 (session 17: validate clock-protected switch pruning)
**Done:**
- Corrected the session 15 routing claim: its identical-FASM check used a stale nominal-corner PIPs file, so it did not prove routing through the pruned graph.
- Initially reported regenerated candidate full-fabric models, protocol routes and frame checks. Session 18 found stale tile copies, then rebuilt and revalidated the protected 5 × 3 model from the exact hardened tile; see session 18 for current evidence.
- Re-hardened the clock-protected tile at 190.40 × 199.08 µm. It synthesizes to 29,820.5 µm² / 1,580 cells, places at 88.8% utilization, completes the pinned tile flow, and has a clear KLayout DRC result. The aggressive candidate was 29,824.2 µm² / 1,595 cells at the same utilization.
**Boxes ticked:** tile-only PPA/DRC screen; no architecture-level gate advanced.
**Next:** see session 18 for corrected current status.

## 2026-09-28 (session 16: make pruning screen reproducible)
**Done:**
- Added `spikes/route_prune/removed_pips.csv` as the exact 313-choice manifest for the measured route-pruning candidate, plus a scratch-only script that applies it to every FABULOUS_LC tile and rejects removal of any selected FASM choice at those sites.
- Reproduced the ignored candidate `.FABulous/pips.txt` byte-for-byte (3,443 internal PIPs removed across 11 LUT tiles). The preserved UART, SPI-controller and I2C-controller routes remain unchanged; this is manifest replay, not a general-purpose topology optimizer.
- Updated the architecture research report with the reproducibility path and the current limits. G1 stays frozen; the held-out protocols were not used.
**Boxes ticked:** none; the physical benefit is promising, but a full-fabric feature map, router and shell flow have not been regenerated for this architecture.
**Next:** develop broader non-held-out route coverage and complete the tile-to-fabric configuration/compiler round trip before deciding whether to pursue this as the new 5 × 3 baseline.

## 2026-09-28 (session 15: physically measure route-option pruning)
**Done:**
- Kept G1 frozen and all edits inside ignored `build/` scratch copies while testing a fabric-native switch-matrix reduction.
- Removed 313 of 1,272 local switch options per LUT tile (24.6%) based on routes present in the current UART, SPI-controller and I2C-controller design set. The initial compiler run appeared to produce byte-identical FASM, but it used stale nominal-corner PIPs and was invalid as route-preservation evidence; see session 17 correction.
- Regenerated the LUT tile's scratch configuration-memory map after removing stale generated mapping data. At the 190.40 × 199.08 µm fifth-column target, synthesis area fell 14.4% (34,831.7 → 29,824.2 µm²; 1,825 → 1,595 cells). The pruned tile completed placement at 88.8% utilization and the tile flow through KLayout DRC; the unpruned tile failed placement at 106.507%.
- Tried the remaining I2C-target design-set workload in both candidate and baseline architectures. It exceeds the current 88-LC logic capacity in both, so it cannot establish a routing regression or win.
- Recorded run paths, metrics and limits in `docs/reports/architecture_research.md`. No held-out protocols were inspected, no G1 architecture or macro changed, and the reduced tile's complete bitstream/configuration integration remains unvalidated.
**Boxes ticked:** none; this is a promising scratch experiment, not a complete architecture candidate. Known-workload route preservation does not establish general routability.
**Next:** make the pruning procedure reproducible, expand preservation evidence with generated non-held-out designs and a compiler/configuration-map round trip, then test full-fabric routeability at equal clock/area. Do not merge pruning into G1 or declare the fifth column feasible until the real tile map, compiler, full fabric and shell hardening agree.

## 2026-09-28 (session 13: test fifth-column tile dimensions)
**Done:**
- Checked the current phase 3 gate and retained G1 as the frozen baseline; successor work remains exploration and no active `arch/`, `macro/`, or shell hardware was modified.
- Retried the current LUT4 tile hardening in an ignored build copy at the proposed fifth-column dimensions, 190.40 × 199.08 µm. The pinned CMOS5L flow generated the tile and reached OpenROAD global placement, then stopped with `GPL-0301`: reported utilization was 106.507%, above 100%. This rejects the unchanged tile at that geometry before detailed routing; no DRC, timing, or GDS result exists.
- Recorded the negative feasibility result and reproduction details in `docs/reports/architecture_research.md`. The result makes physical configuration-cell/pin remapping the next high-value experiment; it does not establish that remapping will recover enough area.
- Attempted to query recent `efpga` CI with `gh run list`; the environment could not connect to `api.github.com`, so current remote CI status could not be refreshed. The last recorded pushed-baseline CI remains the all-green set in session 12.
**Boxes ticked:** none; this scratch tile did not pass placement, and no phase gate was advanced.
**Next:** inspect the generated tile/configuration and placement reports, then test bounded config-cell/pin mapping changes in the ignored build copy. Require the tile to complete place-and-route with meaningful margin before attempting 5 × 3 fabric generation. Keep G1 unchanged.

## 2026-09-28 (session 14: inspect tile fit and event-tile integration limits)
**Done:**
- Read the current run's placement report rather than inferring from the headline utilization: 35,943.264 µm² movable cell area + 1,160.105 µm² pin-density adjustment over 34,836.480 µm² core. Eliminating pin-density overhead alone would still leave cell area 3.18% over capacity; with current overhead the footprint needs at least 6.11% recovery to pass 100% utilization, before routing margin.
- Checked FABulous 2.2's documented custom-tile generator limit: 32 internal inputs and 8 internal outputs. The proposed event tile's 29 inputs fit, but its 32 outputs do not fit that stock generation path. A bespoke matrix and matching compiler/bitstream support would be needed; no such integration was built.
- Updated `docs/reports/architecture_research.md` with the exact physical evidence and event-tile tool constraint. No active hardware changed.
**Boxes ticked:** none; the tile still fails global placement, and the event-tile path is not compiler-ready.
**Next:** prioritize reducing LUT-tile cell footprint (especially switch/configuration logic) while keeping routing checks and bitstream semantics; do not expect pin-order changes alone to make the fifth-column target fit. Reassess the event-lane option only after a generated tile can be compiled and configured by the real flow.

---

## 2026-09-28 (session 12: test a fabric-coupled event-lane direction)
**Done:**
- Deepened the closest prior-art check. PRISM's published IHP design already describes two independent 16-state shards, loaded from Verilog state tables, with shifters, counters, FIFOs, CRC, edge capture/sampling, debug and optional trace. Updated `docs/notes/prior_art.md` and the research ranking: lane count, shared code, CRC and capture are not WARP differentiators by themselves.
- Extended `spikes/event_lanes/` with per-lane ready/valid byte channels and `TX_SHIFT`. Added `warp_byte_bridge.v`, a one-byte elastic buffer with a configurable XOR transform, and a concurrent receive-transform-transmit test. All three lane/bridge testbenches pass; Verilator lint is clean.
- Compiled the user bridge through WARP's existing G1 flow: 17/88 LUT4s, 18/36 IOBUFs, 722 words, nextpnr estimated Fmax 212.77 MHz at `nom_slow_1p08V_125C`. This validates the user-logic block independently, not an integrated eFPGA/event-macro data path.
- Re-ran the area screens with channel state included: 8-word writable image 33,451 µm²; 8-word static image plus estimated configuration latches 26,157 µm²; 16-word writable image 51,272 µm²; 16-word static image plus latches 37,387 µm². These remain SG13G2 screening estimates, not CMOS5L routed results.
- Updated `docs/reports/architecture_screen.md`, `docs/reports/architecture_research.md`, and the successor exploration to emphasize the required proof: user Verilog must process bytes between independent pin-timing lanes through the actual fabric.
**Boxes ticked:** none; the ready/valid bridge compiles as a separate G1 user design, while the event-lane/fabric composition and physical tile remain unimplemented.
**Next:** make the static instruction image part of a generated FABulous configuration map, route the ready/valid interface through the real fabric, then load both together and run the transform test end-to-end. Keep the physical tile-remapping experiment as the higher-confidence path to more general eFPGA capacity; select neither candidate without equal-area physical evidence.

---

## 2026-09-28 (session 11: prototype shared-image event lanes)
**Done:**
- Kept G1 frozen and prototyped the first successor block under `spikes/event_lanes/`: two independent protocol-neutral event lanes with per-lane timing/state and a shared instruction image.
- Wrote the instruction/cycle contract before implementing RTL. Added masked drive/release, pin waits, 16-bit delays, sample, conditional branch, jump, halt, and generic shift-in/shift-out operations. Both lanes keep separate output requests and observe the sampled pin inputs; no pad arbitration is inferred.
- Implemented two storage policies: writable program RAM with a write lock while either lane runs, and a static-image wrapper intended to use the fabric's configuration latches.
- Added pin-level testbenches for each policy. `spikes/event_lanes/run.sh` passes both concurrency tests and warning-clean Verilator lint; Yosys mapped the RAM and static variants at 8 and 16 words using the SG13G2 typical Liberty.
- Area screen (`docs/reports/architecture_screen.md`): 8-word runtime RAM 33,067 µm²; 8-word static image including 192 estimated config latches 25,849 µm²; 16-word RAM 50,263 µm²; 16-word static image including 384 estimated config latches 36,411 µm². Cross-library comparisons to a CMOS5L tile are explicitly approximate. Static configuration saves ~22% at 8 words but has no bitstream compiler or fabric integration yet.
- Updated `docs/design/ARCHITECTURE_EXPLORATION.md`; no `arch/`, `macro/`, shell RTL or active hardware changed.
**Boxes ticked:** none; this is a tested, synthesized candidate spike, not a routed tile or successor selection.
**Next:** map static instruction bits into a generated FABulous config interface; then add a bounded generic data/event channel between the lanes and LUT fabric and prove a concurrent lane-plus-transform workload. Compare against the same workload on G1 before changing the active architecture. Do not tune against the previously opened held-out protocols.

---

## 2026-09-28 (session 10: reopen architecture exploration)
**Done:**
- Read the new `WARP_Branch_Review_and_Competitor_Recommendations.md` with the current fabric definition, profiling, G0/G1 results, physical constraints and decisions. Confirmed the user's revised objective: improve the programmable fabric for broad communication workloads while keeping hardware primitives protocol-agnostic.
- Reopened phase 3 exploration under D-037. G1 remains the baseline and frozen fallback; no RTL, architecture, macro or pinout hardware changed.
- Wrote `docs/design/ARCHITECTURE_EXPLORATION.md`: candidates include a denser LUT fabric, a hybrid LUT fabric with generic independently paced sequencers, and a small sequencer control architecture; defines equal-area metrics, workload coverage, a fresh sealed holdout, and gates through physical hardening.
- Measured the generated G1 configuration structure: 4,940/6,656 configuration bits (74.2%) are switch-matrix choices, a concrete target for routability-preserving pruning. Added the caveat that bit counts do not predict area savings.
- Synthesized a temporary two-lane generic event sequencer in ignored `build/arch_explore/`, then consolidated host programming onto one shared address/data bus: 16 × 24-bit instructions per lane maps to 73,589 µm²; 8 instructions per lane maps to 42,553 µm² in SG13G2 typical Liberty. That is about 2.04 vs. 1.18 G1 LUT-tile standard-cell area equivalents, before routing and integration. Logged the assumptions and limitations in `docs/reports/architecture_screen.md`.
- Extended the probe with a shared writable instruction image and independent fetch ports. The two-lane model maps to 47,992 µm² for 16 words and 30,054 µm² for 8 words, about 35% and 29% smaller than private memories. This supports sharing code across replicated endpoints, though the toy engine's timing semantics are incomplete and its cost is not a candidate-core estimate.
- Deeper online research found FABulous-specific physical optimization: a peer-reviewed tile study reports 21.7% area reduction from configuration-cell and interface-pin remapping on SkyWater 130 nm/Innovus. WARP uses IHP CMOS5L/OpenROAD, so the result must be remeasured. Geometry analysis found that 190.4 × 199.08 µm tiles could make a 5 × 3 grid fit with the model's 200 µm shell reserve, enabling 112 LUT4s with one primitive tile (vs. 88 today). This is an ambitious physical target with little utilization slack, not a fit result.
- Confirmed the installed FABulous 2.2.0 package has a tile-area optimization flow and configurable pin placer; WARP's current Nix tile runner fixes tile sizes and its generated G1 feature-to-frame map is linear. Searched the pinned Nix plugin source: it has no optimizer or FABulous pin-placement step, and its LibreLane/OpenROAD/Yosys versions differ from the installed FABulous package. A direct switch to the newer flow is therefore unverified. The report now records a single-tile scratch backport or fixed-geometry sweep as the next physical gate.
- Reviewed current competition entries more closely. Tempo documents a tested two-engine build with capture and timing features; Abagel's similar CPU-plus-lane concept is currently a proposal with estimated block costs. This means WARP's differentiator needs to be the spatial eFPGA coordinating user-defined parallel monitor/transform logic with timed I/O, not lane count or timestamping alone. Research and evidence boundaries: `docs/reports/architecture_research.md`.
- Researched FABulous/OpenFPGA architecture flexibility and the case for custom mux/configuration cells; reviewed public sequencer-based competitor descriptions as self-reported claims. Sources and their implications are linked in the architecture screen report.
- Corrected `tools/areamodel/model.py`: it still used the phase 1 1.07× primitive-tile estimate even though D-026 measured 0.97× LUT-tile standard-cell area. The model now uses the hardened values (35,094 vs. 36,047 µm²) and states that both tiles occupy the same footprint; `capacity.md` labels its earlier estimate historical.
- Reviewed current competing architecture descriptions: Tempo documents two independently paced engines plus capture; GP_PAE documents multiple sequencer lanes and concurrency. These are self-reported public project descriptions, not independently rerun results. Competition brief states uniqueness/general reprogrammability are goals and 6x4 is the current maximum while 8x4 remains a possibility.
- CI on `ee259cb`: docs 36491754412, formal 36491754401, unit 36491754404, lint 36491754317, test 36491754349, fabric 36491754296, and GDS 36491754364 all passed. The GDS run includes successful hardening, TinyTapeout precheck, viewer, and gate-level `gl_test` (completed 23:16:39 UTC). The pushed G1 baseline is fully green.
**Boxes ticked:** none for the reopened architecture exploration; the first low-cost synthesis screen is not a routed or physically hardened candidate.
**Next:** test whether the FABulous generation/hardening flow can safely optimize tile config-cell placement and interface pin placement in a scratch copy, then harden a 190.4 × 199.08 µm tile. This determines whether the fifth fabric column is feasible before spending time on a larger event engine. Also formalize shared-code engine timing, then seal a new holdout before tuning any successor. Keep G1 unchanged until a successor clears the gates.

---

## 2026-09-28 (session 9: close phase 4 CI; phase 5 reproduction and shell verification)
**Done:**
- CI from the Phase 4 push completed green: `gds`/precheck/`gl_test` 36451108163; `fabric` 36451328356 (including co-simulation); `unit` 36451328364, `lint` 36451328384, `test` 36451328368, `docs` 36451328775. No committed hardware files changed since `hw-freeze` (`git diff --name-only hw-freeze..14e7063 -- src arch macro info.yaml` empty). Phase 4 checklist and summary finalized; Phase 4 complete.
- F3 FIFO formal proof passes locally at depths 2 and 4 (`scripts/formal.sh f3_fifo.sby`, `abc pdr`). Independent shell transaction model plus pyuvm environment passes seed 1 locally: 2,288 transactions, 2,851 response bytes, 228 configuration words, 137 design-side bytes, no mismatches, 79/79 coverage bins. Pinned pyuvm and added the checks to `unit` CI and `scripts/check_all.sh`. The mutation report now records 11/11 killed locally.
- Filled Phase 4 CI IDs into `docs/CLAIMS.md` and `docs/EVIDENCE.md`; completed the user guide, prior-art comparison, README and Tiny Tapeout datasheet draft. `docs/summaries/PHASE5.md` is in progress.
- Clean source export of 14e7063 plus the proposed README and Phase 5 sources in `/tmp/warp-repro.vVyH1n`, fresh Python 3.12 venv: `scripts/check_all.sh` passed (377 pytest, all default protocol RTL tests, 30 idle-fabric chip tests, 2 primitive tests, pyuvm 2,288 transactions/79 bins); all 11 committed bitstreams rebuilt identically; UART compiled; UART co-simulation passed; fabric RTL chip suite passed 30/30 including the showcase. Found two README gaps (non-executable fetch script; Python 3.12 required) and BUGS #20 (stale idle-fabric simulator reused for the real fabric); fixed instructions and separated simulator build paths. This is a clean source export and venv on the same development machine, not a separate clean machine/container.
**Boxes ticked:** Phase 4 exit checklist (CI IDs above); Phase 5 claims audit and user-guide/datasheet items (`docs/design/phases/PHASE5_EVIDENCE_DOCS.md`).
**Next:** repeat reproduction in a clean container; finish the evidence report's local-measurement run-ID audit; get CI on the uncommitted Phase 5 changes before closing Phase 5.

---

## 2026-09-27 (session 8: G0 chip green in CI; G1 primitives usable; UART, SPI, I2C controller fit G1)
**Done:**
- **G0 chip in CI, all green** (e5b1f98): `gds` + precheck + `gl_test` 17/17 in 36353540402 (45.8 min; setup +10.63 ns, hold +0.121 ns, DRC/LVS/antenna 0, IR drop 0.77 mV); lint, unit, test, docs, formal, fabric green. D-025 evidence and the hardening table updated.
- **G1 hard primitives** (D-026): `wp_timer`, `wp_shift` (`arch/prims/`), proven equal to a spec model (F4, `formal/f4_prims.sby`, k-induction), white-box tested against `tools/refmodels/prims.py`; primitive tile `PRIM2T2S` hardened at 0.97 × a LUT tile; G1 fabric stitched (`macro/warp_g1`, same size and ports as G0, KLayout DRC 0, antenna 0).
- **Compile flow support:** `WP_TIMER`/`WP_SHIFT` wrappers and BEL cell library (`tools/compile/prims/`), mapped, placed and configured (`examples/prims2`: RELOAD and LEN bits in the FASM, accepted by bitgen). `compile.protocols` takes `--arch`, `--only`, `--set`.
- **BUGS #15:** placement failed with free LCs because each LUT tile has one clock enable and one set/reset; the flow now turns enables/resets used by < 4 flip-flops into logic (`dfflegalize -mince/-minsrst`). Every design got smaller.
- **Protocols on the primitives** (`PRIMS=1`; plain form kept): UART, SPI controller, I2C controller rewritten; all RTL tests pass in both forms (UART DIV 16/13/5 + sigrok, SPI 4 modes × 2 speeds, I2C Q 2/4/5). I2C controller also lost its own synchronizers (ARCHITECTURE §6) and three wait states. Unit CI runs the `PRIMS=1` configurations.
- **Results:** G1 places UART 29, SPI 47, I2C controller 70 of 88 LCs (69–124 MHz slow corner); G0 places only SPI (86/96). `docs/reports/g1_results.md`, `g0_results.md` rewritten.
**Boxes ticked:** full 6x4 hardening of shell + G0 (CI 36353540402); protocols compiled onto G0 (`g0_results.md`).
**Later the same session:**
- CI on b438814: `fabric` failed: the committed test bitstreams predate the BUGS #15 flow change, and `prims2` needs G1 (fixed by the G1 switch, which rebuilds them). The `gds` run it started re-hardens the unchanged G0 (arch/prims touched `arch/**`).
- **G1 into the chip (D-027):** `arch/CURRENT` = warp_g1, ARCH_VERSION 0x0003 (shell, host software), `src/warp_g1.v` black box, `config.json` macro files, test stub and settle files regenerated, RTL fabric model includes `arch/prims`. New chip tests `test_prims` (both block types configured by a real bitstream) and `test_uart` (the design-set UART on the primitives through the host interface; test bitstream `uart16`). Local: RTL suite **19/19**, stub 13 + 6 skipped, F1 PASS (k-induction), pytest 63, lint clean.
- **I2C target** rewritten (hard shift register for the bus byte, shared register ports, no own synchronizers): 6/6 tests in both forms at Q 4/6/11; 205 → 184 LCs (G0), 169 (G1); does not fit either, even with 2 registers (123 on G1) — generic Yosys LUT4 mapping agrees, so it is the design's size: phase 3 (register-file tile or larger fabric).
- BUGS #16 (`sda_o` undriven after the rewrite, found by lint): `lint` now checks all protocol designs in both forms.
- G1 pre-flight: overflow 20, stripes OK, 21 detailed-routing violations all on `clk` at the strip above the fabric (G1 LEF identical to G0's; D-027 records it and the fallback). Pushed as d6f5dcd; CI hardening queued behind the G0 re-run.
- **Protocol chip tests:** `test_spi_ctrl` and `test_i2c_ctrl` (reference target models on the pins, open-drain bus for I2C) through the host interface, bitstreams `spi8`, `i2c8`; pass on the fabric RTL. `compile.protocols --require`; the `fabric` workflow compiles every protocol and fails if UART, SPI or I2C controller stops fitting.
- CI on d6f5dcd (G1 in the chip): lint, unit, test, docs, formal, fabric green; gds (G1 hardening) running.
- **BUGS #17 / D-028:** nextpnr left every path through the hard primitives untimed, so the G1 Fmax figures were optimistic. Primitive arcs from OpenSTA (`tools/timing/`, slow corner, ×1.5 margin) into `placement_estimate.txt`; the compile flow now uses nextpnr 0.11.1 (OSS CAD Suite 2026-09-27, `scripts/fetch_nextpnr.sh`), which reads them (identical FASM to 0.10-82 without them). Timed: UART 93–95 MHz, SPI 83.2, I2C controller 58.0, all above 50 MHz. Test bitstreams rebuilt; RTL suite **21/21**; pytest 69.
- **G1 chip green in CI** (36367067731 on d6f5dcd): gds 43.6 min, precheck pass, gl_test **19/19** (incl. `test_prims`, `test_uart`), routing DRC/LVS/antenna 0, setup +10.73 ns, hold +0.143 ns. D-026 and D-027 Accepted; D-029 (G1 is a valid fallback); `docs/reports/formal.md`; `docs/summaries/PHASE2.md` (in progress).
**Boxes ticked:** exit items: shell + G1 hardened, gl_test with real bitstreams, g0_results for every protocol, formal summary, fabric workflow green, decision point.
- **Timing cross-check** (`tools/timing/tile_check.sh`): STA of the hardened `PRIM2T2S` tile against the model. Clock-to-out bounded (6.79 vs 15.17 ns); the timer's in-tile setup (4.0 ns, a NOR with 33 loads) exceeded the standalone arc ×1.5, so setup/combinational margins are now ×3.0 (input side 8.06 vs 12.06 ns). Timed estimates: UART 90.7, SPI 78.0, I2C controller 53.0 MHz. Timing-model box ticked (documented conservative model).
- CI on fe4cac8: `fabric` failed with exit 126: `scripts/fetch_nextpnr.sh` committed without the executable bit (created from Windows); the workflow now runs it with `bash`, and the three new scripts get `git update-index --chmod=+x`. gds (21-test gl_test) running.
- CI gds on fe4cac8 (36372341186): gl_test **21/21** incl. `test_spi_ctrl`, `test_i2c_ctrl` on the hardened chip; pin-level protocol tests box ticked.
**Next (superseded):** push the margin fix + fabric fix + rebuilt bitstreams; all CI green closes phase 2 (then PHASE2.md final).
- **Phase 2 complete (2026-09-28):** all CI green at 2befd16 (gds/precheck/gl_test 21/21 36376994834); exit boxes ticked; `docs/summaries/PHASE2.md` final.
- TT linter warnings reviewed: `PINMISSING` VPWR/VGND on the macro (TT's black box has power pins; power via PDN_MACRO_CONNECTIONS, LVS 0: harmless), `WIDTHTRUNC` on Frame_Data_Reg's Row (32-bit genvar expression into a 5-bit parameter; values fit), `SYNCASYNCNET` on rst_n: BUGS #18.
- BUGS #18 fixed locally: reset synchronizer (+ separate config-path reset flop); full-top lint without waivers clean of SYNCASYNCNET/WIDTHTRUNC; suites 21/21 (RTL) and 13+8 skipped (stub); F1 PASS.
- Pre-flight of the fix: overflow 37, stripes 22/22, 36 detailed-routing violations, all on `clk` where it reaches the fabric's clock pin on the macro's west face (y ≈ 640 µm) and the local router cuts onto the macro's Metal4 blockage. Same net and area as the 21 of the G1 switch, which CI (LibreLane 3.1) routed with 0 violations three times on this floorplan: a local-vs-CI router difference for this net; CI decides. Fallback if CI fails there: room for the clock pin (macro one row lower or a keep-out west of the pin) as its own hardening.
**Phase 3 started (2026-09-28):**
- `tools/profiling/limits.py` + `docs/reports/g1_limits.md`: on G1 the counters/shifting are absorbed; control logic is what is left; control sets (3–7) and primitive count are not limits; every critical path goes through a primitive; the I2C target would not fit even with a register file.
- D-030 candidate 1 (registered terminal count): F4 re-proved, `tc` 2.98 → 0.88 ns at no area cost, but the I2C controller (the worst design) is limited by paths into the timer: 53.0 → 52.1 MHz: not kept alone (parked in build/c1/parked).
- Root of the timer's slow input path: the primitive tile's hardening config (copied from the tile library) disables resizer/repair, so a NOR drives 33 loads unbuffered.
- D-031 candidate 2 (primitive tile with design repair): three local tile runs; repair works only once inserted as a step (the tile driver applied removals only), then detailed placement fails: the 92 %-full tile has no room for buffers. Not feasible; config restored; `tile_check.sh` now picks the newest completed tile run.
- CI on 3047dea (BUGS #18 fix): all green; gds/precheck/gl_test 21/21 (36383587262), setup WS +12.48 ns.
- Organizers' reply (D-032): eFPGA accepted; software side required (flow, loading, UART/SPI/I2C examples); phase 4/5 plans updated.
- `docs/reports/architecture_comparison.md` + chart; D-033 final architecture G1.
- User kept hardware open for the I2C target: D-034 register-file tile measured (169 → 123 LCs, still no fit); user then chose to freeze and drop the I2C target (D-035).
- Phase 3 exit boxes ticked except the tag; `docs/summaries/PHASE3.md` drafted.
- User tagged `hw-freeze` → 3047dea. CI on a578359 all green: **phase 3 complete**; `docs/summaries/PHASE3.md` final.
**Phase 4 started:**
- Demo-board loader `tools/board/warp.py` (MicroPython + CPython): checked load, run control, host channel, FAB_IN pins, ttboard glue; `tools/board/tests` 270 pass (equal to the reference host); `test_board_loader` (the module's own code drives the chip model through cocotb bridge/resume) passes on the fabric RTL. Not tested on hardware.
- **End-to-end examples** (D-032): `compile --set NAME=VALUE`, report records params; `tools/board/examples.py` (UART send/recv, SPI transfer, I2C write/read/probe); `docs/EXAMPLES.md` (pins, commands at 10 MHz, wiring, what is tested); the board code tested against the chip model for all three (`test_board_loader`, `test_board_examples_spi`, `test_board_examples_i2c`). BUGS #19: parked `uo_out` pins assert active-low outputs (SPI CS_N) while stopped; documented, fix at the pin map (bidirectional pin + pull-up). Loader refuses to load while RUNNING with a clear message.
- **Held-out set unsealed and evaluated** (`docs/reports/heldout_results.md`): models first from each spec (`tools/refmodels/{ws2812,onewire,swd,can}.py`, each tested on its own), then designs in both forms:
  - H1 WS2812: fits (32/88 LCs, 54.3 MHz after tying the period timer's enable high; G0 82); chip test `test_ws2812` passes. Needs a host streaming a byte per ~10 µs (no pixel buffer).
  - H2 1-Wire: fits (77/88, 54.5 MHz; G0 126 = no fit) after a restructure with the second timer (116 → 77); chip test `test_onewire` (READ ROM, CRC) passes.
  - H3 SWD: fits (44/88; G0 61) as a bit engine with packets in `tools/board/swd.py`; chip test `test_swd` passes.
  - H4 CAN 2.0A: RTL correct (3/3 vs reference nodes), **does not fit** (207/88; G0 241).
- Showcase replaced (D-036): six protocols switched at run time on one chip (`test_showcase_protocol_switching` passes). Robustness: `test_corrupt_load_over_running_design`, `test_uart_input_phase` pass; mutation campaign `scripts/mutation.py` 8/8 killed (`docs/reports/mutation.md`); co-simulation `test_internal/cosim` (UART source RTL vs its bitstream on the fabric: identical TX waveforms, equal RX) passes. Local: chip suite 27/27, pytest 377, lint 8 protocols × 2 forms clean, bitstreams reproducible. `docs/summaries/PHASE4.md` drafted.
- Pushed (76860b1, 14e7063); CI: unit, lint, docs, test green; gds (76860b1) and fabric running.
**Phase 5 started in parallel** (the user asked; phase 4's only open exit items are its CI runs): `docs/CLAIMS.md` audited (C1–C10), `docs/USER_GUIDE.md`, `docs/EVIDENCE.md` (draft), `docs/reports/prior_art_comparison.md`, README rewritten, `docs/info.md` + `info.yaml` pinout comment for G1; clean-checkout reproduction running.
**Next:** CI results → close phase 4 and fill the pending run IDs; clean reproduction; PHASE5 summary.
**Next (superseded):** after the G1 hardening result, push the protocol chip tests + timing work (touches `test/` and `macro/`, so one more hardening, which also gives gl_test evidence for the 21 tests); then phase 2 exit: timing cross-check, per-tile equivalence plan, PHASE2 summary.

---

## 2026-09-27 (session 7: phase 2 started: shell, compile flow, real bitstreams)
**Done:**
- **Shell** (ARCHITECTURE §2–6): `wp_spi_target`, `wp_shell` (commands, checked loader, run control, 2-entry host channel FIFOs), `wp_crc32` (bit-serial), `wp_fifo`, `wp_sync`; new top-level pinout; FABulous's bit-bang receiver removed. Spec clarifications D-021.
- **Host software** `tools/host/protocol.py` (from the spec): transactions, STATUS decode, CRC, architecture check before loading.
- **Formal:** F1 output isolation proven unbounded (k-induction); F2 bounded (BMC 84) against an independent shadow loader. The F2 cover trace exposed **BUGS #12** (an empty load reached LOADED), now fixed. New `formal` workflow.
- **Compile flow** `tools/compile/` (D-022): pin map → wrapper → Yosys → nextpnr (slow-corner timing) → WARP bitgen → `.wbit` + report. `arch/warp_tiny/` (fabric.csv, pins.csv, arch.yaml). **BUGS #13**: FABulous's bitgen drops the global-clock mux selects; our generator fixes it and matches upstream word for word elsewhere.
- **Real bitstreams on the whole chip:** `test/test_bitstream.py` loads `counter4` and `logic4` over SPI and checks them at the pins, on the fabric RTL (`WARP_FABRIC=rtl`, new job in `fabric`) and on the hardened macro's gate-level netlists (`GATES=yes`, what CI `gl_test` runs). Gate level needed D-023 (settle X routing loops; no reload over a running configuration).
**Boxes ticked:** host interface, loader, run control, IO cells, host software, compile flow, host rejects other architectures, F1, F2, `gl_test` with two real bitstreams. **CI on acc3af3/2faaa36 all green:** `gds` + precheck + `gl_test` 16/16 36342012141 (35.6 min; shell 3,239 cells / 51,066 µm², setup +12.04 ns, hold +0.117 ns, DRC/LVS/antenna 0), `formal` 36342012194, `fabric` 36342012182, `test` 36342480467, `lint` 36342480574, `unit` 36342480768 (after moving it to Python 3.12), `docs` 36342480572.
**Also (uncommitted at session end, local):** design-set synthesis on the real flow (`python -m compile.fit`, `capacity.md`: UART 129, SPI 96, I2C ctrl 154, I2C target 208 LCs vs G0's 96); `N_IO` tile hardened (0 DRC); G0 fabric stitched (`arch/warp_g0`, 1016.64 × 669.06 µm, D-024 proposed); `spikes/fabric_tiny/run.sh` takes `FABRIC=<name>`.
**Not yet:** host data path into the fabric (FIFOs exist, the current fabric has no channel BELs), G0/G1 fabric, 6x4 hardening, timing model documentation, protocols on G0, `gl_test` evidence from CI.
**Later the same session:** the compile flow's wrapper instantiates IO cells explicitly (needed for the host channel; D-022); the new bitstreams exposed zero-delay hangs in the gate-level fabric model, so `gl_test` now simulates the gate-level shell with the fabric RTL, plus hold-X during loads and settle after (D-023 revised); per-tile netlist-vs-RTL equivalence added to the plan. Local: gl_local 16/16, RTL 16/16, pytest 42, bitstreams reproducible.
**G0 into the chip (later the same session, local, uncommitted at the time of writing):** `arch/CURRENT` = warp_g0 (ARCH_VERSION 0x0002); new top level with all 19 pins and the host channel through the fabric (D-024); black box generated from the macro (`scripts/gen_macro_stub.py`); compile flow maps `h_*` by name; examples `idle` and `hostecho`; RTL suite 17/17 incl. `test_host_channel`; F1 re-proved. Placement took six local pre-flight rounds (new `scripts/preflight.sh`): global-routing overflow 9,290 → 23 via east-channel obstruction, per-column frame decode (`wp_frame_select`), placement density 75 %, routing derate 0.15 (D-025); detailed routing 0 violations, power stripes full height. BUGS #14 (compile flow merged carry chains).
**Next:** push G0 and get the CI hardening + precheck + gl_test green; then G1 primitives and the protocols on G0/G1.
**Earlier next:** G0 into the chip: top-level pin and host-channel wiring (D-024), macro placement in `src/config.json` (D-019 rules), local routing pre-flight, then one CI hardening.

---

## 2026-09-27 (session 6: fabric through TT's flow; phase 1 complete)
**Done:**
- Three CI iterations on the chip-level integration, each failure logged: routing stuck because the fabric's pin faces pointed at the die edges (BUGS #9, run cancelled after ~4.8 h); `"//"` keys inside MACROS (BUGS #10); precheck pin check failed on pdngen's short channel stripes beside the fabric (BUGS #11). Adopted the R3 SRAM spike's macro settings (D-019 rev 2: routing-iteration cap, Magic/LVS handling, port-only black box). Added a local pre-flight: TT's merged config through LibreLane (Nix) up to detailed routing + a full-height power-stripe check (~3 min).
- **CI run 36327510268 (dea2150): `gds` 32.5 min, precheck 9/9, `gl_test` pass**; DRC/LVS/antenna 0, timing met at 50 MHz, IR drop 0.38 mV. Recorded in PHYSICAL_DESIGN_AND_CI, `fabric_tiny.md`, CLAIMS (C1–C3), risk register.
- D-020: template `fpga` workflow not applicable with a hard macro.
**Boxes ticked:** tiny fabric hardened with precheck (task + exit), all CI green on `efpga`, `docs/summaries/PHASE1.md` (final). **Phase 1 complete.**
**Next step:** phase 2 (`docs/design/phases/PHASE2_BASELINE_FABRIC.md`), starting with the shell (SPI host interface + checked loader + run control, ARCHITECTURE §2–4) and the formal properties F1/F2 for it.

## 2026-09-26 (session 5: tiny fabric)
**Done:**
- Magic hang root cause found (BUGS #2): the CMOS5L Magic tech file needs Magic >= 8.3.657; the LibreLane 3.0.0 Nix environment has 8.3.623. Workaround everywhere: skip Magic; KLayout writes the GDS and runs the DRC, OpenROAD writes the LEF (`write_abstract_lef`), unused VIA definitions stripped (the FABulous fabric flow misreads them as the tile size).
- All 9 tile types hardened on CMOS5L (0 routing DRC, 0 antenna each); **16-LUT fabric `warp_tiny` stitched: 357 × 484 µm, KLayout DRC 0**, bitstream spec generated (`docs/reports/fabric_tiny.md`).
- Line endings: my Windows-side Python edits had written CRLF into 14 committed files; all converted back to LF (content unchanged, checked with `git diff --ignore-cr-at-eol`). Edits now go through WSL or the Edit tool.
- The first background tile run was stopped by Claude Code for low memory on the Windows side (not a job failure).
**Boxes ticked:** none yet (the tiny-fabric box needs the chip-level integration + precheck).
**Later the same session:**
- D-017: tile power stripes on a global 109.92 µm grid (2.1 µm wide, per-tile-type offsets) so TT's chip stripes can land on the fabric's power columns (lesson from `main`'s R3 SRAM spike). First attempt put the east tiles' ground stripe outside the tile (arithmetic slip); fixed with grid phase 12.00. All 9 tiles and the fabric re-hardened: power pins are full-height columns exactly on the grid; KLayout DRC 0.
- Placement boundary (IHP 189/4) added to the fabric GDS; macro exported to `macro/warp_tiny/` (GDS, LEF, fabric + 9 tile netlists, fabric RTL, bitstream spec).
- Chip-level RTL (D-018): `tt_um_warp` = `warp_tiny` + `wp_fabric_cfg` (FABulous bitbang + ConfigFSM copied unmodified into `src/fabric_gen/`) + run control/parking. `src/lint.vlt` waives lint only for upstream files and the black box. New pin-level tests (parking, config session). `config.json` (D-019): MACROS, PDN_MACRO_CONNECTIONS, `pdn_cfg.tcl` from `main`'s R3 spike, stripe pitch 109.92 / offset 20.64.
- Local: `check_all` PASS, `gl_local` PASS (4/4 on a Yosys netlist), TT `--check-docs` and `--create-user-config` OK.
**Next step:** push; the CI `gds` run (hardening + precheck + gl_test) is the test of the phase 1 tiny-fabric box.
**While CI ran (run 36277723397):** wrote ARCHITECTURE v1 (pins, SPI host commands + status, loading with version/length/CRC, run states + parking, clock/reset, IO cells, G0/G1 resources, primitive sketches, variants, user Verilog rules; OPEN items marked), VERIFICATION v1 (V0–V7, F1–F4 with bounds, coverage goals), PHYSICAL_DESIGN_AND_CI v1 (three-level flow, known limits), risk register in OVERVIEW, in-progress `docs/summaries/PHASE1.md`. `gh` is installed and logged in (user); run logs/artifacts are fetched with it after runs complete. Boxes ticked: the three specs, the risk register, exit item "specs v1 written".

## 2026-09-25 (session 4: phase 1 starts)
**Done:**
- Phase 0 closed (D-012: organizer email waived by the user). CI green on 7405a2e.
- Held-out set sealed at **0171cf7**: WS2812, 1-Wire, SWD, CAN (D-013, `docs/design/HELDOUT.md`).
- Provisional user-design interface (D-014): pins + host byte channels + status; settings as bitstream parameters by default.
- UART: independent model `tools/refmodels/uart.py` (6 pytest incl. hypothesis) written first; then RTL `protocols/uart/` (tx, rx, top); 8 cocotb tests vs the model and sigrok, DIV 16/13/runtime, all pass; Verilator/Icarus lint clean. First profile: 171 LUTs fixed divisor, 262 runtime (budget ~96). BUGS #3 (harness). `unit` workflow added (D-015); `check_all` runs protocol tests.
**Boxes ticked:** phase 1: held-out chosen + sealed (0171cf7), `protocols/uart/`.
**Later:** `protocols/README.md` states that protocol designs are soft user logic, never silicon (user asked; D-002). SPI controller: model `tools/refmodels/spi.py` (7 pytest) then RTL `protocols/spi_ctrl/`; 24/24 cocotb runs (MODE 0–3, HALF 4/5/7) vs model + sigrok; lint clean; 85 LUTs / 42 FFs. BUGS #4 (model skipped a response; spec `HALF >= 4`, not 3). D-014 revised (`h_wlast`). `check_all` PASS.
**Boxes ticked:** `protocols/spi_ctrl/`.
I2C controller: model `tools/refmodels/i2c.py` (bus, target, decoder; 5 pytest incl. stretching) then RTL `protocols/i2c_ctrl/` (command byte stream); 18/18 cocotb runs (Q 4/2/7) vs model + sigrok; lint clean; 164 LUTs / 65 FFs at ~100 kHz. BUGS #5 (hold time, found in review).
**Boxes ticked:** `protocols/i2c_ctrl/`.
I2C target: reference controller model added to `tools/refmodels/i2c.py` (generator; 2 more pytest incl. stretching), then RTL `protocols/i2c_target/` (4-register map, host command access, dirty bits); 18/18 cocotb runs (Q 4/6/11) incl. sigrok; lint clean; 240 LUTs / 79 FFs. BUGS #6 (harness).
**Boxes ticked:** `protocols/i2c_target/`, reference models + RTL tests, sigrok check. All design-set protocol RTL is done.
Profiling: `tools/profiling/workload.py` (renamed from `profile`, BUGS #7) sweeps LUT3/4/6 ± carry and attributes every LUT to the function of the registers it feeds. UART counters resized to the divisor first (fairness; 171 → 144 LUTs). Result (`docs/reports/profiling.md`): of 648 LUT4s, counters 23 %, storage 21 % (mostly the I2C target's register map), shift 17 %, control 17 %, shared 15 %. Ranked: timer/counter, shift register, host channel in the shell, I/O cell sync/registered/open-drain, register file (1 user). Upper bound: UART/SPI/I2C controller fit ~96 LUTs after ranks 1–4; the I2C target does not without a register file.
**Boxes ticked:** profiling script, profiling report, exit item "profiling.md complete".
Area model `tools/areamodel/` (5 pytest) + primitive sketches (`spikes/primitive_area/`: timer ~2,751 µm², shift ~1,538 µm² incl. config bits). Capacity (`docs/reports/capacity.md`): 4 × 3 tiles fit next to a ~273 µm shell column: 96 LUT4, 88 with one primitive tile (2 timers + 2 shifts). UART/SPI/I2C controller fit; I2C target (~220) does not. **D-016: GO specialized eFPGA**; I2C target/showcase open (register file, smaller map, or showcase on the controller).
**Boxes ticked:** area model, capacity estimate, needs vs capacity, go/no-go decision, 2 exit items.
**Next step:** harden a tiny FABulous fabric (stitched tiles) through the flow with live config; then ARCHITECTURE/VERIFICATION/PHYSICAL v1 and the risk register.

## 2026-09-25 (session 3, continued)
**Done:** fetched the CI `GDS_logs` (user download): die 1289.28 × 710.64 µm, 0 DRC/LVS/antenna, timing met, **top level routes only to Metal4** (TopMetal1 is TT power); recorded in `PHYSICAL_DESIGN_AND_CI.md`. `fpga` run 36201219254 green. D-008 accepted (G1 fallback; goal still full specialization). D-011 (`unit` arrives with the first Python tool). `VERSIONS.md` complete. Phase 0 summary written (in progress).
Tile runs 2–3 (`docs/reports/tile_cmos5l.md`): with signals on Metal2–Metal4 the tile routes at the same size (6 iterations, 0 antenna); run 3 skips Magic (BUGS #2 workaround), KLayout GDS written, **KLayout DRC 0 violations (328 rules)**.
**Boxes ticked:** template workflows green (all four), resource usage, `lint`/`unit` workflows (D-011), `VERSIONS.md` complete, phase 0 summary.
**Open in phase 0:** organizer email (parked by the user); all CI green on `efpga` after the push.
**Next step:** push and confirm CI green. Then phase 1 (after the email closes phase 0, or on the user's call): seal the held-out set first.

## 2026-09-25 (session 3)
**Done:**
- Nix 2.35.2 installed by the user; FOSSi cache configured (`/etc/nix/nix.conf`). LibreLane 3.0.0 + FABulous plugin environment builds in 2.5 min (Nix store 6.9 GB). CMOS5L PDK at TT's revision in `~/.cache/warp/pdk-full`. CI LibreLane version recorded (3.1.0.dev3).
- `fabric` CI run 36196784852 green (FABulous demo in CI).
- **First FABulous tile on CMOS5L** (`spikes/tile_cmos5l`, patch D-010): `LUT4x8_ha` routes at the SG13G2 size/density: 40.7K µm² per 8 LUT4s (~5.1K µm² per LUT4), 97 % utilisation, 0 routing and antenna violations. `docs/reports/tile_cmos5l.md`. Capacity at 6x4: ~96 LUT4s with margin (the synthesis estimate was 60–90). D-008 updated; still stands (UART ~215 cells).
- Magic stream-out hung (BUGS #2); stopped by hand, so no GDS/DRC/STA yet.

**Boxes ticked:** none new (tile hardening is phase 1 evidence; `fab_demo` got its CI run ID).

**Next step:** KLayout stream-out + DRC + STA for the tile (BUGS #2). Close phase 0: organizer email (user), `fpga` workflow run (user clicks), `unit` workflow, phase 0 summary. D-008 decision (user).

## 2026-09-25 (session 2, part 3)
**Done:** `fabric` workflow (`.github/workflows/fabric.yaml`) runs `spikes/fab_demo/run.sh` in CI with the pinned tools (Ubuntu Python 3.12, OSS CAD Suite 2026-06-29, cached). PRISM prior-art notes (`docs/notes/prior_art.md`): Verilog → Yosys → bitstream on IHP already exists there, with a fixed datapath close to our hard-block candidates; our claims must rest on the parallel fabric model and the measured method.
**Boxes ticked:** PRISM notes.
**Next step:** push; record the first `fabric` run ID. Waiting on the user: Nix install (tile hardening), D-008, organizer email. The `main` gate is resolved: every "green on `main`" rule (CLAUDE.md, phase checklists) now says `efpga` (user decision, 2026-09-25).

## 2026-09-25 (session 2, continued)
**Done:**
- `gds` 36170807513 on a63877d fully green: hardening 35.1 min, precheck 12.3 min, `gl_test` pass. Recorded in `PHYSICAL_DESIGN_AND_CI.md`. Cell stats and the CI LibreLane version need the `GDS_logs` artifact (login required).
- Tiny FABulous study: `docs/notes/tiny_fabulous.md`. Tiles → fabric → top, three LibreLane runs, submitted via `custom_gds`. Phase 0 decision point answered: D-009 (yes; our plan: fabric macro integrated by the template `gds` job, as TRIPWIRE's R3 did with the SRAM).
- Early capacity estimate: `docs/reports/capacity_early.md`. ~4.5K µm² per LUT4 (stock LUT4AB tile, cmos5l synthesis), so a generic 6x4 fabric holds ~60–90 LUT4s; a scratch UART needs ~215. Proposed D-008 (the fallback becomes G0 + minimal hard primitives).

**Boxes ticked:** template design green on `test`/`gds`/precheck/`gl_test`; hardening time; Tiny FABulous read + written down; phase 0 decision point (D-009).

**Open in phase 0:** PRISM notes; `unit` workflow (waits for the first Python tool); the template `fpga` workflow has never run (manual); `VERSIONS.md` CI LibreLane version; "all CI green on `main`" (`main` is TRIPWIRE: the gate needs retargeting to `efpga` or a separate repo; the user decides); organizer email; phase 0 summary.

**Next step:** the user decides D-008. Then harden one LUT4AB tile on cmos5l with `FABulousTile` (needs OpenROAD/KLayout/Magic: Nix or the LibreLane container) to replace the synthesis estimate with a real one.

## 2026-09-25 (session 2)
**Done:**
- Fixed the `gds` docs check failure (empty title/author/description/pinout, missing `info.md` sections): filled `info.yaml` (WARP, 6x4, 50 MHz, `tt_um_warp`) and `docs/info.md`. Pinout is provisional (D-006).
- Renamed the placeholder top to `tt_um_warp` (`src/tt_um_warp.v`, `test/tb.v`, `test/Makefile`).
- Took the template `gl_test` UDP fix preemptively (BUGS #1).
- Added `scripts/setup_venv.sh`, `check_all.sh`, `gl_local.sh`, `requirements-dev.txt`, the `lint` workflow, and the `gds` paths filter + non-cancelling concurrency.
- Installed OSS CAD Suite 2026-09-25 to `~/oss-cad-suite`; FABulous-FPGA 2.2.0 into `.venv` (pinned). PATH order D-007; versions in `docs/VERSIONS.md`.
- Deleted the duplicate `docs/OVERVIEW.md` (the user did this).

**Boxes ticked (phase 0):** repo/info.yaml (local `--check-docs` pass; CI `docs` 36170807355 green on a63877d), sign-up form (done by Kanishk), docs skeleton, setup_venv, OSS CAD Suite + PATH (D-007), check_all (PASS), gl_local (PASS).

**Later in the session:**
- The user installed `python3-tk` and pushed (a63877d): `test` 36170807382, `lint` 36170807369, `docs` 36170807355 all green; `gds` 36170807513 still running at session end.
- FABulous demo: OSS CAD Suite 2026-09-25 breaks `synth_fabulous`; switched to 2026-06-29, the release FABulous 2.2 pins. `check_all` and `gl_local` re-passed on it.
- `spikes/fab_demo/run.sh`: stock fabric, two bitstreams (stock counter; our `lfsr_down`), each matches its source for 100 cycles, and B mismatches A's source. Report `docs/reports/fab_demo.md`. Ticked: reference fabric, reference design, second design, FABulous pin, and the exit item "two different bitstreams".
- Found: FABulous's wrapper generator only wires its own demo design (see the report); our compile flow needs its own.

**Next step:** check `gds` 36170807513 (precheck, `gl_test`, hardening time, LibreLane version). Then the Tiny FABulous study (how the fabric went through the TT flow), which answers the phase 0 decision point, and the LUT4AB area / config-bit measurement on cmos5l for the early capacity estimate. The organizer email is still open (the user will send it; low priority). `unit` workflow waits for the first Python tool with tests.

## 2026-09-25
**Done:** Project plan, CLAUDE.md and phase docs created (drafted in a Claude chat, not yet checked against a working repo).
**Boxes ticked:** none.
**Next step:** Phase 0, first task: create the repo from the CMOS5L template.
