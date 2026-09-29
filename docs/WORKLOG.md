# Worklog

Newest entry at the top. One entry per session: what was done, boxes ticked (with evidence), next step.

---

## 2026-09-29 (user-authorized TT integration)
- Replaced the adder with the 16-LUT fabric, hold/validator/guard and byte
  host. Updated generated-source provenance, source lists, actual pinout,
  architecture prototype contract and datasheet. ANISH-D11 records scope.
- TT-port cocotb test passes initial load, 256 counter checks, partial/CRC
  rejection, recovery and deselection; 4,692 simulated clocks, Icarus 13.
  Local hierarchy/proc connectivity check passes. Strict generated lint
  still fails; no physical warnings/checks were disabled to force success.
- Report `ANISH_TT_INTEGRATION.md` records evidence and local tool pitfalls.
  No phase exit boxes ticked; no GDS/timing/full-chip gate-level pass claimed.
- Usage 20% at start, 31/38/44% during work; reserve remaining headroom
  for saving and the user-authorized push that triggers chip CI.
- Next inspect the GDS run, fix generated lint and physical blockers, then
  expand reload/circuit coverage. Scheduled automation remains off.


## 2026-09-29 (resumed: small mapped user-circuit execution)
- User resumed work; hourly automation remains deleted. Usage checked at
  0%, 8% and 12% five-hour, below the retained 50% ceiling. No credit action.
- Reused cached small grid and tile netlist; no competing CAD jobs found.
  Added public-port cold-load runner and an independent arithmetic oracle.
- Icarus 13 runs `warp-small-cold.ResnzZRo` (RTL) and `.8oi2sd91`
  (both LUT tiles mapped) each pass 1,074 checks and reject the deliberate
  wrong-result control at check zero. Header, 40 addresses and footer audited.
- Initial test expected the wrong external enable polarity; FAB-10 records
  the correction. Pin numbering was correct; no generated RTL was changed.
- Report: `docs/reports/ANISH_SMALL_COLD.md`. No phase boxes ticked:
  this is cold-load mixed-level behavior, not chip gate-level/timing signoff.
- Validation: 23 existing Python regressions, all three experiment runner
  syntax checks, and whitespace checks pass. First pytest invocation used
  an incorrect audit-test path and ran no tests; corrected invocation passed.
- Next adapt small-grid hold/validator geometry, require distinct-image
  reload and recovery, then map the remaining loader/I/O before physical work.


## 2026-09-29 01:13 UTC (heartbeat: small counter compilation)
- Usage 20% five-hour / 3% weekly at start, 40% during diagnosis, 52% after
  the corrected run. Stopped technical work then; only checkpoint recording
  followed. No reset credits were invoked by this run. No active jobs found.
- Generated a two-column/two-row reference-derived fabric with 16 LUT4
  sites and four I/O pins. The first run falsely accepted an empty image
  because custom wrapper ports were unconnected; FAB-9 records the cause.
- Corrected runner explicitly connects I/O and rejects empty compilation.
  `warp-small-compile.khvqjtBG` compiles a two-bit reset/enable counter to
  four logic cells, 70 FASM features and 504 bytes. Inputs/logs/hash retained;
  source and result are documented in ANISH-D10 / ANISH_SMALL_COMPILE.md.
- No phase boxes ticked. No live-loading, mapped-execution or physical
  result is claimed. Existing local work preserved; no commit or push.
- Next reuse this cached project for a cold-load pin-level RTL oracle,
  then adapt geometry/hold/loader validation and execute it on mapped logic.

## 2026-09-28 23:11 UTC (heartbeat: small-fabric integration audit)
- Started at 40% five-hour / 66% weekly. Chose a bounded source/interface
  audit to preserve headroom under the 50% ceiling; no synthesis/P&R jobs
  launched and no active jobs found. Preserved previous local changes.
- Verified the reference's 14-row/10-column/84-LUT-tile geometry, both
  12,024-byte image lengths and exact mapped tile port preservation.
  Evidence: `build/small-fabric-integration-audit-20260928.json`.
- Recorded concrete generator, hold patch, validator, decoder, loader and
  testbench dependencies in `ANISH_SMALL_FABRIC_INTEGRATION.md`. The new
  fabric requires its own geometry and architecture identity; cropping the
  old image or weakening validation is not an integration path.
- No phase boxes ticked, no RTL/physical result added, no commit/push or
  credit use. Next generate the smallest practical connected fabric that
  compiles a small counter, then adapt and test its real loading path.

