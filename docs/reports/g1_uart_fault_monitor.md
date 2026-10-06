# G1 UART fault injection with concurrent monitoring

Local run `uart_fault_monitor_20261005`, 2026-10-05. This extends the
UART/monitor user bitstream, without changing frozen G1 hardware.

The new top `protocols/uart_monitor/uart_fault_monitor_top.v` adds an XOR
between UART TX and synchronized FAB_IN2. A timed control pulse corrupts
selected transmitted data; a high control while idle forces TX low.
FAB_IN0 remains RX, FAB_IN1 the independent event input, and FAB_OUT0 TX.
Counter and UART status retain the existing monitor format.

The actual compiled image uses **38/88 LCs**, all two timers and two shifts,
17/36 IO BELs, and 722 words. Relative to the sampled monitor it costs one
LC and one input IO BEL. Compile report:
`build/uart_fault_monitor_20261005/report.json`. The 89.90 MHz model estimate
is not chip signoff or a demonstrated physical protocol rate.

## Loaded-interface verification

Both full suites load the same image through top-level host SPI, with two
cases and no failure/error/skip:

- RTL shell/fabric: `build/uart_fault_monitor_20261005/rtl_full_results.xml`,
  39.35 s across two cases.
- Fresh synthesized gate shell/RTL fabric:
  `build/uart_fault_monitor_20261005/gate_shell_full_results.xml`, 68.50 s.

The unchanged monitor test checks normal TX, RX, independent overlapping
events, counter wrap, framing-error status, USER_RESET and STOP with fault
control low. The new test transmits normal 0x55, injects a pulse to flip data
bit 1 and independently decodes 0x57 with a valid stop bit, then verifies
normal 0x55 transmission recovers. The event counter reaches three while
these transmissions occur. It also checks idle inversion, restoration,
reset clearing status and STOP parking despite held-high fault control.

The gate shell is the isolated freshly synthesized frozen-G1 shell described
in `g1_uart_monitor.md`, not a hardened netlist. Fabric remains RTL with D-023
settling. No SDF, native mapped-fabric signoff or silicon result is claimed.

## Scope and reproduction

This is an externally timed programmable line override, not an autonomous
fault scheduler. Synchronizer/output-register latency must be allowed for;
sub-clock pulses are not supported. Host SPI alone cannot schedule a precise
single-bit override at DIV=16. The test supplies the control through a top-level
input, timed in project clocks. Counters still wrap without an overflow flag.
There is no new hard protocol-specific block.

```sh
source .venv/bin/activate
export PATH="$PATH:/home/younix/oss-cad-suite/bin"
export PYTHONPATH="$PWD/tools:$PWD/test"
python -m compile.compile protocols/uart_monitor/uart_fault_monitor_top.v \
  protocols/uart_monitor/uart_monitor_top.v protocols/uart/*.v \
  --pins protocols/uart_monitor/fault.yaml --arch arch/warp_g1 \
  --strict-ports -o build/uart_fault_fresh
export WARP_UART_FAULT_BITFILE="$PWD/build/uart_fault_fresh/fault.wbit"
export WARP_UART_MONITOR_BITFILE="$WARP_UART_FAULT_BITFILE"
make -C test WARP_FABRIC=rtl \
  COCOTB_TEST_MODULES=test_uart_monitor,test_uart_fault_monitor \
  SIM_BUILD="$PWD/build/uart_fault_fresh/sim" \
  COCOTB_RESULTS_FILE="$PWD/build/uart_fault_fresh/results.xml"
```

Use a fresh output directory and pinned project tools. Exact gate-shell
commands/logs for the local run are retained in the ignored build directory;
this result has no new CI run ID.
