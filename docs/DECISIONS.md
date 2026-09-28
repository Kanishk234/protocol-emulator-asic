# Decisions

Format for each entry: ID, date, status (Proposed / Accepted / Superseded), decision, reason, alternatives considered, cost, evidence.

---

## ANISH-D8: Compare a management-owned word-only configuration path
- **Date:** 2026-09-28 · **Status:** measured reference candidate
- **Decision:** optional fixture mode bypasses UART/bitbang frontends and
  arbitration, connecting the word port to the unchanged pinned ConfigFSM.
  Preserve the default all-frontend path and all 448 row-register bits.
- **Reason:** the management wrapper already disables serial configuration;
  retaining those frontends behind hierarchy inflated this bounded cost.
- **Evidence/cost:** `ANISH_WORD_ONLY_LOADER.md`, `warp-loader-cost.t41jdJxH`:
  byte-CRC total 47,208.5334 µm² / 1,921 cells, 31.12% below the retained
  all-frontend reference. Four mapped control-path runs pass, using both
  CRC modes and both image payloads. No physical or full-chip saving claim.
- **Tradeoff/gate:** serial bypass and serial status functionality are
  omitted. Byte-CRC live-fabric follow-up `warp-validated.FtTE9K1D` passes
  all nine reload/rejection/recovery scenarios with the cached baseline's
  load timing and diagnostic counts. The optional hash-checked transform
  changes only the frontend instance in a generated-source copy.
  Full-fabric GL, broader isolation, physical implementation and the final
  host/recovery contract remain open; no production interface is changed.

## ANISH-D7: Bound loader-inclusive mapping at the row-register interface
- **Date:** 2026-09-28 · **Status:** reference measurement, not chip adoption
- **Decision:** map management plus actual pinned configuration loader and
  14 row registers; keep a single opaque fabric-side boundary. Retain loader
  hierarchy for mapped diagnostics and explicitly include retained serial
  frontends in this measurement rather than assuming them free.
- **Reason:** the prior wrapper cost excluded loader/storage staging.
  Observable variable frame data prevents accidental removal of that bank.
- **Evidence/cost:** `ANISH_LOADER_COST.md`, `warp-loader-cost.AXvDP6i0`:
  byte mode 68,536.6542 µm², word mode 69,542.6256 µm². Both modes pass
  mapped control-path tests with both images. Loader cost dominates this
  large-reference boundary; compare a word-only path before further CRC work.
- **Limits:** excludes fabric configuration storage, column frame selects,
  host/CDC and physical overhead. Hierarchy/14-row dimensions are experiment
  choices, not a frozen tapeout ABI or a minimum-area implementation.

## ANISH-D6: Compare byte CRC within the existing four-clock word budget
- **Date:** 2026-09-27 · **Status:** measured candidate, not production adoption
- **Decision:** retain word-wide CRC as default and add `SERIAL_CRC=1` to
  process one byte per cycle, with explicit CRC backpressure. Completion
  alone cannot release the guard; final checksum validity is required.
- **Reason:** D5 already spaces accepted words four clocks apart. Byte CRC
  can use that interval, reducing XOR logic while adding a 24-bit holding
  register and control. It is shared management cost for all protocols.
- **Evidence/cost:** matched validator-plus-guard maps: word 14,078.3832 µm²
  / 905 cells, byte 13,250.3742 µm² / 828 cells, a 5.88% isolated area saving.
  Both pass 41 RTL and 41 functional GL cases, including CRC-busy stalls
  and cancellation. See `ANISH_BYTE_CRC.md` for runs and integration evidence.
- **Limits/alternatives:** full management/physical cost unmeasured; no
  maximum-clock claim. Word CRC remains useful for a future faster loader.
  Bit-serial CRC has not been compared and is not implicitly ruled out.

## ANISH-D5: Couple validated words to the reference loader with pacing
- **Date:** 2026-09-27 · **Status:** reference integration experiment
- **Decision:** add a separate validated wrapper with a ready/valid word
  boundary. Forward the same accepted stream to validator and loader until
  completion/error. Begin/abort/reset coordinate both transaction lifetimes;
  commit waits for all pending writes. Preserve trusted/stock baselines.
- **Reason:** the pinned loader stretches each frame write for two cycles.
  Allowing a new address before that pulse drains could select the wrong
  frame. Conservatively allow one word every four clocks; three idle edges
  follow each forwarded word. Remove the TB's 100-cycle final settle delay.