## 2026-09-28 22:11 UTC (heartbeat: full tile mapping and storage)
**Done:**
- Capacity reset: 0% five-hour / 60% weekly at start, 36%/65% after
  validation. Clean starting tree at c56ce58; no competing jobs or reset
  credits used. Reused cached reference/PDK/simulator inputs.
- Inspected pinned upstream tile/plugin/LibreLane sources. The tile flow
  disables STA; its synthesis metric uses a pre-flatten report. The new
  local experiment demonstrates why a clean stage count is not a feedback
  proof. Source snapshots and hashes retained in ignored build evidence.
- `warp-tile-mapping.sOBN3KHk`: stock/held complete reference tiles map to
  35,904.2166 / 36,173.3904 µm² of cells. Each retains all 616 dynamic
  configuration latches and distinct variable configuration nets.
- Check counts for hierarchy/generic/mapped/expanded-cell stages are
  0/184/0/143 stock and 0/189/0/173 held. Every warning is a logic loop;
  non-loop warnings fail the new measurement. Original strict preflight
  remains unchanged. No production check or timing exception was added.
- Held mapped tile storage passes 2,620 frame vectors / 5,202 full-bank
  comparisons using an independent CSV decoder. Tests cover open-gate
  transparency, closed-gate retention, both bit polarities and padding.
  Wrong-expected control fails at vector 19 as intended. Seven mapping
  audit regressions, script syntax, Python compile and whitespace checks pass.
- Added ANISH-D9 and `ANISH_TILE_MAPPING.md`; updated FAB-8 and phase-0
  summary. All jobs completed; changes remain local, no push or history edit.

**Boxes ticked:** none. This is cell mapping and an internal read-only
  storage witness with hold asserted. No compiled user circuit is exercised
  on the mapped tile, and no full-chip area, physical fit or timing is proven.
  The production Tiny Tapeout top still contains the placeholder.

**Next:** build a small stitched fabric with actual loader/edge connections,
  load a compiled design into mapped logic, and test public behavior across
  hold release. Establish configuration-aware timing and the complete
  CMOS5L physical environment before treating tile layout as chip signoff.

## 2026-09-28 (user: prioritize competitiveness, stop near 50%, push)
- User authorized pushing this checkpoint and requested a 50% usage stop;
  interpreted explicitly as five-hour usage. Readings were 30%, 37%, 47%
  during work (weekly 52–54%). Initial usage call stalled; retry succeeded.
- Reviewed fetched R4 physical-flow documentation without reading held-out
  implementations. Clean routing at one size is encouraging, but slow
  timing and larger-size fit remain unresolved. No main merge was made.
- Added a repeatable whole-reference-tile preflight. Actual measurement
  `warp-tile-preflight.hbGIhisV` reports 184 stock / 189 held structural
  loop warnings and deliberately blocks the physical-flow gate. No tile
  mapped-area estimate was manufactured from this failed gate. FAB-8 and
  `ANISH_PHYSICAL_PREFLIGHT.md` record the failures and next experiment.
- Preserve the validated loader/area work from prior sessions, review and
  commit source and documentation separately, then ordinary-push only
  anish_branch under anishvivek16. No phase boxes are ticked.
- Final usage check before publishing: 53% five-hour / 55% weekly; the
  finishing checks/docs crossed the requested threshold, so no further
  technical work was started. Twenty-three Python tests and runner syntax
  checks pass. Source checkpoint committed as `4cd016c`; documentation
  accompanies it. Remote was synchronized before the ordinary push.
- Next: inspect the pinned tile hardening method's treatment of programmable
  feedback, prove dynamic configuration in a small mapped fabric, then
  measure CMOS5L routing/timing and useful protocol capacity. These take
  priority over more isolated loader savings.

## 2026-09-28 17:10 UTC (heartbeat: word-only loader in live fabric)
**Done:**
- Usage 3% five-hour / 48% weekly at start, 20%/50% after validation.
  No competing jobs found. Reused cached images/tools and compiled one
  executable for the nine-case suite. No reset credits consumed.
- Extended the hash-checked reference-copy patch and validated-fabric
  runner with optional word-only loading. The actual row bank, selectors,
  configuration storage and user fabric remain intact. Default transforms
  match cached baseline outputs; only eFPGA_top.v differs in the candidate.
  A changed ConfigFSM is rejected before output creation.
- `warp-validated.FtTE9K1D`: byte CRC plus word-only loader passes all nine
  full-fabric RTL cases, including 67,987 A/B/A functional checks, 2,479
  B/A/B checks, two interrupted uploads, corruption, duplicate frames,
  padding, loader reset and the expected wrong-function failure.
