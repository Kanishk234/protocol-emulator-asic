# G1 UART plus bounded event timestamp capture

Local runs `uart_capture_20261005`, `uart_capture6_20261005` and
`uart_capture6_final_20261005`, 2026-10-05. User bitstream only; frozen chip
hardware and fixed architecture-comparison workload list are unchanged.

An initial eight-bit timestamp/two-entry queue uses91/88LCs and does not fit.
The six-bit variant compiles/routes into83/88LCs, all two timers/two shifts,
17/36IO BELs and722words. The69.69MHz slow-corner estimate is only compiler
model timing, not configured-chip STA or a silicon rate. Final report:
`build/uart_capture6_final_20261005/report.json`. Its provenance audit passes;
the final demo-default image is byte-identical to the initial six-bit image
used in loaded tests.

The UART runs alongside soft timestamp capture on FAB_IN1. Six-bit timestamps
wrap every64project clocks. Two entries absorb events while capture delivery
is deselected or the shell backpressures it. Full storage drops the newest
event and sets sticky overflow. Fabric-side sampling adds observation latency.
A simultaneous pop makes room for a push even at full occupancy; this case
is specified in RTL but not claimed as a separately isolated loaded-test bin.

FAB_IN2 chooses which stream feeds the shell RX FIFO. It does not replace
bytes already queued there; drain the old stream before changing interpretation.
The shell's two entries provide additional buffering for the selected stream,
but are shared with UART. Host writes still transmit UART; UART receive can
fill/overrun while deselected. These limits are part of the user interface,
not a new shell protocol or hard resource.

The loaded top-level test checks UART0x55 while three events occur, two-entry
full/drop-newest overflow, ordered timestamp delta32, queue reuse and a known
68-clock event separation producing modular delta4. It then clears state
through USER_RESET, receives UART0xA5 after selection changes, and checks STOP
parking. The extended test additionally withholds host reads with capture
selected to fill the shell and soft queues, checks four retained events in
order with unequal intervals, and confirms the fifth is dropped. Final tests
PASS, each exactly one case with no failure/error/skip:

- RTL shell/fabric: `build/uart_capture6_20261005/rtl_results.xml`,26.75s.
- Synthesized gate shell/RTL fabric:
  `build/uart_capture6_20261005/gate_shell_results.xml`,43.55s.

Tests use real SPI loading, RTL fabric and D-023 settling. The gate-shell
netlist is freshly synthesized frozen G1 (same isolated setup as the earlier
monitor demos), without SDF or hardened-netlist signoff. No native mapped
fabric or silicon result is claimed.

## Reproduce

```sh
source .venv/bin/activate
export PATH="$PATH:/home/younix/oss-cad-suite/bin"
export PYTHONPATH="$PWD/tools:$PWD/test"
python -m compile.compile protocols/uart_capture/uart_capture_top.v \
  protocols/uart/*.v --pins protocols/uart_capture/demo.yaml \
  --arch arch/warp_g1 --strict-ports -o build/uart_capture_fresh
python -m compile.audit build/uart_capture_fresh/report.json
export WARP_UART_CAPTURE_BITFILE="$PWD/build/uart_capture_fresh/demo.wbit"
make -C test WARP_FABRIC=rtl COCOTB_TEST_MODULES=test_uart_capture \
  SIM_BUILD="$PWD/build/uart_capture_fresh/sim" \
  COCOTB_RESULTS_FILE="$PWD/build/uart_capture_fresh/results.xml"
```

Use fresh directories and pinned tools. The demo YAML selects six bits;
`--set STAMP_BITS=8` reproduces the rejected wider screen. Timestamps are
ambiguous for unknown intervals of64clocks or more, and there is no timestamp
wrap flag. This is a small buffering demonstration, not a deep logic analyzer.

## Prescaled range option (session50)

`STAMP_SHIFT=2` stores the upper six bits of an eight-bit free-running counter.
It samples events every project clock but timestamps them in four-clock ticks,
extending wrap from64to256clocks. Queue depth remains two. It fits85/88LCs,
two more than the original, with three spare; timers/shifts/IO/722-word image
length and69.69MHz model estimate stay the same. This sacrifices timestamp
resolution and still cannot disambiguate unknown intervals beyond one wrap.
No chip clock or architecture contract changes.

Run `build/uart_capture_prescaled_20261005/report.json` and `prescaled.wbit`:
provenance audit PASS. Actual SPI-loaded top-port tests PASS RTL29.28s and
synthesized-shell/RTL-fabric46.93s (`rtl_results.xml`, `gate_shell_results.xml`
in that directory), each one case with no failure/error/skip. The existing
TX/capture/overflow/backpressure/RX/reset/STOP test now checks a272-clock
interval giving modular delta4 and a13-clock interval giving3or4ticks,
depending on phase. The latter checks timestamp quantization without dropping
events. Same-cycle full pop/push remains an unisolated coverage bin.

Recompile using `--pins protocols/uart_capture/prescaled.yaml`; set
`WARP_UART_CAPTURE_BITFILE` to its `prescaled.wbit` and
`WARP_UART_CAPTURE_STAMP_SHIFT=2` when running the loaded test above. Default
test setting remains0. Fresh unscaled build `uart_capture_default_refresh_20261005`
audits PASS, is byte-identical to the earlier tested83-cell image, and passes
the expanded loaded RTL test31.00s. Its report replaces the older report for
auditing the current parameterized source; historical source hashes are not
expected to match after this edit. Verilog-2005 elaboration passes. These are
local simulation/model results, without SDF, native mapped fabric or silicon.