- **Cost/alternatives:** two pacing flops and associated gates plus the
  existing validator/guard/parking logic; integrated CMOS5L cost unmeasured.
  Selective frame-boundary pacing could improve throughput but is untested.
- **Evidence/limits:** `ANISH_VALIDATED_FABRIC.md`. Two compiled demo designs,
  synchronous management interface, no host CDC or physical timing signoff.
  This is not a production fabric/generator or architecture-contract change.

## ANISH-D4: Strict reference-image validation at a synchronous word boundary
- **Date:** 2026-09-27 · **Status:** isolated experiment, not a production ABI
- **Decision:** derive validity from pinned architecture/version/length,
  canonical frame completeness and CRC. Reject padding and extra words;
  allow release only on an idle commit after successful validation.
- **Reason:** the D3 guard's trusted host validity signal cannot detect a
  truncated or corrupted upload. Canonical order avoids frame-coverage RAM
  at the cost of rejecting selective or reordered uploads.
- **Cost/alternatives:** word-parallel CRC plus validator/guard maps to 904
  CMOS5L cells, 14,123.7054 µm² before physical overhead. Compare byte/bit-
  serial CRC at the host's required throughput before production adoption.
- **Evidence/limits:** `ANISH_IMAGE_VALIDATOR.md`, run `warp-validator.x2xpdWlS`:
  41 RTL and 41 functional GL cases pass. Full-fabric connection, host CDC,
  physical timing and production format remain unvalidated. All protocols
  would share this management cost; no protocol resource is specialized.

## ANISH-D3: Reference reload guard and isolated mapping measurement
- **Date:** 2026-09-26 · **Status:** experiment, not a production shell contract
- **Decision:** separate internal hold release from pad release. Keep pads
  parked while the configured user reset propagates, reject invalid/busy
  commit requests, and disable word writes outside the loading state.
- **Reason:** the D2 hold-only test reset user state after release; that did
  not demonstrate a clean first visible output. Holding every LUT output
  at zero also prevents user-reset logic from propagating through the fabric.
- **Limits:** the demo wrapper reserves pins 0/1 for reset/enable and trusts
  `image_valid`. A real transaction validator and production reset ABI are
  required. Isolation remains limited to the D2 LUT/carry paths.
- **Evidence/cost:** `ANISH_GUARDED_RELOAD.md`: full guarded A/B/A and recovery
  pass; functional guard/primitive gate-level checks pass; controller
  665.8848 µm² and isolation increment 9.072 µm² per primitive as isolated
  Liberty area sums, with all physical and integration exclusions documented.

## ANISH-D2: Reference-only reload isolation experiment
- **Date:** 2026-09-26 · **Status:** experiment; not an accepted chip architecture
- **Decision:** test a fixed `ReloadHold` input that clamps LUT outputs and
  carry outputs to zero during upload. The proposed production shell and
  generator are unchanged. A hash-checked transformer in
  `patches/reference_reload_hold.py` creates a separate generated-source copy,
  a patch and before/after hashes; it never edits the upstream installation.
- **Reason:** ANISH-FAB-2 demonstrates a LUT feedback loop during live reload.
  This experiment asks whether cutting LUT/carry paths removes the observed
  failure when using the same bitstreams and public loader.
- **Cost and limits:** two output clamps per reference LUT cell before
  optimization, plus a new distributed control net. No CMOS5L area/timing
  measurement yet. Routing-only loops, DSP/RAM paths, pin parking, user-state
  reset before release and control skew are not solved by this patch.
- **Acceptance:** even a two-image pass is a diagnostic result, not complete
  reload signoff. Preserve the unmodified failing control and require the
  broader recovery and physical checks in `ANISH_RELOAD_PLAN.md`.

## D-001: Build on FABulous
- **Date:** 2026-09-25 · **Status:** Proposed (confirm in phase 0)
- **Decision:** Use FABulous for fabric generation, synthesis mapping, place and route, and bitstream generation, pinned to one release.
- **Reason:** Open source, supports custom fabrics and primitives, has a physical implementation flow and IHP precedent, and has been used on Tiny Tapeout before (Tiny FABulous).
- **Alternatives:** OpenFPGA (not developed in parallel); writing a fabric and toolchain from scratch (too much work for the schedule).
- **Evidence:** to be added in phase 0 (reference fabric demo).

