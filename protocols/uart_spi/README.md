# Concurrent UART and SPI baseline workload

Experimental design-set workload for the fresh-candidate comparison; not a supported
production personality or a new chip capability claim. Sources also include
`protocols/uart/*.v` and `protocols/spi_ctrl/*.v`. The generic protocol collector
currently discovers only sources in this directory, so this workload is compiled
through its explicit campaign rather than that collector until dependency support
is added.

At the current 50 MHz target, DIV=434 and HALF=25 retain the existing UART and
SPI baseline settings. SPI mode is fixed by CPOL/CPHA in the image. UART full
duplex and SPI full duplex run concurrently, using two inputs and four outputs.
The host has the same physical channel as G1; two-byte framing adds explicit
servicing overhead, identical for every compared architecture.

Host writes alternate header then payload. Header bit0 selects UART(0)/SPI(1);
bit1 is SPI last-byte/CS-release; bits7:2 are ignored. Payload is one byte for
that engine. A blocked engine applies head-of-line backpressure to this channel;
the other engine can continue already accepted work but cannot receive a new
command until the blocked payload is accepted. Reset aborts partial packets.

Host reads alternate lane tag (0/1) then received byte. Once a tag is accepted,
its lane stays locked until its payload is accepted. When both lanes have data,
round-robin arbitration favors the lane opposite the previous completed packet.
Each engine has its original one-byte receive slot; service promptly to avoid
its documented overrun/drop behavior. Status[7:5] is UART {overrun,ferr,busy};
status[4:3] is SPI {overrun,cs_active}; status[2:0] is zero.

UART_PRIMS=1/SPI_PRIMS=1 requires three timers and three shifts, exceeding G1's
two of each. Default 1/0 keeps UART hard primitives and makes SPI soft logic.
Additional 0/1 and 0/0 forms distinguish primitive pressure from logic capacity.
Fit, loaded operation and timing are unqualified until campaign evidence passes.