- Selected load timestamps, check cycles, word/frame/parked counts and all
  exit codes match cached all-frontend `warp-validated.VxA9xvJv` in all nine
  cases (`baseline-comparison.json`). Patch checks, syntax and whitespace
  checks pass. Report, D8 and phase-0 summary updated. All jobs completed.

**Boxes ticked:** none. Full-fabric tests are RTL only and cover the two demo
  circuits with byte CRC. Prior bounded area/GL evidence does not establish
  full-chip area, physical timing or arbitrary-image isolation. Pending
  work preserved locally; no commit, push or history rewrite this run.
  Git identity remains anishvivek16 with the verified noreply address.

**Next:** review transferable physical-flow documentation on fetched main
  (`e9da6b8`) without touching held-out protocol implementations, then choose
  a tiny-fabric CMOS5L integration experiment. Broader isolation and the
  final host/recovery contract remain gates before production adoption.

## 2026-09-28 (user resume: word-only loader comparison)
**Done:**
- Usage 71% five-hour / 45% weekly at start, 76%/46% after checks. No active
  jobs were found. Reused cached images, library and simulator; no reset
  credits consumed. Preserved prior pending work.
- Added optional `word-only` mode to the bounded fixture/runner: management
  feeds the unchanged pinned ConfigFSM directly, omitting UART/bitbang
  receivers and arbitration. All 448 row-register bits remain observable.
  Default all-frontend mode and production RTL are unchanged (ANISH-D8).
- `warp-loader-cost.t41jdJxH`: four mapped runs pass, both CRC variants and
  both images; each checks 12,129 steps, 15 cancellations, 3,006 words and
  200 exact frame payloads. Word-CRC candidate: 2,018 cells / 48,188.7630 µm²;
  byte: 1,921 cells / 47,208.5334 µm². Byte total is 31.12% below cached
  all-frontend baseline `warp-loader-cost.AXvDP6i0` at the same boundary.
- Default RTL regression `warp-handshake.MtxHcGZ2` passes both CRC modes.
  Synthesis/boundary/area checks, runner syntax and whitespace checks pass.
  Results and tradeoffs are in `ANISH_WORD_ONLY_LOADER.md`.

**Boxes ticked:** none. This removes serial configuration capability from
  the experiment, not programmable protocol resources. Actual fabric,
  configuration latches, host and physical implementation remain excluded.
  Current work is local/uncommitted; no push or history rewrite this run.

**Next:** integrate the word-only path with the patched live reference
  fabric and repeat reload/rejection/recovery tests before considering it
  for the production host contract. Then return to physical/phase-0 gates;
  check usage before another substantial milestone.

## 2026-09-28 05:05 UTC (`anish_branch`: loader-inclusive mapped control path)
**Done:**
- Resumed after an interrupted read/fetch-only turn; working tree was clean
  and no simulation/synthesis jobs remained. Prior push is confirmed at
  `10204fa` on `origin/anish_branch`. Usage at resume 27% five-hour / 38%
  weekly, 58%/43% after validation; no reset credits consumed.
- Added an optional fixture boundary that retains all 448 row-register
  bits, plus a cached runner that maps management AND the actual pinned
  loader/row registers. Loader hierarchy is intentionally retained; opaque
  fabric outputs prevent constant-fixture area pruning. Production unchanged.
- `warp-loader-cost.AXvDP6i0`: word and byte CRC each pass mapped tests with
  counter and LFSR image payloads (four runs, 12,129 steps each, 15 busy
  cancellations, 3,006 words, 200 exact frame payloads). All actual control-
  path logic is mapped; only the fabric-side output stand-in is behavioral.
- Correct totals: word 3,591 cells / 69,542.6256 µm²; byte 3,492 cells /
  68,536.6542 µm². The loader/row bank is about 79.8% of the byte total.
  Serial frontends remain included; this 14-row reference cost excludes
  column frame selection, fabric/config storage, future host and physical
  overhead. See `ANISH_LOADER_COST.md` / ANISH-D7.
- Fixed two measurement/test issues: optimized private mux-wire references
  (FAB-6) and double-counted hierarchical area (FAB-7). Failed/intermediate
  runs retained separately. New reporter computes direct Liberty cell sums
  and checks inclusive hierarchy totals independently.
- Twenty-three Python tests pass, including three accounting regressions.
  Default RTL handshake recheck `warp-handshake.TJ9LnOFl` passes both CRC
  modes; runner syntax and whitespace checks pass. All jobs finished.

