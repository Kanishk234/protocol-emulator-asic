# Primitive-aware user HDL helpers

These Verilog-2005 modules use the existing G1 `WP_TIMER` / `WP_SHIFT` resources. Supply helper files as additional source arguments to `python -m compile.compile`; the compiler supplies `warp_prims.v` for a primitive architecture. For simulation use `tools/compile/prims/warp_prims_sim.v` plus `arch/prims/wp_timer.v` and `arch/prims/wp_shift.v`, instead of the synthesis wrappers.

Both modules require synchronous active-low `rst_n`. Requests are accepted only at an edge with `start && ready`. A held-high start requests another operation when ready returns: drive a one-cycle request for a single operation. Requests while busy are ignored, rather than queued. Reset cancels an operation. Input signals must already be synchronous; these wrappers do not synchronize pins.

## `wp_delay`

`CYCLES` must be 1–65536. Accepting start loads `CYCLES-1`; that edge does not count toward the delay. `elapsed` is asserted before the CYCLES-th subsequent **enabled** edge, and that edge consumes it and returns ready. With CYCLES=1, elapsed asserts immediately after acceptance if enable is high. Pausing enable freezes progress and suppresses elapsed. Consumers act on elapsed at a clock edge; it is an enable-qualified terminal condition, not an unconditional registered pulse. Costs one timer and one busy FF plus control logic. It does not use timer half-load rounding.

## `wp_shift_transaction`

`BITS` must be 1–15. The byte register remains eight bits even for longer transactions. Accepting start loads data and does not shift. Each subsequent edge with step shifts one bit while busy; pauses preserve the word. `serial` shows the outgoing bit **before** a shift edge. After BITS shifts, complete asserts for one clock cycle and result holds the shifted word; ready returns at the following edge. Steps after completion cannot corrupt result. MSB_FIRST=1 shifts toward bit 7, inserting sin at bit 0; MSB_FIRST=0 does the opposite. A short MSB-first transmission must left-align its payload in data. Longer than eight bits shifts out inserted bits after the first byte. Costs one shift register and one busy FF plus control logic.

Example instantiations:

```verilog
wp_delay #(.CYCLES(16)) wait_bit (
    .clk(clk), .rst_n(rst_n), .start(request), .enable(1'b1),
    .ready(ready), .elapsed(tick));
wp_shift_transaction #(.BITS(8), .MSB_FIRST(1'b0)) transfer (
    .clk(clk), .rst_n(rst_n), .start(load_byte), .step(tick),
    .sin(rx), .data(tx_byte), .ready(byte_ready), .complete(byte_done),
    .serial(tx), .result(rx_byte));
```

The example illustrates connections, not a complete protocol. No timing, fit, or bitstream claim is made until compilation and loaded-fabric checks run. Parameters outside the supported ranges are invalid; the HDL does not contain synthesis-time initial assertions.

`tools/compile/tests/test_helpers.py` exercises pause, reset cancellation, load priority, ignored busy requests, both bit orders, and prevention of extra shifts using Icarus only on GitHub Actions. Set WARP_HELPER_RTL_TESTS=1 for an explicitly requested local simulator run.

Compile the included smoke example in the cloud with:

```sh
PYTHONPATH=tools python -m compile.compile --pins tools/compile/helpers/helper_demo.yaml \
  -o build/helpers-demo tools/compile/helpers/helper_demo.v \
  tools/compile/helpers/wp_delay.v tools/compile/helpers/wp_shift_transaction.v
```

This example produces one delayed shift per accepted delay request, so eight suitably spaced requests are needed for one transfer. It is intended to exercise compiler integration, not demonstrate a periodic serial engine. Avoid tying delay start to a constant: requests while the one-shot delay is busy are intentionally ignored.
