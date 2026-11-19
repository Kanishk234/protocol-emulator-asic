# UART multicast capture and echo

`programs/uart_bridge_capture.trw` demonstrates the existing qualified fabric:
RX on ui0 enters U1, lane 0 checks start/stop bits, and L0.O1 multicasts the
result to HOST_OUT and L1.I0. Lane 1 frames valid DATA for U0 TX on uo0; ERR
is consumed without echo. The host receives valid bytes and complete raw error
frames in order. HOST_IN is unused. Capture means the host token stream, not
an on-chip SRAM recorder or the deferred CAPTURE helper.

Cost: two lanes, three L0 slots, two L1 slots, two L0 K entries, two existing
pin units and no SRAM routine/data words. D-189 records the general need and
cost. RTL, encoding, macros, physical config and official workflow jobs stay
unchanged. The 24 preceding firmware images must retain their receipt hashes.

## Workload contract

The two consumers are blocking multicast subscribers. Host draining is required;
there is no external UART flow control or unbounded buffering. Demonstrated
rates are 115200 and 460800 baud at 50 MHz, with the existing fractional period
encoding. Sustained 1 Mbaud capture is not qualified: the host transaction rate
can be slower than the incoming byte rate. Physical pad timing, analog levels,
RS-232 transceivers and silicon interoperability are not established.

Eight model tests exercise both rates with clean and broken-stop streams, all
256 byte values at 460800, an isolated frame with delayed host service, and a
sustained stream without host service. The model uses a one-token host queue
and drains every 560 clocks in normal workloads. A disconnected multicast branch
fails the expected echo check. The no-service workload must expose RX overrun;
this negative control prevents a false unbounded-lossless claim.

The chip-port test drives ten bytes per rate, including three bad stop bits.
Each rate must deliver exactly seven DATA and three full raw ERR tokens to the
host, echo exactly seven well-framed bytes, recover after each error and leave
both pin-unit status registers zero. It compares the actual RX/TX wires with
an external UART framing decoder and requires sigrok on the unmodified TX
capture. This is a finite demonstration, not arbitrary malformed-line recovery.

## Evidence status

Focused model tests pass 8/8. Verilator passes the single chip-port test,
including both profiles, in 7.41 seconds. Icarus RTL also passes in 31.48 seconds. Exact official-netlist replay passes
in 97.01 seconds, with zero failures/skips. All three simulators cover both
profiles in the single selected test. Six unmodified TX captures independently
decode identically, with capture/decode hashes in the receipt. The final full
non-slow Python regression passes **1,126 tests in 136.41 seconds**. The gate replay uses unchanged official
run 44189196098, matching PDK and Tiny Tapeout Icarus 13 without SDF annotation.
Receipt `phase3_uart_multicast_result.json` binds source, image, capture and
result hashes once complete. No extra Phase 3 exit box is implied by this
showcase; capture dumps, metamorphic, formal, compiler and FPGA gates remain.