**Boxes ticked:** none. Full-fabric GL, arbitrary-image isolation and physical
  timing are not demonstrated. Changes remain uncommitted and no push was
  made during this heartbeat, per its instruction; Git identity preserved.

**Next:** measure a deliberate word-only reference loader and row-bank
  sizing tradeoff before further CRC tuning. Review transferable physical-
  flow documentation from fetched `origin/main` (`e9da6b8`) without merging
  unrelated architecture work or profiling held-out protocols. Broader
  isolation/physical gates remain open; check usage before substantial work.

## 2026-09-27 (user-authorized commit and push preparation)
- User explicitly requested pushing this branch. Fetched `origin/anish_branch`:
  local history is ahead with no divergent remote commits. No force push or
  main-branch update is needed.
- Committed experimental RTL, tests, patch and runners as `485b725`; package
  the evidence/decisions/worklog in a separate documentation commit. Earlier
  local commits `36acbb7` and `58d027f` are also included in the planned push.
- Author and committer verified as `anishvivek16` with the account's noreply
  address. Twenty Python regressions, all six new runner syntax checks and
  staged whitespace checks pass. Prior HDL/GL evidence is retained; large
  builds were not repeated for this administrative step.
- Only source and reports are staged. Ignored raw builds, logs and generated
  images remain local. No phase gate changes. Verify the remote head after
  the ordinary `anish_branch` push; continue technical work at the next
  usage-eligible run from the management-wrapper checkpoint below.

## 2026-09-27 05:28 UTC (`anish_branch`: mapped management wrapper)
**Done:**
- Usage 80% five-hour / 28% weekly at start. Completed one bounded cached
  cost/validation run; no competing jobs found. Afterward usage is 86%/29%,
  so defer further substantial work until a later eligible run. No reset
  credits consumed.
- `warp-management.xWb9WYPm`: mapped the actual reference wrapper with
  eFPGA_top preserved as exactly one empty black box, preventing constant
  fixture outputs from eliminating pad muxes. Verified only CMOS5L cells
  outside that boundary; strict synthesis checks report zero problems.
- Word CRC: 981 cells / 14,773.3740 µm². Byte CRC: 886 cells /
  13,869.1224 µm². Saving 904.2516 µm² (6.12%). Includes pacing, parking
  and demo reset muxes; excludes the fabric AND its configuration loader,
  host/CDC, physical buffers and routing. See `ANISH_MANAGEMENT_COST.md`.
- Both mapped wrappers pass the 12,129-step handshake regression with the
  actual RTL loader fixture: 15 cancellation cases, 3,006 words, 200 exact
  frame payload checks. This is mixed gate/RTL simulation without SDF,
  not full-fabric GL or physical timing validation. Evidence retained.

**Boxes ticked:** none. All jobs finished. Existing work/branch/identity
  preserved; edits remain uncommitted. No push or history rewrite.

**Next eligible run:** include the actual configuration loader in a bounded
  cost/test target. Then expand routing/DSP/RAM isolation and physical
  control-distribution evidence. A future host/CDC block remains unspecified;
  do not claim complete-chip or complete-shell area from current results.

## 2026-09-27 (user continuation: focused loader handshake regression)
**Done:**
- Usage was 71% five-hour / 27% weekly at start, 75%/28% after the first
  focused check. Kept this milestone small and reused cached loader/images.
  No active jobs were found and no reset credits were consumed.
- Added a small fixture around the actual pinned configuration loader and
  row registers; programmable fabric is replaced by constant user outputs
  solely to test parking. No production RTL was changed.
- `warp-handshake.rw1QbkFj`: both word and byte CRC modes pass 12,129 steps,
  15 busy cancellation/priority cases, a continuously asserted valid stream
  of 3,006 words and exact address/row-payload checks for 200 frame writes.
  Includes begin during CRC work, concurrent commit/write/reset/abort,
  stale-validity clearing, minimum word spacing and no write/frame overlap.
- The original byte-only run `warp-handshake.X4N5oQLx` also passed. Test
  sources, actual loader files, hashes, tool versions and logs are retained.
  Runner syntax and whitespace checks pass. See `ANISH_LOADER_HANDSHAKE.md`.

**Boxes ticked:** none. These are sampled loader/control RTL diagnostics,
  not full-fabric execution, exhaustive proofs or physical timing. All jobs
  finished; previous work and Git identity are preserved. Changes remain
  uncommitted; nothing pushed or rewritten.

**Next:** measure the complete management/pacing/parking wrapper with
  variable fabric-facing ports, so fixture constants cannot undercount its
  hardware. Keep physical timing and broader isolation as separate gates;
  check remaining usage before the next substantial milestone.

