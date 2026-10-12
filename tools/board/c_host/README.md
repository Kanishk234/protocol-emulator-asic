# Portable C channel transport

`warp_host.c` is an allocation-free C99 host-channel layer for the existing
WARP shell. It uses a caller-supplied synchronous SPI callback, so an RP2040
hardware-SPI backend or another host can supply transport without changing
the chip. No board backend or measured speedup is claimed here.

`warp_read_id` checks the WP magic and returns the architecture version.
`warp_load_words` loads native uint32_t words in big-endian wire order;
`warp_load_wbit` accepts the existing WBIT file format, checking its magic,
length, sync word and IEEE CRC-32 before device I/O. Both loaders require
1..64 words per chunk, a nonempty image and a 16-bit word count. They verify
the device architecture, refuse RUNNING, issue LOAD_BEGIN/DATA/END and check
the final LOADED state/error. They do not issue RUN. Two fixed 257-byte
transaction buffers bound temporary storage independently of image size;
the caller owns the image storage. No heap or system initialization is used.
Input image memory must remain valid and unchanged until the call returns.
As with channels, exclusive ownership and callback timing are required.
Load transport errors leave an uncertain partial configuration and return
immediately; recover deliberately with a fresh load rather than retrying a
possibly completed transaction. File checks do not prove fabric frame
semantics: valid bitstreams must come from the matching compiler.
Once the architecture and stopped state are checked, the loaders explicitly
read/clear prior sticky shell errors before LOAD_BEGIN. Successful loading
does not itself clear an old error, so this allows recovery from a failed
earlier load and makes the final error check specific to the new load.
WBIT's reserved two header bytes are ignored, matching both existing Python
parsers; they are not a format-version field. Compiler-generated files write
them as zero.

Each callback invocation is exactly one complete CS-low transaction. Supply
mode 0, MSB-first bytes, SCK no faster than project clock / 8, at least eight
project clocks from CS falling to first SCK rising, and at least four project
clocks of CS-high idle. Ensure the callback completes all bytes and reports
any transport failure. The driver itself does not generate pin timing.

`warp_poll` uses the opcode-time status of READ_ID and does not clear sticky
errors. `warp_read_status` explicitly reads and clears shell status/error
flags according to the architecture contract. Writes poll for RUNNING and
tx_ready before sending one CH_WRITE transaction. Reads first poll READ_ID
and issue CH_READ only after observing rx_valid. This matters because the
shell captures outgoing status near CS assertion but decides whether to pop
at opcode completion: an empty CH_READ can consume a byte that arrives
during its opcode even though its returned status said empty. Non-destructive
READ_ID polling avoids that race and avoids bad-command errors outside RUNNING.
The driver also verifies the CH_READ response status. Poll limits bound
transaction attempts, not elapsed time. Both functions reject a non-RUNNING
state. A zero poll limit performs no I/O and returns WARP_TIMEOUT.

The `*_many` functions preserve byte order and report confirmed progress.
Only the final byte carries `last` for a write with last enabled. They still
send individual protocol commands: there is no unsupported burst opcode.
CH_READ has no last flag in the host response.

The caller must exclusively own the host interface across each operation,
including polling and transfers: another reader can invalidate rx_valid and
another writer can invalidate tx_ready.
Serialize callbacks and prevent concurrent STOP/reset/reconfiguration.
On an I/O error the current byte may already have been accepted or consumed;
do not blindly retry it. Return buffers/progress exclude that uncertain byte.
Recovery requires application-level synchronization or reset/reload.

Build with `cc -std=c99 -Wall -Wextra -Werror -c warp_host.c`. The native
tests compile and execute a scripted callback harness under pytest; they
validate wire framing/backpressure/error handling, not silicon behavior.

## Bounded duplex service

`warp_channel_duplex` services up to one incoming byte, then one outgoing byte
per round. A full TX queue does not block polling/draining RX, and an empty RX
queue does not block sending TX. Use disjoint buffers and progress pointers,
exclusive host ownership and an explicit maximum round count. The final `last`
flag belongs only to the final outgoing byte.

On timeout, both counters identify confirmed prefixes; the caller can resume
the remaining slices. On I/O failure the current transaction may have been
accepted despite the callback failure: retain reported progress but resolve
that ambiguity before retrying. Other state/errors stop immediately. No heap,
automatic RUN, bulk hardware opcode or unbounded polling is introduced.

45 focused C wire/model tests pass locally, including independent shell-model
backpressure, ordered duplex bytes/last flags, partial progress and a write
accepted before I/O failure. This is transaction-level verification; callback
timing on a board and real board performance remain separate.

[Loaded integration run38293580979](https://github.com/Kanishk234/protocol-emulator-asic/actions/runs/38293580979) compiles this C driver and connects its callback to actual simulated SPI pins. A fresh hostecho image is loaded with stale-error recovery, then31bytes are exchanged in both directions with order, final indication, USER_RESET and STOP checks. This passes under the documented D-023 configured-fabric RTL simulation scope; no board/backend speed or native/SDF acceptance follows.
The current budget planner remains single-direction and does not certify this
round-robin service's full-duplex throughput.
