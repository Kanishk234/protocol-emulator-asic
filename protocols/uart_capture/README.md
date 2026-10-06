# UART with two-entry event timestamp capture

Design-set showcase on unchanged G1. UART RX/TX retain FAB_IN0/FAB_OUT0.
FAB_IN1 events pass through a fabric sample/history pair. Each detected rising
edge queues a configurable free-running timestamp. The fitting
demo uses six bits, modulo64; the module's eight-bit default is a rejected screen.
`STAMP_SHIFT` selects the number of low counter bits omitted from storage:
zero gives one project clock per tick, two gives four clocks per tick.
Events are still observed every clock; only timestamp resolution changes.
The queue has two entries and drops the newest event when full, setting a
sticky overflow flag until USER_RESET. A simultaneous pop permits a push
even when full; delivery returns the old head. USER_RESET clears the soft
queue/history/time; already queued shell bytes remain until drained or STOP.

FAB_IN2 selects the stream feeding the shell's RX FIFO: low selects UART RX;
high selects capture bytes, which drain automatically while the shell is ready.
Already queued host bytes retain their order across selection changes; drain
them before interpreting a newly selected stream.
Host writes always transmit UART bytes. Hold select stable before/through a
stream transfer; selection is not a host command. UART RX can fill/overrun
while its reads are deselected. This is bounded soft storage, not a new hard
block, deep trace buffer, autonomous fault scheduler or silicon rate claim.

USER_STATUS: bit7 overflow, bit6 full, bit5 nonempty, bit4 zero; bits3:0
retain UART status. Demo timestamps wrap after64clocks; differences are meaningful
only when the elapsed interval is known to be shorter than that. Pulses must
survive shell synchronization. No event counter or explicit timestamp-wrap flag.

Compile the top plus `protocols/uart/*.v` with `demo.yaml`, explicit
`--arch arch/warp_g1`, project venv and pinned tools. This uses `demo.yaml`
to stay outside the frozen architecture comparison workload discovery.
Fit and loaded verification are required before making a functionality claim.

Initial eight-bit timestamp build does not fit:91/88LCs in local run
`uart_capture_20261005`. `STAMP_BITS` can be1–8; narrower timestamps reduce
storage/counter cost and wrap after `2**STAMP_BITS` clocks. The six-bit variant
fits83/88LCs and passes loaded RTL/synthesized-shell tests; high host-byte bits
are zero. No eight-bit fit or silicon rate claim. Exact evidence/reproduction:
[capture report](../../docs/reports/g1_uart_capture.md).

`prescaled.yaml` keeps six stored bits and sets `STAMP_SHIFT=2`: four clocks
per timestamp tick, wrapping after256clocks, at85/88LCs in local build
`uart_capture_prescaled_20261005`. It costs two more cells than `demo.yaml`
and leaves three spare. Queue depth and event sampling latency are unchanged.
Intervals not divisible by four quantize to either adjacent tick difference,
depending on counter phase. Range is still finite and there is no wrap flag.
See the report for loaded verification and its gate/silicon limits.