## 2026-09-27 04:27 UTC (`anish_branch`: byte CRC area comparison)
**Done:**
- Usage gate passed: five-hour 45%, weekly 23% at start; 66%/26% after
  validation. No active build jobs were found. Reused images/PDK/simulators;
  compiled one byte-mode full-fabric executable for nine cases. No credits
  or resets consumed.
- Added optional `SERIAL_CRC=1`, explicit CRC readiness and pending-byte
  cancellation. Word CRC remains default. Guard release requires the last
  checksum byte to be checked, not just receipt of the last word. The
  integration wrapper combines CRC readiness with its existing pacing.
- Matched isolated RTL/GL runs: byte `warp-validator.Yc1dlz11` passes 41
  cases / 296,422 steps; word `warp-validator.YLYLyxNZ` passes 41 cases /
  116,831 steps. Updated tests hold valid/data through CRC stalls, reject
  forwarding while busy, try early commit and cancel pending CRC work.
- CMOS5L validator-plus-guard area: word 14,078.3832 µm² / 905 cells;
  byte 13,250.3742 µm² / 828 cells. Saving 828.009 µm² (5.88%) against
  matched current source, not the older 14,123.7054 µm² snapshot. No full-
  wrapper/physical-area or maximum-clock claim. Recorded ANISH-D6.
- Byte full-fabric `warp-validated.VxA9xvJv` passes all nine expected outcomes:
  A/B/A 67,987 checks; B/A/B 2,479; six interruption/rejection/reset recovery
  cases 1,322 each; semantic wrong-image control fails as expected. Logged
  load times, word/frame/parked counts match the prior word-wide suite in
  every case; comparison JSON retained. CRC fits the four-clock word budget.
- Twenty Python tests, both runner syntax checks, legacy conditional TB
  syntax and whitespace checks pass. All jobs finished and evidence is
  retained. See `ANISH_BYTE_CRC.md` for measurements and exclusions.

**Boxes ticked:** none. Byte CRC is a measured candidate, not a production
  default or chip-level area win. Full-fabric GL, physical timing and broader
  isolation remain open. Pending changes remain uncommitted; branch/identity
  preserved as `anish_branch` / `anishvivek16`. No push/history rewrite.

**Next:** build a small loader-focused regression for held-valid requests,
  begin during CRC work and coincident commit/reset/abort, then price the
  complete management/pacing/parking wrapper. Use the usage gate before
  substantial work. Expand routing/DSP/RAM isolation and physical validation
  before treating runtime reload as a production capability.

## 2026-09-27 03:27 UTC (`anish_branch`: validated full-fabric integration)
**Done:**
- Usage gate passed: five-hour 22%, weekly 19% at start; 42%/22% after
  validation. No active simulation/build jobs were found. Reused cached
  bitstreams and pinned fabric, compiling once for nine scenarios. No
  reset credits consumed.
- Added a separate validated wrapper with synchronous ready/valid words,
  coordinated loader/validator reset, and conservative four-clock word
  spacing. Commit waits for pending frame writes; removed the validated
  TB's 100-cycle post-load wait. Documented pinned ConfigFSM timing in D5.
- `warp-validated.soYb2Cvu`: all nine full-fabric RTL scenarios meet expected
  exits/markers. A/B/A passes 67,987 independent checks and 45,186 parked
  samples; B/A/B at maximum accepted word rate passes 2,479 checks. Every
  accepted image has 3,006 accepted/forwarded words and 200 frame pulses.
- Recovery after interruption at frames 33 and 199, payload corruption,
  duplicate frame with recomputed CRC, extra padding, and loader reset each
  passes 1,322 functional checks. Bad images remain held/parked. Correctly
  checksummed wrong-function image still fails the semantic oracle at first
  release (expected exit 1). Separate read-only word/frame diagnostics do
  not force/deposit internal state.
- Twenty Python tests, runner shell syntax, legacy TB conditional syntax
  and whitespace checks pass. Preserved all previous experimental modes.
  Results and exclusions: `ANISH_VALIDATED_FABRIC.md`.

**Boxes ticked:** none. Only two compiled reference designs, selected faults
  and RTL integration are covered. New wrapper has no mapped area/timing
  result; prior isolated GL evidence is not full-fabric GL signoff. Working
  changes remain uncommitted; branch/identity preserved as `anish_branch` /
  `anishvivek16`. No push or history rewrite.

