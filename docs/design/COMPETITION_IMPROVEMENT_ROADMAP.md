# WARP competition improvement roadmap

Date: 2026-10-05. Recommendations, not approved architecture changes.

The goal is useful, independently verified programmable behavior within the
6 × 4 CMOS5L allocation. Frozen G1 remains the fallback whether or not the
compact candidate succeeds. The [competition brief](https://blog.janestreet.com/protocol-emulator-asic-competition/)
values unique functionality and design/verification methods. More LUTs or
more named protocols alone do not establish a stronger entry.

## What survives if compact integration fails?

G1 already provides 88 LUT4 cells, two timers, two shift blocks, synchronized
inputs, programmable pin outputs and a host byte/status channel. User
bitstreams, host software and compiler work can change without new silicon.
Extra hard resources, new routing, configuration circuitry or changed primitive
timing require a separately verified hardware revision. They cannot be added
to the frozen chip through a bitstream.

| Improvement | Possible on unchanged G1? | Benefit and compromise | First experiment / acceptance evidence |
|---|---|---|---|
| Concurrent emulator and monitor | Yes, subject to resource/pin fit | Parallel response plus observation; shares finite LUTs, pins and host bandwidth | Compile a design-set emulator plus small independent event monitor; load through real shell and check both while overlapping traffic |
| Programmable fault injection | Yes, within available logic | Selected NACK, delays, corrupted data or unusual timing; injection consumes logic and must have defined scope | Extend a fitting design-set showcase; independently check normal and injected behavior |
| Compiler and placement efficiency | Yes | Improve fit or model timing without changing hardware; optimizations may favor particular designs | Compare deterministic seeds, FSM encoding, widths, shared compares and primitive mapping; retain behavior checks and unsuccessful results |
| Routing/configuration locality | No hardware improvement to frozen G1; compiler locality is possible | Smaller mux/configuration burden and shorter wires; reduced choices may break routing | Measure full workload route completion, actual configuration/mux cost and congestion; propagate any bit remap through bitstream generation |
| Timer/shifter input timing | No, requires revised primitives | Better timing margin; buffering or changed logic can increase area or alter semantics | Characterize worst input arcs, change one feature, verify cycle behavior/equivalence and harden the real tile |
| Generic event engine beside LUT logic | No new hard engine on G1; soft implementation can be screened | Offloads timed waits/sample/shift; instruction storage, private state and compiler integration cost area | Screen smallest shared-code lanes and show user-compiled LUT transformation/monitoring concurrently; reject if complete integration loses at equal area |
| Small queues / timestamp capture | Yes as soft logic if it fits; hard storage needs revision | Absorbs host latency, enables debugging; queue depth and timestamp width cost resources | Measure data arrival/service rates, compare minimal soft buffers, test backpressure, overflow and timestamp wrap |
| Stronger verification and timing evidence | Yes | Makes correctness and rate claims assessable; costs engineering time | Resolve mapped-fabric unknown state, check tile equivalence, audit timing models, run real loaded-image tests |
| Better host/compiler usability | Yes | Makes writing, loading and debugging new protocols reproducible | Clear resource/fit diagnostics, worked examples, status interpretation and clean-checkout reproduction |
| Broader protocol coverage | Sometimes | Demonstrates flexibility; larger designs may exceed capacity | Required protocols first; declare feature/rate limits, compile/load/test each additional design |

“Possible” is not a promise that every combination fits. UART currently uses
all four hard primitives, while the I2C controller leaves fewer LUTs for a
monitor. A passive monitor may use soft logic; two independent full engines
may fail to fit. See [G1 limits](../reports/g1_limits.md) and the
[equal-area comparison](../reports/architecture_comparison.md).

## Recommended order

1. Complete current compact physical/gate diagnosis while retaining G1.
   Do not let successor exploration block phase 5 evidence and reproduction.
2. On G1, screen placement seeds and resource-efficient compilation of the
   existing UART/SPI/I2C design set. Model Fmax is only a screening metric.
3. Build a small emulator-plus-independent-monitor showcase, then selected
   fault injection. Start with existing resources; measure where it fails.
4. Improve host tools, compilation diagnostics and reproduction instructions.
   Verify loaded bitstreams, resets, parking and error paths.
5. Select one hardware experiment from measured limits: routing locality,
   primitive input timing, or minimal generic event lanes. Keep hardware
   experiments isolated and make one hardware change per hardening.
6. Evaluate a revised architecture against fresh sealed workloads, then
   complete all physical, timing and end-to-end gates before promotion.

## Architectural experiments worth screening

- **Sparse local routing and pin placement:** preserve clock/reset routes,
  test several placements and workload sizes, and avoid pruning solely around
  one previously routed circuit. Configuration-bit and interface-wire
  remapping have published prior art: [Chung et al., How to Shrink My FPGAs](https://pure.manchester.ac.uk/ws/portalfiles/portal/207833524/FPGA_2020_FABulous_optimizations_1_.pdf).
  A physical bit remap requires corresponding tool/configuration updates.
- **Primitive input timing:** earlier registered-terminal-count and buffered
  tile attempts did not improve the worst workload or fit. Revisit the actual
  input fanout/path, rather than presenting those rejected changes as fixes.
- **Event lanes:** the existing `spikes/event_lanes/` prototype is a screen,
  not an integrated block. Its value must come from timed lanes cooperating
  with arbitrary live user logic; two sequencers alone are insufficient evidence.
- **Queues/capture:** try narrow bounded soft storage before adding hard
  storage. Specify drop policy, backpressure, host service assumptions and wrap.

Defer extra primitive tiles, extra control sets, large register files, larger
LUTs and custom transistor cells unless new profiling establishes a benefit.
Existing data does not justify simply adding them. Custom cells additionally
need process layout, DRC, timing characterization and tool integration.

## Measurement and promotion rules

Every hardware comparison uses equal total chip area, including shell,
configuration and routing, and the same clock target. Record compilation fit,
resources, actual routes/congestion, final timing, bitstream size/load time,
concurrency limits and test evidence. Cell count or initial DRT markers alone
are insufficient. Do not claim chip protocol rates from nextpnr estimates.

Protocol behavior remains programmable. Any new hard primitive must help
multiple protocols, have a DECISIONS entry with profiling/cost evidence, and
work through synthesis, place/route, bitstream generation and real loading.
Spec changes require the project's existing approval process.

G1's opened held-out protocols remain valid evidence for frozen G1. They are
not independent test data for a tuned successor. Establish a fresh sealed set
before revised architecture selection, without using its identities to tune.

## Work started now

`spikes/compiler_seeds/run.py` compiles the existing UART, SPI controller and
I2C controller on explicit `arch/warp_g1` with seeds 1, 2 and 3. It writes each
report/bitstream and an incremental `summary.json` into a fresh ignored build
directory. It changes neither frozen hardware nor protocol RTL.

```sh
source .venv/bin/activate
export PATH=/home/younix/oss-cad-suite/bin:$PATH
python spikes/compiler_seeds/run.py --out build/compiler_seeds_fresh
```

Use the project's pinned EDA versions. This is a placement/model-timing
screen, not behavior equivalence, gate-level proof or signoff. Any selected
placement still needs the existing loaded-bitstream tests. Current run:
`build/compiler_seeds_20261005/summary.json`.

Completed: all nine builds fit and generate bitstreams; neither alternate
seed improves model timing. Keep seed 1. Results and limits:
[G1 placement-seed screen](../reports/g1_compiler_seeds.md).

First concurrency demonstration: UART plus a separate four-bit event monitor
fits frozen G1 at 37/88 LCs and passes real SPI-loaded RTL and synthesized gate-shell testing. See
[G1 UART monitor](../reports/g1_uart_monitor.md) for exact evidence and limits.

Fault injection now also works on frozen G1: a 38/88-LC UART/monitor image
uses a separate synchronized input to invert selected transmitted bits.
Loaded RTL and synthesized-shell suites check corruption, recovery, normal
RX/events and STOP parking. It is externally timed, not an autonomous fault
scheduler. [Evidence and scope](../reports/g1_uart_fault_monitor.md).

Compiler follow-up: shared-control thresholds and FSM encodings were screened
on the design set. Retain defaults: no clear improvement, binary SPI trades
one LC for lower model timing, and binary I2C exceeds capacity. Added strict
port checking and failure resource reports for usable fit diagnostics.
[Results and reproduction](../reports/g1_compiler_controls.md).

Soft storage/capture now has a fitting G1 example: UART plus two queued six-bit
timestamps uses83/88LCs, with loaded RTL/synthesized-shell checks for concurrent
TX, overflow, ordering, wrap and shell backpressure. Eight-bit timestamps
exceeded capacity at91LCs. The fitting version wraps at64clocks and leaves
fiveLCs; it is bounded capture, not deep trace storage.
[Evidence and reproduction](../reports/g1_uart_capture.md).

Completed range screen: `STAMP_SHIFT=2` uses85/88LCs, storing six timestamp
bits with four-clock resolution and256-clock wrap. Loaded RTL and synthesized
shell tests pass quantization/wrap and the existing concurrent capture/UART
suite; the original83-cell option remains byte-identical. A wider stored
timestamp still does not fit. For any further range/queue change, explicitly test
quantization, wrap, drop policy and stream switching. Do not claim a larger
capture range until the actual compiled image passes loaded tests.


## October7 host-side progress

The capture decoder (`tools/host/capture.py`, `python -m host.capture`) reports
relative interval ranges, rejects reported overflow and requires an explicit
known bound to avoid modular-time ambiguity. Prescaled timestamps retain
phase uncertainty; no absolute timestamps or pin latency correction are
invented. README examples cover both timestamp settings. The new checked
CH_READ parser distinguishes a valid zero from an empty channel, and rejects
malformed/out-of-state responses. Loader validation rejects negative chunks
and truncated word/architecture fields (BUG42). All31 host tests and CLI
examples pass locally with lightweight Python only; hosted verification pending.
These improvements apply to the fallback without chip changes. They do not
increase queue depth, host bandwidth or validated hardware rates.
