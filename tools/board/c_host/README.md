# Portable C channel transport

`warp_host.c` is an allocation-free C99 host-channel layer for the existing
WARP shell. It uses a caller-supplied synchronous SPI callback, so an RP2040
hardware-SPI backend or another host can supply transport without changing
the chip. No board backend or measured speedup is claimed here.

Each callback invocation is exactly one complete CS-low transaction. Supply
mode 0, MSB-first bytes, SCK no faster than project clock / 8, at least eight
project clocks from CS falling to first SCK rising, and at least four project
clocks of CS-high idle. Ensure the callback completes all bytes and reports
any transport failure. The driver itself does not generate pin timing.

`warp_poll` uses the opcode-time status of READ_ID and does not clear sticky
errors. `warp_read_status` explicitly reads and clears shell status/error
flags according to the architecture contract. Writes poll for RUNNING and
tx_ready before sending one CH_WRITE transaction. Reads issue CH_READ and
accept the response only when that transaction's opcode-time rx_valid is
set; an empty read never produces a fabricated byte. Poll limits bound
transaction attempts, not elapsed time. Both functions reject a non-RUNNING
state. A zero poll limit performs no I/O and returns WARP_TIMEOUT.

The `*_many` functions preserve byte order and report confirmed progress.
Only the final byte carries `last` for a write with last enabled. They still
send individual protocol commands: there is no unsupported burst opcode.
CH_READ has no last flag in the host response.

The caller must exclusively own the host interface across each operation,
including polling and writes: another writer can invalidate tx_ready.
Serialize callbacks and prevent concurrent STOP/reset/reconfiguration.
On an I/O error the current byte may already have been accepted or consumed;
do not blindly retry it. Return buffers/progress exclude that uncertain byte.
Recovery requires application-level synchronization or reset/reload.

Build with `cc -std=c99 -Wall -Wextra -Werror -c warp_host.c`. The native
tests compile and execute a scripted callback harness under pytest; they
validate wire framing/backpressure/error handling, not silicon behavior.