**Next:** compare byte/bit-serial CRC at the required host throughput, price
  the complete management wrapper, and add a small loader-focused regression
  for held-valid stalls, commit/reset/abort edge cases. Broader routing/DSP/RAM
  isolation, physical distribution and remaining phase-0 gates stay open.

## 2026-09-27 02:26 UTC (`anish_branch`: isolated image validation)
**Done:**
- Usage gate passed (five-hour 0%, weekly 16% at start; 17%/18% at the
  post-build check). Reused cached images, PDK and simulator; no active
  synthesis/simulation jobs were found. No reset credits consumed.
- Added experimental Verilog-2005 validator and guard composition. It
  checks architecture/version/12,024-byte length, canonical 200-frame
  structure and CRC before accepting an idle commit. Extra/padded words
  invalidate a completed transaction; reset/abort/begin suppress writes.
- `warp-validator.x2xpdWlS`: 41 transaction cases / 116,831 steps pass in
  both RTL and mapped CMOS5L functional simulation. Cases include real
  images, randomized payloads, independent zlib checksums, truncation,
  malformed/duplicate/swapped frames, corruption, metadata errors, commit
  races and abort/reset recovery. Verilog-2005 parsing and strict Yosys
  pre/post-mapping checks pass. No SDF or physical timing claim.
- Validator plus guard maps to 904 cells / 14,123.7054 µm² of Liberty area;
  host, fabric, output muxes and physical overhead are excluded. Documented
  the throughput/area tradeoff and a future serial-CRC comparison (D4).
- Fixed missing cell-direction definitions in the new mapping runner
  (ANISH-FAB-5); first failed attempt retained separately. Twenty existing
  Python checks and runner syntax pass. See `ANISH_IMAGE_VALIDATOR.md`.

**Boxes ticked:** none. This is isolated reference de-risking; the existing
  full-fabric wrapper still trusts `ImageValid`. No production ABI or phase
  gate changed. Pending work is preserved and remains uncommitted; Git
  identity remains `anishvivek16`. No push/history rewrite.

**Next:** connect this synchronous boundary to a validated full-fabric mode;
  prove identical word consumption/reset handling and final-write settling.
  Re-run both reload directions, interrupted/corrupt image recovery and
  semantic wrong-image detection. Then compare serial CRC cost at the host
  throughput requirement before allocating production shell area.

## 2026-09-26 22:23 UTC (continuation usage checkpoint)
Codex usage is 90% of the five-hour window and 14% of the weekly window.
Deferred substantial work per the automation's 85% five-hour threshold.
Reviewed the latest checkpoint; preserved pending changes, started no builds,
and consumed no reset credits. No phase boxes changed. Next eligible run:
implement image length/frame/checksum validation and malformed-load tests.

23:23 UTC recheck: five-hour usage 97%, weekly usage 15%; still above the
configured threshold. Deferred builds and implementation again, preserving
the same next step and all pending work. No reset credits consumed.

## 2026-09-26 (`anish_branch`: guarded release and mapped cost)
**Done:**
- Added an experimental synchronous reload guard and a synthesizable
  reference wrapper that parks data/tristate outputs, permits writes only
  during loading, and resets the two demo designs before pad release.
  Invalid/busy commits cannot release the fabric; abort/reset take priority.
- `warp-order.v5IBJS6u`: guarded full A/B/A passes 67,987 cycles and 61,848
  parked output samples; interrupted loads at 33/199 frames recover with
  1,322 checks each; wrong image fails immediately on guarded release.
  Controller unit check passes 120 steps; LUT/carry unit check passes 256
  vectors plus unknown-input isolation. `image_valid` is still a trusted
  input, not a checksum implementation.
- `warp-guard-cost.3TVEQJRI`: mapped guard and isolated LUT pass functional
  tests using CMOS5L cell/UDP models and TT Icarus 13. Liberty area sums:
  guard 665.8848 µm²; base primitive 344.736 µm²; held primitive 353.808 µm²
  (increment 9.072 µm²). These exclude routing, control buffering, config
  storage, parking muxes and host/validator cost. No timing signoff claim.
- Fixed the area reporter's namespace/metadata handling; retained earlier
  attempts separately. Twenty Python tests, five runner syntax checks and
  whitespace checks pass. See `ANISH_GUARDED_RELOAD.md` and ANISH-D3.
- At the user's request to report milestones and continue afterward,
  enabled hourly continuation in this chat (`continue-asic-design-work`).
  It reuses cached work, reports meaningful changes, and defers heavy work
  at 85% five-hour or 90% weekly Codex usage; it never spends reset credits.

