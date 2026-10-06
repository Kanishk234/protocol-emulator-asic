# UART with independent event monitor

A design-set showcase extension for unchanged G1, not a new hard block or
held-out evaluation. Uses the existing UART TX/RX RTL and a separate soft
four-bit rising-edge counter on FAB_IN1. UART RX is FAB_IN0 and TX FAB_OUT0.

`USER_STATUS[7:4]` reports the event count modulo 16. Bits 3:0 retain UART
status (bit 2 overrun, bit 1 framing error, bit 0 TX busy; bit 3 zero).
An extra fabric-side input sample register precedes edge detection, adding
one cycle of observation latency beyond the shell synchronizer. Reset clears
the sample, history and counter. An input high at reset release counts as a rising
event; drive it low during loading for a zero starting count. There is no
timestamp, event FIFO or overflow flag. Consecutive pulses must survive the
shell input synchronizer; the test uses eight-clock high and low intervals.

DIV=16 is a simulation-friendly fixed divisor. No silicon baud or event-rate
claim. All two timers and two shifters are used by UART; monitoring uses LUTs
and flip-flops. Compilation uses `demo.yaml`, this folder's RTL plus `../uart/*.v`.
The demonstration is separate from the fixed architecture comparison set.

Top-level loaded-fabric test: `test/test_uart_monitor.py`. Its bitstream path
comes from `WARP_UART_MONITOR_BITFILE`; it does not overwrite standard images.

Compile and test from the repository root, with the project venv and D-007
tool PATH (system simulator first, OSS CAD Suite appended):

```sh
source .venv/bin/activate
export PATH="$PATH:/home/younix/oss-cad-suite/bin"
export PYTHONPATH="$PWD/tools:$PWD/test"
python -m compile.compile protocols/uart_monitor/uart_monitor_top.v \
  protocols/uart/*.v --pins protocols/uart_monitor/demo.yaml \
  --arch arch/warp_g1 -o build/uart_monitor_fresh
export WARP_UART_MONITOR_BITFILE="$PWD/build/uart_monitor_fresh/demo.wbit"
make -C test WARP_FABRIC=rtl COCOTB_TEST_MODULES=test_uart_monitor \
  SIM_BUILD="$PWD/build/uart_monitor_sim_fresh" \
  COCOTB_RESULTS_FILE="$PWD/build/uart_monitor_sim_fresh_results.xml"
```

The loaded-chip test checks three transmitted bytes while 20 independent
input events are counted, including counter wrap, then host USER_RESET and
STOP. It also checks receive-plus-monitor overlap and framing-error status
with a deliberately bad stop bit. It uses the existing D-023 RTL routing-loop simulation handling, not
state initialization. It does not establish native mapped-fabric correctness
or a silicon rate.

## Fault injection variant

`uart_fault_monitor_top.v` and `fault.yaml` add FAB_IN2 as a synchronized
line-inversion control. Low gives normal UART TX; a timed high pulse can
corrupt selected transmitted bits, and high during idle forces TX low.
This costs one additional LC and one input IO BEL (38/88 LCs in local run
`uart_fault_monitor_20261005`). It retains RX and independent event counting.

The control is externally timed, with shell synchronizer/output latency;
it is not a host-command fault scheduler. A host cannot schedule a precise
single-bit pulse over SPI at the simulation's DIV=16. STOP parking still
overrides the loaded design even if fault control stays high.
Compile/load/test instructions and exact evidence:
[UART fault monitor report](../../docs/reports/g1_uart_fault_monitor.md).
