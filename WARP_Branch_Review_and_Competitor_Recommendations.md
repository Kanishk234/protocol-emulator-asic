# WARP: branch-specific review and competitor recommendations

Reviewed September 28, 2026. Input: `protocol-emulator-asic-efpga.zip`, archive comment `14e70638f0d7f2cd5ce8664b568c1b73751c32dc`. Hardware freeze recorded in the project: G1 at `3047dea`.

This adds the actual WARP implementation to the earlier competitor survey. It supersedes recommendations in that survey where they describe capabilities WARP already has. No project source files, architecture, or freeze decisions were changed. Repository measurements and CI results are attributed to the supplied reports; their remote logs were not independently verified.

## 1. Assessment

WARP already implements most of the useful foundational ideas found in the competitor search: a FABulous fabric, configurable timer/shift primitives, a complete compiler/bitstream/loader path, a fixed management shell, output parking, independent protocol models, mutation checks, and a held-out evaluation.

The best next work is to make its configured implementation and end-to-end claims stronger, then add a small reactive demonstration within the frozen fabric. Broad architectural expansion is less attractive than the earlier survey suggested. Capacity is already a measured constraint, and several obvious hardware ideas have already been rejected with data.

Your most defensible existing differentiator is the measured specialization experiment: replace eight generic LUT cells with reusable primitives, keep the same macro footprint, and show which workloads become feasible. That is a stronger argument than simply calling the design an eFPGA. It is not evidence of superiority over a CPU/PIO entry, which would require a separate comparable baseline.

## 2. What you actually have

| Capability | Evidence inspected in the ZIP | Assessment |
|---|---|---|
| Specialized fabric | `arch/CURRENT`, `arch/warp_g1`, `macro/warp_g1`, `arch/prims` | G1: 88 LUT4+FF cells, two timers, two byte-wide shift registers |
| Generic baseline | `arch/warp_g0`, architecture comparison | G0: 96 LUT4 cells in the same macro footprint |
| Real programming flow | `tools/compile/{compile,bitgen,bitfile}.py` | Verilog → Yosys → nextpnr → FASM → `.wbit`; own bitgen addresses an upstream clock-select issue |
| Fixed shell | `src/{tt_um_warp,wp_shell,wp_spi_target,wp_fifo,wp_crc32}.v` | Architecture/version/length/CRC checks, run control, two-entry host FIFOs, registered outputs and parking |
| I/O handling | `src/tt_um_warp.v` | Input synchronization; output and OE registers; open drain through value=0 plus OE, not a separate hard mode |
| Reprogrammability demonstration | `test/test_bitstream.py`, phase-4 summary | Six sequentially loaded protocol personalities reported passing locally |
| Independent checking | `tools/refmodels`, protocol tests, `test_internal/cosim` | Reference models and UART source-versus-configured-fabric co-simulation exist |
| Formal work | `formal/`, `docs/reports/formal.md` | F1 isolation and F4 primitive/spec equivalence reported unbounded; F2 loader check bounded to 84 cycles |
| Mutation testing | `scripts/mutation.py`, mutation report | Eight reported kills; result classification needs strengthening |
| Physical work | Macro files, `src/config.json`, physical/decision reports | Substantial physical implementation evidence, with important black-box and timing qualifications below |

### Recorded protocol fit

These are the project's reported workload results, not new place-and-route runs here. Different example parameters can produce slightly different estimates.

| Workload | G1 cells / 88 | Hard timers / shifts | G0 cells / 96 | Scope |
|---|---:|---:|---:|---|
| UART | 29 | 2 / 2 | 124, no fit | TX/RX |
| SPI controller | 47 | 1 / 1 | 86 | Controller, not an SPI target |
| I2C controller | 70 | 1 / 1 | 115, no fit | I2C target is a separate unsupported design |
| WS2812 transmitter | 32 | 2 / 1 | 82 | Requires sustained host service |
| 1-Wire controller | 77 | 2 / 1 | 126, no fit | Standard speed; no ROM search |
| SWD | 44 | 1 / 1 | 61 | Fabric bit engine; packets, parity decisions, retries in host software |
| I2C register-map target | 169, no fit | 0 / 1 | 184, no fit | Tested source RTL, not supported by the configured chip |
| CAN example | 207, no fit | 2 / 1 | 241, no fit | No chip-level support; additional protocol limitations documented |

Sources: `docs/reports/g1_results.md`, `g1_limits.md`, `heldout_results.md`, and protocol READMEs. The UART reduction from 124 to 29 cells is approximately 77%; 1-Wire from 126 to 77 is approximately 39%. These concern soft-cell demand, not total chip-area reduction.

## 3. Which competitor ideas still add value

