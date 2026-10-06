# Compact acceptance plan and competitor research — 2026-10-06

## Assessment before changing the design

WARP is not wholly broken: frozen G1 has a recorded clean physical CI run
36383587262, and new compiled monitoring/capture demos pass real SPI-loaded RTL
and mapped-shell/RTL-fabric tests. The compact successor is not accepted.
Its best **completed** stock route has144 markers and zero antenna violations.
The warm-start experiment saves15 markers at complete iteration8, then ends
without final antenna repair/checkers. No local heavy EDA process was visible
when cloud migration began. Retained checkpoints are evidence, not acceptance.

The144-marker baseline's extracted shell STA reports slow setup
+12.418807667ns and fast hold+0.144112337ns at20ns under
`chip_shared_crc_cfgbranches/runs/compact_local_route/15-openroad-stapostpnr`.
The macro is black-boxed. These numbers neither prove configured-fabric timing
nor apply automatically to a newly rerouted snapshot. The earlier original
compact native-gate probe also fails UART despite8707 configuration bits being
known and matching. The tighter candidate must be tested independently.

The ground-up geometry audit finds all144 markers in the west shell strip,
mostly Metal2, with local available-row occupancy as high as97.86%.
Tiny cell pin escapes and control/clock crossings are implicated. Zero global
overflow does not resolve these local conflicts. Diode preplacement ends258
markers; higher clock layer and CRC padding screens do not justify full runs.
The larger-NOR backup has legal placement and a passing mapped-shell UART
screen, but the original NOR cluster disappears without resizing in the warm
restart. See [the exact audit](compact_route_root_causes.md).

## Ordered experiments and acceptance gates

1. **Finish a bounded stock route in hosted CI.** Resume the hashed iteration8
   checkpoint with the complete64-iteration budget. Require zero native routing,
   antenna and critical disconnected pins. Keep needed hold repair and foundry
   geometry rules. Retain the last complete checkpoint on timeout. Hosted flow
   packaging and four threads differ from the local run; this is not an isolated
   iteration-limit comparison.
2. **Use surviving geometry to choose one fix.** Classify each final cluster as
   intra-cell pin access, cell-to-cell escape, macro boundary access, clock
   crossing or antenna-repair congestion. Inspect actual shapes/vias and pin
   accessibility before applying a control. Reject changes that shift rather
   than remove conflicts. Test router pin-access search settings within PDK
   rules first; then targeted cell orientation/master or local placement.
   Larger NOR is a backup, not the next full run. Equivalent CRC decomposition
   is another hypothesis, requiring an isolated netlist, equivalence/loaded
   tests, actual added area and new timing. This PDK has no larger o21ai variant.
3. **If locality still prevents closure, reserve routing space deliberately.**
   Consider local density redistribution and macro-edge pin distribution.
   A wider shell strip can cost fabric capacity or require narrower edges;
   smaller fabric is an explicit fallback, not a free improvement. Compare
   complete area and the same20ns target. Moving clocks or adding branch
   buffers pays metal/cell/hold-repair costs. Do not launch all options at once.
4. **Close physical checks on the accepted snapshot.** Re-extract parasitics,
   check setup/hold and electrical limits at all supplied corners, then stock
   GDS DRC/LVS/antenna and official Tiny Tapeout precheck. A green routing job
   alone is insufficient. Record exact source/config/tool/input hashes.
5. **Close native functionality separately.** Run the real configuration loader
   against actual tighter mapped fabric with a passing RTL control. Trace the
   first unknown user-state/route signal from reset and configuration. Separate
   zero-delay combinational settling/model effects from a real reset or mapping
   error using minimal reproducible cones and independent checks. Do not force
   configuration or user state to manufacture a pass. Existing D-023 settling
   is a diagnostic limitation, not proof of native correctness. Any model fix
   needs demonstrated semantics and loaded regression evidence.
6. **Close timing inside the configured fabric.** Recover hash-matched tile
   timing/parasitics, bind models to actual hardened views, and measure loaded
   workload paths including hard primitives and shell interfaces. Add SDF
   checks where appropriate; functional pin simulation does not prove rates.
   Neither the current macro-black-box shell STA nor nextpnr estimates replace
   this gate. Fresh timing must also qualify G1 claims where evidence is missing.
7. **Reproduce and promote only after all gates.** Clean-source generation,
   compile/bitstream consistency, all required CI, and the unchanged phase gate
   remain necessary. The checkpoint job accelerates diagnosis, not reproduction
   certification. Retain frozen G1 until a successor earns acceptance.

## What other entries teach us

These are observations from public project sources, not independent verification
or equal-area rankings. No competitor code was copied; check license and retain
attribution if a later implementation uses it.

| Project/source | Observed approach | WARP application and cost |
|---|---|---|
| [Loom decisions](https://github.com/thomasgilbert481/tt_um_loom/blob/main/docs/DECISIONS.md) | Shared datapath; small cell additions can substantially worsen congestion; optional autonomous feature dropped for routing budget | Favor local/narrow/shared control; judge actual routing, not cell count. Shared resources can constrain concurrent activity. Our shared CRC and frame-index branches already follow this direction. |
| [STT](https://github.com/TejasDasa/protocol-emulator-asic) | Independent programmable engines; memory blocks consume upper routing layers; explicit distinction between clean geometry and a50MHz timing violation; cycle lockstep, mutation and generated-spec checks | Inventory macro/PDN metal blockage, prove tests can catch faults, and separate evidence scopes. New memory is not automatically an area/routing win. No memory change is authorized by this report. |
| [Tempo](https://github.com/satyaammu93/jane-street-asic-2026/tree/main/protocol_emulator) | Two timed engines, capture, bounded waits and fault observability | Emphasize reproducible fault/capture demos and host-visible failure information. WARP's soft monitors/capture already work on G1; hard deadline primitives would need profiling, area measurement and a new decision. |
| [Sophos](https://github.com/OliverKlug/sophos-protocol-emulator) | One programmable engine with capture/replay; reported physical timing at40MHz | Build a convincing capture/replay workflow and rate evidence. Replay consumes soft resources;40MHz results are not comparable to our50MHz target without matching conditions. |
| [mcranny](https://github.com/mcranny/protocol-emulator-asic) | SPI-loaded instruction engine and small TX FIFO;25MHz target and stated acceptance limitations | Quantify host service bandwidth, overflow and batching. Host/compiler improvements transfer to G1. Different targets/electrical limits cannot be borrowed as a closure workaround. |

The promising transferable ideas are observability, deterministic replay/fault
experiments, explicit host bandwidth budgets, adversarial verification and
careful locality. They do not require switching WARP to a processor. The
competition value remains programmable parallel user logic backed by measured
coverage; a claim that WARP outperforms these designs requires equal-area data.

## Work independent of compact routing

The monitor, fault monitor, two-entry capture and timestamp-prescaling option
already fit G1, as do compiler input validation, stale-image removal and
hash-bound reports. Hosted CI now rechecks four demonstrations. Remaining
software opportunities include capture/replay tooling, host batching and
service-bandwidth measurement, failure trace export, deterministic demo scripts
and test mutation. Those preserve the fallback hardware. Larger event queues,
wider timestamps, memory, deadline cells, fabric I/O redesign or more hard blocks
can require additional capacity/hardware and must pass the architecture gates.
See [the full roadmap](../design/COMPETITION_IMPROVEMENT_ROADMAP.md).
