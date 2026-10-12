#include "warp_host.h"

static int transfer(warp_host *host, const uint8_t *tx, uint8_t *rx, size_t n)
{
    if (!host || !host->transfer) return WARP_ARGUMENT;
    return host->transfer(host->context, tx, rx, n) ? WARP_IO : WARP_OK;
}
static uint32_t get_be32(const uint8_t *p)
{
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16)
         | ((uint32_t)p[2] << 8) | p[3];
}
static void put_be32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v;
}
static uint32_t crc_byte(uint32_t crc, uint8_t byte)
{
    unsigned i;
    crc ^= byte;
    for (i = 0; i < 8; ++i)
        crc = (crc >> 1) ^ ((crc & 1) ? UINT32_C(0xedb88320) : 0);
    return crc;
}
int warp_read_id(warp_host *host, uint16_t *architecture)
{
    const uint8_t tx[] = {1, 0, 0, 0, 0};
    uint8_t rx[5];
    int rc;
    if (!architecture) return WARP_ARGUMENT;
    rc = transfer(host, tx, rx, sizeof tx);
    if (rc) return rc;
    if (rx[1] != 0x57 || rx[2] != 0x50) return WARP_FORMAT;
    *architecture = (uint16_t)(((uint16_t)rx[3] << 8) | rx[4]);
    return WARP_OK;
}
/* Exactly one of words/body is supplied, already validated before I/O. */
static int load(warp_host *host, uint16_t arch, const uint32_t *words,
                const uint8_t *body, size_t count, size_t chunk, uint32_t crc)
{
    uint8_t tx[257], rx[257], status, error;
    uint16_t device_arch;
    size_t offset, i;
    int rc = warp_read_id(host, &device_arch);
    if (rc) return rc;
    if (device_arch != arch) return WARP_ARCH;
    rc = warp_poll(host, &status);
    if (rc) return rc;
    if ((status >> 5) == 3) return WARP_STATE;
    /* Successful LOAD_BEGIN/END do not clear a prior sticky error. Clear it
       deliberately before this load so the final error belongs to this load. */
    rc = warp_read_status(host, &status, &error);
    if (rc) return rc;
    if ((status >> 5) == 3) return WARP_STATE;
    tx[0] = 0x10; tx[1] = (uint8_t)(arch >> 8); tx[2] = (uint8_t)arch;
    tx[3] = (uint8_t)(count >> 8); tx[4] = (uint8_t)count;
    rc = transfer(host, tx, rx, 5);
    if (rc) return rc;
    for (offset = 0; offset < count; offset += chunk) {
        size_t n = count - offset < chunk ? count - offset : chunk;
        tx[0] = 0x11;
        for (i = 0; i < n; ++i) {
            uint32_t word = words ? words[offset + i] : get_be32(body + 4 * (offset + i));
            put_be32(tx + 1 + 4 * i, word);
        }
        rc = transfer(host, tx, rx, 1 + 4 * n);
        if (rc) return rc;
    }
    tx[0] = 0x12; put_be32(tx + 1, crc);
    rc = transfer(host, tx, rx, 5);
    if (rc) return rc;
    rc = warp_read_status(host, &status, &error);
    if (rc) return rc;
    return (status >> 5) == 2 && error == 0 ? WARP_OK : WARP_LOAD;
}
int warp_load_words(warp_host *host, uint16_t arch, const uint32_t *words,
                    size_t count, size_t chunk)
{
    uint32_t crc = UINT32_C(0xffffffff);
    size_t i;
    unsigned j;
    if (!host || !host->transfer || !words || !count || count > 65535
        || !chunk || chunk > 64) return WARP_ARGUMENT;
    if (words[0] != UINT32_C(0xfab0fab1)) return WARP_FORMAT;
    for (i = 0; i < count; ++i)
        for (j = 0; j < 4; ++j)
            crc = crc_byte(crc, (uint8_t)(words[i] >> (24 - 8 * j)));
    return load(host, arch, words, 0, count, chunk, crc ^ UINT32_C(0xffffffff));
}
int warp_load_wbit(warp_host *host, const uint8_t *data, size_t length, size_t chunk)
{
    uint32_t count, crc = UINT32_C(0xffffffff);
    size_t i;
    uint16_t arch;
    if (!host || !host->transfer || !data || !chunk || chunk > 64)
        return WARP_ARGUMENT;
    if (length < 16 || data[0] != 'W' || data[1] != 'B'
        || data[2] != 'I' || data[3] != 'T') return WARP_FORMAT;
    count = get_be32(data + 8);
    if (!count || count > 65535 || length != 16 + (size_t)count * 4)
        return WARP_FORMAT;
    if (get_be32(data + 16) != UINT32_C(0xfab0fab1)) return WARP_FORMAT;
    for (i = 16; i < length; ++i) crc = crc_byte(crc, data[i]);
    crc ^= UINT32_C(0xffffffff);
    if (crc != get_be32(data + 12)) return WARP_FORMAT;
    arch = (uint16_t)(((uint16_t)data[4] << 8) | data[5]);
    return load(host, arch, 0, data + 16, count, chunk, crc);
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

int warp_channel_duplex(warp_host *host, const uint8_t *tx, size_t tx_length,
                        int last, uint8_t *rx, size_t rx_length, size_t rounds,
                        size_t *tx_completed, size_t *rx_completed)
{
    size_t round;
    if (!tx_completed || !rx_completed || tx_completed == rx_completed)
        return WARP_ARGUMENT;
    *tx_completed = 0; *rx_completed = 0;
    if (!host || !host->transfer || (!tx && tx_length) || (!rx && rx_length))
        return WARP_ARGUMENT;
    for (round = 0; round < rounds; ++round) {
        int rc;
        if (*rx_completed < rx_length) {
            rc = warp_channel_read(host, rx + *rx_completed, 1);
            if (rc == WARP_OK) ++*rx_completed;
            else if (rc != WARP_TIMEOUT) return rc;
        }
        if (*tx_completed < tx_length) {
            rc = warp_channel_write(host, tx[*tx_completed],
                     last && *tx_completed == tx_length - 1, 1);
            if (rc == WARP_OK) ++*tx_completed;
            else if (rc != WARP_TIMEOUT) return rc;
        }
        if (*tx_completed == tx_length && *rx_completed == rx_length)
            return WARP_OK;
    }
    return *tx_completed == tx_length && *rx_completed == rx_length
           ? WARP_OK : WARP_TIMEOUT;
}