| Competitor idea | WARP status | Recommendation |
|---|---|---|
| FABulous/custom primitives | Already present | Do not migrate toolchains or re-add timer/shifter blocks |
| Independent models, mutation, co-simulation | Already present | Improve failure classification and broaden the configuration-path checks |
| STT's explicit proof scope and intentional failures | Partly present | Close the hardened-tile equivalence gap and make proof failures distinguishable from infrastructure failures |
| Tempo's observable failure and configuration contracts | Parking/checks already present | Tighten complete-image validation and document exactly what is protected |
| mcranny's sustained-bandwidth accounting | WARP has a faster link, but per-byte overhead remains | Measure the actual board transport and remove avoidable polling overhead |
| BitLoom/Sophos capture and debug visibility | No general capture/replay personality identified | Start with a small bounded capture or trigger-response bitstream |
| GP_PAE/STT concurrency | Six WARP personalities currently run sequentially | Try a deliberately reduced composite workload; do not concatenate existing full designs |
| STT/Abagel CRC/stuffing hardware | Not exposed as fabric hard primitives | Future architecture experiment only; no evidence it alone makes CAN fit |
| PRISM/configuration-memory optimization | WARP already uses frame-based configuration latches | Their instruction-memory macro savings are not a direct replacement for distributed eFPGA configuration |

