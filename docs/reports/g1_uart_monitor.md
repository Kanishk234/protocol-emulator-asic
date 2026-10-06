# G1 concurrent UART and event monitor

Current local revision: `uart_monitor_sampled_20261005`, 2026-10-05.
User design: `protocols/uart_monitor/`; top-level test:
`test/test_uart_monitor.py`. Frozen G1 hardware is unchanged.

The compiled user design combines UART TX/RX and an independent four-bit
rising-edge monitor on FAB_IN1. It fits 37/88 logic cells, 2/2 timers,
2/2 shifts and 16/36 IO BELs, producing a 722-word bitstream.
Evidence: `build/uart_monitor_sampled_20261005/report.json`, including tool
versions. Its 91.12 MHz timing-model estimate is not whole-chip timing
signoff or a silicon rate.

Both full loaded tests pass, with exactly one case and no failures, errors
or skips:

- RTL shell/fabric: `build/uart_monitor_sampled_20261005/rtl_results.xml`, 23.23 s.
- Freshly synthesized gate shell/RTL fabric:
  `build/g1_monitor_gate_20261005/sampled_results.xml`, 33.82 s.

The tests load through real top-level host SPI, decode three transmitted
UART bytes while counting 20 independent events, check modulo-16 wrap,
receive 0xA5 while ten events occur, and verify framing-error status beside
the counter after a deliberately bad stop bit. USER_RESET clears state;
STOP is also exercised. This demonstrates concurrent UART and monitoring,
not two complete independent protocols, timestamp capture or deep buffering.

The initial 36-cell revision passed RTL but missed monitor events with the
synthesized shell (BUGS #26). Read-only probes found known synchronized inputs
and updating history. A mixed gate/RTL input-to-enable timing race remains a
hypothesis; the physical cause is not established. The current design adds
one fabric sample register before edge detection, costing one LC and one
additional clock of observation latency, and passes both tests above.
Historical initial evidence is retained under `build/uart_monitor_20261005/`
and `build/g1_monitor_gate_20261005/`.

The gate shell was generated from frozen-G1 source using Yosys 0.66+179 and
CMOS5L typical Liberty. Commands and the isolated Makefile are retained in
`build/g1_monitor_gate_20261005/`. This uses RTL fabric and existing D-023
routing-loop settling, has no SDF, and is not the hardened CI netlist.
Fully mapped-fabric verification and exact whole-chip timing remain separate
gates. No user state is forced. No real-hardware result is claimed.

The counter wraps without an overflow flag. Pulses must survive the shell
synchronizer; the TX test uses eight-clock high/low periods. Reproduction,
pins and status semantics are in the design README. This experiment uses
separate inputs from active routing jobs; it can still share CPU and memory.
