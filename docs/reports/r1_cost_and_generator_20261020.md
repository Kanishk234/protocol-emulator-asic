# R1 configuration cost and clean-generator gate

Source counts are not physical area. `tools/profiling/config_cost.py` checks generated configuration latches, every switch selector index, declared fan-in, custom mux data slots/padding and the complete fabric grid. Border tiles are included. Local outputs: build/r1_config_cost_g1.json; focused source tests pass.

| Configuration state | Interior only | Complete G1 fabric |
|---|---:|---:|
| Switch selection | 4940 | 6032 |
| Other configuration | 1716 | 1828 |
| Total stored bits | 6656 | 7860 |

The historical6656 figure is an interior count. A LUT tile has566 stored bits/414 switch bits. Its131 four-input muxes contribute262 switch bits,32 sixteen-input muxes128bits,16 two-input muxes16bits, and two nine-input muxes8bits. Fixed/direct paths consume no select state. The old clock-protected LUT pruning artifact has530stored/378switch bits, a36-bit reduction; this does not establish physical area savings or sufficient chip compaction.

## Regeneration qualification

First disposable probe used the old build/tile_cmos5l library, which contains prior LUT/primitive pruning. Its regenerated graph silently omitted3546 of19450 original G1 PIP records while retaining the same BEL interfaces. That probe is rejected. No candidate compiler or hardware result was accepted from it. BUG110.

`spikes/r1/qualify_generator.py` now stages only a Git archive of pinned fabulous-tiles7999e5a91dab77357fe9d401b6dfb0758f438bf1, overlays WARP's committed primitive sources, and generates fresh configuration maps. Inputs and resulting library are hashed. Regenerated G1 must match original PIP multiplicities, BEL records and every configuration-map section. Seven known additional ArchSpecs fields are explicitly checked; PIP delays remain unqualified.

Actual clean local result:19450PIP records,133BEL records,3185BEL-v2 records including repeated entries match exactly. Full configuration maps match. Applying the regenerated bitstream spec to the six authenticated FASM outputs from39471254787 reproduces each exact722-word stream. These are software configuration/graph checks, not loaded mapped-fabric tests. No independent-agent review is claimed.

## Capacity control, not physical candidate

A disposable six-column/three-row software model supplies128LUT4s,4timers,4shifts and42IO cells. Both concurrency workloads are compiled with three hard timer/shift pairs; the shared original external pin budget is retained. Diagnostic architecture ID0x00FE cannot load on G1. The unchanged tile geometry is not an equal-area solution; do not harden or promote this oversized reference.

Source arithmetic for its complete grid is11408stored configuration bits versus7860 for G1. This measures state count, not area or timing. It illustrates why a capacity-only expansion does not solve the physical design task.

Hosted39477188058 at70e0244 passes46checker tests, full cost census, clean G1 regeneration and resource model generation. Compilation stops on a missing corner-named PIP file before placement. BUG111; no fit or nonfit conclusion. Fix exports the required filename with explicit placeholder/uncharacterized timing metadata; no physical timing claim. Local updated47testsPASS; hosted retry pending.

## Next gate

Authenticate corrected hosted resource-model compilation before interpreting capacity. Then screen a physically plausible organization with complete configuration/routing/shell cost and actual pin-access/channel budget. Full native physical closure and all six retained personalities plus the primary concurrency target remain replacement requirements. Original121/experimental118coarse proposal and frozen G1 remain unchanged.

## Corrected compile result and portability gap

39479506675 at55c4120SUCCESS:47checks, clean control and both concurrent images pass. Native user-fabric PNR places103/128cells for UART+SPI and123/128 for UART+I2C, each using3of4timers/shifts; each image962words. This is the oversized model with placeholder timing, not silicon routing or an equal-area advantage.

Downloaded audit verifies API/source identity, strict47XML cases, original-control hashes/graphs/maps and installed FABulous module hashes. Candidate-model audit stops because the default artifact policy omitted its hidden .FABulous directory. BUG112; rerun with explicit hidden generated-model retention before calling evidence fully portable. Separately, exact-buffer census hashing regression raises local qualification count to48.


## Complete portable audit (October 21)

[Run 39480270318](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/39480270318), source4a1f35a7eeeff67b8cbac618e5dda5395c441cc0, succeeds with48strict checks and complete hidden model retention. Independent downloaded-artifact audit checks53source/generated inputs,284library files and121FABulous Python modules. Both FASM streams regenerate the emitted962-word CRC-checked images exactly. Native user-fabric placement reports103/128cells for UART+SPI and123/128 for UART+I2C, each3/4timer/shift pairs. The previous portable-audit gap is closed. Local audit: build/r1_hosted_complete/independent-audit.json. Physical, timing and equal-area acceptance remain false.

## Global-channel folding screen (October 21)

`tools/profiling/track_screen.py` folds only directional global channel names, retains eight local jump tracks and preserves clock/reset/carry names. Sources of merged destinations become explicit mux choices; aliases are never wired together. This is a graph proposal, not generated hardware. Six focused tests cover retained connections, direct-edge mux creation, source deduplication, supported arity and malformed inputs;54combined qualifier tests pass locally.

Applied to the clean qualified G1 canonical switch connections:

| Global tracks | LUT switch bits | Primitive switch bits | Projected complete 128LC control stored bits |
|---|---:|---:|---:|
| 8 | 414 | 386 | 11408 |
| 6 | 414 | 386 | 11228 |
| 4 | 414 | 386 | 10976 |

Savings are entirely at borders:180or432bits. Merging direct global paths creates additional selections, offsetting interior savings. All projected mux fan-ins remain at most16. Raw ignored screen output: build/r1_track_proposals.json. Counts are analytical graph projections; regenerated configuration maps must confirm them.

A LUT tile currently exposes306port bits, including192directional data-channel bits. Keeping its114fixed bits would project258ports at six tracks or210at four. This could reduce pin-access pressure, but neither port projection establishes a smaller legal macro, physical routability or timing. Retained local jump edges also do not establish whole-workload routability after global track loss.

Next experiment: regenerate a four-global-track model from clean owned transformations, verify ports/configuration, then compile all six retained personalities and both concurrent workloads. Reject it on lost capability or insufficient total-cost benefit. Keep the unmodified eight-track oversized control for comparison; choose any third topology only after this screen. Physical evaluation still requires equal total area, the same50MHz target and complete native routing/timing evidence. No physical attempt has been consumed by these software screens.
