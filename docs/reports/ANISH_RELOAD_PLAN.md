# Reload repair plan — 2026-09-26

Recommendation: keep the specialized eFPGA plus fixed shell as the leading
candidate, but make safe complete-image replacement a design requirement.
The [reference experiment](ANISH_REFERENCE.md) exposes an intermediate LUT
feedback loop even though both final bitstreams work. Adding a CPU does not
repair this fabric behavior; architecture selection still needs equal-area
workload and physical evidence.

## What the shell must control

Proposed sequence: park external outputs; quiesce the programmable network;
load and verify the complete image; reset user state; release isolation;
enable protocol execution. A failed or interrupted load must stay parked
and quiescent until a fresh complete image is accepted. Management logic
must remain clocked and reachable throughout recovery.

Parking pins prevents incorrect external drive but does not interrupt
internal loops. Stopping user clocks prevents sequential progress but does
not interrupt a combinational inverter loop. Neither measure alone closes
the newly demonstrated failure. An image checksum detects corruption but
does not make intermediate routing safe.

## Experiments, in order

1. **Minimal witness:** retain the failing column 1/frame 12 boundary and
   X1Y8/LC probe. The same configuration transition must fail before a fix
   and complete after it. Keep the ordinary public-port A/B/A test separate
   from static snapshots and the diagnostic probe.
2. **Load-order screening:** test alternate frame orders using identical
   final images. Require A/B/A, B/A/B and interrupted/restarted loads. A
   successful pair only establishes a workaround for that pair; do not
   generalize it to arbitrary user HDL. Zeroing configuration first also
   transitions through mixed configurations and needs its own evidence.
3. **Isolation candidate:** define a fixed, nonprogrammable inhibit signal
   that cuts every potentially cyclic active path during loading. Begin
   with a minimal LUT/routing reproducer and explicit graph cut coverage;
   then include carry chains, local feedback, routing-only cycles and hard
   block bypass paths. Clamping just the observed LUT fixes one witness,
   not the general architecture. Release only after configuration settles
   and user reset is established. Do not rely on the simulator's initial X
   state or force internal nets in the acceptance test.
4. **Price the repair:** synthesize the isolation implementation in CMOS5L
   and include its gates, fanout buffers, timing impact, routing and reset
   distribution in the total fabric budget. Compare against a validated
   restricted load protocol. Shadow configuration doubles the storage
   component before commit mux/distribution costs and still needs safe
   switching; treat it as a comparison, not a free atomic-load solution.
5. **Acceptance:** independent pin checks for both designs, reset while
   disabled, full counter wraparound, no unknown outputs after release,
   bounded load completion, parked pins throughout loading, and recovery
   after reset/truncation at selected frame boundaries. Expand to all
   boundaries and broader circuits before claiming arbitrary reload safety.

No chip RTL or frozen architecture contract is changed by this plan. A
repair is accepted only after the generated fabric, host sequence and real
loader agree; the current reload gate remains open. Keep the generic fabric
as a control and the TRIPWIRE alternative available while capacity and
reconfiguration costs remain unresolved.

## Primary-source context

The FABulous maintainers describe addressed frames that can be written in
different orders, and routing-resource partitioning for partial
reconfiguration. That supports testing load order; it does not demonstrate
safe transitions for our independently routed whole-fabric images.
[FABulous discussion #608](https://github.com/FPGA-Research/FABulous/discussions/608)
(read 2026-09-26).

Tiny FABulous distinguishes live configuration simulation from static
emulation, which initializes configuration and permits pruning unused
logic. Our static SCC analysis is only a diagnostic; dynamic loading must
remain the acceptance path. Its integration flow implements tile libraries
and stitches a fabric before the top-level Tiny Tapeout build; transferring
that approach to CMOS5L still requires matching physical views and flow
validation. [Tiny FABulous SKY26a README](https://github.com/mole99/tt-fabulous-sky-26a)
(read 2026-09-26).
