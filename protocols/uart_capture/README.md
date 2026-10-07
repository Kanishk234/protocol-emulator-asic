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

`test/` isolates queue boundaries through the user-design top ports: a full
queue pops its old head while accepting a simultaneous event, preserves order
and stays full without setting overflow; an empty ready queue retains a new
event until the next cycle. The hosted `capture queue boundaries` workflow
checks both timestamp settings. This is source-RTL coverage, supplementary to
the compiled SPI-loaded tests. [Run37520971978](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/37520971978)
passes both settings; independent XML audit finds one case per setting and no
failure, error or skipped result.

## Decode a saved capture

After draining the previous shell stream, select capture and save only valid
CH_READ payload bytes as a JSON array, for example `[60, 4]`. Check the capture
overflow bit in USER_STATUS: a set bit means events were lost. Do not mix UART
bytes or data retained before USER_RESET into this capture session.
`host.protocol.parse_channel_read(response)` returns `(status, payload)` with
`payload=None` for an empty channel; a valid zero timestamp remains `0`.
Append only non-None payloads. It rejects malformed responses and CH_READ
outside RUNNING.

```sh
source .venv/bin/activate
PYTHONPATH=tools python -m host.capture trace.json --max-gap-clocks 20
```

This reports an eight-clock interval for the example, assuming the interval
between observed events is known to be at most20 clocks. It does not report
absolute time or subtract shell/fabric input latency. The byte stream alone
cannot verify that assumption: a longer interval can have the same timestamps.

For `prescaled.yaml`, add `--stamp-shift 2`. The decoder reports an interval
range because counter phase is unknown: `[60, 0]` means13–19 clocks when the
maximum gap assumption is20. With six bits, accepted maximum-gap bounds are
at most63 clocks unscaled or252 clocks prescaled. Even a253-clock prescaled
gap can look like zero ticks at some counter phases, so a bound merely below
the256-clock wrap period is insufficient. Pass `--overflow` when overflow was
observed; decoding then rejects the trace. Incompatible bytes and intervals
contradicting the supplied bound are also rejected.

This host decoder works with either chip design using the same capture image
contract; its tests verify arithmetic and validation, not new hardware rates.

## Divide-by-eight candidate

`prescaled8.yaml` is an experimental six-bit timestamp image with
`STAMP_SHIFT=3`. It targets a512-clock counter period, with eight-clock
quantization. The host decoder needs `--stamp-shift 3` and a known maximum
gap of at most504 clocks; the stream cannot reveal extra full wraps.
The `extended capture image` cloud workflow must compile and audit the image,
check source queue boundaries and pass the existing real SPI-loaded capture
test before this configuration is treated as usable. Fit and timing are
pending measurements. This changes only the user bitstream, so the frozen G1
hardware can run it if those checks pass.
