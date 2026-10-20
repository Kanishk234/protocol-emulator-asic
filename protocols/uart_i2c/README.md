# Concurrent UART and I2C-controller baseline

Experimental R1 comparison workload; no production fit or hardware claim.
Compile with `protocols/uart/*.v`, `protocols/i2c_ctrl/i2c_ctrl_top.v` and this
wrapper. Uses `concurrency.yaml`, not an automatically discovered `pins.yaml`.
At the50MHz assessment target, DIV434 and Q125 match existing single-engine
settings. Keep the I2C controller's documented scope: single controller,
clock stretching, host-issued address/byte commands; not an I2C target.

The same two-byte framing, round-robin response arbitration, one-slot receive
limits and head-of-line write blocking as the UART+SPI benchmark apply. Header
bit0 selects UART0 or I2C1; all other header bits are ignored by these engines.
I2C payloads are the unchanged native START/WRITE/READ/STOP command stream.
Every response is lane tag then data. Status[7:5] is UART {overrun,ferr,busy};
status[4]=0; status[3:0] is I2C {err,overrun,last_nack,bus_owned}.

One input/one output serve UART; two bidirectional pins serve open-drain I2C.
Each bidirectional output value stays zero; only its output enable is driven.
The wrapper does not create protocol-specific hard blocks. Fully hard-backed
UART+I2C requires three timers and three shifts. Mixed variants establish
whether G1's existing two pairs plus soft logic can support this workload.

Pin-level tests reuse the existing independent I2C target/reference decoder
and UART peer helper. They exercise concurrent UART TX/RX, I2C write/read,
repeated START, clock stretching and tagged host servicing in all four
hard/soft selections. Configured fabric operation and physical timing remain
separate acceptance gates.
