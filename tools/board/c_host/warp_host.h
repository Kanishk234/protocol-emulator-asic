#ifndef WARP_HOST_H
#define WARP_HOST_H
#include <stddef.h>
#include <stdint.h>

/* One complete CS-low transaction. Return 0 on success, nonzero on failure.
 * Implementations supply mode-0 timing, CS setup/idle and serialization. */
typedef int (*warp_transfer_fn)(void *, const uint8_t *, uint8_t *, size_t);
typedef struct { warp_transfer_fn transfer; void *context; } warp_host;
enum { WARP_OK = 0, WARP_TIMEOUT = 1, WARP_STATE = 2,
       WARP_IO = 3, WARP_ARGUMENT = 4, WARP_FORMAT = 5,
       WARP_ARCH = 6, WARP_LOAD = 7 };
int warp_read_id(warp_host *, uint16_t *architecture);
/* chunk_words must be 1..64; no heap allocations or automatic RUN. */
int warp_load_words(warp_host *, uint16_t architecture, const uint32_t *,
                    size_t word_count, size_t chunk_words);
int warp_load_wbit(warp_host *, const uint8_t *, size_t length, size_t chunk_words);
int warp_poll(warp_host *, uint8_t *status);
int warp_read_status(warp_host *, uint8_t *status, uint8_t *error);
int warp_channel_write(warp_host *, uint8_t byte, int last, size_t polls);
int warp_channel_read(warp_host *, uint8_t *byte, size_t polls);
/* Progress reports only confirmed complete transactions. IO failure leaves
 * the current transaction's acceptance unknown: do not automatically retry. */
int warp_channel_write_many(warp_host *, const uint8_t *, size_t length,
                            int last, size_t polls_per_byte, size_t *completed);
int warp_channel_read_many(warp_host *, uint8_t *, size_t length,
                           size_t polls_per_byte, size_t *completed);
/* Read-first round-robin: at most one byte per direction per round.
 * Buffers must be disjoint. Timeout reports confirmed progress for both lanes.
 * Empty RX/full TX skips that lane; other state/IO errors stop immediately. */
int warp_channel_duplex(warp_host *, const uint8_t *tx, size_t tx_length,
                        int last, uint8_t *rx, size_t rx_length, size_t rounds,
                        size_t *tx_completed, size_t *rx_completed);
#endif