**Boxes ticked:** none. Stock fabric reload still fails; the guarded
prototype is not a complete production shell. New edits remain uncommitted.

**Next:** replace trusted `image_valid` with a real transaction validator
  (length/frame completeness/checksum/version); test malformed/truncated
  input and restart. Then expand isolation coverage and physical timing.

## 2026-09-26 (`anish_branch`: successful reference isolation candidate)
**Done:**
- Reused cached bitstreams to test reverse frame order and all-frame
  column clearing. Both directions timed out in each experiment. The latter
  also stalls when loading the LFSR from cleared startup state. Clarified
  that Tiny FABulous's pinned clear helper instead drives the parallel
  fabric interface, asserting all frame strobes simultaneously.
- Added ANISH-D2 and a hash-checked transformer in `patches/` that clamps
  LUT and carry outputs under a fixed hold input in a separate RTL copy.
  Installed upstream sources, chip RTL and user bitstreams are unchanged.
- Candidate quick run `warp-order.Q6ZUMUHn`: A/B/A and B/A/B each pass
  2,479 independent checks. Extended run `warp-order.eg3GdZkQ`: full A/B/A
  passes 67,987 checks; interrupted B at 33 and 199 frames recovers to A
  with 1,322 checks each; wrong-image control fails as expected (exit 1).
  Both runs pass the 256-vector primitive test plus unknown-input hold.
- Added order/payload preservation tests: 20 Python tests now pass across
  experiment tooling and the existing configuration audit. Four shell
  runners pass syntax checks; whitespace checks pass.
- Fixed ANISH-FAB-3: a live shell script was edited during exploratory runs,
  causing parsing errors after the recorded simulator timeouts. Subsequent
  runs execute immutable copies and retain the runner with their evidence.
- Fetched main at `e1305e4` and reviewed its R4 integration report: physical
  routing results are still pending at that revision. Updated the upstream
  comparison without merging or repeating another branch's measurements.

**Boxes ticked:** none. The unmodified stock reload remains a failing
control. A patched reference RTL pass is not a production isolation proof,
CMOS5L signoff, or a complete phase-0 exit. New changes are uncommitted.

**Next:** define shell-controlled output parking and reset-before-release;
extend isolation to every potentially cyclic path and test control skew;
measure CMOS5L cost before adopting the patch in the generator. Keep the
specialized eFPGA candidate conditional on total-area and routing evidence.

## 2026-09-26 (`anish_branch`: user-authorized commits)
The user explicitly authorized committing the pending work. Reviewed the
experiment sources, runners and reports, retaining the documented failing
reload gate. Tooling and documentation are grouped separately using the
verified `anishvivek16` author/committer identity. Existing validation
remains 14 passing unit tests, shell syntax checks, and the recorded fabric
simulations; no expensive builds were repeated. No push was requested.
No phase boxes were ticked; the next step remains the reload repair plan.

## 2026-09-26 (`anish_branch`: frame-level reload diagnosis)
**Done:**
- Reused the two existing compiled images; no repeated synthesis/P&R or
  physical build. Cached run `warp-recheck.EAQHpix8`: cold LFSR 1,157 checks
  passes, wrong-image negative control exits 1, quick reload times out at
  byte 1996 (column 1/frame 12). Logs are now retained on the Windows volume.
- Added a strict reference-frame decoder and static SCC runner. Decoding
  matches all 140 macros of the tool-generated LFSR header. Complete
  counter/LFSR snapshots have 8 common DSP SCCs, while snapshots after
  32/33 new frames have 10/12 total SCCs, including new LUT feedback.
  Run IDs and limitations are in `docs/reports/ANISH_REFERENCE.md`.
- Added a separate read-only probe: `warp-recheck.GJ42Zo6F` observes
  64 transitions at one timestamp in X1Y8/LC's feedback mux, with A=1,
  B=0 and select fed by its output. This confirms RTL-model oscillation;
  it does not measure silicon behavior. Probe run remains a failure.
- Retained full-counter rerun `warp-recheck.bM6h67mg`: exit 0, 65,673 checks
  including wraparound. Corrected evidence references to supersede the
  initial temporary diagnostic log that did not survive WSL shutdown.
- Added `ANISH_RELOAD_PLAN.md`: test load ordering, define isolation graph
  coverage, include recovery and isolation cost in capacity comparisons.
  Consulted the upstream partial-reconfiguration discussion and Tiny
  FABulous integration/simulation documentation. Updated bug, research,
  version and phase-summary documents without changing chip RTL.