Useful external sources: [STT formal notes](https://github.com/TejasDasa/protocol-emulator-asic/blob/main/docs/formal.md), [STT area study](https://github.com/TejasDasa/protocol-emulator-asic/blob/main/docs/area-study.md), [Tempo RTL](https://github.com/satyaammu93/jane-street-asic-2026/blob/main/protocol_emulator/src/tt_um_protocol_emulator.v), [mcranny throughput plan](https://github.com/mcranny/protocol-emulator-asic/blob/main/docs/phase-2-plan.md), [BitLoom](https://github.com/sheehanmunim/bitloom), [Sophos](https://github.com/OliverKlug/sophos-protocol-emulator). BitLoom evidence in the preceding search was indexed documentation, not inspected RTL. Competitor results were not rerun.

## 4. Highest-priority improvements on the frozen chip

### 4.1 Close the implementation-evidence gap

**Observed:** `test/Makefile` defaults `GATES=yes` to `WARP_FABRIC=rtl`. This tests a synthesized shell around generated fabric RTL. A separate macro-netlist mode exists, but unused routing loops and zero-delay hazards caused hangs. D-023 explicitly records that CI no longer exercises the hardened fabric netlist with the bitstreams and proposes per-tile equivalence.

**Observed:** `src/config.json` supplies a port-only macro black box to chip synthesis/STA and abstracts the macro for LVS. Positive top-level timing slack is therefore not a signoff result for the programmed LUT-to-routing-to-primitive paths. `tools/timing/README.md` is appropriately cautious: nextpnr uses a mixture of extracted routing, fixed library arcs, and margined primitive arcs; configured designs have not been timed end to end by STA.

**Do next:** complete per-tile RTL/netlist equivalence, state its configuration/loading assumptions, and check the stitched macro's connectivity. Add configured-design timing analysis for representative images, including the fabric clock path, register-to-register paths, shell/fabric boundaries, setup and hold. Set configuration constants for analysis only; preserve live configuration in the manufacturing design. Validate the configuration-to-constant translation itself.

**Acceptance:** proof or qualified equivalence evidence for every used tile type; an auditable hierarchy of physical/LVS coverage; timing results tied to exact macro revision and image hash. Do not treat simply reducing the clock as a substitute for hold or connectivity checks.

This is the most valuable verification lesson from the competitors, because it strengthens the part specific to your architecture.

### 4.2 Enforce timing in the compile/CI contract

**Observed:** `tools/compile/compile.py` invokes nextpnr with `--timing-allow-fail`. It records `meets_50mhz`, but successful compilation still returns an image. `tools/compile/protocols.py --require` checks `fits`, not that timing meets the target. The fabric workflow uses that command.

**Proposal:** retain permissive compilation for research, but add a requested clock frequency and an explicit timing acceptance gate for supported releases. Reject a missing timing result for sequential designs, and handle intentionally combinational/idle examples separately. Record the target clock in the report/manifest and ensure the board helper uses the matching clock. This is a flow change; it does not need new silicon.

**Acceptance:** an intentionally too-fast target makes the release check fail; a fit-only run remains available and clearly labeled. This gate still checks a model until the configured timing work above is completed.

### 4.3 Make mutation results distinguish bugs from broken tooling

**Observed:** `scripts/mutation.py` classifies any nonzero subprocess exit as a kill. For SymbiYosys it treats absence of `DONE (PASS` as a kill. A missing executable, elaboration failure, or solver problem can therefore look like success. The classifier also does not establish a fresh passing baseline for each selected command.

This does not show that the recorded eight kills were false. It shows the harness cannot exclude that explanation on its own.

**Proposal:** require a passing unmodified control, successful elaboration, evidence the intended test/assertion executed, and a recognized assertion/test failure. Classify infrastructure errors and timeouts separately. Preserve the specific failing property/test and its log. For formal runs, require the expected FAIL result rather than merely absence of PASS.

**Acceptance:** deliberately hide a tool or break a dependency; the campaign reports infrastructure failure, not a kill. Deliberately alter timer period; the intended functional checker fails.

### 4.4 Validate complete configurations, not only transport integrity

**Observed:** the shell's format check verifies the initial sync word. Length is the host-declared word count and CRC covers the supplied words. The compiler performs additional framing checks and emits a complete image. Both public `.wbit` parsers accept a CRC-correct image consisting of the sync word alone; I reproduced that parser behavior. F2's documented one-word cover likewise does not establish full-fabric coverage.

**Implication:** integrity/version checks do not establish that every configuration location was initialized. A well-formed transport carrying an incomplete image is different from a corrupted transport. This is especially relevant after a previous design or a failed load, because configuration latches retain values not overwritten.

**Frozen-chip improvement:** validate the architecture-specific frame set, complete rows, allowed columns/selects, unique coverage, exact terminator, and required length in the host loading API. Apply validation to raw `load()` as well as file loading. The 11 shipped images each contain 722 words: sync, 120 frames of one header plus five row words, then desync.

**Scope:** host validation protects the supported loading path; it does not make the existing hardware reject arbitrary raw SPI traffic. If that guarantee is required, it is a hardware-contract change for a later revision. Preserve this distinction in F2 claims.

## 5. Best new functionality experiments

### 5.1 A small reactive responder instead of the full register-map target

The failed I2C target combines protocol control, a shared register map, host register commands, dirty/status state, and data selection. Its failure to fit is not proof that every useful I2C target must fail.

**Suggested new bitstream:** fixed-address I2C responder with a bounded response, or a streaming target that uses clock stretching while waiting for host data. Remove the shared register-file abstraction and its host command decoder. Keep byte reception, ACK policy, START/STOP/repeated-START behavior, and any stretch timeout in the fabric.

A first demonstration could return a short configured identity, capture a write, and optionally NACK a selected transaction. It need not reproduce the original target's full semantics. Host-mediated service requires a controller that tolerates the chosen stretch duration; it cannot be assumed universal.

**Why this is worth trying:** it restores a reactive endpoint use case through a bitstream-only change, rather than adding hard I2C logic. Resource fit is unknown until synthesized and routed. Keep the existing unsupported target and its failed fit as part of the honest evaluation.

### 5.2 Concurrent minimal functions

D-036 correctly identifies resource problems for the existing full examples. UART uses both timers and shifters; SPI plus SWD totals 91 cells before integration, above 88. That does not establish impossibility for reduced or jointly optimized designs.

Try one of: UART TX-only plus a small external-event counter; a serializer plus edge-triggered output response; or a minimal SPI transaction generator plus a bounded event monitor. Use one command decoder and one host-output multiplexer instead of concatenating complete host interfaces. Measure merged resources, routing, and combined host traffic.

**Acceptance:** both functions demonstrably progress independently under asynchronous stimuli, with bounded response latency and no silent data loss. A small successful concurrent case makes the fabric's spatial execution easier to demonstrate. Do not claim it outperforms multi-lane PIO without measurement.

### 5.3 Capture and replay, starting very small

The BitLoom/Sophos direction fits the competition's debugging use case, but a large trace buffer is a poor first fit for 88 cells. Start with one captured event/timestamp, a short pulse-width measurement, or a trigger followed by a programmed response. Explicitly signal capture overrun.

`wp_timer` exposes terminal count rather than its current count, so an arbitrary timestamp cannot simply be read from it. A capture personality would need soft timestamp state, a limited alternative such as counting intervals, or new hardware. Streaming timestamps for every high-rate edge will run into the host link.

Replay must either be bounded/preloaded or use a proved host schedule. Do not promise indefinite high-rate capture/replay from two-entry FIFOs.

### 5.4 Faster host service before bigger FIFOs

At the specified 50-MHz clock, the shell permits at most 6.25-MHz SPI. `CH_WRITE` costs three bytes per payload byte; `Warp.ch_write()` additionally polls status in a separate one-byte transaction before each successful write. The ideal wire-only upper bound for this helper is therefore approximately 195 KB/s, before chip-select gaps, synchronization/response timing, and software overhead. At the documented 10-MHz board example clock the same bound is approximately 39 KB/s.

These are calculations, not measured board rates. The current transport bit-bangs pins, so actual performance can be substantially lower. This explains why the documented WS2812 need of roughly one byte every 10 microseconds is a meaningful constraint.

**Frozen-chip options:** a faster compatible board transport, queued execution, using the status already returned during transactions where safe, and caching conservative FIFO-space information. Preserve flow-control correctness; do not merely delete polling.

**Future silicon options:** packed channel commands and deeper FIFOs. First measure actual host service latency and average bandwidth. Larger buffers cannot correct a sustained deficit.

## 6. Hardware ideas to defer or investigate only with new evidence

- **More timers/shifters:** the project already measured that primitive count is not the design-set limiter. An extra primitive tile costs eight LUT cells. Revisit only for a chosen concurrent workload that benefits enough.
- **Register-file tile:** D-034 already evaluated it and the existing target still failed to fit. Do not repeat this proposal without a substantially different workload/interface.
- **Registered terminal count alone:** already evaluated in D-030. It improved a timer output arc but did not improve the limiting I2C-controller estimate.
- **CRC/stuffing primitive:** potentially useful, but CAN needs 207 cells against 88. Profile the parser/control, CRC, stuffing, and host logic separately before proposing a tile. The existing `src/wp_crc32.v` is a loader checksum unit; it is not a programmable protocol CRC accessible to fabric routing.
- **Runtime-configurable timer reload:** current primitive reload is bitstream configuration; UART's runtime-divisor path uses plain logic. A dynamic reload interface could help baud adaptation, but consumes tile ports/routing and requires a new fabric version. Software recompilation may be sufficient for the intended use.
- **Large CPU subsystem, general trace SRAM, partial reconfiguration:** high integration cost and no demonstrated need in the current feature set. Preserve G1 as the proven baseline.
- **LUT-size/routing overhaul:** already constrained by the hardened tile library and equal-area comparison. It is a new architecture experiment, not a quick optimization.

If architecture tuning uses the now-revealed WS2812/1-Wire/SWD/CAN results, those protocols become training data for that revision. A new held-out set is needed to claim an independent generalization result.

## 7. Presentation fixes that affect the submission

The root README is still the Tiny Tapeout template. `docs/CLAIMS.md` stops at the early tiny-fabric results, and parts of the architecture/G1 report still describe already-completed work as planned. The documentation needs a concise current entry point, not more volume.

Lead with the current resource budget, compile/load commands, supported protocol roles, specialization results, and proof/physical scope. Link historical reports as historical. Clarify these distinctions:

- Six sequential personalities are reconfiguration evidence, not concurrency.
- Mutation testing injects implementation bugs to assess tests; it is not an on-chip feature that injects malformed transactions into an external device. D-036's wording conflates them.
- SWD bit timing can be autonomous while SWD packet handling remains host-controlled.
- I2C-controller support does not imply I2C-target support.
- A fixed-output pin parked at zero may assert an active-low external signal. The existing BUGS #19 workaround deserves prominence in pin examples.
- The estimated Fmax values are model results; shell STA and behavioral fabric tests do not replace configured-fabric timing.

Also soften the architecture comparison's word “dominates”: G1 improves workload fit, but its reported minimum Fmax is lower and is computed over a different set of fitting workloads. State the capability gain and compare common workloads individually.

## 8. Checks performed here and their limits

I inspected the RTL, compile/host tooling, test/CI configuration, architecture decisions, fit/timing reports, formal scope, and mutation runner. I ran limited Python checks in a local virtual environment against all 11 committed `.wbit` files:

- CRC/length validation and exact serialization round trip;
- agreement between the compiler-side and board-side parsers;
- architecture version 3;
- 722 words per image, all 120 expected frame headers, and terminal desync.

All passed. I also reproduced acceptance of a sync-only CRC-correct file by both parsers and evaluated the mutation classifier's handling of an infrastructure error.

I did not run HDL simulation, formal tools, synthesis, routing, or the complete pytest suite: this session lacks Icarus, Verilator, Yosys, pytest, cocotb, and the required fabric dependencies. No physical timing, protocol-correctness, or mutation-kill result was newly established here. Full FASM regeneration was not performed.

## 9. Recommended order

1. Complete hardened-tile equivalence and configured timing evidence; fix compile timing and mutation acceptance gates.
2. Strengthen full-image validation and align the README/claims with the current implementation.
3. Prototype a reduced reactive endpoint or small concurrent trigger/capture demonstration on G1; stop early if mapping proves it unhelpful.
4. Measure and improve the actual board transport.
5. Consider new silicon primitives only after a specific workload demonstrates a gain large enough to justify reopening the architecture.

The strongest next step is not to add the whole competitor feature list. It is to turn the existing specialized fabric into a demonstrably reliable, useful programmable instrument while keeping its limits explicit.
