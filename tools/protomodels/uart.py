"""Reference UART line model, 8N1: idle high, start bit 0, 8 data bits LSB first, stop bit 1.

Written from the standard asynchronous serial framing, not from TRIPWIRE firmware.
Levels are one value per 50 MHz clock; bit boundaries use exact fractional positions.
"""


def encode(data, clocks_per_bit, idle_bits=4, stop_bits=1, bad_stop=()):
    """Waveform for `data`. Byte indices in `bad_stop` get a 0 stop bit (framing error),
    followed by one idle (high) bit: a start bit is a high-to-low edge, so no receiver can
    find the next frame if the line never returns high."""
    level, t = [], 0.0

    def emit(bit, nbits=1):
        nonlocal t
        start, t = round(t), t + nbits * clocks_per_bit
        level.extend([bit] * (round(t) - start))

    emit(1, idle_bits)
    for i, byte in enumerate(data):
        emit(0)
        for k in range(8):
            emit((byte >> k) & 1)
        emit(0 if i in bad_stop else 1, stop_bits)
        if i in bad_stop:
            emit(1)
    emit(1, idle_bits)
    return level


def decode(samples, clocks_per_bit):
    """Decode a waveform: returns [(byte, framing_ok)], sampling each bit in its middle."""
    out, i, n = [], 1, len(samples)
    while i < n:
        if samples[i - 1] == 1 and samples[i] == 0:              # falling edge: start bit
            mid = lambda k: i + round((k + 0.5) * clocks_per_bit)
            if mid(9) >= n:
                break
            if samples[mid(0)] == 0:                              # still low mid-bit: real start
                byte = sum(samples[mid(1 + k)] << k for k in range(8))
                out.append((byte, samples[mid(9)] == 1))
                i = mid(9)
                continue
        i += 1
    return out