- Validation: 14 decoder/configuration-audit tests pass, all three shell
  runners pass `bash -n`, and `git diff --check` passes. No new chip/CI or
  physical signoff result is claimed.

**Boxes ticked:** none. The persistent reload acceptance test still fails.
No commit or push; branch and Git identity remain `anish_branch` /
`anishvivek16`. No changes to others' history.

**Next:** use the preserved frame/loop witness to test alternate loading
orders, then a minimal isolation candidate. Require a live A/B/A pass and
interrupted-load recovery before accepting a repair. Include any required
hardware overhead in the equal-area architecture comparison.

## 2026-09-25 (`anish_branch`: supported reference flow and upstream review)
**Done:**
- Fetched `origin/main` (`43282b4`) and `origin/efpga` (`b45a1d8`); reviewed
  their new pin-unit measurements and fabric capacity estimate. Added
  `docs/reports/ANISH_UPSTREAM_REVIEW.md` and linked it from the research
  plan. No branch merge or history change.
- Installed OSS CAD Suite 2026-06-29 under `/home/awsma/eda/2026-06-29`;
  removed exploratory replacement LUT/FF maps and pinned the compatible
  reference toolchain. Documented ANISH-D1 and the tool mismatch bug.
- Added independent pin-oracle tests and a reproducible runner for two
  real images, reset/enable behavior, counter wraparound, persistent A/B/A
  reload, a cold LFSR check and a wrong-image negative control. Added LF
  attributes for shell/FABulous scripts and evidence manifests.
- Local run `warp-reference.OBUfXfus`: counter compilation 26 logic cells;
  LFSR 19; both images 12,024 bytes. Counter passes 65,673 checked cycles
  before reload; cold LFSR passes 1,157; wrong-image test catches the
  functional mismatch. These are stock reference results, not chip capacity.
- Found ANISH-FAB-2: reload stalls during the second image upload. The
  bounded diagnostic reproduces it after the byte-1024 marker. Added
  progress logs and time limits; the runner fails rather than claiming PASS.
- Configuration audit: 616 mapped bits and 24 padding per reference tile;
  seven audit unit tests pass. `docs/reports/ANISH_REFERENCE.md` records
  scope, image hashes, run ID and unresolved checks.

**Boxes ticked:** none. Individual reference results do not close the
persistent reload or complete phase-0 gates. No chip RTL was changed.

**Next:** isolate the failing configuration transition and test a safe load
sequence/isolation repair; only then map complete protocol workloads and
measure actual primitive savings. The candidate remains specialized eFPGA
plus fixed shell; equal-area comparison, I2C-target storage and routing
margin remain open. All current edits are uncommitted for user review.

## 2026-09-25 (session 2)
**Done:**
- Fixed the `gds` docs check failure (empty title/author/description/pinout, missing `info.md` sections): filled `info.yaml` (WARP, 6x4, 50 MHz, `tt_um_warp`) and `docs/info.md`. Pinout is provisional (D-006).
- Renamed the placeholder top to `tt_um_warp` (`src/tt_um_warp.v`, `test/tb.v`, `test/Makefile`).
- Took the template `gl_test` UDP fix preemptively (BUGS #1).
- Added `scripts/setup_venv.sh`, `check_all.sh`, `gl_local.sh`, `requirements-dev.txt`, the `lint` workflow, and the `gds` paths filter + non-cancelling concurrency.
- Installed OSS CAD Suite 2026-09-25 to `~/oss-cad-suite`; FABulous-FPGA 2.2.0 into `.venv` (pinned). PATH order D-007; versions in `docs/VERSIONS.md`.
- Deleted the duplicate `docs/OVERVIEW.md` (the user did this).

**Boxes ticked (phase 0):** repo/info.yaml (local `--check-docs` pass), docs skeleton, setup_venv, OSS CAD Suite + PATH (D-007), check_all (PASS), gl_local (PASS). All local; CI run IDs to be added after the push.

**Blocked:** `FABulous` does not start: `ModuleNotFoundError: No module named 'tkinter'`. Needs `sudo apt install python3-tk` (the user; needs a password).

**Next step:** after `python3-tk`, build the FABulous demo fabric and run its reference user design through to a bitstream and simulation; then the LUT4AB area/config-bit measurement on cmos5l (early capacity estimate). Push and record CI run IDs for `test`, `gds`, `lint`.

## 2026-09-25
**Done:** Project plan, CLAUDE.md and phase docs created (drafted in a Claude chat, not yet checked against a working repo).
**Boxes ticked:** none.
**Next step:** Phase 0, first task: create the repo from the CMOS5L template.
