# Configured C2 timing diagnostic preparation

This is a plan and a source/clock audit, not a timing pass. Physical source
[37814078650](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37814078650)
retains its deferred virtual-clock setup failure and configuration fanout failures.
The exact final C2 netlist subsequently passes the four real-loaded control and
candidate cases in
[37958116481](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37958116481).
That functional result provides a trustworthy configured image; it does not
establish its physical operating frequency.

## Concrete preparation

`test_internal/cloud_configured_c2_timing.py` reads authenticated artifacts and
the exact loaded UART image, without invoking EDA or generating SDC. It checks
the successful result/cone/netlist/image hashes and strict XML/configuration,
28 TX/28 RX, STOP and USER_RESET evidence. For each actual C2 instance at
X2Y1 and X2Y3, it records all 529 configuration latch Q pins, their real
FrameStrobe/FrameData bindings, and the corresponding image values. This reads
the actual circuit and compiler image, without consulting an independent
reference model. No constants are introduced into the circuit.

All eight user FF clocks in the physical C2 connect through mux4 `_1288_`.
Its selector latches `_1809_` and `_1810_` bind to frame 0 bits 20 and 21.
Both instances' loaded image selects `11`, hence `N_GBUF_END[3]`. C2 has
no retained GCLK/UserCLK port. All eight FF RESET_B pins are actual tie-high;
functional user reset remains in the D logic and must remain timed. The audit
retains these 16 instance-specific clock endpoints and hashes of the actual
ODB, NL, LEF, GDS, SPEF and existing SDC for review.

## Proposed diagnostic, requiring review before execution

Use separate fast, slow and typical STA processes with the exact final netlist,
matching extracted SPEF, and pinned IHP Liberty files. Verify SPEF annotation
coverage and every storage instance/pin before reporting slack. The current
null-port virtual clock cannot establish user-register clocks:
[OpenSTA's create_clock documentation](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/sdc/Sdc.tcl)
distinguishes virtual clocks from clocks attached to circuit pins.

For a **tile-local** diagnostic, attach the 20 ns architecture target to the
proven `N_GBUF_END[3]` boundary and propagate its real mux/buffer/interconnect
delays to the eight user CLK pins. This omits upstream distribution latency,
intertile skew and shell clock interaction, which must be reported as limits.
For full-fabric timing, use the genuine shell clock root and the actual
configured global routing network instead. The upstream SW termination includes
configuration-controlled logic, so it must be traced rather than assumed to be
a chain of buffers. Do not create independent ideal clocks on each FF or
replace real clock propagation with a virtual clock.
[OpenSTA's propagation command](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/sdc/Sdc.tcl)
uses gate/interconnect delays; its implementation explicitly rejects propagation
of virtual clocks. Pin exact runner command versions before implementing this
plan; the links document semantics, not a claimed installed-tool test.

RUN mode can apply image-derived case analysis to actual configuration latch Q
pins after proving configuration remains stable and FrameStrobe stays inactive
in RUN. Keep user Q/D, CLK, reset data paths and user inputs dynamic. Do not
freeze FFs to a successful simulation snapshot. A separate USER_RESET scenario
must preserve its synchronous data-path timing. Case analysis legitimately
selects configured routing and LUT functions, but does not establish startup
or reconfiguration safety.
[OpenSTA's case-analysis documentation](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/sdc/Sdc.tcl)
states that constant pins stop path propagation; applying it to user state or
clocks would therefore remove the very behavior being checked.

Require an endpoint census: every expected user CLK pin has exactly the intended
clock; no required active data endpoint is silently unconstrained; configured
combinational loops and arc exclusions are explicitly reported. Retain minimum
and maximum paths with full clock paths, setup/hold counts, clock pulse checks
where supported, and all original reports. Do not use arbitrary loop cuts,
false paths or relaxed timing budgets to obtain a pass.
[OpenSTA's sanity checks](https://github.com/The-OpenROAD-Project/OpenSTA/blob/master/search/Search.tcl)
cover missing/multiple clocks, unconstrained endpoints and combinational loops.

The architectural period alone does not supply tile boundary input arrivals,
output required times, loads, external clock latency or skew. Those must come
from a reviewed boundary contract or matching full-fabric extracted paths.
Do not silently reuse generic virtual-clock 4 ns I/O delays as proof of
configured protocol timing. Initial local register-to-register results can be
useful while remaining explicitly limited.

## Electrical and acceptance boundaries

Configuration distribution remains a separate electrical/loading gate. The
tile's reported configuration fanout failures are not waived because Q is
constant during RUN. In LOAD, configuration Q can change and the physical
FrameData/FrameStrobe network must meet its real latch capture, pulse and
settling requirements. Retain image-independent connected-load/fanout/capacitance
checks and appropriate loading-mode slew/capture checks alongside RUN timing.

Successful configured timing for these two C2 instances and this UART image
would support only that diagnostic scope. Other passing tile types still need
matching physical views; full-fabric timing needs extracted intertile and shell
connections. No frequency, competition readiness, all-image safety or hardware
promotion follows from this preparation. The next action is review of boundary
constraints, clock/annotation coverage and mode properties before adding a
bounded cloud STA workflow.

## October 10 mode-property preparation

New cloud_run_config_property.py authenticates the actual compact shared-CRC
shell and configuration pipeline, rather than substituting current fallback
RTL. Instrumented copies retain original F2 checks and its explicit assumption
that the abstract SPI receiver does not deliver a byte while CRC is busy.
Fabric response outputs are arbitrary; mapped configuration storage is not
included. Added assertions check cfg_strobe/restart/frame strobes inactive in
RUN and cfg_word/frame_data stable across consecutive RUN cycles. No RUN or
configuration stability assumption is introduced. Require both84-cycle BMC
and all84-cycle covers, including reachable RUN. Source preparation controls
pass; hosted38101606932 is pending. This is not an STA execution.

The shared CRC takes32 cycles per word. Depth84 may reach RUN after a minimal
sync-only load but cannot demonstrate a complete five-row frame write followed
by RUN. Even a pass therefore supplies only the stated short bounded evidence;
it is insufficient alone to justify constant case analysis after arbitrary
full loads. A separate full-frame-write→RUN reachability check needs a larger
justified bound or a partitioned invariant proof. Actual loaded-image simulation
already covers the concrete longer UART execution, without proving all traces.
async2sync/dffunmap model clock-cycle behavior, not analog reset or pulse safety.
