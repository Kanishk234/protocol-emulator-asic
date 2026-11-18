# Phase 2: building and fitting the chip

**Current status:** the real design has a green unchanged official Tiny Tapeout
workflow44189196098 on main revisione19556e. Final artifact review is complete.
**Phase2is complete on this verified baseline.** All exit items pass, including
the refreshed million-cycle RTL/model check and both fault injections. Closure
revision7f3ae9a has green test,lint,unit and docs CI. The warning/coverage review
found no additional physical change needed; power-analysis limitations remain
documented. No Phase3implementation starts in this report.

## Goal

Turn the programmable architecture into a chip that fits, behaves correctly and
can be manufactured through the official flow. Firmware, rather than dedicated
protocol blocks, defines what the chip speaks.

## What we built

Two lanes run triggered reflex instructions and bounded SRAM routines. A multicast
fabric connects them to four timed pin units; U0has the optional PULSE, carrier and
BITSYNC features. A512x16SRAM holds routines/data. Host SPI loads programs after
reset or power loss. The chip targets50MHz in the organizer-approved8x4CMOS5Ltile.

The smaller resource count is deliberate: it preserves every individually tested
protocol, while limiting concurrency. A two-lane program occupies both lanes.
Source, generated software tables, macro views and physical config are bound by
an integration manifest so experimental results cannot be mistaken for main.

## What passed

The official GDS, precheck, gate-level tests and viewer all pass. So do required
main test, lint, unit and docs workflows on the verified revision. Precheck passes
10checks; official gate-level tests pass UART, SPI and I2C. The exact final netlist
also passes the full22-case protocol replay with reference models and required
sigrok decoding. Icarus and Verilator provide independent RTL simulation coverage.

Final routing/KLayoutDRC/LVS/antenna violations are zero. Setup, hold, slew and
capacitance checks pass every corner. Actual slow functional setup reserve is
+0.163ns and fast hold+0.151ns. Ordinary aggregate setupWS remains0; these are
separate measurements. The official physical data/timing reports match the audited
checkpoint. Routing takes1h26m, and the complete official workflow3h08m.
The design fits at57.14%reported utilization excluding fill.

## What we learned and what remains

Timing needed changes to logic, fanout, clock distribution and configuration
paths, followed by exact-source routing and extracted checks. Early estimates
alone could not prove closure. Supported post-timing antenna repair and strict
congestion rejection were also needed.

The SRAM exposes a documented Magic limitation. D-185explicitly uses full merged-
GDS CMOS5L KLayoutDRC as the authority and waives unsupported MagicSRAMDRC and
abstract-overlap errors. Ten known macro abstraction markers remain; rawMagic-zero
is not claimed. LVS, timing, electrical, antenna and routing gates remain required.

Current-revision model/RTL lockstep passes1,000,000clocks with zero divergences.
Both clean mutation baselines pass, and the checker catches priority and cursor
faults at clocks99and326. This is deterministic simulation, not exhaustive formal
verification. Phase3can next address protocol showcases, independent verification,
formal/compiler analysis and FPGA support. The163pssetup reserve remains narrow, and no
fabricated-chip or real-hardware behavior has been measured.

**Takeaway:** the full design now passes official hardening, protocol tests and
the refreshed model check; preserve this baseline as Phase3begins.

Evidence: [official result](../reports/PHASE2_OFFICIAL_GREEN_44189196098.md),
[checklist](../design/phases/PHASE2_RTL_CORE.md), [claims](../CLAIMS.md),
[historical work](../WORKLOG.md) and [decisions](../DECISIONS.md).