## D-002: Domain-specific but protocol-agnostic
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** Specialize the fabric for protocol emulation, but never add a dedicated protocol block. Hard blocks and cell features must be general primitives useful to more than one protocol. Each addition needs profiling data, benefiting protocols, area cost, and cost to non-users.
- **Reason:** The brief rules out "a UART block, an SPI block and an I2C block"; generality after fabrication is the point.

## D-003: Design set and sealed held-out set
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** Optimize the architecture on a design set (UART, SPI controller, I2C controller, I2C target). Evaluate generality on a held-out set chosen and committed in phase 1, untouched until the hardware freeze.
- **Reason:** Without a held-out set, a specialized fabric can overfit to the protocols it was tuned on, and the generality claim can't be checked.

## D-004: Equal-area comparison
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** Architecture variants are compared at equal total area (fabric, configuration, routing, shell) and equal clock target.
- **Reason:** A variant using fewer LUTs is not better if its hard blocks cost more area than the LUTs saved.

## D-005: G0 is the fallback submission
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** The generic baseline fabric with the complete shell (phase 2) must be a valid, submittable chip before any specialization work.
- **Reason:** Guarantees a working entry if specialization runs late.

## D-006: Provisional pin allocation
- **Date:** 2026-09-25 · **Status:** Proposed (finalized in `ARCHITECTURE.md` §1, phase 1)
- **Decision:** Shell host interface on `ui[0]` CS_N, `ui[1]` SCK, `ui[2]` MOSI, `uo[0]` MISO, `uo[1]` IRQ. Everything else goes to the fabric: `ui[3..7]` (5 inputs), `uo[2..7]` (6 outputs), `uio[0..7]` (8 bidirectional, needed for open-drain I2C and 1-Wire).
- **Reason:** the TT `check-docs` step rejects an empty pinout, so `info.yaml` needs a pinout before the spec exists. SPI-like host port with polled status per OVERVIEW; IRQ is optional and can be dropped.
- **Alternatives:** host port on `uio` (costs bidirectional pins the protocols need); a 2-wire host port (fewer pins, slower loads).
- **Cost:** 5 of 24 pins go to the shell.
- **Evidence:** none yet; revisit with the pin needs of the design set and the showcase.

## D-007: Local tool PATH order
- **Date:** 2026-09-25 · **Status:** Accepted
- **Decision:** System `/usr/bin` comes first; `~/oss-cad-suite/bin` is appended to the end of PATH (`scripts/check_all.sh` and `scripts/gl_local.sh` do this themselves). Python runs only in `.venv`.
- **Reason:** CI's `test` and `lint` jobs use Ubuntu 24.04's apt Icarus 12.0 and Verilator 5.020, which are also the WSL system versions. The OSS CAD Suite ships its own newer Icarus and Verilator; appending it keeps the CI versions in front while still providing Yosys, nextpnr and SymbiYosys.
- **Evidence:** local `iverilog -V` 12.0, `verilator --version` 5.020 (Debian 5.020-1); `scripts/check_all.sh` and `scripts/gl_local.sh` pass (2026-09-25). Versions in `docs/VERSIONS.md`.

## ANISH-D1: Isolated reference-flow toolchain
- **Date:** 2026-09-25 · **Status:** local experiment tooling on `anish_branch`
- **Decision:** `scripts/fabric_reference.sh` uses FABulous 2.2 in the project
  `.venv-fabric` (or an equivalent activated project venv) with OSS CAD Suite
  2026-06-29 first on PATH. Install the suite in a Linux path without spaces.
  This is an explicit reference-experiment exception to D-007; template CI
  simulator versions and `check_all.sh` retain their own settings.
- **Reason:** September's `synth_fabulous` is incompatible with the released
  FABulous mapping flow. Hand-written replacement maps introduce avoidable
  correctness risk. The supported suite also avoids launcher paths split at
  spaces. Pin manifests are retained in the experiment evidence directory.
- **Scope:** no chip RTL, physical constraints or architecture contract is
  changed. Generic nextpnr timing is not CMOS5L timing signoff.
- **Evidence:** upstream report at `origin/efpga` `b45a1d8`, local reference
  compilation logs, and `docs/reports/ANISH_REFERENCE.md` for completed checks.
