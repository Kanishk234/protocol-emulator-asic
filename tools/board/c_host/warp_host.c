#include "warp_host.h"

static int transfer(warp_host *host, const uint8_t *tx, uint8_t *rx, size_t n)
{
    if (!host || !host->transfer) return WARP_ARGUMENT;
    return host->transfer(host->context, tx, rx, n) ? WARP_IO : WARP_OK;
}
int warp_poll(warp_host *host, uint8_t *status)
{
    const uint8_t tx[] = {0x01};
    uint8_t rx[1];
    int rc;
    if (!status) return WARP_ARGUMENT;
    rc = transfer(host, tx, rx, sizeof tx);
    if (!rc) *status = rx[0];
    return rc;
}
int warp_read_status(warp_host *host, uint8_t *status, uint8_t *error)
{
    const uint8_t tx[] = {0x02, 0, 0};
    uint8_t rx[3];
    int rc;
    if (!status || !error) return WARP_ARGUMENT;
    rc = transfer(host, tx, rx, sizeof tx);
    if (!rc) { *status = rx[1]; *error = rx[2]; }
    return rc;
}
int warp_channel_write(warp_host *host, uint8_t byte, int last, size_t polls)
{
    size_t i;
    uint8_t status;
    uint8_t tx[] = {0x30, last ? 1 : 0, byte};
    uint8_t rx[3];
    if (!host || !host->transfer) return WARP_ARGUMENT;
    for (i = 0; i < polls; ++i) {
        int rc = warp_poll(host, &status);
        if (rc) return rc;
        if ((status >> 5) != 3) return WARP_STATE;
        if (status & 0x08) return transfer(host, tx, rx, sizeof tx);
    }
    return WARP_TIMEOUT;
}
int warp_channel_read(warp_host *host, uint8_t *byte, size_t polls)
{
    size_t i;
    const uint8_t tx[] = {0x31, 0};
    uint8_t rx[2];
    uint8_t status;
    if (!host || !host->transfer || !byte) return WARP_ARGUMENT;
    for (i = 0; i < polls; ++i) {
        int rc = warp_poll(host, &status);
        if (rc) return rc;
        if ((status >> 5) != 3) return WARP_STATE;
        if (status & 0x10) {
            rc = transfer(host, tx, rx, sizeof tx);
            if (rc) return rc;
            if ((rx[0] >> 5) != 3) return WARP_STATE;
            if (!(rx[0] & 0x10)) return WARP_STATE;
            *byte = rx[1];
            return WARP_OK;
        }
    }
    return WARP_TIMEOUT;
}
int warp_channel_write_many(warp_host *host, const uint8_t *data, size_t length,
                            int last, size_t polls, size_t *completed)
{
    size_t i;
    if (!completed) return WARP_ARGUMENT;
    *completed = 0;
    if (!host || !host->transfer || (!data && length)) return WARP_ARGUMENT;
    for (i = 0; i < length; ++i) {
        int rc = warp_channel_write(host, data[i], last && i == length - 1, polls);
        if (rc) return rc;
        ++*completed;
    }
    return WARP_OK;
}
int warp_channel_read_many(warp_host *host, uint8_t *data, size_t length,
                           size_t polls, size_t *completed)
{
    size_t i;
    if (!completed) return WARP_ARGUMENT;
    *completed = 0;
    if (!host || !host->transfer || (!data && length)) return WARP_ARGUMENT;
    for (i = 0; i < length; ++i) {
        int rc = warp_channel_read(host, &data[i], polls);
        if (rc) return rc;
        ++*completed;
    }
    return WARP_OK;
}
