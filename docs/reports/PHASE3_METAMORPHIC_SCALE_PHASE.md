# D-191 SCALE and native routine-phase qualification

This milestone implements the explicitly approved D-191 timing-domain rules.
It does not claim that the whole host-to-pad waveform scales2x, that physical
propagation delays are identical, or that arbitrary absolute-time programs are
lane-invariant. Production hardware, firmware, clock period and official workflow
jobs are unchanged. The finite L4 checkpoint is now supported by the completed replay results
below and earlier LOOP/IDLE/TAP/PERM receipts; Phase3remains open.

## SCALE: declared intervals and explicit exclusions

The same production UART/SPI/I2C-controller programs run at fast/slow settings.
Model profiles are UART500000→250000 and625000→312500baud; SPIperiod10→20,20→40,
50→100; I2Cperiod50→100,100→200,124→248. All periods are exactly representable,
even integer clock counts. There are eight pairs and815programmed interval
correspondences, measured on complete, unchanged pad captures.

| Protocol | Compared interval | Boundaries and checks |
|---|---|---|
| UART |16within-frame edge intervals for actual55/AA TX frames | Known bit patterns require every expected edge at its declared multiple of PERIOD; both TX bytes and seven independent RX bytes must decode |
| SPI |90low/high intervals within six8-clock bursts | Exactly48rises/falls; boundaries come from six known CLK8 commands, never gap-width heuristics; MOSI/MISO and peer results checked |
| I2C |94low cells and77programmed high cells within17known bursts | Exactly94rises/falls; CLK command lengths are9,9,9,1,9,1,9,9,1,9,8,1,8,1,8,1,1; writes/reads/ACK/address/STOP function retained |

UART within-frame intervals are compared directly. SPI half-periods must equal
PERIOD/2 and double exactly. I2C low cells must equal PERIOD/2. With STRETCH,
ARCHITECTURE P11/P33 explicitly times high phases from synchronized IDLE and
allows up to3recognition clocks. The checker measures one constant overhead
across every internal high cell, requires it within0..3, requires the same value
at both rates, and compares the programmed component separately. Observed
model/Verilator overhead is3clocks:50/53low/high at PERIOD100and100/103at200.
The raw high times are retained; the captures and decoder input are never edited.
No independent correction per edge is permitted. A jittered/missing edge cannot
be reclassified as a new burst or an arbitrary host gap.

The excluded, separately reported timing consists of origin-to-first-edge launch,
UART inter-frame edge gaps, inter-burst host/reflex/SRAM service and START/STOP/SDA
sequencing. Final capture tails are also not scaled. Some excluded gaps contain
both programmed delay and fixed service; no2xclaim is made for them. Original
functional peers, exact expected host words, open-drain checks, pin flags and
independent UART/SPI/I2C decoding remain mandatory. This is finite clock-interval
qualification, not full analog/datasheet conformance or a maximum-rate result.

Eight positive model tests each decode both fast/slow captures. Three scratch
trace controls delay one internal edge by one clock and must be rejected. No
positive waveform is modified. Focused11/11pass in11.08seconds; alternate scheduler also passes11/11in8.59seconds. Baseline model/RTL sampling origins differ
because model commands are queued directly while RTL uses the real SPI host;
reported launch times are not inferred core propagation delays.

## Native routine PERM with actual matched SRAM phase

The existing period124I2C controller with40clocktarget stretching runs three
ways: L0/identity units, L1/remapped units with one actual pre-load idle clock,
and L1/remapped units without that clock. The documented host TIME register is
read at the same point in each load sequence. Require
`(moved_phase - moved_lane) mod4 == (baseline_phase - baseline_lane) mod4`.
Only actual clock execution establishes this premise; no trace is shifted after
execution. Each run must complete its original data/address/ACK/STOP oracle.

Verilator measures baseline TIMEphase3, matched movedphase0and unalignedphase3.
The matched pad traces and host observation checkpoints are identical. The
unaligned trace differs while its function/data pass, preserving the counterexample
on real RTL rather than merely in the model. No universal arbitrary-scheduler,
absolute-time-program or unaligned routine invariance is claimed.

## Evidence status and remaining gates

The chip suite has four cases: three SCALE pairs and the three-run routine-phase
case. Verilator passes4/4with0failures/skips in42.37seconds. Icarus passes4/4in157.98seconds,
and the exact official netlist passes4/4in465.52seconds. All six SCALE capture
hashes/metrics and the native-phase observations match across simulators.
The full non-slow Python regression passes1,198tests in194.18seconds. Exact-netlist
replay uses official44189196098's unchanged final netlist, matching PDK and
Tiny Tapeout Icarus13, without SDF or fresh physical signoff.

Evidence: phase3_metamorphic_scale_phase_result.json. All prior production images
must remain identical. Own unit CI/internal aggregator include this suite;
pytest/nightly discover model checks. These successful results complete the
finite L4 checklist together with the earlier LOOP/IDLE/TAP/strict PERM receipts.
They do not complete Phase3: decoder coverage, formal properties, compiler
analysis/fuzzing, FPGA and required green main CI remain separate.
